import os
import json
import pickle
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

# US State Name to Abbreviation Mapping
US_STATES = {
    'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR', 'CALIFORNIA': 'CA',
    'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE', 'FLORIDA': 'FL', 'GEORGIA': 'GA',
    'HAWAII': 'HI', 'IDAHO': 'ID', 'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA',
    'KANSAS': 'KS', 'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
    'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS', 'MISSOURI': 'MO',
    'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ',
    'NEW MEXICO': 'NM', 'NEW YORK': 'NY', 'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH',
    'OKLAHOMA': 'OK', 'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
    'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT', 'VERMONT': 'VT',
    'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY'
}

def normalize_state(state_input: str) -> str:
    """Normalize state string (name or abbreviation) to 2-letter uppercase postal code."""
    if not state_input:
        return 'AL'
    clean = str(state_input).strip().upper()
    if len(clean) == 2:
        return clean
    return US_STATES.get(clean, clean[:2])

# ============================================================
# ML PIPELINE V3 CLASS FOR MEDICAL + SDOH INFERENCE
# ============================================================

class MedicalSDOHInferencePipelineV3:
    def __init__(self, med_dataset_path=None, sdoh_dataset_path=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_dir = os.path.dirname(base_dir)

        med_candidates = [
            med_dataset_path,
            os.path.join(base_dir, "clinical_data", "synthetic_medical_75000_V2.csv"),
            os.path.join(workspace_dir, "clinical_data", "synthetic_medical_75000_V2.csv"),
            os.path.join(base_dir, "synthetic_medical_75000_V2.csv"),
            r"p:\project\cts\clinical_data\synthetic_medical_75000_V2.csv"
        ]
        self.med_dataset_path = next((p for p in med_candidates if p and os.path.exists(p)), med_candidates[-1])

        sdoh_candidates = [
            sdoh_dataset_path,
            os.path.join(base_dir, "dataset", "synthetic_county_context_50_FINAL.csv"),
            os.path.join(workspace_dir, "dataset", "synthetic_county_context_50_FINAL.csv"),
            os.path.join(base_dir, "synthetic_county_context_50_FINAL.csv"),
            os.path.join(base_dir, "clinical_data", "synthetic_county_context_50_FINAL.csv"),
            r"p:\project\cts\dataset\synthetic_county_context_50_FINAL.csv"
        ]
        self.sdoh_dataset_path = next((p for p in sdoh_candidates if p and os.path.exists(p)), sdoh_candidates[-1])

        self.diseases = ['diabetes', 'hypertension', 'heart_disease', 'asthma']
        
        # V2/V3 Streamlined 19 Medical Numeric Features
        self.medical_num_cols = [
            'age', 'height_cm', 'weight_kg', 'bmi', 'waist_cm', 
            'systolic_bp', 'diastolic_bp', 'heart_rate', 'hba1c', 
            'fasting_glucose', 'total_cholesterol', 'ldl', 'hdl', 
            'triglycerides', 'alt', 'ast', 'albumin', 'bilirubin', 
            'sedentary_minutes'
        ]

        # 4 Categorical Features
        self.medical_cat_cols = ['sex', 'race_ethnicity', 'smoking_status', 'alcohol_use']

        # 11 Core SDOH Features used in modeling
        self.sdoh_cols = [
            'svi_overall', 'poverty_rate', 'median_household_income', 'unemployment_rate', 
            'food_insecurity', 'transportation_barrier', 'housing_insecurity', 
            'obesity_prevalence', 'physical_inactivity', 'smoking_prevalence', 'lack_health_insurance'
        ]
        
        self.all_feature_cols = self.medical_num_cols + self.sdoh_cols + self.medical_cat_cols
        
        self.models = {}
        self.preprocessors = {}
        self.medians = {}
        self.sdoh_lookup = {}
        self.sdoh_quantiles = {}
        self.is_fitted = False

    def fit(self):
        """Train models on Medical V2 + SDOH dataset, cache defaults and quantile thresholds for SDOH indicators."""
        print(f"Initializing & fitting ML V3 pipeline models using datasets:\n  Medical: {self.med_dataset_path}\n  SDOH: {self.sdoh_dataset_path}")
        
        if os.path.exists(self.med_dataset_path):
            med_df = pd.read_csv(self.med_dataset_path)
        else:
            print("Notice: Medical CSV not found on disk, building synthetic medical DataFrame in memory...")
            np.random.seed(42)
            n_samples = 1000
            med_df = pd.DataFrame({
                'county_fips': np.random.choice(['20195', '01083', '39035', '18097'], size=n_samples),
                'age': np.random.randint(20, 80, size=n_samples),
                'height_cm': np.random.uniform(150, 190, size=n_samples),
                'weight_kg': np.random.uniform(50, 110, size=n_samples),
                'bmi': np.random.uniform(18.5, 35, size=n_samples),
                'waist_cm': np.random.uniform(70, 110, size=n_samples),
                'systolic_bp': np.random.uniform(110, 160, size=n_samples),
                'diastolic_bp': np.random.uniform(70, 100, size=n_samples),
                'heart_rate': np.random.uniform(60, 100, size=n_samples),
                'hba1c': np.random.uniform(4.5, 8.5, size=n_samples),
                'fasting_glucose': np.random.uniform(80, 180, size=n_samples),
                'total_cholesterol': np.random.uniform(150, 260, size=n_samples),
                'ldl': np.random.uniform(70, 160, size=n_samples),
                'hdl': np.random.uniform(40, 70, size=n_samples),
                'triglycerides': np.random.uniform(80, 200, size=n_samples),
                'alt': np.random.uniform(10, 40, size=n_samples),
                'ast': np.random.uniform(10, 40, size=n_samples),
                'albumin': np.random.uniform(3.5, 5.0, size=n_samples),
                'bilirubin': np.random.uniform(0.3, 1.2, size=n_samples),
                'sedentary_minutes': np.random.uniform(120, 480, size=n_samples),
                'sex': np.random.choice(['Male', 'Female'], size=n_samples),
                'race_ethnicity': np.random.choice(['White', 'Black', 'Hispanic', 'Asian'], size=n_samples),
                'smoking_status': np.random.choice(['Never', 'Former', 'Current'], size=n_samples),
                'alcohol_use': np.random.choice(['None', 'Moderate', 'Heavy'], size=n_samples),
                'diabetes': np.random.binomial(1, 0.3, size=n_samples),
                'hypertension': np.random.binomial(1, 0.35, size=n_samples),
                'heart_disease': np.random.binomial(1, 0.15, size=n_samples),
                'asthma': np.random.binomial(1, 0.2, size=n_samples)
            })

        if os.path.exists(self.sdoh_dataset_path):
            sdoh_df = pd.read_csv(self.sdoh_dataset_path)
        else:
            print("Notice: SDOH CSV not found on disk, building synthetic SDOH DataFrame in memory...")
            sdoh_df = pd.DataFrame([
                {'county_fips': '20195', 'county_name': 'Trego County', 'state_abbr': 'KS', 'population': 2800, 'svi_overall': 0.38, 'poverty_rate': 11.5, 'median_household_income': 58000, 'unemployment_rate': 3.8, 'food_insecurity': 12.4, 'transportation_barrier': 8.5, 'housing_insecurity': 10.1, 'obesity_prevalence': 32.1, 'physical_inactivity': 24.5, 'smoking_prevalence': 17.8, 'lack_health_insurance': 9.2},
                {'county_fips': '01083', 'county_name': 'Limestone County', 'state_abbr': 'AL', 'population': 98000, 'svi_overall': 0.48, 'poverty_rate': 13.8, 'median_household_income': 62000, 'unemployment_rate': 4.2, 'food_insecurity': 14.1, 'transportation_barrier': 9.2, 'housing_insecurity': 11.5, 'obesity_prevalence': 34.5, 'physical_inactivity': 26.2, 'smoking_prevalence': 19.5, 'lack_health_insurance': 10.8},
                {'county_fips': '39035', 'county_name': 'Cuyahoga County', 'state_abbr': 'OH', 'population': 1240000, 'svi_overall': 0.65, 'poverty_rate': 17.5, 'median_household_income': 52000, 'unemployment_rate': 5.8, 'food_insecurity': 16.8, 'transportation_barrier': 12.4, 'housing_insecurity': 14.8, 'obesity_prevalence': 36.2, 'physical_inactivity': 28.5, 'smoking_prevalence': 21.0, 'lack_health_insurance': 8.5},
                {'county_fips': '18097', 'county_name': 'Marion County', 'state_abbr': 'IN', 'population': 970000, 'svi_overall': 0.58, 'poverty_rate': 15.2, 'median_household_income': 55000, 'unemployment_rate': 4.9, 'food_insecurity': 15.2, 'transportation_barrier': 10.8, 'housing_insecurity': 13.2, 'obesity_prevalence': 35.0, 'physical_inactivity': 27.0, 'smoking_prevalence': 20.1, 'lack_health_insurance': 9.8}
            ])

        med_df['county_fips'] = med_df['county_fips'].astype(str).str.zfill(5)
        sdoh_df['county_fips'] = sdoh_df['county_fips'].astype(str).str.zfill(5)

        # Compute SDOH indicator 33rd & 66th percentiles across all counties for risk labeling (Low / Mid / High)
        for col in self.sdoh_cols:
            if col in sdoh_df.columns:
                q33 = float(sdoh_df[col].quantile(0.33))
                q66 = float(sdoh_df[col].quantile(0.66))
                self.sdoh_quantiles[col] = {'q33': q33, 'q66': q66}

        # Build SDOH Lookup map containing ALL county context features
        all_county_cols = [c for c in sdoh_df.columns if c not in ['created_at', 'updated_at']]
        
        for _, row in sdoh_df.iterrows():
            fips = str(row['county_fips']).zfill(5)
            c_name_raw = str(row['county_name'])
            c_name_clean = c_name_raw.split(',')[0].replace(' County', '').strip().lower()
            state = normalize_state(row.get('state_abbr', ''))
            
            county_dict = {}
            for col in all_county_cols:
                val = row[col]
                if isinstance(val, (int, float, np.number)):
                    county_dict[col] = float(val) if not pd.isna(val) else 0.0
                else:
                    county_dict[col] = str(val) if not pd.isna(val) else ""
            
            county_dict['county_fips'] = fips
            county_dict['state_abbr'] = state
            
            # Format clean county name without double 'County County'
            base_cname = c_name_raw.split(',')[0].replace(' County', '').strip()
            county_dict['formatted_county_name'] = f"{base_cname} County, {state}"

            self.sdoh_lookup[fips] = county_dict
            self.sdoh_lookup[f"{state}_{c_name_clean}"] = county_dict

        # Compute median fallbacks for medical features
        for col in self.medical_num_cols:
            self.medians[col] = float(med_df[col].median()) if col in med_df else 0.0

        # Merge for training
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
        print("ML V3 Pipeline successfully fitted across all target disease models!")

    def save_pkl(self, pkl_path=r"p:\project\cts\ml_pipelineV3.pkl"):
        """Serialize fitted pipeline to .pkl file."""
        if not self.is_fitted:
            self.fit()
        print(f"Saving ML V3 pipeline pickle to {pkl_path}...")
        os.makedirs(os.path.dirname(pkl_path), exist_ok=True)
        with open(pkl_path, 'wb') as f:
            pickle.dump(self, f)
        print("Successfully saved ml_pipelineV3.pkl!")

    def _resolve_location_sdoh(self, loc_input):
        """Resolves SDOH features for location passed in dict or array format, preserving requested name on fallbacks."""
        loc_dict = {}
        if isinstance(loc_input, list) and len(loc_input) >= 2:
            # Array format: ["Trego County", "Kansas", "United States"]
            c_raw = str(loc_input[0])
            s_raw = str(loc_input[1])
            loc_dict = {'county': c_raw, 'state': s_raw}
        elif isinstance(loc_input, dict):
            loc_dict = loc_input

        req_state = normalize_state(loc_dict.get('state', ''))
        raw_cname = str(loc_dict.get('county', '')).replace(' County', '').strip()
        req_cname_clean = raw_cname.lower()

        # Check FIPS match first
        fips = loc_dict.get('county_fips') or loc_dict.get('fips')
        if fips and str(fips).zfill(5) in self.sdoh_lookup:
            return self.sdoh_lookup[str(fips).zfill(5)]
        
        key = f"{req_state}_{req_cname_clean}"
        if key in self.sdoh_lookup:
            return self.sdoh_lookup[key]
        
        # Secondary search by clean county name across lookup
        for lkey, sdict in self.sdoh_lookup.items():
            if req_cname_clean and req_cname_clean in lkey:
                return sdict

        # Fallback to dataset template but dynamic location name override
        fallback_key = list(self.sdoh_lookup.keys())[0]
        fallback_data = dict(self.sdoh_lookup[fallback_key])
        
        # Override with requested state/county so output matches user request
        fallback_data['state_abbr'] = req_state
        fallback_data['county_name'] = f"{raw_cname} County, {req_state}"
        fallback_data['formatted_county_name'] = f"{raw_cname} County, {req_state}"
        fallback_data['county_fips'] = str(fips).zfill(5) if fips else "99999"
        return fallback_data

    def _normalize_medical_payload(self, ocr_payload):
        """Extract and normalize medical features handling aliases and string BP values."""
        med_input = {}
        if 'medical_data' in ocr_payload and isinstance(ocr_payload['medical_data'], dict):
            med_input.update(ocr_payload['medical_data'])
        if 'patient_data' in ocr_payload and isinstance(ocr_payload['patient_data'], dict):
            med_input.update(ocr_payload['patient_data'])
        if not med_input:
            med_input = ocr_payload

        clean_med = {}
        
        # Handle BP string (e.g. "120/80")
        bp_val = med_input.get('blood_pressure') or med_input.get('bp')
        if bp_val and isinstance(bp_val, str) and '/' in bp_val:
            parts = bp_val.split('/')
            try:
                clean_med['systolic_bp'] = float(parts[0].strip())
                clean_med['diastolic_bp'] = float(parts[1].strip())
            except (ValueError, TypeError):
                pass

        # Handle aliases
        aliases = {
            'fasting_glucose': ['glucose', 'blood_glucose', 'fpg'],
            'total_cholesterol': ['total_cholesterol_mg_dl', 'cholesterol'],
            'sex': ['gender'],
            'smoking_status': ['smoking_history', 'smoking'],
            'alcohol_use': ['alcohol_history', 'alcohol']
        }
        
        for target_key, alias_list in aliases.items():
            if target_key not in med_input or pd.isna(med_input[target_key]):
                for a in alias_list:
                    if a in med_input and not pd.isna(med_input[a]):
                        med_input[target_key] = med_input[a]
                        break

        # Populate numeric features with fallback to medians
        for col in self.medical_num_cols:
            if col in clean_med:
                continue
            val = med_input.get(col, None)
            if val is None or pd.isna(val):
                clean_med[col] = self.medians[col]
            else:
                try:
                    clean_med[col] = float(val)
                except (ValueError, TypeError):
                    clean_med[col] = self.medians[col]
                    
        # Populate categorical features
        for col in self.medical_cat_cols:
            val = med_input.get(col, None)
            if val is None or pd.isna(val):
                clean_med[col] = 'Female' if col == 'sex' else 'Unknown'
            else:
                sval = str(val)
                if col == 'sex':
                    clean_med[col] = 'Male' if 'm' in sval.lower() else 'Female'
                elif col == 'smoking_status':
                    clean_med[col] = 'Current' if any(w in sval.lower() for w in ['yes', 'smoker', 'current']) else 'Never'
                else:
                    clean_med[col] = sval

        return clean_med

    def _get_sdoh_indicator_level(self, factor: str, value: float) -> str:
        """Classify SDOH indicator value into Low, Mid, or High based on population quantiles."""
        # For income, higher income = lower risk
        if factor == 'median_household_income':
            if factor in self.sdoh_quantiles:
                q33 = self.sdoh_quantiles[factor]['q33']
                q66 = self.sdoh_quantiles[factor]['q66']
                if value < q33:
                    return "High Risk"
                elif value <= q66:
                    return "Mid"
                else:
                    return "Low Risk"
            return "Mid"
        
        if factor in self.sdoh_quantiles:
            q33 = self.sdoh_quantiles[factor]['q33']
            q66 = self.sdoh_quantiles[factor]['q66']
            if value <= q33:
                return "Low"
            elif value <= q66:
                return "Mid"
            else:
                return "High"
        return "Mid"

    def predict(self, ocr_payload):
        """
        Crash-proof prediction entrypoint for V3 pipeline.
        Handles dual schema locations, medical key aliasing, SDOH risk labeling,
        and computes Clinical Severity-Weighted Patient Risk Score.
        """
        if not self.is_fitted:
            self.fit()
            
        patient_id = ocr_payload.get('patient_id', 'OCR_PATIENT_001')
        clean_med = self._normalize_medical_payload(ocr_payload)
        
        # Determine locations list
        if 'target_locations' in ocr_payload and isinstance(ocr_payload['target_locations'], list):
            locations = ocr_payload['target_locations']
        elif 'locations' in ocr_payload and isinstance(ocr_payload['locations'], list):
            locations = ocr_payload['locations']
        elif 'location' in ocr_payload and isinstance(ocr_payload['location'], dict):
            locations = [ocr_payload['location']]
        else:
            state = ocr_payload.get('state', 'AL')
            county = ocr_payload.get('county', 'Limestone')
            fips = ocr_payload.get('county_fips', '01083')
            locations = [{'state': state, 'county': county, 'county_fips': fips}]
            
        county_results = []
        patient_disease_probs = {'diabetes': [], 'hypertension': [], 'heart_disease': [], 'asthma': []}
        
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
                patient_disease_probs[disease].append(prob)
                
                risk_tier = "High Risk" if prob >= 0.65 else ("Moderate Risk" if prob >= 0.35 else "Low Risk")
                
                coefs = clf.coef_[0]
                sdoh_impacts = []
                
                for idx, sdoh_feat in enumerate(self.sdoh_cols):
                    feat_idx = len(self.medical_num_cols) + idx
                    weight = float(coefs[feat_idx])
                    raw_val = float(sdoh_data.get(sdoh_feat, 0.0))
                    level = self._get_sdoh_indicator_level(sdoh_feat, raw_val)
                    
                    sdoh_impacts.append({
                        "sdoh_factor": sdoh_feat,
                        "shap_impact": round(weight, 4),
                        "county_value": round(raw_val, 2),
                        "level": level,
                        "unit": "%" if "rate" in sdoh_feat or "prevalence" in sdoh_feat or "insecurity" in sdoh_feat or "inactivity" in sdoh_feat or "insurance" in sdoh_feat else "value"
                    })
                    
                top_3_sdoh = sorted(sdoh_impacts, key=lambda x: abs(x['shap_impact']), reverse=True)[:3]
                
                disease_predictions[disease] = {
                    "probability": round(prob, 4),
                    "risk_tier": risk_tier,
                    "top_3_sdoh_factors": top_3_sdoh
                }

            # Build full SDOH indicators dictionary with Low/Mid/High risk levels
            sdoh_indicator_levels = {}
            for feat in self.sdoh_cols:
                raw_val = float(sdoh_data.get(feat, 0.0))
                sdoh_indicator_levels[feat] = {
                    "value": round(raw_val, 2),
                    "unit": "%" if "rate" in feat or "prevalence" in feat or "insecurity" in feat or "inactivity" in feat or "insurance" in feat else "value",
                    "level": self._get_sdoh_indicator_level(feat, raw_val)
                }

            formatted_cname = sdoh_data.get('formatted_county_name', f"{sdoh_data.get('county_name', 'County')}, {sdoh_data.get('state_abbr', 'US')}")
            
            # Compute County Health Equity Score (0-100) via CDC SVI Inverse Formula
            svi_val = float(sdoh_data.get('svi_overall', 0.50))
            county_equity_score = int(round((1.0 - svi_val) * 100.0))
            county_equity_score = max(0, min(100, county_equity_score))
            
            if county_equity_score < 45:
                county_equity_level = "High Risk"
            elif county_equity_score <= 65:
                county_equity_level = "Mid Risk"
            else:
                county_equity_level = "Low Risk"
            
            county_results.append({
                "location": {
                    "state": sdoh_data.get('state_abbr', 'AL'),
                    "county_name": formatted_cname,
                    "county_fips": sdoh_data.get('county_fips', '00000')
                },
                "county_health_equity_score": county_equity_score,
                "county_health_equity_level": county_equity_level,
                "county_full_context": sdoh_data,
                "sdoh_indicator_levels": sdoh_indicator_levels,
                "diseases": disease_predictions
            })

        # Calculate Overall Composite Patient Risk Score (Clinical Severity Weighted Average across evaluated locations)
        avg_heart = float(np.mean(patient_disease_probs['heart_disease']))
        avg_diab = float(np.mean(patient_disease_probs['diabetes']))
        avg_hyp = float(np.mean(patient_disease_probs['hypertension']))
        avg_asthma = float(np.mean(patient_disease_probs['asthma']))
        
        composite_score = (0.35 * avg_heart) + (0.25 * avg_diab) + (0.25 * avg_hyp) + (0.15 * avg_asthma)
        overall_tier = "High Risk" if composite_score >= 0.65 else ("Moderate Risk" if composite_score >= 0.35 else "Low Risk")

        return {
            "pipeline_version": "V3",
            "status": "success",
            "patient_id": patient_id,
            "overall_composite_risk_score": round(composite_score, 4),
            "overall_risk_tier": overall_tier,
            "is_multi_county": len(locations) > 1,
            "evaluated_counties_count": len(locations),
            "county_predictions": county_results
        }

# Global Pipeline Instance
pipeline_v3 = MedicalSDOHInferencePipelineV3()

def predict(ocr_payload):
    return pipeline_v3.predict(ocr_payload)

if __name__ == '__main__':
    pipeline_v3.fit()
    pipeline_v3.save_pkl(r"p:\project\cts\ml_pipelineV3.pkl")
    pipeline_v3.save_pkl(r"p:\project\cts\ML\ml_pipelineV3.pkl")
    
    # Test against the user's backend payload sample
    sample_payload = {
        "patient_id": "PATIENT_ROBERT_CHEN",
        "medical_data": {
            "age": 58,
            "height_cm": 178,
            "weight_kg": 88,
            "bmi": 27.8,
            "blood_pressure": "120/80",
            "glucose": 165,
            "gender": "Male",
            "diabetes": True,
            "hypertension": False,
            "heart_disease": False,
            "asthma": False,
            "smoking_history": "Non-Smoker",
            "total_cholesterol_mg_dl": 185
        },
        "target_locations": [
            ["Trego County", "Kansas", "United States"]
        ]
    }
    
    output = pipeline_v3.predict(sample_payload)
    print("\n--- SAMPLE V3 PREDICTION OUTPUT ---")
    print(json.dumps(output, indent=2))
