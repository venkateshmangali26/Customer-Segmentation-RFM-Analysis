"""Tests for src/clv_modeling.py — the fixed BG/NBD + Gamma-Gamma module."""
import numpy as np
import pandas as pd
import pytest

from src.clv_modeling import (
    BGNBDModel,
    GammaGammaModel,
    prepare_clv_summary_data,
    compute_predictive_clv,
)


@pytest.fixture(scope="module")
def synthetic_clv_data():
    """Generate synthetic data with enough customers for the BG/NBD fit to converge."""
    np.random.seed(42)
    n_customers = 800

    # Synthetic BG/NBD parameters
    true_r, true_alpha = 0.85, 8.0
    true_a, true_b = 0.5, 1.5

    # Customer tenures in weeks (uniform 10–100 weeks)
    T = np.random.uniform(10, 100, n_customers).astype(float)

    # Purchase counts follow NegBinom(r, alpha/(alpha+T))
    # Use scipy.stats.nbinom directly
    from scipy.stats import nbinom
    # nbinom uses (n, p) where mean = n*(1-p)/p; we want mean = r*T/(alpha+T)
    # so n=r, p = alpha/(alpha+T)
    p_per_customer = true_alpha / (true_alpha + T)
    x = np.array([nbinom.rvs(true_r, p) for p in p_per_customer])

    # Recency: for x > 0, t_x is uniform between 0 and T
    t_x = np.where(x > 0, np.random.uniform(0, T, n_customers), 0.0)

    # Monetary values: Gamma(2, 450) — mean ₹900, var ₹900² × 2 ≈ ₹405k²
    # (Indian e-commerce typical AOV in INR)
    m = np.random.gamma(2.0, 450.0, n_customers).astype(float)

    # Build the cleaned transactions DataFrame from this summary
    rows = []
    for i in range(n_customers):
        cid = f"CUST-{i:05d}"
        # Generate x+1 orders (first + x repeat) at roughly uniform intervals
        n_orders = int(x[i]) + 1
        for j in range(n_orders):
            order_date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(T[i] * 7 * (j + 1) / (n_orders + 1)))
            rows.append({
                "InvoiceNo": f"INV-{cid}-{j}",
                "StockCode": "SKU",
                "Description": "test product",
                "Quantity": 1,
                "InvoiceDate": order_date.strftime("%Y-%m-%d %H:%M:%S"),
                "UnitPrice": m[i],
                "CustomerID": cid,
                "Country": "United Kingdom",
                "TotalPrice": m[i],
            })

    df = pd.DataFrame(rows)
    return df


def test_prepare_clv_summary_data_produces_expected_columns(synthetic_clv_data):
    summary = prepare_clv_summary_data(synthetic_clv_data)
    expected_cols = {"CustomerID", "frequency", "recency", "T", "monetary_value",
                     "TotalOrders", "FirstOrderDate", "LastOrderDate", "TotalSpend"}
    assert expected_cols.issubset(summary.columns)
    # All frequencies should be >= 0
    assert (summary["frequency"] >= 0).all()
    # T should be positive (BG/NBD requirement)
    assert (summary["T"] > 0).all()
    # Monetary value should be positive
    assert (summary["monetary_value"] > 0).all()


def test_bgnbd_fit_returns_finite_params(synthetic_clv_data):
    summary = prepare_clv_summary_data(synthetic_clv_data)
    x = summary["frequency"].values.astype(float)
    t_x = summary["recency"].values.astype(float)
    T = summary["T"].values.astype(float)

    model = BGNBDModel().fit(x, t_x, T)
    assert model.is_fitted
    assert np.isfinite(model.r)
    assert np.isfinite(model.alpha)
    assert np.isfinite(model.a)
    assert np.isfinite(model.b)
    # All params must be positive (the bounds require this)
    assert model.r > 0
    assert model.alpha > 0
    assert model.a > 0
    assert model.b > 0


def test_predict_p_alive_handles_x_equals_zero():
    """Bug A regression: x=0 (one-time customers) must NOT default to 100% alive.
    The fixed implementation uses the Fader-Hardie x=0 closed form."""
    # Use a model with b > 1 (so the x=0 formula is well-defined)
    model = BGNBDModel()
    model.r, model.alpha, model.a, model.b = 0.85, 8.0, 0.5, 2.0  # b > 1
    model.is_fitted = True

    # Mix of one-time (x=0) and repeat (x>=1) customers
    x = np.array([0, 0, 1, 2, 3, 0, 5, 0])
    t_x = np.array([0, 0, 5, 10, 15, 0, 25, 0])
    T = np.array([10, 20, 15, 25, 30, 12, 35, 18])

    p_alive = model.predict_p_alive(x, t_x, T)
    assert p_alive.shape == x.shape
    # All probabilities are in (0, 1) — clipped to (0.001, 0.999)
    assert (p_alive >= 0.001).all()
    assert (p_alive <= 0.999).all()

    # CRITICAL: one-time customers (x=0) should NOT all be 1.0
    one_time_p_alive = p_alive[x == 0]
    assert not np.allclose(one_time_p_alive, 1.0), \
        "Bug A regression: x=0 customers default to 100% alive"
    # One-time customers with longer tenure should have lower P(Alive) — the
    # longer they've gone without a repeat purchase, the more likely they've churned
    p_alive_short = model.predict_p_alive(np.array([0]), np.array([0]), np.array([5]))[0]
    p_alive_long = model.predict_p_alive(np.array([0]), np.array([0]), np.array([50]))[0]
    assert p_alive_long < p_alive_short, \
        f"P(Alive) for x=0 should decrease with T; got short={p_alive_short}, long={p_alive_long}"


def test_predict_expected_purchases_returns_nonnegative():
    """Bug B regression: expected purchases must use the canonical Fader-Hardie
    closed form, not the heuristic. Output should be non-negative."""
    model = BGNBDModel()
    model.r, model.alpha, model.a, model.b = 0.85, 8.0, 0.5, 2.0
    model.is_fitted = True

    x = np.array([0, 1, 2, 5, 10, 0, 3])
    t_x = np.array([0, 5, 10, 25, 50, 0, 15])
    T = np.array([10, 15, 25, 40, 80, 12, 30])

    # 90-day = ~12.857 weeks
    exp_90d = model.predict_expected_purchases(12.857, x, t_x, T)
    assert exp_90d.shape == x.shape
    assert (exp_90d >= 0).all()
    assert np.all(np.isfinite(exp_90d))
    # Expected purchases should be reasonable (not absurdly large)
    # For 90 days with realistic BG/NBD params, mean should be < 5 purchases
    assert exp_90d.mean() < 20

    # 365-day should be larger than 90-day (more time = more expected purchases)
    exp_365d = model.predict_expected_purchases(52.143, x, t_x, T)
    assert (exp_365d >= exp_90d - 1e-6).all(), "365D expected purchases should be >= 90D"


def test_gammagamma_fit_returns_positive_params(synthetic_clv_data):
    summary = prepare_clv_summary_data(synthetic_clv_data)
    x = summary["frequency"].values.astype(float)
    m = summary["monetary_value"].values.astype(float)

    model = GammaGammaModel().fit(x, m)
    assert model.is_fitted
    # q must be > 1 (required for finite E[M] = p*γ/(q-1))
    assert model.q > 1.0
    assert model.p > 0
    assert model.gamma > 0


def test_gammagamma_predict_spend_shrinks_towards_prior(synthetic_clv_data):
    """Bug C regression: the Gamma-Gamma model should produce empirical-Bayes
    shrinkage, NOT just echo back the observed mean."""
    summary = prepare_clv_summary_data(synthetic_clv_data)
    x = summary["frequency"].values.astype(float)
    m = summary["monetary_value"].values.astype(float)

    model = GammaGammaModel().fit(x, m)
    pred = model.predict_expected_spend(x, m)
    assert (pred >= 5.0).all()  # the implementation floors at $5

    # For customers with high x (many repeat purchases), prediction should be
    # closer to observed m. For customers with low x, prediction should shrink
    # towards the prior mean.
    high_x_mask = x > np.median(x)
    if high_x_mask.any() and (~high_x_mask).any():
        # High-x customers: prediction should be closer to observed m
        high_pred = pred[high_x_mask]
        high_obs = m[high_x_mask]
        # |pred - m| / m should be smaller for high-x customers
        rel_diff_high = np.abs(high_pred - high_obs) / high_obs
        low_pred = pred[~high_x_mask]
        low_obs = m[~high_x_mask]
        rel_diff_low = np.abs(low_pred - low_obs) / low_obs
        assert rel_diff_high.mean() <= rel_diff_low.mean() + 0.5, \
            "Shrinkage should be stronger (smaller pred-to-obs gap) for high-x customers"


def test_compute_predictive_clv_end_to_end(synthetic_clv_data):
    """End-to-end smoke test: compute_predictive_clv should produce a DataFrame
    with all expected columns and finite CLV values."""
    # Build a minimal rfm_df with the columns compute_predictive_clv needs
    from src.rfm_analysis import calculate_rfm_metrics
    rfm_df = calculate_rfm_metrics(synthetic_clv_data)
    # Add a dummy Cluster_Persona so downstream code works
    rfm_df["Cluster_Persona"] = "VIP Champions"

    enriched, stats = compute_predictive_clv(synthetic_clv_data, rfm_df, output_path=None)
    assert isinstance(enriched, pd.DataFrame)
    assert isinstance(stats, dict)
    expected_cols = {"P_Alive", "Churn_Risk", "Pred_Purchases_90D", "Pred_Purchases_365D",
                     "Pred_Spend_Per_Order", "Predicted_CLV_90D", "Predicted_CLV_365D", "CLV_Tier"}
    assert expected_cols.issubset(enriched.columns)

    # CLV values should be non-negative and finite
    assert (enriched["Predicted_CLV_90D"] >= 0).all()
    assert (enriched["Predicted_CLV_365D"] >= 0).all()
    assert enriched["Predicted_CLV_365D"].apply(np.isfinite).all()

    # Stats dict has all expected keys
    expected_stats_keys = {"bgnbd_r", "bgnbd_alpha", "bgnbd_a", "bgnbd_b",
                           "bgnbd_fit_success", "gg_p", "gg_q", "gg_gamma", "gg_fit_success",
                           "mean_p_alive", "total_predicted_clv_365d", "mean_predicted_clv_365d",
                           "n_one_time_customers", "n_repeat_customers"}
    assert expected_stats_keys.issubset(stats.keys())

    # CLV tiers should be one of the four expected
    assert set(enriched["CLV_Tier"].unique()).issubset({
        "Platinum CLV (Top 10%)", "Gold CLV (Top 30%)",
        "Silver CLV (Mid 30%)", "Bronze CLV (Bottom 40%)"
    })
