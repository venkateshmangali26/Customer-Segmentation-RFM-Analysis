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
