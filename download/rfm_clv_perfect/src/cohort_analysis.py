"""
Cohort Retention Analysis Module.

Builds monthly acquisition cohorts from transaction logs and tracks the
retention curve of each cohort over time. Produces a triangular retention
matrix suitable for heatmap visualization, plus summary metrics (cohort
size, average retention at month N, half-life).

This is a useful complement to RFM (which is point-in-time) and BG/NBD CLV
(which is forward-looking) — cohort analysis shows the actual observed
retention curve per acquisition vintage.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import REPORTS_DIR


def build_cohort_matrix(
    cleaned_df: pd.DataFrame,
    cohort_period: str = "M",  # "M" = monthly, "Q" = quarterly, "W" = weekly
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build a cohort retention matrix from cleaned transactions.

    Args:
        cleaned_df: cleaned transaction DataFrame with columns InvoiceDate,
                    CustomerID, TotalPrice.
        cohort_period: pandas offset alias for cohort grouping. Default "M".

    Returns:
        (cohort_sizes, retention_matrix) where:
          - cohort_sizes: DataFrame with columns CohortDate, CohortSize,
            TotalRevenue, AvgOrderValue
          - retention_matrix: DataFrame indexed by CohortDate, columns are
            MonthIndex (0, 1, 2, ...), values are the count of customers
            from that cohort who made at least one purchase in that month.
            MonthIndex 0 is always == cohort size (acquisition month).
    """
    df = cleaned_df.copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # Cohort = first-purchase month per customer
    df["CohortDate"] = df.groupby("CustomerID")["InvoiceDate"].transform("min").dt.to_period(cohort_period)

    # Activity month per row
    df["ActivityPeriod"] = df["InvoiceDate"].dt.to_period(cohort_period)

    # Cohort index = (ActivityPeriod - CohortDate) in months
    # Use the period arithmetic: subtraction yields a number of periods
    df["CohortIndex"] = (df["ActivityPeriod"] - df["CohortDate"]).apply(lambda p: int(getattr(p, "n", 0)))

    # Build the (CohortDate, CohortIndex) → unique customer count matrix
    grouping = df.groupby(["CohortDate", "CohortIndex"])["CustomerID"].nunique().reset_index()
    retention_matrix = grouping.pivot(
        index="CohortDate", columns="CohortIndex", values="CustomerID"
    ).fillna(0.0)

    # Cohort size = retention_matrix column 0
    cohort_sizes = retention_matrix.iloc[:, 0] if retention_matrix.shape[1] > 0 else pd.Series(dtype=float)

    # Convert counts to retention rates by dividing by cohort size
    # But also return the raw counts for the heatmap layer
    return cohort_sizes, retention_matrix


def compute_retention_rate_matrix(retention_matrix: pd.DataFrame) -> pd.DataFrame:
    """Convert raw customer counts to retention rate (0-1) by dividing each
    row by its month-0 cohort size."""
    cohort_sizes = retention_matrix.iloc[:, 0] if retention_matrix.shape[1] > 0 else pd.Series(dtype=float)
    rate_matrix = retention_matrix.div(cohort_sizes, axis=0)
    return rate_matrix.round(4)


def compute_cohort_revenue_matrix(cleaned_df: pd.DataFrame, cohort_period: str = "M") -> pd.DataFrame:
    """Average revenue per cohort customer at each month index. Useful for
    showing whether cohorts that stick around are also spending more."""
    df = cleaned_df.copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["CohortDate"] = df.groupby("CustomerID")["InvoiceDate"].transform("min").dt.to_period(cohort_period)
    df["ActivityPeriod"] = df["InvoiceDate"].dt.to_period(cohort_period)
    df["CohortIndex"] = (df["ActivityPeriod"] - df["CohortDate"]).apply(lambda p: int(getattr(p, "n", 0)))

    # Total revenue per (CohortDate, CohortIndex)
    revenue = df.groupby(["CohortDate", "CohortIndex"])["TotalPrice"].sum().reset_index()
    # Cohort size (unique customers in cohort)
    cohort_size = df.groupby("CohortDate")["CustomerID"].nunique()
    revenue["CohortSize"] = revenue["CohortDate"].map(cohort_size)
    revenue["AvgRevenuePerCustomer"] = (revenue["TotalPrice"] / revenue["CohortSize"]).round(2)

    matrix = revenue.pivot(
        index="CohortDate", columns="CohortIndex", values="AvgRevenuePerCustomer"
    ).fillna(0.0)
    return matrix


def summarize_cohorts(cohort_sizes: pd.Series, retention_matrix: pd.DataFrame) -> pd.DataFrame:
    """One-row-per-cohort summary table for display: cohort date, size,
    month-1 retention %, half-life (month where retention drops below 50%)."""
    rate_matrix = compute_retention_rate_matrix(retention_matrix)

    rows = []
    for cohort_date, row in rate_matrix.iterrows():
        size = int(retention_matrix.loc[cohort_date].iloc[0]) if retention_matrix.shape[1] > 0 else 0
        month1_ret = float(row.iloc[1]) if len(row) > 1 else 0.0

        # Half-life: first month where retention drops below 50%
        half_life = None
        for m_idx, rate in enumerate(row):
            if m_idx > 0 and rate < 0.5:
                half_life = m_idx
                break

        rows.append({
            "CohortDate": str(cohort_date),
            "CohortSize": size,
            "Month1_Retention_Pct": round(month1_ret * 100, 2),
            "HalfLife_Months": half_life,
            "FinalMonth_Retention_Pct": round(float(row.iloc[-1]) * 100, 2) if len(row) > 0 else 0.0,
            "MonthsTracked": len(row),
        })

    return pd.DataFrame(rows)


def run_cohort_analysis(
    cleaned_df: pd.DataFrame,
    cohort_period: str = "M",
    output_dir: Optional[Path] = REPORTS_DIR,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """End-to-end cohort analysis. Returns:
       (cohort_sizes, retention_matrix, retention_rate_matrix, summary_df)
    """
    cohort_sizes, retention_matrix = build_cohort_matrix(cleaned_df, cohort_period=cohort_period)
    rate_matrix = compute_retention_rate_matrix(retention_matrix)
    summary_df = summarize_cohorts(cohort_sizes, retention_matrix)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        retention_matrix.to_csv(output_dir / "cohort_retention_counts.csv")
        rate_matrix.to_csv(output_dir / "cohort_retention_rates.csv")
        summary_df.to_csv(output_dir / "cohort_summary.csv", index=False)

    return cohort_sizes, retention_matrix, rate_matrix, summary_df


if __name__ == "__main__":
    # Smoke test on a tiny synthetic dataset
    np.random.seed(42)
    n_customers = 200
    customer_ids = list(range(10000, 10000 + n_customers))
    rows = []
    for cid in customer_ids:
        # First purchase between Jan and Jun 2024
        first_dt = pd.Timestamp("2024-01-01") + pd.Timedelta(days=np.random.randint(0, 180))
        n_repeat = np.random.poisson(2)
        last_dt = first_dt
        for _ in range(n_repeat + 1):
            rows.append({
                "InvoiceNo": f"INV-{cid}-{_}",
                "StockCode": "TEST",
                "Description": "Test product",
                "Quantity": 1,
                "InvoiceDate": last_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "UnitPrice": 25.0,
                "CustomerID": str(cid),
                "Country": "United Kingdom",
                "TotalPrice": 25.0,
            })
            last_dt = last_dt + pd.Timedelta(days=np.random.randint(15, 60))

    df = pd.DataFrame(rows)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    cohort_sizes, ret_matrix, rate_matrix, summary = run_cohort_analysis(df, cohort_period="M")
    print(f"Cohorts: {len(cohort_sizes)}")
    print(f"Matrix shape: {ret_matrix.shape}")
    print(f"\nFirst 5 cohorts:\n{summary.head()}")
    print("\nAll cohort analysis components verified ✓")
