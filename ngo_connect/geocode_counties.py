"""
geocode_counties.py
-------------------
Resolves county centre coordinates using the US Census Geocoder API.
Results are cached locally in a JSON file keyed by 5-digit FIPS code to
prevent redundant API calls.

Census Geocoder endpoint used:
    https://geocoding.geo.census.gov/geocoder/locations/address
    (and the benchmark/vintage-free geography endpoint for counties)

Because the Census Geocoder works best with addresses, this module uses the
Census Geography API — specifically the "geographies/list/counties" endpoint —
which returns a centroid for any FIPS code without needing a street address.

Fallback: if the Census API is unavailable, the module warns and returns None.
"""

import json
import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_FILE: str = os.path.join(os.path.dirname(__file__), "geocode_cache.json")
CENSUS_API_TIMEOUT: int = 10  # seconds per request
RETRY_ATTEMPTS: int = 3
RETRY_BACKOFF: float = 2.0  # seconds between retries

# US Census TIGERweb county centroid lookup.
# Layer 82 = Counties; query by GEOID (full 5-digit FIPS).
# Docs: https://tigerweb.geo.census.gov/tigerwebmain/TIGERweb_main.html
TIGER_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/tigerWMS_Current/MapServer/82/query"
)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Cache file unreadable (%s), starting fresh.", exc)
    return {}


def _save_cache(cache: dict) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, indent=2)
    except OSError as exc:
        logger.error("Could not write cache: %s", exc)


# ---------------------------------------------------------------------------
# Geocoding helpers
# ---------------------------------------------------------------------------

def _query_census_tiger(fips: str) -> Optional[tuple[float, float]]:
    """
    Query the Census TIGERweb REST API (layer 82 — Counties) for a county
    centroid using the full 5-digit GEOID.

    Parameters
    ----------
    fips : str
        5-digit county FIPS (e.g. "06037").

    Returns
    -------
    (latitude, longitude) or None
    """
    fips = str(fips).zfill(5)

    params = {
        "where": f"GEOID='{fips}'",
        "outFields": "GEOID,NAME,CENTLAT,CENTLON,INTPTLAT,INTPTLON",
        "returnGeometry": "false",
        "f": "json",
    }

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = requests.get(
                TIGER_URL, params=params, timeout=CENSUS_API_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            if features:
                attrs = features[0].get("attributes", {})
                # Prefer CENTLAT/CENTLON; fall back to INTPTLAT/INTPTLON
                lat = attrs.get("CENTLAT") or attrs.get("INTPTLAT")
                lon = attrs.get("CENTLON") or attrs.get("INTPTLON")
                if lat is not None and lon is not None:
                    return float(lat), float(lon)
            logger.warning("No feature returned for FIPS %s", fips)
            return None
        except requests.RequestException as exc:
            logger.warning(
                "Census API attempt %d/%d failed for FIPS %s: %s",
                attempt, RETRY_ATTEMPTS, fips, exc,
            )
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_BACKOFF * attempt)

    return None


def _query_census_geocoder(county_name: str, state_abbr: str) -> Optional[tuple[float, float]]:
    """
    Fallback: use the Census Geocoder address search with county + state.
    Returns (lat, lon) or None.
    """
    url = "https://geocoding.geo.census.gov/geocoder/locations/address"
    params = {
        "street": "",
        "city": county_name.replace(" County", "").replace(" Parish", ""),
        "state": state_abbr,
        "benchmark": "Public_AR_Current",
        "format": "json",
    }
    try:
        resp = requests.get(url, params=params, timeout=CENSUS_API_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        matches = data.get("result", {}).get("addressMatches", [])
        if matches:
            coords = matches[0].get("coordinates", {})
            lat = coords.get("y")
            lon = coords.get("x")
            if lat and lon:
                return float(lat), float(lon)
    except requests.RequestException as exc:
        logger.debug("Census Geocoder fallback failed: %s", exc)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def geocode_county(
    fips: str,
    county_name: str = "",
    state_abbr: str = "",
    cache: Optional[dict] = None,
    save: bool = True,
) -> Optional[dict]:
    """
    Return geocoded coordinates for a county, using the local cache first.

    Parameters
    ----------
    fips : str
        5-digit county FIPS code.
    county_name : str
        Human-readable county name (used as fallback).
    state_abbr : str
        Two-letter state abbreviation (used as fallback).
    cache : dict, optional
        Pre-loaded cache dict.  If None, the cache file is loaded each call.
    save : bool
        Whether to persist a new result to the cache file.

    Returns
    -------
    dict or None
        ``{"fips": ..., "county_name": ..., "lat": ..., "lon": ...}``
        or None if geocoding fails.
    """
    fips = str(fips).zfill(5)

    # --- cache hit ---
    if cache is None:
        cache = _load_cache()
    if fips in cache:
        return cache[fips]

    # --- primary: TIGERweb centroid ---
    result = _query_census_tiger(fips)

    # --- fallback: address geocoder ---
    if result is None and county_name and state_abbr:
        result = _query_census_geocoder(county_name, state_abbr)

    if result is None:
        logger.error("Geocoding failed for FIPS %s (%s, %s)", fips, county_name, state_abbr)
        return None

    lat, lon = result
    entry = {
        "fips":        fips,
        "county_name": county_name,
        "state_abbr":  state_abbr,
        "lat":         lat,
        "lon":         lon,
    }
    cache[fips] = entry
    if save:
        _save_cache(cache)
    logger.info("Geocoded %s -> (%.4f, %.4f)", fips, lat, lon)
    return entry


def geocode_all_counties(
    df,
    delay: float = 0.25,
) -> dict:
    """
    Geocode every county in *df* that is not already in the local cache.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: county_fips, county_name, state_abbr.
    delay : float
        Seconds to sleep between API calls to be polite to the Census API.

    Returns
    -------
    dict
        Updated cache keyed by FIPS.
    """
    cache = _load_cache()
    missing = df[~df["county_fips"].astype(str).str.zfill(5).isin(cache)]
    logger.info(
        "%d counties already cached; %d to geocode.",
        len(cache), len(missing),
    )
    for _, row in missing.iterrows():
        fips = str(row["county_fips"]).zfill(5)
        geocode_county(
            fips=fips,
            county_name=str(row.get("county_name", "")),
            state_abbr=str(row.get("state_abbr", "")),
            cache=cache,
            save=False,  # bulk-save below for efficiency
        )
        time.sleep(delay)

    _save_cache(cache)
    logger.info("Geocoding complete.  Cache now holds %d entries.", len(cache))
    return cache


def load_cache() -> dict:
    """Return the current geocoding cache (convenience re-export)."""
    return _load_cache()


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    fips_arg = sys.argv[1] if len(sys.argv) > 1 else "06037"
    name_arg = sys.argv[2] if len(sys.argv) > 2 else "Los Angeles County"
    state_arg = sys.argv[3] if len(sys.argv) > 3 else "CA"

    result = geocode_county(fips_arg, name_arg, state_arg)
    if result:
        print(
            f"FIPS {result['fips']}: {result['county_name']}, {result['state_abbr']} "
            f"→ ({result['lat']:.4f}, {result['lon']:.4f})"
        )
    else:
        print(f"Geocoding failed for FIPS {fips_arg}")
