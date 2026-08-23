"""
api/routers/stats.py
---------------------
GET /stats   — dataset overview counts
"""
from fastapi import APIRouter, Depends
import pandas as pd

from api.dependencies import get_df, get_csv_rows

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("", summary="Dataset overview statistics")
def get_stats(
    df:       pd.DataFrame = Depends(get_df),
    csv_rows: list         = Depends(get_csv_rows),
):
    """Returns high-level dataset statistics shown on the app homepage."""
    total_counties     = len(df)
    high_risk_counties = int(df["high_risk"].sum())
    states_covered     = int(df["state_abbr"].nunique())
    ngo_count          = len(csv_rows)

    # Domain breakdown from CSV
    from collections import Counter
    domain_counts = dict(Counter(r.get("Domain", "") for r in csv_rows))

    return {
        "total_counties":     total_counties,
        "high_risk_counties": high_risk_counties,
        "states_covered":     states_covered,
        "ngo_count":          ngo_count,
        "ngo_by_domain":      domain_counts,
    }
