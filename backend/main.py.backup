"""
FastAPI application for health risk prediction pipeline with unified orchestration.
Main entry point with API endpoints combining ML, KB, SDOH, and RAG.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
# The .env file is in the parent directory (Demo_cts_hackathon)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from config import get_settings
from services.neo4j_service import Neo4jService
from services.ml_services import RiskPredictionService
from services.data_service import DataService
from services.rag_service import RAGService
from services.unified_pipeline import UnifiedHealthRiskPipeline, UnifiedPipelineInput
from agents.langgraph_orchestrator import HealthRiskOrchestrator
from schemas.models import ChatMessage, ChatResponse
from routers import ocr_routes

# Global service instances
settings = None
neo4j_service = None
ml_service = None
data_service = None
rag_service = None
unified_pipeline = None
langgraph_orchestrator = None


# ==================== Lifespan Management ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle (startup/shutdown)."""
    global settings, neo4j_service, ml_service, data_service, rag_service, unified_pipeline, langgraph_orchestrator
    
    # Startup
    logger.info("🚀 Starting Health Risk Pipeline with unified orchestration...")
    try:
        settings = get_settings()
        logger.info(f"✓ Settings loaded")
        
        # Initialize Neo4j
        logger.info("Connecting to Neo4j Aura...")
        try:
            neo4j_service = Neo4jService(
                settings.neo4j_uri,
                settings.neo4j_username,
                settings.neo4j_password
            )
            logger.info("✓ Neo4j connected")
        except Exception as e:
            logger.warning(f"⚠️  Neo4j connection failed: {str(e)}")
            neo4j_service = None
        
        # Initialize ML services
        logger.info("Loading ML models...")
        model_path = Path(__file__).parent.parent / "ml" / "models"
        ml_service = RiskPredictionService(model_path=str(model_path))
        logger.info(f"✓ ML models loaded")
        
        # Initialize Data Service
        logger.info("Loading SDOH data...")
        data_service = DataService(settings.sdoh_data_path)
        logger.info(f"✓ SDOH data loaded")
        
        # Initialize RAG Service
        logger.info("Initializing RAG service...")
        rag_model = os.getenv("GROQ_MODEL", settings.llm_model)
        rag_service = RAGService(settings.groq_api_key, rag_model)
        logger.info("✓ RAG service initialized")
        
        # Initialize LLM for LangGraph
        llm = None
        provider = os.getenv("LLM_PROVIDER", settings.llm_provider).lower() if hasattr(settings, 'llm_provider') else "groq"
        logger.info(f"Using LLM provider: {provider}")
        
        # Try Groq first if specified
        if provider == "groq":
            try:
                from langchain_groq import ChatGroq
                groq_key = os.getenv("GROQ_API_KEY", settings.groq_api_key)
                groq_model = os.getenv("GROQ_MODEL", settings.llm_model)
                if groq_key and groq_key.strip() and groq_key != "demo_mode":
                    llm = ChatGroq(
                        groq_api_key=groq_key,
                        model_name=groq_model,
                        temperature=0.3
                    )
                    logger.info(f"✓ LLM initialized (Groq): {groq_model}")
            except Exception as e:
                logger.warning(f"Groq LLM failed: {e}, trying fallback")
        
        # Try NVIDIA if Groq fails and specified
        if llm is None and provider == "nvidia":
            try:
                from langchain_nvidia_ai_endpoints import ChatNVIDIA
                nvidia_key = os.getenv("NVIDIA_API_KEY", settings.nvidia_api_key)
                if nvidia_key and nvidia_key.strip() and nvidia_key != "demo_mode":
                    llm = ChatNVIDIA(
                        model=settings.nvidia_model,
                        api_key=nvidia_key,
                        temperature=0.3
                    )
                    logger.info(f"✓ LLM initialized (NVIDIA): {settings.nvidia_model}")
            except Exception as e:
                logger.warning(f"NVIDIA LLM failed: {e}, trying fallback")
        
        # Try OpenAI if others fail
        if llm is None and settings.llm_model.startswith("openai/"):
            try:
                from langchain_openai import ChatOpenAI
                openai_key = os.getenv("OPENAI_API_KEY", settings.openai_api_key)
                if openai_key and openai_key.strip() and openai_key != "demo_mode":
                    llm = ChatOpenAI(
                        model=settings.llm_model.replace("openai/", ""),
                        api_key=openai_key,
                        temperature=0.3
                    )
                    logger.info(f"✓ LLM initialized (OpenAI): {settings.llm_model}")
            except Exception as e:
                logger.warning(f"OpenAI LLM failed: {e}, trying Groq")
        
        # Final fallback to Groq (if not already tried)
        if llm is None:
            try:
                from langchain_groq import ChatGroq
                groq_key = os.getenv("GROQ_API_KEY", settings.groq_api_key)
                groq_model = os.getenv("GROQ_MODEL", settings.llm_model)
                if groq_key and groq_key.strip() and groq_key != "demo_mode":
                    llm = ChatGroq(
                        groq_api_key=groq_key,
                        model_name=groq_model,
                        temperature=0.3
                    )
                    logger.info(f"✓ LLM initialized (Groq): {groq_model}")
            except Exception as e:
                logger.warning(f"Groq LLM failed: {e}")
        
        if llm is None:
            logger.error("No LLM provider available, using demo mode")
            llm = None
        
        # Initialize LangGraph Orchestrator
        logger.info("Building LangGraph orchestrator...")
        langgraph_orchestrator = HealthRiskOrchestrator(
            llm=llm,
            neo4j_service=neo4j_service,
            ml_service=ml_service,
            data_service=data_service,
            rag_service=rag_service
        )
        logger.info("✓ LangGraph orchestrator ready")
        
        # Initialize Unified Pipeline
        logger.info("Initializing unified pipeline...")
        unified_pipeline = UnifiedHealthRiskPipeline(
            ml_service=ml_service,
            neo4j_service=neo4j_service,
            data_service=data_service,
            rag_service=rag_service,
            llm=llm,
            orchestrator=langgraph_orchestrator
        )
        app.state.settings = settings
        app.state.neo4j_service = neo4j_service
        app.state.ml_service = ml_service
        app.state.data_service = data_service
        app.state.rag_service = rag_service
        app.state.unified_pipeline = unified_pipeline
        app.state.langgraph_orchestrator = langgraph_orchestrator

        logger.info("✅ All services initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down services...")
    if neo4j_service:
        neo4j_service.close()
    logger.info("✓ Shutdown complete")


# ==================== FastAPI Application ====================

app = FastAPI(
    title="Health Risk Prediction Pipeline",
    description="Unified pipeline combining ML predictions, knowledge graph reasoning, SDOH analysis, and RAG documents",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include OCR routes
app.include_router(ocr_routes.router)


# ==================== Health Check Endpoints ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "neo4j": "connected" if neo4j_service and neo4j_service.is_connected() else "disconnected",
            "ml": "ready" if ml_service else "unavailable",
            "rag": "ready" if rag_service else "unavailable",
            "unified_pipeline": "ready" if unified_pipeline else "unavailable",
            "langgraph": "ready" if langgraph_orchestrator else "unavailable"
        },
        "pipeline_version": "2.0.0 (Unified)"
    }


# ==================== Unified Risk Prediction Endpoint ====================

@app.post("/api/v1/unified-predict")
async def unified_health_prediction(
    member_id: str,
    health_metrics: dict,
    zipcode: Optional[str] = None,
    query: Optional[str] = None
):
    """
    Unified health risk prediction combining all sources.
    
    Flow:
    1. ML Model → Risk scores for 4 diseases
    2. SDOH Data → Health equity analysis
    3. Neo4j KB → Disease pathways and factors
    4. RAG → Evidence-based guidelines
    5. LLM → Unified comprehensive response
    """
    if not unified_pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        logger.info(f"🔄 Processing unified prediction for member: {member_id}")
        
        # Create pipeline input
        input_data = UnifiedPipelineInput(
            member_id=member_id,
            health_metrics=health_metrics,
            zipcode=zipcode,
            query=query
        )
        
        # Process through unified pipeline
        output = unified_pipeline.process(input_data)
        
        # Store patient metrics in data_service for RAG/Chat context
        if data_service:
            data_service.store_member_prediction(member_id, {
                **health_metrics,
                "zipcode": zipcode
            })
            
        logger.info(f"✅ Unified prediction complete for {member_id}")
        
        return output.model_dump()
        
    except Exception as e:
        logger.error(f"❌ Prediction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Quick Prediction Endpoint ====================

@app.post("/api/v1/quick-predict")
async def quick_predict(health_report: dict):
    """Quick prediction with basic risk scores"""
    if not ml_service:
        raise HTTPException(status_code=503, detail="ML service not initialized")
    
    try:
        member_id = health_report.get("member_id", "UNKNOWN")
        health_metrics = health_report.get("health_metrics", {})
        
        # Get SDOH scores if zipcode provided
        sdoh_scores = {}
        if health_metrics.get("zipcode") and data_service:
            sdoh_scores = data_service.get_sdoh_scores(
                health_metrics["zipcode"],
                health_metrics.get("year", 2023)
            )
        
        # Get risk scores
        risk_scores = {}
        for disease in ["diabetes", "hypertension", "heart_disease", "asthma"]:
            score, confidence = ml_service.predict_risk(
                health_metrics,
                sdoh_scores,
                disease
            )
            risk_scores[disease] = {
                "risk_score": score,
                "risk_level": _get_risk_level(score),
                "confidence": confidence
            }
        
        return {
            "member_id": member_id,
            "risk_scores": risk_scores,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Quick predict error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Chat Endpoint ====================

@app.post("/api/v1/chat")
async def chat_with_health_bot(message: ChatMessage, member_id: Optional[str] = None) -> ChatResponse:
    """Chat with RAG-based health information assistant"""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        # Get member context if available
        context_data = {}
        if member_id:
            if data_service:
                member_data = data_service.get_member_data(member_id)
                if member_data:
                    context_data = member_data
                else:
                    context_data = {"member_id": member_id}
            else:
                context_data = {"member_id": member_id}
        
        # Query RAG
        result = rag_service.query(message.content, context_data)
        
        return ChatResponse(
            response=result.get("response", ""),
            source_type=result.get("source_type", "unknown"),
            confidence=result.get("confidence", 0.0)
        )
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== KB Graph Query Endpoint ====================

@app.get("/api/v1/kb-graph/{disease}")
async def query_knowledge_graph(disease: str, zipcode: Optional[str] = None):
    """Query Neo4j knowledge graph for disease insights"""
    if not neo4j_service or not neo4j_service.is_connected():
        raise HTTPException(status_code=503, detail="Knowledge graph not available")
    
    try:
        # Get disease factors
        factors = neo4j_service.get_factors_for_disease(disease)
        
        # Get disease pathways
        pathways = neo4j_service.get_disease_pathways(disease, zipcode)
        
        # Get interventions
        interventions = neo4j_service.get_disease_interventions(disease)
        
        return {
            "disease": disease,
            "factors": factors,
            "pathways": pathways,
            "interventions": interventions
        }
    except Exception as e:
        logger.error(f"KB graph query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Root & Info ====================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Health Risk Prediction Pipeline",
        "version": "2.0.0 (Unified)",
        "description": "Comprehensive health risk assessment combining ML, knowledge graphs, SDOH, and RAG",
        "endpoints": {
            "health": "/health",
            "unified_predict": "/api/v1/unified-predict",
            "quick_predict": "/api/v1/quick-predict",
            "chat": "/api/v1/chat",
            "kb_graph": "/api/v1/kb-graph/{disease}",
            "docs": "/docs"
        }
    }


# ==================== Helper Functions ====================

def _get_risk_level(score: float) -> str:
    """Map risk score to level"""
    if score < 0.25:
        return "Low"
    elif score < 0.50:
        return "Medium"
    elif score < 0.75:
        return "High"
    else:
        return "Very High"


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )
