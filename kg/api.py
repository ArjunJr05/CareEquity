import os
import tempfile
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
CSV_DATA_PATH = os.path.join(os.path.dirname(__file__), "src", "SDOH_MODEL_DATA.csv")

# Global variables for Neo4j driver and cached CSV dataset
driver = None
df_csv: Optional[pd.DataFrame] = None


def load_dataset():
    global df_csv
    if os.path.exists(CSV_DATA_PATH):
        df_csv = pd.read_csv(CSV_DATA_PATH)
        df_csv['fips_str'] = df_csv['county_fips'].astype(int).astype(str)
    else:
        df_csv = pd.DataFrame()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to handle Neo4j driver startup and shutdown."""
    global driver
    load_dataset()
    if NEO4J_URI and NEO4J_USERNAME and NEO4J_PASSWORD:
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            driver.verify_connectivity()
            print("Successfully connected to Neo4j Aura Graph Database!")
        except Exception as e:
            print(f"Warning: Could not connect to Neo4j database: {e}")
            driver = None
    else:
        print("Warning: Neo4j credentials missing in environment.")

    yield

    if driver:
        driver.close()
        print("Neo4j driver connection closed.")


app = FastAPI(
    title="SDoH Knowledge Graph REST API",
    description="Production REST API for Social Determinants of Health (SDoH) Knowledge Graph Explorer",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- PYDANTIC RESPONSE MODELS ---

class HealthCheckResponse(BaseModel):
    status: str
    db_connected: bool
    neo4j_uri: str


class CountyListItem(BaseModel):
    fips: str
    county_name: str
    state_abbr: str
    display_label: str


class CountyOverviewResponse(BaseModel):
    fips: str
    county_name: str
    state_abbr: str
    population: int
    median_household_income: Optional[float]
    svi_overall: Optional[float]


class NodeModel(BaseModel):
    id: str
    label: str
    type: str
    color: str
    size: int
    title: str


class EdgeModel(BaseModel):
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    label: str
    color: str
    width: int
    dashes: bool = False
    title: Optional[str] = ""

    class Config:
        populate_by_name = True


class GraphResponse(BaseModel):
    fips: str
    county_name: str
    nodes: List[NodeModel]
    edges: List[EdgeModel]


class SDoHBarrierItem(BaseModel):
    factor_name: str
    county_value: float
    unit: str
    us_avg: float
    difference: float


class HealthOutcomeItem(BaseModel):
    condition_name: str
    county_prevalence: float
    us_avg: float
    difference: float


# --- API ENDPOINTS ---

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
def health_check():
    """Health check endpoint to verify API and Neo4j connectivity."""
    db_connected = False
    if driver:
        try:
            driver.verify_connectivity()
            db_connected = True
        except Exception:
            db_connected = False

    return HealthCheckResponse(
        status="online",
        db_connected=db_connected,
        neo4j_uri=NEO4J_URI
    )


@app.get("/api/counties", response_model=List[CountyListItem], tags=["Counties"])
def get_counties_list():
    """Returns list of all available counties for autocompletion."""
    if df_csv is None or df_csv.empty:
        raise HTTPException(status_code=500, detail="County dataset not loaded.")

    counties = []
    for _, r in df_csv.iterrows():
        fips = str(r['fips_str'])
        name = str(r['county_name'])
        state = str(r['state_abbr'])
        counties.append(CountyListItem(
            fips=fips,
            county_name=name,
            state_abbr=state,
            display_label=f"{name} ({fips})"
        ))

    return counties


@app.get("/api/county/{fips}", response_model=CountyOverviewResponse, tags=["Counties"])
def get_county_overview(fips: str):
    """Returns overview KPI data for a target county FIPS."""
    if df_csv is None or df_csv.empty:
        raise HTTPException(status_code=500, detail="County dataset not loaded.")

    match = df_csv[df_csv['fips_str'] == str(fips)]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"County FIPS {fips} not found.")

    r = match.iloc[0]
    return CountyOverviewResponse(
        fips=str(r['fips_str']),
        county_name=str(r['county_name']),
        state_abbr=str(r['state_abbr']),
        population=int(r['population']),
        median_household_income=float(r['median_household_income']) if not pd.isna(r['median_household_income']) else None,
        svi_overall=float(r['svi_overall']) if not pd.isna(r['svi_overall']) else None
    )


@app.get("/api/county/{fips}/graph", response_model=GraphResponse, tags=["Knowledge Graph"])
def get_county_graph(fips: str, top_k: int = Query(10, ge=1, le=20)):
    """
    Queries Neo4j Aura Graph Database for central County node, connected State,
    and top K SDoH risk factors affecting the specified county.
    Automatically falls back to rich dataset when Neo4j is offline.
    """
    if df_csv is None or df_csv.empty:
        raise HTTPException(status_code=500, detail="County dataset not loaded.")

    county_match = df_csv[df_csv['fips_str'] == str(fips)]
    if county_match.empty:
        raise HTTPException(status_code=404, detail=f"County FIPS {fips} not found.")

    c_row = county_match.iloc[0]
    county_name = c_row['county_name']

    nodes_dict: Dict[str, Dict[str, Any]] = {}
    edges_list: List[Dict[str, Any]] = []

    if not driver:
        # Generate graph dynamically from local CSV dataset if Neo4j is offline
        c_row = county_match.iloc[0]
        nodes_dict['County'] = {
            'id': f"county_{fips}",
            'label': str(c_row['county_name']),
            'type': 'County',
            'color': '#6366f1',
            'size': 42,
            'title': f"<b>{c_row['county_name']}</b><br>FIPS: {fips}<br>Population: {int(c_row['population']):,}<br>Income: ${float(c_row['median_household_income']):,.0f}<br>SVI Score: {float(c_row['svi_overall']):.4f}"
        }

        # State Node
        state_id = f"state_{c_row['state_abbr']}"
        nodes_dict['State'] = {
            'id': state_id,
            'label': f"State: {c_row['state_abbr']}",
            'type': 'State',
            'color': '#3b82f6',
            'size': 26,
            'title': f"State: {c_row['state_abbr']}"
        }
        edges_list.append({
            'from': nodes_dict['County']['id'],
            'to': state_id,
            'label': 'IN_STATE',
            'color': '#94a3b8',
            'width': 2,
            'dashes': True,
            'title': 'State Link'
        })

        # SDoH Factors from CSV
        sdoh_cols = [
            ("Poverty Rate", 'poverty_rate', 15.1),
            ("Unemployment Rate", 'unemployment_rate', 5.16),
            ("No Vehicle Rate", 'no_vehicle_rate', 6.20),
            ("Lack of Health Insurance", 'lack_health_insurance', 11.57),
            ("Food Insecurity", 'food_insecurity', 16.87),
            ("Housing Insecurity", 'housing_insecurity', 13.66)
        ]

        for idx, (label, col, avg) in enumerate(sdoh_cols[:top_k]):
            val = float(c_row[col]) if col in c_row and not pd.isna(c_row[col]) else avg
            n_id = f"sdoh_{label.replace(' ', '_')}"
            diff = val - avg
            color = '#ef4444' if diff > 2 else ('#10b981' if diff < -2 else '#f59e0b')
            sev = 'High Risk' if diff > 2 else ('Protective' if diff < -2 else 'Moderate')

            nodes_dict[n_id] = {
                'id': n_id,
                'label': f"{label}\n({val:.1f}%)",
                'type': 'SDoHFactor',
                'color': color,
                'size': 30,
                'title': f"<b>SDoH Feature: {label}</b><br>Value: {val:.2f}%<br>National Avg: {avg:.2f}%<br>Status: <b>{sev}</b>"
            }

            edges_list.append({
                'from': nodes_dict['County']['id'],
                'to': n_id,
                'label': f"{val:.1f}%",
                'color': color,
                'width': 3,
                'dashes': False,
                'title': f"Status: {sev}"
            })

        nodes_formatted = [NodeModel(**n) for n in nodes_dict.values()]
        edges_formatted = [EdgeModel(**e) for e in edges_list]

        return GraphResponse(
            fips=str(fips),
            county_name=county_name,
            nodes=nodes_formatted,
            edges=edges_formatted
        )

    cypher_query = """
    MATCH (c:County {fips: $fips})-[r:HAS_FACTOR]->(f:SDoHFactor)
    OPTIONAL MATCH (c)-[:IN_STATE]->(s:State)
    RETURN c, s, r, f
    """

    sdoh_factors_list = []

    with driver.session() as session:
        result = session.run(cypher_query, fips=str(fips))
        records = list(result)

        if not records:
            raise HTTPException(status_code=404, detail=f"No graph data found in Neo4j for FIPS {fips}.")

        for record in records:
            c = record['c']
            s = record['s']
            r = record['r']
            f = record['f']

            # County Node
            if 'County' not in nodes_dict:
                nodes_dict['County'] = {
                    'id': f"county_{c['fips']}",
                    'label': c['name'],
                    'type': 'County',
                    'color': '#6366f1',
                    'size': 42,
                    'title': f"<b>{c['name']}</b><br>FIPS: {c['fips']}<br>Population: {c['population']:,}<br>Income: ${c['median_household_income']:,.0f}<br>SVI Score: {c['svi_overall']:.4f}"
                }

            # State Node
            if s and 'State' not in nodes_dict:
                n_id = f"state_{s['abbr']}"
                nodes_dict['State'] = {
                    'id': n_id,
                    'label': f"State: {s['abbr']}",
                    'type': 'State',
                    'color': '#3b82f6',
                    'size': 26,
                    'title': f"State: {s['abbr']}"
                }
                edges_list.append({
                    'from': nodes_dict['County']['id'],
                    'to': n_id,
                    'label': 'IN_STATE',
                    'color': '#94a3b8',
                    'width': 2,
                    'dashes': True,
                    'title': 'State Link'
                })

            # SDoH Factor
            if f:
                r_props = dict(r)
                val = r_props.get('value', 0)
                sev = r_props.get('severity', 'Medium')

        st_abbr = str(c_row['state_abbr']) if 'state_abbr' in c_row and not pd.isna(c_row['state_abbr']) else ''
        if st_abbr and 'State' not in nodes_dict:
            n_id = f"state_{st_abbr}"
            nodes_dict['State'] = {
                'id': n_id,
                'label': f"State: {st_abbr}",
                'type': 'State',
                'color': '#3b82f6',
                'size': 26,
                'title': f"State: {st_abbr}"
            }
            edges_list.append({
                'from': nodes_dict['County']['id'],
                'to': n_id,
                'label': 'IN_STATE',
                'color': '#94a3b8',
                'width': 2,
                'dashes': True,
                'title': 'State Link'
            })

        sdoh_config = [
            ("Poverty Rate", 'poverty_rate', "%", 15.1, 'Economic'),
            ("Unemployment Rate", 'unemployment_rate', "%", 5.16, 'Economic'),
            ("No Vehicle Rate", 'no_vehicle_rate', "%", 6.20, 'Transportation'),
            ("Internet Access Gap", 'internet_subscription_rate', "%", 82.5, 'Infrastructure'),
            ("Lack of Health Insurance", 'lack_health_insurance', "%", 11.57, 'Healthcare'),
            ("Food Insecurity", 'food_insecurity', "%", 16.87, 'Nutrition'),
            ("Transportation Barrier", 'transportation_barrier', "%", 9.23, 'Transportation'),
            ("Housing Insecurity", 'housing_insecurity', "%", 13.66, 'Housing'),
            ("Low Food Access Pct", 'low_access_population_pct_2019', "%", 24.30, 'Nutrition'),
            ("SNAP Low Access Pct", 'snap_low_access_pct_2019', "%", 7.89, 'Nutrition'),
            ("Fast Food Density", 'fast_food_per_1000_2020', "per 1k", 0.67, 'Nutrition'),
            ("Grocery Store Density", 'grocery_stores_per_1000_2020', "per 1k", 0.21, 'Nutrition')
        ]

        sdoh_factors_list = []
        for label, col, unit, us_avg, category in sdoh_config:
            if col in c_row and not pd.isna(c_row[col]):
                val = float(c_row[col])
                diff = ((val - us_avg) / max(abs(us_avg), 0.001)) * 100
                if col == 'internet_subscription_rate':
                    sev = "High Risk" if val < (us_avg - 10) else ("Medium Risk" if val < us_avg else "Low Risk")
                elif col == 'grocery_stores_per_1000_2020':
                    sev = "High Risk" if val < (us_avg * 0.7) else ("Medium Risk" if val < us_avg else "Low Risk")
                else:
                    sev = "High Risk" if diff > 15 else ("Medium Risk" if diff > 0 else "Low Risk")

                prio = 0 if 'High' in sev else (1 if 'Medium' in sev else 2)
                sdoh_factors_list.append({
                    'factor_name': label,
                    'category': category,
                    'value': val,
                    'severity': sev,
                    'priority': prio
                })

        sdoh_factors_list.sort(key=lambda x: x['priority'])
        for factor in sdoh_factors_list[:top_k]:
            fname = factor['factor_name']
            val = factor['value']
            sev = factor['severity']
            n_id = f"sdoh_{fname.replace(' ', '_')}"
            color = '#ef4444' if 'High' in sev else ('#10b981' if 'Low' in sev else '#f59e0b')

            nodes_dict[n_id] = {
                'id': n_id,
                'label': f"{fname}\n({val:.1f})",
                'type': 'SDoHFactor',
                'color': color,
                'size': 30,
                'title': f"<b>SDoH Feature: {fname}</b><br>Category: {factor['category']}<br>Value: {val:.2f}<br>Severity: <b>{sev}</b>"
            }
            edges_list.append({
                'from': nodes_dict['County']['id'],
                'to': n_id,
                'label': f"{val:.1f}",
                'color': color,
                'width': 3,
                'dashes': False,
                'title': f"Severity: {sev}"
            })

    nodes_formatted = [NodeModel(**n) for n in nodes_dict.values()]
    edges_formatted = [EdgeModel(**e) for e in edges_list]

    return GraphResponse(
        fips=str(fips),
        county_name=county_name,
        nodes=nodes_formatted,
        edges=edges_formatted
    )


@app.get("/api/county/{fips}/sdoh", response_model=List[SDoHBarrierItem], tags=["SDoH Factors"])
def get_county_sdoh_barriers(fips: str):
    """Returns SDoH risk factor statistics compared against US National averages."""
    if df_csv is None or df_csv.empty:
        raise HTTPException(status_code=500, detail="County dataset not loaded.")

    county_match = df_csv[df_csv['fips_str'] == str(fips)]
    if county_match.empty:
        raise HTTPException(status_code=404, detail=f"County FIPS {fips} not found.")

    c_row = county_match.iloc[0]

    sdoh_config = [
        ("Poverty Rate", 'poverty_rate', "%", 15.1),
        ("Unemployment Rate", 'unemployment_rate', "%", 5.16),
        ("No Vehicle Rate", 'no_vehicle_rate', "%", 6.20),
        ("Internet Subscription Rate", 'internet_subscription_rate', "%", 82.5),
        ("Lack of Health Insurance", 'lack_health_insurance', "%", 11.57),
        ("Food Insecurity", 'food_insecurity', "%", 16.87),
        ("Transportation Barrier", 'transportation_barrier', "%", 9.23),
        ("Housing Insecurity", 'housing_insecurity', "%", 13.66),
        ("Low Food Access Pct", 'low_access_population_pct_2019', "%", 24.30),
        ("SNAP Low Access Pct", 'snap_low_access_pct_2019', "%", 7.89),
        ("Grocery Store Density (per 1k)", 'grocery_stores_per_1000_2020', "per 1k", 0.21),
        ("Fast Food Density (per 1k)", 'fast_food_per_1000_2020', "per 1k", 0.67)
    ]

    items = []
    for label, col, unit, us_avg in sdoh_config:
        val = float(c_row[col]) if not pd.isna(c_row[col]) else 0.0
        diff = val - us_avg
        items.append(SDoHBarrierItem(
            factor_name=label,
            county_value=round(val, 2),
            unit=unit,
            us_avg=us_avg,
            difference=round(diff, 2)
        ))

    return items


@app.get("/api/county/{fips}/health-outcomes", response_model=List[HealthOutcomeItem], tags=["Health Outcomes"])
def get_county_health_outcomes(fips: str):
    """Returns chronic health outcomes prevalence compared against US National averages."""
    if df_csv is None or df_csv.empty:
        raise HTTPException(status_code=500, detail="County dataset not loaded.")

    county_match = df_csv[df_csv['fips_str'] == str(fips)]
    if county_match.empty:
        raise HTTPException(status_code=404, detail=f"County FIPS {fips} not found.")

    c_row = county_match.iloc[0]

    health_config = [
        ("Diabetes Prevalence", 'diabetes_prevalence', 11.13),
        ("Obesity Prevalence", 'obesity_prevalence', 37.67),
        ("High Blood Pressure Prevalence", 'high_bp_prevalence', 33.48),
        ("Physical Inactivity", 'physical_inactivity', 26.98),
        ("Smoking Prevalence", 'smoking_prevalence', 16.32),
        ("Heart Disease Prevalence", 'heart_disease_prevalence', 5.97),
        ("Poor Mental Health (14+ Days)", 'poor_mental_health', 18.61),
        ("Poor Physical Health (14+ Days)", 'poor_physical_health', 13.82)
    ]

    items = []
    for label, col, us_avg in health_config:
        val = float(c_row[col]) if not pd.isna(c_row[col]) else 0.0
        diff = val - us_avg
        items.append(HealthOutcomeItem(
            condition_name=label,
            county_prevalence=round(val, 2),
            us_avg=us_avg,
            difference=round(diff, 2)
        ))

    return items
