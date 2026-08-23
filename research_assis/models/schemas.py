#!/usr/bin/env python3
"""
Data models and schemas for CareEquity SDOH 4-Agent Research Assistant with Live Web Health Surveillance.
"""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RiskCase(BaseModel):
    """Input representing a patient risk case and SDOH assessment."""
    
    case_id: str
    member_id: Optional[str] = None
    age: Optional[int] = 45
    age_group: Optional[str] = None
    geography: Optional[str] = "Urban - NYC"
    zip_code: Optional[str] = None
    
    # Risk Assessment
    risk_score: float = Field(default=70.0, ge=0, le=100)
    risk_level: Literal["low", "moderate", "high", "critical", "very high"] = "high"
    
    # Clinical factors
    clinical_risk_factors: List[str] = Field(default_factory=list)
    chronic_conditions: List[str] = Field(default_factory=list)
    
    # SDOH Barrier Indicators
    transportation: Optional[bool] = False
    housing: Optional[bool] = False
    food_access: Optional[bool] = False
    economic_stability: Optional[bool] = False
    employment: Optional[bool] = False
    social_isolation: Optional[bool] = False
    digital_access: Optional[bool] = False
    language_barriers: Optional[bool] = False
    education_access: Optional[bool] = False
    healthcare_access: Optional[bool] = False
    neighborhood_environment: Optional[bool] = False
    social_community_context: Optional[bool] = False
    
    # Extra Context
    sdoh_factors: Dict[str, bool] = Field(default_factory=dict)
    utilization_metrics: Dict[str, Any] = Field(default_factory=dict)
    recent_ed_visits: Optional[int] = 0
    missed_appointments: Optional[int] = 0
    socioeconomic_context: Optional[str] = None
    environmental_context: Optional[str] = None
    intervention_goal: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None


class HealthAnalysisResult(BaseModel):
    """Output from Agent 1: Health & SDOH Risk Analyzer."""
    case_id: str
    risk_level: str
    risk_score: float
    condition_impacts: List[str] = Field(default_factory=list)
    sdoh_impacts: List[str] = Field(default_factory=list)
    age_factors: List[str] = Field(default_factory=list)
    risk_interpretation: str = ""
    key_findings: List[str] = Field(default_factory=list)
    provider_used: str = ""


class GeographicResult(BaseModel):
    """Output from Agent 2: Geographic & Environment Specialist."""
    location: str
    area_health_profile: str = ""
    health_disparities: str = ""
    environmental_factors: str = ""
    sdoh_challenges: str = ""
    demographics: Dict[str, Any] = Field(default_factory=dict)
    health_statistics: Dict[str, Any] = Field(default_factory=dict)
    provider_used: str = ""


class LiveHealthIntelligence(BaseModel):
    """Output from Live Web Search Intelligence Agent."""
    location: str
    search_queries: List[str] = Field(default_factory=list)
    active_disease_alerts: List[str] = Field(default_factory=list)
    public_health_trends: List[str] = Field(default_factory=list)
    recent_news_snippets: List[Dict[str, str]] = Field(default_factory=list)
    surveillance_summary: str = ""
    provider_used: str = ""


class ResourceResult(BaseModel):
    """Output from Agent 3: Local Resource & Service Locator."""
    location: str
    healthcare_providers: List[str] = Field(default_factory=list)
    transportation_programs: List[str] = Field(default_factory=list)
    food_nutrition_services: List[str] = Field(default_factory=list)
    housing_financial_aid: List[str] = Field(default_factory=list)
    community_organizations: List[str] = Field(default_factory=list)
    emergency_contacts: Dict[str, str] = Field(default_factory=dict)
    provider_used: str = ""


class Intervention(BaseModel):
    """Structured SDOH intervention recommendation."""
    name: str
    target_sdoh: str
    description: str
    specific_benefits: List[str] = Field(default_factory=list)
    how_to_access: str
    expected_outcome: str
    eligibility: str
    contact_info: str
    evidence_base: str
    timeline: str


class CompleteAnalysisReport(BaseModel):
    """Final synthesized output from multi-agent pipeline."""
    status: Literal["SUCCESS", "ERROR"] = "SUCCESS"
    case_id: str
    execution_time_seconds: float = 0.0
    patient_profile: RiskCase
    health_analysis: HealthAnalysisResult
    geographic_analysis: GeographicResult
    live_surveillance: LiveHealthIntelligence = Field(default_factory=lambda: LiveHealthIntelligence(location=""))
    local_resources: ResourceResult
    interventions: List[Intervention] = Field(default_factory=list)
    comprehensive_report: str = ""
    providers_used: Dict[str, str] = Field(default_factory=dict)
    error: Optional[str] = None
