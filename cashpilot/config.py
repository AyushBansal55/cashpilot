"""
Central configuration for Cashpilot.

Keeping model names and tunable constants in one place makes it trivial to swap
models or adjust thresholds without hunting through the codebase. No secrets
live here — the Gemini API key is read from the environment (.env), never
committed.
"""

import os

# Gemini model used by all agents. `gemini-flash-latest` is fast and cheap,
# which keeps the multi-agent loop responsive during the demo. Swap to a Pro
# model later if reasoning quality on the advisor step needs a boost.
MODEL = os.getenv("CASHPILOT_MODEL", "gemini-flash-latest")

# --- Forecasting / risk thresholds (used from Phase 3 onward) ---------------
# Cash position (EUR) below which a day is flagged as "at risk".
CASH_RISK_THRESHOLD = float(os.getenv("CASHPILOT_RISK_THRESHOLD", "5000"))

# Forecast horizon in days.
FORECAST_HORIZON_DAYS = int(os.getenv("CASHPILOT_HORIZON_DAYS", "90"))
