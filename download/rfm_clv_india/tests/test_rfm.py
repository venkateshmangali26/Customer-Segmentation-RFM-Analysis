"""Tests for src/data_processing.py and src/rfm_analysis.py."""
import numpy as np
import pandas as pd
import pytest

from src.data_generator import generate_synthetic_transactions
from src.data_processing import clean_transactions
from src.rfm_analysis import (
    calculate_rfm_metrics,
    score_rfm_quantiles,
    assign_rfm_segments,
    run_rfm_pipeline,
)


@pytest.fixture(scope="module")
def synthetic_data():
    """Small synthetic dataset reused across tests in this module."""
    df = generate_synthetic_transactions(
        n_transactions=3000,
        n_customers=150,
        output_path=None,
    )
    return df


@pytest.fixture
def cleaned_data(synthetic_data):
    df, _ = clean_transactions(synthetic_data, output_path=None)
    return df


def test_clean_transactions_removes_missing_customer_ids(synthetic_data):
    cleaned, stats = clean_transactions(synthetic_data, output_path=None)
    # No missing CustomerID should remain
    assert cleaned["CustomerID"].isna().sum() == 0
    # Retained records should be less than initial
    assert stats["retained_clean_records"] <= stats["initial_records"]
    # All retained quantities and prices are positive
    assert (cleaned["Quantity"] > 0).all()
    assert (cleaned["UnitPrice"] > 0).all()
    # TotalPrice is computed
    assert "TotalPrice" in cleaned.columns
    assert np.allclose(cleaned["TotalPrice"], cleaned["Quantity"] * cleaned["UnitPrice"])


def test_clean_transactions_customerid_is_string(cleaned_data):
    """CustomerID should always be a string after cleaning, never a float
    like '17850.0' — this is the type-safety fix from the audit."""
    assert cleaned_data["CustomerID"].dtype == object
    # No CustomerID should have a decimal point
    assert not cleaned_data["CustomerID"].str.contains(r"\.", regex=True).any()


def test_calculate_rfm_metrics_produces_expected_columns(cleaned_data):
    rfm = calculate_rfm_metrics(cleaned_data)
    expected_cols = {"CustomerID", "Recency", "Frequency", "Monetary", "AOV",
                     "FirstPurchase", "LastPurchase", "UniqueProducts", "Country",
                     "Tenure_Days", "Lifespan_Days"}
    assert expected_cols.issubset(rfm.columns)
    assert len(rfm) > 0
    # Recency should be non-negative
    assert (rfm["Recency"] >= 0).all()
    # Frequency >= 1 (every customer made at least one order)
    assert (rfm["Frequency"] >= 1).all()
    # Monetary should match the sum of cleaned TotalPrice per customer
    expected_monetary = cleaned_data.groupby("CustomerID")["TotalPrice"].sum()
    actual_monetary = rfm.set_index("CustomerID")["Monetary"]
    np.testing.assert_allclose(actual_monetary.values, expected_monetary.values, rtol=1e-2)


def test_score_rfm_quantiles_produces_1_to_5_scores(cleaned_data):
    rfm = calculate_rfm_metrics(cleaned_data)
    scored = score_rfm_quantiles(rfm)
    for col in ["R_Score", "F_Score", "M_Score"]:
        assert col in scored.columns
        assert scored[col].between(1, 5).all()
    assert "RFM_Score_Code" in scored.columns
    assert scored["RFM_Score_Code"].str.len().eq(3).all()


def test_assign_rfm_segments_produces_known_segments(cleaned_data):
    rfm = calculate_rfm_metrics(cleaned_data)
    scored = score_rfm_quantiles(rfm)
    segmented = assign_rfm_segments(scored)
    assert "RFM_Segment" in segmented.columns
    expected_segments = {
        "Champions", "Loyal Customers", "Potential Loyalists", "Recent Customers",
        "Promising", "Customers Needing Attention", "About to Sleep", "At Risk",
        "Can't Lose Them", "Hibernating", "Lost",
    }
    actual_segments = set(segmented["RFM_Segment"].unique())
    # Most segments should be present (some may be empty on tiny datasets)
    overlap = expected_segments & actual_segments
    assert len(overlap) >= 5, f"Expected at least 5 known segments, got {len(overlap)}"


def test_run_rfm_pipeline_returns_dataframe_and_summary(cleaned_data):
    rfm, summary = run_rfm_pipeline(cleaned_data, output_path=None)
    assert isinstance(rfm, pd.DataFrame)
    assert isinstance(summary, pd.DataFrame)
    assert len(rfm) > 0
    assert "RFM_Segment" in summary.columns
    assert "CustomerSharePct" in summary.columns
    assert "RevenueSharePct" in summary.columns
    # Customer shares should sum to ~100%
    np.testing.assert_allclose(summary["CustomerSharePct"].sum(), 100.0, rtol=1e-3)
    np.testing.assert_allclose(summary["RevenueSharePct"].sum(), 100.0, rtol=1e-3)
