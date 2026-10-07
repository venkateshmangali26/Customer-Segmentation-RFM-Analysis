"""Tests for src/marketing_strategy.py — the A/B simulator + rollout."""
import numpy as np
import pandas as pd
import pytest

from src.marketing_strategy import (
    MARKETING_PLAYBOOKS,
    simulate_campaign_ab_test,
    simulate_full_segmented_rollout,
    generate_marketing_playbook_report,
)


@pytest.fixture
def fake_rfm_df():
    """A small fake rfm_df with the columns the simulator needs.
    INDIA: AOV is in INR (₹) — typical Indian e-commerce scale."""
    return pd.DataFrame({
        "CustomerID": [f"CUST-{i:04d}" for i in range(200)],
        "Cluster_Persona": ["VIP Champions", "Loyal Regulars",
                            "At-Risk Lapsed Spenders", "Hibernating / One-Time Buyers"] * 50,
        "AOV": np.random.uniform(300, 2500, 200),  # ₹300–₹2500 typical Indian AOV range
        "RFM_Segment": ["Champions"] * 200,
    })


def test_simulate_campaign_ab_test_returns_expected_keys(fake_rfm_df):
    res = simulate_campaign_ab_test(fake_rfm_df)
    expected_keys = {
        "total_audience", "control_sample_size", "treatment_sample_size",
        "control_conversions", "treatment_conversions",
        "control_response_rate_pct", "treatment_response_rate_pct",
        "absolute_lift_pct_pts", "relative_lift_pct",
        "z_statistic", "p_value", "statistically_significant",
        # INDIA: keys are suffixed `_inr` instead of `_usd`
        "control_cost_inr", "control_revenue_inr", "control_net_profit_inr", "control_roi_pct",
        "treatment_cost_inr", "treatment_revenue_inr", "treatment_net_profit_inr", "treatment_roi_pct",
        "profit_gain_inr",
    }
    assert expected_keys.issubset(res.keys())


def test_simulate_campaign_ab_test_respects_cpc_parameter(fake_rfm_df):
    """Bug #1 regression: cpc_email parameter must actually affect the cost
    numbers, not be silently dropped on the floor.
    INDIA: defaults are in INR (₹0.50/message) instead of USD ($0.05)."""
    res_default = simulate_campaign_ab_test(fake_rfm_df, cpc_email=0.50)   # ₹0.50 default
    res_high_cpc = simulate_campaign_ab_test(fake_rfm_df, cpc_email=5.00)  # ₹5.00 — 10x higher
    # 10x cpc → 10x control_cost_inr
    assert abs(res_high_cpc["control_cost_inr"] / res_default["control_cost_inr"] - 10.0) < 0.5, \
        "cpc_email parameter did not propagate to control_cost_inr"


def test_simulate_campaign_ab_test_respects_margin_parameter(fake_rfm_df):
    """Bug #1 regression: margin parameter must actually affect profit numbers."""
    res_low_margin = simulate_campaign_ab_test(fake_rfm_df, margin=0.20)
    res_high_margin = simulate_campaign_ab_test(fake_rfm_df, margin=0.80)
    # Higher margin → higher profit (assuming any conversions happened)
    if res_high_margin["treatment_conversions"] > 0:
        assert res_high_margin["treatment_net_profit_inr"] > res_low_margin["treatment_net_profit_inr"]


def test_simulate_campaign_ab_test_respects_aov_parameters(fake_rfm_df):
    """Bug #1 regression: aov_control and aov_targeted must affect revenue.
    INDIA: defaults are ₹900 / ₹1350 instead of $65 / $82.50."""
    res_low_aov = simulate_campaign_ab_test(fake_rfm_df, aov_control=200.0, aov_targeted=300.0)   # ₹ scale
    res_high_aov = simulate_campaign_ab_test(fake_rfm_df, aov_control=2000.0, aov_targeted=3000.0)
    # Higher AOV → higher revenue per conversion
    if res_high_aov["control_conversions"] > 0:
        assert res_high_aov["control_revenue_inr"] > res_low_aov["control_revenue_inr"]


def test_simulate_campaign_ab_test_handles_zero_control_conversions():
    """Edge case: very low response rate might simulate 0 control conversions.
    The implementation must not divide by zero on rel_lift."""
    df = pd.DataFrame({"CustomerID": range(50)})  # tiny audience
    # This should not raise ZeroDivisionError
    res = simulate_campaign_ab_test(df, baseline_response_rate=0.001, target_lift_pct=10.0)
    assert np.isfinite(res["relative_lift_pct"])


def test_simulate_campaign_ab_test_validates_inputs():
    """The function should raise ValueError on out-of-range inputs."""
    df = pd.DataFrame({"CustomerID": range(100)})
    with pytest.raises(ValueError):
        simulate_campaign_ab_test(df, baseline_response_rate=0.0)  # p must be > 0
    with pytest.raises(ValueError):
        simulate_campaign_ab_test(df, baseline_response_rate=1.5)  # p must be < 1


def test_simulate_full_segmented_rollout_produces_per_segment_rows(fake_rfm_df):
    rollout = simulate_full_segmented_rollout(fake_rfm_df)
    assert isinstance(rollout, pd.DataFrame)
    expected_cols = {
        "Segment_Persona", "Audience_Size", "Audience_Share_Pct",
        "Baseline_Response_Rate_Pct", "Targeted_Response_Rate_Pct",
        "Relative_Response_Lift_Pct", "Baseline_Conversions", "Targeted_Conversions",
        "Incremental_Conversions", "Estimated_Incremental_Revenue",
        "Primary_Channel", "Strategic_Objective",
    }
    assert expected_cols.issubset(rollout.columns)
    # Should produce one row per persona in the input data
    expected_personas = set(fake_rfm_df["Cluster_Persona"].unique())
    actual_personas = set(rollout["Segment_Persona"].unique())
    assert actual_personas == expected_personas
    # Audience shares should sum to ~100%
    np.testing.assert_allclose(rollout["Audience_Share_Pct"].sum(), 100.0, rtol=1e-3)


def test_generate_marketing_playbook_report_produces_markdown(fake_rfm_df):
    report = generate_marketing_playbook_report(fake_rfm_df)
    assert isinstance(report, str)
    assert report.startswith("# ")
    assert "Executive Summary" in report
    assert "A/B Test Validation Results" in report
    assert "Segment Rollout Performance Table" in report


def test_marketing_playbooks_dict_has_expected_structure():
    """All four persona playbooks should have the required fields."""
    expected_personas = {
        "VIP Champions", "Loyal Regulars",
        "At-Risk Lapsed Spenders", "Hibernating / One-Time Buyers",
    }
    assert set(MARKETING_PLAYBOOKS.keys()) == expected_personas
    for persona, pb in MARKETING_PLAYBOOKS.items():
        required_fields = {
            "objective", "primary_channels", "recommended_offer", "cadence",
            "sample_subject_lines", "conversion_driver",
            "expected_baseline_response", "targeted_response_rate",
        }
        assert required_fields.issubset(pb.keys()), f"Playbook {persona} missing: {required_fields - set(pb.keys())}"
        # All playbooks should have at least 2 sample subject lines
        assert len(pb["sample_subject_lines"]) >= 2
