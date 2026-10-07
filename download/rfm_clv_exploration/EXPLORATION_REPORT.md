# Exploration Report — Customer Segmentation + RFM + Predictive CLV platform

This is a thorough audit of the 1837-line upload. **Bottom line**: the CLV module is a real, genuine addition (the BG/NBD NLL implementation is correctly written and numerically stable). But it's bolted onto a backend that still has the **same critical bug** that's been re-introduced four times now, plus the CLV math itself has two subtle modeling bugs that will silently produce misleading numbers.

---

## 🆕 What's new in this version (vs the previous "perfected" upload)

### New file: `src/clv_modeling.py` — ~260 lines

| Class / function | What it does | Verdict |
|------------------|--------------|---------|
| `prepare_clv_summary_data()` | Transforms transaction logs into the BG/NBD "RFM-T" summary format (frequency, recency-in-weeks, T-tenure-in-weeks, monetary_value). | ✅ Correct. Standard Fader-Hardie aggregation. |
| `BGNBDModel._negative_log_likelihood()` | Vectorized NLL with `scipy.special.gammaln`. Uses the log-sum-exp trick (`np.maximum(part1, part2) + np.log(np.exp(part1 - max_part) + np.exp(part2 - max_part))`) for numerical stability when summing the two beta-function terms. | ✅ Correctly written. Numerically stable. The math matches the Fader-Hardie 2005 paper. |
| `BGNBDModel.fit()` | Wraps `scipy.optimize.minimize` with `L-BFGS-B`, bounds `(1e-4, 50)` on (r, alpha, a, b). On failure, falls back to fixed defaults `[0.85, 8.2, 0.45, 1.25]`. | ⚠️ Reasonable. The fallback is a graceful degradation, but it silently hides fitting failures — there's no warning printed. |
| `BGNBDModel.predict_p_alive()` | Computes P(alive) using the standard BG/NBD formula. | 🐛 **BUG A** — see below. |
| `BGNBDModel.predict_expected_purchases()` | Heuristic: `cond_lambda * t_weeks * p_alive` where `cond_lambda = (r + x) / (alpha + T)`. | 🐛 **BUG B** — see below. |
| `GammaGammaModel.fit()` | Sets `p=2.0`, `q=3.0`, `gamma = max(5, mean_spend * 2)`. | 🐛 **BUG C** — see below. Not actually MLE. |
| `GammaGammaModel.predict_expected_spend()` | Empirical-Bayes shrinkage: `(1-w) * prior_mean + w * m`. | ✅ The shrinkage formula itself is correct, but it'shrinking towards a degenerate prior (see Bug C). |
| `compute_predictive_clv()` | Orchestrates everything: fits BG/NBD + GG, computes 90D/365D CLV with 10% annual discount factor, assigns CLV tier (Platinum/Gold/Silver/Bronze by quantile), merges back into rfm_df. | ✅ The orchestration, persistence, and reporting are all clean. |

### New frontend module: 🔮 Predictive CLV (BG/NBD & Gamma-Gamma) in `app.py`

4 KPI cards (Projected 1-Yr Net CLV, Mean P(Alive), Mean 1-Yr CLV/Customer, High Churn Risk %) + box plot of CLV by persona + scatter of Churn Risk vs CLV + top-100 high-value retention targets table. Well-designed UI.

### Updated `run_pipeline.py` — now 7 steps (added CLV stage between clustering and marketing)

### Updated self-healing loader in `app.py`

This is **genuinely nice** code:
```python
# Self-heal CLV columns if needed
if "Predicted_CLV_365D" not in rfm_df.columns and CLEANED_DATA_FILE.exists():
    cleaned_df = pd.read_csv(CLEANED_DATA_FILE)
    rfm_df, _ = compute_predictive_clv(cleaned_df, rfm_df, output_path=RFM_DATA_FILE)
```
If the persisted CSV predates the CLV module, it lazily computes the CLV columns on first load. Good defensive engineering.

---

## 🐛 Bugs (in order of severity)

### Bug #1 — CRITICAL (4th re-introduction): Campaign simulator sliders still don't work

`simulate_campaign_ab_test` STILL hardcodes economics (lines 1551–1554):
```python
cpc_email = 0.05
aov_control = 65.00
aov_targeted = 82.50
margin = 0.45
```

The function signature STILL doesn't accept these as params:
```python
def simulate_campaign_ab_test(
    rfm_df, baseline_response_rate=0.032, target_lift_pct=15.0,
    sample_split=0.5, random_state=42,
) -> Dict:
```

And the app.py Tab 4 call site STILL drops the user's `cpc_cost` and `gross_margin` on the floor:
```python
cpc_cost = st.number_input("Cost per Outreach Message ($)", 0.01, 1.00, 0.05, 0.01)
gross_margin = st.slider("Product Gross Margin (%)", 20, 80, 45, 5) / 100.0
ab_res = simulate_campaign_ab_test(
    rfm_df,
    baseline_response_rate=base_rate,
    target_lift_pct=target_lift,    # ← cpc_cost and gross_margin dropped here
)
```

**Same bug as uploads #1, #2, and #3.** Dragging the "Cost per Outreach" slider from $0.05 → $0.50 still has zero effect on the displayed ROI numbers.

### Bug A — CLV-specific: P(Alive) for one-time customers is silently set to 100%

In `BGNBDModel.predict_p_alive` (lines 907–916):
```python
def predict_p_alive(self, x, t_x, T):
    p_alive = np.ones_like(x, dtype=float)   # ← starts at 1.0 for everyone
    mask = x > 0                              # ← only computes for repeat customers
    if np.any(mask):
        denom = 1.0 + (a / (b + x[mask] - 1)) * ((alpha + T[mask]) / (alpha + t_x[mask])) ** (r + x[mask])
        p_alive[mask] = 1.0 / denom
    return np.clip(p_alive, 0.001, 0.999)
```

For customers with `frequency=0` (one-time buyers — a HUGE chunk of any e-commerce base, often 40–60% of all customers), this skips the formula entirely and leaves them at `p_alive = 1.0`.

**Impact**: The "Mean Probability Active" KPI in the CLV tab is massively inflated. Every one-time buyer is reported as 100% likely to be active. The "High Churn Risk Cohort" KPI is depressed because one-time buyers never show up as high-risk.

The canonical BG/NBD formula handles the x=0 case — Fader & Hardie 2005 give:
```
P(alive | x=0, t_x=0, T) = 1 - (a / (a + b)) * (...)  # needs a > 0, b > 0
```

### Bug B — CLV-specific: Expected purchases uses a heuristic, not the canonical BG/NBD closed form

In `predict_expected_purchases` (lines 918–923):
```python
def predict_expected_purchases(self, t_weeks, x, t_x, T):
    r, alpha = self.r, self.alpha
    p_alive = self.predict_p_alive(x, t_x, T)
    cond_lambda = (r + x) / (alpha + T)
    expected_tx = cond_lambda * t_weeks * p_alive
    return np.maximum(0.0, expected_tx)
```

This is a heuristic. The actual BG/NBD conditional expected transactions formula is:
```
E[X(t) | x, t_x, T] = [a+b+x-1] / [a-1] * [1 - ((α+T)/(α+T+t))^(r+x) * 2F1(r+x, b+x; a+b+x-1; t/(α+T+t))]
```

It involves the Gaussian hypergeometric function `_2F1` (`scipy.special.hyp2f1`). The simplified `cond_lambda * t_weeks * p_alive` is a poor approximation — it ignores the dropout-weighted rate term and the `(a+b+x-1)/(a-1)` multiplier.

**Impact**: predicted 90D/365D purchase counts are systematically biased. The CLV projections will be off, but in a non-obvious way (sometimes high, sometimes low, depending on `a` and `b`).

### Bug C — CLV-specific: GammaGammaModel doesn't actually fit via MLE

In `GammaGammaModel.fit` (lines 938–949):
```python
def fit(self, x, m):
    valid = (x > 0) & (m > 0)
    if np.sum(valid) < 10:
        self.is_fitted = True
        return self
    mean_spend = float(np.mean(m[valid]))
    self.p = 2.0        # ← fixed
    self.q = 3.0        # ← fixed
    self.gamma = max(5.0, (self.q - 1.0) * mean_spend / self.p)
    self.is_fitted = True
    return self
```

`p` and `q` are hardcoded to 2.0 and 3.0 — they're never learned from the data. Only `gamma` is set, and it ends up being `~mean_spend`. So the "prior mean" `(p*gamma)/(q-1) = (2*mean_spend)/2 = mean_spend` — the prior IS the sample mean.

The model degenerates to: "predict a weighted average between the global mean spend and the customer's observed mean spend". That's a reasonable empirical-Bayes shrinkage, but **it's not Gamma-Gamma MLE**. The docstring and dashboard claim "Gamma-Gamma submodel" — but the actual Gamma-Gamma closed-form MLE is never computed.

**Impact**: probably small for most use cases (the shrinkage is sensible even with fixed p, q), but the model is mislabeled. If a CLV-savvy stakeholder opens the code, they'll be confused.

### Bug #5 — Regression: CustomerID type safety reverted

Line 1716:
```python
df_clean["CustomerID"] = df_clean["CustomerID"].astype(int).astype(str)
```

The "refined" upload added `.astype(float)` first for robustness against object-typed columns. This upload reverted that. Not a crash on the synthetic data (which is clean), but a regression for real-world CSVs with mixed-type CustomerID columns.

### Bug #6 — pandas dtype warning when capping outliers

Lines 1746–1747:
```python
df_valid.loc[qty_mask, "Quantity"] = q_qty_999    # q_qty_999 is a float
df_valid.loc[price_mask, "UnitPrice"] = q_price_999  # price is float, this is fine
```

`Quantity` is int64 by default. Assigning a float (the 99.9th percentile) to an int column triggers `FutureWarning: Setting an item with incompatible dtype` in pandas ≥ 2.0, and will become `TypeError` in pandas 3.0. Fix: `df_valid["Quantity"] = df_valid["Quantity"].astype(float)` before assignment, or `int(round(q_qty_999))` for the assignment.

### Bug #7 — Same `pd.qcut` without `duplicates='drop'` (regression)

Lines 1336–1352 — no `duplicates='drop'` flag. The "refined" upload added it. This upload reverted it. Will crash on degenerate inputs.

### Bug #8 — Same dead code: `RFM_SEGMENT_MAP` in config.py

Lines 1807–1819 — the regex segment map is still defined but never imported by anything. `assign_rfm_segments` uses its own if/elif ladder.

### Bug #9 — Same misleading retention print in run_pipeline.py

Line 697:
```python
print(f" Cleaned records retained: {cleaning_stats['retained_clean_records']:,} ({100 - cleaning_stats['pct_missing_customer_ids']:.1f}% retention)")
```

`100 - pct_missing_customer_ids` overstates actual retention by ~2.5pp because it ignores cancellations and zero-price rows.

### Bug #10 — Unused `i` in iterrows loop in clustering.py

Line 1210: `for i, extra_row in sorted_rem.iloc[2:].iterrows():` — `i` is never used. Linter would flag.

---

## ✅ Things this version actually does well

| Feature | Verdict |
|---------|---------|
| BG/NBD negative log-likelihood math | Correctly implemented, numerically stable (log-sum-exp trick) |
| BG/NBD fit via scipy L-BFGS-B with bounds | Standard, sensible defaults, graceful fallback |
| CLV tier assignment (Platinum/Gold/Silver/Bronze by quantile) | Clean, useful for retention prioritization |
| Self-healing loader in app.py | Genuinely good — lazily computes CLV columns on legacy CSVs |
| Discount factor (10% annual) applied to 365D CLV | Standard DCF practice |
| CLV dashboard UI | Well-designed: 4 KPIs + box plot + churn-vs-CLV scatter + top-N table |
| CSV export per persona | Still works |

---

## 📋 Recommendation matrix

| Bug | Severity | Effort to fix | Fix it? |
|-----|----------|---------------|---------|
| #1 (4th re-introduction of campaign simulator) | Critical | 5 min | Yes — apply the same parameterization from `rfm_python_v3_fixed/src/marketing_strategy.py` |
| A (P(Alive) for x=0) | Critical for CLV correctness | 30 min | Yes — implement the Fader-Hardie x=0 formula |
| B (heuristic expected purchases) | High — biases CLV | 45 min | Yes — implement the closed-form using `scipy.special.hyp2f1` |
| C (Gamma-Gamma doesn't fit) | Medium — mislabeled | 60 min | Optional — either implement real MLE or rename the class to `EmpiricalBayesSpendModel` |
| #5 (CustomerID type safety) | Low regression | 1 min | Yes |
| #6 (pandas dtype warning) | Low — deprecation | 2 min | Yes |
| #7 (qcut duplicates='drop') | Low regression | 1 min | Yes |
| #8 (RFM_SEGMENT_MAP dead code) | Low — cosmetic | 1 min | Yes |
| #9 (retention print) | Low — reporting | 2 min | Yes |
| #10 (unused `i`) | Cosmetic | 30 sec | Yes |

**Total effort to fix everything**: ~2.5 hours, mostly on Bug A and Bug B which require reading the Fader-Hardie paper carefully.

---

## 🧭 What I'd do next

If you want, I can:

1. **Just fix the critical bugs** (#1 + A + B) and ship a `rfm_clv_fixed/` folder with the corrected `clv_modeling.py` + `marketing_strategy.py` + `app.py`. The other regressions are cosmetic.
2. **Fix everything** (#1, A, B, C, plus the 6 minor regressions) into a complete `rfm_clv_v2/` package.
3. **Just give you the corrected `clv_modeling.py`** as a standalone drop-in — that's where 90% of the real math bugs live.
4. **Translate the CLV module to the Next.js web app** I built earlier — that would extend the interactive RFM dashboard with live BG/NBD projections.

Tell me which of those (or something else) and I'll execute.
