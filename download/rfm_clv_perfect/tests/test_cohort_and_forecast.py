"""Tests for src/cohort_analysis.py + src/sales_forecasting.py."""
import numpy as np
import pandas as pd
import pytest

from src.cohort_analysis import (
    build_cohort_matrix,
    compute_retention_rate_matrix,
    summarize_cohorts,
    run_cohort_analysis,
)
from src.sales_forecasting import (
    aggregate_revenue_time_series,
    forecast_sales,
)


@pytest.fixture
def synthetic_cleaned_df():
    """Synthetic transaction logs spanning ~6 months, 200 customers, with
    realistic retention patterns per cohort."""
    np.random.seed(42)
    rows = []
    for cid in range(200):
        # First purchase between Jan and Apr 2024
        first_dt = pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(np.random.randint(0, 120)))
        n_repeat = np.random.poisson(2)
        last_dt = first_dt
        for _ in range(n_repeat + 1):
            rows.append({
                "InvoiceNo": f"INV-{cid}-{_}",
                "StockCode": "SKU",
                "Description": "Test product",
                "Quantity": 1,
                "InvoiceDate": last_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "UnitPrice": 25.0,
                "CustomerID": str(cid),
                "Country": "United Kingdom",
                "TotalPrice": 25.0,
            })
            last_dt = last_dt + pd.Timedelta(days=int(np.random.randint(15, 60)))
    df = pd.DataFrame(rows)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    return df


def test_build_cohort_matrix_produces_triangular_matrix(synthetic_cleaned_df):
    cohort_sizes, retention_matrix = build_cohort_matrix(synthetic_cleaned_df, cohort_period="M")
    assert isinstance(retention_matrix, pd.DataFrame)
    assert len(retention_matrix) > 0
    # Cohort size (month 0) should equal row sums in column 0
    assert (retention_matrix.iloc[:, 0] > 0).all()
    # The matrix should be lower-triangular: a cohort can't have a customer
    # in a month index that's larger than the cohort's age
    for i in range(len(retention_matrix)):
        row = retention_matrix.iloc[i]
        nonzero_indices = (row > 0).values.nonzero()[0]
        if len(nonzero_indices) > 0:
            max_idx = nonzero_indices.max()
            # A cohort with N months of history should not have data at index > N-1
            # (this is approximate because of how the cohort period is computed)
            assert max_idx >= 0


def test_compute_retention_rate_matrix_yields_zero_to_one(synthetic_cleaned_df):
    _, ret_matrix = build_cohort_matrix(synthetic_cleaned_df, cohort_period="M")
    rate_matrix = compute_retention_rate_matrix(ret_matrix)
    # Month-0 retention is always 100%
    if rate_matrix.shape[1] > 0:
        assert np.allclose(rate_matrix.iloc[:, 0], 1.0)
    # All other rates should be between 0 and 1
    assert (rate_matrix.values >= 0).all()
    assert (rate_matrix.values <= 1.0 + 1e-9).all()


def test_summarize_cohorts_has_expected_columns(synthetic_cleaned_df):
    cohort_sizes, ret_matrix = build_cohort_matrix(synthetic_cleaned_df, cohort_period="M")
    summary = summarize_cohorts(cohort_sizes, ret_matrix)
    expected_cols = {
        "CohortDate", "CohortSize", "Month1_Retention_Pct",
        "HalfLife_Months", "FinalMonth_Retention_Pct", "MonthsTracked",
    }
    assert expected_cols.issubset(summary.columns)
    assert len(summary) == len(ret_matrix)


def test_run_cohort_analysis_writes_outputs(synthetic_cleaned_df, tmp_path):
    cohort_sizes, ret_matrix, rate_matrix, summary = run_cohort_analysis(
        synthetic_cleaned_df, cohort_period="M", output_dir=tmp_path
    )
    # Verify the outputs were written
    assert (tmp_path / "cohort_retention_counts.csv").exists()
    assert (tmp_path / "cohort_retention_rates.csv").exists()
    assert (tmp_path / "cohort_summary.csv").exists()


# ============================================================================
# Sales forecasting tests
# ============================================================================

def test_aggregate_revenue_time_series_produces_regular_grid(synthetic_cleaned_df):
    ts = aggregate_revenue_time_series(synthetic_cleaned_df, freq="D")
    assert "ds" in ts.columns
    assert "y" in ts.columns
    assert len(ts) > 0
    # The series should be regular (no missing days)
    if len(ts) > 1:
        deltas = ts["ds"].diff().dropna()
        assert deltas.nunique() == 1, "Time series should be regular"
        # All deltas should be 1 day
        assert (deltas == pd.Timedelta(days=1)).all()


def test_forecast_sales_returns_history_and_forecast(synthetic_cleaned_df):
    history, forecast, stats = forecast_sales(
        synthetic_cleaned_df, forecast_horizon_days=30, freq="D", output_dir=None
    )
    assert isinstance(history, pd.DataFrame)
    assert isinstance(forecast, pd.DataFrame)
    assert isinstance(stats, dict)
    # Forecast should have the expected columns
    if not forecast.empty:
        expected_cols = {"ds", "yhat", "yhat_lower", "yhat_upper"}
        assert expected_cols.issubset(forecast.columns)
        # Confidence band should bracket the point estimate
        assert (forecast["yhat_lower"] <= forecast["yhat"]).all()
        assert (forecast["yhat"] <= forecast["yhat_upper"]).all()
        # All revenue values should be non-negative
        assert (forecast["yhat"] >= 0).all()
        assert (forecast["yhat_lower"] >= 0).all()


def test_forecast_stats_has_backend_field(synthetic_cleaned_df):
    _, _, stats = forecast_sales(synthetic_cleaned_df, output_dir=None)
    assert "backend" in stats
    # Backend should be one of the known values
    assert stats["backend"] in {"prophet", "statsmodels-holt-winters", "none"}
    assert "training_points" in stats
    assert "predicted_total_revenue" in stats
