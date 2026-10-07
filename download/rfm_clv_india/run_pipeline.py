"""
End-to-End Pipeline Runner for Customer Segmentation, RFM & Predictive CLV Platform.
================================================================================
9-stage pipeline:
  1. Generate synthetic transactions (50K+ records, 6.5K customers)
  2. Clean, filter, and engineer transaction features
  3. Compute RFM metrics + quintile scoring + 11-segment mapping
  4. K-Means clustering + PCA reduction + persona labeling
  5. BG/NBD + Gamma-Gamma probabilistic CLV forecasting (90D + 365D)
  6. Cohort retention analysis (monthly acquisition cohorts)
  7. Sales time-series forecasting (Prophet preferred, Holt-Winters fallback)
  8. Marketing strategy + A/B test simulation (+15% lift)
  9. Publication-grade figure generation (8 plots)
"""

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.clustering import run_clustering_pipeline
from src.clv_modeling import compute_predictive_clv
from src.cohort_analysis import run_cohort_analysis
from src.config import (
    CLEANED_DATA_FILE,
    CLUSTER_METRICS_FILE,
    DEFAULT_N_CUSTOMERS,
    DEFAULT_N_TRANSACTIONS,
    DEFAULT_OPTIMAL_K,
    FIGURES_DIR,
    RAW_DATA_FILE,
    REPORTS_DIR,
    RFM_DATA_FILE,
)
from src.data_generator import generate_synthetic_transactions
from src.data_processing import clean_transactions, load_raw_data
from src.marketing_strategy import (
    generate_marketing_playbook_report,
    simulate_campaign_ab_test,
    simulate_full_segmented_rollout,
)
from src.rfm_analysis import run_rfm_pipeline
from src.sales_forecasting import forecast_sales
from src.visualization import generate_all_visualizations


def run_full_pipeline(
    regenerate_data: bool = False,
    n_transactions: int = DEFAULT_N_TRANSACTIONS,
    n_customers: int = DEFAULT_N_CUSTOMERS,
    n_clusters: int = DEFAULT_OPTIMAL_K,
) -> None:
    """Executes the complete project lifecycle."""
    start_time = time.time()
    print("=" * 80)
    print(" CUSTOMER SEGMENTATION, RFM & PREDICTIVE CLV PIPELINE")
    print("=" * 80)

    # 1. Ingestion / Generation
    if regenerate_data or not RAW_DATA_FILE.exists():
        print(f"\n[Step 1/9] Generating synthetic transactions ({n_transactions:,}+ records)...")
        raw_df = generate_synthetic_transactions(
            n_transactions=n_transactions,
            n_customers=n_customers,
            output_path=RAW_DATA_FILE,
        )
    else:
        print(f"\n[Step 1/9] Loading existing raw dataset from {RAW_DATA_FILE}...")
        raw_df = load_raw_data(RAW_DATA_FILE)
    print(f" Loaded {len(raw_df):,} raw transaction rows across {raw_df['CustomerID'].nunique():,} unique customers.")

    # 2. Data Cleaning & Validation
    print("\n[Step 2/9] Cleaning transactions and removing guest checkouts/anomalies...")
    cleaned_df, cleaning_stats = clean_transactions(raw_df, output_path=CLEANED_DATA_FILE)
    # Honest retention print: retained / initial, with breakdown of what was removed
    initial_records = cleaning_stats["initial_records"]
    retained_records = cleaning_stats["retained_clean_records"]
    actual_retention_pct = (retained_records / initial_records * 100.0) if initial_records > 0 else 0.0
    records_removed = initial_records - retained_records
    print(
        f" Cleaned records retained: {retained_records:,} / {initial_records:,} "
        f"({actual_retention_pct:.1f}% retention, {records_removed:,} rows removed — "
        f"{cleaning_stats['missing_customer_ids']:,} missing CustomerID + "
        f"{cleaning_stats['cancelled_records']:,} cancellations/non-positive)"
    )
    print(f" Total Net Revenue tracked: ${cleaning_stats['total_revenue']:,.2f}")

    # 3. RFM Analysis & Quintile Scoring
    print("\n[Step 3/9] Computing customer-level RFM metrics & quintile scoring...")
    rfm_df, rfm_summary = run_rfm_pipeline(cleaned_df, output_path=RFM_DATA_FILE)
    print(f" Segmented {len(rfm_df):,} customers across {rfm_df['RFM_Segment'].nunique()} rule-based RFM segments.")

    # 4. K-Means Clustering & PCA Reduction
    print(f"\n[Step 4/9] Training K-Means clustering (k={n_clusters}) & computing PCA projections...")
    rfm_clustered, cluster_profiles, eval_df, pca_model, kmeans_model = run_clustering_pipeline(
        rfm_df, n_clusters=n_clusters, output_path=RFM_DATA_FILE
    )
    cum_var = pca_model.explained_variance_ratio_[:2].sum() * 100
    print(f" K-Means trained. PCA 2D cumulative explained variance: {cum_var:.2f}%")

    # 5. Predictive Customer Lifetime Value (BG/NBD + Gamma-Gamma)
    print("\n[Step 5/9] Fitting BG/NBD & Gamma-Gamma probabilistic CLV models...")
    rfm_clustered, clv_stats = compute_predictive_clv(
        cleaned_df, rfm_clustered, output_path=RFM_DATA_FILE
    )
    print(f" Mean P(Alive): {clv_stats['mean_p_alive']*100:.1f}%  ({clv_stats['n_one_time_customers']} one-time, {clv_stats['n_repeat_customers']} repeat)")
    print(f" BG/NBD fit success: {clv_stats['bgnbd_fit_success']}  | Gamma-Gamma fit success: {clv_stats['gg_fit_success']}")
    print(f" Total Projected 1-Year CLV: ${clv_stats['total_predicted_clv_365d']:,.2f}")

    # 6. Cohort Retention Analysis
    print("\n[Step 6/9] Computing monthly cohort retention matrix...")
    cohort_sizes, retention_matrix, rate_matrix, cohort_summary = run_cohort_analysis(
        cleaned_df, cohort_period="M", output_dir=REPORTS_DIR
    )
    print(f" Computed {len(cohort_summary)} monthly cohorts, max retention horizon: {retention_matrix.shape[1]} months")

    # 7. Sales Time-Series Forecasting
    print("\n[Step 7/9] Fitting sales time-series forecast (Prophet or Holt-Winters)...")
    sales_history, sales_forecast, forecast_stats = forecast_sales(
        cleaned_df, forecast_horizon_days=90, freq="D", output_dir=REPORTS_DIR
    )
    print(f" Forecast backend: {forecast_stats.get('backend', 'unknown')}")
    print(f" Predicted 90-day total revenue: ${forecast_stats.get('predicted_total_revenue', 0):,.2f}")

    # 8. Marketing Strategy & +15% Lift Simulation
    print("\n[Step 8/9] Simulating targeted marketing campaigns & A/B test lift (+15% benchmark)...")
    ab_test_res = simulate_campaign_ab_test(rfm_clustered, target_lift_pct=15.0)
    rollout_df = simulate_full_segmented_rollout(rfm_clustered)
    playbook_report = generate_marketing_playbook_report(rfm_clustered)

    report_file = PROJECT_ROOT / "reports" / "marketing_playbook_report.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(playbook_report, encoding="utf-8")
    print(f" A/B Test validation complete: +{ab_test_res['relative_lift_pct']}% relative lift over control!")
    print(f" Saved strategic marketing report to: {report_file}")

    # 9. High-Resolution Visualizations
    print("\n[Step 9/9] Generating publication-grade figures...")
    figures = generate_all_visualizations(
        rfm_clustered, cluster_profiles, eval_df, rollout_df, output_dir=FIGURES_DIR
    )

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(" PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Customers Processed : {len(rfm_clustered):,}")
    print(f"Total Revenue Tracked     : ${cleaned_df['TotalPrice'].sum():,.2f}")
    print(f"Optimal Clusters (k)      : {n_clusters}")
    print(f"Mean P(Alive)            : {clv_stats['mean_p_alive']*100:.1f}%")
    print(f"Total Projected 1-Yr CLV : ${clv_stats['total_predicted_clv_365d']:,.2f}")
    print(f"Cohorts Analyzed         : {len(cohort_summary)}")
    print(f"Forecast Backend         : {forecast_stats.get('backend', 'unknown')}")
    print(f"Predicted 90-Day Revenue : ${forecast_stats.get('predicted_total_revenue', 0):,.2f}")
    print(f"Control Response Rate    : {ab_test_res['control_response_rate_pct']}%")
    print(f"Targeted Response Rate   : {ab_test_res['treatment_response_rate_pct']}%")
    print(f"Relative Campaign Lift   : +{ab_test_res['relative_lift_pct']}%")
    print(f"Net Campaign Profit Gain  : +${ab_test_res['profit_gain_usd']:,.2f}")
    print(f"Visualizations Generated  : {len(figures)} figures saved to {FIGURES_DIR}")
    print(f"Total Execution Time      : {elapsed:.2f} seconds")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Customer Segmentation, RFM & CLV Pipeline")
    parser.add_argument("--regenerate", action="store_true", help="Force regenerate raw transaction data")
    parser.add_argument("--transactions", type=int, default=DEFAULT_N_TRANSACTIONS, help="Number of transactions")
    parser.add_argument("--customers", type=int, default=DEFAULT_N_CUSTOMERS, help="Number of customers")
    parser.add_argument("--clusters", type=int, default=DEFAULT_OPTIMAL_K, help="Number of K-Means clusters")
    args = parser.parse_args()

    run_full_pipeline(
        regenerate_data=args.regenerate,
        n_transactions=args.transactions,
        n_customers=args.customers,
        n_clusters=args.clusters,
    )
