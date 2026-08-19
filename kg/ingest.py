import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Feature mapping lists
health_cols = {
    'diabetes_prevalence': 'Diabetes',
    'obesity_prevalence': 'Obesity',
    'high_bp_prevalence': 'High Blood Pressure',
    'physical_inactivity': 'Physical Inactivity',
    'smoking_prevalence': 'Smoking',
    'heart_disease_prevalence': 'Heart Disease',
    'poor_mental_health': 'Poor Mental Health',
    'poor_physical_health': 'Poor Physical Health'
}

sdoh_cols = {
    'poverty_rate': ('Poverty Rate', 'Socioeconomic'),
    'unemployment_rate': ('Unemployment Rate', 'Socioeconomic'),
    'no_vehicle_rate': ('No Vehicle Rate', 'Infrastructure'),
    'internet_subscription_rate': ('Internet Subscription Rate', 'Infrastructure'),
    'lack_health_insurance': ('Lack of Health Insurance', 'Socioeconomic'),
    'food_insecurity': ('Food Insecurity', 'Food Access'),
    'transportation_barrier': ('Transportation Barrier', 'Infrastructure'),
    'housing_insecurity': ('Housing Insecurity', 'Socioeconomic'),
    'low_access_population_pct_2019': ('Low Food Access Pct', 'Food Access'),
    'snap_low_access_pct_2019': ('SNAP Low Access Pct', 'Food Access'),
    'grocery_stores_per_1000_2020': ('Grocery Store Density', 'Food Access'),
    'fast_food_per_1000_2020': ('Fast Food Density', 'Food Access')
}

def clean_and_prepare_db(driver):
    """
    Sets up constraints and clears old SDOH data.
    """
    print("Clearing existing SDOH model elements from database...")
    with driver.session() as session:
        # Clear relationships first, then nodes
        session.run("MATCH (c:County) DETACH DELETE c")
        session.run("MATCH (s:State) DETACH DELETE s")
        session.run("MATCH (f:SDoHFactor) DETACH DELETE f")
        session.run("MATCH (h:HealthOutcome) DETACH DELETE h")
        
        # Setup constraints
        session.run("CREATE CONSTRAINT county_fips IF NOT EXISTS FOR (c:County) REQUIRE c.fips IS UNIQUE")
        session.run("CREATE CONSTRAINT state_abbr IF NOT EXISTS FOR (s:State) REQUIRE s.abbr IS UNIQUE")
        session.run("CREATE CONSTRAINT sdoh_factor_name IF NOT EXISTS FOR (f:SDoHFactor) REQUIRE f.name IS UNIQUE")
        session.run("CREATE CONSTRAINT health_outcome_name IF NOT EXISTS FOR (h:HealthOutcome) REQUIRE h.name IS UNIQUE")
    print("Database preparation completed.")

def ingest_global_nodes_and_correlations(driver, corr_matrix):
    """
    Creates global SDoHFactor and HealthOutcome nodes, linking them by computed correlations.
    """
    print("Ingesting global factor nodes and correlation links...")
    with driver.session() as session:
        # Create SDoH Factor Nodes
        for col, (name, category) in sdoh_cols.items():
            session.run(
                "MERGE (f:SDoHFactor {name: $name}) ON CREATE SET f.category = $category",
                name=name, category=category
            )
            
        # Create Health Outcome Nodes
        for col, name in health_cols.items():
            session.run("MERGE (h:HealthOutcome {name: $name})", name=name)
            
        # Create CORRELATES_WITH relationships based on Pearson correlation coefficient
        for sdoh_col, (sdoh_name, _) in sdoh_cols.items():
            for health_col, health_name in health_cols.items():
                coef = corr_matrix.loc[sdoh_col, health_col]
                # Filter out weak correlations (threshold absolute value >= 0.25)
                if abs(coef) >= 0.25:
                    direction = "Positive" if coef > 0 else "Negative"
                    strength = "Strong" if abs(coef) >= 0.6 else "Moderate"
                    
                    session.run("""
                        MATCH (f:SDoHFactor {name: $sdoh_name})
                        MATCH (h:HealthOutcome {name: $health_name})
                        MERGE (f)-[r:CORRELATES_WITH]->(h)
                        SET r.coefficient = $coefficient,
                            r.direction = $direction,
                            r.strength = $strength
                        """,
                        sdoh_name=sdoh_name,
                        health_name=health_name,
                        coefficient=float(coef),
                        direction=direction,
                        strength=strength
                    )
    print("Global factors and correlation matrix ingested.")

def get_severity(val, mean_val, std_val, is_protective=False):
    """
    Assigns severity relative to national mean.
    For protective features (high is good): high value = Low Risk, low value = High Risk.
    For risk features (high is bad): high value = High Risk, low value = Low Risk.
    """
    if is_protective:
        if val > mean_val + 0.5 * std_val:
            return "Low (Protective)"
        elif val < mean_val - 0.5 * std_val:
            return "High Risk"
        else:
            return "Medium"
    else:
        if val > mean_val + 0.5 * std_val:
            return "High Risk"
        elif val < mean_val - 0.5 * std_val:
            return "Low Risk"
        else:
            return "Medium"

def ingest_counties(driver, df, means, stds):
    """
    Ingests all 3,222 counties in batches using UNWIND for high performance.
    """
    print("Formatting county batches for ingestion...")
    counties_data = []
    
    for idx, row in df.iterrows():
        # Formulate factor list for county
        factors = []
        for col, (name, _) in sdoh_cols.items():
            is_protective = col in ['internet_subscription_rate', 'grocery_stores_per_1000_2020']
            severity = get_severity(row[col], means[col], stds[col], is_protective)
            factors.append({
                "name": name,
                "value": float(row[col]),
                "severity": severity
            })
            
        # Formulate outcome list for county
        outcomes = []
        for col, name in health_cols.items():
            severity = get_severity(row[col], means[col], stds[col], is_protective=False)
            outcomes.append({
                "name": name,
                "value": float(row[col]),
                "severity": severity
            })
            
        # Compile county dictionary
        counties_data.append({
            "fips": str(int(row['county_fips'])),
            "name": row['county_name'],
            "state_abbr": row['state_abbr'],
            "population": int(row['population']),
            "median_household_income": float(row['median_household_income']) if not pd.isna(row['median_household_income']) else 0.0,
            "svi_overall": float(row['svi_overall']) if not pd.isna(row['svi_overall']) else 0.0,
            "factors": factors,
            "outcomes": outcomes
        })
        
    print(f"Total counties to ingest: {len(counties_data)}")
    
    # Ingest in batches of 100
    batch_size = 100
    total_batches = (len(counties_data) + batch_size - 1) // batch_size
    
    query = """
    UNWIND $batch AS cData
    MERGE (s:State {abbr: cData.state_abbr})
    MERGE (c:County {fips: cData.fips})
    SET c.name = cData.name,
        c.population = cData.population,
        c.median_household_income = cData.median_household_income,
        c.svi_overall = cData.svi_overall
    MERGE (c)-[:IN_STATE]->(s)
    
    WITH c, cData
    UNWIND cData.factors AS factor
    MATCH (f:SDoHFactor {name: factor.name})
    MERGE (c)-[:HAS_FACTOR {value: factor.value, severity: factor.severity}]->(f)
    
    WITH c, cData
    UNWIND cData.outcomes AS outcome
    MATCH (h:HealthOutcome {name: outcome.name})
    MERGE (c)-[:HAS_OUTCOME {prevalence: outcome.value, severity: outcome.severity}]->(h)
    """
    
    with driver.session() as session:
        for i in range(total_batches):
            batch = counties_data[i*batch_size : (i+1)*batch_size]
            session.run(query, batch=batch)
            print(f"Ingested batch {i+1} of {total_batches} ({len(batch)} counties)...")
            
    print("County ingestion completed successfully!")

def main():
    if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
        print("Error: Neo4j Aura credentials not fully set in .env file.")
        return
        
    print(f"Connecting to Neo4j instance at {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    try:
        # Load CSV and compute stats
        df = pd.read_csv(r"d:\KNOW GRAPH ANTYGRA\SDOH_MODEL_DATA.csv")
        means = df.mean(numeric_only=True)
        stds = df.std(numeric_only=True)
        
        # Calculate Pearson correlations
        corr_matrix = df[list(sdoh_cols.keys()) + list(health_cols.keys())].corr()
        
        # Prepare DB
        clean_and_prepare_db(driver)
        
        # Ingest nodes & correlations
        ingest_global_nodes_and_correlations(driver, corr_matrix)
        
        # Ingest county network
        ingest_counties(driver, df, means, stds)
        
        print("\n=== SDOH KNOWLEDGE GRAPH BUILT SUCCESSFULLY IN NEO4J AURA! ===")
    except Exception as e:
        print(f"An error occurred during ingestion: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()
