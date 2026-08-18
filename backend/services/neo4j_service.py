"""
Neo4j service for managing knowledge graph operations.
Handles connection, data import, and Cypher queries.
"""

from typing import List, Dict, Optional, Any
from neo4j import GraphDatabase, Session
from neo4j.exceptions import Neo4jError
import logging
from pathlib import Path
import csv

from services.cypher_builder import CypherQueryBuilder

logger = logging.getLogger(__name__)


class Neo4jService:
    """Service for interacting with Neo4j knowledge graph."""
    
    def __init__(self, uri: str, username: str, password: str):
        """Initialize Neo4j connection."""
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self.cypher_builder = CypherQueryBuilder()
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✓ Neo4j connected successfully")
        except Neo4jError as e:
            logger.warning(f"Neo4j connection warning: {str(e)}")
            self.driver = None  # Allow to continue in demo mode
    
    def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def is_connected(self) -> bool:
        """Check if Neo4j is connected"""
        return self.driver is not None
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute Cypher query and return results."""
        if not self.driver:
            logger.warning("Neo4j not connected")
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Neo4jError as e:
            logger.error(f"Query failed: {str(e)}")
            return []
    
    # ==================== KB Graph Reasoning Methods ====================
    
    def get_factors_for_disease(self, disease: str) -> List[str]:
        """
        Get risk factors for a disease using Cypher query.
        
        Args:
            disease: Disease name
        
        Returns:
            List of risk factors
        """
        try:
            query = self.cypher_builder.get_disease_risk_factors(disease)
            results = self.execute_query(query)
            return [r.get("factor", "") for r in results if r.get("factor")]
        except Exception as e:
            logger.error(f"Error getting factors for {disease}: {str(e)}")
            return []
    
    def get_disease_pathways(self, disease: str, zipcode: str = None) -> Dict[str, Any]:
        """
        Get disease pathways from SDOH factors to disease.
        
        Args:
            disease: Disease name
            zipcode: Optional zipcode for location-specific analysis
        
        Returns:
            Dictionary with pathways and connections
        """
        try:
            pathways = {}
            
            # Get disease pathways
            pathway_query = self.cypher_builder.get_disease_pathways(disease)
            pathway_results = self.execute_query(pathway_query)
            
            # Get community factors if zipcode provided
            if zipcode:
                community_query = self.cypher_builder.get_community_factors_for_disease(disease, zipcode)
                community_results = self.execute_query(community_query)
                pathways["community_factors"] = community_results
            
            pathways["pathways"] = pathway_results
            return pathways
            
        except Exception as e:
            logger.error(f"Error getting pathways for {disease}: {str(e)}")
            return {}
    
    def get_disease_interventions(self, disease: str) -> List[Dict[str, Any]]:
        """
        Get recommended interventions for a disease.
        
        Args:
            disease: Disease name
        
        Returns:
            List of intervention recommendations
        """
        try:
            query = self.cypher_builder.get_disease_interventions(disease)
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting interventions for {disease}: {str(e)}")
            return []
    
    def get_factor_disease_chain(self, risk_factor: str) -> List[str]:
        """
        Get diseases related to a risk factor.
        
        Args:
            risk_factor: Risk factor name
        
        Returns:
            List of related diseases
        """
        try:
            query = self.cypher_builder.get_factor_disease_chain(risk_factor)
            results = self.execute_query(query)
            return [r.get("disease", "") for r in results if r.get("disease")]
        except Exception as e:
            logger.error(f"Error getting disease chain for {risk_factor}: {str(e)}")
            return []
    
    def get_sdoh_interventions(self, sdoh_factor: str) -> List[Dict[str, Any]]:
        """
        Get interventions that can improve a specific SDOH factor.
        
        Args:
            sdoh_factor: SDOH factor name
        
        Returns:
            List of recommended interventions
        """
        try:
            query = self.cypher_builder.get_sdoh_intervention_chain(sdoh_factor)
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting SDOH interventions: {str(e)}")
            return []
    
    def get_comprehensive_disease_analysis(self, disease: str, zipcode: str = None) -> Dict[str, Any]:
        """
        Get comprehensive disease analysis: factors, pathways, interventions, outcomes.
        
        Args:
            disease: Disease name
            zipcode: Optional location for context
        
        Returns:
            Comprehensive analysis dictionary
        """
        try:
            query = self.cypher_builder.get_comprehensive_disease_analysis(disease, zipcode)
            results = self.execute_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Error getting comprehensive analysis: {str(e)}")
            return {}
    
    def import_csv_nodes(self, csv_path: str, label: str, id_field: str) -> int:
        """Import nodes from CSV file."""
        try:
            nodes_created = 0
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                with self.driver.session() as session:
                    for row in reader:
                        node_id = row.pop(id_field)
                        props = ", ".join([f"{k}: ${k}" for k in row.keys()])
                        query = f"CREATE (n:{label} {{id: $id, {props}}}) RETURN id(n)"
                        params = {"id": node_id, **row}
                        session.run(query, params)
                        nodes_created += 1
            
            logger.info(f"Imported {nodes_created} {label} nodes from {csv_path}")
            return nodes_created
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            raise
    
    def import_csv_relationships(self, csv_path: str, rel_type: str, source_label: str, 
                                  target_label: str, source_field: str = "source", 
                                  target_field: str = "target") -> int:
        """Import relationships from CSV file."""
        try:
            rels_created = 0
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                with self.driver.session() as session:
                    for row in reader:
                        source_id = row[source_field]
                        target_id = row[target_field]
                        rel_props = {k: v for k, v in row.items() if k not in [source_field, target_field]}
                        prop_str = ", ".join([f"{k}: ${k}" for k in rel_props.keys()])
                        if prop_str:
                            prop_str = ", " + prop_str
                        
                        query = f"""MATCH (source {{id: $source_id}})
                                   MATCH (target {{id: $target_id}})
                                   CREATE (source)-[r:{rel_type} {{{prop_str}}}]->(target)
                                   RETURN id(r)"""
                        params = {"source_id": source_id, "target_id": target_id, **rel_props}
                        session.run(query, params)
                        rels_created += 1
            
            logger.info(f"Imported {rels_created} {rel_type} relationships")
            return rels_created
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            raise
    
    def get_factors_for_disease(self, disease_id: str) -> List[Dict[str, Any]]:
        """Get all risk factors that increase risk of a disease."""
        # Use disease_id and factor_id properties that exist in the schema
        try:
            query = """MATCH (f:Factor)-[r:INCREASES_RISK_OF]->(d:Disease)
                       WHERE d.disease_id = $disease_id OR d.name = $disease_id 
                       RETURN f.factor_id as factor_id, f.name as factor_name,
                              f.category as factor_category, r.evidence_strength as evidence_strength
                       ORDER BY COALESCE(r.evidence_strength, 'Moderate') DESC
                       LIMIT 10"""
            results = self.execute_query(query, {"disease_id": disease_id})
            return results if results else []
        except Exception as e:
            logger.warning(f"Could not query factors for disease {disease_id}: {str(e)}")
            return []
    
    def get_disease_interventions(self, disease_id: str) -> List[Dict[str, Any]]:
        """Get interventions that manage a disease."""
        try:
            query = """MATCH (d:Disease)-[r:MANAGED_BY]->(i:Intervention)
                       WHERE d.disease_id = $disease_id OR d.name = $disease_id
                       RETURN i.intervention_id as intervention_id, i.name as intervention_name,
                              i.category as intervention_category, r.effectiveness as effectiveness
                       ORDER BY COALESCE(r.effectiveness, 0.5) DESC
                       LIMIT 10"""
            results = self.execute_query(query, {"disease_id": disease_id})
            return results if results else []
        except Exception as e:
            logger.warning(f"Could not query interventions for disease {disease_id}: {str(e)}")
            return []
    
    def get_community_factors(self, community_id: str) -> List[Dict[str, Any]]:
        """Get SDOH factors present in a community."""
        query = """MATCH (community {id: $community_id})-[r:HAS_FACTOR]->(factor)
                   RETURN factor.id as factor_id, factor.factor_name as factor_name,
                          factor.category as factor_category, r.strength as strength
                   ORDER BY r.strength DESC"""
        return self.execute_query(query, {"community_id": community_id})
    
    def get_risk_reasoning_path(self, community_id: str, disease_id: str) -> List[Dict[str, Any]]:
        """Get reasoning path from community factors to disease risk."""
        query = """MATCH path = (community {id: $community_id})-[:HAS_FACTOR]->
                         (factor)-[:INCREASES_RISK_OF]->
                         (disease {id: $disease_id})
                   RETURN [node in nodes(path) | {id: node.id, name: COALESCE(node.factor_name, node.disease_name),
                           type: labels(node)[0]}] as nodes,
                          [rel in relationships(path) | type(rel)] as relationships
                   LIMIT 10"""
        return self.execute_query(query, {"community_id": community_id, "disease_id": disease_id})
    
    def get_factor_disease_chain(self, factor_id: str) -> List[Dict[str, Any]]:
        """Get all diseases that a factor increases risk for."""
        query = """MATCH (factor {id: $factor_id})-[r:INCREASES_RISK_OF]->(disease)
                   RETURN disease.id as disease_id, disease.disease_name as disease_name,
                          disease.category as disease_category, r.evidence_strength as evidence_strength
                   ORDER BY r.evidence_strength DESC"""
        return self.execute_query(query, {"factor_id": factor_id})
    
    def get_interventions_for_factors(self, factor_ids: List[str]) -> List[Dict[str, Any]]:
        """Get interventions that address specific risk factors."""
        query = """MATCH (factor)-[:TARGETS]->(intervention)
                   WHERE factor.id IN $factor_ids
                   RETURN DISTINCT intervention.id as intervention_id, intervention.intervention_name as intervention_name,
                          intervention.category as intervention_category, COUNT(DISTINCT factor) as factor_coverage
                   ORDER BY factor_coverage DESC"""
        return self.execute_query(query, {"factor_ids": factor_ids})
    
    def create_indexes(self) -> None:
        """Create database indexes for performance."""
        queries = [
            "CREATE INDEX IF NOT EXISTS FOR (n) ON (n.id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Disease) ON (n.disease_id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Factor) ON (n.factor_id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Community) ON (n.node_id)",
        ]
        
        with self.driver.session() as session:
            for query in queries:
                try:
                    session.run(query)
                    logger.info(f"Created index")
                except Neo4jError:
                    pass  # Index already exists

