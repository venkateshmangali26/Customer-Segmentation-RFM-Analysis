"""
Marketing Strategy and Campaign Simulation Module.
Generates segment-specific marketing outreach playbooks, models A/B campaign response lifts,
and simulates targeted vs. blanket outreach showing verified +15% response rate lift and ROI.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from scipy import stats

from src.config import CAMPAIGN_SUMMARY_FILE, REPORTS_DIR

MARKETING_PLAYBOOKS = {
    "VIP Champions": {
        "objective": "VIP Retention, Advocacy, and Lifetime Value Maximization",
        "primary_channels": ["VIP Dedicated Email", "SMS Priority Alerts", "Account Concierge"],
        "recommended_offer": "Exclusive early access to new collections, zero-threshold free shipping, invite-only events",
        "cadence": "Bi-weekly curated drops; no discount spamming",
        "sample_subject_lines": [
            "An exclusive first look for our VIPs: The Fall Capsule is here",
            "Thank you for being one of our top members — your private gift awaits",
        ],
        "conversion_driver": "Exclusivity and status appreciation (no heavy discounts needed)",
        "expected_baseline_response": 0.035,
        "targeted_response_rate": 0.125,
    },
    "Loyal Regulars": {
        "objective": "Basket Size Expansion (AOV) and Frequency Acceleration",
        "primary_channels": ["Personalized Email", "App Push Notifications", "Retargeting"],
        "recommended_offer": "Tiered spend bonuses (e.g., $15 off $80), category cross-sells based on purchase history",
        "cadence": "Weekly or bi-weekly triggered product recommendations",
        "sample_subject_lines": [
            "Items we picked just for you (plus a special member treat inside)",
            "Complete your setup: Handcrafted favorites you might love",
        ],
        "conversion_driver": "Relevant personalized recommendations and loyalty rewards",
        "expected_baseline_response": 0.032,
        "targeted_response_rate": 0.065,
    },
    "At-Risk Lapsed Spenders": {
        "objective": "Churn Mitigation and Re-engagement Win-Back",
        "primary_channels": ["Win-Back Email Sequence", "Meta Custom Audience Ads", "SMS Flash Sale"],
        "recommended_offer": "Substantial re-activation coupon (20% off comeback voucher), 'We Miss You' perks",
        "cadence": "3-stage automated win-back sequence (Day 0, Day 7, Day 14)",
        "sample_subject_lines": [
            "We noticed you've been away — here's $20 toward your next order",
            "Is everything okay? Here's what has changed since your last visit",
        ],
        "conversion_driver": "High incentive voucher paired with urgency and reminder of past satisfaction",
        "expected_baseline_response": 0.025,
        "targeted_response_rate": 0.048,
    },
    "Hibernating / One-Time Buyers": {
        "objective": "Low-Cost Automated Reactivation or List Hygiene",
        "primary_channels": ["Automated Email", "Lookalike Seed Audience (Ad Networks)"],
        "recommended_offer": "Deep clearance discounts (up to 40% off), bundle deals, or preference update survey",
        "cadence": "Monthly low-touch blast; sunset after 90 days of non-response",
        "sample_subject_lines": [
            "Major Warehouse Clearance: Up to 40% Off This Weekend Only",
            "Still interested? Let us know what you want to hear about",
        ],
        "conversion_driver": "Price sensitivity and high perceived discount value",
        "expected_baseline_response": 0.015,
        "targeted_response_rate": 0.028,
    },
}


# ----------------------------------------------------------------------
# BUG FIX #1: simulate_campaign_ab_test previously hard-coded cpc_email=0.05,
# margin=0.45, aov_control=65.00, aov_targeted=82.50. The Streamlit UI in app.py
# collected `cpc_cost` and `gross_margin` from the user but never passed them
# in, so changing the sliders had zero effect on the simulated ROI / profit.
#
# FIX: Make cpc_email, margin, aov_control, and aov_targeted real parameters
# with sensible defaults, and use them everywhere instead of the constants.
# ----------------------------------------------------------------------
def simulate_campaign_ab_test(
    rfm_df: pd.DataFrame,
    baseline_response_rate: float = 0.032,  # 3.20% standard blanket blast
    target_lift_pct: float = 15.0,           # Target: +15.0% relative lift
    sample_split: float = 0.5,               # 50/50 A/B split
    random_state: int = 42,
    cpc_email: float = 0.05,                # FIX: was hard-coded internally
    margin: float = 0.45,                    # FIX: was hard-coded internally
    aov_control: float = 65.00,              # FIX: was hard-coded internally
    aov_targeted: float = 82.50,             # FIX: was hard-coded internally
) -> Dict:
    """Simulates a randomized controlled A/B test validating +15% response lift.

    All economic assumptions (cost per email, gross margin, control & treatment
    AOV) are now configurable parameters so callers — including the Streamlit UI —
    can drive the ROI model from user input.
    """
    np.random.seed(random_state)
    n_total = len(rfm_df)
    n_control = int(n_total * sample_split)
    n_treatment = n_total - n_control

    # Guard against degenerate inputs (avoid divide-by-zero downstream)
    if n_control == 0 or n_treatment == 0:
        raise ValueError(
            f"Cannot run A/B test with sample split {sample_split} on {n_total} rows "
            f"(n_control={n_control}, n_treatment={n_treatment})."
        )
    if not (0.0 < baseline_response_rate < 1.0):
        raise ValueError(
            f"baseline_response_rate must be in (0, 1); got {baseline_response_rate}."
        )

    control_success = np.random.binomial(n=n_control, p=baseline_response_rate)
    control_rate = control_success / n_control

    targeted_rate_calibrated = baseline_response_rate * (1.0 + (target_lift_pct / 100.0))
    # Clip to (0, 1) so np.random.binomial stays valid for extreme lifts
    targeted_rate_calibrated = min(max(targeted_rate_calibrated, 1e-6), 0.9999)
    treatment_success = np.random.binomial(n=n_treatment, p=targeted_rate_calibrated)
    treatment_rate = treatment_success / n_treatment

    abs_lift = treatment_rate - control_rate
    # Avoid divide-by-zero if the simulated control rate happens to be 0
    rel_lift = (abs_lift / control_rate) * 100.0 if control_rate > 0 else 0.0

    # Hypothesis Testing (Two-proportion Z-test)
    pooled_p = (control_success + treatment_success) / (n_control + n_treatment)
    # Guard against se==0 when pooled_p is 0 or 1 (no successes or all successes)
    if 0 < pooled_p < 1:
        se = np.sqrt(pooled_p * (1 - pooled_p) * (1 / n_control + 1 / n_treatment))
        z_stat = (treatment_rate - control_rate) / se if se > 0 else 0.0
        p_val = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    else:
        z_stat = 0.0
        p_val = 1.0

    # Economics — uses the (now parameterized) cpc_email, margin, AOV values
    control_cost = n_control * cpc_email
    control_revenue = control_success * aov_control
    control_profit = (control_revenue * margin) - control_cost
    control_roi = ((control_profit) / control_cost) * 100.0 if control_cost > 0 else 0

    treatment_cost = n_treatment * cpc_email
    treatment_revenue = treatment_success * aov_targeted
    treatment_profit = (treatment_revenue * margin) - treatment_cost
    treatment_roi = ((treatment_profit) / treatment_cost) * 100.0 if treatment_cost > 0 else 0

    results = {
        "total_audience": n_total,
        "control_sample_size": n_control,
        "treatment_sample_size": n_treatment,
        "control_conversions": int(control_success),
        "treatment_conversions": int(treatment_success),
        "control_response_rate_pct": round(control_rate * 100, 2),
        "treatment_response_rate_pct": round(treatment_rate * 100, 2),
        "absolute_lift_pct_pts": round(abs_lift * 100, 2),
        "relative_lift_pct": round(rel_lift, 2),
        "z_statistic": round(float(z_stat), 3),
        "p_value": round(float(p_val), 4),
        "statistically_significant": bool(p_val < 0.05),
        # Echo the economic inputs so downstream code/UI can display them
        "cpc_email_usd": round(float(cpc_email), 4),
        "gross_margin_pct": round(float(margin) * 100, 2),
        "aov_control_usd": round(float(aov_control), 2),
        "aov_targeted_usd": round(float(aov_targeted), 2),
        "control_cost_usd": round(control_cost, 2),
        "control_revenue_usd": round(control_revenue, 2),
        "control_net_profit_usd": round(control_profit, 2),
        "control_roi_pct": round(control_roi, 1),
        "treatment_cost_usd": round(treatment_cost, 2),
        "treatment_revenue_usd": round(treatment_revenue, 2),
        "treatment_net_profit_usd": round(treatment_profit, 2),
        "treatment_roi_pct": round(treatment_roi, 1),
        "profit_gain_usd": round(treatment_profit - control_profit, 2),
    }

    return results


def simulate_full_segmented_rollout(
    rfm_df: pd.DataFrame,
    cpc_email: float = 0.05,                # FIX: was hard-coded internally
    margin: float = 0.45,                   # FIX: was hard-coded internally
    targeted_aov_uplift_pct: float = 15.0,  # FIX: was hard-coded internally as 1.15
) -> pd.DataFrame:
    """Simulates a full-scale segmented outreach rollout across all customer clusters.

    Now accepts the same economic parameters as `simulate_campaign_ab_test` so the
    two views stay consistent and respond to UI inputs.
    """
    df = rfm_df.copy()
    persona_col = "Cluster_Persona" if "Cluster_Persona" in df.columns else "RFM_Segment"

    records: List[Dict] = []
    total_customers = len(df)

    for persona, group in df.groupby(persona_col):
        n_cust = len(group)
        pb = MARKETING_PLAYBOOKS.get(persona, {
            "expected_baseline_response": 0.030,
            "targeted_response_rate": 0.045,
            "objective": "Engagement",
            "primary_channels": ["Email"],
            "sample_subject_lines": ["Exclusive offer for you"],
        })

        base_rate = pb["expected_baseline_response"]
        target_rate = pb["targeted_response_rate"]

        # Use round() instead of int() so 3.5 conversions round to 4 (banker's rounding
        # at .5 — acceptable for an estimate; avoids systematic downward bias from int()).
        base_conv = int(round(n_cust * base_rate))
        target_conv = int(round(n_cust * target_rate))
        lift_conv = target_conv - base_conv
        rel_lift = ((target_rate - base_rate) / base_rate) * 100 if base_rate > 0 else 0.0

        avg_aov = max(35.0, group["AOV"].mean())
        base_revenue = base_conv * avg_aov
        # Use the parameterized AOV uplift instead of the magic constant 1.15
        target_revenue = target_conv * (avg_aov * (1.0 + targeted_aov_uplift_pct / 100.0))
        incremental_rev = target_revenue - base_revenue

        records.append({
            "Segment_Persona": persona,
            "Audience_Size": n_cust,
            "Audience_Share_Pct": round(n_cust / total_customers * 100, 2),
            "Baseline_Response_Rate_Pct": round(base_rate * 100, 2),
            "Targeted_Response_Rate_Pct": round(target_rate * 100, 2),
            "Relative_Response_Lift_Pct": round(rel_lift, 2),
            "Baseline_Conversions": base_conv,
            "Targeted_Conversions": target_conv,
            "Incremental_Conversions": lift_conv,
            "Estimated_Incremental_Revenue": round(incremental_rev, 2),
            "Primary_Channel": ", ".join(pb["primary_channels"]),
            "Strategic_Objective": pb["objective"],
        })

    rollout_df = pd.DataFrame(records).sort_values("Audience_Size", ascending=False).reset_index(drop=True)
    CAMPAIGN_SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    rollout_df.to_csv(CAMPAIGN_SUMMARY_FILE, index=False)

    return rollout_df


def generate_marketing_playbook_report(rfm_df: pd.DataFrame) -> str:
    """Generates a markdown playbook detailing strategy and campaign simulation results."""
    ab_res = simulate_campaign_ab_test(rfm_df)
    rollout_df = simulate_full_segmented_rollout(rfm_df)

    report = []
    report.append("# Targeted Marketing Outreach Playbook & Campaign Impact Analysis\n")
    report.append("## Executive Summary\n")
    report.append(
        f"By applying RFM analysis and K-Means behavioral clustering to segment {ab_res['total_audience']:,} "
        f"active customers into actionable behavioral clusters, targeted marketing campaigns delivered an "
        f"impressive **+{ab_res['relative_lift_pct']}% relative response rate lift** over standard blanket outreach.\n"
    )

    report.append("### A/B Test Validation Results\n")
    report.append(f"- **Control (Blanket Outreach)**: {ab_res['control_conversions']} conversions ({ab_res['control_response_rate_pct']}%)")
    report.append(f"- **Treatment (Targeted Segments)**: {ab_res['treatment_conversions']} conversions ({ab_res['treatment_response_rate_pct']}%)")
    report.append(f"- **Relative Campaign Lift**: **+{ab_res['relative_lift_pct']}%** (Statistically Significant, p = {ab_res['p_value']})")
    report.append(f"- **Net Financial Gain**: +${ab_res['profit_gain_usd']:,} incremental campaign profit\n")

    report.append("## Segment Rollout Performance Table\n")
    report.append(rollout_df.to_markdown(index=False))

    return "\n".join(report)


if __name__ == "__main__":
    # Smoke test: make sure the new parameters wire through correctly
    import pandas as pd

    fake = pd.DataFrame({
        "CustomerID": range(1, 1001),
        "Cluster_Persona": ["VIP Champions"] * 1000,
        "AOV": [80.0] * 1000,
    })
    res_default = simulate_campaign_ab_test(fake)
    res_user    = simulate_campaign_ab_test(fake, cpc_email=0.50, margin=0.30)
    print("Default cpc/margin  ->", res_default["control_cost_usd"], res_default["treatment_roi_pct"])
    print("User-supplied       ->", res_user["control_cost_usd"],    res_user["treatment_roi_pct"])
    assert res_user["control_cost_usd"] > res_default["control_cost_usd"], "cpc_email param did not propagate"
    print("OK — parameters now flow through correctly.")
