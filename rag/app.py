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
import re
import json
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from mcp_client import search_pubmed_sync   # kept for fallback path
from bot import ask_bot, build_county_context, classify_intent

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

# Custom CSS for premium glassmorphism styling
st.markdown("""
<style>
    /* Global Styles & Animations */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background & Text */
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #0f172a 40%, #020617);
        color: #f8fafc;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Premium Headers */
    h1, h2, h3, h4, h5, h6 {
        background: linear-gradient(to right, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Glassmorphism Metrics */
    .stMetric {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .stMetric:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px 0 rgba(96, 165, 250, 0.15);
        border-color: rgba(96, 165, 250, 0.3);
    }

    /* Chat Message Bubbles */
    div[data-testid="stChatMessage"] {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        animation: fadeIn 0.4s ease-out forwards;
        color: #f8fafc !important;
    }
    div[data-testid="stChatMessage"] * {
        color: #f8fafc !important;
        font-size: 1.05rem;
        line-height: 1.6;
    }

    /* User Message distinct style */
    div[data-testid="stChatMessage"][data-baseweb="flex"]:has([alt="user"]) {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(30, 41, 59, 0.6));
        border-color: rgba(59, 130, 246, 0.3);
    }

    /* Chat Input Bar */
    div[data-testid="stChatInput"] {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
    }

    /* Inputs & Selectboxes */
    .stSelectbox div[data-baseweb="select"], .stTextInput input {
        background-color: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 8px !important;
        transition: all 0.3s ease;
    }
    .stSelectbox div[data-baseweb="select"]:hover, .stTextInput input:hover {
        border-color: #3b82f6 !important;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6);
        color: white;
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)


# --- DATA & API CLIENT FUNCTIONS ---

@st.cache_data(ttl=60)
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

# --- MAIN INTERFACE ---
st.title("Social Determinants of Health (SDoH) RAG Assistant")
st.markdown("Chat with our AI Assistant to explore county-level socioeconomic barriers and receive evidence-based interventions via **PubMed**.")

# Selection Controls in Sidebar
st.sidebar.markdown("### County Selection")
# Load county list for autocomplete (from FastAPI if available, else pandas)
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

input_fips = st.sidebar.text_input("Enter County FIPS Code:", value="1001", help="e.g. 1001 for Autauga County, AL")
selected_county_option = st.sidebar.selectbox("Or Select County by Name:", options=county_options, index=default_idx)
selected_fips_from_dropdown = selected_county_option.split("(")[-1].replace(")", "").strip()

# Resolve active FIPS code
if input_fips != "1001" and input_fips in df_csv['fips_str'].values:
    active_fips = input_fips
else:
    active_fips = selected_fips_from_dropdown

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

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Active County:** {c_name}, {c_state}")
st.sidebar.markdown(f"**Population:** {int(c_pop):,}")
if c_income and not pd.isna(c_income):
    st.sidebar.markdown(f"**Median Income:** ${c_income:,.0f}")

st.caption("Powered by NVIDIA NIM · Neo4j Aura Knowledge Graph · PubMed MCP · FastAPI REST")

# --- BACKGROUND DATA RETRIEVAL ---
# We retrieve SDoH and Health Outcomes silently to use as context for the RAG Assistant
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


# --- RAG CHATBOT WIDGET ---

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ── Header row ────────────────────────────────────────────────────────────────
col_title, col_clear = st.columns([8, 1])
with col_title:
    intent_icon = "🧠"
    st.markdown(f"##### {intent_icon} NVIDIA AI Assistant — Analysing {c_name}, {c_state}")
with col_clear:
    if st.button("🗑️ Clear", key="clear_chat"):
        st.session_state.chat_messages = []
        st.rerun()

# ── Build county context string (shared by every turn) ────────────────────────
county_context = build_county_context(
    c_name, c_state, c_pop, c_income, c_svi, sdoh_df, health_df
)

# ── Routing hint banner ───────────────────────────────────────────────────────
st.markdown(
    """
    <div style="
        background: rgba(99,102,241,0.15);
        border: 1px solid rgba(99,102,241,0.35);
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 12px;
        font-size: 0.88rem;
        color: #c7d2fe;
    ">
    💡 <b>Smart routing active:</b>
    &nbsp;Ask about <b>risk factors / data</b> → answered from the Knowledge Graph.
    &nbsp;Ask about <b>care, treatment, or interventions</b> → searches PubMed for evidence.
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Chat display ──────────────────────────────────────────────────────────────
chat_container = st.container(height=520)
with chat_container:
    for msg in st.session_state.chat_messages:
        if msg["role"] in ("user", "assistant"):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
if user_query := st.chat_input("Ask about risk factors, care, interventions, or county health data…"):

    # Show user message immediately
    st.session_state.chat_messages.append({"role": "user", "content": user_query})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_query)

    # Show assistant placeholder while working
    with chat_container:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("⏳ *Thinking…*")

            # Live status updates fed back into the same placeholder
            def update_status(msg: str):
                # Remap ASCII prefixes (used in bot.py for console safety)
                # back to friendly emoji for Streamlit display
                msg = (msg
                    .replace("[KG]",      "🔍")
                    .replace("[BOT]",     "📋")
                    .replace("[PubMed]",  "📚")
                    .replace("[Writing]", "✍️")
                    .replace(">>",        "🧠")
                )
                placeholder.markdown(msg)

            try:
                # ── Call the NVIDIA bot ───────────────────────────────────────
                answer, updated_history = ask_bot(
                    user_question    = user_query,
                    county_context   = county_context,
                    chat_history     = [
                        m for m in st.session_state.chat_messages
                        if m["role"] in ("user", "assistant")
                    ][:-1],          # exclude the message we just appended
                    status_callback  = update_status,
                )

                # Render the final formatted answer
                placeholder.markdown(answer)

                # Persist only user + assistant display messages
                st.session_state.chat_messages = [
                    m for m in st.session_state.chat_messages
                    if m["role"] in ("user", "assistant")
                    and m not in [{"role": "user", "content": user_query}]
                ]
                # Re-attach current user message + new assistant answer
                st.session_state.chat_messages.append(
                    {"role": "user", "content": user_query}
                )
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as exc:
                # ── Graceful fallback: direct KG context + raw PubMed ────────
                intent = classify_intent(user_query)
                fallback_parts = []

                fallback_parts.append(
                    f"⚠️ *NVIDIA API unavailable ({type(exc).__name__}). "
                    f"Showing direct data instead.*\n"
                )

                # Always show elevated risk factors from the KG context
                elevated = []
                if sdoh_df is not None and not sdoh_df.empty:
                    for _, row in sdoh_df.iterrows():
                        try:
                            val    = float(row.get("County Value", 0))
                            us_avg = float(row.get("US National Average", 0))
                            if val > us_avg:
                                elevated.append({
                                    "factor": row.get("SDoH Barrier Factor", ""),
                                    "val":    val,
                                    "avg":    us_avg,
                                    "diff":   val - us_avg,
                                    "unit":   row.get("Unit", ""),
                                })
                        except Exception:
                            pass
                elevated.sort(key=lambda x: x["diff"], reverse=True)

                if elevated:
                    fallback_parts.append(f"### ⚠️ Elevated Risk Factors in {c_name}\n")
                    for r in elevated[:5]:
                        fallback_parts.append(
                            f"- **{r['factor']}**: {r['val']}{r['unit']} "
                            f"(US avg: {r['avg']}{r['unit']}, "
                            f"+{r['diff']:.1f} above average)\n"
                        )

                # If care/mixed, still try PubMed directly
                if intent in ("care", "mixed"):
                    try:
                        update_status("📚 *Falling back to direct PubMed search…*")
                        pubmed_raw = search_pubmed_sync(
                            f"{user_query} {c_name}", max_results=3
                        )
                        if pubmed_raw and "Error" not in pubmed_raw:
                            fallback_parts.append(
                                "\n### 📚 PubMed Search Results\n"
                            )
                            for block in pubmed_raw.split("\n\n"):
                                block = block.strip()
                                if not block:
                                    continue
                                pmid_m = re.search(r"PMID[:\s]+(\d+)", block)
                                lines  = [l.strip() for l in block.split("\n") if l.strip()]
                                title  = lines[1] if len(lines) > 1 else lines[0]
                                title  = title.split("doi:")[0].strip()
                                if pmid_m:
                                    pmid = pmid_m.group(1)
                                    fallback_parts.append(
                                        f"**{title}**  \n"
                                        f"[Read on PubMed (PMID {pmid})]"
                                        f"(https://pubmed.ncbi.nlm.nih.gov/{pmid}/)\n\n"
                                    )
                                else:
                                    fallback_parts.append(f"**{title}**\n\n")
                    except Exception as mcp_exc:
                        fallback_parts.append(
                            f"\n*PubMed search also failed: {mcp_exc}*\n"
                        )

                fallback_answer = "\n".join(fallback_parts)
                placeholder.markdown(fallback_answer)

                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": fallback_answer}
                )

