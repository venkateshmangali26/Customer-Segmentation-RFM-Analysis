"""
RFM (Recency, Frequency, Monetary) Analysis Module.
Computes customer-level behavioral metrics, calculates quantile-based RFM scores,
and assigns industry-standard customer behavioral segments.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.config import RFM_DATA_FILE


def calculate_rfm_metrics(
    df: pd.DataFrame,
    snapshot_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Aggregates cleaned transactions into customer-level RFM metrics."""
    df = df.copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    if snapshot_date is None:
        snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    else:
        snapshot_date = pd.to_datetime(snapshot_date)

    rfm = df.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda d: (snapshot_date - d.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("TotalPrice", "sum"),
        FirstPurchase=("InvoiceDate", "min"),
        LastPurchase=("InvoiceDate", "max"),
        UniqueProducts=("StockCode", "nunique"),
        Country=("Country", lambda c: c.mode()[0] if not c.empty else "Unknown"),
    ).reset_index()

    rfm["AOV"] = (rfm["Monetary"] / rfm["Frequency"]).round(2)
    rfm["Tenure_Days"] = (snapshot_date - rfm["FirstPurchase"]).dt.days
    rfm["Lifespan_Days"] = (rfm["LastPurchase"] - rfm["FirstPurchase"]).dt.days
    rfm["Monetary"] = rfm["Monetary"].round(2)

    return rfm


def score_rfm_quantiles(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns quintile scores (1 to 5) for Recency, Frequency, and Monetary.
    - Recency: 5 is best (most recent / lowest days).
    - Frequency: 5 is best (highest order count).
    - Monetary: 5 is best (highest total spend).
    """
    df = rfm_df.copy()

    df["R_Score"] = pd.qcut(
        df["Recency"].rank(method="first"),
        q=5,
        labels=[5, 4, 3, 2, 1],
    ).astype(int)

    df["F_Score"] = pd.qcut(
        df["Frequency"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    df["M_Score"] = pd.qcut(
        df["Monetary"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    df["RFM_Score_Code"] = (
        df["R_Score"].astype(str) + df["F_Score"].astype(str) + df["M_Score"].astype(str)
    )
    df["RFM_Score_Total"] = df["R_Score"] + df["F_Score"] + df["M_Score"]

    return df


def assign_rfm_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Maps customer R, F, and M scores to actionable business segment labels."""
    df = df.copy()

    def get_segment(row) -> str:
        r = row["R_Score"]
        f = row["F_Score"]
        m = row["M_Score"]

        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if r <= 2 and f >= 4 and m >= 4:
            return "Can't Lose Them"
        if r >= 3 and f >= 3 and m >= 3:
            return "Loyal Customers"
        if r <= 2 and (f >= 3 or m >= 3):
            return "At Risk"
        if r >= 4 and f in [2, 3] and m >= 2:
            return "Potential Loyalists"
        if r >= 4 and f == 1:
            return "Recent Customers"
        if r == 3 and f in [1, 2] and m in [2, 3]:
            return "Promising"
        if r in [2, 3] and f in [2, 3] and m in [2, 3]:
            return "Customers Needing Attention"
        if r in [2, 3] and f <= 2 and m <= 2:
            return "About to Sleep"
        if r == 1 and f == 1 and m == 1:
            return "Lost"
        if r <= 2:
            return "Hibernating"
        return "Promising"

    df["RFM_Segment"] = df.apply(get_segment, axis=1)
    return df


def run_rfm_pipeline(
    cleaned_df: pd.DataFrame,
    output_path: Optional[Path] = RFM_DATA_FILE,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executes end-to-end RFM metric generation, scoring, and segmentation."""
    rfm = calculate_rfm_metrics(cleaned_df)
    rfm_scored = score_rfm_quantiles(rfm)
    rfm_final = assign_rfm_segments(rfm_scored)

    total_rev = rfm_final["Monetary"].sum()
    total_cust = len(rfm_final)

    summary = (
        rfm_final.groupby("RFM_Segment")
        .agg(
            CustomerCount=("CustomerID", "count"),
            TotalRevenue=("Monetary", "sum"),
            AvgRecency=("Recency", "mean"),
            AvgFrequency=("Frequency", "mean"),
            AvgMonetary=("Monetary", "mean"),
            AvgAOV=("AOV", "mean"),
        )
        .reset_index()
    )

    summary["CustomerSharePct"] = (summary["CustomerCount"] / total_cust * 100).round(2)
    summary["RevenueSharePct"] = (summary["TotalRevenue"] / total_rev * 100).round(2)
    summary["AvgRecency"] = summary["AvgRecency"].round(1)
    summary["AvgFrequency"] = summary["AvgFrequency"].round(1)
    summary["AvgMonetary"] = summary["AvgMonetary"].round(2)
    summary["AvgAOV"] = summary["AvgAOV"].round(2)
    summary["TotalRevenue"] = summary["TotalRevenue"].round(2)

    summary = summary.sort_values("TotalRevenue", ascending=False).reset_index(drop=True)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rfm_final.to_csv(output_path, index=False)
        print(f"RFM analysis completed: {len(rfm_final):,} customers segmented and saved to {output_path}")

    return rfm_final, summary


if __name__ == "__main__":
    from src.data_processing import load_raw_data, clean_transactions
    raw_df = load_raw_data()
    cleaned_df, _ = clean_transactions(raw_df)
    rfm_df, segment_summary = run_rfm_pipeline(cleaned_df)
    print("\n--- RFM Segment Summary ---")
    print(segment_summary.to_string(index=False))
