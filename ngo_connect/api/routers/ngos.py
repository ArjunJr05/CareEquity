"""
api/routers/ngos.py
--------------------
GET /ngos                — organisations for one intervention + state, distance-sorted
GET /ngos/top3           — exactly 3 best orgs (CSV → directory tier pipeline)
GET /ngos/all            — all interventions for a county in one call
"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_df, get_csv_rows, get_geo_cache

router = APIRouter(prefix="/ngos", tags=["NGOs"])


# ── Domain → intervention label mapping (mirrors csv_ngo_loader) ──────────
DOMAIN_TO_INTERVENTION = {
    "food":                 "Food Assistance",
    "housing":              "Housing Support",
    "transportation":       "Transportation Support",
    "healthcare":           "Healthcare Access",
    "education-employment": "Employment Assistance",
}
INTERVENTION_TO_DOMAIN = {v: k for k, v in DOMAIN_TO_INTERVENTION.items()}

VALID_INTERVENTIONS = list(DOMAIN_TO_INTERVENTION.values()) + ["Utility Assistance"]


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin(math.radians(lat2 - lat1) / 2) ** 2
         + math.cos(phi1) * math.cos(phi2)
         * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _csv_row_to_org(row: dict, clat=None, clon=None) -> dict:
    lat = _safe_float(row.get("Latitude", ""))
    lon = _safe_float(row.get("Longitude", ""))
    dist = None
    if clat is not None and clon is not None and lat and lon:
        dist = round(_haversine_km(clat, clon, lat, lon), 2)

    city    = (row.get("City") or "").strip()
    address = (row.get("Address") or "").strip()
    full_addr = f"{address}, {city}".strip(", ") if address else city

    return {
        "name":        (row.get("Organization Name") or "").strip(),
        "address":     full_addr,
        "city":        city,
        "state":       (row.get("State") or "").strip(),
        "lat":         lat,
        "lon":         lon,
        "email":       (row.get("Email") or "").strip(),
        "phone":       (row.get("Phone") or "").strip(),
        "website":     (row.get("Website") or "").strip(),
        "hours":       "",
        "source":      "CareEquity CSV",
        "distance_km": dist,
        "domain":      (row.get("Domain") or "").strip(),
    }


def _get_csv_orgs(intervention: str, state_abbr: str,
                  csv_rows: list, clat=None, clon=None, n=25) -> list[dict]:
    """Filter + distance-sort CSV rows for one intervention/state."""
    domain_key = INTERVENTION_TO_DOMAIN.get(intervention, "")
    if not domain_key:
        return []   # Utility Assistance — not in CSV

    state_up = state_abbr.upper()
    state_orgs = [
        _csv_row_to_org(r, clat, clon)
        for r in csv_rows
        if r.get("Domain", "").lower() == domain_key
        and r.get("State", "").upper() == state_up
        and (r.get("Organization Name") or "").strip()
    ]

    if len(state_orgs) < 5:
        national = [
            _csv_row_to_org(r, clat, clon)
            for r in csv_rows
            if r.get("Domain", "").lower() == domain_key
            and r.get("State", "").upper() != state_up
            and (r.get("Organization Name") or "").strip()
        ]
        national.sort(key=lambda x: x.get("distance_km") or 99999)
        state_orgs += national[: max(0, n - len(state_orgs))]

    state_orgs.sort(key=lambda x: x.get("distance_km") or 99999)
    return state_orgs[:n]


def _get_top3(intervention: str, state_abbr: str,
              csv_rows: list, clat=None, clon=None) -> list[dict]:
    """3-tier pipeline: CSV → ngo_directory → (empty)."""
    from ngo_directory import get_fallback_ngos

    orgs = _get_csv_orgs(intervention, state_abbr, csv_rows, clat, clon, n=25)
    with_email = sorted(
        [o for o in orgs if o.get("email","").strip()
         and "no public email" not in o.get("email","").lower()],
        key=lambda x: x.get("distance_km") or 9999,
    )
    result = list(with_email[:3])

    if len(result) < 3:
        seen = {r["name"].lower() for r in result}
        for org in get_fallback_ngos(intervention, state_abbr, n=3):
            if len(result) >= 3:
                break
            n = (org.get("name") or "").strip().lower()
            if n and n not in seen:
                result.append(org)
                seen.add(n)

    return result[:3]


# ── GET /ngos ──────────────────────────────────────────────────────────────

@router.get("", summary="Organisations for one intervention + state")
def get_ngos(
    intervention: str = Query(..., description="e.g. Food Assistance"),
    state:        str = Query(..., description="2-letter state abbreviation"),
    lat:   Optional[float] = Query(None, description="County centre latitude"),
    lon:   Optional[float] = Query(None, description="County centre longitude"),
    limit: int            = Query(25, ge=1, le=100),
    csv_rows: list        = Depends(get_csv_rows),
):
    """Returns up to `limit` organisations sorted by distance (closest first)."""
    if intervention not in VALID_INTERVENTIONS:
        raise HTTPException(
            status_code=422,
            detail=f"intervention must be one of: {VALID_INTERVENTIONS}",
        )
    orgs = _get_csv_orgs(intervention, state.upper(), csv_rows, lat, lon, n=limit)

    # Supplement Utility Assistance / small states from directory
    if intervention == "Utility Assistance" or len(orgs) < 3:
        from ngo_directory import get_fallback_ngos
        seen = {o["name"].lower() for o in orgs}
        for org in get_fallback_ngos(intervention, state.upper(), n=5):
            if org["name"].lower() not in seen:
                orgs.append(org)
                seen.add(org["name"].lower())

    return {"intervention": intervention, "state": state.upper(),
            "count": len(orgs), "organisations": orgs}


# ── GET /ngos/top3 ─────────────────────────────────────────────────────────

@router.get("/top3", summary="Best 3 orgs for one intervention + state")
def get_top3_endpoint(
    intervention: str = Query(..., description="e.g. Housing Support"),
    state:        str = Query(..., description="2-letter state abbreviation"),
    lat:   Optional[float] = Query(None),
    lon:   Optional[float] = Query(None),
    csv_rows: list = Depends(get_csv_rows),
):
    """Runs the 3-tier pipeline (CSV → directory) and returns exactly ≤3 orgs."""
    if intervention not in VALID_INTERVENTIONS:
        raise HTTPException(status_code=422,
                            detail=f"Valid interventions: {VALID_INTERVENTIONS}")
    orgs = _get_top3(intervention, state.upper(), csv_rows, lat, lon)
    return {"intervention": intervention, "state": state.upper(),
            "organisations": orgs}


# ── GET /ngos/all ──────────────────────────────────────────────────────────

@router.get("/all", summary="All interventions for a county in one call")
def get_all_ngos(
    fips:  str = Query(..., description="5-digit county FIPS"),
    lat:   Optional[float] = Query(None, description="County lat (auto-geocoded if omitted)"),
    lon:   Optional[float] = Query(None, description="County lon (auto-geocoded if omitted)"),
    top_n: int             = Query(3,  ge=1, le=6),
    csv_rows: list   = Depends(get_csv_rows),
    df                    = Depends(get_df),
    geo_cache: dict  = Depends(get_geo_cache),
):
    """
    Returns NGOs for all ranked interventions for a county in one round-trip.

    If lat/lon not provided, geocodes the county automatically.
    Returns the county profile, ranked interventions, and top-3 orgs per intervention.
    """
    from api.dependencies import save_geo_cache

    fips = fips.zfill(5)
    matches = df[df["county_fips"] == fips]
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"FIPS '{fips}' not found.")

    row         = matches.iloc[0]
    state_abbr  = str(row.get("state_abbr", ""))
    county_name = str(row.get("county_name", ""))

    # Auto-geocode if coords not supplied
    if lat is None or lon is None:
        from geocode_counties import geocode_county
        geo = geocode_county(fips, county_name, state_abbr,
                             cache=geo_cache, save=True)
        save_geo_cache()
        if geo is None:
            raise HTTPException(status_code=503,
                                detail=f"Geocoding failed for FIPS {fips}.")
        lat, lon = geo["lat"], geo["lon"]

    # Ranked interventions
    from intervention_engine import recommend_interventions
    interventions = recommend_interventions(row, top_n=top_n)

    # NGOs per intervention
    ngo_map: dict[str, list] = {}
    for iv in interventions:
        label = iv["intervention"]
        orgs  = _get_csv_orgs(label, state_abbr, csv_rows, lat, lon, n=25)

        if label == "Utility Assistance" or len(orgs) < 3:
            from ngo_directory import get_fallback_ngos
            seen = {o["name"].lower() for o in orgs}
            for org in get_fallback_ngos(label, state_abbr, n=5):
                if org["name"].lower() not in seen:
                    orgs.append(org)
                    seen.add(org["name"].lower())

        ngo_map[label] = orgs

    return {
        "fips":          fips,
        "county_name":   county_name,
        "state_abbr":    state_abbr,
        "lat":           lat,
        "lon":           lon,
        "interventions": interventions,
        "ngos":          ngo_map,
    }
