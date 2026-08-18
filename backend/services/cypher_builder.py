"""
Cypher query builder for Neo4j knowledge graph reasoning.
Generates queries to find disease pathways, risk factors, and interventions.
Uses the actual schema: Disease(disease_id, name, category), Factor(factor_id, name, category), etc.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class CypherQueryBuilder:
    """Builder for Neo4j Cypher queries for health risk analysis"""
    
    @staticmethod
    def get_disease_risk_factors(disease: str) -> str:
        """Get risk factors for a specific disease"""
        disease_lower = disease.lower()
        return f"""
MATCH (f:Factor)-[r:INCREASES_RISK_OF]->(d:Disease)
WHERE TOLOWER(d.name) CONTAINS "{disease_lower}" OR d.disease_id CONTAINS "{disease_lower}"
RETURN f.name as factor, f.category as category, r.evidence_strength as strength
LIMIT 10
"""
    
    @staticmethod
    def get_disease_pathways(disease: str, depth: int = 3) -> str:
        """Get disease pathways from SDOH factors"""
        disease_lower = disease.lower()
        return f"""
MATCH (d:Disease)
WHERE TOLOWER(d.name) CONTAINS "{disease_lower}" OR d.disease_id CONTAINS "{disease_lower}"
RETURN d.name as disease, d.category as category
LIMIT 5
"""
    
    @staticmethod
    def get_disease_interventions(disease: str) -> str:
        """Get interventions for a disease"""
        disease_lower = disease.lower()
        return f"""
MATCH (d:Disease)-[r:MANAGED_BY]->(i:Intervention)
WHERE TOLOWER(d.name) CONTAINS "{disease_lower}" OR d.disease_id CONTAINS "{disease_lower}"
RETURN i.name as intervention, i.category as category, r.effectiveness as effectiveness
LIMIT 10
"""
    
    @staticmethod
    def get_community_factors_for_disease(disease: str, zipcode: str = None) -> str:
        """Get community factors affecting disease"""
        disease_lower = disease.lower()
        if zipcode:
            return f"""
MATCH (c:Community {{zipcode: "{zipcode}"}})-[r1:HAS_FACTOR]->(f:Factor)
OPTIONAL MATCH (f)-[r2:INCREASES_RISK_OF]->(d:Disease)
WHERE TOLOWER(d.name) CONTAINS "{disease_lower}" OR d.disease_id CONTAINS "{disease_lower}"
RETURN f.name as sdoh_factor, c.overall_sdoh_score as sdoh_score, r2.evidence_strength as risk_strength
LIMIT 10
"""
        return ""
    
    @staticmethod
    def get_factor_disease_chain(risk_factor: str) -> str:
        """Get chain from risk factor to diseases"""
        factor_lower = risk_factor.lower()
        return f"""
MATCH (f:Factor)-[r:INCREASES_RISK_OF]->(d:Disease)
WHERE TOLOWER(f.name) CONTAINS "{factor_lower}"
RETURN DISTINCT d.name as disease
LIMIT 10
"""
    
    @staticmethod
    def get_sdoh_intervention_chain(sdoh_factor: str) -> str:
        """Get interventions for SDOH factor"""
        factor_lower = sdoh_factor.lower()
        return f"""
MATCH (f:Factor)-[r:CAN_BE_IMPROVED_BY]->(i:Intervention)
WHERE TOLOWER(f.name) CONTAINS "{factor_lower}"
RETURN i.name as intervention, i.category as category, r.effectiveness as effectiveness
LIMIT 10
"""
    
    @staticmethod
    def get_similar_patients(member_risk_profile: Dict[str, float], limit: int = 5) -> str:
        """Find similar patients in knowledge graph"""
        return """
MATCH (m)
WHERE m:Member OR m:Patient
RETURN COALESCE(m.member_id, m.patient_id, "") as member_id, 
       COALESCE(m.age, 0) as age
LIMIT ?
"""
    
    @staticmethod
    def get_outcome_statistics(disease: str) -> str:
        """Get outcomes for disease"""
        disease_lower = disease.lower()
        return f"""
MATCH (d:Disease)
WHERE TOLOWER(d.name) CONTAINS "{disease_lower}" OR d.disease_id CONTAINS "{disease_lower}"
RETURN d.name as disease
LIMIT 5
"""
    
    @staticmethod
    def get_medication_disease_relationship(disease: str) -> str:
        """Get medications for a disease"""
        disease_lower = disease.lower()
        return f"""
MATCH (m:Medication)-[r:TREATS]->(d:Disease)
WHERE TOLOWER(d.name) CONTAINS "{disease_lower}" OR d.disease_id CONTAINS "{disease_lower}"
RETURN m.name as medication, r.effectiveness as effectiveness
LIMIT 10
"""
    
    @staticmethod
    def get_comprehensive_disease_analysis(disease: str, zipcode: str = None) -> str:
        """Get comprehensive disease analysis"""
        disease_lower = disease.lower()
        return f"""
MATCH (d:Disease)
WHERE TOLOWER(d.name) CONTAINS "{disease_lower}" OR d.disease_id CONTAINS "{disease_lower}"
RETURN {{
    disease: d.name,
    category: d.category
}} as analysis
LIMIT 1
"""
    
    @staticmethod
    def validate_cypher_query(query: str) -> bool:
        """Basic validation of Cypher query"""
        query_upper = query.upper()
        has_match = 'MATCH' in query_upper
        has_return = 'RETURN' in query_upper
        return has_match and has_return
