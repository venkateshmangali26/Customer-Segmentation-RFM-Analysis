# Customer Segmentation, RFM & Predictive CLV Platform

Production-grade CRM analytics platform combining **rule-based RFM quintiles**, **unsupervised K-Means/PCA clustering**, **probabilistic forward CLV modeling** (BG/NBD + Gamma-Gamma), **monthly cohort retention analysis**, **Prophet time-series sales forecasting**, and **econometric A/B campaign simulation** — all behind a colorful, self-healing Streamlit dashboard.

This is the **perfected** version of the project, with every bug from the prior audits fixed:

| Bug | Status |
|-----|--------|
| `simulate_campaign_ab_test` hardcodes `cpc_email=0.05, margin=0.45, aov_*=…` and the Streamlit UI doesn't wire them through | ✅ Fixed — 4 economic parameters now plumbed end-to-end |
| `BGNBDModel.predict_p_alive` returns 100% for one-time (x=0) customers | ✅ Fixed — uses the Fader-Hardie 2005 x=0 closed form |
| `predict_expected_purchases` uses a heuristic `cond_lambda * t * p_alive` instead of the canonical closed form | ✅ Fixed — uses `scipy.special.hyp2f1` for the Gaussian hypergeometric |
| `GammaGammaModel.fit` doesn't actually fit via MLE (p, q hardcoded) | ✅ Fixed — fits (p, q, γ) via L-BFGS-B on the Fader-Hardie 2013 NLL |
| Misleading "retention %" in run_pipeline.py print | ✅ Fixed — shows actual retained/initial with breakdown |
| Dead `RFM_SEGMENT_MAP` regex in config.py | ✅ Removed with deprecation note |
| CustomerID type safety regression | ✅ Fixed — `astype(float).astype(int).astype(str)` |
| `pd.qcut` without `duplicates='drop'` | ✅ Added across all three quantile calls |
| Snake plot divides by `std()` inline (zero-std edge case) | ✅ Fixed with `_z()` helper and zero-std guard |
| Empty multiselect in RFM Explorer = "0 of N" | ✅ Fixed — empty now means "show all" with info toast |
| `@st.cache_data` doesn't invalidate on pipeline re-run | ✅ Fixed — "Clear cache" button in sidebar |

---

## 📁 Project layout (17 files)

```
rfm_clv_perfect/
├── README.md                          ← you are here
├── requirements.txt                   ← all deps incl. Prophet + statsmodels + pytest
├── .gitignore
├── Dockerfile                         ← single-container Streamlit deployment
├── docker-compose.yml                 ← dashboard + one-shot pipeline-runner services
├── app.py                             ← 8-module Streamlit frontend, colorful UI
├── run_pipeline.py                    ← 9-stage CLI orchestrator
├── .github/workflows/ci.yml           ← GitHub Actions: pytest on Py 3.10/3.11/3.12
├── prisma/schema.prisma               ← (not used; legacy file from earlier scaffold)
├── src/
│   ├── __init__.py
│   ├── config.py                       ← paths, hyperparameters, auto-create dirs at import
│   ├── data_processing.py              ← ingestion, cleaning, outlier capping, type-safe CustomerID
│   ├── rfm_analysis.py                ← R/F/M metrics, quintile scoring with duplicates='drop', 11-segment mapping
│   ├── clustering.py                  ← log1p + StandardScaler + KMeans + PCA + persona labeling
│   ├── marketing_strategy.py          ← 4 playbooks + parameterized A/B simulator + edge-case guards
│   ├── data_generator.py              ← 50K+ realistic synthetic transactions
│   ├── visualization.py               ← 8 publication-grade 300-DPI figures
│   ├── clv_modeling.py                ← BG/NBD + Gamma-Gamma — fixed canonical math ★
│   ├── cohort_analysis.py             ← monthly acquisition cohorts + retention heatmap ★ NEW
│   └── sales_forecasting.py           ← Prophet (preferred) + Holt-Winters fallback ★ NEW
└── tests/
    ├── conftest.py
    ├── test_rfm.py                     ← RFM + cleaning + segments (8 tests)
    ├── test_clv.py                    ← BG/NBD + GG + bug A/B/C regression tests (7 tests)
    ├── test_clustering.py             ← KMeans + PCA + persona labeling (6 tests)
    ├── test_marketing.py              ← A/B simulator + bug #1 regression tests (7 tests)
    └── test_cohort_and_forecast.py    ← cohort + sales forecast (7 tests)
```

★ = new module; ★ NEW = entirely new feature vs prior versions.

---

## 🚀 Quickstart (local)

```bash
# 1. Create venv (Python 3.10+ recommended)
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies (Prophet is optional — falls back to statsmodels)
pip install -r requirements.txt
# If Prophet fails to install (cmdstan toolchain missing), the dashboard will
# automatically use Holt-Winters exponential smoothing instead.

# 3. Run the full 9-stage pipeline (one-time)
python run_pipeline.py
# Output: data/raw/, data/processed/, reports/{cluster_profiles.csv,
#         campaign_simulation_results.csv, clv_summary_metrics.csv,
#         cohort_retention_*.csv, sales_history.csv, sales_forecast.csv},
#         reports/figures/01..08_*.png

# 4. Launch the colorful Streamlit dashboard
streamlit run app.py               # opens http://localhost:8501
```

### First-run self-healing

If you skip step 3 and just `streamlit run app.py`, the dashboard detects the missing CSVs and **automatically generates data and runs the full pipeline** on first load (with a progress spinner). Subsequent loads hit the `@st.cache_data` cache. To force a reload from disk after re-running the pipeline, click the **"🔄 Clear cache & reload from disk"** button at the top of the sidebar.

---

## 🐳 Docker deployment

```bash
# Build and launch the dashboard
docker compose up -d --build
# Open http://localhost:8501

# Run the pipeline as a one-shot job (writes CSVs to ./reports/)
docker compose run --rm pipeline-runner

# View logs
docker compose logs -f

# Stop and remove
docker compose down
```

The compose file mounts `./data` and `./reports` as volumes so generated CSVs persist across container restarts. The `Dockerfile` includes a healthcheck that pings Streamlit's `/_stcore/health` endpoint.

---

## 🧪 CI/CD (GitHub Actions)

The `.github/workflows/ci.yml` workflow runs on every push/PR against `main`/`master`:

- **Matrix**: Python 3.10, 3.11, 3.12
- **Steps**:
  1. Cache pip downloads
  2. Install `requirements.txt` (with fallback to slim stack if Prophet fails)
  3. Syntax-check all `src/*.py` + `app.py` + `run_pipeline.py`
  4. Run the full pytest suite (35+ tests)
  5. Smoke-test the entire pipeline end-to-end on a 5K-record dataset

The CI is Prophet-tolerant: if Prophet fails to install on a given platform, the test suite still passes because `sales_forecasting.py` gracefully falls back to statsmodels Holt-Winters.

---

## 🧪 Run the pytest suite locally

```bash
pip install pytest pytest-cov
pytest tests/ -v --tb=short
# ~35 tests across 5 test files, should complete in <60s
```

To get a coverage report:
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

---

## 📊 What the dashboard renders (8 sidebar modules)

### 1. 📊 Executive KPI Overview
4 styled KPI cards (Active Customers, Total Net Revenue, VIP Revenue Share, Avg Customer Spend) — each with a different accent color. Pareto bar chart (customer vs revenue share per persona) + revenue composition donut + cluster profiling table with money/percent formatting.

### 2. 🔍 RFM Quantile Explorer
Segment multiselect + R/F/M score range sliders + 2 Plotly scatter plots (Recency×Frequency bubble, Frequency×Monetary log-scale) + top-300 customer records table.

### 3. 🤖 K-Means & PCA Clustering
4 sub-tabs: 2D PCA scatter, 3D interactive PCA, Elbow + Silhouette evaluation curves with metrics table, behavioral Snake Plot (zero-std-guarded).

### 4. 🔮 Predictive CLV (BG/NBD + Gamma-Gamma)
4 KPI cards (Projected 1-Yr Net CLV, Mean P(Alive), Mean 1-Yr CLV/Customer, High Churn Risk %) + box plot of CLV by persona + scatter of Churn Risk vs CLV (log-scale, colored by CLV Tier) + top-100 retention targets table.

### 5. 📅 Cohort Retention Heatmap ★ NEW
Monthly acquisition cohort retention heatmap (purple-to-white gradient) + cohort summary table (size, month-1 retention, half-life, final retention) + per-cohort retention curves line view.

### 6. 📈 Sales Forecast (Prophet) ★ NEW
Time-grain selector (Daily / Weekly / Monthly) + "Run Forecast" button + 3 stat metrics (backend, training points, predicted total revenue) + Plotly chart with historical revenue (blue line) + forecast point estimate (pink dotted) + 80% confidence band (pink shaded).

### 7. 🚀 Targeted Campaign Simulator
**6 user inputs**: baseline rate, target lift, cost per message, gross margin, control AOV, targeted AOV — **all wired through** to the parameterized `simulate_campaign_ab_test`. 4 metric cards (Control Response, Targeted Response, Relative Lift, Net Profit Gain) + grouped bar chart comparing Conversions / Net Profit / ROI + statistical significance verdict based on Z-test p-value.

### 8. 📋 Strategic Playbook & Export
4 collapsible persona playbooks (objective, channels, offer, cadence, sample email subject lines, conversion driver) + CSV export button per segment (now includes CLV columns when available).

---

## 🧮 Module reference

### `src/clv_modeling.py` — the fixed BG/NBD + Gamma-Gamma module

**Canonical math, finally correct:**

#### `BGNBDModel`
- `fit(x, t_x, T)` — fits `(r, α, a, b)` via `scipy.optimize.minimize` with `L-BFGS-B` and bounds `(1e-4, 100)`. Falls back to empirical priors on optimization failure.
- `predict_p_alive(x, t_x, T)` — uses the **Fader-Hardie 2005 closed form** for both cases:
  - x = 0 (one-time): `P(alive | x=0, t_x=0, T) = 1 / (1 + (a/(b-1)) * ((α+T)/α)^r)` — requires `b > 1`, falls back to 0.5 otherwise
  - x ≥ 1 (repeat): `P(alive | x, t_x, T) = 1 / (1 + (a/(b+x-1)) * ((α+T)/(α+t_x))^(r+x))`
- `predict_expected_purchases(t_weeks, x, t_x, T)` — uses the canonical Fader-Hardie conditional expectation with `scipy.special.hyp2f1` for the Gaussian hypergeometric function:
  ```
  E[X(t) | x, t_x, T] = ((a+b+x-1)/(a-1)) *
      (1 - ((α+T)/(α+T+t))^(r+x) * 2F1(r+x, b+x-1; a+b+x-1; t/(α+T+t)))
  ```

#### `GammaGammaModel`
- `fit(x, m)` — fits `(p, q, γ)` via L-BFGS-B on the Fader-Hardie 2013 negative log-likelihood:
  ```
  log L = Σ_j [ gammaln(p*x_j + q) - gammaln(p*x_j) - gammaln(q)
                + p*x_j * log(γ) - (p*x_j + q) * log(γ + x_j*m_j) ]
  ```
  Falls back to method-of-moments estimate on optimization failure.
- `predict_expected_spend(x, m)` — empirical-Bayes shrinkage:
  ```
  E[M | x, m] = ((1-w) * prior_mean + w * m)
  where w = p*x / (p*x + q - 1)  and  prior_mean = p*γ / (q-1)
  ```

#### `compute_predictive_clv(cleaned_df, rfm_df, gross_margin=0.45, discount_rate=0.10)`
Orchestrates everything: prepare summary → fit BG/NBD → fit GG → predict → enrich rfm_df → write `clv_summary_metrics.csv`. Returns `(enriched_df, model_stats_dict)`.

### `src/cohort_analysis.py` ★ NEW

- `build_cohort_matrix(cleaned_df, cohort_period="M")` — pivots to triangular cohort × month-index matrix of unique customer counts.
- `compute_retention_rate_matrix(retention_matrix)` — divides by cohort size to get 0-1 rates.
- `summarize_cohorts(...)` — one-row-per-cohort summary: size, month-1 retention %, half-life (first month where retention drops below 50%), final month retention.
- `run_cohort_analysis(cleaned_df, ...)` — end-to-end with CSV output to `reports/cohort_*.csv`.

### `src/sales_forecasting.py` ★ NEW

- `aggregate_revenue_time_series(cleaned_df, freq="D")` — produces a regular `(ds, y)` daily/weekly/monthly revenue series, filling gaps with 0.
- `forecast_with_prophet(...)` — uses Facebook's Prophet with yearly + weekly seasonality, 80% interval width, 0.05 changepoint prior scale.
- `forecast_with_statsmodels(...)` — Holt-Winters triple exponential smoothing fallback with additive trend + additive seasonality (period 7/52/12 based on freq). Uses residual bootstrap for confidence intervals.
- `forecast_sales(...)` — picks Prophet if installed, else statsmodels. Returns `(history_df, forecast_df, stats_dict)`.

### `src/marketing_strategy.py` — the parameterized A/B simulator

`simulate_campaign_ab_test` now accepts ALL economic inputs as keyword args:
```python
def simulate_campaign_ab_test(
    rfm_df,
    baseline_response_rate=0.032,
    target_lift_pct=15.0,
    sample_split=0.5,
    random_state=42,
    cpc_email=0.05,        # ← NEW: now parameterized
    margin=0.45,            # ← NEW: now parameterized
    aov_control=65.00,      # ← NEW: now parameterized
    aov_targeted=82.50,     # ← NEW: now parameterized
) -> Dict:
```

Plus edge-case guards:
- `ValueError` if `baseline_response_rate` not in `(0, 1)`
- `ValueError` if sample split produces empty control/treatment groups
- `targeted_rate_calibrated` clipped to `(1e-6, 0.9999)` so `np.random.binomial` never errors
- `rel_lift` guarded against `control_rate == 0` (ZeroDivisionError)
- Z-test guarded against `pooled_p ∈ {0, 1}` (zero-SE)

---

## 🎨 Visual design

The dashboard uses a colorful glassmorphism theme:

- **Background**: deep navy → midnight gradient (`#0a0e27 → #151b3d → #1a1f4d → #0d2136`)
- **KPI cards**: glassmorphic with accent left border (purple/blue/green/orange per role), hover lift, gradient gold value text (`#fbbf24 → #f59e0b`)
- **Tabs**: pill-style with gradient fill on active (`#8b5cf6 → #6366f1`), purple glow
- **Sidebar**: vertical gradient with section headers in lavender
- **Plotly charts**: dark theme, semi-transparent backgrounds, Bold color palette for scatter series
- **Typography**: headings use a purple→blue→teal gradient text effect

The CSS is injected via `st.markdown(..., unsafe_allow_html=True)` at the top of `app.py` — easy to customize.

---

## 🛠️ Tech stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Data | pandas + numpy | Standard |
| ML | scikit-learn | KMeans, PCA, StandardScaler, silhouette/DB/CH metrics |
| Stats | scipy.stats + scipy.special | Z-test, gammaln, hyp2f1 |
| Forecast | Prophet (optional) + statsmodels | Auto-fallback if Prophet unavailable |
| Plots (interactive) | plotly | All dashboard charts |
| Plots (publication) | matplotlib + seaborn | 8 300-DPI figures |
| Frontend | Streamlit | Single-file dashboard |
| Tests | pytest + pytest-cov | 35+ tests, includes regression tests for every fixed bug |
| Deployment | Docker + docker-compose | Single-container Streamlit + one-shot pipeline-runner |
| CI/CD | GitHub Actions | Matrix on Python 3.10/3.11/3.12 |

---

## ✅ Verify the fixes

```bash
# Run the full test suite (verifies all bug fixes via regression tests)
pytest tests/ -v

# Smoke-test the CLV math directly
python -m src.clv_modeling
# Should print: BG/NBD fit params, P(Alive) split by x=0 vs x>0,
#                expected purchases 90D/365D, Gamma-Gamma params
#                "All CLV model components verified ✓"

# Smoke-test the cohort module
python -m src.cohort_analysis

# Smoke-test the forecasting module
python -m src.sales_forecasting

# Run the full pipeline
python run_pipeline.py --regenerate

# Launch the dashboard
streamlit run app.py
# Then in Tab 7 (Campaign Simulator), drag the cpc_cost slider — the
# ROI numbers should now ACTUALLY change in response (Bug #1 fixed).
# In Tab 4 (CLV), check that one-time customers don't all show P(Alive)=100%
# (Bug A fixed — they should now reflect realistic dropout probabilities).
```

---

## 📋 Reproducibility

- `RANDOM_SEED = 42` everywhere — deterministic data generation, KMeans fits, A/B simulation
- BG/NBD fit starts from a method-of-moments initial guess
- Gamma-Gamma fit starts from `(p=2, q=3, γ=2*mean_spend)` — both fall back to MoM on L-BFGS-B failure

---

## 🧭 What I'd add next

- **Real-time WebSocket updates** for the dashboard (push new transactions live)
- **Customer journey Sankey diagram** showing flow between segments over time
- **Churn prediction ML model** (XGBoost on RFM features) to complement the probabilistic BG/NBD churn estimate
- **REST API** (`/api/rfm/analyze`, `/api/clv/forecast`) so other systems can consume the analytics
- **Multi-tenant support** (separate databases per brand)

Let me know which of those (or anything else) and I'll execute.
