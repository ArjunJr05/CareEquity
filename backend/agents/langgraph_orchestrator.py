"""
LangGraph-based agent orchestrator for health risk prediction pipeline.

Three specialized agents:
1. Model + KB + SDOH Agent: Predictions, knowledge graph reasoning, health equity
2. RAG Document Agent: Evidence-based guidelines and recommendations
3. Unified Response Agent: Combines all sources into comprehensive response
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

from prompts.system_prompt import (
    UNIFIED_RESPONSE_PROMPT,
    KB_REASONING_PROMPT,
    PREDICTION_EXPLANATION_PROMPT,
)

logger = logging.getLogger(__name__)


# ==================== State Models ====================

class AgentState(BaseModel):
    """State passed between agents in the LangGraph"""
    
    # Input
    member_id: str
    query: str
    health_metrics: Dict[str, Any] = Field(default_factory=dict)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Model predictions
    risk_scores: Dict[str, float] = Field(default_factory=dict)
    ml_confidence: float = 0.0
    contributing_factors: List[str] = Field(default_factory=list)
    
    # KB graph reasoning
    kb_insights: str = ""
    kb_pathways: Dict[str, List[str]] = Field(default_factory=dict)
    kb_confidence: float = 0.0
    
    # SDOH analysis
    sdoh_scores: Dict[str, float] = Field(default_factory=dict)
    sdoh_barriers: List[str] = Field(default_factory=list)
    sdoh_recommendations: List[str] = Field(default_factory=list)
    
    # RAG documents
    rag_documents: List[str] = Field(default_factory=list)
    rag_guidelines: str = ""
    rag_recommendations: str = ""
    
    # Final response
    unified_response: str = ""
    sources_used: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ==================== Model + KB + SDOH Agent ====================

class ModelKBSDOHAgent:
    """Agent combining ML predictions, KB reasoning, and SDOH analysis"""
    
    def __init__(self, llm: ChatGroq, neo4j_service, ml_service, data_service):
        """
        Initialize the agent with required services.
        
        Args:
            llm: Language model (Groq)
            neo4j_service: Neo4j service for KB queries
            ml_service: ML service for predictions
            data_service: Data service for SDOH scores
        """
        self.llm = llm
        self.neo4j_service = neo4j_service
        self.ml_service = ml_service
        self.data_service = data_service
    
    def process(self, state: AgentState) -> AgentState:
        """Process health metrics through ML + KB + SDOH pipeline"""
        try:
            logger.info(f"Model+KB+SDOH Agent processing member: {state.member_id}")
            
            # Step 1: Get ML predictions
            if state.health_metrics and state.risk_scores == {}:
                state = self._predict_risks(state)
            
            # Step 2: Query KB graph for disease pathways
            state = self._query_kb_graph(state)
            
            # Step 3: Analyze SDOH factors
            state = self._analyze_sdoh(state)
            
            # Step 4: Generate KB reasoning explanation
            state = self._generate_kb_reasoning(state)
            
            state.sources_used.append("Model")
            state.sources_used.append("KB Graph")
            state.sources_used.append("SDOH")
            
            logger.info(f"Model+KB+SDOH Agent completed for {state.member_id}")
            return state
            
        except Exception as e:
            logger.error(f"Model+KB+SDOH Agent error: {str(e)}")
            return state
    
    def _predict_risks(self, state: AgentState) -> AgentState:
        """Get ML model predictions"""
        try:
            for disease in ["diabetes", "hypertension", "heart_disease", "asthma"]:
                risk_score, confidence = self.ml_service.predict_risk(
                    state.health_metrics,
                    state.sdoh_scores if state.sdoh_scores else {},
                    disease
                )
                state.risk_scores[disease] = risk_score
                state.ml_confidence = max(state.ml_confidence, confidence)
                
            logger.info(f"ML predictions: {state.risk_scores}")
        except Exception as e:
            logger.error(f"ML prediction error: {str(e)}")
        
        return state
    
    def _query_kb_graph(self, state: AgentState) -> AgentState:
        """Query Neo4j knowledge graph for disease pathways"""
        try:
            if not self.neo4j_service:
                logger.warning("Neo4j service not available")
                return state
            
            # Query pathways for top diseases
            for disease, risk_score in sorted(state.risk_scores.items(), key=lambda x: x[1], reverse=True)[:2]:
                if risk_score > 0.3:  # Only high-risk diseases
                    # Query disease factors
                    factors = self.neo4j_service.get_factors_for_disease(disease)
                    if factors:
                        state.kb_pathways[disease] = factors
                    
                    logger.info(f"KB factors for {disease}: {factors}")
            
            state.kb_confidence = 0.85
            
        except Exception as e:
            logger.error(f"KB graph query error: {str(e)}")
        
        return state
    
    def _analyze_sdoh(self, state: AgentState) -> AgentState:
        """Analyze SDOH factors affecting health"""
        try:
            # Get SDOH scores if not already present
            if not state.sdoh_scores and state.health_metrics.get("zipcode"):
                state.sdoh_scores = self.data_service.get_sdoh_scores(
                    state.health_metrics["zipcode"],
                    state.health_metrics.get("year", 2023)
                )
            
            # Identify barriers (low scores)
            for factor, score in state.sdoh_scores.items():
                if score < 0.4:  # Low score = barrier
                    state.sdoh_barriers.append(f"{factor.replace('_', ' ')}: {score:.1%}")
            
            logger.info(f"SDOH barriers: {state.sdoh_barriers}")
            
        except Exception as e:
            logger.error(f"SDOH analysis error: {str(e)}")
        
        return state
    
    def _generate_kb_reasoning(self, state: AgentState) -> AgentState:
        """Generate reasoning using KB insights"""
        try:
            if not state.kb_pathways:
                return state
            
            # Build context
            context = "Disease Pathways from Knowledge Graph:\n"
            for disease, factors in state.kb_pathways.items():
                context += f"\n{disease.upper()}:\n"
                for factor in factors[:5]:  # Top 5 factors
                    context += f"  - {factor}\n"
            
            # Generate reasoning
            prompt = f"""{KB_REASONING_PROMPT}

Patient Data:
- Risk Scores: {state.risk_scores}
- SDOH Barriers: {state.sdoh_barriers}

{context}

Provide analysis of disease pathways and contributing factors."""
            
            messages = [
                SystemMessage(content=KB_REASONING_PROMPT),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            state.kb_insights = response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"KB reasoning generation error: {str(e)}")
        
        return state


# ==================== RAG Document Agent ====================

class RAGDocumentAgent:
    """Agent for retrieving and processing RAG documents"""
    
    def __init__(self, llm: ChatGroq, rag_service):
        """
        Initialize RAG agent.
        
        Args:
            llm: Language model (Groq)
            rag_service: RAG service for document retrieval
        """
        self.llm = llm
        self.rag_service = rag_service
    
    def process(self, state: AgentState) -> AgentState:
        """Process documents for relevant guidelines"""
        try:
            logger.info(f"RAG Document Agent processing for member: {state.member_id}")
            
            # Get top diseases
            top_diseases = sorted(state.risk_scores.items(), key=lambda x: x[1], reverse=True)[:2]
            
            for disease, risk_score in top_diseases:
                if risk_score > 0.3:
                    # Query for disease-specific guidelines
                    query = f"Guidelines and recommendations for {disease} prevention and management"
                    
                    result = self.rag_service.query(query, state.context_data)
                    
                    if result.get("response"):
                        state.rag_documents.append(result["response"])
                        state.rag_guidelines += f"\n{result['response']}\n"
            
            # Generate recommendations from documents
            state = self._generate_recommendations(state)
            
            state.sources_used.append("RAG Guidelines")
            logger.info("RAG Document Agent completed")
            
            return state
            
        except Exception as e:
            logger.error(f"RAG Document Agent error: {str(e)}")
            return state
    
    def _generate_recommendations(self, state: AgentState) -> AgentState:
        """Generate actionable recommendations from guidelines"""
        try:
            if not state.rag_guidelines:
                return state
            
            prompt = f"""Based on the following guidelines for managing health risks, provide specific, actionable recommendations:

Guidelines:
{state.rag_guidelines}

SDOH Barriers:
{', '.join(state.sdoh_barriers)}

Provide recommendations that:
1. Are evidence-based from the guidelines
2. Are feasible given SDOH constraints
3. Include specific action items
4. Address the patient's top risk factors"""
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            state.rag_recommendations = response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {str(e)}")
        
        return state


# ==================== Unified Response Agent ====================

class UnifiedResponseAgent:
    """Agent that combines all sources into unified response"""
    
    def __init__(self, llm: ChatGroq):
        """
        Initialize unified response agent.
        
        Args:
            llm: Language model (Groq)
        """
        self.llm = llm
    
    def process(self, state: AgentState) -> AgentState:
        """Combine all sources into unified response"""
        try:
            logger.info(f"Unified Response Agent processing for member: {state.member_id}")
            
            # Build comprehensive context
            context = self._build_context(state)
            
            # Generate unified response
            prompt = f"""{UNIFIED_RESPONSE_PROMPT}

PATIENT CONTEXT:
{context}

Generate a comprehensive health risk assessment combining all available information."""
            
            messages = [
                SystemMessage(content=UNIFIED_RESPONSE_PROMPT),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            state.unified_response = response.content if hasattr(response, 'content') else str(response)
            
            # Calculate overall confidence
            state.confidence_score = (state.ml_confidence * 0.4 + 
                                     state.kb_confidence * 0.3 + 
                                     0.85 * 0.3)  # RAG confidence
            
            logger.info(f"Unified response generated with confidence: {state.confidence_score:.2f}")
            return state
            
        except Exception as e:
            logger.error(f"Unified Response Agent error: {str(e)}")
            return state
    
    def _build_context(self, state: AgentState) -> str:
        """Build comprehensive context for response"""
        context = f"""## Patient Health Assessment

### Risk Scores [ML Model]:
"""
        for disease, score in state.risk_scores.items():
            level = self._get_risk_level(score)
            context += f"- {disease.title()}: {score:.1%} ({level})\n"
        
        context += "\n### Disease Pathways [Knowledge Graph]:\n"
        for disease, factors in state.kb_pathways.items():
            context += f"- {disease.title()}: {', '.join(factors[:3])}\n"
        
        context += "\n### Health Equity Factors [SDOH]:\n"
        if state.sdoh_barriers:
            for barrier in state.sdoh_barriers:
                context += f"- {barrier}\n"
        else:
            context += "- No significant SDOH barriers identified\n"
        
        context += "\n### Evidence-Based Guidelines:\n"
        context += state.rag_guidelines[:500] + "...\n" if state.rag_guidelines else "- No guidelines retrieved\n"
        
        context += "\n### Patient Data:\n"
        for key, value in state.health_metrics.items():
            context += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        return context
    
    @staticmethod
    def _get_risk_level(score: float) -> str:
        """Map score to risk level"""
        if score < 0.25:
            return "Low"
        elif score < 0.50:
            return "Medium"
        elif score < 0.75:
            return "High"
        else:
            return "Very High"


# ==================== LangGraph Orchestrator ====================

class HealthRiskOrchestrator:
    """LangGraph-based orchestrator for health risk pipeline"""
    
    def __init__(self, llm: ChatGroq, neo4j_service, ml_service, data_service, rag_service):
        """Initialize orchestrator with all required services"""
        self.llm = llm
        self.neo4j_service = neo4j_service
        self.ml_service = ml_service
        self.data_service = data_service
        self.rag_service = rag_service
        
        # Initialize agents
        self.model_kb_sdoh_agent = ModelKBSDOHAgent(
            llm, neo4j_service, ml_service, data_service
        )
        self.rag_agent = RAGDocumentAgent(llm, rag_service)
        self.unified_agent = UnifiedResponseAgent(llm)
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes with unique names
        workflow.add_node("predict_kb_sdoh", self._node_model_kb_sdoh)
        workflow.add_node("retrieve_rag", self._node_rag_documents)
        workflow.add_node("generate_response", self._node_unified_response)
        
        # Add edges
        workflow.set_entry_point("predict_kb_sdoh")
        workflow.add_edge("predict_kb_sdoh", "retrieve_rag")
        workflow.add_edge("retrieve_rag", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _node_model_kb_sdoh(self, state: AgentState) -> AgentState:
        """Execute Model+KB+SDOH agent"""
        return self.model_kb_sdoh_agent.process(state)
    
    def _node_rag_documents(self, state: AgentState) -> AgentState:
        """Execute RAG Document agent"""
        return self.rag_agent.process(state)
    
    def _node_unified_response(self, state: AgentState) -> AgentState:
        """Execute Unified Response agent"""
        return self.unified_agent.process(state)
    
    def process(self, member_id: str, query: str, health_metrics: Dict[str, Any],
                context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process health risk assessment through the pipeline.
        
        Args:
            member_id: Member identifier
            query: User query
            health_metrics: Patient health metrics
            context_data: Additional context
        
        Returns:
            Comprehensive health risk assessment
        """
        try:
            # Initialize state
            state = AgentState(
                member_id=member_id,
                query=query,
                health_metrics=health_metrics,
                context_data=context_data
            )
            
            # Execute graph
            logger.info(f"Processing member {member_id} through orchestrator...")
            final_state = self.graph.invoke(state)
            
            # Format response
            response = {
                "member_id": final_state.member_id,
                "query": final_state.query,
                "risk_scores": final_state.risk_scores,
                "confidence": final_state.confidence_score,
                "kb_insights": final_state.kb_insights,
                "rag_guidelines": final_state.rag_guidelines,
                "recommendations": final_state.rag_recommendations,
                "sdoh_barriers": final_state.sdoh_barriers,
                "unified_response": final_state.unified_response,
                "sources": final_state.sources_used,
                "timestamp": final_state.timestamp
            }
            
            logger.info(f"Processing complete for {member_id}")
            return response
            
        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}")
            return {
                "member_id": member_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
