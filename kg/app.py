import os
import streamlit as st
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile

# Page configuration
st.set_page_config(
    page_title="SDoH Knowledge Graph Explorer",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000").rstrip("/")

# Custom CSS for dark glassmorphism styling
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stMetric {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(30, 41, 59, 0.5);
        border-radius: 8px;
        padding: 8px 16px;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
    }
    .css-1r6594q {
        background-color: #1e293b;
    }
</style>
""", unsafe_allow_html=True)


# --- DATA & API CLIENT FUNCTIONS ---

def check_fastapi_health(api_url):
    """Checks if FastAPI backend server is online."""
    try:
        resp = requests.get(f"{api_url}/health", timeout=2.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


@st.cache_data
def load_csv_data():
    """Loads CSV locally (Fallback mode)."""
    csv_path = os.path.join(os.path.dirname(__file__), "src", "SDOH_MODEL_DATA.csv")
    df = pd.read_csv(csv_path)
    df['fips_str'] = df['county_fips'].astype(int).astype(str)
    return df


@st.cache_resource
def get_neo4j_driver(uri, user, pwd):
    """Cached driver connection to Neo4j Aura (Fallback mode)."""
    try:
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        driver.verify_connectivity()
        return driver
    except Exception:
        return None


# Helper functions to query FastAPI backend REST API
def fetch_counties_from_api(api_url):
    try:
        resp = requests.get(f"{api_url}/api/counties", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def fetch_county_overview_from_api(api_url, fips):
    try:
        resp = requests.get(f"{api_url}/api/county/{fips}", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def fetch_graph_from_api(api_url, fips):
    try:
        resp = requests.get(f"{api_url}/api/county/{fips}/graph", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            # Normalize field names for Pyvis (from_node -> from, to_node -> to)
            nodes = data.get('nodes', [])
            edges = []
            for e in data.get('edges', []):
                e_copy = dict(e)
                if 'from_node' in e_copy:
                    e_copy['from'] = e_copy.pop('from_node')
                if 'to_node' in e_copy:
                    e_copy['to'] = e_copy.pop('to_node')
                edges.append(e_copy)
            return nodes, edges
    except Exception:
        pass
    return None, None


def fetch_sdoh_from_api(api_url, fips):
    try:
        resp = requests.get(f"{api_url}/api/county/{fips}/sdoh", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def fetch_health_from_api(api_url, fips):
    try:
        resp = requests.get(f"{api_url}/api/county/{fips}/health-outcomes", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# Fallback Direct Neo4j Query Function
def query_county_graph_direct(driver, fips):
    nodes = {}
    edges = []
    sdoh_factors_list = []
    
    cypher_query = """
    MATCH (c:County {fips: $fips})-[r:HAS_FACTOR]->(f:SDoHFactor)
    OPTIONAL MATCH (c)-[:IN_STATE]->(s:State)
    RETURN c, s, r, f
    """
    
    with driver.session() as session:
        result = session.run(cypher_query, fips=str(fips))
        for record in result:
            c = record['c']
            s = record['s']
            r = record['r']
            f = record['f']
            
            if 'County' not in nodes:
                nodes['County'] = {
                    'id': f"county_{c['fips']}",
                    'label': c['name'],
                    'type': 'County',
                    'color': '#6366f1',
                    'size': 42,
                    'title': f"<b>{c['name']}</b><br>FIPS: {c['fips']}<br>Population: {c['population']:,}<br>Income: ${c['median_household_income']:,.0f}<br>SVI Score: {c['svi_overall']:.4f}"
                }
                
            if s and 'State' not in nodes:
                n_id = f"state_{s['abbr']}"
                nodes['State'] = {
                    'id': n_id,
                    'label': f"State: {s['abbr']}",
                    'type': 'State',
                    'color': '#3b82f6',
                    'size': 26,
                    'title': f"State: {s['abbr']}"
                }
                edges.append({
                    'from': nodes['County']['id'],
                    'to': n_id,
                    'label': 'IN_STATE',
                    'color': '#94a3b8',
                    'width': 2,
                    'dashes': True
                })
                
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

    sdoh_factors_list.sort(key=lambda x: x['priority'])
    top10_factors = sdoh_factors_list[:10]
    
    for factor in top10_factors:
        fname = factor['factor_name']
        val = factor['value']
        sev = factor['severity']
        n_id = f"sdoh_{fname}"
        
        if 'High Risk' in sev:
            color = '#ef4444'
        elif 'Low' in sev or 'Protective' in sev:
            color = '#10b981'
        else:
            color = '#f59e0b'
            
        nodes[n_id] = {
            'id': n_id,
            'label': f"{fname}\n({val:.1f})",
            'type': 'SDoHFactor',
            'color': color,
            'size': 30,
            'title': f"<b>SDoH Feature: {fname}</b><br>Category: {factor['category']}<br>Value: {val:.2f}<br>Severity: <b>{sev}</b>"
        }
        
        edges.append({
            'from': nodes['County']['id'],
            'to': n_id,
            'label': f"{val:.1f}",
            'color': color,
            'width': 3
        })
        
    return list(nodes.values()), edges


# Initialize Services & Fallbacks
api_health = check_fastapi_health(FASTAPI_URL)
use_fastapi = api_health is not None

df_csv = load_csv_data()
driver = get_neo4j_driver(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

# --- SIDEBAR STATUS ---
st.sidebar.title("🕸️ SDoH Control Panel")
st.sidebar.markdown("---")

# Service Status Badges
if use_fastapi:
    st.sidebar.success(f" FastAPI REST Backend Connected (`{FASTAPI_URL}`)")
else:
    st.sidebar.warning(f" FastAPI REST Server Offline (`{FASTAPI_URL}`). Using direct fallback mode.")

if api_health and api_health.get('db_connected'):
    st.sidebar.success(" Neo4j Aura Database Connected (via FastAPI)")
elif driver:
    st.sidebar.success(" Connected directly to Neo4j Aura")
else:
    st.sidebar.error(" Neo4j Aura Disconnected. Check `.env` settings.")

# Fixed internal graph configuration settings
physics_enabled = True

# --- MAIN INTERFACE ---
st.title("Social Determinants of Health (SDoH) Knowledge Graph")
st.markdown("Explore county-level socioeconomic barriers, infrastructure, food access, and chronic health outcomes powered by **FastAPI & Neo4j**.")

# Zipcode mapping / lookup dictionary
ZIP_TO_FIPS = {
    # Sample US Zipcodes mapped to County FIPS for instant lookup
    "36003": "1001", "36006": "1001", "36008": "1001", "36066": "1001", "36067": "1001", # Autauga County, AL
    "36507": "1003", "36526": "1003", "36532": "1003", "36535": "1003", "36580": "1003", # Baldwin County, AL
    "90001": "6037", "90012": "6037", "90210": "6037", "90401": "6037", "91101": "6037", # Los Angeles County, CA
    "94102": "6075", "94103": "6075", "94107": "6075", "94110": "6075", # San Francisco, CA
    "30301": "13121", "30303": "13121", "30305": "13121", "30309": "13121", # Fulton County, GA
    "10001": "36061", "10002": "36061", "10011": "36061", "10019": "36061", # New York County, NY
    "33101": "12086", "33139": "12086", "33140": "12086", # Miami-# Load county list for autocomplete (from FastAPI if available, else pandas)
api_counties = fetch_counties_from_api(FASTAPI_URL) if use_fastapi else None

if api_counties:
    county_options = [c['display_label'] for c in api_counties]
else:
    county_options = df_csv.apply(lambda r: f"{r['county_name']} ({r['fips_str']})", axis=1).tolist()

default_idx = 0
for idx, opt in enumerate(county_options):
    if "(1001)" in opt:
        default_idx = idx
        break

selected_county_option = st.selectbox("Select County by Name or FIPS:", options=county_options, index=default_idx)
active_fips = selected_county_option.split("(")[-1].replace(")", "").strip()
strip()
        st.session_state['fips_selection'] = extracted

# Calculate current dropdown index based on session state
current_fips = st.session_state['fips_selection']
matched_idx = 0
for idx, opt in enumerate(county_options):
    if f"({current_fips})" in opt:
        matched_idx = idx
        break

with col_search1:
    st.text_input(
        "Enter FIPS or US Zipcode:",
        value=current_fips,
        key="user_search_input",
        on_change=on_input_change,
        help="Type a 5-digit US Zipcode (e.g., 90210) or 4-5 digit FIPS code (e.g., 1001)"
    )

with col_search2:
    st.selectbox(
        "Or Select County by Name:",
        options=county_options,
        index=matched_idx,
        key="user_dropdown_select",
        on_change=on_dropdown_change
    )

active_fips = st.session_state['fips_selection']

# Fetch County Overview Data
api_overview = fetch_county_overview_from_api(FASTAPI_URL, active_fips) if use_fastapi else None

if api_overview:
    c_name = api_overview['county_name']
    c_state = api_overview['state_abbr']
    c_pop = api_overview['population']
    c_income = api_overview['median_household_income']
    c_svi = api_overview['svi_overall']
else:
    county_info = df_csv[df_csv['fips_str'] == active_fips]
    if county_info.empty:
        st.error(f"County FIPS `{active_fips}` not found in dataset.")
        st.stop()
    c_row = county_info.iloc[0]
    c_name = c_row['county_name']
    c_state = c_row['state_abbr']
    c_pop = c_row['population']
    c_income = c_row['median_household_income']
    c_svi = c_row['svi_overall']

# --- KPI METRICS HEADER ---
st.markdown("### 📌 County Overview")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("County Name", c_name)
m2.metric("State", c_state)
m3.metric("Population", f"{int(c_pop):,}")
m4.metric("Median Income", f"${c_income:,.0f}" if c_income and not pd.isna(c_income) else "N/A")
m5.metric("SVI Score (Overall)", f"{c_svi:.4f}" if c_svi and not pd.isna(c_svi) else "N/A")

st.markdown("---")

# --- TABBED LAYOUT ---
tab_graph, tab_sdoh, tab_health = st.tabs([
    "🕸️ Interactive Knowledge Graph",
    "📊 SDoH Risk Factors",
    "🩺 Health Outcomes"
])

with tab_graph:
    st.markdown("#### 🔍 Top 10 SDoH Factors Knowledge Graph")
    st.caption("Clean, interactive radial graph showing the central County node connected to its State and the Top 10 SDoH features affecting this county.")

    nodes, edges = None, None

    # Try fetching graph via FastAPI REST API first
    if use_fastapi:
        nodes, edges = fetch_graph_from_api(FASTAPI_URL, active_fips)

    # Fallback to direct Neo4j query if FastAPI graph was not fetched
    if not nodes and driver:
        nodes, edges = query_county_graph_direct(driver, active_fips)

    if not nodes:
        st.warning(f"No graph data returned for FIPS `{active_fips}`. Ensure Neo4j Aura and `ingest.py` have been executed.")
    else:
        # Build Pyvis Network
        net = Network(height="650px", width="100%", bgcolor="#0f172a", font_color="#ffffff", heading="")
        net.options.physics.enabled = physics_enabled
        
        net.barnes_hut(
            gravity=-8000,
            central_gravity=0.3,
            spring_length=150,
            spring_strength=0.05,
            damping=0.09
        )
        
        for node in nodes:
            net.add_node(
                node['id'],
                label=node['label'],
                color=node['color'],
                size=node['size'],
                title=node['title']
            )
            
        for edge in edges:
            net.add_edge(
                edge['from'],
                edge['to'],
                label=edge.get('label', ''),
                color=edge['color'],
                width=edge.get('width', 2),
                dashes=edge.get('dashes', False),
                title=edge.get('title', '')
            )
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
            net.save_graph(tmp_file.name)
            tmp_file.seek(0)
            html_content = tmp_file.read().decode('utf-8')
            
        components.html(html_content, height=680, scrolling=False)
        
        st.markdown("""
        **Node Legend:** 
        🟣 **County** (Center) &nbsp;|&nbsp; 🔵 **State** &nbsp;|&nbsp; 🟢 **Low Risk / Protective SDoH** &nbsp;|&nbsp; 🟡 **Medium SDoH** &nbsp;|&nbsp; 🔴 **High Risk SDoH**
        <br>
        **Edge Legend:** 
        ─── Colored Line: Direct SDoH Feature Impact (Showing raw value) &nbsp;|&nbsp; 🟦 Dashed Line: State Link
        """, unsafe_allow_html=True)

with tab_sdoh:
    st.markdown(f"#### 📊 SDoH Barriers Breakdown for {c_name}")
    
    api_sdoh = fetch_sdoh_from_api(FASTAPI_URL, active_fips) if use_fastapi else None
    
    if api_sdoh:
        sdoh_df = pd.DataFrame(api_sdoh)
        sdoh_df.rename(columns={
            "factor_name": "SDoH Barrier Factor",
            "county_value": "County Value",
            "unit": "Unit",
            "us_avg": "US National Average",
            "difference": "Difference vs US Avg"
        }, inplace=True)
    else:
        county_info = df_csv[df_csv['fips_str'] == active_fips]
        c_row = county_info.iloc[0]
        sdoh_display = [
            ("Poverty Rate", c_row['poverty_rate'], "%", 15.1),
            ("Unemployment Rate", c_row['unemployment_rate'], "%", 5.16),
            ("No Vehicle Rate", c_row['no_vehicle_rate'], "%", 6.20),
            ("Internet Subscription Rate", c_row['internet_subscription_rate'], "%", 82.5),
            ("Lack of Health Insurance", c_row['lack_health_insurance'], "%", 11.57),
            ("Food Insecurity", c_row['food_insecurity'], "%", 16.87),
            ("Transportation Barrier", c_row['transportation_barrier'], "%", 9.23),
            ("Housing Insecurity", c_row['housing_insecurity'], "%", 13.66),
            ("Low Food Access Pct", c_row['low_access_population_pct_2019'], "%", 24.30),
            ("SNAP Low Access Pct", c_row['snap_low_access_pct_2019'], "%", 7.89),
            ("Grocery Store Density (per 1k)", c_row['grocery_stores_per_1000_2020'], "per 1k", 0.21),
            ("Fast Food Density (per 1k)", c_row['fast_food_per_1000_2020'], "per 1k", 0.67)
        ]
        sdoh_df = pd.DataFrame(sdoh_display, columns=["SDoH Barrier Factor", "County Value", "Unit", "US National Average"])
        sdoh_df["Difference vs US Avg"] = sdoh_df["County Value"] - sdoh_df["US National Average"]

    st.dataframe(sdoh_df.style.format({
        "County Value": "{:.2f}",
        "US National Average": "{:.2f}",
        "Difference vs US Avg": "{:+.2f}"
    }), use_container_width=True)

with tab_health:
    st.markdown(f"#### 🩺 Chronic Health Outcomes Prevalence for {c_name}")
    
    api_health_outcomes = fetch_health_from_api(FASTAPI_URL, active_fips) if use_fastapi else None

    if api_health_outcomes:
        health_df = pd.DataFrame(api_health_outcomes)
        health_df.rename(columns={
            "condition_name": "Health Condition",
            "county_prevalence": "County Prevalence (%)",
            "us_avg": "US National Avg (%)",
            "difference": "Difference vs US Avg (%)"
        }, inplace=True)
    else:
        county_info = df_csv[df_csv['fips_str'] == active_fips]
        c_row = county_info.iloc[0]
        health_display = [
            ("Diabetes Prevalence", c_row['diabetes_prevalence'], 11.13),
            ("Obesity Prevalence", c_row['obesity_prevalence'], 37.67),
            ("High Blood Pressure Prevalence", c_row['high_bp_prevalence'], 33.48),
            ("Physical Inactivity", c_row['physical_inactivity'], 26.98),
            ("Smoking Prevalence", c_row['smoking_prevalence'], 16.32),
            ("Heart Disease Prevalence", c_row['heart_disease_prevalence'], 5.97),
            ("Poor Mental Health (14+ Days)", c_row['poor_mental_health'], 18.61),
            ("Poor Physical Health (14+ Days)", c_row['poor_physical_health'], 13.82)
        ]
        health_df = pd.DataFrame(health_display, columns=["Health Condition", "County Prevalence (%)", "US National Avg (%)"])
        health_df["Difference vs US Avg (%)"] = health_df["County Prevalence (%)"] - health_df["US National Avg (%)"]

    st.dataframe(health_df.style.format({
        "County Prevalence (%)": "{:.2f}%",
        "US National Avg (%)": "{:.2f}%",
        "Difference vs US Avg (%)": "{:+.2f}%"
    }), use_container_width=True)

st.caption("Powered by FastAPI REST API & Neo4j Aura Graph Database | SDOH Knowledge Graph Project")