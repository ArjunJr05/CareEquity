#!/usr/bin/env python3
"""
Agent 4: Intervention & Care Plan Synthesizer
Synthesizes clinical risk, geographic determinants, live public health surveillance,
and localized resources into concise, high-impact SDOH interventions and a clean report.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from models.schemas import (
    RiskCase,
    HealthAnalysisResult,
    GeographicResult,
    ResourceResult,
    LiveHealthIntelligence,
    Intervention,
)
from config.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class ReportSynthesizerAgent:
    """Agent 4: Synthesizes final actionable interventions and concise SDOH care plan."""

    def __init__(self):
        self.llm = get_llm_client()

    def synthesize(
        self,
        risk_case: RiskCase,
        health_analysis: HealthAnalysisResult,
        geographic_analysis: GeographicResult,
        local_resources: ResourceResult,
        live_surveillance: Optional[LiveHealthIntelligence] = None
    ) -> Tuple[List[Intervention], str, str]:
        """
        Synthesize tailored interventions and generate a crisp, concise report.
        Returns: (interventions_list, markdown_report_string, provider_used)
        """
        location = geographic_analysis.location or risk_case.geography or "Urban Area"
        conditions_str = ", ".join(risk_case.chronic_conditions or ["Chronic conditions"])

        # 1. Build Targeted Interventions
        interventions = self._build_interventions(
            risk_case, health_analysis, geographic_analysis, local_resources, live_surveillance
        )

        # 2. Concise Clinical Impact Summary
        live_context = ""
        if live_surveillance and live_surveillance.active_disease_alerts:
            live_context = f"\nActive Local Outbreaks ({location}): " + "; ".join(live_surveillance.active_disease_alerts[:2])

        prompt = f"""Summarize in 2 concise sentences how addressing these SDOH barriers and local disease conditions will directly stabilize patient {risk_case.case_id} ({conditions_str}, {risk_case.risk_level.upper()} Risk in {location}):
{live_context}"""

        system_prompt = "You are a Chief Medical Officer. Keep summaries concise, clear, and direct (max 2 sentences)."
        llm_summary, provider_used = self.llm.generate(prompt, system_prompt=system_prompt, max_tokens=150)

        # 3. Assemble Clean & Concise Comprehensive Report
        report_md = self._format_concise_report(
            risk_case=risk_case,
            health_analysis=health_analysis,
            geographic_analysis=geographic_analysis,
            local_resources=local_resources,
            live_surveillance=live_surveillance,
            interventions=interventions,
            clinical_summary=llm_summary.strip() if llm_summary else "Targeted SDOH support directly stabilizes chronic disease outcomes and prevents avoidable hospital utilization."
        )

        return interventions, report_md, provider_used

    def _build_interventions(
        self,
        risk_case: RiskCase,
        health: HealthAnalysisResult,
        geo: GeographicResult,
        res: ResourceResult,
        live: Optional[LiveHealthIntelligence] = None
    ) -> List[Intervention]:
        """Construct structured concise interventions."""
        interventions = []
        loc = geo.location

        # Respiratory outbreak flag
        respiratory_alert = False
        if live and live.active_disease_alerts:
            for alert in live.active_disease_alerts:
                if any(w in alert.lower() for w in ["respiratory", "flu", "covid", "rsv", "air quality", "asthma"]):
                    respiratory_alert = True
                    break

        # 1. Transportation
        if risk_case.transportation or not interventions:
            transit_prog = res.transportation_programs[0] if res.transportation_programs else "Medical Transit Vouchers"
            interventions.append(
                Intervention(
                    name=f"Medical Transportation Program ({loc})",
                    target_sdoh="Transportation",
                    description=f"Pre-scheduled ride vouchers and paratransit support via {transit_prog}.",
                    specific_benefits=[
                        "Round-trip ride vouchers for clinical appointments & pharmacy",
                        "Escort support for seniors and mobility-impaired patients",
                        "Reduced-fare public transit card enrollment"
                    ],
                    how_to_access=f"Call 211 or contact clinic care coordinator ({res.healthcare_providers[0] if res.healthcare_providers else 'Local Clinic'}).",
                    expected_outcome="Reduces missed appointments by 35% and improves medication refill continuity.",
                    eligibility="Medicaid/Medicare beneficiaries, seniors (65+), or low-income chronic care patients.",
                    contact_info=f"Transit Coordinator at {res.healthcare_providers[0] if res.healthcare_providers else 'Primary Clinic'} / 211.",
                    evidence_base="AJPH: Coordinated medical transit reduces 90-day acute care admissions by 24%.",
                    timeline="Vouchers active within 3-5 business days."
                )
            )

        # 2. Food & Nutrition
        if risk_case.food_access or len(interventions) < 2:
            food_svc = res.food_nutrition_services[0] if res.food_nutrition_services else "Local Food Bank Network"
            conds_lower = " ".join(risk_case.chronic_conditions).lower()
            diet_type = "Diabetic & Low-Sodium Grocery Support" if "diabetes" in conds_lower or "hypertension" in conds_lower else "Medically Tailored Food Access"
            
            interventions.append(
                Intervention(
                    name=f"Food & Medical Nutrition Support",
                    target_sdoh="Food Insecurity",
                    description=f"{diet_type} and nutrition counseling through {food_svc}.",
                    specific_benefits=[
                        "Bi-weekly condition-tailored fresh food and produce boxes",
                        "1-on-1 registered dietitian guidance",
                        "SNAP/EBT fresh food voucher matching"
                    ],
                    how_to_access="Request a 'Food Rx' from your physician or register directly with food pantry partner.",
                    expected_outcome="Lowers HbA1c by ~0.8% and improves blood pressure regulation in 6 months.",
                    eligibility="Patients with diagnosed chronic conditions facing food access limitations.",
                    contact_info=f"{food_svc} / Hospital Social Work.",
                    evidence_base="JAMA Internal Medicine: Tailored nutrition reduces all-cause hospitalizations by 49%.",
                    timeline="Immediate pantry access; meal deliveries start within 7 days."
                )
            )

        # 3. Live Disease Outbreak / Prevention
        if respiratory_alert:
            interventions.append(
                Intervention(
                    name=f"Outbreak Prevention & Vaccine Access ({loc})",
                    target_sdoh="Infectious Disease Risk",
                    description=f"Outbreak response in {loc}: seasonal immunization, HEPA air vouchers, and telehealth triage.",
                    specific_benefits=[
                        "In-home or priority clinic vaccination (Flu, RSV, COVID)",
                        "HEPA air filtration vouchers for in-home allergen & viral safety",
                        "Telehealth triage line to avoid emergency room exposure"
                    ],
                    how_to_access=f"Contact {res.healthcare_providers[0] if res.healthcare_providers else 'Local Health Center'} or 211.",
                    expected_outcome="Decreases acute viral exacerbations and emergency visits by 40%.",
                    eligibility="High-risk pulmonary, cardiac, or diabetic patients in active alert zones.",
                    contact_info="Clinic Care Coordinator / Municipal Health Dept.",
                    evidence_base="Lancet Respiratory Medicine: Outpatient vaccination & air filters reduce viral ED visits by 37%.",
                    timeline="Immediate appointment scheduling."
                )
            )

        # 4. Financial Assistance
        if risk_case.economic_stability or risk_case.employment or len(interventions) < 3:
            interventions.append(
                Intervention(
                    name="Prescription & Healthcare Cost Relief",
                    target_sdoh="Financial Hardship",
                    description="Co-pay assistance, sliding-fee scale clinic conversion, and utility relief.",
                    specific_benefits=[
                        "100% manufacturer drug assistance for brand maintenance meds",
                        "Sliding fee scale enrollment at local FQHC clinics",
                        "LIHEAP energy assistance subsidy to prevent shut-offs"
                    ],
                    how_to_access="Schedule an intake with the hospital or clinic financial counselor.",
                    expected_outcome="Removes prescription cost barriers, raising continuous adherence to >85%.",
                    eligibility="Uninsured, underinsured, or household income <= 400% FPL.",
                    contact_info=f"Financial Navigation at {res.healthcare_providers[0] if res.healthcare_providers else 'FQHC Center'}.",
                    evidence_base="Health Affairs: Drug assistance programs yield a 3.2x return in reduced acute hospital care.",
                    timeline="Immediate sliding-fee enrollment; PAP drug approvals in 2 weeks."
                )
            )

        # 5. Housing Support
        if risk_case.housing:
            housing_org = res.housing_financial_aid[0] if res.housing_financial_aid else "Housing Assistance Network"
            interventions.append(
                Intervention(
                    name="Housing Stabilization Program",
                    target_sdoh="Housing Instability",
                    description=f"Eviction prevention, rental relief, and housing voucher navigation through {housing_org}.",
                    specific_benefits=[
                        "Emergency rental arrears and eviction defense support",
                        "Safe medication storage & refrigeration support",
                        "Supportive housing case management"
                    ],
                    how_to_access=f"Contact {housing_org} or dial 211 for expedited housing intake.",
                    expected_outcome="Prevents displacement, stabilizing home care environment.",
                    eligibility="Households facing rental cost burden (>40% income) or displacement.",
                    contact_info=f"{housing_org} / Municipal Housing Dept.",
                    evidence_base="NEJM: Stable supportive housing correlates with a 38% decrease in ED visits.",
                    timeline="Emergency aid within 48-72 hours."
                )
            )

        return interventions[:3]

    def _format_concise_report(
        self,
        risk_case: RiskCase,
        health_analysis: HealthAnalysisResult,
        geographic_analysis: GeographicResult,
        local_resources: ResourceResult,
        live_surveillance: Optional[LiveHealthIntelligence],
        interventions: List[Intervention],
        clinical_summary: str
    ) -> str:
        """Format a clean, concise, high-density Markdown report."""
        timestamp = datetime.now().strftime("%B %d, %Y")
        location = geographic_analysis.location
        conditions_str = ", ".join(risk_case.chronic_conditions or ["Chronic conditions"])

        # SDOH tags
        sdoh_tags = []
        if risk_case.transportation: sdoh_tags.append("Transportation")
        if risk_case.food_access: sdoh_tags.append("Food Access")
        if risk_case.housing: sdoh_tags.append("Housing")
        if risk_case.economic_stability: sdoh_tags.append("Financial Strain")
        if risk_case.social_isolation: sdoh_tags.append("Social Isolation")
        sdoh_line = ", ".join(sdoh_tags) if sdoh_tags else "General Support"

        # Interventions bullets
        interventions_text = ""
        for idx, item in enumerate(interventions, 1):
            interventions_text += f"""
### {idx}. {item.name} `[{item.target_sdoh}]`
- **Overview:** {item.description}
- **Benefits:** {'; '.join(item.specific_benefits[:2])}
- **Action:** {item.how_to_access}
- **Expected Outcome:** {item.expected_outcome}
- **Contact:** {item.contact_info} *(Timeline: {item.timeline})*
"""

        # Live alerts
        alerts_text = ""
        if live_surveillance and live_surveillance.active_disease_alerts:
            alerts_text = "\n".join([f"- ⚠️ **{a}**" for a in live_surveillance.active_disease_alerts])
        else:
            alerts_text = "- Standard chronic disease and seasonal respiratory monitoring active."

        # Findings
        findings_text = "\n".join([f"- **{f}**" for f in health_analysis.key_findings[:3]])

        # Resources
        providers_text = ", ".join(local_resources.healthcare_providers[:3]) if local_resources.healthcare_providers else "Community Health Centers (FQHC)"
        transit_text = ", ".join(local_resources.transportation_programs[:2]) if local_resources.transportation_programs else "Medicaid Medical Transit"
        food_text = ", ".join(local_resources.food_nutrition_services[:2]) if local_resources.food_nutrition_services else "Regional Food Bank"

        report = f"""# 🏥 CareEquity SDOH Clinical Action Plan
**Case ID:** `{risk_case.case_id}` | **Risk:** **{risk_case.risk_score:.0f}/100 ({risk_case.risk_level.upper()})** | **Location:** {location} | **Date:** {timestamp}

---

### 📋 Patient Summary & Risk Assessment
- **Conditions:** {conditions_str} (Age: {risk_case.age or 'Adult'})
- **Active SDOH Barriers:** {sdoh_line}
- **Clinical Assessment:** {health_analysis.risk_interpretation}
- **Care Goal:** *{clinical_summary}*

---

### 🔍 Key Health & SDOH Findings
{findings_text}

---

### 🌐 Live Public Health & Disease Surveillance ({location.upper()})
{alerts_text}

---

### 💡 Recommended Interventions
{interventions_text}

---

### 📍 Local Community Safety Net
- **Medical Centers:** {providers_text}
- **Transit Services:** {transit_text}
- **Food & Nutrition:** {food_text}
- **Emergency Numbers:** Medical: `911` | Community Referral: `211` | Crisis: `988`

---

### 🚀 Immediate Action Roadmap
1. **Week 1:** Review plan with care coordinator & dial `211` for prioritized food/transit enrollment.
2. **Weeks 2-4:** Complete copay relief forms and confirm transportation for next clinical visit.
3. **Months 2-6:** Target biometric stabilization (A1C < 7.5%, BP < 130/80 mmHg) and zero emergency visits.
"""
        return report.strip()
