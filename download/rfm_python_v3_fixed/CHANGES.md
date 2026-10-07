# What's in this version (`rfm_python_v3_fixed`)

This folder is the **merged** result of two earlier passes:

1. **`rfm_python_fixes/`** — my first bug-fix pass against the original Python upload (3 bugs).
2. **The "refined, production-grade, error-free" upload** — a second pass by someone else that claimed to fix everything but actually re-introduced the critical bug and stripped a ton of functionality.

This `v3_fixed` keeps the **real** improvements from the second upload and **re-applies** the bug fixes the second upload dropped.

---

## ✅ Improvements kept from the "refined" upload (the 3 real ones)

| File | Improvement | Why it's worth keeping |
|------|-------------|------------------------|
| `src/rfm_analysis.py` | `pd.qcut(..., duplicates="drop")` on all three scoring calls | Even though `rank(method="first")` already produces unique ranks, `duplicates="drop"` is belt-and-suspenders hardening — it turns a `ValueError: Bin edges must be unique` into a graceful collapse on degenerate inputs (e.g. a test dataset where every customer has the same Recency). |
| `src/data_processing.py` | `df_clean["CustomerID"].astype(float).astype(int).astype(str)` (was just `astype(int).astype(str)`) | The CSV column may already be `float64` (NaN forces upcast), in which case `astype(int)` first needs the float→int normalization. The extra `float` step means the cast works no matter what the input dtype is — int, float, str, or object-mixed. |
| `src/config.py` | Pre-create `RAW_DATA_DIR / PROCESSED_DATA_DIR / REPORTS_DIR / FIGURES_DIR / NOTEBOOKS_DIR` at import time | Eliminates a class of `FileNotFoundError` on first run. Every writer still calls `mkdir(parents=True, exist_ok=True)` for safety, but now there's no chance of a missing parent at any code path. |
| `src/clustering.py` | `sample_size = 1500 if len(...) > 1500 else None` pattern for `silhouette_score` | Functionally equivalent to `min(1500, len(...))` but more readable — explicitly says "no sampling" for small datasets instead of "sample the entire dataset". |

## 🐛 Bugs from the "refined" upload that I had to **re-fix**

These were fixed in `rfm_python_fixes/` but the "refined" upload either didn't apply them or reverted them.

### Bug A — CRITICAL: `simulate_campaign_ab_test` still hardcodes economic inputs

**The "refined" upload** (lines 793–796 of `marketing_strategy.py`):
```python
cpc_email = 0.05
aov_control = 65.00
aov_targeted = 82.50
margin = 0.45
```

The function signature was never updated to accept these as parameters, and the Streamlit call site only passes `baseline_response_rate` + `target_lift_pct`. Result: the simulator's ROI numbers are frozen at `cpc=0.05` and `margin=0.45` no matter what.

**This `v3_fixed` version** restores the parameterized signature:
```python
def simulate_campaign_ab_test(
    rfm_df, baseline_response_rate=0.032, target_lift_pct=15.0,
    sample_split=0.5, random_state=42,
    cpc_email=0.05,         # ← now a parameter
    margin=0.45,            # ← now a parameter
    aov_control=65.00,       # ← now a parameter
    aov_targeted=82.50,     # ← now a parameter
) -> Dict:
```
plus the input validation, zero-control-rate guard, and lift-clipping that the upload didn't add.

### Bug B — CRITICAL: The Streamlit UI was stripped of the campaign simulator's economic inputs

**The "refined" upload** (`app.py` Tab 4, ~30 lines total) collected only `base_rate` and `target_lift` and showed 4 metric cards. It removed:
- the `cpc_cost` slider
- the `gross_margin` slider
- the AOV inputs
- the bar chart comparing control vs treatment on conversions / profit / ROI
- the statistical-significance verdict

This `v3_fixed` version restores the full Tab 4: 6 economic inputs, 4 metric cards, the comparison bar chart, and the Z-test verdict.

### Bug C — The frontend lost 80% of its visualizations

The "refined" `app.py` was reduced to ~125 lines from ~540 in the original. It lost:

| Original feature | Status in "refined" upload | Status in `v3_fixed` |
|-------------------|-----------------------------|----------------------|
| KPI cards (4, formatted) | Reduced to 4 plain numbers, no formatting | Restored with `$X.XXM` / thousands formatting |
| Pareto bar chart (customer vs revenue share per persona) | Removed | Restored |
| Revenue composition donut | Removed | Restored |
| Cluster summary table with money/percent formatting | Removed formatting | Restored |
| RFM Quantile Explorer — R/F/M score sliders | Removed (no sliders) | Restored |
| RFM Explorer — Recency×Frequency bubble chart | Removed | Restored |
| RFM Explorer — Frequency×Monetary log-scale scatter | Removed | Restored |
| K-Means tab — 2D PCA scatter with cluster centroids | Removed (only basic scatter) | Restored |
| K-Means tab — 3D interactive PCA scatter | Removed | Restored |
| K-Means tab — Elbow + Silhouette curves + metrics table | Removed | Restored |
| K-Means tab — Snake plot (standardized RFM profiles) | Removed | Restored |
| Campaign Simulator — full A/B comparison bar chart | Removed | Restored |
| Campaign Simulator — statistical significance verdict | Removed | Restored |
| Playbook — sample email subject lines | Removed | Restored |
| Playbook — cadence + conversion driver | Removed | Restored |
| CSV export | Restored (kept) | Restored (kept) |

The "refined" `src/visualization.py` similarly dropped 6 of 8 plot functions. This `v3_fixed` keeps all 8 publication-grade figures.

### Bug D — Dead code: `RFM_SEGMENT_MAP` in `config.py`

The "refined" upload **kept** the regex-based segment map in `config.py` even though nothing imports it (`assign_rfm_segments` uses its own if/elif ladder). This `v3_fixed` removes it again and leaves the deprecation note.

### Bug E — `simulate_full_segmented_rollout` still hardcodes the magic `1.15` AOV uplift

The "refined" upload (line 855 of `marketing_strategy.py`):
```python
incremental_rev = (target_conv * (avg_aov * 1.15)) - (base_conv * avg_aov)
```

This `v3_fixed` parameterizes it as `targeted_aov_uplift_pct: float = 15.0` and computes `avg_aov * (1.0 + targeted_aov_uplift_pct / 100.0)`.

### Bug F — No edge-case guards on the A/B simulator

The "refined" upload's `simulate_campaign_ab_test` would crash on:
- `control_rate == 0` (zero control conversions simulated) → `rel_lift = (abs_lift / 0) * 100` raises `ZeroDivisionError`
- `baseline_response_rate * (1 + target_lift_pct/100) >= 1.0` → `np.random.binomial(n, p)` raises `ValueError` because `p` must be in `[0, 1]`
- `n_control == 0` or `n_treatment == 0` → division by zero on the rate calculations
- `pooled_p == 0` or `pooled_p == 1` → `se == 0`, then `z_stat = ... / 0` (this one was guarded as `if se > 0 else 0`, but only by luck)

This `v3_fixed` version guards all four explicitly:
```python
if n_control == 0 or n_treatment == 0:
    raise ValueError(...)
if not (0.0 < baseline_response_rate < 1.0):
    raise ValueError(...)
targeted_rate_calibrated = min(max(targeted_rate_calibrated, 1e-6), 0.9999)
rel_lift = (abs_lift / control_rate) * 100.0 if control_rate > 0 else 0.0
if 0 < pooled_p < 1: ... else: z_stat = 0.0; p_val = 1.0
```

---

## 📋 Final file inventory (13 files)

```
rfm_python_v3_fixed/
├── README.md                 ← setup + module reference
├── BUGFIX_REPORT.md          ← original 3-bug write-up (Bug #1, #2, #3 from rfm_python_fixes)
├── CHANGES.md                ← THIS file — what changed in v3 vs the "refined" upload
├── requirements.txt
├── app.py                    ← Streamlit dashboard with all 5 tabs restored
├── run_pipeline.py           ← CLI orchestrator with honest retention print
└── src/
    ├── __init__.py
    ├── config.py             ← RFM_SEGMENT_MAP removed; auto-create dirs at import
    ├── data_processing.py    ← float→int→str CustomerID type safety
    ├── rfm_analysis.py       ← pd.qcut with duplicates='drop'
    ├── clustering.py         ← silhouette_score with sample_size=None for small data
    ├── marketing_strategy.py ← parameterized cpc/margin/AOV + edge-case guards + smoke test
    ├── data_generator.py     ← unchanged
    └── visualization.py      ← all 8 publication plots (not the 2-plot stripped version)
```

---

## 🧪 How to verify

```bash
# 1. Smoke test the parameterized A/B simulator (no Streamlit needed)
python -m src.marketing_strategy
# Expected: "OK — parameters now flow through correctly."

# 2. Run the full pipeline (will create dirs automatically now thanks to the
#    config.py improvement — no need to pre-create anything)
python run_pipeline.py --regenerate
# Expected output line (from the BUGFIX_REPORT.md fix):
#   "Cleaned records retained: ~54,000 / ~60,000 (~90.x% retention, ~6,000 rows removed —
#    ~4,800 missing CustomerID + ~1,200 cancellations/non-positive)"

# 3. Launch the dashboard and confirm all 5 tabs work
streamlit run app.py
# - Tab 1 (Executive): 4 KPI cards + Pareto bar + donut + cluster table
# - Tab 2 (RFM Explorer): segment multiselect + R/F/M sliders + 2 scatter plots + records table
# - Tab 3 (K-Means): 2D PCA + 3D PCA + Elbow/Silhouette + Snake plot (4 tabs)
# - Tab 4 (Campaign): 6 economic inputs + 4 metrics + comparison bar chart + significance verdict
# - Tab 5 (Playbook): 4 personas with all fields + CSV export
```

---

## 🧭 If you want to diff against the "refined" upload

The fastest way to see what changed:

```bash
diff -ru path/to/refined_upload/ rfm_python_v3_fixed/
```

The biggest deltas will be:
- `app.py` — ~125 lines → ~540 lines (restored visualizations + economic inputs)
- `src/visualization.py` — 2 plot functions → 8 plot functions
- `src/marketing_strategy.py` — 4 hardcoded consts → 4 parameters + edge-case guards
- `src/config.py` — RFM_SEGMENT_MAP dict present → removed + deprecation note + auto-dir creation
