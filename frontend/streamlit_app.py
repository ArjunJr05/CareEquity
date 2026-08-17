"""
Streamlit Frontend for Health Risk Prediction Pipeline
======================================================
Interactive UI for testing disease risk prediction, knowledge graph queries, and RAG chatbot.
"""

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any, Optional

# ==================== Configuration ====================

API_BASE_URL = "http://localhost:8000"
DISEASES = ["diabetes", "hypertension", "heart_disease", "asthma"]

st.set_page_config(
    page_title="Health Risk Prediction",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Styling ====================

st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .risk-low { color: green; font-weight: bold; }
    .risk-medium { color: orange; font-weight: bold; }
    .risk-high { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==================== Helper Functions ====================

def check_api_health() -> bool:
    """Check if backend API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_risk_color(risk_level: str) -> str:
    """Get color for risk level."""
    colors = {
        "Low": "🟢",
        "Medium": "🟡",
        "High": "🔴",
        "Very High": "🔴"
    }
    return colors.get(risk_level, "⚪")

def format_risk_score(score: float) -> str:
    """Format risk score as percentage."""
    return f"{score * 100:.1f}%"

# ==================== Sidebar Setup ====================

st.sidebar.title("🏥 Health Risk Prediction Pipeline")
st.sidebar.markdown("---")

# API Status
api_status = check_api_health()
if api_status:
    st.sidebar.success("✅ Backend API Connected")
else:
    st.sidebar.error("❌ Backend API Not Available")
    st.sidebar.info("Start the backend with: `python main.py`")

st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Select Module",
    ["🔍 Quick Prediction", "📊 Full Analysis", "💬 Health Chatbot", "📈 SDOH Data", "ℹ️ About"]
)

# Settings
st.sidebar.markdown("---")
st.sidebar.subheader("Settings")
api_url_custom = st.sidebar.checkbox("Custom API URL")
if api_url_custom:
    api_url = st.sidebar.text_input("API URL", value=API_BASE_URL)
else:
    api_url = API_BASE_URL

# ==================== Page: Quick Prediction ====================

if page == "🔍 Quick Prediction":
    st.title("🔍 Quick Risk Prediction")
    st.markdown("Quickly assess disease risk based on health metrics")
    
    with st.form("quick_predict_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Personal Information")
            member_id = st.text_input("Member ID", value="M001")
            age = st.slider("Age", 18, 100, 45)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            
        with col2:
            st.subheader("Health Metrics")
            height_cm = st.number_input("Height (cm)", 140, 220, 175)
            weight_kg = st.number_input("Weight (kg)", 40, 200, 85)
            bmi = st.number_input("BMI", 10.0, 60.0, (weight_kg / ((height_cm / 100) ** 2)))
            
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("Lab Values")
            glucose_mg_dl = st.number_input("Glucose (mg/dL)", 50, 400, 100)
            hba1c = st.number_input("HbA1c (%)", 3.0, 15.0, 5.5)
            
        with col4:
            st.subheader("Additional")
            cholesterol = st.number_input("Cholesterol (mg/dL)", 100, 400, 200)
            smoking = st.selectbox("Smoking Status", ["Non-Smoker", "Former Smoker", "Smoker"])
            zipcode = st.text_input("Zipcode", value="84620")
        
        submitted = st.form_submit_button("🚀 Predict Risk", use_container_width=True)
    
    if submitted and api_status:
        with st.spinner("Analyzing health data..."):
            try:
                payload = {
                    "member_id": member_id,
                    "health_metrics": {
                        "age": age,
                        "gender": gender,
                        "zipcode": zipcode,
                        "height_cm": height_cm,
                        "weight_kg": weight_kg,
                        "bmi": bmi,
                        "glucose_mg_dl": glucose_mg_dl,
                        "hba1c_percent": hba1c,
                        "total_cholesterol_mg_dl": cholesterol,
                        "smoking_history": smoking
                    },
                    "year": 2023
                }
                
                response = requests.post(
                    f"{api_url}/api/v1/quick-predict",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    st.success("✅ Prediction Complete")
                    
                    # Display risk scores
                    st.subheader("Risk Scores by Disease")
                    
                    cols = st.columns(len(DISEASES))
                    for i, disease in enumerate(DISEASES):
                        with cols[i]:
                            if disease in data.get("risk_scores", {}):
                                risk_data = data["risk_scores"][disease]
                                risk_score = risk_data.get("risk_score", 0)
                                risk_level = risk_data.get("risk_level", "Unknown")
                                confidence = risk_data.get("confidence", 0)
                                
                                st.metric(
                                    disease.replace("_", " ").title(),
                                    format_risk_score(risk_score),
                                    f"{get_risk_color(risk_level)} {risk_level}",
                                    delta=f"Confidence: {confidence*100:.0f}%"
                                )
                    
                    # Display as table
                    st.subheader("Detailed Results")
                    risk_df = pd.DataFrame([
                        {
                            "Disease": d.replace("_", " ").title(),
                            "Risk Score": format_risk_score(data["risk_scores"][d]["risk_score"]),
                            "Risk Level": data["risk_scores"][d]["risk_level"],
                            "Confidence": f"{data['risk_scores'][d]['confidence']*100:.1f}%"
                        }
                        for d in DISEASES if d in data.get("risk_scores", {})
                    ])
                    st.dataframe(risk_df, use_container_width=True)
                    
                else:
                    st.error(f"API Error: {response.status_code}")
                    st.json(response.json())
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend API")
                st.info(f"Make sure backend is running at {api_url}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif submitted and not api_status:
        st.error("❌ Backend API is not available")


# ==================== Page: Full Analysis ====================

elif page == "📊 Full Analysis":
    st.title("📊 Full Analysis with Reasoning")
    st.markdown("Comprehensive prediction with risk factors and recommendations")
    
    with st.form("full_analysis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Patient Information")
            member_id = st.text_input("Member ID", value="M001")
            age = st.slider("Age", 18, 100, 45, key="fa_age")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="fa_gender")
            
        with col2:
            st.subheader("Health Metrics")
            height_cm = st.number_input("Height (cm)", 140, 220, 175, key="fa_height")
            weight_kg = st.number_input("Weight (kg)", 40, 200, 85, key="fa_weight")
            bmi = st.number_input("BMI", 10.0, 60.0, 27.8, key="fa_bmi")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("Lab & Vital Values")
            glucose = st.number_input("Glucose (mg/dL)", 50, 400, 105, key="fa_glucose")
            hba1c = st.number_input("HbA1c (%)", 3.0, 15.0, 5.8, key="fa_hba1c")
            cholesterol = st.number_input("Cholesterol (mg/dL)", 100, 400, 210, key="fa_cholesterol")
        
        with col4:
            st.subheader("Lifestyle & Location")
            smoking = st.selectbox("Smoking Status", ["Non-Smoker", "Former Smoker", "Smoker"], key="fa_smoking")
            zipcode = st.text_input("Zipcode", value="84620", key="fa_zipcode")
            include_reasoning = st.checkbox("Include Reasoning Chain", value=True)
            include_recommendations = st.checkbox("Include Recommendations", value=True)
        
        submitted = st.form_submit_button("🔬 Run Full Analysis", use_container_width=True)
    
    if submitted and api_status:
        with st.spinner("Running comprehensive analysis..."):
            try:
                payload = {
                    "health_report": {
                        "member_id": member_id,
                        "health_metrics": {
                            "age": age,
                            "gender": gender,
                            "zipcode": zipcode,
                            "height_cm": height_cm,
                            "weight_kg": weight_kg,
                            "bmi": bmi,
                            "glucose_mg_dl": glucose,
                            "hba1c_percent": hba1c,
                            "total_cholesterol_mg_dl": cholesterol,
                            "smoking_history": smoking
                        },
                        "year": 2023
                    },
                    "include_reasoning": include_reasoning,
                    "include_recommendations": include_recommendations
                }
                
                response = requests.post(
                    f"{api_url}/api/v1/predict",
                    json=payload,
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    prediction = result.get("prediction", {})
                    
                    st.success("✅ Analysis Complete")
                    
                    # Main prediction
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Member ID", member_id)
                    with col2:
                        st.metric("Risk Score", format_risk_score(prediction.get("risk_score", 0)))
                    with col3:
                        st.metric("Risk Level", f"{get_risk_color(prediction.get('risk_level', 'Unknown'))} {prediction.get('risk_level', 'Unknown')}")
                    with col4:
                        st.metric("Confidence", f"{prediction.get('confidence', 0)*100:.0f}%")
                    
                    # Top Risk Factors
                    if prediction.get("top_risk_factors"):
                        st.subheader("🎯 Top Risk Factors")
                        factors_data = []
                        for factor in prediction.get("top_risk_factors", []):
                            factors_data.append({
                                "Factor": factor.get("factor_name", "Unknown"),
                                "Category": factor.get("factor_category", "Unknown"),
                                "Contribution": f"{factor.get('risk_contribution', 0)*100:.1f}%",
                                "Evidence": factor.get("evidence_strength", "Unknown")
                            })
                        st.dataframe(pd.DataFrame(factors_data), use_container_width=True)
                    
                    # Recommendations
                    if include_recommendations and result.get("recommendations"):
                        st.subheader("💡 Recommendations")
                        for i, rec in enumerate(result.get("recommendations", []), 1):
                            st.info(f"{i}. {rec}")
                    
                    # Health Guidelines
                    if result.get("health_guidelines"):
                        st.subheader("📋 Health Guidelines")
                        for guideline in result.get("health_guidelines", []):
                            st.success(guideline)
                    
                    # Raw JSON
                    if st.checkbox("Show Raw Response"):
                        st.json(result)
                    
                else:
                    st.error(f"API Error: {response.status_code}")
                    st.json(response.json())
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif submitted and not api_status:
        st.error("❌ Backend API is not available")


# ==================== Page: Health Chatbot ====================

elif page == "💬 Health Chatbot":
    st.title("💬 Health Information Chatbot")
    st.markdown("Ask questions about health conditions, risk factors, and prevention")
    
    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])
    
    # Chat input
    user_input = st.chat_input("Ask a health question...")
    
    if user_input and api_status:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)
        
        # Get response
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{api_url}/api/v1/chat",
                    json={"role": "user", "content": user_input},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bot_response = data.get("response", "I couldn't generate a response.")
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": bot_response
                    })
                    st.chat_message("assistant").write(bot_response)
                    
                    # Show metadata
                    if st.checkbox("Show Sources"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Confidence", f"{data.get('confidence', 0)*100:.0f}%")
                        with col2:
                            st.metric("Source Type", data.get("source_type", "Unknown"))
                        
                        if data.get("references"):
                            st.markdown("**References:**")
                            for ref in data.get("references", []):
                                st.caption(f"- {ref}")
                else:
                    st.error("Failed to get response from chatbot")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif user_input and not api_status:
        st.error("❌ Backend API is not available")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()


# ==================== Page: SDOH Data ====================

elif page == "📈 SDOH Data":
    st.title("📈 Social Determinants of Health (SDOH)")
    st.markdown("View SDOH scores and statistics for a specific location")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        zipcode = st.text_input("Enter Zipcode", value="84620")
    
    with col2:
        if st.button("📍 Get SDOH Data", use_container_width=True):
            fetch_data = True
        else:
            fetch_data = False
    
    if fetch_data and api_status:
        with st.spinner("Fetching SDOH data..."):
            try:
                response = requests.get(
                    f"{api_url}/api/v1/sdoh/{zipcode}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    st.success(f"✅ SDOH Data for {zipcode}")
                    
                    # Display scores
                    st.subheader("SDOH Scores")
                    
                    sdoh_scores = data.get("sdoh_scores", {})
                    
                    cols = st.columns(3)
                    score_labels = [
                        ("Economic Stability", "economic_stability_score"),
                        ("Healthcare Access", "healthcare_access_quality_score"),
                        ("Education Access", "education_access_quality_score"),
                        ("Built Environment", "neighborhood_built_environment_score"),
                        ("Food Security", "food_security_score"),
                        ("Social Community", "social_community_context_score"),
                    ]
                    
                    for i, (label, key) in enumerate(score_labels):
                        with cols[i % 3]:
                            score = sdoh_scores.get(key, 0.5)
                            st.metric(label, f"{score:.2f}", delta=f"(0-1 scale)")
                    
                    # Statistics
                    if data.get("statistics"):
                        st.subheader("Statistics")
                        stats = data.get("statistics", {})
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Average SDOH Score", f"{stats.get('score_average', 0):.3f}")
                        with col2:
                            st.metric("Zipcode", stats.get("zipcode", "N/A"))
                    
                    # Display as chart
                    st.subheader("Score Visualization")
                    chart_data = pd.DataFrame([
                        {
                            "Factor": label.replace("_", " ").title(),
                            "Score": sdoh_scores.get(key, 0.5)
                        }
                        for label, key in score_labels
                    ])
                    st.bar_chart(chart_data.set_index("Factor"))
                    
                else:
                    st.error(f"Error: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif fetch_data and not api_status:
        st.error("❌ Backend API is not available")


# ==================== Page: About ====================

elif page == "ℹ️ About":
    st.title("ℹ️ About This Application")
    
    st.markdown("""
    ## Health Risk Prediction Pipeline
    
    An integrated platform for disease risk prediction combining machine learning, 
    knowledge graphs, and social determinants of health (SDOH).
    
    ### Features
    
    - **🔍 Quick Prediction**: Fast risk assessment for multiple diseases
    - **📊 Full Analysis**: Comprehensive prediction with risk factors and reasoning
    - **💬 Health Chatbot**: RAG-based Q&A for health information
    - **📈 SDOH Data**: Community health and social factors
    - **📱 Interactive UI**: Streamlit-based frontend
    
    ### Supported Diseases
    
    1. **Diabetes** - Metabolic disorder affecting blood sugar
    2. **Hypertension** - High blood pressure condition
    3. **Heart Disease** - Cardiovascular condition
    4. **Asthma** - Respiratory condition
    
    ### Backend Services
    
    - **ML Models**: Scikit-learn random forest classifiers
    - **Knowledge Graph**: Neo4j-based disease/factor relationships
    - **SDOH Data**: Community health metrics and statistics
    - **RAG System**: LangChain + Groq for health information retrieval
    - **API**: FastAPI with comprehensive endpoints
    
    ### Technology Stack
    
    **Frontend**: Streamlit
    **Backend**: FastAPI, Python 3.10+
    **ML**: scikit-learn, pandas, numpy
    **Database**: Neo4j (knowledge graph)
    **LLM**: Groq openai/gpt-oss-120btral model via LangChain
    **Embeddings**: Sentence Transformers + FAISS
    
    ### Getting Started
    
    1. **Start Backend**:
       ```bash
       cd backend
       python main.py
       ```
    
    2. **Run Frontend**:
       ```bash
       streamlit run frontend/streamlit_app.py
       ```
    
    3. **Access Application**:
       - Frontend: http://localhost:8501
       - API Docs: http://localhost:8000/docs
       - Health Check: http://localhost:8000/health
    
    ### Limitations & Notes
    
    - ML models are trained on demo data (not real-world validated)
    - Neo4j connection requires valid credentials
    - RAG requires valid Groq API key
    - SDOH data must be present for location-based queries
    
    ### About CTS Hackathon
    
    This is a demo application for the CTS (Community-based Treatment Support) 
    Hackathon showcasing AI/ML integration for health prediction and decision support.
    """)
    
    st.markdown("---")
    
    # Status indicator
    st.subheader("Current Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if api_status:
            st.success("✅ Backend API")
        else:
            st.error("❌ Backend API")
    
    with col2:
        st.info("📱 Frontend: Running")
    
    with col3:
        st.warning(f"⏰ {datetime.now().strftime('%H:%M:%S')}")


# ==================== Footer ====================

st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.caption("🏥 Health Risk Prediction Pipeline | CTS Hackathon Demo")

with col2:
    if st.button("🔄 Refresh Status"):
        st.rerun()

with col3:
    st.caption(f"Backend: {api_url}")
