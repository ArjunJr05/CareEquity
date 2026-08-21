#!/usr/bin/env python3
"""
CareEquity SDOH Multi-Agent Orchestration Engine with Live Web Health Surveillance.

Executes:
- Agent 1: Health & SDOH Risk Analyzer
- Agent 2: Geographic & Environment Specialist
- Agent 3: Local Resource & Service Locator
- Live Web Search: Real-time Public Health & Disease Surveillance Agent
in parallel via ThreadPoolExecutor, then synthesizes comprehensive results in Agent 4 (Synthesizer).
"""

import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from models.schemas import (
    RiskCase,
    HealthAnalysisResult,
    GeographicResult,
    ResourceResult,
    LiveHealthIntelligence,
    CompleteAnalysisReport,
)
from agents.health_analyzer import HealthAnalyzerAgent
from agents.geographic_agent import GeographicAgent
from agents.resource_locator import ResourceLocatorAgent
from agents.web_search_agent import WebSearchAgent
from agents.report_synthesizer import ReportSynthesizerAgent
from config.settings import settings

logger = logging.getLogger(__name__)


class SDOHWorkflowOrchestrator:
    """High-speed parallel orchestrator for SDOH agents with live web surveillance."""

    def __init__(self):
        self.health_agent = HealthAnalyzerAgent()
        self.geographic_agent = GeographicAgent()
        self.resource_agent = ResourceLocatorAgent()
        self.web_search_agent = WebSearchAgent()
        self.synthesizer_agent = ReportSynthesizerAgent()
        logger.info("Initialized CareEquity SDOH Multi-Agent Orchestrator with Live Web Surveillance")

    def run(self, risk_case: RiskCase) -> CompleteAnalysisReport:
        """
        Execute multi-agent pipeline with Phase 1 parallel execution.
        Total execution time: ~1-3 seconds.
        """
        start_time = time.time()
        logger.info(f"Starting multi-agent analysis for patient {risk_case.case_id} ({risk_case.geography})")

        try:
            # Phase 1: Concurrent execution of Health, Geo, Resources, and Live Web Search
            with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
                future_health = executor.submit(self.health_agent.analyze, risk_case)
                future_geo = executor.submit(self.geographic_agent.analyze, risk_case)
                future_res = executor.submit(self.resource_agent.find_resources, risk_case)
                future_web = executor.submit(self.web_search_agent.search_live_health, risk_case)

                health_result: HealthAnalysisResult = future_health.result()
                geo_result: GeographicResult = future_geo.result()
                res_result: ResourceResult = future_res.result()
                live_surveillance: LiveHealthIntelligence = future_web.result()

            # Phase 2: Synthesis in Agent 4
            interventions, report_md, syn_provider = self.synthesizer_agent.synthesize(
                risk_case=risk_case,
                health_analysis=health_result,
                geographic_analysis=geo_result,
                local_resources=res_result,
                live_surveillance=live_surveillance
            )

            elapsed = round(time.time() - start_time, 2)
            providers_used = {
                "Agent 1 (Health Analyzer)": health_result.provider_used or "Knowledge Base",
                "Agent 2 (Geographic Specialist)": geo_result.provider_used or "Knowledge Base",
                "Agent 3 (Resource Locator)": res_result.provider_used or "Knowledge Base",
                "Live Web Surveillance": live_surveillance.provider_used or "Web Search",
                "Agent 4 (Report Synthesizer)": syn_provider or "Knowledge Base"
            }

            logger.info(f"Multi-agent pipeline completed in {elapsed}s for case {risk_case.case_id}")

            return CompleteAnalysisReport(
                status="SUCCESS",
                case_id=risk_case.case_id,
                execution_time_seconds=elapsed,
                patient_profile=risk_case,
                health_analysis=health_result,
                geographic_analysis=geo_result,
                live_surveillance=live_surveillance,
                local_resources=res_result,
                interventions=interventions,
                comprehensive_report=report_md,
                providers_used=providers_used
            )

        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            logger.error(f"Multi-agent pipeline error: {e}", exc_info=True)
            return CompleteAnalysisReport(
                status="ERROR",
                case_id=risk_case.case_id,
                execution_time_seconds=elapsed,
                patient_profile=risk_case,
                health_analysis=HealthAnalysisResult(case_id=risk_case.case_id, risk_level=risk_case.risk_level, risk_score=risk_case.risk_score),
                geographic_analysis=GeographicResult(location=risk_case.geography or "Urban Area"),
                live_surveillance=LiveHealthIntelligence(location=risk_case.geography or "Urban Area"),
                local_resources=ResourceResult(location=risk_case.geography or "Urban Area"),
                error=str(e),
                comprehensive_report=f"# Error Generating Report\nAn error occurred during multi-agent analysis: {e}"
            )


# Global workflow instance
_orchestrator: Optional[SDOHWorkflowOrchestrator] = None

def get_orchestrator() -> SDOHWorkflowOrchestrator:
    """Get singleton workflow orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SDOHWorkflowOrchestrator()
    return _orchestrator


def run_sdoh_analysis(risk_case: RiskCase) -> CompleteAnalysisReport:
    """Convenience function to run complete analysis on a RiskCase."""
    return get_orchestrator().run(risk_case)
