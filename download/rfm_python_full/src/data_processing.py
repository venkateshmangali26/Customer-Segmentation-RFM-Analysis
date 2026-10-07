"""
Data Preprocessing and Ingestion Module.
Performs data validation, missing value imputation/removal, cancellation tracking,
outlier handling, and feature engineering on e-commerce transaction logs.
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.config import CLEANED_DATA_FILE, RAW_DATA_FILE


def load_raw_data(file_path: Optional[Path] = None) -> pd.DataFrame:
    """Loads raw transactions CSV."""
    path = file_path or RAW_DATA_FILE
    if not Path(path).exists():
        raise FileNotFoundError(f"Raw data file not found at: {path}")
    df = pd.read_csv(path, dtype={"InvoiceNo": str, "StockCode": str})
    return df


def clean_transactions(
    df: pd.DataFrame,
    cap_outliers: bool = True,
    output_path: Optional[Path] = CLEANED_DATA_FILE,
) -> Tuple[pd.DataFrame, Dict]:
    """
    Cleans raw transactions:
    1. Removes missing CustomerIDs.
    2. Isolates and logs cancellations.
    3. Filters valid transactions (Quantity > 0, UnitPrice > 0).
    4. Computes TotalPrice = Quantity * UnitPrice.
    5. Optionally caps extreme outliers at the 99.9th percentile.
    """
    initial_rows = len(df)
    initial_customers = df["CustomerID"].nunique()

    # 1. Check Missing Values
    missing_customers = df["CustomerID"].isna().sum()
    pct_missing_customers = (missing_customers / initial_rows) * 100

    # Retain only records with known CustomerID
    df_clean = df.dropna(subset=["CustomerID"]).copy()
    df_clean["CustomerID"] = df_clean["CustomerID"].astype(int).astype(str)

    # 2. Cancellations & Negative Quantities
    is_cancelled = df_clean["InvoiceNo"].str.startswith("C", na=False) | (df_clean["Quantity"] <= 0)
    cancelled_count = is_cancelled.sum()
    cancellation_rate = (cancelled_count / len(df_clean)) * 100

    # 3. Filter valid purchases
    valid_mask = (~is_cancelled) & (df_clean["UnitPrice"] > 0)
    df_valid = df_clean[valid_mask].copy()

    # 4. Date Parsing and Feature Engineering
    df_valid["InvoiceDate"] = pd.to_datetime(df_valid["InvoiceDate"])
    df_valid["TotalPrice"] = df_valid["Quantity"] * df_valid["UnitPrice"]

    df_valid["InvoiceYear"] = df_valid["InvoiceDate"].dt.year
    df_valid["InvoiceMonth"] = df_valid["InvoiceDate"].dt.month
    df_valid["InvoiceDay"] = df_valid["InvoiceDate"].dt.day
    df_valid["DayOfWeek"] = df_valid["InvoiceDate"].dt.day_name()
    df_valid["Hour"] = df_valid["InvoiceDate"].dt.hour

    # 5. Outlier Handling (optional capping)
    outliers_capped = 0
    if cap_outliers:
        q_qty_999 = df_valid["Quantity"].quantile(0.999)
        q_price_999 = df_valid["UnitPrice"].quantile(0.999)

        qty_mask = df_valid["Quantity"] > q_qty_999
        price_mask = df_valid["UnitPrice"] > q_price_999
        outliers_capped = int(qty_mask.sum() + price_mask.sum())

        df_valid.loc[qty_mask, "Quantity"] = q_qty_999
        df_valid.loc[price_mask, "UnitPrice"] = q_price_999
        df_valid["TotalPrice"] = df_valid["Quantity"] * df_valid["UnitPrice"]

    # Summary Statistics
    summary = {
        "initial_records": initial_rows,
        "initial_unique_customers": initial_customers,
        "missing_customer_ids": int(missing_customers),
        "pct_missing_customer_ids": round(pct_missing_customers, 2),
        "cancelled_records": int(cancelled_count),
        "cancellation_rate_pct": round(cancellation_rate, 2),
        "retained_clean_records": len(df_valid),
        "retained_unique_customers": df_valid["CustomerID"].nunique(),
        "outliers_capped": outliers_capped,
        "total_revenue": round(float(df_valid["TotalPrice"].sum()), 2),
        "date_range_start": str(df_valid["InvoiceDate"].min()),
        "date_range_end": str(df_valid["InvoiceDate"].max()),
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_valid.to_csv(output_path, index=False)
        print(f"Data cleaned successfully: {len(df_valid):,} valid records saved to {output_path}")

    return df_valid, summary


if __name__ == "__main__":
    raw_df = load_raw_data()
    cleaned_df, stats = clean_transactions(raw_df)
    for k, v in stats.items():
        print(f"  - {k}: {v}")
