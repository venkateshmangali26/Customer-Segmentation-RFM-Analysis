# Bug-Fix Report — Customer Segmentation & RFM Analysis (Python)

I audited all 9 files you uploaded (`app.py`, `run_pipeline.py`, and `src/{config,data_processing,rfm_analysis,clustering,marketing_strategy,data_generator,visualization}.py`). Below is every bug I found, why it matters, and which file in this folder contains the fix.

---

## Bug #1 — CRITICAL: Streamlit UI sliders had zero effect on the campaign simulation

**Where:** `app.py` (Tab 4) and `src/marketing_strategy.py::simulate_campaign_ab_test`

**Symptom:**
The "Targeted Campaign Simulator" tab collected four economic inputs from the user:

```python
cpc_cost      = st.number_input("Cost per Outreach Message ($)", 0.01, 1.00, 0.05, 0.01)
gross_margin  = st.slider("Product Gross Margin (%)", 20, 80, 45, 5) / 100.0
```

But the call site only forwarded two of them:

```python
ab_res = simulate_campaign_ab_test(
    rfm_df,
    baseline_response_rate=base_rate,
    target_lift_pct=target_lift,
)
```

Inside `simulate_campaign_ab_test`, the function then **hard-coded** the economics:

```python
cpc_email    = 0.05      # ignores user's cpc_cost
aov_control  = 65.00     # ignores user
aov_targeted = 82.50     # ignores user
margin       = 0.45      # ignores user's gross_margin
```

**Impact:** Moving the "Cost per Outreach Message" slider from $0.05 → $0.50 (10× higher) had **no effect** on the displayed `control_cost_usd`, `treatment_cost_usd`, `control_roi_pct`, `treatment_roi_pct`, or `profit_gain_usd` — they all still used $0.05. Same for the gross-margin slider (still used 45%). The simulator was effectively decorative for those inputs.

**Fix:**
1. In `src/marketing_strategy.py`, added `cpc_email`, `margin`, `aov_control`, and `aov_targeted` as real keyword parameters on `simulate_campaign_ab_test` (with the original values as defaults, so existing callers that don't pass them keep working). The function body now uses the parameters instead of the constants.
2. Did the same for `simulate_full_segmented_rollout` (it had a magic `1.15` AOV uplift factor — now parameterized as `targeted_aov_uplift_pct`).
3. In `app.py`, wired `cpc_cost`, `gross_margin`, and two new AOV inputs through to the call site:

   ```python
   ab_res = simulate_campaign_ab_test(
       rfm_df,
       baseline_response_rate=base_rate,
       target_lift_pct=target_lift,
       cpc_email=cpc_cost,
       margin=gross_margin,
       aov_control=aov_control_in,
       aov_targeted=aov_targeted_in,
   )
   ```
4. The result dict now echoes `cpc_email_usd`, `gross_margin_pct`, `aov_control_usd`, `aov_targeted_usd` so the UI can show the values used.

**Hardening added while I was in there:**
- Validation: `baseline_response_rate` must be in `(0, 1)`; sample split must produce non-empty control/treatment groups.
- Edge cases: if `pooled_p` is 0 or 1 (no conversions anywhere, or everyone converted), the Z-test standard error would be 0 → division-by-zero. Now guarded, returns `z_stat=0`, `p_val=1`.
- If `targeted_rate_calibrated` ends up ≥ 1 (e.g. baseline 6% + 95% lift), `np.random.binomial` would have errored. Now clipped to `(1e-6, 0.9999)`.
- If `control_rate == 0` (no control conversions simulated), `rel_lift = abs_lift / control_rate * 100` would have crashed. Now guarded, returns 0.

**Smoke test** at the bottom of `marketing_strategy.py`:

```python
res_default = simulate_campaign_ab_test(fake)
res_user    = simulate_campaign_ab_test(fake, cpc_email=0.50, margin=0.30)
assert res_user["control_cost_usd"] > res_default["control_cost_usd"]
```

Run with `python src/marketing_strategy.py` to confirm parameters propagate.

---

## Bug #2 — Reporting: "retention %" was wrong by ~8 percentage points

**Where:** `run_pipeline.py`, Step 2/6 print

**Original:**
```python
print(f" Cleaned records retained: {cleaning_stats['retained_clean_records']:,} "
      f"({100 - cleaning_stats['pct_missing_customer_ids']:.1f}% retention)")
```

`pct_missing_customer_ids` is the share of **raw rows with missing CustomerID** (≈ 8% in the synthetic generator). But the cleaning step also removes:
- All cancellation rows (`InvoiceNo` starts with "C" or `Quantity <= 0`) — another ~2.5%.
- Rows with `UnitPrice <= 0` (the generator sets ~0.2% of unit prices to 0 for "promo" rows).

So actual retention = `retained_clean_records / initial_records` ≈ 90%, but the original print computed `100 - 8 = 92.0%` and called it "retention". The displayed number was always higher than reality, and the discrepancy scaled with cancellation/promo rates.

**Fix in `run_pipeline.py`:**
```python
actual_retention_pct = (retained_records / initial_records * 100.0) if initial_records > 0 else 0.0
records_removed = initial_records - retained_records
print(
    f" Cleaned records retained: {retained_records:,} / {initial_records:,} "
    f"({actual_retention_pct:.1f}% retention, {records_removed:,} rows removed — "
    f"{cleaning_stats['missing_customer_ids']:,} missing CustomerID + "
    f"{cleaning_stats['cancelled_records']:,} cancellations/non-positive)"
)
```

No change needed in `data_processing.py` — its `summary` dict already exposes both `initial_records` and `retained_clean_records`.

---

## Bug #3 — Dead code: `RFM_SEGMENT_MAP` defined but never used

**Where:** `src/config.py`

`config.py` defined a regex-based segment map:
```python
RFM_SEGMENT_MAP = {
    r"[4-5][4-5][4-5]": "Champions",
    ...
    r"111": "Lost",
}
```

But `src/rfm_analysis.py::assign_rfm_segments()` never imports or references `RFM_SEGMENT_MAP` — it uses its own hand-written if/elif ladder. Two parallel definitions of the same business logic is a maintenance hazard: someone editing the regex map would assume their change took effect, but it silently wouldn't. The two definitions also disagreed in subtle cases (e.g. the regex `[1-2][1-2][1-2]` matches "111" which the if-chain routes to "Lost" first).

**Fix in `src/config.py`:** Removed the dict entirely and replaced it with a deprecation comment that (a) flags that it was dead code, (b) explains why it diverged from the if-chain, and (c) tells future maintainers how to re-introduce a data-driven segment table safely (as ordered tuples, not regexes).

---

## Minor improvements applied along the way

These aren't bugs per se, but they were small fragilities in the same files I was already touching:

| File | Change |
|------|--------|
| `app.py` Tab 1 | `vip_rev = cluster_profiles.loc[cluster_profiles["Cluster_Persona"] == "VIP Champions", "TotalRevenue"].sum()` would silently return 0 if the persona wasn't labeled exactly "VIP Champions" (e.g. after a re-run with different k). Wrapped with `if vip_mask.any()` guard. |
| `app.py` Tab 2 | The `multiselect` default `["Champions", "Loyal Customers", "At Risk"]` would crash if any of those segments didn't exist in `rfm_df` (Streamlit errors if `default` contains values not in `options`). Now defaults to whichever of those three are actually present in the data, capped at 3. Also: clearing the multiselect used to silently filter to zero rows ("0 of N customers"). Now treats empty selection as "show all" with an info toast. |
| `marketing_strategy.py` | `simulate_full_segmented_rollout` used `int(n_cust * base_rate)` which truncates (e.g. 3.5 → 3). Switched to `int(round(...))` so 3.5 → 4, removing a small systematic downward bias in conversion counts. |

---

## What I did **not** change (and why)

- **`src/data_processing.py`** — the cleaning logic itself is correct; only the *reporting* of retention in `run_pipeline.py` was wrong, and that's fixed there.
- **`src/rfm_analysis.py`** — the if/elif segment ladder is internally consistent with the (now-removed) regex map. No bugs.
- **`src/clustering.py`** — KMeans/PCA logic is sound. The `int(vip_cluster)` casts work because numpy int64 hashes the same as native int. The unused `i` in the iteritems loop is style, not a bug.
- **`src/data_generator.py`** — generation is sound; the `np.random.randint(min_rec, max(min_rec + 1, min(max_rec, total_days)))` guard correctly handles the case where `max_rec > total_days`.
- **`src/visualization.py`** — all 8 plots are correct. The legend code in `plot_clustering_evaluation` looked suspicious (fake `Line2D` for the k=4 indicator) but is actually fine because `lines + [fake_line]` has 3 handles matching the 3 labels.

---

## Files in this folder

```
rfm_python_fixes/
├── app.py                         # Fixed Tab 4 wiring + Tab 1/2 hardening
├── run_pipeline.py                # Fixed retention % print (Step 2/6)
└── src/
    ├── config.py                  # Removed dead RFM_SEGMENT_MAP
    └── marketing_strategy.py      # Parameterized cpc/margin/AOV + edge-case guards + smoke test
```

The other 6 source files (`data_processing.py`, `rfm_analysis.py`, `clustering.py`, `data_generator.py`, `visualization.py`, `requirements.txt`) are unchanged from your upload — drop them in alongside these three and the project will run as before, but with a working campaign simulator and an honest retention metric.

## How to verify the fix

After replacing the three files:

```bash
# 1. Confirm the parameter wiring works (no Streamlit needed):
python src/marketing_strategy.py
# Expected: prints "OK — parameters now flow through correctly."

# 2. Re-run the full pipeline to see the corrected retention print:
python run_pipeline.py --regenerate
# Expected: "Cleaned records retained: ~54,000 / ~60,000 (~90.x% retention, ..."

# 3. Launch Streamlit and verify the simulator responds to slider changes:
streamlit run app.py
# In Tab 4, drag "Cost per Outreach Message" from $0.05 → $0.50.
# Expected: control_cost_usd and treatment_cost_usd jump 10x, ROI drops sharply.
```
