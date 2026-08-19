# SDoH Dataset Analysis Report

This report provides a comprehensive analysis of the **Social Determinants of Health (SDoH) Risk Dataset** located in `d:\KNOW GRAPH ANTYGRA\SDOH_MODEL_DATA.csv`. The dataset integrates county-level socioeconomic, infrastructure, food access, and health prevalence metrics across the United States.

---

## 1. Dataset Overview

* **Observations (Rows):** 3,222 counties and county-equivalents.
* **Features (Columns):** 35 columns, comprising structural identifiers, demographic variables, SDoH barriers, health outcomes, and data missing flags.
* **Geographical Coverage:** 52 unique State/Territory codes, including all 50 US States, the District of Columbia (`DC`), and Puerto Rico (`PR`).

---

## 2. Feature Schema & Description

The features can be categorized into four primary domains:

| Category | Variable Name | Data Type | Description |
| :--- | :--- | :--- | :--- |
| **Identifiers & Demographics** | `county_fips` | Integer | Unique Federal Information Processing Standards (FIPS) county code |
| | `county_name` | String | Name of the county |
| | `state_abbr` | String | Two-letter state/territory abbreviation |
| | `population` | Integer | Total population of the county |
| **SDoH Barriers (Socioeconomic & Infrastructure)** | `median_household_income` | Float | Median annual household income (USD) |
| | `poverty_rate` | Float | Percentage of population living below the poverty line |
| | `unemployment_rate` | Float | Unemployment rate (%) |
| | `no_vehicle_rate` | Float | Percentage of households with no registered vehicle |
| | `internet_subscription_rate`| Float | Percentage of households with an active broadband subscription |
| | `svi_socioeconomic` | Float | CDC Social Vulnerability Index (SVI) Socioeconomic percentile |
| | `svi_household_disability` | Float | SVI Household Composition & Disability percentile |
| | `svi_racial_ethnic_minority`| Float | SVI Minority & Language percentile |
| | `svi_housing_transportation`| Float | SVI Housing Type & Transportation percentile |
| | `svi_overall` | Float | CDC SVI Overall social vulnerability score (0.0 to 1.0) |
| | `lack_health_insurance` | Float | Percentage of population lacking health insurance |
| **SDoH Barriers (Food Access & Retail)** | `food_insecurity` | Float | Percentage of population experiencing food insecurity |
| | `transportation_barrier` | Float | Percentage of population facing transportation barriers to food/care |
| | `housing_insecurity` | Float | Percentage of population facing housing instability |
| | `low_access_population_pct` | Float | Pct of population with low access to a grocery store |
| | `low_income_low_access_pct` | Float | Pct of low-income population with low grocery access |
| | `no_car_low_access_pct` | Float | Pct of population with no vehicle and low grocery access |
| | `snap_low_access_pct` | Float | Pct of population on SNAP benefits with low grocery access |
| | `grocery_stores_per_1000` | Float | Number of grocery stores per 1,000 residents (2020) |
| | `fast_food_per_1000` | Float | Number of fast food restaurants per 1,000 residents (2020) |
| **Health Outcomes** | `diabetes_prevalence` | Float | Percentage of adult population with diagnosed diabetes |
| (CDC PLACES) | `obesity_prevalence` | Float | Percentage of adult population with obesity |
| | `high_bp_prevalence` | Float | Percentage of adult population with high blood pressure |
| | `physical_inactivity` | Float | Percentage of adults reporting no leisure-time physical activity |
| | `smoking_prevalence` | Float | Percentage of adults who currently smoke |
| | `heart_disease_prevalence` | Float | Percentage of adults with coronary heart disease |
| | `poor_mental_health` | Float | Prevalence of adults reporting 14+ poor mental health days/month |
| | `poor_physical_health` | Float | Prevalence of adults reporting 14+ poor physical health days/month |
| **Data Quality Indicators** | `places_data_missing` | Binary | Flag indicating if CDC PLACES data was missing |
| | `svi_data_missing` | Binary | Flag indicating if CDC SVI data was missing |
| | `usda_data_missing` | Binary | Flag indicating if USDA food atlas data was missing |

---

## 3. Descriptive Statistics & Data Range Highlights

The dataset spans highly diverse environments—from highly urbanized metropolitan counties to tiny rural outposts.

* **Population:** Ranges from **50 residents** (Kalawao County, HI) to **9.93 million residents** (Los Angeles County, CA).
* **Household Income:** Median household income averages **$62,326**, spanning from **$14,525** (Guánica Municipio, PR) to **$170,463** (Loudoun County, VA).
* **Poverty Rates:** Poverty rates range from **1.6%** to **66.32%**, with an average of **15.1%**.
* **Health Outcomes:**
  * **Obesity Prevalence:** Averages **37.67%**, peaking at **54.0%** (Perry County, AL).
  * **Diabetes Prevalence:** Averages **11.13%**, peaking at **23.8%** (Oglala Lakota County, SD).
  * **Lack of Health Insurance:** Averages **11.57%**, peaking at **43.7%** (Starr County, TX).

---

## 4. Key Findings: SDoH Drivers of Health Outcomes

A Pearson correlation analysis reveals crucial insights into how structural and social barriers affect public health outcomes. 

### A. Socioeconomic Insecurity is the Strongest Predictor of Chronic Disease
Health outcomes such as **diabetes, high blood pressure, and poor physical health** are extremely strongly correlated with material hardship variables:

* **Food Insecurity** has a massive positive correlation with:
  * Diabetes prevalence: **+0.7920**
  * High blood pressure: **+0.7726**
  * Poor physical health: **+0.6929**
* **Housing Insecurity** and **Transportation Barriers** show similarly high correlations of **+0.7788** and **+0.7716** respectively with diabetes.
* **Overall Social Vulnerability (SVI Overall)** shows a **+0.7100** correlation with diabetes and **+0.6556** with poor physical health.

### B. Income and Infrastructure Act as Protective Shields
Conversely, wealth and digital access are strongly negatively correlated with chronic illnesses:

* **Median Household Income** is strongly negatively correlated with:
  * Heart disease: **-0.7168**
  * Poor physical health: **-0.6773**
  * Smoking: **-0.6633**
  * Diabetes: **-0.5569**
* **Internet Subscription Rate** also displays strong protective correlations:
  * Heart disease: **-0.6439**
  * Smoking: **-0.6042**
  * Poor physical health: **-0.6023**
  * Diabetes: **-0.5660**

> [!NOTE]
> High internet subscription rates are typically a proxy for both technological infrastructure and household resources, which facilitate telehealth access, health literacy, and remote work opportunities.

### C. Geographic Access vs. Economic Security (The Food Desert Paradox)
Intriguingly, the raw geographical distance metric **`low_access_population_pct_2019`** (percentage of population living far from a grocery store) has virtually **zero correlation** with health outcomes (e.g., **-0.0411** with diabetes, **-0.0586** with obesity).

However, when adjusting for resource levels:
* **`snap_low_access_pct_2019`** (low access *and* SNAP recipient status) has a strong positive correlation with:
  * Heart disease: **+0.6526**
  * Smoking: **+0.6198**
  * Poor mental health: **+0.5998**
  * High blood pressure: **+0.5958**

> [!IMPORTANT]
> This suggests that geographical distance to food sources alone does not cause poor health outcomes, but rather the **intersection of low access and low financial resources** (requiring SNAP assistance) creates the severe health risks.

---

## 5. Data Completeness & Missing Values

The dataset is clean and pre-imputed (having no raw null values), but includes indicator flags for observations where original data sources were missing:

* **PLACES Data Missing:** **266 counties** (8.25%) are missing CDC health prevalence data.
* **USDA Food Data Missing:** **89 counties** (2.76%) are missing food accessibility/retail metrics.
* **SVI Data Missing:** **78 counties** (2.42%) are missing CDC Social Vulnerability Index metrics.
