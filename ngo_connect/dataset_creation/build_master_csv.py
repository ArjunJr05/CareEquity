"""
build_master_csv.py
--------------------
Utility functions for building, geocoding, deduplicating, and saving
careequity_master_sdoh_ngo.csv

Usage:
    python build_master_csv.py          # geocode + dedup + finalize existing CSV
    python build_master_csv.py --check  # just print stats on current CSV
"""

import csv
import json
import os
import sys
import time
import requests

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CSV_PATH  = os.path.join(BASE_DIR, "careequity_master_sdoh_ngo.csv")
GEO_CACHE = os.path.join(BASE_DIR, "sdoh_geo_cache.json")

COLUMNS = [
    "Organization Name",
    "Domain",
    "State",
    "City",
    "Address",
    "Phone",
    "Email",
    "Website",
    "Latitude",
    "Longitude",
    "Source",
]

DOMAINS = [
    "Food",
    "Housing",
    "Transportation",
    "Healthcare",
    "Education-Employment",
]


# ── Geocoding ──────────────────────────────────────────────────────────────

def _load_geo_cache() -> dict:
    if os.path.exists(GEO_CACHE):
        try:
            with open(GEO_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_geo_cache(cache: dict) -> None:
    with open(GEO_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def geocode_address(address: str, city: str, state: str, cache: dict) -> tuple:
    """Return (lat, lon) using Census geocoder or Nominatim fallback."""
    key = f"{address}|{city}|{state}".lower().strip()
    if key in cache:
        return cache[key]

    lat, lon = "", ""

    # --- US Census Geocoder ---
    if address.strip():
        try:
            params = {
                "street":    address,
                "city":      city,
                "state":     state,
                "benchmark": "Public_AR_Current",
                "format":    "json",
            }
            r = requests.get(
                "https://geocoding.geo.census.gov/geocoder/locations/address",
                params=params, timeout=10,
            )
            if r.status_code == 200:
                matches = r.json().get("result", {}).get("addressMatches", [])
                if matches:
                    coords = matches[0].get("coordinates", {})
                    lat = str(round(float(coords.get("y", "")), 6))
                    lon = str(round(float(coords.get("x", "")), 6))
        except Exception:
            pass

    # --- Nominatim fallback ---
    if not lat:
        try:
            q = f"{address}, {city}, {state}, USA" if address.strip() else f"{city}, {state}, USA"
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": q, "format": "json", "limit": 1, "countrycodes": "us"},
                headers={"User-Agent": "CareEquity/1.0"},
                timeout=10,
            )
            if r.status_code == 200:
                results = r.json()
                if results:
                    lat = str(round(float(results[0]["lat"]), 6))
                    lon = str(round(float(results[0]["lon"]), 6))
        except Exception:
            pass
        time.sleep(0.5)  # Nominatim rate limit

    cache[key] = (lat, lon)
    return lat, lon


# ── CSV helpers ────────────────────────────────────────────────────────────

def load_csv() -> list[dict]:
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(rows: list[dict]) -> None:
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved {len(rows)} rows -> {CSV_PATH}")


def append_rows(new_rows: list[dict]) -> list[dict]:
    """Append new_rows to the existing CSV, deduplicate, return all rows."""
    existing = load_csv()

    # Build dedup key: org name + domain + state (case-insensitive)
    seen = {
        (r["Organization Name"].lower().strip(), r["Domain"].lower().strip(), r["State"].lower().strip())
        for r in existing
    }
    added = 0
    for row in new_rows:
        k = (row["Organization Name"].lower().strip(),
             row["Domain"].lower().strip(),
             row["State"].lower().strip())
        if k not in seen:
            # Ensure all columns present
            for col in COLUMNS:
                row.setdefault(col, "")
            existing.append(row)
            seen.add(k)
            added += 1

    print(f"  +{added} new rows added ({len(existing)} total)")
    save_csv(existing)
    return existing


def geocode_all(rows: list[dict]) -> list[dict]:
    """Fill missing lat/lon for every row."""
    cache = _load_geo_cache()
    updated = 0
    for i, row in enumerate(rows):
        if row.get("Latitude") and row.get("Longitude"):
            continue
        lat, lon = geocode_address(
            row.get("Address", ""), row.get("City", ""), row.get("State", ""), cache
        )
        if lat:
            row["Latitude"]  = lat
            row["Longitude"] = lon
            updated += 1
        if (i + 1) % 50 == 0:
            _save_geo_cache(cache)
            print(f"    Geocoded {i+1}/{len(rows)} rows …")
    _save_geo_cache(cache)
    print(f"  Geocoding done — {updated} rows updated")
    return rows


def print_stats(rows: list[dict]) -> None:
    from collections import Counter
    print(f"\n  Total rows : {len(rows)}")
    by_domain = Counter(r["Domain"] for r in rows)
    by_state  = Counter(r["State"]  for r in rows)
    print(f"  Domains    : {dict(by_domain)}")
    print(f"  States     : {len(by_state)} states covered")
    with_email = sum(1 for r in rows if r.get("Email","").strip()
                     and "no public email" not in r.get("Email","").lower())
    with_coords = sum(1 for r in rows if r.get("Latitude","").strip())
    print(f"  With email : {with_email}/{len(rows)}")
    print(f"  With lat/lon: {with_coords}/{len(rows)}")


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rows = load_csv()
    if "--check" in sys.argv:
        print_stats(rows)
        sys.exit(0)

    print("Geocoding all rows with missing coordinates …")
    rows = geocode_all(rows)
    save_csv(rows)
    print_stats(rows)
    print("Done.")
