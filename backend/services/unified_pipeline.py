"""
Unified Health Risk Prediction Pipeline
Combines ML model predictions, knowledge graph reasoning, SDOH analysis, and RAG documents
into a comprehensive health risk assessment.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UnifiedPipelineInput(BaseModel):
    """Input data for unified pipeline"""
    member_id: str
    health_metrics: Dict[str, Any]
    context_data: Dict[str, Any] = Field(default_factory=dict)
    query: Optional[str] = None
    zipcode: Optional[str] = None


class UnifiedPipelineOutput(BaseModel):
    """Output from unified pipeline"""
    member_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Risk assessment
    risk_scores: Dict[str, float]
    risk_levels: Dict[str, str]
    
    # Contributing factors
    top_factors: List[str]
    modifiable_factors: List[str]
    non_modifiable_factors: List[str]
    
    # KB insights
    disease_pathways: Dict[str, Any]
    kb_insights: str
    
    # SDOH analysis
    sdoh_barriers: List[str]
    sdoh_recommendations: List[str]
    
    # RAG guidelines
    evidence_based_guidelines: str
    action_items: List[str]
    
    # Unified response
    comprehensive_assessment: str
    recommendations: List[str]
    next_steps: List[str]
    
    # Metadata
    sources_used: List[str]
    confidence_score: float
    processing_time_ms: float


class UnifiedHealthRiskPipeline:
    """Unified pipeline for comprehensive health risk assessment"""
    
    def __init__(self, 
                 ml_service,
                 neo4j_service,
                 data_service,
                 rag_service,
                 llm,
                 orchestrator):
        """
        Initialize unified pipeline with all services.
        
        Args:
            ml_service: Machine learning prediction service
            neo4j_service: Neo4j knowledge graph service
            data_service: SDOH data service
            rag_service: RAG document retrieval service
            llm: Language model for reasoning
            orchestrator: LangGraph orchestrator
        """
        self.ml_service = ml_service
        self.neo4j_service = neo4j_service
        self.data_service = data_service
        self.rag_service = rag_service
        self.llm = llm
        self.orchestrator = orchestrator
        
        logger.info("✓ Unified Pipeline initialized")
    
    def process(self, input_data: UnifiedPipelineInput) -> UnifiedPipelineOutput:
        """
        Process health data through complete pipeline.
        
        Flow:
        1. ML Model → Risk predictions for 4 diseases
        2. Neo4j KB → Disease pathways and contributing factors
        3. SDOH Data → Health equity analysis with zipcode data
        4. RAG → Evidence-based guidelines and recommendations
        5. LLM → Unified reasoning combining all sources
        
        Args:
            input_data: Pipeline input
        
        Returns:
            Comprehensive health risk assessment
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting unified pipeline for member: {input_data.member_id}")
            
            # Step 1: Get SDOH scores first
            logger.info("Step 1: SDOH Analysis")
            sdoh_scores, sdoh_barriers = self._get_sdoh_analysis(
                input_data.health_metrics,
                input_data.zipcode
            )
            
            # Step 2: Get ML predictions with SDOH scores
            logger.info("Step 2: ML Model Predictions")
            risk_scores, ml_confidence, factors = self._get_ml_predictions(
                input_data.health_metrics,
                sdoh_scores
            )
            
            # Step 3: Query Knowledge Graph
            logger.info("Step 3: Knowledge Graph Reasoning")
            disease_pathways, kb_insights, kb_factors = self._query_knowledge_graph(
                risk_scores,
                input_data.zipcode
            )
            
            # Step 4: Get RAG documents
            logger.info("Step 4: RAG Document Retrieval")
            guidelines, rag_recommendations = self._get_rag_documents(
                risk_scores,
                sdoh_barriers
            )
            
            # Step 5: Generate unified response
            logger.info("Step 5: Unified Response Generation")
            comprehensive_assessment, final_recommendations, action_items = self._generate_unified_response(
                input_data,
                risk_scores,
                sdoh_barriers,
                kb_insights,
                guidelines
            )
            
            # Step 6: Prepare output
            output = UnifiedPipelineOutput(
                member_id=input_data.member_id,
                
                # Risk assessment
                risk_scores=risk_scores,
                risk_levels={
                    disease: self._get_risk_level(score)
                    for disease, score in risk_scores.items()
                },
                
                # Contributing factors
                top_factors=factors[:5],
                modifiable_factors=[f for f in factors if "modifiable" in f.lower()],
                non_modifiable_factors=[f for f in factors if "non-modifiable" in f.lower() or "age" in f.lower()],
                
                # KB insights
                disease_pathways=disease_pathways,
                kb_insights=kb_insights,
                
                # SDOH analysis
                sdoh_barriers=sdoh_barriers,
                sdoh_recommendations=self._generate_sdoh_recommendations(sdoh_barriers),
                
                # RAG guidelines
                evidence_based_guidelines=guidelines,
                action_items=action_items,
                
                # Unified response
                comprehensive_assessment=comprehensive_assessment,
                recommendations=final_recommendations,
                next_steps=self._generate_next_steps(risk_scores, sdoh_barriers),
                
                # Metadata
                sources_used=["ML Model", "Knowledge Graph", "SDOH Data", "RAG Documents", "LLM"],
                confidence_score=(ml_confidence * 0.3 + 0.85 * 0.7),  # Weighted confidence
                processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            logger.info(f"Pipeline completed for {input_data.member_id} in {output.processing_time_ms:.2f}ms")
            return output
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}", exc_info=True)
            raise
    
    def _get_ml_predictions(self, health_metrics: Dict[str, Any], 
                           sdoh_scores: Dict[str, Any] = None) -> tuple:
        """Get ML model predictions for all diseases"""
        try:
            risk_scores = {}
            factors = []
            max_confidence = 0.0
            
            # Use provided SDOH scores or get defaults
            if sdoh_scores is None:
                sdoh_scores = {
                    "economic_stability_score": 0.5,
                    "healthcare_access_quality_score": 0.5,
                    "education_access_quality_score": 0.5,
                    "neighborhood_built_environment_score": 0.5,
                    "food_security_score": 0.5,
                    "social_community_context_score": 0.5,
                }
            
            diseases = ["diabetes", "hypertension", "heart_disease", "asthma"]
            
            for disease in diseases:
                score, confidence = self.ml_service.predict_risk(
                    health_metrics,
                    sdoh_scores,
                    disease
                )
                risk_scores[disease] = score
                max_confidence = max(max_confidence, confidence)
                
                # Extract key factors
                if score > 0.5:
                    factors.append(f"High risk factors for {disease}")
            
            logger.info(f"ML predictions: {risk_scores}")
            return risk_scores, max_confidence, factors
            
        except Exception as e:
            logger.error(f"ML prediction error: {str(e)}")
            return {}, 0.0, []
    
    def _get_sdoh_analysis(self, health_metrics: Dict[str, Any], 
                          zipcode: Optional[str] = None) -> tuple:
        """Get SDOH scores and identify barriers"""
        try:
            sdoh_scores = {}
            barriers = []
            
            # Get zipcode from health metrics if not provided
            if not zipcode and health_metrics.get("zipcode"):
                zipcode = health_metrics["zipcode"]
            
            # Get SDOH scores
            if zipcode:
                sdoh_scores = self.data_service.get_sdoh_scores(
                    zipcode,
                    health_metrics.get("year", 2023)
                )
                
                # Identify barriers (low scores)
                for factor, score in sdoh_scores.items():
                    if score < 0.4:  # Threshold for barrier
                        barriers.append(f"{factor.replace('_', ' ')}: {score:.1%}")
            
            logger.info(f"SDOH barriers identified: {len(barriers)}")
            return sdoh_scores, barriers
            
        except Exception as e:
            logger.error(f"SDOH analysis error: {str(e)}")
            return {}, []
    
    def _query_knowledge_graph(self, risk_scores: Dict[str, float],
                              zipcode: Optional[str] = None) -> tuple:
        """Query Neo4j knowledge graph for disease insights"""
        try:
            if not self.neo4j_service or not self.neo4j_service.is_connected():
                logger.warning("Neo4j not available, skipping KB query")
                return {}, "", []
            
            pathways = {}
            all_factors = []
            insights = ""
            
            # Query pathways for high-risk diseases
            for disease, score in sorted(risk_scores.items(), key=lambda x: x[1], reverse=True):
                if score > 0.3:  # Only for elevated risks
                    # Get disease factors
                    factors = self.neo4j_service.get_factors_for_disease(disease)
                    if factors:
                        pathways[disease] = factors
                        all_factors.extend(factors[:3])
                    
                    # Get comprehensive analysis
                    analysis = self.neo4j_service.get_comprehensive_disease_analysis(
                        disease, zipcode
                    )
                    if analysis:
                        pathways[f"{disease}_analysis"] = analysis
            
            # Generate insights
            if pathways:
                insights = self._format_kb_insights(pathways, risk_scores)
            
            logger.info(f"KB query complete: {len(pathways)} disease pathways")
            return pathways, insights, all_factors
            
        except Exception as e:
            logger.error(f"KB query error: {str(e)}")
            return {}, "", []
    
    def _get_rag_documents(self, risk_scores: Dict[str, float],
                          sdoh_barriers: List[str]) -> tuple:
        """Retrieve RAG documents for guidelines and recommendations"""
        try:
            guidelines = ""
            recommendations = []
            
            # Query for top diseases
            top_diseases = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)[:2]
            
            for disease, score in top_diseases:
                if score > 0.3:
                    # Build query
                    query = f"Guidelines for {disease} prevention and management"
                    
                    # Get RAG response
                    result = self.rag_service.query(query, {"disease": disease})
                    
                    if result.get("response"):
                        guidelines += f"\n## {disease.upper()}\n{result['response']}\n"
                        recommendations.append(result["response"][:200])  # First 200 chars
            
            logger.info("RAG document retrieval complete")
            return guidelines, recommendations
            
        except Exception as e:
            logger.error(f"RAG retrieval error: {str(e)}")
            return "", []
    
    def _generate_unified_response(self,
                                  input_data: UnifiedPipelineInput,
                                  risk_scores: Dict[str, float],
                                  sdoh_barriers: List[str],
                                  kb_insights: str,
                                  guidelines: str) -> tuple:
        """Generate unified response combining all sources"""
        try:
            # Build comprehensive context
            context = self._build_assessment_context(
                input_data,
                risk_scores,
                sdoh_barriers,
                kb_insights,
                guidelines
            )
            
            # Generate assessment
            prompt = f"""Based on the following comprehensive health assessment, provide a unified health risk report:

{context}

Provide:
1. Overall risk assessment summary
2. Key contributing factors
3. Evidence-based recommendations
4. Specific action items addressing SDOH barriers
5. Next steps for the patient"""
            
            response = self.llm.invoke([
                {"role": "system", "content": "You are a comprehensive health risk assessment specialist."},
                {"role": "user", "content": prompt}
            ])
            
            assessment = response.content if hasattr(response, 'content') else str(response)
            
            # Extract recommendations and action items
            recommendations = self._extract_recommendations(assessment)
            action_items = self._extract_action_items(assessment)
            
            return assessment, recommendations, action_items
            
        except Exception as e:
            logger.error(f"Unified response generation error: {str(e)}")
            return "", [], []
    
    def _build_assessment_context(self,
                                 input_data: UnifiedPipelineInput,
                                 risk_scores: Dict[str, float],
                                 sdoh_barriers: List[str],
                                 kb_insights: str,
                                 guidelines: str) -> str:
        """Build comprehensive assessment context"""
        context = f"""
# COMPREHENSIVE HEALTH RISK ASSESSMENT
Member ID: {input_data.member_id}
Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

## DISEASE RISK SCORES (Machine Learning Model)
"""
        
        for disease, score in risk_scores.items():
            level = self._get_risk_level(score)
            context += f"- {disease.title()}: {score:.1%} ({level})\n"
        
        context += f"\n## CONTRIBUTING FACTORS (Knowledge Graph)\n{kb_insights}\n"
        
        context += "\n## HEALTH EQUITY FACTORS (SDOH)\n"
        if sdoh_barriers:
            for barrier in sdoh_barriers:
                context += f"- {barrier}\n"
        else:
            context += "- No significant health equity barriers identified\n"
        
        context += f"\n## EVIDENCE-BASED GUIDELINES\n{guidelines}\n"
        
        context += "\n## PATIENT HEALTH METRICS\n"
        for key, value in input_data.health_metrics.items():
            context += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        return context
    
    def _format_kb_insights(self, pathways: Dict[str, Any],
                           risk_scores: Dict[str, float]) -> str:
        """Format knowledge graph insights into readable text"""
        insights = ""
        
        for disease, factors in pathways.items():
            if disease.endswith("_analysis"):
                continue
            
            if isinstance(factors, list):
                insights += f"\n**{disease.upper()}**:\n"
                insights += f"Risk Score: {risk_scores.get(disease, 0):.1%}\n"
                insights += "Contributing Factors:\n"
                for factor in factors[:5]:
                    insights += f"  - {factor}\n"
        
        return insights
    
    def _generate_sdoh_recommendations(self, sdoh_barriers: List[str]) -> List[str]:
        """Generate SDOH-specific recommendations"""
        recommendations = []
        
        for barrier in sdoh_barriers:
            if "economic" in barrier.lower():
                recommendations.append("Explore community financial assistance programs and subsidized healthcare")
            elif "healthcare" in barrier.lower():
                recommendations.append("Utilize community health centers and telehealth options")
            elif "food" in barrier.lower():
                recommendations.append("Access food assistance programs and nutrition counseling")
            elif "social" in barrier.lower():
                recommendations.append("Join community health groups and support networks")
            elif "education" in barrier.lower():
                recommendations.append("Enroll in health literacy programs specific to your conditions")
        
        return recommendations
    
    def _generate_next_steps(self, risk_scores: Dict[str, float],
                            sdoh_barriers: List[str]) -> List[str]:
        """Generate actionable next steps"""
        steps = []
        
        # Schedule screenings for high-risk diseases
        for disease, score in risk_scores.items():
            if score > 0.6:
                steps.append(f"Schedule {disease} screening with healthcare provider")
        
        # Address SDOH factors
        if sdoh_barriers:
            steps.append("Connect with community resources to address social determinants")
        
        # General steps
        steps.append("Begin lifestyle modifications (exercise, diet)")
        steps.append("Schedule follow-up assessment in 3-6 months")
        
        return steps
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from assessment text"""
        recommendations = []
        
        # Simple extraction - look for numbered items or bullet points
        lines = text.split('\n')
        for line in lines:
            if line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')):
                recommendation = line.strip().lstrip('-•*0123456789. ')
                if len(recommendation) > 10:
                    recommendations.append(recommendation)
        
        return recommendations[:5]  # Return top 5
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from assessment text"""
        action_items = []
        
        # Extract items related to actions
        if "action" in text.lower() or "step" in text.lower():
            lines = text.split('\n')
            for line in lines:
                if any(word in line.lower() for word in ["schedule", "monitor", "reduce", "increase", "avoid", "contact"]):
                    item = line.strip().lstrip('-•*0123456789. ')
                    if len(item) > 10:
                        action_items.append(item)
        
        return action_items[:5]  # Return top 5
    
    @staticmethod
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
