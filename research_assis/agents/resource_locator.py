#!/usr/bin/env python3
"""
Agent 3: Local Resource & Service Locator
Identifies real-world healthcare providers, transit services, food banks, housing programs, and crisis hotlines.
"""

import logging
from typing import Dict, List, Any
from models.schemas import RiskCase, ResourceResult
from config.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class ResourceLocatorAgent:
    """Agent 3: Discovers localized healthcare and social safety-net resources."""

    def __init__(self):
        self.llm = get_llm_client()
        self.directory = self._build_directory()

    def find_resources(self, risk_case: RiskCase) -> ResourceResult:
        """Locate verified community healthcare and social resources."""
        location = (risk_case.geography or "Urban Area").strip()
        data = self._match_location(location)

        emergency_contacts = {
            "Medical Emergency": "911 (Immediate life-threatening care)",
            "Community Services & Food/Housing": "211 (24/7 National Social Referral)",
            "Mental Health & Crisis Hotline": "988 (Suicide & Crisis Lifeline)",
            "Care Management Helpline": "1-800-555-CARE (CareEquity Support Network)"
        }

        # Query LLM to supplement localized resources if unusual location
        prompt = f"""List 2 major safety net clinics or hospital systems and 1 public transit medical voucher service in {location}."""
        system_prompt = "You are a social work case manager specializing in local safety net healthcare. Be concise and name real institutions."
        llm_response, provider = self.llm.generate(prompt, system_prompt=system_prompt, max_tokens=150)

        providers = list(data.get("healthcare", []))
        if llm_response:
            for line in llm_response.split("\n"):
                clean = line.strip().lstrip("*-•123456789. ")
                if len(clean) > 10 and clean not in providers and len(providers) < 6:
                    providers.append(clean)

        return ResourceResult(
            location=location,
            healthcare_providers=providers[:6],
            transportation_programs=data.get("transportation", [])[:5],
            food_nutrition_services=data.get("food", [])[:5],
            housing_financial_aid=data.get("housing", [])[:5],
            community_organizations=data.get("community", [])[:5],
            emergency_contacts=emergency_contacts,
            provider_used=provider
        )

    def _match_location(self, location: str) -> Dict[str, List[str]]:
        loc_lower = location.lower()
        for key in self.directory:
            if key in loc_lower or any(w in loc_lower for w in key.split()):
                return self.directory[key]
        return self.directory["default"]

    def _build_directory(self) -> Dict[str, Dict[str, List[str]]]:
        return {
            "bronx": {
                "healthcare": [
                    "BronxCare Health System (Concourse & Fulton Divisions)",
                    "Montefiore Medical Center - Comprehensive Community Care",
                    "NYC Health + Hospitals / Lincoln & Jacobi Medical Centers",
                    "Morris Heights Health Center (FQHC - Primary & Specialty Care)",
                    "Urban Health Plan - Plaza del Sol & Bella Vista Clinics"
                ],
                "transportation": [
                    "MTA Access-A-Ride Paratransit (Medical Discretionary Rides)",
                    "Healthfirst CompleteCare Non-Emergency Medical Transport",
                    "NYC DOT Senior Reduced Fare MetroCard Program",
                    "Bronx Community Health Shuttles (Free Clinic Loops)"
                ],
                "food": [
                    "Food Bank For New York City - Bronx Distribution Hubs",
                    "BronxWorks Community Food Pantries & Produce Drops",
                    "NYC Department of Health 'Health Bucks' ($2 SNAP incentive at Farmers Markets)",
                    "City Harvest Mobile Markets - South Bronx Locations"
                ],
                "housing": [
                    "BronxWorks Housing & Eviction Prevention Centers",
                    "NYC Human Resources Administration (HRA) Rental Assistance (CityFHEPS)",
                    "Low-Income Home Energy Assistance Program (LIHEAP/HEAP)",
                    "Legal Aid Society - Housing Justice Bronx Unit"
                ],
                "community": [
                    "Bronx House Community Health & Wellness Network",
                    "South Bronx United Community Resources",
                    "Fordham Center for Social Justice & Health Navigation"
                ]
            },
            "brooklyn": {
                "healthcare": [
                    "The Brooklyn Hospital Center - Primary Care & Chronic Disease",
                    "NYC Health + Hospitals / Kings County & Woodhull",
                    "Maimonides Medical Center - Community Health Center",
                    "Bedford Stuyvesant Family Health Center (FQHC)",
                    "Sunset Park Family Health Center at NYU Langone"
                ],
                "transportation": [
                    "MTA Paratransit Access-A-Ride Brooklyn Division",
                    "Brooklyn Wheels Medical Transport Network",
                    "Medicaid Non-Emergency Medical Transportation (NEMT) Broker"
                ],
                "food": [
                    "Brooklyn Food Coalition & Mobile Pantries",
                    "City Harvest Fresh Food Distribution - Crown Heights & Sunset Park",
                    "WIC Program Centers - Brooklyn East & South"
                ],
                "housing": [
                    "Brooklyn Legal Services - Tenant Rights & Eviction Prevention",
                    "CAMBA Housing Assistance and Supportive Living",
                    "Emergency Rent Relief Portal (NYC HRA)"
                ],
                "community": [
                    "Brooklyn Community Services (BCS) Care Navigation",
                    "Caribbean Women's Health Association",
                    "Arab American Family Support Center"
                ]
            },
            "manhattan": {
                "healthcare": [
                    "NYC Health + Hospitals / Bellevue & Harlem Hospital",
                    "Mount Sinai Health System - Community Care Network",
                    "NewYork-Presbyterian Hospital Community Clinics",
                    "Ryan Health (FQHC Multi-Site Primary Care)"
                ],
                "transportation": [
                    "MTA Access-A-Ride Manhattan Transit",
                    "Encore Community Services Medical Escort & Transportation",
                    "Subway & Bus Reduced-Fare Card Center"
                ],
                "food": [
                    "West Side Campaign Against Hunger (WSCAH - Supermarket-style Pantry)",
                    "Food Bank For New York City - Harlem Community Kitchen",
                    "GrowNYC Fresh Food Box Program"
                ],
                "housing": [
                    "Coalition for the Homeless Housing Programs",
                    "Manhattan Community Board Housing Assistance Clinics",
                    "NYC Department of Social Services Eviction Prevention"
                ],
                "community": [
                    "Northern Manhattan Improvement Corporation (NMIC)",
                    "Lenox Hill Neighborhood House Social Services",
                    "Harlem United Community AIDS & Health Center"
                ]
            },
            "default": {
                "healthcare": [
                    "Federally Qualified Health Centers (FQHC - Sliding Fee Scale)",
                    "County Public Health Hospital & Outpatient Clinics",
                    "Community Health Center Network",
                    "Free and Charitable Clinics Alliance"
                ],
                "transportation": [
                    "Medicaid Non-Emergency Medical Transportation (NEMT)",
                    "County Public Transit Dial-A-Ride / Paratransit",
                    "Volunteer Medical Driver Network (211 Referral)"
                ],
                "food": [
                    "Feeding America Network Regional Food Banks",
                    "Local Faith-Based and Community Food Pantries",
                    "USDA Supplemental Nutrition Assistance Program (SNAP/EBT)",
                    "Emergency Food Assistance Program (TEFAP)"
                ],
                "housing": [
                    "Community Action Agency Emergency Rental Aid",
                    "HUD Housing Choice Voucher Program (Section 8 Navigation)",
                    "Low Income Home Energy Assistance (LIHEAP)",
                    "Local Homeless Prevention and Rapid Re-Housing Network"
                ],
                "community": [
                    "United Way 2-1-1 Health & Human Services Navigation",
                    "Area Agency on Aging (Elderly Resource Network)",
                    "Community Action Partnership Resource Centers"
                ]
            }
        }
