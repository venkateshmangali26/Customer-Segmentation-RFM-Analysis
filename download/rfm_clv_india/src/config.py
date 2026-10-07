import sys
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

# Pre-create all output directories at import time so downstream modules
# can write to RAW_DATA_FILE / CLEANED_DATA_FILE / RFM_DATA_FILE / etc.
# without each one having to mkdir() at every code path. This eliminates
# a class of FileNotFoundError bugs on first run.
for _d in (RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR, NOTEBOOKS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# File Paths
RAW_DATA_FILE = RAW_DATA_DIR / "ecommerce_transactions.csv"
CLEANED_DATA_FILE = PROCESSED_DATA_DIR / "cleaned_transactions.csv"
RFM_DATA_FILE = PROCESSED_DATA_DIR / "customer_rfm_segmented.csv"
CLUSTER_METRICS_FILE = REPORTS_DIR / "cluster_profiles.csv"
CAMPAIGN_SUMMARY_FILE = REPORTS_DIR / "campaign_simulation_results.csv"

# Hyperparameters & Constants
RANDOM_SEED = 42
DEFAULT_N_TRANSACTIONS = 60000  # >= 50,000 records
DEFAULT_N_CUSTOMERS = 6500

# Clustering Settings
K_MIN = 2
K_MAX = 9
DEFAULT_OPTIMAL_K = 4

# ============================================================================
# INDIA-SPECIFIC CONFIGURATION
# ============================================================================

# Currency: Indian Rupee (INR). 1 USD ≈ ₹83 (as of late 2024).
CURRENCY_SYMBOL = "₹"
CURRENCY_CODE = "INR"
CURRENCY_NAME = "Indian Rupee"

# Indian e-commerce economic defaults (used by marketing_strategy.py)
# These reflect typical Indian D2C / marketplace seller economics.
DEFAULT_CPC_INR = 0.50          # ₹0.50 per SMS/WhatsApp message (bulk rate)
DEFAULT_GROSS_MARGIN = 0.35     # 35% — Indian D2C margins are thinner than West
DEFAULT_AOV_CONTROL_INR = 900.00     # ₹900 typical Indian e-commerce AOV
DEFAULT_AOV_TARGETED_INR = 1350.00  # ₹1350 with cross-sell + festival bundling

# Indian festival calendar — drives seasonality in the data generator.
# Each entry: (month, sales_boost_factor, festival_name)
# November (Diwali) is the single biggest e-commerce week of the year in India.
INDIAN_FESTIVAL_CALENDAR = [
    (1, 1.25, "Republic Day Sale"),                  # Jan 26
    (3, 1.20, "Holi Festival Sale"),                 # March (varies)
    (8, 1.30, "Independence Day + Raksha Bandhan"),  # Aug 15 + mid-Aug
    (10, 1.45, "Navratri & Dussehra Sale"),          # Oct (varies)
    (11, 1.80, "Diwali Mega Sale"),                  # Nov — biggest e-commerce week
    (12, 1.30, "Christmas & Year-End Sale"),         # Dec
]

# Indian number formatting helpers — lakh (1L = 100,000) and crore (1Cr = 10M)
# are the natural Indian number scales. Use these in display formatting.
LAKH = 100_000      # 1,00,000
CRORE = 10_000_000  # 1,00,00,000

def format_inr(amount: float, use_indian_scale: bool = True) -> str:
    """Format an amount as an Indian Rupee string.

    Args:
        amount: numeric amount in INR
        use_indian_scale: if True, large amounts use lakh/crore notation
            (₹1.50 Cr, ₹25.00 L) — the natural Indian format. If False,
            uses Western M/B notation (₹1.50M, ₹25.00K).
    """
    if use_indian_scale:
        if abs(amount) >= CRORE:
            return f"₹{amount/CRORE:.2f} Cr"
        if abs(amount) >= LAKH:
            return f"₹{amount/LAKH:.2f} L"
        return f"₹{amount:,.0f}"
    else:
        if abs(amount) >= 1_000_000:
            return f"₹{amount/1_000_000:.2f}M"
        if abs(amount) >= 1_000:
            return f"₹{amount/1_000:.1f}K"
        return f"₹{amount:.2f}"

# ---------------------------------------------------------------------------
# DEPRECATED — DO NOT IMPORT.
#
# `RFM_SEGMENT_MAP` was a regex-based segment map intended to drive segmentation,
# but `src/rfm_analysis.py::assign_rfm_segments()` actually uses its own hand-
# written if/elif ladder. The two definitions also disagreed in subtle cases
# (e.g. the regex `[1-2][1-2][1-2]` matches "111" which the if-chain routes to
# "Lost" first). To remove the ambiguity and the dead-code hazard, this map has
# been removed.
#
# If you want to re-introduce a data-driven segment table, build it as a list of
# (r_range, f_range, m_range, label) tuples in priority order and consume it
# from `assign_rfm_segments`. Do not use regexes — they make overlapping rules
# hard to reason about.
# ---------------------------------------------------------------------------
