import os
import streamlit as st
import pandas as pd
import numpy as np
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

@st.cache_data
def load_csv_data():
    """Loads CSV for county search autocompletion."""
    df = pd.read_csv(r"d:\KNOW GRAPH ANTYGRA\SDOH_MODEL_DATA.csv")
    df['fips_str'] = df['county_fips'].astype(int).astype(str)
    return df

@st.cache_resource
def get_neo4j_driver(uri, user, pwd):
    """Cached driver connection to Neo4j Aura."""
    try:
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        # Verify connectivity
        driver.verify_connectivity()
        return driver
    except Exception as e:
        return None

df_csv = load_csv_data()
driver = get_neo4j_driver(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

# --- SIDEBAR ---
st.sidebar.title("🕸️ SDoH Graph Control")
st.sidebar.markdown("---")

# Database status
if driver:
    st.sidebar.success(f" Connected to Neo4j Aura")
    st.sidebar.caption(f"**URI:** `{NEO4J_URI}`")
else:
    st.sidebar.error(" Failed to connect to Neo4j Aura. Check `.env` settings.")

# Fixed internal graph configuration settings
min_correlation = 0.40
show_correlation_edges = False
physics_enabled = True

# --- MAIN INTERFACE ---
st.title("Social Determinants of Health (SDoH) Knowledge Graph")
st.markdown("Explore how county-level socioeconomic barriers, infrastructure, and food access correlate with chronic health outcomes.")

# Selection Controls
col_search1, col_search2 = st.columns([1, 2])

with col_search1:
    # Direct FIPS Input
    input_fips = st.text_input("Enter County FIPS Code:", value="1001", help="e.g. 1001 for Autauga County, AL")

with col_search2:
    # Autocomplete Dropdown
    county_options = df_csv.apply(lambda r: f"{r['county_name']} ({r['fips_str']})", axis=1).tolist()
    
    # Default index for Autauga County (1001)
    default_idx = 0
    for idx, opt in enumerate(county_options):
        if "(1001)" in opt:
            default_idx = idx
            break
            
    selected_county_option = st.selectbox("Or Select County by Name:", options=county_options, index=default_idx)
    selected_fips_from_dropdown = selected_county_option.split("(")[-1].replace(")", "").strip()

# Resolve FIPS code (Prioritize manual FIPS if modified, else dropdown)
if input_fips != "1001" and input_fips in df_csv['fips_str'].values:
    active_fips = input_fips
else:
    active_fips = selected_fips_from_dropdown

# Retrieve County Data from CSV
county_info = df_csv[df_csv['fips_str'] == active_fips]

if county_info.empty:
    st.error(f"County FIPS `{active_fips}` not found in dataset. Please enter a valid FIPS code.")
    st.stop()

c_row = county_info.iloc[0]

# --- KPI METRICS HEADER ---
st.markdown("### 📌 County Overview")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("County Name", c_row['county_name'])
m2.metric("State", c_row['state_abbr'])
m3.metric("Population", f"{int(c_row['population']):,}")
m4.metric("Median Income", f"${c_row['median_household_income']:,.0f}" if not pd.isna(c_row['median_household_income']) else "N/A")
m5.metric("SVI Score (Overall)", f"{c_row['svi_overall']:.4f}" if not pd.isna(c_row['svi_overall']) else "N/A")

st.markdown("---")

# Function to query Neo4j Graph for Active County
def query_county_graph(driver, fips):
    """
    Queries Neo4j Aura for the target county's node, connected State, 
    and the top 10 SDoH factors affecting that county.
    """
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
            
            # Central County Node
            if 'County' not in nodes:
                nodes['County'] = {
                    'id': f"county_{c['fips']}",
                    'label': c['name'],
                    'type': 'County',
                    'color': '#6366f1',
                    'size': 42,
                    'title': f"<b>{c['name']}</b><br>FIPS: {c['fips']}<br>Population: {c['population']:,}<br>Income: ${c['median_household_income']:,.0f}<br>SVI Score: {c['svi_overall']:.4f}"
                }
                
            # State Node
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
                
            # SDoH Factor
            if f:
                r_props = dict(r)
                val = r_props.get('value', 0)
                sev = r_props.get('severity', 'Medium')
                
                # Assign sort priority (High Risk > Medium > Low/Protective)
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

    # Sort factors by priority and pick top 10
    sdoh_factors_list.sort(key=lambda x: x['priority'])
    top10_factors = sdoh_factors_list[:10]
    
    # Add top 10 SDoH factor nodes and edges
    for factor in top10_factors:
        fname = factor['factor_name']
        val = factor['value']
        sev = factor['severity']
        n_id = f"sdoh_{fname}"
        
        if 'High Risk' in sev:
            color = '#ef4444' # Red
        elif 'Low' in sev or 'Protective' in sev:
            color = '#10b981' # Green
        else:
            color = '#f59e0b' # Amber
            
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

# --- TABBED LAYOUT ---
tab_graph, tab_sdoh, tab_health = st.tabs([
    "🕸️ Interactive Knowledge Graph",
    "📊 SDoH Risk Factors",
    "🩺 Health Outcomes"
])

with tab_graph:
    st.markdown("#### 🔍 Top 10 SDoH Factors Knowledge Graph")
    st.caption("Clean, interactive radial graph showing the central County node connected to its State and the Top 10 SDoH features affecting this county.")

    if driver:
        nodes, edges = query_county_graph(driver, active_fips)
        
        if not nodes:
            st.warning(f"No graph data returned from Neo4j Aura for FIPS `{active_fips}`. Make sure `ingest.py` has been executed.")
        else:
            # Build Pyvis Network
            net = Network(height="650px", width="100%", bgcolor="#0f172a", font_color="#ffffff", heading="")
            net.options.physics.enabled = physics_enabled
            
            # Configure BarnesHut physics for balanced layout
            net.barnes_hut(
                gravity=-8000,
                central_gravity=0.3,
                spring_length=150,
                spring_strength=0.05,
                damping=0.09
            )
            
            # Add nodes
            for node in nodes:
                net.add_node(
                    node['id'],
                    label=node['label'],
                    color=node['color'],
                    size=node['size'],
                    title=node['title']
                )
                
            # Add edges
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
                
            # Render HTML and display in Streamlit
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
                net.save_graph(tmp_file.name)
                tmp_file.seek(0)
                html_content = tmp_file.read().decode('utf-8')
                
            components.html(html_content, height=680, scrolling=False)
            
            # Legend
            st.markdown("""
            **Node Legend:** 
            🟣 **County** (Center) &nbsp;|&nbsp; 🔵 **State** &nbsp;|&nbsp; 🟢 **Low Risk / Protective SDoH** &nbsp;|&nbsp; 🟡 **Medium SDoH** &nbsp;|&nbsp; 🔴 **High Risk SDoH**
            <br>
            **Edge Legend:** 
            ─── Colored Line: Direct SDoH Feature Impact (Showing raw value) &nbsp;|&nbsp; 🟦 Dashed Line: State Link
            """, unsafe_allow_html=True)
    else:
        st.error("Neo4j driver is not connected. Please check your `.env` credentials.")

with tab_sdoh:
    st.markdown(f"#### 📊 SDoH Barriers Breakdown for {c_row['county_name']}")
    
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
    st.markdown(f"#### 🩺 Chronic Health Outcomes Prevalence for {c_row['county_name']}")
    
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

st.caption("Powered by Neo4j Aura Graph Database & Streamlit | SDOH Knowledge Graph Project")
