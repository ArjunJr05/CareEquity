import os
import json
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

# ============================================================
# ML PIPELINE CLASS FOR MEDICAL + SDOH INFERENCE
# ============================================================

class MedicalSDOHInferencePipeline:
    def __init__(self, med_dataset_path=None, sdoh_dataset_path=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        default_med = os.path.join(base_dir, "clinical_data", "synthetic_medical_75000.csv")
        default_sdoh = os.path.join(base_dir, "clinical_data", "synthetic_county_context_50_FINAL.csv")
        
        self.med_dataset_path = med_dataset_path or default_med
        self.sdoh_dataset_path = sdoh_dataset_path or default_sdoh
        
        self.diseases = ['diabetes', 'hypertension', 'heart_disease', 'asthma']
        
        self.medical_num_cols = ['age', 'height_cm', 'weight_kg', 'bmi', 'waist_cm', 'systolic_bp', 'diastolic_bp', 
                                'heart_rate', 'hba1c', 'fasting_glucose', 'total_cholesterol', 'ldl', 'hdl', 
                                'triglycerides', 'creatinine', 'egfr', 'bun', 'urine_albumin', 'urine_creatinine', 'acr',
                                'hemoglobin', 'hematocrit', 'wbc', 'platelets', 'mcv', 'alt', 'ast', 'albumin', 
                                'bilirubin', 'sedentary_minutes']

        self.medical_cat_cols = ['sex', 'race_ethnicity', 'smoking_status', 'alcohol_use']

        self.sdoh_cols = ['svi_overall', 'poverty_rate', 'median_household_income', 'unemployment_rate', 
                         'food_insecurity', 'transportation_barrier', 'housing_insecurity', 
                         'obesity_prevalence', 'physical_inactivity', 'smoking_prevalence', 'lack_health_insurance']
        
        self.all_feature_cols = self.medical_num_cols + self.sdoh_cols + self.medical_cat_cols
        
        self.models = {}
        self.preprocessors = {}
        self.medians = {}
        self.sdoh_lookup = {}
        self.is_fitted = False
        
    def fit(self):
        """Train models on Medical + SDOH dataset and cache defaults for crash-proof inference."""
        print("Initializing & fitting ML pipeline models...")
        med_df = pd.read_csv(self.med_dataset_path)
        sdoh_df = pd.read_csv(self.sdoh_dataset_path)

        med_df['county_fips'] = med_df['county_fips'].astype(str).str.zfill(5)
        sdoh_df['county_fips'] = sdoh_df['county_fips'].astype(str).str.zfill(5)

        for _, row in sdoh_df.iterrows():
            fips = row['county_fips']
            c_name = str(row['county_name']).split(',')[0].replace(' County', '').strip().lower()
            state = str(row['state_abbr']).strip().upper()
            
            sdoh_dict = {col: float(row[col]) for col in self.sdoh_cols if col in row}
            sdoh_dict['county_name'] = str(row['county_name'])
            sdoh_dict['state_abbr'] = state
            sdoh_dict['county_fips'] = fips
            
            self.sdoh_lookup[fips] = sdoh_dict
            self.sdoh_lookup[f"{state}_{c_name}"] = sdoh_dict

        for col in self.medical_num_cols:
            self.medians[col] = float(med_df[col].median()) if col in med_df else 0.0

        df = med_df.merge(sdoh_df.drop(columns=['state_abbr', 'county_name'], errors='ignore'), on='county_fips', how='inner')
        num_cols = self.medical_num_cols + self.sdoh_cols
        
        for disease in self.diseases:
            num_trans = Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])
            cat_trans = Pipeline([('imputer', SimpleImputer(strategy='most_frequent')), ('encoder', OneHotEncoder(handle_unknown='ignore', drop='first'))])
            
            preprocessor = ColumnTransformer([('num', num_trans, num_cols), ('cat', cat_trans, self.medical_cat_cols)])
            
            X_train = preprocessor.fit_transform(df[num_cols + self.medical_cat_cols])
            y_train = df[disease].astype(int)
            
            clf = LogisticRegression(max_iter=500, random_state=42)
            clf.fit(X_train, y_train)
            
            self.preprocessors[disease] = preprocessor
            self.models[disease] = clf
            
        self.is_fitted = True
        print("ML Pipeline successfully fitted across all 4 target disease models!")

    def _resolve_location_sdoh(self, loc_dict):
        if 'county_fips' in loc_dict and str(loc_dict['county_fips']).zfill(5) in self.sdoh_lookup:
            return self.sdoh_lookup[str(loc_dict['county_fips']).zfill(5)]
        
        state = str(loc_dict.get('state', '')).strip().upper()
        c_name = str(loc_dict.get('county', '')).split(',')[0].replace(' County', '').strip().lower()
        key = f"{state}_{c_name}"
        
        if key in self.sdoh_lookup:
            return self.sdoh_lookup[key]
        
        first_key = list(self.sdoh_lookup.keys())[0]
        return self.sdoh_lookup[first_key]

    def predict(self, ocr_payload):
        if not self.is_fitted:
            self.fit()
            
        patient_id = ocr_payload.get('patient_id', 'OCR_PATIENT_001')
        med_input = ocr_payload.get('medical_data', ocr_payload)
        
        if 'locations' in ocr_payload and isinstance(ocr_payload['locations'], list):
            locations = ocr_payload['locations']
        elif 'location' in ocr_payload and isinstance(ocr_payload['location'], dict):
            locations = [ocr_payload['location']]
        else:
            state = ocr_payload.get('state', 'AL')
            county = ocr_payload.get('county', 'Limestone')
            fips = ocr_payload.get('county_fips', '01083')
            locations = [{'state': state, 'county': county, 'county_fips': fips}]
            
        clean_med = {}
        for col in self.medical_num_cols:
            val = med_input.get(col, None)
            if val is None or pd.isna(val):
                clean_med[col] = self.medians[col]
            else:
                try:
                    clean_med[col] = float(val)
                except (ValueError, TypeError):
                    clean_med[col] = self.medians[col]
                    
        for col in self.medical_cat_cols:
            val = med_input.get(col, None)
            if val is None or pd.isna(val):
                clean_med[col] = 'Unknown' if col != 'sex' else 'Female'
            else:
                clean_med[col] = str(val)

        county_results = []
        
        for loc in locations:
            sdoh_data = self._resolve_location_sdoh(loc)
            combined_row = {**clean_med, **sdoh_data}
            input_df = pd.DataFrame([combined_row])
            
            disease_predictions = {}
            
            for disease in self.diseases:
                preprocessor = self.preprocessors[disease]
                clf = self.models[disease]
                
                num_cols = self.medical_num_cols + self.sdoh_cols
                X_trans = preprocessor.transform(input_df[num_cols + self.medical_cat_cols])
                prob = float(clf.predict_proba(X_trans)[0][1])
                
                risk_tier = "High Risk" if prob >= 0.65 else ("Moderate Risk" if prob >= 0.35 else "Low Risk")
                
                coefs = clf.coef_[0]
                sdoh_impacts = []
                
                for idx, sdoh_feat in enumerate(self.sdoh_cols):
                    feat_idx = len(self.medical_num_cols) + idx
                    weight = float(coefs[feat_idx])
                    raw_val = float(sdoh_data.get(sdoh_feat, 0.0))
                    
                    sdoh_impacts.append({
                        "sdoh_factor": sdoh_feat,
                        "shap_impact": round(weight, 4),
                        "county_value": round(raw_val, 2),
                        "unit": "%" if "rate" in sdoh_feat or "prevalence" in sdoh_feat or "insecurity" in sdoh_feat or "inactivity" in sdoh_feat or "insurance" in sdoh_feat else "value"
                    })
                    
                top_3_sdoh = sorted(sdoh_impacts, key=lambda x: abs(x['shap_impact']), reverse=True)[:3]
                
                disease_predictions[disease] = {
                    "probability": round(prob, 4),
                    "risk_tier": risk_tier,
                    "top_3_sdoh_factors": top_3_sdoh
                }
                
            county_results.append({
                "location": {
                    "state": sdoh_data.get('state_abbr', loc.get('state', 'AL')),
                    "county_name": sdoh_data.get('county_name', loc.get('county', 'Unknown')),
                    "county_fips": sdoh_data.get('county_fips', '00000')
                },
                "diseases": disease_predictions
            })
            
        return {
            "status": "success",
            "patient_id": patient_id,
            "is_multi_county": len(locations) > 1,
            "evaluated_counties_count": len(locations),
            "county_predictions": county_results
        }

pipeline = MedicalSDOHInferencePipeline()

def predict(ocr_payload):
    return pipeline.predict(ocr_payload)

if __name__ == '__main__':
    pipeline.fit()
    sample_payload = {
        "patient_id": "TEST_PATIENT_TRAVEL_01",
        "medical_data": {
            "age": 58,
            "bmi": 32.1,
            "systolic_bp": 142,
            "smoking_status": True
        },
        "locations": [
            {"state": "AL", "county": "Limestone"},
            {"state": "AL", "county": "Wilcox"}
        ]
    }
    output = pipeline.predict(sample_payload)
    print(json.dumps(output, indent=2))
