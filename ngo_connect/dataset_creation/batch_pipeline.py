"""
batch_pipeline.py
-----------------
Full offline processing pipeline for all ~3,222 US counties.

Workflow per county
-------------------
  1.  Load SDoH data and compute intervention priorities
  2.  Geocode county → (lat, lon)   [cached in geocode_cache.json]
  3.  Find nearby NGOs per intervention (Overpass + Geoapify)
  4.  Append result to pipeline_results.json
  5.  Log success / failure to pipeline_log.json

Resumability
------------
  The pipeline reads pipeline_log.json at startup.
  Counties already marked "done" are skipped.
  Counties marked "failed" and within retry budget are retried.

High-risk prioritisation
-------------------------
  When --prioritise-high-risk flag is given (or PRIORITISE_HIGH_RISK=1 env var),
  high-risk counties (svi_overall > 0.75) are processed first.

Usage
-----
  python batch_pipeline.py [options]

Options
-------
  --csv         PATH       Path to SDOH_MODEL_DATA.csv   (default: auto-detect)
  --results     PATH       Output JSON file               (default: pipeline_results.json)
  --log         PATH       Progress log JSON              (default: pipeline_log.json)
  --batch-size  N          Counties per save checkpoint   (default: 50)
  --max-retries N          Max retry attempts per county  (default: 2)
  --delay       SECONDS    Seconds between counties       (default: 1.5)
  --high-risk-only         Only process high-risk counties
  --prioritise-high-risk   Process high-risk counties first
  --fips        FIPS,...   Comma-separated FIPS to process (overrides all)
  --limit       N          Stop after N counties (useful for testing)
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV   = os.path.join(BASE_DIR, "SDOH_MODEL_DATA.csv")
DEFAULT_RESULTS = os.path.join(BASE_DIR, "pipeline_results.json")
DEFAULT_LOG   = os.path.join(BASE_DIR, "pipeline_log.json")

GEOAPIFY_KEY  = os.getenv("GEOAPIFY_API_KEY", "")


# ---------------------------------------------------------------------------
# Log / results helpers
# ---------------------------------------------------------------------------

def _load_json(path: str, default) -> any:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read %s: %s — starting fresh.", path, exc)
    return default


def _save_json(path: str, data: any) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
    os.replace(tmp, path)


class PipelineLog:
    """
    Manages per-county status in pipeline_log.json.

    Schema per entry
    ----------------
    {
        "fips": "06037",
        "county_name": "Los Angeles County",
        "state": "CA",
        "status": "done" | "failed" | "skipped",
        "attempts": 1,
        "completed_at": "2026-08-21T12:00:00Z",
        "error": null | "error message"
    }
    """

    def __init__(self, path: str):
        self.path = path
        raw: list[dict] = _load_json(path, [])
        self._index: dict[str, dict] = {e["fips"]: e for e in raw}

    def is_done(self, fips: str) -> bool:
        return self._index.get(fips, {}).get("status") == "done"

    def attempts(self, fips: str) -> int:
        return self._index.get(fips, {}).get("attempts", 0)

    def mark_done(self, fips: str, county_name: str, state: str) -> None:
        self._index[fips] = {
            "fips":         fips,
            "county_name":  county_name,
            "state":        state,
            "status":       "done",
            "attempts":     self.attempts(fips) + 1,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "error":        None,
        }
        self._persist()

    def mark_failed(self, fips: str, county_name: str, state: str, error: str) -> None:
        prev = self._index.get(fips, {})
        self._index[fips] = {
            "fips":         fips,
            "county_name":  county_name,
            "state":        state,
            "status":       "failed",
            "attempts":     prev.get("attempts", 0) + 1,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "error":        error,
        }
        self._persist()

    def _persist(self) -> None:
        _save_json(self.path, list(self._index.values()))

    def summary(self) -> dict:
        statuses = [e["status"] for e in self._index.values()]
        return {
            "done":   statuses.count("done"),
            "failed": statuses.count("failed"),
            "total":  len(statuses),
        }


class ResultsStore:
    """
    Append-safe store for processed county results (pipeline_results.json).
    Loads existing results on init so we never lose prior work.
    """

    def __init__(self, path: str):
        self.path = path
        existing: list[dict] = _load_json(path, [])
        self._by_fips: dict[str, dict] = {
            str(r.get("fips", r.get("county_fips", ""))).zfill(5): r
            for r in existing
        }

    def upsert(self, fips: str, data: dict) -> None:
        self._by_fips[fips.zfill(5)] = data

    def save(self) -> None:
        _save_json(self.path, list(self._by_fips.values()))

    def __len__(self) -> int:
        return len(self._by_fips)


# ---------------------------------------------------------------------------
# Core per-county processing
# ---------------------------------------------------------------------------

def process_county(row, df_normalised, geocache: dict, geoapify_key: str) -> dict:
    """
    Run the full pipeline for a single county row.

    Parameters
    ----------
    row : pd.Series
        Row from the normalised DataFrame.
    df_normalised : pd.DataFrame
        Full normalised DataFrame (needed for recommend_interventions).
    geocache : dict
        Shared geocoding cache dict (mutated in-place on cache miss).
    geoapify_key : str
        Geoapify API key.

    Returns
    -------
    dict
        Combined county info + interventions + NGOs dict ready for storage.
    """
    from intervention_engine import recommend_interventions, is_high_risk
    from geocode_counties import geocode_county
    from find_ngos_for_intervention import find_all_intervention_ngos

    fips = str(row["county_fips"]).zfill(5)
    county_name = row.get("county_name", "")
    state_abbr  = row.get("state_abbr", "")

    # 1. Interventions
    interventions = recommend_interventions(row, top_n=3)

    # 2. Geocode
    geo = geocode_county(
        fips=fips,
        county_name=county_name,
        state_abbr=state_abbr,
        cache=geocache,
        save=True,
    )
    lat = geo["lat"] if geo else None
    lon = geo["lon"] if geo else None

    # 3. NGOs (only if we have coordinates)
    ngos: dict[str, list] = {}
    if lat is not None and lon is not None:
        ngos = find_all_intervention_ngos(
            interventions, lat, lon, geoapify_key=geoapify_key
        )

    # 4. Assemble result
    return {
        "fips":                   fips,
        "county_name":            county_name,
        "state_abbr":             state_abbr,
        "population":             _safe_val(row.get("population")),
        "svi_overall":            _safe_val(row.get("svi_overall")),
        "high_risk":              bool(is_high_risk(row)),
        "lat":                    lat,
        "lon":                    lon,
        "food_insecurity":        _safe_val(row.get("food_insecurity")),
        "housing_insecurity":     _safe_val(row.get("housing_insecurity")),
        "transportation_barrier": _safe_val(row.get("transportation_barrier")),
        "lack_health_insurance":  _safe_val(row.get("lack_health_insurance")),
        "poverty_rate":           _safe_val(row.get("poverty_rate")),
        "unemployment_rate":      _safe_val(row.get("unemployment_rate")),
        "median_household_income":_safe_val(row.get("median_household_income")),
        "interventions":          interventions,
        "ngos":                   ngos,
        "processed_at":           datetime.now(timezone.utc).isoformat(),
    }


def _safe_val(val) -> Optional[float]:
    import math
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    csv_path: str        = DEFAULT_CSV,
    results_path: str    = DEFAULT_RESULTS,
    log_path: str        = DEFAULT_LOG,
    batch_size: int      = 50,
    max_retries: int     = 2,
    delay: float         = 1.5,
    high_risk_only: bool = False,
    prioritise_high_risk: bool = False,
    fips_filter: Optional[list[str]] = None,
    limit: Optional[int] = None,
    geoapify_key: str    = GEOAPIFY_KEY,
) -> None:
    from intervention_engine import load_and_normalise
    from geocode_counties import load_cache

    logger.info("=" * 60)
    logger.info("CareEquity Batch Pipeline starting")
    logger.info("CSV:     %s", csv_path)
    logger.info("Results: %s", results_path)
    logger.info("Log:     %s", log_path)
    logger.info("=" * 60)

    # Load data
    df = load_and_normalise(csv_path)
    geocache = load_cache()

    # Apply FIPS filter
    if fips_filter:
        fips_filter = [str(f).zfill(5) for f in fips_filter]
        df = df[df["county_fips"].isin(fips_filter)]
        logger.info("FIPS filter applied: %d counties selected.", len(df))

    # High-risk handling
    if high_risk_only:
        df = df[df["high_risk"]]
        logger.info("High-risk only mode: %d counties selected.", len(df))
    elif prioritise_high_risk:
        df = df.sort_values("high_risk", ascending=False)
        logger.info("High-risk counties prioritised.")

    # Limit
    if limit:
        df = df.head(limit)
        logger.info("Processing limit set to %d.", limit)

    log = PipelineLog(log_path)
    store = ResultsStore(results_path)

    total = len(df)
    processed = 0
    skipped = 0
    errors = 0

    logger.info("Total counties to process: %d", total)
    start_time = time.time()

    for idx, (_, row) in enumerate(df.iterrows(), 1):
        fips        = str(row["county_fips"]).zfill(5)
        county_name = row.get("county_name", fips)
        state_abbr  = row.get("state_abbr", "")

        # Skip already completed
        if log.is_done(fips):
            skipped += 1
            continue

        # Skip if exceeded retry budget
        if log.attempts(fips) >= max_retries and not log.is_done(fips):
            logger.warning("Skipping %s — exceeded %d retries.", fips, max_retries)
            skipped += 1
            continue

        logger.info(
            "[%d/%d]  Processing %s (%s, %s) …",
            idx, total, county_name, state_abbr, fips,
        )

        try:
            result = process_county(row, df, geocache, geoapify_key)
            store.upsert(fips, result)
            log.mark_done(fips, county_name, state_abbr)
            processed += 1

        except Exception as exc:  # noqa: BLE001
            err_msg = str(exc)
            logger.error("  ERROR for %s: %s", fips, err_msg)
            log.mark_failed(fips, county_name, state_abbr, err_msg)
            errors += 1

        # Checkpoint save every batch_size successes
        if processed % batch_size == 0:
            store.save()
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total - processed - skipped) / rate if rate > 0 else 0
            logger.info(
                "  Checkpoint saved.  Done: %d  Errors: %d  "
                "Rate: %.1f/min  ETA: %.0f min",
                processed, errors, rate * 60, eta / 60,
            )

        # Polite delay
        if delay > 0:
            time.sleep(delay)

    # Final save
    store.save()
    elapsed = time.time() - start_time
    summary = log.summary()
    logger.info("=" * 60)
    logger.info("Pipeline complete in %.1f minutes.", elapsed / 60)
    logger.info("  Processed:  %d", processed)
    logger.info("  Skipped:    %d", skipped)
    logger.info("  Errors:     %d", errors)
    logger.info("  Log totals: %s", summary)
    logger.info("  Results at: %s", results_path)
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="CareEquity SDoH batch processing pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--csv",        default=DEFAULT_CSV,     help="Path to SDOH_MODEL_DATA.csv")
    p.add_argument("--results",    default=DEFAULT_RESULTS, help="Output pipeline_results.json path")
    p.add_argument("--log",        default=DEFAULT_LOG,     help="Progress log JSON path")
    p.add_argument("--batch-size", type=int, default=50,    help="Save checkpoint every N counties")
    p.add_argument("--max-retries",type=int, default=2,     help="Max retry attempts per county")
    p.add_argument("--delay",      type=float, default=1.5, help="Seconds to sleep between counties")
    p.add_argument("--high-risk-only",        action="store_true", help="Only process high-risk counties")
    p.add_argument("--prioritise-high-risk",  action="store_true", help="Process high-risk counties first")
    p.add_argument("--fips",       default="",              help="Comma-separated FIPS to process")
    p.add_argument("--limit",      type=int, default=None,  help="Stop after N counties")
    p.add_argument("--geoapify-key", default=GEOAPIFY_KEY, help="Geoapify API key")
    return p.parse_args(argv)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(BASE_DIR, "pipeline_run.log"), encoding="utf-8"),
        ],
    )

    args = _parse_args()
    fips_list = [f.strip() for f in args.fips.split(",") if f.strip()] if args.fips else None

    run_pipeline(
        csv_path             = args.csv,
        results_path         = args.results,
        log_path             = args.log,
        batch_size           = args.batch_size,
        max_retries          = args.max_retries,
        delay                = args.delay,
        high_risk_only       = args.high_risk_only,
        prioritise_high_risk = args.prioritise_high_risk,
        fips_filter          = fips_list,
        limit                = args.limit,
        geoapify_key         = args.geoapify_key,
    )
