#!/usr/bin/env python3
"""
Agent 2: Geographic & Environment Specialist
Analyzes location-based health determinants, demographics, environmental factors, and health equity disparities.
"""

import logging
from typing import Dict, Any
from models.schemas import RiskCase, GeographicResult
from config.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class GeographicAgent:
    """Agent 2: Maps geographical and environmental factors affecting patient health."""

    def __init__(self):
        self.llm = get_llm_client()
        self.knowledge_base = self._build_geo_knowledge()

    def analyze(self, risk_case: RiskCase) -> GeographicResult:
        """Analyze area-specific health environment."""
        location = (risk_case.geography or "Urban Area").strip()
        data = self._get_area_data(location)

        demographics = data.get("demographics", {})
        health_stats = data.get("health_stats", {})
        env = data.get("environment", {})
        sdoh_data = data.get("sdoh_factors", {})
        equity = data.get("health_equity", {})

        # Build comprehensive descriptions
        area_profile = f"{location} features a median age of {demographics.get('median_age', 36)} years with an estimated {demographics.get('poverty_rate', 18)}% poverty rate. Area health data indicates {health_stats.get('diabetes_rate', 12)}% diabetes prevalence, {health_stats.get('hypertension_rate', 35)}% hypertension prevalence, and {health_stats.get('obesity_rate', 28)}% obesity."
        
        disparities = []
        if equity.get("racial_disparities", False):
            disparities.append("Marked racial/ethnic health disparities present in chronic disease complications.")
        if equity.get("income_disparities", True):
            disparities.append("Lower-income census tracts experience 35-45% higher rates of avoidable emergency department admissions.")
        if equity.get("language_barriers", False):
            disparities.append("Non-English primary language households encounter navigation and interpretation gaps.")
        disparities_text = " ".join(disparities) or "Manageable disparities addressed by regional community health coalitions."

        env_factors = []
        env_factors.append(f"Air quality rating: {env.get('air_quality', 'moderate').upper()}.")
        if env.get("food_deserts", False):
            env_factors.append("Classified USDA food desert pockets present, restricting access to affordable fresh produce.")
        else:
            env_factors.append("Adequate supermarket and fresh food density across primary residential corridors.")
        env_factors.append(f"Walkability index is rated {env.get('walkability', 'moderate').upper()} for daily mobility.")
        env_text = " ".join(env_factors)

        sdoh_challenges = f"Housing cost burden affects {sdoh_data.get('housing_cost_burden', 35)}% of households. Public transit accessibility is rated {sdoh_data.get('public_transit', 'moderate')}. Regional unemployment rate stands at {sdoh_data.get('unemployment_rate', 7.5)}%."

        # Quick LLM insight for geographic localization
        prompt = f"""Provide 2 quick sentences on key public health challenges for a chronic disease patient living in: {location}. Focus on transportation, food access, and healthcare equity."""
        system_prompt = "You are a public health and urban epidemiology expert. Keep answers factual and brief."
        llm_response, provider = self.llm.generate(prompt, system_prompt=system_prompt, max_tokens=150)

        if llm_response and len(llm_response.strip()) > 30:
            area_profile = area_profile + " " + llm_response.strip()

        return GeographicResult(
            location=location,
            area_health_profile=area_profile,
            health_disparities=disparities_text,
            environmental_factors=env_text,
            sdoh_challenges=sdoh_challenges,
            demographics=demographics,
            health_statistics=health_stats,
            provider_used=provider
        )

    def _get_area_data(self, location: str) -> Dict[str, Any]:
        loc_lower = location.lower()
        for key in self.knowledge_base:
            if key in loc_lower or any(word in loc_lower for word in key.split()):
                return self.knowledge_base[key]
        return self.knowledge_base["default_urban"]

    def _build_geo_knowledge(self) -> Dict[str, Any]:
        return {
            "bronx": {
                "demographics": {"median_age": 34, "poverty_rate": 28, "population": 1400000},
                "health_stats": {"diabetes_rate": 16, "hypertension_rate": 42, "obesity_rate": 35},
                "health_equity": {"racial_disparities": True, "income_disparities": True, "language_barriers": True},
                "environment": {"air_quality": "moderate", "food_deserts": True, "walkability": "moderate"},
                "sdoh_factors": {"housing_cost_burden": 48, "public_transit": "good", "unemployment_rate": 11.2}
            },
            "brooklyn": {
                "demographics": {"median_age": 36, "poverty_rate": 21, "population": 2600000},
                "health_stats": {"diabetes_rate": 13, "hypertension_rate": 37, "obesity_rate": 31},
                "health_equity": {"racial_disparities": True, "income_disparities": True, "language_barriers": True},
                "environment": {"air_quality": "moderate", "food_deserts": False, "walkability": "high"},
                "sdoh_factors": {"housing_cost_burden": 44, "public_transit": "excellent", "unemployment_rate": 8.5}
            },
            "manhattan": {
                "demographics": {"median_age": 38, "poverty_rate": 16, "population": 1600000},
                "health_stats": {"diabetes_rate": 9, "hypertension_rate": 29, "obesity_rate": 21},
                "health_equity": {"racial_disparities": False, "income_disparities": True, "language_barriers": False},
                "environment": {"air_quality": "good", "food_deserts": False, "walkability": "excellent"},
                "sdoh_factors": {"housing_cost_burden": 52, "public_transit": "excellent", "unemployment_rate": 5.8}
            },
            "queens": {
                "demographics": {"median_age": 39, "poverty_rate": 17, "population": 2300000},
                "health_stats": {"diabetes_rate": 12, "hypertension_rate": 33, "obesity_rate": 26},
                "health_equity": {"racial_disparities": True, "income_disparities": True, "language_barriers": True},
                "environment": {"air_quality": "good", "food_deserts": False, "walkability": "moderate"},
                "sdoh_factors": {"housing_cost_burden": 41, "public_transit": "good", "unemployment_rate": 6.9}
            },
            "chicago": {
                "demographics": {"median_age": 35, "poverty_rate": 20, "population": 2700000},
                "health_stats": {"diabetes_rate": 14, "hypertension_rate": 36, "obesity_rate": 32},
                "health_equity": {"racial_disparities": True, "income_disparities": True, "language_barriers": True},
                "environment": {"air_quality": "moderate", "food_deserts": True, "walkability": "moderate"},
                "sdoh_factors": {"housing_cost_burden": 37, "public_transit": "good", "unemployment_rate": 9.1}
            },
            "los angeles": {
                "demographics": {"median_age": 37, "poverty_rate": 19, "population": 3850000},
                "health_stats": {"diabetes_rate": 13, "hypertension_rate": 34, "obesity_rate": 29},
                "health_equity": {"racial_disparities": True, "income_disparities": True, "language_barriers": True},
                "environment": {"air_quality": "moderate", "food_deserts": True, "walkability": "moderate"},
                "sdoh_factors": {"housing_cost_burden": 49, "public_transit": "moderate", "unemployment_rate": 8.0}
            },
            "houston": {
                "demographics": {"median_age": 34, "poverty_rate": 21, "population": 2300000},
                "health_stats": {"diabetes_rate": 15, "hypertension_rate": 38, "obesity_rate": 36},
                "health_equity": {"racial_disparities": True, "income_disparities": True, "language_barriers": True},
                "environment": {"air_quality": "moderate", "food_deserts": True, "walkability": "limited"},
                "sdoh_factors": {"housing_cost_burden": 34, "public_transit": "limited", "unemployment_rate": 7.4}
            },
            "default_urban": {
                "demographics": {"median_age": 36, "poverty_rate": 18, "population": 600000},
                "health_stats": {"diabetes_rate": 12, "hypertension_rate": 35, "obesity_rate": 28},
                "health_equity": {"racial_disparities": False, "income_disparities": True, "language_barriers": False},
                "environment": {"air_quality": "moderate", "food_deserts": False, "walkability": "moderate"},
                "sdoh_factors": {"housing_cost_burden": 35, "public_transit": "moderate", "unemployment_rate": 7.2}
            }
        }
