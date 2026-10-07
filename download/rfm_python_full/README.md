# Customer Segmentation & RFM Behavioral Analysis

End-to-end e-commerce data-science pipeline:
- **Backend** (`src/` + `run_pipeline.py`): generates 50K+ realistic transactions, cleans them, computes RFM metrics, runs K-Means + PCA clustering, simulates A/B marketing campaigns, and produces 8 publication-grade figures.
- **Frontend** (`app.py`): Streamlit dashboard with 5 modules — Executive KPI Overview, RFM Quantile Explorer, K-Means & PCA Clustering (2D + 3D), Targeted Campaign Simulator, Strategic Playbook & CRM Export.

This is the **bug-fixed** version. See `BUGFIX_REPORT.md` for the full list of fixes; the short version:

| # | Bug | Severity | Status |
|---|-----|----------|--------|
| 1 | Streamlit simulator sliders (`cpc_cost`, `gross_margin`) had no effect — function used hardcoded values | Critical | Fixed |
| 2 | `run_pipeline.py` printed wrong retention % (off by ~8 pp) | Reporting | Fixed |
| 3 | `RFM_SEGMENT_MAP` in `config.py` was dead code | Maintenance | Removed |
| — | Minor: empty multiselect crash, missing "VIP Champions" persona crash, `int()` truncation on conversions | Hardening | Fixed |

---

## Project layout

```
rfm_python_full/
├── app.py                  # 🌐 FRONTEND: Streamlit dashboard (5 modules)
├── run_pipeline.py         # ⚙️  CLI orchestrator (6-stage pipeline)
├── requirements.txt
├── README.md               # ← you are here
├── BUGFIX_REPORT.md        # detailed bug write-up
└── src/
    ├── __init__.py
    ├── config.py            # paths, hyperparameters (RFM_SEGMENT_MAP removed)
    ├── data_processing.py   # ingestion, cleaning, outlier capping
    ├── rfm_analysis.py      # R/F/M metrics, quintile scoring, 11-segment mapping
    ├── clustering.py        # log1p + StandardScaler + KMeans + PCA + persona labeling
    ├── marketing_strategy.py # 4 persona playbooks, A/B test, ROI engine (FIXED)
    ├── data_generator.py    # 50K+ realistic synthetic transactions
    └── visualization.py     # 8 publication-grade 300-DPI figures
```

The pipeline auto-creates these output directories at runtime:

```
data/raw/              → ecommerce_transactions.csv         (generated raw data)
data/processed/        → cleaned_transactions.csv           (post-cleaning)
                       → customer_rfm_segmented.csv        (RFM + cluster labels)
reports/               → cluster_profiles.csv               (cluster summary)
                       → clustering_evaluation_metrics.csv  (k=2..9 metrics)
                       → campaign_simulation_results.csv    (segment rollout)
                       → marketing_playbook_report.md       (executive report)
reports/figures/      → 01..08_*.png                       (8 publication figures)
```

---

## Quickstart

```bash
# 1. Create a virtual environment (Python 3.10+ recommended)
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the full pipeline (generates data, models, figures, reports)
python run_pipeline.py             # ~30-60s on a modern laptop

# 4. Launch the Streamlit dashboard
streamlit run app.py               # opens http://localhost:8501
```

### CLI options for `run_pipeline.py`

```bash
python run_pipeline.py --regenerate           # force-regenerate raw data (50K records)
python run_pipeline.py --transactions 80000  # generate 80K transactions
python run_pipeline.py --customers 8000      # use 8,000 customers
python run_pipeline.py --clusters 5         # use k=5 for K-Means
```

### Run individual modules

Each backend module is also runnable standalone for debugging:

```bash
python -m src.data_generator        # regenerate raw data only
python -m src.data_processing       # clean raw → cleaned CSV
python -m src.rfm_analysis          # RFM scoring + segmentation
python -m src.clustering            # K-Means + PCA + persona labeling
python -m src.marketing_strategy    # smoke-test the A/B simulator (NEW)
python -m src.visualization         # regenerate all 8 figures
```

---

## Module-by-module reference

### `src/config.py`
Central config — paths, hyperparameters (`K_MIN=2`, `K_MAX=9`, `DEFAULT_OPTIMAL_K=4`, `RANDOM_SEED=42`, `DEFAULT_N_TRANSACTIONS=60000`, `DEFAULT_N_CUSTOMERS=6500`). The old `RFM_SEGMENT_MAP` regex table has been removed (it was dead code; see `BUGFIX_REPORT.md`).

### `src/data_processing.py`
- `load_raw_data()` — reads `data/raw/ecommerce_transactions.csv`.
- `clean_transactions(df, cap_outliers=True)` — removes missing `CustomerID`, isolates cancellations (`InvoiceNo` starts with "C" or `Quantity ≤ 0`), filters `UnitPrice > 0`, computes `TotalPrice`, derives date features (year/month/day/hour/day-of-week), caps `Quantity` and `UnitPrice` at the 99.9th percentile. Returns `(cleaned_df, summary_dict)`.

### `src/rfm_analysis.py`
- `calculate_rfm_metrics(df, snapshot_date=None)` — per-customer Recency (days since last order), Frequency (distinct invoices), Monetary (sum TotalPrice), AOV, Tenure, Lifespan, UniqueProducts, Country.
- `score_rfm_quantiles(rfm_df)` — uses `pd.qcut(... rank(method="first"))` to assign 1–5 scores; Recency is inverted (5 = most recent).
- `assign_rfm_segments(df)` — if/elif ladder over (R,F,M) producing 11 segments: Champions, Loyal Customers, Potential Loyalists, Recent Customers, Promising, Customers Needing Attention, About to Sleep, At Risk, Can't Lose Them, Hibernating, Lost.
- `run_rfm_pipeline(cleaned_df)` — chains the three steps, writes `customer_rfm_segmented.csv`.

### `src/clustering.py`
- `preprocess_rfm_for_clustering(rfm_df)` — `np.log1p` to tame skew, then `StandardScaler`. Reports pre/post-log skewness.
- `evaluate_cluster_range(scaled_features, k_min=2, k_max=9)` — for each k, fits KMeans (`k-means++`, `n_init=10`) and records inertia, silhouette, Davies-Bouldin, Calinski-Harabasz.
- `train_kmeans_clustering(scaled_features, n_clusters=4)` — final fit (`n_init=30`, `max_iter=500`).
- `apply_pca_reduction(scaled_features, n_components=3)` — PCA + loadings DataFrame.
- `interpret_and_label_clusters(rfm_df)` — auto-labels clusters as VIP Champions, Hibernating / One-Time Buyers, Loyal Regulars, At-Risk Lapsed Spenders (based on mean Monetary / Recency rankings). Writes `cluster_profiles.csv`.

### `src/marketing_strategy.py` **(FIXED)**
- `MARKETING_PLAYBOOKS` — dict of 4 persona playbooks (objective, channels, offer, cadence, sample email subject lines, expected/targeted response rates).
- `simulate_campaign_ab_test(rfm_df, baseline_response_rate, target_lift_pct, sample_split, random_state, cpc_email, margin, aov_control, aov_targeted)` — **NEW parameters** for all economic inputs. Runs a 50/50 binomial A/B test, computes relative lift, two-proportion Z-test p-value, cost/revenue/profit/ROI for both arms. Echoes the economic inputs back in the result dict. Includes input validation and zero-SE / zero-control-rate guards.
- `simulate_full_segmented_rollout(rfm_df, cpc_email, margin, targeted_aov_uplift_pct)` — per-segment rollout table; the AOV uplift factor is now parameterized (was hardcoded `1.15`).
- `generate_marketing_playbook_report(rfm_df)` — markdown report combining the A/B results and segment rollout table.

### `src/data_generator.py`
- `PRODUCT_CATALOG` — 49 realistic SKUs across 6 categories with base prices.
- `COUNTRIES` — 10 countries with realistic distribution (UK = 85%).
- `generate_customer_profiles(n_customers)` — assigns each customer a behavioral archetype (VIP 10%, Loyal 25%, Potential 20%, Occasional 20%, AtRisk 10%, Hibernating 15%) and a country.
- `generate_synthetic_transactions(n_transactions=60000, n_customers=6500, start_date='2024-01-01', end_date='2025-06-30')` — generates realistic orders per customer based on archetype, with VIPs buying 18-35 orders at high quantities and Hibernating customers buying 1-3. Injects ~2.5% cancellations (negative quantities, `C`-prefixed invoice numbers), ~8% guest checkouts (NaN CustomerID), and ~0.2% promo items (`UnitPrice = 0`).

### `src/visualization.py`
8 publication-grade 300-DPI PNGs (saved under `reports/figures/`):
1. `01_rfm_distributions.png` — raw vs log1p distribution of R/F/M (with skew annotations)
2. `02_correlation_heatmap.png` — Pearson correlation matrix of R/F/M/AOV/Tenure/UniqueProducts
3. `03_clustering_evaluation_curves.png` — dual-axis Elbow + Silhouette across k=2..9
4. `04_pca_clusters_2d.png` — 2D PCA scatter colored by persona, with cluster centroids
5. `05_pca_discrete_feature_2d.png` — same projection colored by R_Score
6. `06_snake_plot_rfm_profiles.png` — standardized RFM profile per persona
7. `07_revenue_vs_customers_pareto.png` — customer-share vs revenue-share bars per segment
8. `08_campaign_response_lift.png` — baseline vs targeted response rate per segment

### `app.py` (Streamlit frontend)
5 sidebar modules:

1. **📊 Executive KPI Overview** — 4 KPI cards (Total Customers, Total Net Revenue, VIP Revenue Concentration, Avg Customer Spend), Pareto bar chart (customer vs revenue share per persona), revenue composition donut, cluster profiling table.
2. **🔍 RFM Quantile Explorer** — multiselect filter by segment + R/F/M score sliders; 2D scatter plots (Recency×Frequency bubble, Frequency×Monetary log-scale), customer records table.
3. **🤖 K-Means & PCA Clustering** — 4 tabs: 2D PCA projection, 3D interactive PCA scatter, Elbow + Silhouette curves with metrics table, behavioral Snake Plot.
4. **🚀 Targeted Campaign Simulator (+15% Lift)** — sliders for baseline rate, target lift, cost per message, gross margin, control AOV, targeted AOV. **All inputs now actually flow through to the simulator** (was the main bug). Displays 4 metric cards (Control Response, Targeted Response, Relative Lift, Net Profit Gain), grouped bar chart of conversions/profit/ROI, and a Z-test significance verdict.
5. **📋 Strategic Playbook & Export** — collapsible cards for each persona playbook (objective, channels, offer, cadence, sample email subjects, conversion driver) and a CSV export button for the selected cohort.

---

## Verifying the fixes

After installing and running the pipeline:

```bash
# 1. Confirm parameter wiring works without launching Streamlit
python -m src.marketing_strategy
# Expected: prints "OK — parameters now flow through correctly."

# 2. Run the full pipeline; the corrected retention line should appear
python run_pipeline.py --regenerate
# Expected: "Cleaned records retained: ~54,000 / ~60,000 (~90.x% retention,
#           ~6,000 rows removed — ~4,800 missing CustomerID + ~1,200 cancellations/non-positive)"

# 3. Launch Streamlit, go to Tab 4 (Campaign Simulator)
streamlit run app.py
# Drag "Cost per Outreach Message" from $0.05 to $0.50 — control_cost_usd and
# treatment_cost_usd should jump 10×, and ROI should drop sharply. Previously
# they would not change at all.
```

---

## Tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| Data | pandas + numpy | Standard, fast enough at 60K rows |
| ML | scikit-learn | KMeans, PCA, StandardScaler, silhouette/DB/CH metrics |
| Stats | scipy.stats | Two-proportion Z-test for A/B significance |
| Plots (static) | matplotlib + seaborn | 300-DPI publication figures |
| Plots (interactive) | plotly | 2D/3D PCA in Streamlit |
| Frontend | Streamlit | Single-file dashboard, instant `st.cache_data` |
| Reproducibility | `RANDOM_SEED=42` everywhere | Deterministic data, KMeans, A/B sim |
