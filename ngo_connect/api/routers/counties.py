"""
api/routers/counties.py
------------------------
GET /counties                         — list all states + total count
GET /counties?state={abbr}            — counties for a state
GET /counties/search?q={name}         — fuzzy county name search
GET /counties/{fips}                  — full SDoH profile for one county
GET /counties/{fips}/interventions    — ranked interventions for one county
"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import pandas as pd

from api.dependencies import get_df

router = APIRouter(prefix="/counties", tags=["Counties"])


# ── helpers ────────────────────────────────────────────────────────────────

def _safe(val) -> Optional[float]:
    """Convert pandas/numpy scalar to plain Python float or None."""
    try:
        if val is None:
            return None
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _county_row_to_profile(row: pd.Series) -> dict:
    return {
        "county_fips":               str(row["county_fips"]),
        "county_name":               str(row.get("county_name", "")),
        "state_abbr":                str(row.get("state_abbr", "")),
        "population":                _safe(row.get("population")),
        "svi_overall":               _safe(row.get("svi_overall")),
        "high_risk":                 bool(row.get("high_risk", False)),
        "food_insecurity":           _safe(row.get("food_insecurity")),
        "housing_insecurity":        _safe(row.get("housing_insecurity")),
        "transportation_barrier":    _safe(row.get("transportation_barrier")),
        "lack_health_insurance":     _safe(row.get("lack_health_insurance")),
        "poverty_rate":              _safe(row.get("poverty_rate")),
        "unemployment_rate":         _safe(row.get("unemployment_rate")),
        "svi_housing_transportation":_safe(row.get("svi_housing_transportation")),
        "median_household_income":   _safe(row.get("median_household_income")),
    }


# ── GET /counties ──────────────────────────────────────────────────────────

@router.get("", summary="List states or counties within a state")
def list_counties(
    state: Optional[str] = Query(None, description="2-letter state abbreviation"),
    df: pd.DataFrame = Depends(get_df),
):
    """
    Without `state`: returns list of all unique states + total county count.
    With `state=XX`: returns all counties for that state as [{county_fips, county_name}].
    """
    if state is None:
        states = sorted(df["state_abbr"].dropna().unique().tolist())
        return {
            "total_counties": len(df),
            "states":         states,
        }

    state = state.upper()
    subset = df[df["state_abbr"] == state][["county_fips", "county_name"]]\
               .sort_values("county_name")
    if subset.empty:
        raise HTTPException(status_code=404, detail=f"State '{state}' not found.")
    return [
        {"county_fips": r["county_fips"], "county_name": r["county_name"]}
        for _, r in subset.iterrows()
    ]


# ── GET /counties/search ───────────────────────────────────────────────────

@router.get("/search", summary="Search counties by name")
def search_counties(
    q: str = Query(..., min_length=1, description="Partial county name"),
    df: pd.DataFrame = Depends(get_df),
):
    """Case-insensitive substring search across all county names."""
    matches = df[df["county_name"].str.contains(q.strip(), case=False, na=False)]
    if matches.empty:
        return []
    return [
        {
            "county_fips": r["county_fips"],
            "county_name": r["county_name"],
            "state_abbr":  r["state_abbr"],
        }
        for _, r in matches.iterrows()
    ]


# ── GET /counties/{fips} ───────────────────────────────────────────────────

@router.get("/{fips}", summary="Full SDoH profile for one county")
def get_county(
    fips: str,
    df: pd.DataFrame = Depends(get_df),
):
    """Returns all 14 SDoH metrics + high_risk flag for the given FIPS."""
    fips = fips.zfill(5)
    matches = df[df["county_fips"] == fips]
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"FIPS '{fips}' not found.")
    return _county_row_to_profile(matches.iloc[0])


# ── GET /counties/{fips}/interventions ────────────────────────────────────

@router.get("/{fips}/interventions", summary="Ranked interventions for a county")
def get_interventions(
    fips: str,
    top_n: int = Query(3, ge=1, le=6, description="Number of interventions to return"),
    df: pd.DataFrame = Depends(get_df),
):
    """
    Returns up to `top_n` ranked interventions for the county, severity-scored
    and priority-labelled, alongside the county profile.
    """
    fips = fips.zfill(5)
    matches = df[df["county_fips"] == fips]
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"FIPS '{fips}' not found.")

    from intervention_engine import recommend_interventions
    row           = matches.iloc[0]
    interventions = recommend_interventions(row, top_n=top_n)

    return {
        "county": _county_row_to_profile(row),
        "interventions": interventions,
    }
