"""
api_client.py
-------------
Thin HTTP client that Streamlit uses to talk to the FastAPI backend.

All calls go to http://localhost:8000 by default.
Set the env var API_BASE_URL to override (e.g. for a deployed backend).

Design rules:
  - Every function returns plain Python dicts/lists — no requests objects leak out.
  - On any network or HTTP error, falls back to calling the underlying Python
    module directly so the Streamlit app keeps working even when the FastAPI
    server is not running (development convenience).
  - Timeout: 15 s per request.
"""
import os
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
API_BASE   = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT    = 15   # seconds


# ── Internal helpers ────────────────────────────────────────────────────────

def _get(path: str, params: dict = None) -> dict | list | None:
    """GET request → parsed JSON, or None on error."""
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return None


def _post(path: str, json_body: dict) -> dict | None:
    """POST request → parsed JSON, or None on error."""
    try:
        r = requests.post(f"{API_BASE}{path}", json=json_body, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("API POST %s failed: %s", path, exc)
        return None


def _api_alive() -> bool:
    """Quick health check — returns True if FastAPI is reachable."""
    try:
        r = requests.get(f"{API_BASE}/", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════
# Stats
# ══════════════════════════════════════════════════════════════════════════

def get_stats() -> dict:
    """
    Returns dataset overview stats.
    Fallback: compute directly from local modules.
    """
    data = _get("/stats")
    if data:
        return data
    # ── fallback ──────────────────────────────────────────────────────────
    logger.info("get_stats: using local fallback")
    import os as _os
    from csv_ngo_loader import _load_all_rows
    rows = _load_all_rows()
    from collections import Counter
    return {
        "total_counties":     0,
        "high_risk_counties": 0,
        "states_covered":     0,
        "ngo_count":          len(rows),
        "ngo_by_domain":      dict(Counter(r.get("Domain","") for r in rows)),
    }


# ══════════════════════════════════════════════════════════════════════════
# Counties
# ══════════════════════════════════════════════════════════════════════════

def list_states_and_counties(state: Optional[str] = None) -> dict | list:
    """
    Without state: {'states': [...], 'total_counties': N}
    With state:    [{'county_fips': ..., 'county_name': ...}, ...]
    """
    params = {"state": state} if state else {}
    data   = _get("/counties", params)
    if data is not None:
        return data
    # ── fallback ──────────────────────────────────────────────────────────
    logger.info("list_states_and_counties: using local fallback")
    from intervention_engine import load_and_normalise
    import os
    df = load_and_normalise(os.path.join(os.path.dirname(__file__), "SDOH_MODEL_DATA.csv"))
    if state is None:
        return {"states": sorted(df["state_abbr"].dropna().unique().tolist()),
                "total_counties": len(df)}
    sub = df[df["state_abbr"] == state.upper()][["county_fips","county_name"]]\
            .sort_values("county_name")
    return [{"county_fips": r["county_fips"], "county_name": r["county_name"]}
            for _, r in sub.iterrows()]


def search_counties(q: str) -> list:
    """Fuzzy county name search → [{county_fips, county_name, state_abbr}, ...]"""
    data = _get("/counties/search", {"q": q})
    if data is not None:
        return data
    # ── fallback ──────────────────────────────────────────────────────────
    logger.info("search_counties: using local fallback")
    from intervention_engine import load_and_normalise
    import os
    df = load_and_normalise(os.path.join(os.path.dirname(__file__), "SDOH_MODEL_DATA.csv"))
    m  = df[df["county_name"].str.contains(q, case=False, na=False)]
    return [{"county_fips": r["county_fips"], "county_name": r["county_name"],
             "state_abbr": r["state_abbr"]} for _, r in m.iterrows()]


def get_county_profile(fips: str) -> dict | None:
    """Full SDoH profile dict for one FIPS, or None if not found."""
    data = _get(f"/counties/{fips.zfill(5)}")
    if data is not None:
        return data
    # ── fallback ──────────────────────────────────────────────────────────
    logger.info("get_county_profile: using local fallback for FIPS %s", fips)
    from intervention_engine import load_and_normalise, get_county_interventions
    import os, math
    df = load_and_normalise(os.path.join(os.path.dirname(__file__), "SDOH_MODEL_DATA.csv"))
    try:
        info, _ = get_county_interventions(df, fips, top_n=3)
        return info
    except ValueError:
        return None


def get_county_interventions(fips: str, top_n: int = 3) -> dict | None:
    """
    Returns {'county': {...}, 'interventions': [...]} or None.
    Fallback returns same shape built from local modules.
    """
    data = _get(f"/counties/{fips.zfill(5)}/interventions", {"top_n": top_n})
    if data is not None:
        return data
    # ── fallback ──────────────────────────────────────────────────────────
    logger.info("get_county_interventions: using local fallback for FIPS %s", fips)
    from intervention_engine import load_and_normalise, get_county_interventions as _gci
    import os
    df = load_and_normalise(os.path.join(os.path.dirname(__file__), "SDOH_MODEL_DATA.csv"))
    try:
        info, ivs = _gci(df, fips, top_n=top_n)
        return {"county": info, "interventions": ivs}
    except ValueError:
        return None


# ══════════════════════════════════════════════════════════════════════════
# Geocoding
# ══════════════════════════════════════════════════════════════════════════

def geocode_county(fips: str, county_name: str = "", state_abbr: str = "") -> dict | None:
    """
    Returns {fips, county_name, state_abbr, lat, lon} or None.
    Fallback uses geocode_counties.geocode_county() directly.
    """
    data = _get(f"/counties/{fips.zfill(5)}/geocode")
    if data is not None:
        return data
    # ── fallback ──────────────────────────────────────────────────────────
    logger.info("geocode_county: using local fallback for FIPS %s", fips)
    from geocode_counties import geocode_county as _gc
    return _gc(fips, county_name, state_abbr)


# ══════════════════════════════════════════════════════════════════════════
# NGOs
# ══════════════════════════════════════════════════════════════════════════

def get_ngos(
    intervention: str,
    state: str,
    lat:   Optional[float] = None,
    lon:   Optional[float] = None,
    limit: int = 25,
) -> list:
    """
    Returns list of org dicts for one intervention + state, distance-sorted.
    Fallback: csv_ngo_loader + ngo_directory.
    """
    params = {"intervention": intervention, "state": state, "limit": limit}
    if lat is not None: params["lat"] = lat
    if lon is not None: params["lon"] = lon

    data = _get("/ngos", params)
    if data is not None:
        return data.get("organisations", [])
    # ── fallback ──────────────────────────────────────────────────────────
    logger.info("get_ngos: using local fallback")
    from csv_ngo_loader import get_orgs_for_intervention
    from ngo_directory  import get_fallback_ngos
    orgs = get_orgs_for_intervention(intervention, state, lat, lon, n=limit)
    if intervention == "Utility Assistance" or len(orgs) < 3:
        seen = {o["name"].lower() for o in orgs}
        for org in get_fallback_ngos(intervention, state, n=5):
            if org["name"].lower() not in seen:
                orgs.append(org); seen.add(org["name"].lower())
    return orgs


def get_top3_ngos(
    intervention: str,
    state: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> list:
    """Best 3 orgs via the tier-1/2/3 pipeline."""
    params = {"intervention": intervention, "state": state}
    if lat is not None: params["lat"] = lat
    if lon is not None: params["lon"] = lon

    data = _get("/ngos/top3", params)
    if data is not None:
        return data.get("organisations", [])
    # ── fallback ──────────────────────────────────────────────────────────
    logger.info("get_top3_ngos: using local fallback")
    return get_ngos(intervention, state, lat, lon, limit=25)[:3]


def get_all_ngos(
    fips: str,
    lat:   Optional[float] = None,
    lon:   Optional[float] = None,
    top_n: int = 3,
) -> dict | None:
    """
    One-shot: returns county profile + interventions + NGOs for all interventions.
    Returns the full API response dict, or None on total failure.
    Fallback builds the same shape locally.
    """
    params: dict = {"fips": fips.zfill(5), "top_n": top_n}
    if lat is not None: params["lat"] = lat
    if lon is not None: params["lon"] = lon

    data = _get("/ngos/all", params)
    if data is not None:
        return data
    # ── fallback ──────────────────────────────────────────────────────────
    logger.info("get_all_ngos: using local fallback for FIPS %s", fips)
    from intervention_engine import load_and_normalise, get_county_interventions
    from csv_ngo_loader import get_orgs_for_intervention
    from ngo_directory  import get_fallback_ngos
    import os

    df = load_and_normalise(os.path.join(os.path.dirname(__file__), "SDOH_MODEL_DATA.csv"))
    try:
        info, ivs = get_county_interventions(df, fips, top_n=top_n)
    except ValueError:
        return None

    state_abbr = info["state_abbr"]
    ngo_map: dict[str, list] = {}
    for iv in ivs:
        label = iv["intervention"]
        orgs  = get_orgs_for_intervention(label, state_abbr, lat, lon, n=25)
        if label == "Utility Assistance" or len(orgs) < 3:
            seen = {o["name"].lower() for o in orgs}
            for org in get_fallback_ngos(label, state_abbr, n=5):
                if org["name"].lower() not in seen:
                    orgs.append(org); seen.add(org["name"].lower())
        ngo_map[label] = orgs

    return {
        "fips":          fips.zfill(5),
        "county_name":   info["county_name"],
        "state_abbr":    state_abbr,
        "lat":           lat,
        "lon":           lon,
        "interventions": ivs,
        "ngos":          ngo_map,
    }


# ══════════════════════════════════════════════════════════════════════════
# Email
# ══════════════════════════════════════════════════════════════════════════

def get_email_status() -> dict:
    """SMTP configuration status. Fallback: reads secrets/env directly."""
    data = _get("/email/status")
    if data is not None:
        return data
    logger.info("get_email_status: using local fallback")
    from email_sender import smtp_status
    return smtp_status()


def send_email(
    to_addr:      str,
    subject:      str,
    body:         str,
    sender_name:  str,
    sender_email: str,
    reply_to:     Optional[str] = None,
) -> dict:
    """
    POST /email/send.
    Returns {'success': bool, 'message': str, 'error': str}.
    Fallback: calls email_sender.send_email() directly.
    """
    payload = {
        "to_addr":      to_addr,
        "subject":      subject,
        "body":         body,
        "sender_name":  sender_name,
        "sender_email": sender_email,
        "reply_to":     reply_to or sender_email,
    }
    data = _post("/email/send", payload)
    if data is not None:
        return data
    # ── fallback ──────────────────────────────────────────────────────────
    logger.info("send_email: using local fallback (direct SMTP)")
    from email_sender import send_email as _se
    result = _se(
        to_addr=to_addr, subject=subject, body=body,
        sender_name=sender_name, sender_email=sender_email,
        reply_to=reply_to,
    )
    return {"success": result.success, "message": result.message, "error": result.error}


# ══════════════════════════════════════════════════════════════════════════
# Convenience: is the API server up?
# ══════════════════════════════════════════════════════════════════════════

def api_is_alive() -> bool:
    return _api_alive()
