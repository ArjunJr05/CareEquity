"""
api/dependencies.py
--------------------
Shared application state loaded ONCE at FastAPI startup and
injected into routers via FastAPI dependency injection.

State held here:
    df          — normalised SDoH DataFrame (3,222 counties)
    csv_rows    — raw list[dict] from careequity_master_sdoh_ngo.csv
    geo_cache   — dict keyed by FIPS, persisted to geocode_cache.json
"""
import os
import sys
import json
import logging
from functools import lru_cache
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ── Resolve project root (api/ is one level below project root) ────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SDOH_CSV     = os.path.join(ROOT, "SDOH_MODEL_DATA.csv")
NGO_CSV      = os.path.join(ROOT, "careequity_master_sdoh_ngo.csv")
GEO_CACHE_F  = os.path.join(ROOT, "geocode_cache.json")


# ── Module-level singletons ────────────────────────────────────────────────
_df: pd.DataFrame | None = None
_csv_rows: list[dict]    = []
_geo_cache: dict         = {}


def get_df() -> pd.DataFrame:
    """FastAPI dependency — returns the normalised SDOH DataFrame."""
    return _df


def get_csv_rows() -> list[dict]:
    """FastAPI dependency — returns all NGO CSV rows."""
    return _csv_rows


def get_geo_cache() -> dict:
    """FastAPI dependency — returns the mutable geocode cache dict."""
    return _geo_cache


# ── Startup initialiser (called once from main.py lifespan) ───────────────

def init_state() -> None:
    """Load all heavy data into module-level singletons."""
    global _df, _csv_rows, _geo_cache

    # 1. Normalised SDOH DataFrame
    logger.info("Loading SDOH data from %s …", SDOH_CSV)
    from intervention_engine import load_and_normalise
    _df = load_and_normalise(SDOH_CSV)
    logger.info("Loaded %d counties.", len(_df))

    # 2. NGO CSV rows
    import csv
    if os.path.exists(NGO_CSV):
        with open(NGO_CSV, newline="", encoding="utf-8") as f:
            _csv_rows = list(csv.DictReader(f))
        logger.info("Loaded %d NGO rows from CSV.", len(_csv_rows))
    else:
        logger.warning("NGO CSV not found at %s", NGO_CSV)

    # 3. Geocode cache
    if os.path.exists(GEO_CACHE_F):
        with open(GEO_CACHE_F, encoding="utf-8") as f:
            _geo_cache = json.load(f)
        logger.info("Loaded %d geocode cache entries.", len(_geo_cache))
    else:
        _geo_cache = {}


def save_geo_cache() -> None:
    """Persist updated geocode cache to disk."""
    with open(GEO_CACHE_F, "w", encoding="utf-8") as f:
        json.dump(_geo_cache, f, indent=2)
