# Customer Segmentation, RFM & Predictive CLV — **India Edition**

The complete perfected platform (`rfm_clv_perfect`) — BG/NBD + Gamma-Gamma CLV modeling, K-Means clustering, cohort retention heatmaps, Prophet sales forecasting, colorful Streamlit dashboard — **localized for the Indian e-commerce market**.

All the bug fixes from the perfected version are preserved. On top of that, every data layer has been adapted to reflect how Indian D2C / marketplace sellers actually operate.

---

## 🇮🇳 What's been localized

### 1. Product catalog → Indian SKUs (`src/data_generator.py`)

The original catalog was British wholesale homewares. Replaced with **8 Indian e-commerce categories** spanning 50+ realistic SKUs at INR price points typical of Flipkart / Amazon.in / Meesho / Myntra sellers:

| Category | Example SKUs | Price range |
|----------|--------------|--------------|
| **Mobile Accessories** | USB-C cables, Bluetooth earbuds, 20W chargers, power banks, tempered glass | ₹199–₹1499 |
| **Fashion** | T-shirts, Anarkali Kurti, slim-fit jeans, cotton sarees, sports shoes, leather wallets, watches, sunglasses | ₹349–₹1499 |
| **Home & Kitchen** | Stainless steel thali sets, non-stick tawa, glass tea cups, water bottles | ₹199–₹599 |
| **Home Decor** | Brass diyas, mandir wall hangings, wooden wall clocks, cushion covers | ₹249–₹799 |
| **Grocery** | Basmati rice 5kg, sunflower oil, mixed pickles, masala tea, pure ghee, saffron, atta, cashews | ₹99–₹449 |
| **Beauty** | Ayurvedic face wash, coconut hair oil, herbal shampoo, henna, rose water toner, neem soap | ₹99–₹299 |
| **Ayurveda** | Ashwagandha capsules, Triphala powder, Chyawanprash, Tulsi drops | ₹199–₹549 |
| **Books & Toys** | Bhagavad Gita, yoga manual, Indian cookery, Panchatantra tales, wooden rattle, chess set, kite-flying set | ₹99–₹699 |
| **Festival Specials** ⭐ | Diwali gift hamper, Rakhi set with sweets, Rangoli colors, Holi color powder, Pooja thali, festive sweets box | ₹199–₹999 |

### 2. Geography → Indian states (`src/data_generator.py`)

Replaced the UK-heavy country distribution (UK = 85%) with a realistic **Indian state distribution** based on e-commerce buyer population share:

| State | Share | Major city |
|-------|-------|-----------|
| Maharashtra | 15.5% | Mumbai, Pune |
| Delhi | 8.5% | New Delhi |
| Karnataka | 9.0% | Bangalore |
| Tamil Nadu | 8.5% | Chennai |
| Telangana | 6.0% | Hyderabad |
| Gujarat | 7.0% | Ahmedabad, Surat |
| Uttar Pradesh | 9.0% | Lucknow, Noida |
| West Bengal | 6.0% | Kolkata |
| Rajasthan | 4.5% | Jaipur |
| … + 14 more states | | |

### 3. Customer names → Indian (`src/data_generator.py`)

Replaced British first/last names with **Indian names** across 4 regional pools:

- **North Indian**: Sharma, Verma, Gupta, Singh, Agarwal, Jain, Kapoor, Khanna, Mishra, Tiwari, Pandey, Tripathi…
- **South Indian**: Iyer, Iyengar, Nair, Menon, Reddy, Rao, Shetty, Murthy, Subramanian, Venkatesan, Pillai…
- **West Indian**: Patel, Shah, Desai, Mehta, Joshi, Gandhi, Modi, Dalal, Sanghvi, Patil, Kulkarni…
- **East Indian**: Das, Banerjee, Bhattacharya, Mukherjee, Chatterjee, Ghosh, Sengupta, Roy, Saha, Bose…

First names span 100+ common Indian male (Aarav, Vivaan, Aditya, Vihaan, Arjun, Sai, Reyansh, Ayaan, Krishna, Ishaan, Rohan, Aryan, Rahul, Karan, Sameer, Vikram, …) and female (Saanvi, Aanya, Aadhya, Anaya, Diya, Kiara, Pari, Myra, Anika, Navya, Aarohi, Riya, Sara, Ira, Ishita, Aditi, …) names.

### 4. Pricing scale → INR (`src/data_generator.py`, `src/marketing_strategy.py`, `src/config.py`)

Every economic parameter shifted from USD to INR scale:

| Parameter | USD (perfect version) | INR (India version) |
|-----------|---------------------|---------------------|
| Default cost per message | $0.05 | ₹0.50 (bulk SMS rate) |
| Default gross margin | 45% | 35% (Indian D2C margins thinner) |
| Default control AOV | $65 | ₹900 |
| Default targeted AOV | $82.50 | ₹1350 (cross-sell + festival bundling) |

### 5. Currency display → ₹ + lakh/crore (`src/config.py`, `app.py`)

- All `$` symbols in the UI replaced with `₹`
- Large amounts shown in **Indian lakh (L) / crore (Cr) notation** — the natural Indian number scale — instead of Western M/K:
  - Total Revenue: `₹1.50 Cr` (instead of `$1.50M`)
  - Projected 1-Yr CLV: `₹0.85 Cr`
  - Avg Customer Spend: `₹1,234` (no scaling needed)
- New helper `format_inr(amount, use_indian_scale=True)` in `config.py`
- Result dict keys renamed from `_usd` suffix to `_inr` suffix (e.g. `control_cost_usd` → `control_cost_inr`)

### 6. Festival seasonality → Indian calendar (`src/data_generator.py`, `src/config.py`)

The data generator now applies a **multiplicative sales boost** based on Indian festival months:

| Month | Festival | Sales boost |
|-------|----------|-------------|
| January | Republic Day Sale (Jan 26) | +25% |
| March | Holi Festival Sale | +20% |
| August | Independence Day + Raksha Bandhan | +30% |
| October | Navratri & Dussehra Sale | +45% |
| **November** | **Diwali Mega Sale** | **+80%** ← biggest week of the year |
| December | Christmas & Year-End Sale | +30% |

The sidebar shows this festival calendar with color-coded boost factors.

### 7. Payment methods → Indian mix (`src/data_generator.py`)

Each transaction now has a `PaymentMethod` column reflecting Indian payment culture:

| Method | Share | Notes |
|--------|-------|-------|
| UPI (PhonePe/GPay/Paytm) | 45% | Dominant in India |
| Credit/Debit Card | 20% | |
| COD (Cash on Delivery) | 25% | Still prevalent in Tier-2/3 |
| Net Banking | 5% | |
| Wallet | 5% | |

Plus an `IsCOD` boolean flag per order.

### 8. Marketing playbook → Indian channels + festivals (`src/marketing_strategy.py`)

Replaced Western channels (Meta Custom Audience, App Push Notifications, Account Concierge) with **Indian e-commerce reality**:

- **WhatsApp Business API** (huge in India for customer support + catalogs)
- **SMS** (still high-conversion in Tier-2/3 cities, cheaper than WhatsApp)
- **Flipkart/Amazon.in retargeting** (instead of generic "Retargeting")
- **Instagram DM** (huge among 18-35 demographic)
- **WhatsApp Broadcast** (opt-in only, for hibernating customers)

Sample email subject lines now reference Indian festivals and Indian payment culture:

- 🪔 *"Aapke liye special: VIP Diwali preview is live — shop 24 hrs before everyone else"*
- *"Aapke liye chune gaye products + ₹100 extra cashback on UPI payment"*
- *"Aap hamare yaar hain — ₹200 off on your next order, COD available"*
- *"🏭 Warehouse Clearance: Up to 70% off — Diwali Sale ends Sunday"*
- *"Holi ke rang, savings ke sang: 50% off on all festive specials"*

Offers use INR amounts appropriate to Indian AOVs (₹100–₹500 discounts, ₹299–₹4999 free-delivery thresholds).

### 9. RFM Explorer → Indian state filter (`app.py`)

The RFM Quantile Explorer now has a **5th filter column** for Indian State, alongside the segment multiselect and R/F/M score sliders. Customers can be filtered by Maharashtra + Delhi + Karnataka etc.

### 10. Sidebar → Festival calendar widget (`app.py`)

A new **"🪔 Indian Festival Calendar"** section in the sidebar lists the 6 festival months with color-coded boost badges:
- 🟧 Orange for the biggest boost (+80% Diwali)
- 🟦 Blue for medium boosts (+25–45%)
- ⬜ Gray for minor boosts

This makes the seasonality visible at a glance.

### 11. Per-customer state aggregation (`src/rfm_analysis.py`)

`calculate_rfm_metrics` now also aggregates `State` per customer (mode of the customer's transaction states) so the RFM DataFrame has a `State` column. Defensive: if the column doesn't exist (legacy CSVs), it skips gracefully.

### 12. Tests updated to INR scale (`tests/test_marketing.py`, `tests/test_clv.py`)

- `fake_rfm_df` fixture's `AOV` column now uses `np.random.uniform(300, 2500)` (₹ scale) instead of `(30, 200)` ($ scale)
- `test_simulate_campaign_ab_test_respects_cpc_parameter` uses ₹0.50 / ₹5.00 (10x ratio) instead of $0.05 / $0.50
- `test_simulate_campaign_ab_test_respects_aov_parameters` uses ₹200/₹2000 instead of $20/$200
- All result dict key assertions updated from `_usd` suffix to `_inr`
- CLV synthetic test data uses `np.random.gamma(2.0, 450.0)` (mean ₹900) instead of `gamma(2.0, 25.0)` (mean $50)

---

## 📁 Project layout (25 files, same as `rfm_clv_perfect`)

```
rfm_clv_india/
├── README.md                          ← you are here (India-specific)
├── requirements.txt                   ← same deps as perfected version
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── app.py                             ← ₹ formatting, festival calendar sidebar, state filter
├── run_pipeline.py                    ← same 9-stage orchestrator
├── .github/workflows/ci.yml
├── prisma/schema.prisma               ← (legacy)
├── src/
│   ├── __init__.py
│   ├── config.py                       ← + INR constants, festival calendar, format_inr() helper
│   ├── data_processing.py              ← unchanged (CustomerID type safety preserved)
│   ├── rfm_analysis.py                ← + State aggregation per customer
│   ├── clustering.py                  ← unchanged
│   ├── marketing_strategy.py          ← India-themed playbooks + INR defaults + _inr keys
│   ├── data_generator.py              ← India-themed: catalog, states, names, festivals, UPI/COD
│   ├── visualization.py               ← unchanged
│   ├── clv_modeling.py                ← unchanged (math is currency-agnostic)
│   ├── cohort_analysis.py             ← unchanged
│   └── sales_forecasting.py           ← unchanged
└── tests/
    ├── conftest.py
    ├── test_rfm.py                     ← works on Indian data
    ├── test_clv.py                    ← ₹-scale synthetic data
    ├── test_clustering.py             ← unchanged
    ├── test_marketing.py              ← ₹-scale AOVs, _inr key assertions
    └── test_cohort_and_forecast.py    ← unchanged
```

---

## 🚀 Run

```bash
cd rfm_clv_india
pip install -r requirements.txt
pytest tests/ -v                       # 35+ tests, all adapted to INR scale
python run_pipeline.py --regenerate    # generates Indian e-commerce data
streamlit run app.py                   # opens http://localhost:8501
```

On first launch:
- The self-healing loader generates 50K Indian e-commerce transactions
- Cleans, computes RFM, trains K-Means, fits BG/NBD + Gamma-Gamma, computes cohort retention, fits sales forecast
- Dashboard opens with all 8 modules populated

### What you'll see different vs the global version

- **Sidebar festival calendar** showing Diwali (+80%), Republic Day (+25%), Holi (+20%), etc.
- **Total Revenue KPI** shows `₹X.XX Cr` (crore notation) instead of `$X.XX M`
- **Avg Customer Spend** is in ₹, typically ₹800–₹2500 range
- **CLV projections** are in ₹, with `₹X.XX Cr` for total cohort value
- **Campaign Simulator** defaults: ₹0.50/message cost, 35% margin, ₹900 control AOV, ₹1350 targeted AOV
- **RFM Explorer** has a 5th filter column for Indian State
- **Playbook** sample email subjects reference Diwali, Holi, Raksha Bandhan, UPI cashback, COD availability
- **Customer names** in the table are Indian (Aarav Sharma, Diya Patel, Krishna Iyer, Saanvi Reddy, etc.)

---

## 🇮🇳 Why these specific adaptations matter

### Currency scale
Indian e-commerce AOVs are ~10–15× smaller in USD-equivalent than mature Western markets (₹900 ≈ $11 vs $65). Showing numbers in USD would obscure the actual purchasing power context. The lakh/crore notation (1L = 100,000, 1Cr = 10,000,000) is what every Indian business stakeholder expects to see — using "₹1.50M" instead of "₹15 L" reads as foreign.

### Festival seasonality
Diwali (Oct/Nov) drives 30–40% of annual e-commerce GMV in India — the so-called "Diwali Sale week" is bigger than Black Friday + Cyber Monday combined for Indian sellers. Skipping this seasonality would make any sales forecast look reasonable on average but miss the actual peak that drives annual planning. The data generator now applies a +80% multiplicative boost to November transactions.

### Channels
Indian e-commerce is fundamentally mobile-first and WhatsApp-centric:
- WhatsApp has 500M+ users in India; WhatsApp Business API is the primary D2C customer-support channel
- SMS still converts well in Tier-2/3 cities where WhatsApp Business adoption is lower
- Email open rates in India are 30-40% lower than the West — but still worth it for retention
- Flipkart and Amazon.in have their own retargeting ecosystems distinct from Meta Ads
- Instagram DM is huge for fashion D2C brands targeting 18-35

The original playbook's "Meta Custom Audience Ads" and "App Push Notifications" miss where Indian customers actually are.

### Payment culture
India's payment mix is dominated by UPI (45%) since 2019, with COD still significant (25%) in Tier-2/3 where trust in advance payment is lower. The data generator now includes a `PaymentMethod` column so downstream analytics can break down CLV and churn by payment method.

### Margins
Indian D2C margins are typically 25-40% — thinner than mature Western D2C (40-55%) because of aggressive marketplace discounting (Flipkart's Big Billion Days, Amazon's Great Indian Festival push AOVs down via deep discounts). The default 35% margin reflects this reality.

---

## ✅ All bug fixes from `rfm_clv_perfect` are preserved

| Bug | Status in India version |
|-----|------------------------|
| `simulate_campaign_ab_test` parameterized economics | ✅ Fixed — and defaults now in INR |
| BG/NBD P(Alive) for x=0 customers | ✅ Fixed — Fader-Hardie closed form |
| BG/NBD expected purchases (canonical with `hyp2f1`) | ✅ Fixed |
| Gamma-Gamma MLE fit | ✅ Fixed |
| CustomerID type safety | ✅ Fixed |
| `pd.qcut` with `duplicates='drop'` | ✅ Fixed |
| RFM_SEGMENT_MAP dead code | ✅ Removed |
| Snake plot zero-std guard | ✅ Fixed |
| Empty multiselect = "show all" | ✅ Fixed |
| Cache invalidation button | ✅ Fixed |

Plus the new features: cohort retention heatmap, Prophet sales forecasting, Docker, CI/CD, 35+ pytest tests.

---

## 🧭 Suggested next moves

1. **Add a per-state CLV breakdown** — show projected CLV by Indian state (Tier-1 metros vs Tier-2/3) to inform regional marketing budget allocation
2. **Add a Diwali-specific forecast overlay** — highlight the Diwali week on the sales forecast chart with a vertical marker
3. **Add payment-method segmentation** — since UPI vs COD customers behave very differently (UPI customers have higher retention)
4. **Multi-language support** — Hindi subject lines for North, Tamil for Tamil Nadu, Bengali for West Bengal (currently English-only with Hindi/Hinglish sprinkled in)
5. **GST-aware pricing** — add GST (18% or 28% depending on category) to the displayed prices

Let me know which and I'll execute.
