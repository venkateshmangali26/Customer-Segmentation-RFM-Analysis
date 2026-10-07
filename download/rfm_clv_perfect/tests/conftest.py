"""Pytest configuration. Adds the project root to sys.path so tests can
import the src package without requiring PYTHONPATH to be set."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
