"""
Cashpilot — Forecasting agent.

Specialist #1 in the cashflow pipeline. Its only job is to call `run_forecast`
and translate the structured result into a thorough, fully-grounded text
summary. It writes that summary into session state under `forecast_summary`,
where the Risk agent picks it up next.

Why pack all the detail (exact dates, amounts, customer names, invoice IDs)
into this summary now? Because downstream agents (Risk, Advisor) reason over
this TEXT, not the raw tool output — so anything omitted here is unavailable
later. Front-loading the grounding here keeps the rest of the pipeline simple
and tool-free.
"""

from google.adk.agents import LlmAgent

from ..config import DEFAULT_RETRY, MODEL
from .mcp_tools import build_financial_toolset

forecasting_agent = LlmAgent(
    name="forecasting_agent",
    model=MODEL,
    description=(
        "Projects the business's daily cash position forward and reports the "
        "trajectory, including any periods where cash is at risk."
    ),
    instruction=(
        "You are a cashflow forecasting specialist. Call run_forecast (use the "
        "default horizon) and produce a thorough written summary covering:\n"
        "1. The opening cash balance and the overall shape of the trajectory "
        "(when it rises, when it falls).\n"
        "2. EVERY shortfall event from the result, with its severity (warning / "
        "severe / critical), exact start and end dates, and the trough date and "
        "balance.\n"
        "3. For any severe/critical shortfall, the `drivers`: list the exact "
        "top_outflows (date + amount) and any receivables_arriving_after_trough "
        "(date, customer, amount, invoice_id) verbatim — these specifics are "
        "essential for downstream advice and must not be dropped or vagued up.\n"
        "4. Whether the business recovers by the end of the forecast horizon.\n\n"
        "Be precise and complete with numbers, dates, names, and invoice IDs — "
        "never round away detail or summarize vaguely. This summary is the only "
        "source of truth for the agents that act on it next."
    ),
    tools=[build_financial_toolset()],
    output_key="forecast_summary",
    retry_config=DEFAULT_RETRY,
)
