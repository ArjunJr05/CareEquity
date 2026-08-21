import os
import sys
import tempfile
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Query, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Import the bot so /api/chat can invoke it directly
sys.path.insert(0, os.path.dirname(__file__))
from bot import ask_bot, build_county_context

# Load environment variables
load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI", "")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
CSV_DATA_PATH  = os.path.join(os.path.dirname(__file__), "src", "SDOH_MODEL_DATA.csv")

# Global variables for Neo4j driver and cached CSV dataset
driver         = None
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


# ── New models for context + chat ─────────────────────────────────
class GraphSeverityItem(BaseModel):
    """Single SDoH factor with Neo4j-computed severity label."""
    factor_name: str
    category:    str
    value:       float
    severity:    str   # "High Risk" | "Medium" | "Low Risk" | "Low (Protective)"


class CountyContextResponse(BaseModel):
    """The fully assembled county context string used by the chatbot."""
    fips:          str
    county_name:   str
    context_text:  str              # plain-text blob injected into every bot prompt
    graph_factors: List[GraphSeverityItem]  # Neo4j severity data (empty if offline)


class ChatRequest(BaseModel):
    fips:          str
    question:      str
    chat_history:  List[Dict[str, str]] = []


class ChatResponse(BaseModel):
    fips:         str
    question:     str
    answer:       str
    intent:       str   # "risk" | "care" | "mixed" | "greeting" | "fips_lookup" | "county_info"
    sources_used: int   # number of PubMed articles cited


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
    """
    if df_csv is None or df_csv.empty:
        raise HTTPException(status_code=500, detail="County dataset not loaded.")

    county_match = df_csv[df_csv['fips_str'] == str(fips)]
    if county_match.empty:
        raise HTTPException(status_code=404, detail=f"County FIPS {fips} not found.")

    county_name = county_match.iloc[0]['county_name']

    nodes_dict: Dict[str, Dict[str, Any]] = {}
    edges_list: List[Dict[str, Any]] = []

    if not driver:
        # Fallback response if DB driver is offline
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j Graph Database is not connected."
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

                if 'High Risk' in sev:
                    prio = 0
                elif 'Medium' in sev:
                    prio = 1
                else:
                    prio = 2

                sdoh_factors_list.append({
                    'factor_name': f['name'],
                    'category': f.get('category', 'SDoH'),
                    'value': val,
                    'severity': sev,
                    'priority': prio
                })

    # Pick top K SDoH factors
    sdoh_factors_list.sort(key=lambda x: x['priority'])
    top_factors = sdoh_factors_list[:top_k]

    for factor in top_factors:
        fname = factor['factor_name']
        val = factor['value']
        sev = factor['severity']
        n_id = f"sdoh_{fname}"

        if 'High Risk' in sev:
            color = '#ef4444'  # Red
        elif 'Low' in sev or 'Protective' in sev:
            color = '#10b981'  # Green
        else:
            color = '#f59e0b'  # Amber

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


# ══════════════════════════════════════════════════════════════════════════════
# TASK 1 + 3 — County Context endpoint (CSV + Neo4j severity wired together)
# ══════════════════════════════════════════════════════════════════════════════

def _build_graph_factors(fips: str) -> List[Dict]:
    """
    Query Neo4j for SDoH factor severity labels for a county.
    Returns a list of {factor_name, category, value, severity} dicts.
    Falls back to empty list if Neo4j is offline.
    """
    if not driver:
        return []
    cypher = """
    MATCH (c:County {fips: $fips})-[r:HAS_FACTOR]->(f:SDoHFactor)
    RETURN f.name AS factor_name,
           f.category AS category,
           r.value AS value,
           r.severity AS severity
    ORDER BY
      CASE r.severity
        WHEN 'High Risk' THEN 0
        WHEN 'Medium'    THEN 1
        ELSE                  2
      END
    """
    try:
        with driver.session() as session:
            result = session.run(cypher, fips=str(fips))
            return [dict(rec) for rec in result]
    except Exception:
        return []


def _assemble_county_context(fips: str) -> tuple[str, list, str, float, float, float, pd.DataFrame, pd.DataFrame]:
    """
    Centralised helper: gather all county data from CSV + Neo4j and
    build the context string used by the chatbot.

    Returns (context_text, graph_factors, county_name, population, income, svi, sdoh_df, health_df)
    """
    if df_csv is None or df_csv.empty:
        raise HTTPException(status_code=500, detail="County dataset not loaded.")

    match = df_csv[df_csv['fips_str'] == str(fips)]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"County FIPS {fips} not found.")

    row = match.iloc[0]

    # ── Overview fields ───────────────────────────────────────────
    c_name   = str(row['county_name'])
    c_state  = str(row['state_abbr'])
    c_pop    = int(row['population'])
    c_income = float(row['median_household_income']) if not pd.isna(row['median_household_income']) else None
    c_svi    = float(row['svi_overall'])             if not pd.isna(row['svi_overall'])             else None

    # ── SDoH factors ──────────────────────────────────────────────
    sdoh_config = [
        ("Poverty Rate",                  'poverty_rate',                "%",      15.10),
        ("Unemployment Rate",             'unemployment_rate',           "%",       5.16),
        ("No Vehicle Rate",               'no_vehicle_rate',             "%",       6.20),
        ("Internet Subscription Rate",    'internet_subscription_rate',  "%",      82.50),
        ("Lack of Health Insurance",      'lack_health_insurance',       "%",      11.57),
        ("Food Insecurity",               'food_insecurity',             "%",      16.87),
        ("Transportation Barrier",        'transportation_barrier',      "%",       9.23),
        ("Housing Insecurity",            'housing_insecurity',          "%",      13.66),
        ("Low Food Access Pct",           'low_access_population_pct_2019',"%",    24.30),
        ("SNAP Low Access Pct",           'snap_low_access_pct_2019',    "%",       7.89),
        ("Grocery Store Density (per 1k)",'grocery_stores_per_1000_2020',"per 1k", 0.21),
        ("Fast Food Density (per 1k)",    'fast_food_per_1000_2020',     "per 1k", 0.67),
    ]
    sdoh_rows = []
    for label, col, unit, us_avg in sdoh_config:
        val = float(row[col]) if not pd.isna(row[col]) else 0.0
        sdoh_rows.append((label, val, unit, us_avg))
    sdoh_df = pd.DataFrame(sdoh_rows,
                           columns=["SDoH Barrier Factor","County Value","Unit","US National Average"])

    # ── Health outcomes ───────────────────────────────────────────
    health_config = [
        ("Diabetes Prevalence",             'diabetes_prevalence',  11.13),
        ("Obesity Prevalence",              'obesity_prevalence',   37.67),
        ("High Blood Pressure Prevalence",  'high_bp_prevalence',   33.48),
        ("Physical Inactivity",             'physical_inactivity',  26.98),
        ("Smoking Prevalence",              'smoking_prevalence',   16.32),
        ("Heart Disease Prevalence",        'heart_disease_prevalence', 5.97),
        ("Poor Mental Health (14+ Days)",   'poor_mental_health',   18.61),
        ("Poor Physical Health (14+ Days)", 'poor_physical_health', 13.82),
    ]
    health_rows = []
    for label, col, us_avg in health_config:
        val = float(row[col]) if not pd.isna(row[col]) else 0.0
        health_rows.append((label, val, us_avg))
    health_df = pd.DataFrame(health_rows,
                              columns=["Health Condition","County Prevalence (%)","US National Avg (%)"])

    # ── Graph severity from Neo4j (Task 3) ────────────────────────
    graph_factors = _build_graph_factors(fips)

    # ── Build context string via bot helper ───────────────────────
    context_text = build_county_context(
        c_name, c_state, c_pop, c_income, c_svi, sdoh_df, health_df
    )

    # Enrich context with Neo4j severity annotations if available
    if graph_factors:
        context_text += "\nNeo4j Knowledge Graph — Factor Severity Labels:\n"
        for gf in graph_factors:
            sev   = gf.get("severity", "")
            fname = gf.get("factor_name", "")
            cat   = gf.get("category", "")
            val   = gf.get("value", 0)
            context_text += f"  - {fname} ({cat}): {val:.2f}  [{sev}]\n"

    return context_text, graph_factors, c_name, c_pop, c_income, c_svi, sdoh_df, health_df


@app.get(
    "/api/county/{fips}/context",
    response_model=CountyContextResponse,
    tags=["Chatbot"],
    summary="Get full county context for the RAG chatbot",
)
def get_county_context(fips: str):
    """
    Returns the fully assembled county context string that the chatbot
    injects into every system prompt.
    Combines:
      - County overview (CSV)
      - 12 SDoH barrier factors vs US avg (CSV)
      - 8 health outcome prevalences vs US avg (CSV)
      - Neo4j Knowledge Graph severity labels (Neo4j — empty if offline)
    """
    ctx, graph_factors, c_name, *_ = _assemble_county_context(fips)

    gf_models = [
        GraphSeverityItem(
            factor_name=g["factor_name"],
            category=g.get("category", "SDoH"),
            value=float(g.get("value", 0)),
            severity=g.get("severity", "Medium"),
        )
        for g in graph_factors
    ]

    return CountyContextResponse(
        fips=fips,
        county_name=c_name,
        context_text=ctx,
        graph_factors=gf_models,
    )


# ══════════════════════════════════════════════════════════════════════════════
# TASK 1 — /api/chat  (main chatbot endpoint)
# ══════════════════════════════════════════════════════════════════════════════

import re as _re

@app.post(
    "/api/chat",
    response_model=ChatResponse,
    tags=["Chatbot"],
    summary="Ask the RAG chatbot a question about a county",
)
def chat_with_bot(req: ChatRequest):
    """
    The central chatbot endpoint.  Accepts a FIPS code, a question, and
    optional prior chat history.

    Internally:
      1. Calls _assemble_county_context() to build the full county context
         from CSV data + Neo4j severity labels.
      2. Passes the context + question to ask_bot() in bot.py.
      3. Returns the formatted answer plus metadata.

    This means the Streamlit frontend only needs ONE POST call per user
    message — all data assembly happens server-side.
    """
    fips     = req.fips.strip()
    question = req.question.strip()

    if not question:
        raise HTTPException(status_code=422, detail="Question must not be empty.")

    # Build context from all data sources
    try:
        ctx, *_ = _assemble_county_context(fips)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context assembly failed: {e}")

    # Call the bot
    try:
        answer, _ = ask_bot(
            user_question  = question,
            county_context = ctx,
            chat_history   = req.chat_history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot error: {e}")

    # Detect intent label for the response metadata
    from bot import classify_intent
    intent = classify_intent(question)

    # Count PubMed links cited in the answer
    sources_used = len(set(_re.findall(
        r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", answer
    )))

    return ChatResponse(
        fips         = fips,
        question     = question,
        answer       = answer,
        intent       = intent,
        sources_used = sources_used,
    )
