"""
Neo4j data importer utility.
Imports CSV datasets into Neo4j knowledge graph.
"""

import logging
from pathlib import Path
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.neo4j_service import Neo4jService
from config import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Neo4jDataImporter:
    """Import datasets into Neo4j."""
    
    def __init__(self, neo4j_service: Neo4jService, data_path: str):
        """
        Initialize importer.
        
        Args:
            neo4j_service: Neo4j service instance
            data_path: Path to neo4j_data directory
        """
        self.neo4j_service = neo4j_service
        self.data_path = Path(data_path)
    
    def import_all_data(self) -> None:
        """Import all datasets in order."""
        try:
            logger.info("Starting Neo4j data import...")
            
            # Create indexes first
            logger.info("Creating database indexes...")
            self.neo4j_service.create_indexes()
            
            # Import nodes first
            logger.info("Importing nodes...")
            self._import_nodes()
            
            # Then import relationships
            logger.info("Importing relationships...")
            self._import_relationships()
            
            logger.info("Data import completed successfully!")
        
        except Exception as e:
            logger.error(f"Data import failed: {str(e)}")
            raise
    
    def _import_nodes(self) -> None:
        """Import all node types."""
        
        # Import SDOH Factor nodes
        sdoh_file = self.data_path / "sdoh_factor_nodes.csv"
        if sdoh_file.exists():
            self.neo4j_service.import_csv_nodes(
                str(sdoh_file),
                "Factor",
                "factor_id"
            )
        
        # Import Disease nodes
        disease_file = self.data_path / "disease_nodes.csv"
        if disease_file.exists():
            self.neo4j_service.import_csv_nodes(
                str(disease_file),
                "Disease",
                "disease_id"
            )
        
        # Import Intervention nodes
        intervention_file = self.data_path / "intervention_nodes.csv"
        if intervention_file.exists():
            self.neo4j_service.import_csv_nodes(
                str(intervention_file),
                "Intervention",
                "intervention_id"
            )
        
        # Import Community nodes
        community_file = self.data_path / "community_nodes.csv"
        if community_file.exists():
            self.neo4j_service.import_csv_nodes(
                str(community_file),
                "Community",
                "node_id"
            )
    
    def _import_relationships(self) -> None:
        """Import all relationship types."""
        
        # Import Factor-Disease relationships
        factor_disease_file = self.data_path / "factor_disease_relationships.csv"
        if factor_disease_file.exists():
            self.neo4j_service.import_csv_relationships(
                str(factor_disease_file),
                "INCREASES_RISK_OF",
                "Factor",
                "Disease",
                source_field="source",
                target_field="target"
            )
        
        # Import Disease-Intervention relationships
        disease_intervention_file = self.data_path / "disease_intervention_relationships.csv"
        if disease_intervention_file.exists():
            self.neo4j_service.import_csv_relationships(
                str(disease_intervention_file),
                "MANAGED_BY",
                "Disease",
                "Intervention",
                source_field="source",
                target_field="target"
            )
        
        # Import Community-Factor relationships
        community_factor_file = self.data_path / "community_factor_relationships.csv"
        if community_factor_file.exists():
            self.neo4j_service.import_csv_relationships(
                str(community_factor_file),
                "HAS_FACTOR",
                "Community",
                "Factor",
                source_field="source",
                target_field="target"
            )


def main():
    """Main entry point."""
    try:
        # Get settings
        settings = get_settings()
        
        # Initialize Neo4j service
        neo4j_service = Neo4jService(
            settings.neo4j_uri,
            settings.neo4j_username,
            settings.neo4j_password
        )
        
        # Create importer
        importer = Neo4jDataImporter(
            neo4j_service,
            settings.neo4j_data_path
        )
        
        # Import data
        importer.import_all_data()
        
        # Close connection
        neo4j_service.close()
        
        logger.info("Script completed successfully!")
    
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
