#!/usr/bin/env python3
"""
CareEquity SDOH Research Assistant - Streamlined Modern Streamlit Dashboard.
Connects to the FastAPI Backend (main.py) with seamless local fallback.
"""

import os
import sys
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
import streamlit as st

# Configure page metadata
st.set_page_config(
    page_title="CareEquity SDOH Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

from models.schemas import RiskCase, CompleteAnalysisReport
from workflow import run_sdoh_analysis
from config.settings import settings

# Backend API Configuration
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Custom CSS for modern compact styling
st.markdown("""
<style>
    .compact-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #0d9488 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .compact-header h2 {
        color: #ffffff;
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .compact-header p {
        color: #e2e8f0;
        margin: 0;
        font-size: 0.9rem;
    }
    .pipeline-strip {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px 14px;
        margin-bottom: 16px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        font-size: 0.8rem;
    }
    .pipeline-chip {
        background: #e0f2fe;
        color: #0369a1;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .intervention-card-compact {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #0d9488;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .alert-box-compact {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.9rem;
    }
    .api-badge {
        font-size: 0.8rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 12px;
    }
    .api-connected { background: #dcfce7; color: #166534; }
    .api-fallback { background: #fef3c7; color: #92400e; }
</style>
""", unsafe_allow_html=True)


def check_backend_status(backend_url: str) -> tuple[bool, Dict[str, Any]]:
    """Check if the FastAPI backend service is reachable."""
    try:
        resp = requests.get(f"{backend_url}/api/health", timeout=2)
        if resp.status_code == 200:
            return True, resp.json()
    except Exception:
        pass
    return False, {}


def fetch_presets_from_backend(backend_url: str) -> List[Dict[str, Any]]:
    """Fetch presets from FastAPI backend or return default presets."""
    try:
        resp = requests.get(f"{backend_url}/api/presets", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    return [
        {
            "case_id": "BRONX_DIABETES_001",
            "age": 54,
            "geography": "Bronx, NY",
            "risk_score": 85.0,
            "chronic_conditions": ["Type 2 Diabetes", "Essential Hypertension", "Obesity"],
            "transportation": True,
            "food_access": True,
            "housing": False,
            "economic_stability": True,
            "social_isolation": False
        },
        {
            "case_id": "BROOKLYN_CARDIAC_002",
            "age": 62,
            "geography": "Brooklyn, NY",
            "risk_score": 76.0,
            "chronic_conditions": ["Congestive Heart Failure", "Hypertension", "Atrial Fibrillation"],
            "transportation": True,
            "food_access": False,
            "housing": True,
            "economic_stability": True,
            "social_isolation": True
        },
        {
            "case_id": "MANHATTAN_ELDER_003",
            "age": 76,
            "geography": "Manhattan, NY",
            "risk_score": 92.0,
            "chronic_conditions": ["COPD", "Chronic Kidney Disease Stage 3", "Depression"],
            "transportation": True,
            "food_access": True,
            "housing": True,
            "economic_stability": True,
            "social_isolation": True
        },
        {
            "case_id": "CHICAGO_HTN_004",
            "age": 45,
            "geography": "Chicago, IL",
            "risk_score": 68.0,
            "chronic_conditions": ["Hypertension", "High Cholesterol"],
            "transportation": False,
            "food_access": True,
            "housing": False,
            "economic_stability": True,
            "social_isolation": False
        }
    ]


def call_backend_analysis(backend_url: str, patient_case: RiskCase) -> CompleteAnalysisReport:
    """Send analysis request to FastAPI backend with seamless local fallback."""
    try:
        payload = patient_case.model_dump()
        resp = requests.post(f"{backend_url}/api/analyze", json=payload, timeout=25)
        if resp.status_code == 200:
            return CompleteAnalysisReport.model_validate(resp.json())
    except Exception:
        pass

    # Local fallback execution
    return run_sdoh_analysis(patient_case)


def main():
    # Sidebar: Backend Connection & Patient Input
    with st.sidebar:
        st.subheader("🔌 Connection")
        backend_url = st.text_input("Backend URL", value=DEFAULT_BACKEND_URL, label_visibility="collapsed")
        is_connected, health_info = check_backend_status(backend_url)

        if is_connected:
            st.markdown('<span class="api-badge api-connected">🟢 FastAPI Backend Connected</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="api-badge api-fallback">🟡 Local Engine Mode</span>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📋 Patient Profile")

        presets_list = fetch_presets_from_backend(backend_url)
        preset_names = [f"{p['case_id']} - {p['geography']} ({p['age']}y)" for p in presets_list] + ["Custom Profile"]
        selected_name = st.selectbox("Preset Case", preset_names)

        if selected_name != "Custom Profile":
            idx = preset_names.index(selected_name)
            preset_data = presets_list[idx]

            case_id = st.text_input("Patient ID", value=preset_data.get("case_id", "PATIENT_001"))
            c_age, c_loc = st.columns(2)
            with c_age:
                age = st.number_input("Age", min_value=18, max_value=110, value=preset_data.get("age", 50))
            with c_loc:
                location = st.text_input("Location", value=preset_data.get("geography", "Bronx, NY"))
            
            risk_score = st.slider("Risk Score", 0.0, 100.0, float(preset_data.get("risk_score", 75.0)), 1.0)

            cond_options = [
                "Type 2 Diabetes", "Essential Hypertension", "Congestive Heart Failure",
                "COPD", "Asthma", "Obesity", "Depression", "Anxiety",
                "Chronic Kidney Disease Stage 3", "Atrial Fibrillation", "High Cholesterol"
            ]
            current_conds = preset_data.get("chronic_conditions", [])
            conditions = st.multiselect(
                "Conditions",
                cond_options,
                default=[c for c in current_conds if c in cond_options]
            )

            st.markdown("**SDOH Barriers**")
            b1, b2 = st.columns(2)
            with b1:
                trans = st.checkbox("Transportation", value=preset_data.get("transportation", False))
                food = st.checkbox("Food Insecurity", value=preset_data.get("food_access", False))
            with b2:
                housing = st.checkbox("Housing Strain", value=preset_data.get("housing", False))
                econ = st.checkbox("Financial Cost", value=preset_data.get("economic_stability", False))
            isolation = st.checkbox("Social Isolation", value=preset_data.get("social_isolation", False))

        else:
            case_id = st.text_input("Patient ID", value=f"PATIENT_{int(time.time())}")
            c_age, c_loc = st.columns(2)
            with c_age:
                age = st.number_input("Age", min_value=18, max_value=110, value=48)
            with c_loc:
                location = st.text_input("Location", value="Bronx, NY")
            
            risk_score = st.slider("Risk Score", 0.0, 100.0, 75.0, 1.0)

            cond_options = [
                "Type 2 Diabetes", "Essential Hypertension", "Congestive Heart Failure",
                "COPD", "Asthma", "Obesity", "Depression", "Anxiety",
                "Chronic Kidney Disease Stage 3", "Atrial Fibrillation", "High Cholesterol"
            ]
            conditions = st.multiselect("Conditions", cond_options, default=["Type 2 Diabetes", "Essential Hypertension"])

            st.markdown("**SDOH Barriers**")
            b1, b2 = st.columns(2)
            with b1:
                trans = st.checkbox("Transportation", value=True)
                food = st.checkbox("Food Insecurity", value=True)
            with b2:
                housing = st.checkbox("Housing Strain", value=False)
                econ = st.checkbox("Financial Cost", value=True)
            isolation = st.checkbox("Social Isolation", value=False)

        risk_level = "critical" if risk_score >= 80 else "high" if risk_score >= 60 else "moderate" if risk_score >= 40 else "low"

        st.markdown("---")
        analyze_btn = st.button("🚀 Analyze Patient", type="primary", use_container_width=True)

    # Main Area Logic
    patient_case = RiskCase(
        case_id=case_id,
        age=age,
        geography=location,
        risk_score=risk_score,
        risk_level=risk_level,
        chronic_conditions=conditions,
        transportation=trans,
        food_access=food,
        housing=housing,
        economic_stability=econ,
        social_isolation=isolation
    )

    # Initialize or fetch report from session state
    if analyze_btn or "current_report" not in st.session_state:
        with st.spinner("Analyzing across multi-agent live intelligence pipeline..."):
            report = call_backend_analysis(backend_url, patient_case)
            st.session_state["current_report"] = report

    report: CompleteAnalysisReport = st.session_state["current_report"]

    # Compact Header Banner
    st.markdown(f"""
    <div class="compact-header">
        <div>
            <h2>🏥 CareEquity SDOH Assistant</h2>
            <p>Patient Case #{report.case_id} • {report.geographic_analysis.location} • {', '.join(report.patient_profile.chronic_conditions[:2])}</p>
        </div>
        <div style="text-align:right;">
            <span style="background:rgba(255,255,255,0.2); padding:4px 12px; border-radius:12px; font-weight:600; font-size:0.9rem;">
                {report.patient_profile.risk_level.upper()} RISK ({report.patient_profile.risk_score:.0f}/100)
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top KPI Metrics Row (Compact)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Risk Level", f"{report.patient_profile.risk_score:.0f}/100", delta=report.patient_profile.risk_level.upper(), delta_color="inverse")
    with m2:
        barriers_count = sum([report.patient_profile.transportation, report.patient_profile.food_access, report.patient_profile.housing, report.patient_profile.economic_stability, report.patient_profile.social_isolation])
        st.metric("SDOH Barriers", f"{barriers_count} Active")
    with m3:
        st.metric("Live Disease Alerts", f"{len(report.live_surveillance.active_disease_alerts)} Active", delta=report.live_surveillance.location)
    with m4:
        st.metric("Response Time", f"{report.execution_time_seconds:.2f}s", delta="Parallel Engine")

    # Compact Pipeline Chips
    st.markdown("""
    <div class="pipeline-strip">
        <span class="pipeline-chip">✓ Agent 1: Health Analysis</span>
        <span class="pipeline-chip">✓ Agent 2: Geographic Profiling</span>
        <span class="pipeline-chip">✓ Agent 3: Local Safety Net</span>
        <span class="pipeline-chip" style="background:#fef3c7; color:#92400e;">🌐 Live Web Disease Surveillance</span>
        <span class="pipeline-chip" style="background:#dcfce7; color:#166534;">✓ Agent 4: Care Plan Synthesis</span>
    </div>
    """, unsafe_allow_html=True)

    # Streamlined Content Tabs
    tab_report, tab_interventions, tab_live, tab_resources, tab_geo = st.tabs([
        "📋 Clinical Care Plan",
        "💡 Targeted Interventions",
        "🌐 Live Disease Alerts",
        "📍 Local Safety Net",
        "🗺️ Area Demographics"
    ])

    with tab_report:
        c_title, c_btn = st.columns([4, 1])
        with c_title:
            st.markdown(f"**SDOH Action Plan** — Case `{report.case_id}`")
        with c_btn:
            st.download_button(
                label="📥 Download Plan (.md)",
                data=report.comprehensive_report,
                file_name=f"SDOH_Plan_{report.case_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
        st.markdown(report.comprehensive_report)

    with tab_interventions:
        st.markdown(f"### Recommended Interventions ({len(report.interventions)})")
        for i, item in enumerate(report.interventions, 1):
            with st.container():
                st.markdown(f"""
                <div class="intervention-card-compact">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <strong style="color:#0f766e; font-size:1.05rem;">{i}. {item.name}</strong>
                        <span style="background:#dbeafe; color:#1e40af; padding:2px 8px; border-radius:10px; font-size:0.75rem; font-weight:600;">{item.target_sdoh}</span>
                    </div>
                    <p style="margin:0 0 6px 0; font-size:0.9rem;">{item.description}</p>
                    <div style="font-size:0.85rem; color:#334155; margin-bottom:4px;">
                        • <strong>Action:</strong> {item.how_to_access}<br>
                        • <strong>Expected Outcome:</strong> {item.expected_outcome}<br>
                        • <strong>Contact:</strong> {item.contact_info} *(Timeline: {item.timeline})*
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab_live:
        st.markdown(f"### Live Disease Surveillance — {report.live_surveillance.location}")
        st.info(report.live_surveillance.surveillance_summary)

        l1, l2 = st.columns(2)
        with l1:
            st.markdown("**⚠️ Active Public Health & Disease Alerts**")
            for alert in report.live_surveillance.active_disease_alerts:
                st.markdown(f"""<div class="alert-box-compact">⚠️ {alert}</div>""", unsafe_allow_html=True)

            st.markdown("**📈 Local Health Trends**")
            for trend in report.live_surveillance.public_health_trends:
                st.markdown(f"- {trend}")

        with l2:
            st.markdown("**📰 Live Web News & Health Advisories**")
            if report.live_surveillance.recent_news_snippets:
                for item in report.live_surveillance.recent_news_snippets[:3]:
                    st.markdown(f"- **[{item.get('title', 'Health Advisory')}]({item.get('url', '#')})**")
                    if item.get('snippet'):
                        st.caption(item.get('snippet')[:120] + "...")
            else:
                st.caption("Active monitoring via regional public health baseline.")

    with tab_resources:
        st.markdown(f"### Local Community Resources — {report.local_resources.location}")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("**🏥 Clinics & Medical Centers**")
            for p in report.local_resources.healthcare_providers[:4]:
                st.markdown(f"- **{p}**")

            st.markdown("**🚌 Medical Transit Services**")
            for t in report.local_resources.transportation_programs[:3]:
                st.markdown(f"- {t}")

        with r2:
            st.markdown("**🍎 Food & Nutrition Programs**")
            for f in report.local_resources.food_nutrition_services[:3]:
                st.markdown(f"- {f}")

            st.markdown("**🚨 24/7 Crisis Helplines**")
            for name, num in report.local_resources.emergency_contacts.items():
                st.markdown(f"- **{name}:** `{num}`")

    with tab_geo:
        st.markdown(f"### Area Health Landscape — {report.geographic_analysis.location}")
        
        # 4 Metric badges
        demo = report.geographic_analysis.demographics
        stats = report.geographic_analysis.health_statistics
        
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            st.metric("Median Age", f"{demo.get('median_age', 36)} yrs")
        with g2:
            st.metric("Poverty Rate", f"{demo.get('poverty_rate', 18)}%")
        with g3:
            st.metric("Diabetes Rate", f"{stats.get('diabetes_rate', 12)}%")
        with g4:
            st.metric("Hypertension Rate", f"{stats.get('hypertension_rate', 35)}%")

        st.markdown("---")
        st.markdown(f"**Context:** {report.geographic_analysis.area_health_profile}")
        st.markdown(f"**Environmental Determinants:** {report.geographic_analysis.environmental_factors}")


if __name__ == "__main__":
    main()
