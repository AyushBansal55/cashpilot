"""
Cashpilot — Risk agent.

Specialist #2 in the cashflow pipeline. Reads the Forecasting agent's summary
(injected automatically via the `{forecast_summary}` state placeholder — ADK
resolves this from session state because the Forecasting agent set
output_key="forecast_summary") and turns it into a risk assessment: how urgent
is this, which specific events matter, and by when must the owner act for an
intervention to still help.

Deliberately tool-free: this agent reasons purely over the prior agent's text,
which keeps the pipeline fast and keeps the specialists cleanly separated by
responsibility (forecasting vs. judging risk vs. advising).
"""

from google.adk.agents import LlmAgent

from ..config import DEFAULT_RETRY, MODEL

risk_agent = LlmAgent(
    name="risk_agent",
    model=MODEL,
    description=(
        "Assesses the urgency of any cashflow shortfalls identified by the "
        "forecasting agent and determines action deadlines."
    ),
    instruction=(
        "You are a cashflow risk analyst. You have been given a forecast "
        "summary:\n\n{forecast_summary}\n\n"
        "Produce a risk assessment that:\n"
        "1. Assigns an overall urgency level: none, low, medium, high, or "
        "critical. Critical = a shortfall goes negative even in the optimistic "
        "case; high = the expected path goes negative; lower otherwise.\n"
        "2. For each severe/critical event, restates WHY it happens in plain "
        "terms, using the specific drivers (named outflows and their dates/"
        "amounts, and any receivables arriving too late) — do not invent causes "
        "not present in the forecast summary.\n"
        "3. States the ACTION DEADLINE: the latest date by which the owner must "
        "act for an intervention to still prevent or reduce the shortfall (e.g. "
        "if a payment could be deferred or an invoice chased, by when must that "
        "happen relative to the trough date).\n"
        "4. Ranks events by urgency if there are multiple.\n\n"
        "Be specific and quantitative. This assessment is what the advisor will "
        "act on, so do not lose any dates, amounts, or names from the forecast "
        "summary that are relevant to the risk."
    ),
    output_key="risk_assessment",
    retry_config=DEFAULT_RETRY,
)
