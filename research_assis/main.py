#!/usr/bin/env python3
"""
CareEquity SDOH Research Assistant - FastAPI Backend Service.

Provides high-speed RESTful endpoints for:
- POST /api/analyze: Parallel 4-agent SDOH analysis with live web disease surveillance
- GET /api/presets: Pre-configured sample patient risk cases
- GET /api/health: System health and active LLM provider diagnostics
- POST /api/test: Automated multi-agent system validation suite

Run via:
    python main.py
Or:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Fix Windows console encoding for UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from models.schemas import RiskCase, CompleteAnalysisReport
from workflow import run_sdoh_analysis
from config.settings import settings
from config.llm_client import get_llm_client
from agents.web_search_agent import WebSearchAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CareEquity-API")

# Initialize FastAPI application
app = FastAPI(
    title="CareEquity SDOH Multi-Agent Intelligence API",
    description="Backend API for Social Determinants of Health (SDOH) analysis, live disease surveillance, and evidence-based interventions.",
    version="4.0.0"
)

# Enable CORS for frontend applications (Streamlit, React, Vue, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_sample_cases() -> List[RiskCase]:
    """Pre-built test cases for diverse patient demographics and conditions."""
    return [
        RiskCase(
            case_id="BRONX_DIABETES_001",
            member_id="M_88201",
            age=54,
            geography="Bronx, NY",
            risk_score=85.0,
            risk_level="high",
            chronic_conditions=["Type 2 Diabetes", "Essential Hypertension", "Obesity"],
            clinical_risk_factors=["HbA1c > 9.0%", "Uncontrolled Systolic BP"],
            transportation=True,
            food_access=True,
            economic_stability=True,
            housing=False,
            social_isolation=False,
            recent_ed_visits=3,
            missed_appointments=4,
            intervention_goal="Reduce emergency department visits and stabilize glycemic control."
        ),
        RiskCase(
            case_id="BROOKLYN_CARDIAC_002",
            member_id="M_44912",
            age=62,
            geography="Brooklyn, NY",
            risk_score=76.0,
            risk_level="high",
            chronic_conditions=["Congestive Heart Failure", "Hypertension", "Atrial Fibrillation"],
            clinical_risk_factors=["Frequent fluid retention", "Medication complexity"],
            transportation=True,
            food_access=False,
            economic_stability=True,
            housing=True,
            social_isolation=True,
            recent_ed_visits=2,
            missed_appointments=2,
            intervention_goal="Enhance outpatient cardiology follow-through and food/fluid regulation."
        ),
        RiskCase(
            case_id="MANHATTAN_ELDER_003",
            member_id="M_11094",
            age=76,
            geography="Manhattan, NY",
            risk_score=92.0,
            risk_level="critical",
            chronic_conditions=["COPD", "Chronic Kidney Disease Stage 3", "Depression"],
            clinical_risk_factors=["Severe respiratory limitation", "Polypharmacy"],
            transportation=True,
            food_access=True,
            economic_stability=True,
            housing=True,
            social_isolation=True,
            recent_ed_visits=4,
            missed_appointments=5,
            intervention_goal="Comprehensive multidisciplinary care coordination and housing/energy support."
        ),
        RiskCase(
            case_id="CHICAGO_HTN_004",
            member_id="M_55102",
            age=45,
            geography="Chicago, IL",
            risk_score=68.0,
            risk_level="high",
            chronic_conditions=["Hypertension", "High Cholesterol"],
            clinical_risk_factors=["Elevated resting heart rate", "Work stress"],
            transportation=False,
            food_access=True,
            economic_stability=True,
            housing=False,
            social_isolation=False,
            recent_ed_visits=1,
            missed_appointments=1,
            intervention_goal="Medication compliance and nutrition management."
        )
    ]


@app.get("/", tags=["Root"])
def root_status():
    """Root endpoint returning API status and active provider configuration."""
    return {
        "service": "CareEquity SDOH Multi-Agent Intelligence API",
        "status": "online",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat(),
        "architecture": {
            "agent_1": "Clinical & SDOH Risk Analyzer",
            "agent_2": "Geographic & Environment Specialist",
            "agent_3": "Local Safety-Net Resource Locator",
            "live_web_agent": "Real-Time Public Health & Disease Surveillance",
            "agent_4": "Intervention & Report Synthesizer"
        },
        "providers_configured": {
            "nvidia": bool(settings.nvidia_api_key),
            "groq": bool(settings.groq_api_key),
            "openrouter": bool(settings.openrouter_api_key),
            "offline_fallback": True
        }
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "engine": "CareEquity Parallel Multi-Agent Orchestrator",
        "models": {
            "nvidia": settings.nvidia_model,
            "groq": settings.groq_model,
            "openrouter": settings.openrouter_model
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/presets", response_model=List[RiskCase], tags=["Presets"])
def get_presets():
    """Retrieve pre-built patient risk cases for demo and rapid testing."""
    return get_sample_cases()


@app.post("/api/analyze", response_model=CompleteAnalysisReport, tags=["Analysis"])
def analyze_patient(risk_case: RiskCase):
    """
    Execute parallel multi-agent SDOH analysis and live web disease surveillance.
    Returns comprehensive clinical report, evidence-based interventions, and localized resources.
    """
    logger.info(f"Received analysis request for case: {risk_case.case_id} (Location: {risk_case.geography})")
    try:
        report = run_sdoh_analysis(risk_case)
        return report
    except Exception as e:
        logger.error(f"Error during analysis for case {risk_case.case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline error: {str(e)}"
        )


@app.post("/api/test", tags=["Diagnostics"])
def run_diagnostics():
    """Execute complete system validation test suite and return detailed diagnostics."""
    test_case = get_sample_cases()[0]
    results = {}

    # Test 1: LLM Client
    try:
        client = get_llm_client()
        resp, prov = client.generate("Reply with 'READY'.", max_tokens=10)
        results["test_1_llm_client"] = {
            "status": "PASSED",
            "provider_used": prov,
            "response": resp
        }
    except Exception as e:
        results["test_1_llm_client"] = {"status": "FAILED", "error": str(e)}

    # Test 2: Live Web Search Agent
    try:
        web_agent = WebSearchAgent()
        live_res = web_agent.search_live_health(test_case)
        results["test_2_web_surveillance"] = {
            "status": "PASSED",
            "location": live_res.location,
            "alerts_count": len(live_res.active_disease_alerts),
            "summary_snippet": live_res.surveillance_summary[:100]
        }
    except Exception as e:
        results["test_2_web_surveillance"] = {"status": "FAILED", "error": str(e)}

    # Test 3: Parallel Pipeline
    try:
        t0 = time.time()
        report = run_sdoh_analysis(test_case)
        elapsed = time.time() - t0
        results["test_3_orchestrator"] = {
            "status": "PASSED" if report.status == "SUCCESS" else "FAILED",
            "execution_time_seconds": elapsed,
            "interventions_count": len(report.interventions),
            "report_length": len(report.comprehensive_report)
        }
    except Exception as e:
        results["test_3_orchestrator"] = {"status": "FAILED", "error": str(e)}

    all_passed = all(v.get("status") == "PASSED" for v in results.values())
    return {
        "overall_status": "PASSED" if all_passed else "FAILED",
        "timestamp": datetime.now().isoformat(),
        "diagnostics": results
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"🚀 Starting CareEquity SDOH FastAPI Backend on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
