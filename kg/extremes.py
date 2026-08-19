import pandas as pd

# Load dataset
df = pd.read_csv(r"d:\KNOW GRAPH ANTYGRA\SDOH_MODEL_DATA.csv")

print("=== EXTREMES IN THE DATASET ===")

print("\nHighest Poverty Rate:")
row = df.loc[df['poverty_rate'].idxmax()]
print(f"  {row['county_name']} ({row['state_abbr']}): {row['poverty_rate']}% (Income: ${row['median_household_income']:.0f})")

print("\nHighest Median Household Income:")
row = df.loc[df['median_household_income'].idxmax()]
print(f"  {row['county_name']} ({row['state_abbr']}): ${row['median_household_income']:.0f} (Poverty: {row['poverty_rate']}%)")

print("\nHighest Diabetes Prevalence:")
row = df.loc[df['diabetes_prevalence'].idxmax()]
print(f"  {row['county_name']} ({row['state_abbr']}): {row['diabetes_prevalence']}% (Obesity: {row['obesity_prevalence']}%)")

print("\nHighest Obesity Prevalence:")
row = df.loc[df['obesity_prevalence'].idxmax()]
print(f"  {row['county_name']} ({row['state_abbr']}): {row['obesity_prevalence']}% (Physical Inactivity: {row['physical_inactivity']}%)")

print("\nHighest Food Insecurity:")
row = df.loc[df['food_insecurity'].idxmax()]
print(f"  {row['county_name']} ({row['state_abbr']}): {row['food_insecurity']}% (Poverty: {row['poverty_rate']}%)")

print("\nHighest Transportation Barrier:")
row = df.loc[df['transportation_barrier'].idxmax()]
print(f"  {row['county_name']} ({row['state_abbr']}): {row['transportation_barrier']}% (No Vehicle Rate: {row['no_vehicle_rate']}%)")

print("\nHighest Lack of Health Insurance:")
row = df.loc[df['lack_health_insurance'].idxmax()]
print(f"  {row['county_name']} ({row['state_abbr']}): {row['lack_health_insurance']}%")

print("\nHighest Overall SVI (Social Vulnerability):")
row = df.loc[df['svi_overall'].idxmax()]
print(f"  {row['county_name']} ({row['state_abbr']}): SVI={row['svi_overall']} (Poverty: {row['poverty_rate']}%)")
