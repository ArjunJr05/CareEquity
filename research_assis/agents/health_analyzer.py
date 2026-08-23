#!/usr/bin/env python3
"""
Agent 1: Clinical & SDOH Risk Analyzer
Analyzes chronic conditions, age dynamics, and SDOH barrier impacts.
"""

import logging
from typing import List, Dict
from models.schemas import RiskCase, HealthAnalysisResult
from config.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class HealthAnalyzerAgent:
    """Agent 1: Evaluates clinical health profiles, disease risks, and SDOH impacts."""

    def __init__(self):
        self.llm = get_llm_client()

    def analyze(self, risk_case: RiskCase) -> HealthAnalysisResult:
        """Run health and SDOH risk analysis."""
        conditions = risk_case.chronic_conditions or risk_case.clinical_risk_factors or ["General Health Management"]
        conditions_str = ", ".join(conditions)

        # Identified SDOH factors
        sdoh_active = []
        if risk_case.transportation:
            sdoh_active.append("Transportation Barriers")
        if risk_case.food_access:
            sdoh_active.append("Food Insecurity / Nutrition Deficit")
        if risk_case.housing:
            sdoh_active.append("Housing Instability")
        if risk_case.economic_stability or risk_case.employment:
            sdoh_active.append("Financial / Employment Hardship")
        if risk_case.social_isolation:
            sdoh_active.append("Social Isolation")

        # 1. Base rule-based clinical insights
        condition_impacts = self._get_condition_impacts(conditions)
        sdoh_impacts = self._get_sdoh_impacts(risk_case)
        age_factors = self._get_age_factors(risk_case.age or 45)
        risk_interpretation = self._interpret_risk(risk_case.risk_score, risk_case.risk_level)

        # 2. LLM Enrichment (Optional / Fast)
        prompt = f"""You are a clinical SDOH specialist. Analyze this patient profile in 3 concise bullet points:
Conditions: {conditions_str}
Risk Level: {risk_case.risk_level} ({risk_case.risk_score}/100)
SDOH Barriers: {', '.join(sdoh_active) if sdoh_active else 'None identified'}
Age: {risk_case.age}

Provide 3 specific clinical impact statements linking their SDOH barriers to disease complications."""

        system_prompt = "You are a healthcare analytics AI specializing in Social Determinants of Health (SDOH). Keep answers clinical, accurate, and concise."
        llm_response, provider_used = self.llm.generate(prompt, system_prompt=system_prompt, max_tokens=300)

        llm_findings = []
        if llm_response:
            for line in llm_response.split("\n"):
                clean = line.strip().lstrip("*-•123456789. ")
                if len(clean) > 20:
                    llm_findings.append(clean)

        key_findings = (llm_findings[:3] if llm_findings else condition_impacts[:2] + sdoh_impacts[:2])

        return HealthAnalysisResult(
            case_id=risk_case.case_id,
            risk_level=risk_case.risk_level,
            risk_score=risk_case.risk_score,
            condition_impacts=condition_impacts,
            sdoh_impacts=sdoh_impacts,
            age_factors=age_factors,
            risk_interpretation=risk_interpretation,
            key_findings=key_findings,
            provider_used=provider_used
        )

    def _get_condition_impacts(self, conditions: List[str]) -> List[str]:
        impacts = []
        text = " ".join(conditions).lower()
        if "diabetes" in text:
            impacts.append("Diabetes requires strict glycaemic control, routine A1C monitoring, and diabetic eye/foot exams.")
            impacts.append("Uncontrolled diabetes accelerates microvascular damage, retinopathy, and renal impairment.")
        if "hypertension" in text or "blood pressure" in text:
            impacts.append("Hypertension demands continuous blood pressure tracking, sodium restriction, and medication adherence.")
            impacts.append("Sustained high blood pressure elevates the 5-year probability of myocardial infarction and stroke.")
        if "heart" in text or "cardiac" in text or "failure" in text:
            impacts.append("Cardiovascular conditions necessitate strict fluid/salt tracking, cardiology follow-ups, and early symptom detection.")
        if "copd" in text or "asthma" in text:
            impacts.append("Respiratory conditions require timely inhaler refills, trigger avoidance, and rapid exacerbation protocols.")
        if "depression" in text or "anxiety" in text:
            impacts.append("Behavioral health concerns significantly compound medication non-adherence and self-care fatigue.")
        if not impacts:
            impacts.append("Multi-morbid chronic disease requires integrated primary care coordination and proactive monitoring.")
        return impacts

    def _get_sdoh_impacts(self, risk_case: RiskCase) -> List[str]:
        impacts = []
        if risk_case.transportation:
            impacts.append("Transportation barriers correlate with 30-40% higher missed appointments and delayed prescription pick-ups.")
        if risk_case.food_access:
            impacts.append("Food insecurity forces trade-offs between groceries and prescription copays, destabilizing blood sugar & BP.")
        if risk_case.housing:
            impacts.append("Housing instability induces chronic neuroendocrine stress and impedes safe medication storage (e.g. refrigerated insulin).")
        if risk_case.economic_stability:
            impacts.append("Financial strain leads to medication rationing, skipped doses, and avoided preventative screenings.")
        if risk_case.social_isolation:
            impacts.append("Social isolation increases 30-day readmission risks and impairs recovery follow-through.")
        if not impacts:
            impacts.append("Stable social determinants provide a strong foundation for outpatient chronic care adherence.")
        return impacts

    def _get_age_factors(self, age: int) -> List[str]:
        if age >= 65:
            return ["Geriatric considerations: Elevated polypharmacy risk, fall vulnerability, and Medicare coordination needs."]
        elif age >= 50:
            return ["Middle-aged cohort: Balancing occupational/caregiver demands with escalating preventative screening schedules."]
        elif age < 35:
            return ["Young adult cohort: Potential gaps in regular primary care continuity and insurance transitions."]
        return ["Adult population: Prioritizing routine biometric screenings and lifestyle modifications."]

    def _interpret_risk(self, score: float, level: str) -> str:
        lvl = level.lower()
        if lvl in ["critical", "very high"] or score >= 80:
            return f"Critical Risk Tier ({score:.0f}/100): Immediate multidisciplinary case management and SDOH emergency stabilization required."
        elif lvl == "high" or score >= 60:
            return f"High Risk Tier ({score:.0f}/100): Proactive outpatient care management and targeted community referral recommended."
        elif lvl == "moderate" or score >= 40:
            return f"Moderate Risk Tier ({score:.0f}/100): Preventative interventions and community resource connection advised."
        return f"Low Risk Tier ({score:.0f}/100): Standard preventative maintenance and routine health education."
