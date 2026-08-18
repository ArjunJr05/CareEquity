"""
Data service for managing SDOH scores and member health data.
Loads and retrieves data from CSV files.
"""

from typing import Dict, Optional, List
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_SDOH_SCORES = {
    "economic_stability_score": 0.5,
    "healthcare_access_quality_score": 0.5,
    "education_access_quality_score": 0.5,
    "neighborhood_built_environment_score": 0.5,
    "food_security_score": 0.5,
    "social_community_context_score": 0.5,
}


class DataService:
    """Service for managing health and SDOH data."""
    
    def __init__(self, sdoh_csv_path: str):
        """Initialize data service."""
        self.sdoh_data = None
        self.member_data = None
        self.sdoh_csv_path = sdoh_csv_path
        self._load_data()
    
    def _load_data(self) -> None:
        """Load SDOH data from CSV."""
        try:
            paths_to_try = [
                self.sdoh_csv_path,
                Path("./data/SDOH/modeling_dataset_with_sdoh (1).csv"),
                Path("../data/SDOH/modeling_dataset_with_sdoh (1).csv"),
                Path("../../data/SDOH/modeling_dataset_with_sdoh (1).csv"),
            ]
            
            for path in paths_to_try:
                if Path(path).exists():
                    self.sdoh_data = pd.read_csv(path)
                    self.sdoh_data.columns = [col.lower() for col in self.sdoh_data.columns]
                    logger.info(f"Loaded SDOH data: {len(self.sdoh_data)} records")
                    return
            
            logger.warning("SDOH data file not found")
            self.sdoh_data = pd.DataFrame()
        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            self.sdoh_data = pd.DataFrame()
    
    def get_sdoh_scores(self, zipcode: str, year: int = 2023) -> Dict[str, float]:
        """Get SDOH scores for a specific zipcode."""
        if self.sdoh_data is None or self.sdoh_data.empty:
            logger.warning(f"No SDOH data for zipcode {zipcode}")
            return DEFAULT_SDOH_SCORES
        
        try:
            zipcode = str(zipcode).strip()
            mask = self.sdoh_data['zipcode'].astype(str).str.strip() == zipcode
            
            if mask.any():
                row = self.sdoh_data[mask].iloc[0]
                return {
                    "economic_stability_score": self._safe_float(row, "economic_stability_score", 0.5),
                    "healthcare_access_quality_score": self._safe_float(row, "healthcare_access_quality_score", 0.5),
                    "education_access_quality_score": self._safe_float(row, "education_access_quality_score", 0.5),
                    "neighborhood_built_environment_score": self._safe_float(row, "neighborhood_built_environment_score", 0.5),
                    "food_security_score": self._safe_float(row, "food_security_score", 0.5),
                    "social_community_context_score": self._safe_float(row, "social_community_context_score", 0.5),
                }
            else:
                logger.warning(f"Zipcode {zipcode} not found")
                return DEFAULT_SDOH_SCORES
        except Exception as e:
            logger.error(f"SDOH lookup failed: {str(e)}")
            return DEFAULT_SDOH_SCORES
    
    def get_community_id(self, zipcode: str, year: int = 2023) -> str:
        """Get community node ID for Neo4j graph."""
        return f"Community_{zipcode}_{year}"
    
    def validate_health_metrics(self, health_metrics: Dict) -> bool:
        """Validate health metrics data."""
        required_fields = ["age", "zipcode", "bmi"]
        
        for field in required_fields:
            if field not in health_metrics or health_metrics[field] is None:
                logger.warning(f"Missing field: {field}")
                return False
        
        if not (0 <= health_metrics["age"] <= 150):
            logger.warning(f"Invalid age: {health_metrics['age']}")
            return False
        
        if not (0 <= health_metrics["bmi"] <= 100):
            logger.warning(f"Invalid BMI: {health_metrics['bmi']}")
            return False
        
        return True
    
    @staticmethod
    def _safe_float(row: pd.Series, column: str, default: float = 0.5) -> float:
        """Safely extract float value from pandas Series."""
        try:
            if column in row.index:
                value = row[column]
                if pd.isna(value):
                    return default
                return float(value)
            return default
        except Exception:
            return default
    
    def get_member_data(self, member_id: str) -> Optional[Dict]:
        """Get stored data for a specific member."""
        if self.member_data is None or self.member_data.empty:
            return None
        
        mask = self.member_data['member_id'].astype(str) == member_id
        if mask.any():
            return self.member_data[mask].iloc[0].to_dict()
        
        return None
    
    def store_member_prediction(self, member_id: str, prediction_data: Dict) -> bool:
        """Store prediction results for a member (in-memory)."""
        try:
            if self.member_data is None:
                self.member_data = pd.DataFrame()
            
            row_data = {"member_id": member_id, **prediction_data}
            new_row = pd.DataFrame([row_data])
            self.member_data = pd.concat([self.member_data, new_row], ignore_index=True)
            
            logger.info(f"Stored prediction for member {member_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store prediction: {str(e)}")
            return False
    
    def get_zipcode_statistics(self, zipcode: str) -> Dict:
        """Get aggregate statistics for a zipcode."""
        sdoh_scores = self.get_sdoh_scores(zipcode)
        
        return {
            "zipcode": zipcode,
            "sdoh_scores": sdoh_scores,
            "score_average": sum(sdoh_scores.values()) / len(sdoh_scores),
        }

