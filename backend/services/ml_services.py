"""
Machine Learning service for disease risk prediction.
Handles model loading, prediction, and risk scoring.
Supports disease-specific feature sets:
- Diabetes: 15 numerical + 6 categorical features
- Hypertension: 16 numerical + 6 categorical features
- Heart Disease: 16 numerical + 6 categorical features
- Asthma: 16 numerical + 6 categorical features
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger(__name__)

DISEASES = ["diabetes", "hypertension", "heart_disease", "asthma"]

# Disease-specific feature configurations
DISEASE_FEATURES = {
    "diabetes": {
        "numerical": [
            "age", "height_cm", "weight_kg", "bmi", "waist_cm", 
            "hba1c_percent", "glucose_mg_dl", "total_cholesterol_mg_dl",
            "income_poverty_ratio",
            "economic_stability_score", "healthcare_access_quality_score",
            "education_access_quality_score", "neighborhood_built_environment_score",
            "food_security_score", "social_community_context_score"
        ],
        "categorical": ["gender", "race_ethnicity", "smoking_history", "hypertension", "heart_disease", "asthma"]
    },
    "hypertension": {
        "numerical": [
            "age", "height_cm", "weight_kg", "bmi", "waist_cm",
            "hba1c_percent", "glucose_mg_dl", "total_cholesterol_mg_dl",
            "diabetes_diagnosed", "income_poverty_ratio",
            "economic_stability_score", "healthcare_access_quality_score",
            "education_access_quality_score", "neighborhood_built_environment_score",
            "food_security_score", "social_community_context_score"
        ],
        "categorical": ["gender", "race_ethnicity", "smoking_history", "diabetes", "heart_disease", "asthma"]
    },
    "heart_disease": {
        "numerical": [
            "age", "height_cm", "weight_kg", "bmi", "waist_cm",
            "hba1c_percent", "glucose_mg_dl", "total_cholesterol_mg_dl",
            "diabetes_diagnosed", "income_poverty_ratio",
            "economic_stability_score", "healthcare_access_quality_score",
            "education_access_quality_score", "neighborhood_built_environment_score",
            "food_security_score", "social_community_context_score"
        ],
        "categorical": ["gender", "race_ethnicity", "smoking_history", "diabetes", "hypertension", "asthma"]
    },
    "asthma": {
        "numerical": [
            "age", "height_cm", "weight_kg", "bmi", "waist_cm",
            "hba1c_percent", "glucose_mg_dl", "total_cholesterol_mg_dl",
            "diabetes_diagnosed", "income_poverty_ratio",
            "economic_stability_score", "healthcare_access_quality_score",
            "education_access_quality_score", "neighborhood_built_environment_score",
            "food_security_score", "social_community_context_score"
        ],
        "categorical": ["gender", "race_ethnicity", "smoking_history", "diabetes", "hypertension", "heart_disease"]
    }
}

# Categorical feature encodings
CATEGORICAL_ENCODINGS = {
    "gender": {"Male": 0, "Female": 1, "Other": 2},
    "race_ethnicity": {"White": 0, "Black": 1, "Hispanic": 2, "Asian": 3, "Other": 4},
    "smoking_history": {"Non-Smoker": 0, "Former Smoker": 1, "Smoker": 2},
    "diabetes": {"No": 0, "Yes": 1, "Unknown": 0.5},
    "hypertension": {"No": 0, "Yes": 1, "Unknown": 0.5},
    "heart_disease": {"No": 0, "Yes": 1, "Unknown": 0.5},
    "asthma": {"No": 0, "Yes": 1, "Unknown": 0.5}
}

FEATURE_IMPORTANCE = {
    "age": 0.25, "bmi": 0.20, "glucose_mg_dl": 0.15, "total_cholesterol_mg_dl": 0.12,
    "hba1c_percent": 0.10, "smoking_history": 0.08, "economic_stability_score": 0.05,
    "healthcare_access_quality_score": 0.03, "food_security_score": 0.02,
}

FACTOR_CATEGORIES = {
    "age": "Demographic", "bmi": "Anthropometric", "glucose_mg_dl": "Metabolic",
    "total_cholesterol_mg_dl": "Metabolic", "hba1c_percent": "Metabolic", "waist_cm": "Anthropometric",
    "height_cm": "Anthropometric", "weight_kg": "Anthropometric",
    "income_poverty_ratio": "Socioeconomic", "smoking_history": "Lifestyle",
    "gender": "Demographic", "race_ethnicity": "Demographic",
    "diabetes": "Medical History", "hypertension": "Medical History", 
    "heart_disease": "Medical History", "asthma": "Medical History",
    "economic_stability_score": "Social Determinant", "healthcare_access_quality_score": "Social Determinant",
    "education_access_quality_score": "Social Determinant", "neighborhood_built_environment_score": "Social Determinant",
    "food_security_score": "Social Determinant", "social_community_context_score": "Social Determinant",
}

EVIDENCE_MAP = {
    "age": "Strong", "bmi": "Strong", "glucose_mg_dl": "Strong", "total_cholesterol_mg_dl": "Moderate",
    "hba1c_percent": "Strong", "smoking_history": "Moderate", "economic_stability_score": "Suggestive",
    "healthcare_access_quality_score": "Moderate", "food_security_score": "Suggestive",
    "diabetes": "Strong", "hypertension": "Strong", "heart_disease": "Strong", "asthma": "Moderate"
}


class RiskPredictionService:
    """Service for predicting disease risk using trained models."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize risk prediction service."""
        self.models = {}
        self.scalers = {}
        self.diseases = DISEASES
        self.disease_features = DISEASE_FEATURES
        
        if model_path:
            self.load_models(model_path)
        else:
            self._initialize_dummy_models()
    
    def _initialize_dummy_models(self) -> None:
        """Initialize demo models with dummy training data."""
        logger.info("Initializing demo models with synthetic training data")
        import numpy as np
        
        # Create synthetic training data with 22 features
        # (15 disease-specific + 6 SDOH + 1 extra for flexibility)
        n_samples = 100
        n_features = 22
        X_train = np.random.randn(n_samples, n_features)
        
        for disease in self.diseases:
            # Create and fit scaler with 22 features
            self.scalers[disease] = StandardScaler()
            self.scalers[disease].fit(X_train)
            
            # Create and fit model
            self.models[disease] = RandomForestClassifier(n_estimators=10, random_state=42)
            # Create synthetic labels (0 or 1)
            y_train = np.random.randint(0, 2, n_samples)
            self.models[disease].fit(X_train, y_train)
            
        logger.info("✓ Demo models initialized and fitted with 22 features")
    
    def load_models(self, model_path: str) -> None:
        """Load pre-trained models from disk."""
        try:
            model_dir = Path(model_path)
            for disease in self.diseases:
                model_file = model_dir / f"{disease}_model.pkl"
                scaler_file = model_dir / f"{disease}_scaler.pkl"
                
                if model_file.exists():
                    self.models[disease] = joblib.load(model_file)
                    self.scalers[disease] = joblib.load(scaler_file)
                    logger.info(f"Loaded {disease} model")
                else:
                    logger.warning(f"Model not found: {model_file}")
        except Exception as e:
            logger.error(f"Failed to load models: {str(e)}")
            self._initialize_dummy_models()
    
    def _encode_categorical_feature(self, feature_name: str, value: str) -> float:
        """Encode categorical feature to numeric value."""
        encoding = CATEGORICAL_ENCODINGS.get(feature_name, {})
        return float(encoding.get(value, 0))
    
    def prepare_features(self, health_metrics: Dict, sdoh_scores: Dict, disease: str) -> Tuple[np.ndarray, List[str]]:
        """Prepare and scale features for model prediction.
        
        Returns:
            Tuple of (scaled_features, feature_order)
        """
        if disease not in self.disease_features:
            logger.error(f"Unknown disease: {disease}")
            return np.array([[]]), []
        
        features = {}
        feature_config = self.disease_features[disease]
        
        # Process numerical features
        numerical_mapping = {
            "age": health_metrics.get("age", 0),
            "height_cm": health_metrics.get("height_cm", 170),
            "weight_kg": health_metrics.get("weight_kg", 70),
            "bmi": health_metrics.get("bmi", 24),
            "waist_cm": health_metrics.get("waist_cm", 85),
            "hba1c_percent": health_metrics.get("hba1c_percent", 5.5),
            "glucose_mg_dl": health_metrics.get("glucose_mg_dl", 100),
            "total_cholesterol_mg_dl": health_metrics.get("total_cholesterol_mg_dl", 200),
            "income_poverty_ratio": health_metrics.get("income_poverty_ratio", 2.0),
            "diabetes_diagnosed": float(health_metrics.get("diabetes_diagnosed", 0)),
            "economic_stability_score": sdoh_scores.get("economic_stability_score", 0.5),
            "healthcare_access_quality_score": sdoh_scores.get("healthcare_access_quality_score", 0.5),
            "education_access_quality_score": sdoh_scores.get("education_access_quality_score", 0.5),
            "neighborhood_built_environment_score": sdoh_scores.get("neighborhood_built_environment_score", 0.5),
            "food_security_score": sdoh_scores.get("food_security_score", 0.5),
            "social_community_context_score": sdoh_scores.get("social_community_context_score", 0.5),
        }
        
        # Add numerical features for this disease
        for feature in feature_config["numerical"]:
            features[feature] = numerical_mapping.get(feature, 0)
        
        # Process categorical features
        categorical_mapping = {
            "gender": health_metrics.get("gender", "Male"),
            "race_ethnicity": health_metrics.get("race_ethnicity", "White"),
            "smoking_history": health_metrics.get("smoking_history", "Non-Smoker"),
            "diabetes": health_metrics.get("diabetes", "No"),
            "hypertension": health_metrics.get("hypertension", "No"),
            "heart_disease": health_metrics.get("heart_disease", "No"),
            "asthma": health_metrics.get("asthma", "No"),
        }
        
        # Add categorical features for this disease
        for feature in feature_config["categorical"]:
            value = categorical_mapping.get(feature, "No")
            features[feature] = self._encode_categorical_feature(feature, value)
        
        # Create feature array in consistent order
        # Numerical features first, then categorical
        feature_order = feature_config["numerical"] + feature_config["categorical"]
        X = np.array([[features.get(f, 0) for f in feature_order]])
        
        # Scale features
        if disease in self.scalers:
            try:
                X = self.scalers[disease].transform(X)
            except Exception as e:
                logger.warning(f"Scaling failed for {disease}: {str(e)}")
        
        return X, feature_order
    
    def predict_risk(self, health_metrics: Dict, sdoh_scores: Dict, disease: str) -> Tuple[float, float]:
        """Predict disease risk for an individual.
        
        Args:
            health_metrics: Patient health measurements
            sdoh_scores: Social Determinants of Health scores
            disease: Disease name (diabetes, hypertension, heart_disease, asthma)
        
        Returns:
            Tuple of (risk_score, confidence)
        """
        try:
            X, _ = self.prepare_features(health_metrics, sdoh_scores, disease)
            
            if disease not in self.models:
                logger.warning(f"Model not found for: {disease}")
                return 0.5, 0.5
            
            probabilities = self.models[disease].predict_proba(X)
            risk_score = float(probabilities[0, 1])
            confidence = float(np.max(probabilities[0]))
            
            return risk_score, confidence
        except Exception as e:
            logger.error(f"Prediction failed for {disease}: {str(e)}")
            return 0.5, 0.3
    
    def get_risk_level(self, risk_score: float) -> str:
        """Categorize risk score into risk level."""
        if risk_score < 0.25:
            return "Low"
        elif risk_score < 0.50:
            return "Medium"
        elif risk_score < 0.75:
            return "High"
        else:
            return "Very High"
    
    def get_top_risk_factors(self, health_metrics: Dict, sdoh_scores: Dict, disease: str, top_n: int = 5) -> List[Dict]:
        """Get top contributing risk factors for a disease prediction.
        
        Uses disease-specific features to identify relevant risk factors.
        """
        top_factors = []
        
        if disease not in self.models or disease not in self.disease_features:
            return top_factors
        
        # Get all features for this disease
        all_features = (
            self.disease_features[disease]["numerical"] + 
            self.disease_features[disease]["categorical"]
        )
        
        # Filter importance scores to only relevant features
        relevant_importance = {
            f: FEATURE_IMPORTANCE.get(f, 0.01) 
            for f in all_features 
            if f in FEATURE_IMPORTANCE
        }
        
        # Sort by importance
        sorted_factors = sorted(
            relevant_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        for factor_name, importance in sorted_factors:
            top_factors.append({
                "factor_name": factor_name.replace("_", " ").title(),
                "factor_category": FACTOR_CATEGORIES.get(factor_name, "Other"),
                "risk_contribution": float(importance),
                "evidence_strength": EVIDENCE_MAP.get(factor_name, "Moderate")
            })
        
        return top_factors
    
    def batch_predict(self, health_data: pd.DataFrame, sdoh_data: pd.DataFrame, disease: str) -> np.ndarray:
        """Batch predict risk for multiple individuals."""
        predictions = []
        
        for idx, row in health_data.iterrows():
            health_metrics = row.to_dict()
            
            # Match SDOH scores by zipcode
            sdoh_row = sdoh_data[sdoh_data['zipcode'] == health_metrics.get('zipcode')]
            sdoh_scores = sdoh_row.iloc[0].to_dict() if not sdoh_row.empty else self._get_default_sdoh_scores()
            
            risk_score, _ = self.predict_risk(health_metrics, sdoh_scores, disease)
            predictions.append(risk_score)
        
        return np.array(predictions)
    
    @staticmethod
    def _get_default_sdoh_scores() -> Dict:
        """Get default SDOH scores for missing data."""
        return {
            "economic_stability_score": 0.5,
            "healthcare_access_quality_score": 0.5,
            "education_access_quality_score": 0.5,
            "neighborhood_built_environment_score": 0.5,
            "food_security_score": 0.5,
            "social_community_context_score": 0.5,
        }
