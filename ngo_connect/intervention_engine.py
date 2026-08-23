"""
intervention_engine.py
----------------------
Computes and ranks SDoH-driven intervention priorities for each county.

Normalization:
    Each raw column is min-max normalized across all counties to a 0-1 scale
    so every intervention score is directly comparable.

    IMPORTANT — all source columns must be on the same kind of scale
    (percentage-based) so normalization is apples-to-apples.  SVI sub-scores
    (which are already 0-1) are intentionally NOT used as primary drivers
    because they compress poorly against percentage columns and inflate
    Utility Assistance rankings artificially.

Intervention categories:
    food_insecurity                       -> Food Assistance
    housing_insecurity                    -> Housing Support
    transportation_barrier + no_vehicle_rate -> Transportation Support
    lack_health_insurance                 -> Healthcare Access
    poverty_rate + unemployment_rate      -> Employment Assistance
    poverty_rate + no_vehicle_rate        -> Utility Assistance
      (no_vehicle_rate is the best percentage proxy for utility/cost burden)

High-risk flag:
    svi_overall > HIGH_RISK_THRESHOLD  (default 0.75)
"""

import pandas as pd
import numpy as np
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HIGH_RISK_THRESHOLD: float = 0.75

# Maps (intervention label) -> list of raw CSV columns that feed it.
# ALL columns here must be percentage-based so min-max normalization
# produces comparable 0-1 scores across all six interventions.
INTERVENTION_COLUMNS: dict[str, list[str]] = {
    "Food Assistance":        ["food_insecurity"],
    "Housing Support":        ["housing_insecurity"],
    "Transportation Support": ["transportation_barrier", "no_vehicle_rate"],
    "Healthcare Access":      ["lack_health_insurance"],
    "Employment Assistance":  ["poverty_rate", "unemployment_rate"],
    "Utility Assistance":     ["poverty_rate", "no_vehicle_rate"],
}

# Colour-coded priority labels used by the UI
PRIORITY_LABELS = [
    (0.75, "🔴 High Priority"),
    (0.50, "🟠 Medium Priority"),
    (0.0,  "🟡 Low Priority"),
]


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _min_max_normalise(series: pd.Series) -> pd.Series:
    """Normalise a numeric Series to [0, 1]."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - lo) / (hi - lo)


def build_normalised_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy of *df* with an extra ``_norm`` column for every raw
    column referenced in INTERVENTION_COLUMNS.

    Parameters
    ----------
    df : pd.DataFrame
        Raw county data loaded from SDOH_MODEL_DATA.csv.

    Returns
    -------
    pd.DataFrame
        Original columns preserved plus ``<col>_norm`` columns.
    """
    df = df.copy()
    raw_cols = {col for cols in INTERVENTION_COLUMNS.values() for col in cols}
    for col in raw_cols:
        if col in df.columns:
            df[f"{col}_norm"] = _min_max_normalise(df[col].fillna(0))
        else:
            df[f"{col}_norm"] = 0.0
    return df


def _priority_label(score: float) -> str:
    for threshold, label in PRIORITY_LABELS:
        if score >= threshold:
            return label
    return PRIORITY_LABELS[-1][1]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def recommend_interventions(
    row: pd.Series,
    normalised_df: Optional[pd.DataFrame] = None,
    top_n: int = 3,
) -> list[dict]:
    """
    Rank intervention needs for a single county row.

    Parameters
    ----------
    row : pd.Series
        A single row from a normalised DataFrame (one with ``_norm`` cols).
        If you pass a raw row without ``_norm`` columns supply *normalised_df*
        so the function can look up the pre-computed normalised values.
    normalised_df : pd.DataFrame, optional
        Full normalised dataset.  Required when *row* comes from the raw CSV.
    top_n : int
        Number of top interventions to return (default 3).

    Returns
    -------
    list[dict]
        Sorted list (highest severity first) of dicts, each containing:
        - intervention  : str
        - severity      : float  (0-1)
        - priority_label: str
    """
    # If normalised_df supplied, fetch the normalised version of this row
    if normalised_df is not None and "food_insecurity_norm" not in row.index:
        fips = row["county_fips"]
        try:
            row = normalised_df.loc[
                normalised_df["county_fips"] == fips
            ].iloc[0]
        except IndexError:
            pass  # fall through with raw row

    scores: list[dict] = []
    for intervention, cols in INTERVENTION_COLUMNS.items():
        norm_cols = [f"{c}_norm" for c in cols]
        available = [c for c in norm_cols if c in row.index]
        if not available:
            continue
        severity = float(np.mean([row[c] for c in available]))
        scores.append(
            {
                "intervention":   intervention,
                "severity":       round(severity, 4),
                "priority_label": _priority_label(severity),
            }
        )

    scores.sort(key=lambda x: x["severity"], reverse=True)
    return scores[:top_n]


def is_high_risk(row: pd.Series, threshold: float = HIGH_RISK_THRESHOLD) -> bool:
    """Return True when the county's overall SVI exceeds *threshold*."""
    val = row.get("svi_overall", 0.0)
    if pd.isna(val):
        return False
    return float(val) > threshold


def load_and_normalise(csv_path: str) -> pd.DataFrame:
    """
    Load SDOH_MODEL_DATA.csv, normalise relevant columns, add helper columns.

    Returns
    -------
    pd.DataFrame
        Full dataset with ``_norm`` columns and a boolean ``high_risk`` column.
    """
    df = pd.read_csv(csv_path, dtype={"county_fips": str})
    # Zero-pad FIPS to 5 digits
    df["county_fips"] = df["county_fips"].str.zfill(5)
    df = build_normalised_df(df)
    df["high_risk"] = df.apply(is_high_risk, axis=1)
    return df


def get_county_interventions(
    df: pd.DataFrame,
    fips: str,
    top_n: int = 3,
) -> tuple[dict, list[dict]]:
    """
    Convenience function: look up a county by FIPS and return its profile.

    Parameters
    ----------
    df : pd.DataFrame
        Result of ``load_and_normalise()``.
    fips : str
        5-digit county FIPS code.
    top_n : int
        Maximum interventions to return.

    Returns
    -------
    (county_info, interventions)
        county_info : dict  – key county metadata
        interventions : list[dict] – ranked intervention list
    """
    fips = str(fips).zfill(5)
    matches = df[df["county_fips"] == fips]
    if matches.empty:
        raise ValueError(f"FIPS code {fips!r} not found in dataset.")

    row = matches.iloc[0]
    county_info = {
        "county_fips":          row["county_fips"],
        "county_name":          row["county_name"],
        "state_abbr":           row["state_abbr"],
        "population":           row.get("population"),
        "svi_overall":          row.get("svi_overall"),
        "high_risk":            bool(row.get("high_risk", False)),
        "food_insecurity":      row.get("food_insecurity"),
        "housing_insecurity":   row.get("housing_insecurity"),
        "transportation_barrier": row.get("transportation_barrier"),
        "lack_health_insurance":row.get("lack_health_insurance"),
        "poverty_rate":         row.get("poverty_rate"),
        "unemployment_rate":    row.get("unemployment_rate"),
        "svi_housing_transportation": row.get("svi_housing_transportation"),
        "median_household_income": row.get("median_household_income"),
    }
    interventions = recommend_interventions(row, top_n=top_n)
    return county_info, interventions


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys, json, os

    csv = os.path.join(os.path.dirname(__file__), "SDOH_MODEL_DATA.csv")
    fips_arg = sys.argv[1] if len(sys.argv) > 1 else "06037"

    df = load_and_normalise(csv)
    print(f"Loaded {len(df)} counties.  High-risk: {df['high_risk'].sum()}")

    info, ivs = get_county_interventions(df, fips_arg)
    print(f"\nCounty: {info['county_name']} ({info['state_abbr']})")
    print(f"SVI Overall: {info['svi_overall']}  |  High Risk: {info['high_risk']}")
    print("\nTop Interventions:")
    for rank, iv in enumerate(ivs, 1):
        print(f"  {rank}. {iv['intervention']:<25} Severity: {iv['severity']}  {iv['priority_label']}")
