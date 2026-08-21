# 🏥 CareEquity SDOH Multi-Agent Research Assistant

An ultra-fast, high-reliability AI assistant designed to analyze **Social Determinants of Health (SDOH)** for complex patient risk cases, mapping clinical disease factors to localized community safety-net resources, tracking live public health disease outbreaks, and synthesizing actionable, evidence-based care intervention plans.

---

## 🏗️ Architecture: Client-Server Model

```
┌────────────────────────────────────────────────────────┐
│               Streamlit Frontend Client                │
│                   (streamlit_app.py)                   │
│        • Interactive Patient Input & Presets           │
│        • Live Multi-Agent Pipeline Visualizer          │
│        • Live Web Disease Surveillance Alerts          │
│        • Downloadable Clinical Markdown Reports        │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (JSON)
                            ▼
┌────────────────────────────────────────────────────────┐
│                 FastAPI Backend Service                │
│                        (main.py)                       │
│        • POST /api/analyze                             │
│        • GET /api/presets                              │
│        • GET /api/health                               │
│        • POST /api/test                                │
│        • Auto-Generated Docs: /docs (Swagger)          │
└───────────────────────────┬────────────────────────────┘
                            │
       ┌────────────────────┴───────────────────┐
       ▼                                        ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│    Parallel Multi-Agent      │ │      Multi-Provider LLM      │
│     Orchestration Engine     │ │            Client            │
│   • Health Analyzer Agent    │ │   • Groq (compound-mini)     │
│   • Geographic Agent         │ │   • NVIDIA (Llama 3.1 8B)    │
│   • Safety Net Locator       │ │   • OpenRouter (Free Tier)   │
│   • Live Web Surveillance    │ │   • High-Quality Offline     │
│   • Report Synthesizer       │ │     Knowledge Base           │
└──────────────────────────────┘ └──────────────────────────────┘
```

---

## ⚡ Multi-Agent Pipeline & Live Web Search

1. **Agent 1: Health & SDOH Risk Analyzer (`agents/health_analyzer.py`)**  
   Evaluates primary chronic conditions (Diabetes, Hypertension, CHF, COPD, Depression), disease exacerbation risks, and patient SDOH barrier impacts.
2. **Agent 2: Geographic & Environment Specialist (`agents/geographic_agent.py`)**  
   Evaluates area health demographics, environmental determinants (air quality, food deserts, walkability), and racial/income health disparities.
3. **Agent 3: Local Resource & Service Locator (`agents/resource_locator.py`)**  
   Maps real-world healthcare facilities (FQHCs, safety-net hospitals), medical transit voucher programs, condition-specific food pantries, emergency rental/utility relief, and crisis hotlines.
4. **Live Web Search: Disease Surveillance Agent (`agents/web_search_agent.py`)**  
   Queries live web search engines in real time for local disease outbreaks, department of health advisories, seasonal surges, and environmental alerts.
5. **Agent 4: Intervention & Report Synthesizer (`agents/report_synthesizer.py`)**  
   Synthesizes findings into structured, evidence-backed SDOH interventions (benefits, how to access, clinical outcomes, timelines) and formats a comprehensive clinical care report.

---

## 📁 Directory Structure

```
research_assis/
├── agents/
│   ├── __init__.py
│   ├── health_analyzer.py        # Agent 1: Clinical & SDOH Risk Analyzer
│   ├── geographic_agent.py       # Agent 2: Geographic & Demographics Specialist
│   ├── resource_locator.py       # Agent 3: Local Safety-Net Resource Locator
│   ├── web_search_agent.py       # Live Web Search Disease Surveillance Agent
│   └── report_synthesizer.py     # Agent 4: Intervention & Care Plan Synthesizer
├── config/
│   ├── __init__.py
│   ├── settings.py               # Environment configuration & model endpoints
│   ├── llm_client.py             # Multi-provider LLM with auto-failover
│   └── llm.py                    # Backward-compatibility layer
├── models/
│   ├── __init__.py
│   └── schemas.py                # Typed Pydantic models & schemas
├── workflow.py                   # Parallel multi-agent orchestration engine
├── main.py                       # FastAPI Backend Service (REST API)
├── streamlit_app.py              # Streamlit Frontend Client (Web Dashboard)
├── requirements.txt              # Project dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore configuration
└── README.md                     # Documentation
```

---

## 🔌 API Endpoints Reference (`main.py`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Root status with active provider configuration |
| `GET` | `/api/health` | Health check & active LLM models |
| `GET` | `/api/presets` | Pre-configured patient risk cases |
| `POST` | `/api/analyze` | Executes multi-agent analysis with live web search |
| `POST` | `/api/test` | Automated system diagnostics suite |
| `GET` | `/docs` | Interactive Swagger API documentation |

---

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API keys (optional, offline fallback active):
```bash
cp .env.example .env
```

### 3. Start the FastAPI Backend Server
```bash
python main.py
```
*Backend runs on `http://localhost:8000`. Access Swagger docs at `http://localhost:8000/docs`.*

### 4. Start the Streamlit Frontend Web App
```bash
streamlit run streamlit_app.py
```
*Frontend runs on `http://localhost:8501`, connecting automatically to the FastAPI backend.*