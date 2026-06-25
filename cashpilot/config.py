"""
Central configuration for Cashpilot.

Keeping model names and tunable constants in one place makes it trivial to swap
models or adjust thresholds without hunting through the codebase. No secrets
live here — the Gemini API key is read from the environment (.env), never
committed.
"""

import os

from google.adk.workflow._retry_config import RetryConfig

# Gemini model used by all agents. `gemini-flash-latest` is fast and cheap,
# which keeps the multi-agent loop responsive during the demo. Swap to a Pro
# model later if reasoning quality on the advisor step needs a boost.
MODEL = os.getenv("CASHPILOT_MODEL", "gemini-flash-latest")

# --- Resilience -------------------------------------------------------------
# The pipeline makes several LLM calls per request (Orchestrator + 3
# specialists). On the FREE Gemini tier, firing them in quick succession trips
# burst rate limits, which Google reports as a 503 "high demand" error even
# though a single call succeeds. This deliberately patient policy — many
# attempts, long backoff — spreads retries out enough for the free tier to keep
# up. If you enable billing (paid tier has far higher burst limits), you can
# safely lower max_attempts/delays for snappier responses.
# NOTE: RetryConfig isn't on a stable public import path in this ADK version
# (google.adk.workflow._retry_config is "private"); if a future ADK release
# moves it, this is the one place to update.
DEFAULT_RETRY = RetryConfig(
    max_attempts=8,
    initial_delay=5.0,
    max_delay=60.0,
    backoff_factor=2.0,
    jitter=1.0,
)

# --- Forecasting / risk thresholds (used from Phase 3 onward) ---------------
# Cash position (EUR) below which a day is flagged as "at risk".
CASH_RISK_THRESHOLD = float(os.getenv("CASHPILOT_RISK_THRESHOLD", "5000"))

# Forecast horizon in days.
FORECAST_HORIZON_DAYS = int(os.getenv("CASHPILOT_HORIZON_DAYS", "90"))

