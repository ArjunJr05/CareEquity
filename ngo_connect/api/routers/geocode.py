"""
api/routers/geocode.py
-----------------------
GET /counties/{fips}/geocode   — county centre lat/lon
"""
from fastapi import APIRouter, Depends, HTTPException
import pandas as pd

from api.dependencies import get_df, get_geo_cache, save_geo_cache

router = APIRouter(prefix="/counties", tags=["Geocode"])


@router.get("/{fips}/geocode", summary="Get lat/lon for a county centre")
def geocode_county_endpoint(
    fips: str,
    df: pd.DataFrame = Depends(get_df),
    geo_cache: dict   = Depends(get_geo_cache),
):
    """
    Returns the geographic centre of the county.

    Hits the US Census TIGERweb API on the first call; subsequent calls
    for the same FIPS are served from the in-process cache (persisted
    to geocode_cache.json).
    """
    fips = fips.zfill(5)

    # Validate FIPS exists in our dataset
    matches = df[df["county_fips"] == fips]
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"FIPS '{fips}' not found.")

    row         = matches.iloc[0]
    county_name = str(row.get("county_name", ""))
    state_abbr  = str(row.get("state_abbr", ""))

    # Delegate to geocode_counties.geocode_county() — uses shared cache dict
    from geocode_counties import geocode_county
    result = geocode_county(
        fips        = fips,
        county_name = county_name,
        state_abbr  = state_abbr,
        cache       = geo_cache,
        save        = True,
    )
    if result is None:
        raise HTTPException(
            status_code=503,
            detail=f"Geocoding failed for FIPS {fips}. "
                   "Census API may be unavailable.",
        )

    # Persist any new entry back to disk
    save_geo_cache()

    return {
        "fips":        result["fips"],
        "county_name": result["county_name"],
        "state_abbr":  result["state_abbr"],
        "lat":         result["lat"],
        "lon":         result["lon"],
    }
