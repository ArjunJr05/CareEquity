"""
Import knowledge graph data from CSV files into Neo4j.
Populates the database with diseases, factors, communities, and relationships.
"""

import csv
import logging
from pathlib import Path
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Neo4jImporter:
    """Import CSV data into Neo4j."""
    
    def __init__(self, uri: str, username: str, password: str):
        """Initialize Neo4j driver."""
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✓ Connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close connection."""
        if self.driver:
            self.driver.close()
    
    def clear_database(self):
        """Clear all data from Neo4j."""
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("✓ Cleared database")
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
    
    def import_disease_nodes(self, csv_path: Path):
        """Import disease nodes."""
        logger.info(f"Importing diseases from {csv_path}...")
        count = 0
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                with self.driver.session() as session:
                    for row in reader:
                        query = """
                        CREATE (d:Disease {
                            disease_id: $disease_id,
                            name: $disease_name,
                            category: $category
                        })
                        """
                        session.run(query, 
                            disease_id=row['disease_id'],
                            disease_name=row['disease_name'],
                            category=row['category']
                        )
                        count += 1
            logger.info(f"✓ Imported {count} diseases")
        except Exception as e:
            logger.error(f"Failed to import diseases: {e}")
    
    def import_sdoh_factor_nodes(self, csv_path: Path):
        """Import SDOH factor nodes."""
        logger.info(f"Importing SDOH factors from {csv_path}...")
        count = 0
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                with self.driver.session() as session:
                    for row in reader:
                        query = """
                        CREATE (f:Factor {
                            factor_id: $factor_id,
                            name: $factor_name,
                            category: $category
                        })
                        """
                        session.run(query,
                            factor_id=row['factor_id'],
                            factor_name=row['factor_name'],
                            category=row['category']
                        )
                        count += 1
            logger.info(f"✓ Imported {count} SDOH factors")
        except Exception as e:
            logger.error(f"Failed to import SDOH factors: {e}")
    
    def import_intervention_nodes(self, csv_path: Path):
        """Import intervention nodes."""
        logger.info(f"Importing interventions from {csv_path}...")
        count = 0
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                with self.driver.session() as session:
                    for row in reader:
                        query = """
                        CREATE (i:Intervention {
                            intervention_id: $intervention_id,
                            name: $intervention_name,
                            category: $category
                        })
                        """
                        session.run(query,
                            intervention_id=row['intervention_id'],
                            intervention_name=row['intervention_name'],
                            category=row['category']
                        )
                        count += 1
            logger.info(f"✓ Imported {count} interventions")
        except Exception as e:
            logger.error(f"Failed to import interventions: {e}")
    
    def import_community_nodes(self, csv_path: Path):
        """Import community nodes efficiently using LOAD CSV."""
        logger.info(f"Importing communities from {csv_path}...")
        try:
            with self.driver.session() as session:
                query = f"""
                LOAD CSV WITH HEADERS FROM 'file:///{csv_path.name}' AS row
                CREATE (c:Community {{
                    node_id: row.node_id,
                    zipcode: row.ZIPCODE,
                    state: row.STATE,
                    region: row.REGION,
                    year: toInteger(row.YEAR),
                    overall_sdoh_score: toFloat(row.overall_sdoh_score),
                    risk_level: row.risk_level
                }})
                """
                result = session.run(query)
                summary = result.consume()
                logger.info(f"✓ Imported {summary.counters.nodes_created} communities")
        except Exception as e:
            logger.warning(f"LOAD CSV not available, using slower import: {e}")
            # Fallback to batch import
            self._import_community_nodes_batch(csv_path)
    
    def _import_community_nodes_batch(self, csv_path: Path, batch_size: int = 100):
        """Import community nodes in batches."""
        count = 0
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                batch = []
                
                with self.driver.session() as session:
                    for row in reader:
                        batch.append(row)
                        
                        if len(batch) >= batch_size:
                            query = """
                            UNWIND $rows AS row
                            CREATE (c:Community {
                                node_id: row.node_id,
                                zipcode: row.ZIPCODE,
                                state: row.STATE,
                                region: row.REGION,
                                year: toInteger(row.YEAR),
                                overall_sdoh_score: toFloat(row.overall_sdoh_score),
                                risk_level: row.risk_level
                            })
                            """
                            session.run(query, rows=batch)
                            count += len(batch)
                            logger.info(f"  Imported {count} communities so far...")
                            batch = []
                    
                    # Import remaining batch
                    if batch:
                        query = """
                        UNWIND $rows AS row
                        CREATE (c:Community {
                            node_id: row.node_id,
                            zipcode: row.ZIPCODE,
                            state: row.STATE,
                            region: row.REGION,
                            year: toInteger(row.YEAR),
                            overall_sdoh_score: toFloat(row.overall_sdoh_score),
                            risk_level: row.risk_level
                        })
                        """
                        session.run(query, rows=batch)
                        count += len(batch)
            
            logger.info(f"✓ Imported {count} communities")
        except Exception as e:
            logger.error(f"Failed to import communities: {e}")
    
    def import_relationships(self, csv_path: Path, rel_type: str, source_label: str, target_label: str):
        """Import relationships from CSV."""
        logger.info(f"Importing {rel_type} relationships from {csv_path}...")
        count = 0
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                with self.driver.session() as session:
                    for row in reader:
                        source_id_field = 'source' if 'source' in row else 'source_id'
                        target_id_field = 'target' if 'target' in row else 'target_id'
                        
                        source_id = row.get(source_id_field)
                        target_id = row.get(target_id_field)
                        
                        # Build properties string for relationships
                        props = {}
                        for key, value in row.items():
                            if key not in [source_id_field, target_id_field]:
                                props[key] = value
                        
                        prop_str = ", ".join([f"{k}: ${k}" for k in props.keys()])
                        if prop_str:
                            prop_str = ", " + prop_str
                        
                        query = f"""
                        MATCH (source:{source_label} {{node_id: $source_id}})
                        MATCH (target:{target_label} {{node_id: $target_id}})
                        CREATE (source)-[r:{rel_type} {{{prop_str}}}]->(target)
                        """
                        
                        # Handle case where we're using disease_id, factor_id, etc
                        if 'disease_id' in row:
                            query = f"""
                            MATCH (source:{source_label} {{factor_id: $source_id}})
                            MATCH (target:{target_label} {{disease_id: $target_id}})
                            CREATE (source)-[r:{rel_type} {{{prop_str}}}]->(target)
                            """
                        
                        try:
                            params = {
                                'source_id': source_id,
                                'target_id': target_id,
                                **props
                            }
                            session.run(query, params)
                            count += 1
                        except Neo4jError as e:
                            logger.debug(f"Relationship creation issue: {e}")
                            continue
            
            logger.info(f"✓ Imported {count} {rel_type} relationships")
        except Exception as e:
            logger.error(f"Failed to import {rel_type} relationships: {e}")
    
    def create_indexes(self):
        """Create database indexes."""
        try:
            with self.driver.session() as session:
                session.run("CREATE INDEX IF NOT EXISTS FOR (n:Disease) ON (n.disease_id)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (n:Factor) ON (n.factor_id)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (n:Intervention) ON (n.intervention_id)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (n:Community) ON (n.zipcode)")
            logger.info("✓ Created indexes")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")


def main():
    """Main import function."""
    # Configuration
    NEO4J_URI = "neo4j+s://5ee87958.databases.neo4j.io"
    NEO4J_USERNAME = "5ee87958"
    NEO4J_PASSWORD = "O4QNSbiyt-f1Y696mhnMyQpJe5wOea0WGDFh871gu2c"
    
    DATA_DIR = Path(__file__).parent.parent / "data" / "neo4j_data"
    
    # Initialize importer
    importer = Neo4jImporter(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    
    try:
        # Clear existing data
        importer.clear_database()
        
        # Import nodes
        importer.import_disease_nodes(DATA_DIR / "disease_nodes.csv")
        importer.import_sdoh_factor_nodes(DATA_DIR / "sdoh_factor_nodes.csv")
        importer.import_intervention_nodes(DATA_DIR / "intervention_nodes.csv")
        importer.import_community_nodes(DATA_DIR / "community_nodes.csv")
        
        # Import relationships
        importer.import_relationships(
            DATA_DIR / "factor_disease_relationships.csv",
            "INCREASES_RISK_OF",
            "Factor",
            "Disease"
        )
        
        importer.import_relationships(
            DATA_DIR / "disease_intervention_relationships.csv",
            "MANAGED_BY",
            "Disease",
            "Intervention"
        )
        
        importer.import_relationships(
            DATA_DIR / "community_factor_relationships.csv",
            "HAS_FACTOR",
            "Community",
            "Factor"
        )
        
        # Create indexes
        importer.create_indexes()
        
        logger.info("✅ Knowledge graph import completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
    finally:
        importer.close()


if __name__ == "__main__":
    main()
