"""
api/main.py
-----------
CareEquity FastAPI backend.

Run:
    uvicorn api.main:app --reload --port 8000

Docs:
    http://localhost:8000/docs     (Swagger UI)
    http://localhost:8000/redoc    (ReDoc)

Endpoints
---------
GET  /                                  health check
GET  /stats                             dataset overview
GET  /counties                          list states / counties
GET  /counties/search?q=...             county name search
GET  /counties/{fips}                   county SDoH profile
GET  /counties/{fips}/interventions     ranked interventions
GET  /counties/{fips}/geocode           county centre lat/lon
GET  /ngos?intervention=...&state=...   orgs for one intervention
GET  /ngos/top3?intervention=...        best 3 orgs (tier pipeline)
GET  /ngos/all?fips=...                 all interventions + orgs
GET  /email/status                      SMTP config check
POST /email/send                        deliver real email
"""
import logging
import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Ensure project root is on sys.path ────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan: load heavy state once at startup ─────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CareEquity API starting up …")
    from api.dependencies import init_state
    init_state()
    logger.info("Startup complete — API ready.")
    yield
    logger.info("CareEquity API shutting down.")


# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "CareEquity SDoH API",
    description = (
        "Backend API for the CareEquity SDoH Intervention Finder.\n\n"
        "Provides county SDoH profiles, ranked interventions, verified NGO "
        "matching, geocoding, and direct email delivery to organisations."
    ),
    version     = "1.0.0",
    lifespan    = lifespan,
)

# Allow the Streamlit frontend (localhost:8501) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:8501",
                         "http://127.0.0.1:8501",
                         "*"],          # restrict in production
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Routers ────────────────────────────────────────────────────────────────

from api.routers import counties, geocode, ngos, email, stats

app.include_router(counties.router)
app.include_router(geocode.router)
app.include_router(ngos.router)
app.include_router(email.router)
app.include_router(stats.router)


# ── Health check ───────────────────────────────────────────────────────────

@app.get("/", tags=["Health"], summary="API health check")
def health():
    return {
        "status":  "ok",
        "service": "CareEquity SDoH API",
        "version": "1.0.0",
        "docs":    "/docs",
    }
