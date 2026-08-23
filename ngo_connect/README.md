# 🏥 CareEquity — SDoH Intervention Finder

A Streamlit application that maps Social Determinants of Health (SDoH) risk across every US county, recommends targeted interventions, and surfaces verified nearby NGOs — with direct email outreach built in.

---

## Features

- **County SDoH profiling** — food insecurity, housing, transport, healthcare, employment, utility scores for all 3,222 US counties
- **Ranked interventions** — top 3 priority interventions per county, severity-scored and colour-coded
- **1,275 verified NGOs** — pre-built CSV covering all 50 states + DC across 5 SDoH domains
- **Interactive maps** — Folium maps with distance lines, county centre pin, org markers
- **Direct email** — sends real SMTP emails to organisations straight from the app
- **No live API calls** — all NGO data served from the local CSV instantly

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-username/careequity.git
cd careequity

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure email (copy template, fill in your Gmail App Password)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your credentials

# 4. Run
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Email Setup (Gmail App Password)

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Search **"App passwords"** → create one → copy the 16-character code
4. Paste into `.streamlit/secrets.toml`:

```toml
[smtp]
host      = "smtp.gmail.com"
port      = 587
username  = "you@gmail.com"
password  = "xxxx xxxx xxxx xxxx"
from_name = "CareEquity Platform"
```

Without this, the app still works — the Send button opens your local email client instead.

---

## Project Structure

```
careequity/
│
├── app.py                        # Main Streamlit application
├── intervention_engine.py        # SDoH scoring & intervention ranking
├── csv_ngo_loader.py             # CSV → org dict pipeline (primary NGO source)
├── email_sender.py               # SMTP email delivery
├── email_scraper.py              # Email enrichment for directory orgs
├── geocode_counties.py           # Census TIGERweb county geocoder
├── ngo_directory.py              # Hardcoded fallback NGO directory
│
├── SDOH_MODEL_DATA.csv           # 3,222-county SDoH metrics dataset
├── careequity_master_sdoh_ngo.csv # 1,275 verified NGOs (all states)
│
├── build_master_csv.py           # CSV builder (geocode + dedup + save)
├── run_all_batches.py            # Runs all 5 batch scripts in sequence
├── batch_pipeline.py             # Full offline batch pipeline
├── batch01_AL_to_GA.py           # NGO data: AL AK AZ AR CA CO CT DE FL GA
├── batch02_HI_to_MD.py           # NGO data: HI ID IL IN IA KS KY LA ME MD
├── batch03_MA_to_NJ.py           # NGO data: MA MI MN MS MO MT NE NV NH NJ
├── batch04_NM_to_SC.py           # NGO data: NM NY NC ND OH OK OR PA RI SC
├── batch05_SD_to_DC.py           # NGO data: SD TN TX UT VT VA WA WV WI WY DC
│
├── requirements.txt
├── .gitignore
└── .streamlit/
    ├── config.toml               # Theme + server settings
    └── secrets.toml.example      # SMTP template (copy → secrets.toml)
```

---

## NGO Data Coverage

| Domain | CSV Column | States |
|---|---|---|
| Food | `Food` | All 51 |
| Housing | `Housing` | All 51 |
| Transportation | `Transportation` | All 51 |
| Healthcare | `Healthcare` | All 51 |
| Employment | `Education-Employment` | All 51 |
| Utility Assistance | *(directory fallback)* | National orgs |

---

## Rebuilding the NGO CSV

If you want to update or regenerate `careequity_master_sdoh_ngo.csv`:

```bash
# Run all 5 batch files + geocode
python run_all_batches.py

# Or geocode only (fills missing lat/lon)
python build_master_csv.py

# Check stats
python build_master_csv.py --check
```

---

## Dependencies

| Package | Version | Use |
|---|---|---|
| streamlit | 1.35.0 | Web UI |
| folium | 0.20.0 | Interactive maps |
| streamlit-folium | 0.20.0 | Folium ↔ Streamlit bridge |
| pandas | 2.2.2 | Data processing |
| numpy | 1.26.4 | Normalization |
| requests | 2.32.3 | Census geocoding API |

---

## Security Notes

- `.streamlit/secrets.toml` is in `.gitignore` — **never committed**
- Gmail App Passwords are account-specific and can be revoked at any time
- No API keys are hardcoded in source files
