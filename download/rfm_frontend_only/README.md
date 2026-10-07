# RFM Analysis — Frontend Only

This is just the **frontend** of the Customer Segmentation & RFM analysis system: a single Streamlit file (`app.py`) that renders the 5-module dashboard.

It is **not** standalone — the dashboard reads pre-computed CSVs produced by the backend pipeline and calls into `src/marketing_strategy.py` for the live campaign simulator. You still need the backend modules in place to run it.

---

## 📄 File

```
rfm_frontend_only/
└── app.py            ← the entire frontend (5 modules, ~540 lines)
```

## 🔌 What it imports from the backend

```python
from src.config import CLUSTER_METRICS_FILE, REPORTS_DIR, RFM_DATA_FILE
from src.marketing_strategy import MARKETING_PLAYBOOKS, simulate_campaign_ab_test
```

So the **minimum** backend surface area the frontend needs:

| Backend file | Symbols the frontend uses |
|--------------|---------------------------|
| `src/config.py` | `CLUSTER_METRICS_FILE`, `REPORTS_DIR`, `RFM_DATA_FILE` (path constants) |
| `src/marketing_strategy.py` | `MARKETING_PLAYBOOKS` (dict of persona playbooks), `simulate_campaign_ab_test()` (the A/B sim function) |

Plus these pre-computed CSVs produced by `python run_pipeline.py`:
- `data/processed/customer_rfm_segmented.csv` (the per-customer RFM table)
- `reports/cluster_profiles.csv` (cluster persona summary)
- `reports/clustering_evaluation_metrics.csv` (optional — Elbow + Silhouette table)

If those CSVs don't exist yet, the dashboard shows a friendly "Please run `python run_pipeline.py` first" error.

---

## 🚀 Run

```bash
# 1. Streamlit is the only "frontend" dependency:
pip install streamlit pandas plotly

# 2. But you still need the backend modules + pre-computed CSVs in place.
#    Either:
#      a) Copy app.py into a project that has the full backend (recommended),
#         then `python run_pipeline.py` once to produce the CSVs.
#      b) If you just want to see the dashboard skeleton render, you can
#         `streamlit run app.py` — it will immediately error on missing CSVs
#         but the layout / sidebar / KPI card CSS will all be visible.

# 3. Once the backend CSVs exist:
streamlit run app.py     # opens http://localhost:8501
```

---

## 📊 What the dashboard renders (5 sidebar modules)

| Module | What you see |
|--------|--------------|
| **📊 Executive KPI Overview** | 4 styled KPI cards (Total Customers, Total Net Revenue, VIP Revenue Share, Avg Customer Spend) + Pareto bar chart (customer vs revenue share per persona) + revenue composition donut + cluster profiling table with money/percent formatting |
| **🔍 RFM Quantile Explorer** | Multiselect segment filter + R/F/M score range sliders + 2 Plotly scatter plots (Recency×Frequency bubble, Frequency×Monetary log-scale) + customer records table (top 250) |
| **🤖 K-Means & PCA Clustering** | 4 sub-tabs: 2D PCA scatter with cluster centroids, 3D interactive PCA, Elbow + Silhouette evaluation curves, behavioral Snake Plot |
| **🚀 Targeted Campaign Simulator** | 6 user inputs (baseline rate, target lift, cpc, gross margin, control AOV, targeted AOV) + 4 metric cards (Control Response, Targeted Response, Relative Lift, Net Profit Gain) + comparison bar chart (Conversions / Net Profit / ROI) + Z-test significance verdict |
| **📋 Strategic Playbook & Export** | 4 collapsible persona playbooks (objective, channels, offer, cadence, sample email subject lines, conversion driver) + CSV export button per segment |

## 🎨 Frontend-only styling

The dashboard uses a custom CSS block injected via `st.markdown(..., unsafe_allow_html=True)`:

```css
.kpi-card   { background: linear-gradient(135deg, #1e2638, #151b28);
              border: 1px solid #2d3748; border-radius: 10px;
              padding: 18px 22px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }
.kpi-title  { font-size: 13px; color: #a0aec0; text-transform: uppercase;
              letter-spacing: 0.05em; margin-bottom: 6px; }
.kpi-value  { font-size: 26px; font-weight: 700; color: #ffffff; }
.kpi-subtitle { font-size: 12px; color: #48bb78; margin-top: 4px; font-weight: 500; }
```

Dark theme with `background-color: #0e1117` on `.main`, Plotly charts use the `plotly_dark` template to match.

---

## 🧭 If you want the matching backend

The full project (frontend + backend + README + bug-fix report) is in:

- `download/rfm_python_v3_fixed/` — the most recent, fully fixed version (recommended)
- `download/rfm_python_full/` — same content, slightly different folder name
- `download/rfm_nextjs_full/` — the Next.js/TypeScript web app version (different stack entirely)

This `rfm_frontend_only/` folder is just `app.py` pulled out for quick reference.
