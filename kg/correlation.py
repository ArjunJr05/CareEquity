import pandas as pd

# Load dataset
df = pd.read_csv(r"d:\KNOW GRAPH ANTYGRA\SDOH_MODEL_DATA.csv")

health_cols = [
    'diabetes_prevalence',
    'obesity_prevalence',
    'high_bp_prevalence',
    'physical_inactivity',
    'smoking_prevalence',
    'heart_disease_prevalence',
    'poor_mental_health',
    'poor_physical_health'
]

sdoh_cols = [
    'population',
    'median_household_income',
    'poverty_rate',
    'unemployment_rate',
    'no_vehicle_rate',
    'internet_subscription_rate',
    'svi_socioeconomic',
    'svi_household_disability',
    'svi_racial_ethnic_minority',
    'svi_housing_transportation',
    'svi_overall',
    'food_insecurity',
    'transportation_barrier',
    'housing_insecurity',
    'lack_health_insurance',
    'low_access_population_pct_2019',
    'low_income_low_access_pct_2019',
    'no_car_low_access_pct_2019',
    'snap_low_access_pct_2019',
    'grocery_stores_per_1000_2020',
    'fast_food_per_1000_2020'
]

print("=== CORRELATION ANALYSIS: SDoH vs. Health Outcomes ===")
corr_matrix = df[sdoh_cols + health_cols].corr()

# For each health outcome, find the top 5 correlated SDoH variables
for health in health_cols:
    print(f"\nTop SDoH Correlates for: {health.upper()}")
    corrs = corr_matrix[health].loc[sdoh_cols].sort_values(ascending=False)
    print("Positive Correlations:")
    for col, val in corrs.head(5).items():
        print(f"  {col:<35} : {val:.4f}")
    print("Negative Correlations:")
    for col, val in corrs.tail(5).items():
        print(f"  {col:<35} : {val:.4f}")
