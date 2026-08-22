"""
csv_ngo_loader.py
-----------------
Loads careequity_master_sdoh_ngo.csv and serves verified org records
as the PRIMARY data source for the CareEquity app, replacing live
Overpass / Geoapify API calls for the guaranteed fallback tier.

Domain mapping  (CSV → app intervention label):
    Food                  → Food Assistance
    Housing               → Housing Support
    Transportation        → Transportation Support
    Healthcare            → Healthcare Access
    Education-Employment  → Employment Assistance
    (no CSV domain)       → Utility Assistance   ← uses ngo_directory fallback

Utility Assistance is not in the CSV taxonomy; those orgs are served
from ngo_directory.py as before.
"""
import csv
import math
import os
from functools import lru_cache
from typing import Optional

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CSV_PATH  = os.path.join(BASE_DIR, "careequity_master_sdoh_ngo.csv")

# ── Domain → intervention label mapping ────────────────────────────────────
DOMAIN_TO_INTERVENTION: dict[str, str] = {
    "food":                 "Food Assistance",
    "housing":              "Housing Support",
    "transportation":       "Transportation Support",
    "healthcare":           "Healthcare Access",
    "education-employment": "Employment Assistance",
}

# Reverse map so we can filter CSV rows by intervention label
INTERVENTION_TO_DOMAIN: dict[str, str] = {v: k for k, v in DOMAIN_TO_INTERVENTION.items()}


# ── Helpers ────────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi   = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _safe_float(val: str) -> Optional[float]:
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _row_to_org(row: dict, clat: Optional[float] = None,
                clon: Optional[float] = None) -> dict:
    """Convert a CSV row dict into the org dict shape used by app.py."""
    lat = _safe_float(row.get("Latitude", ""))
    lon = _safe_float(row.get("Longitude", ""))
    distance_km = None
    if clat is not None and clon is not None and lat is not None and lon is not None:
        distance_km = round(_haversine_km(clat, clon, lat, lon), 2)

    # City + Address combined into a readable address string
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
        "hours":       "",           # CSV does not have hours column
        "source":      "CareEquity CSV",
        "distance_km": distance_km,
        "domain":      (row.get("Domain") or "").strip(),
    }


# ── Core loader ────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_all_rows() -> list[dict]:
    """Load and cache all rows from the CSV (raw dicts, no distance computed)."""
    rows = []
    if not os.path.exists(CSV_PATH):
        return rows
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def get_orgs_for_intervention(
    intervention: str,
    state_abbr: str,
    clat: Optional[float] = None,
    clon:  Optional[float] = None,
    n: int = 25,
) -> list[dict]:
    """
    Return up to *n* orgs from the CSV that match *intervention* for *state_abbr*,
    sorted by straight-line distance from (clat, clon) when coords are given.

    Falls back to national scope (any state) when the state has fewer than 3 matches.

    Parameters
    ----------
    intervention : str
        One of the 6 app intervention labels, e.g. "Food Assistance".
    state_abbr : str
        2-letter US state abbreviation, e.g. "CA".
    clat, clon : float | None
        County centre coordinates for distance sorting.
    n : int
        Maximum number of results to return.

    Returns
    -------
    list[dict]
        Org dicts in the shape expected by app.py, sorted by distance_km
        ascending (None distances go last).
    """
    domain_key = INTERVENTION_TO_DOMAIN.get(intervention, "")
    if not domain_key:
        return []   # Utility Assistance — not in CSV

    all_rows = _load_all_rows()
    state_up = state_abbr.upper()

    # ── State-specific first ───────────────────────────────────────────────
    state_orgs = [
        _row_to_org(r, clat, clon)
        for r in all_rows
        if r.get("Domain", "").lower() == domain_key
        and r.get("State", "").upper() == state_up
        and (r.get("Organization Name") or "").strip()
    ]

    # ── If fewer than 5, pad with national scope (other states) ───────────
    if len(state_orgs) < 5:
        national_orgs = [
            _row_to_org(r, clat, clon)
            for r in all_rows
            if r.get("Domain", "").lower() == domain_key
            and r.get("State", "").upper() != state_up
            and (r.get("Organization Name") or "").strip()
        ]
        # Sort national orgs by distance too (may be far but still useful)
        national_orgs.sort(key=lambda x: x.get("distance_km") or 99999)
        state_orgs = state_orgs + national_orgs[: max(0, n - len(state_orgs))]

    # ── Sort by distance ───────────────────────────────────────────────────
    state_orgs.sort(key=lambda x: x.get("distance_km") or 99999)

    return state_orgs[:n]


def get_all_interventions_from_csv(
    interventions: list[dict],
    state_abbr: str,
    clat: Optional[float],
    clon:  Optional[float],
) -> dict[str, list[dict]]:
    """
    Return CSV orgs for every intervention in *interventions*.

    Parameters
    ----------
    interventions : list[dict]
        Output of ``intervention_engine.recommend_interventions()``.
    state_abbr : str
        2-letter state abbreviation.
    clat, clon : float | None
        County centre coordinates.

    Returns
    -------
    dict[str, list[dict]]
        Mapping of intervention label → list of org dicts.
    """
    result: dict[str, list[dict]] = {}
    for iv in interventions:
        label = iv["intervention"]
        result[label] = get_orgs_for_intervention(
            label, state_abbr, clat, clon, n=25
        )
    return result
