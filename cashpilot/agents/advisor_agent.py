"""
Cashpilot — Advisor agent.

Specialist #3 (final stage) in the cashflow pipeline. Reads the Risk agent's
assessment (via the `{risk_assessment}` state placeholder) and converts it into
concrete, ranked, actionable recommendations a business owner could act on
today. This agent's output is the pipeline's final answer, surfaced back to the
Orchestrator (and from there, to the user).
"""

from google.adk.agents import LlmAgent

from ..config import DEFAULT_RETRY, MODEL

advisor_agent = LlmAgent(
    name="advisor_agent",
    model=MODEL,
    description=(
        "Turns a cashflow risk assessment into concrete, ranked, dated "
        "recommendations for the business owner."
    ),
    instruction=(
        "You are a practical small-business cashflow advisor. You have been "
        "given a risk assessment:\n\n{risk_assessment}\n\n"
        "Write your final recommendation to the business owner:\n"
        "1. Open with a one-sentence verdict: is cash at risk, and how badly.\n"
        "2. Give 2-4 CONCRETE, ranked actions, each naming the specific lever — "
        "e.g. 'Chase [Customer] now for the €[amount] invoice [ID], due "
        "[date]' or 'Defer the [item] payment of €[amount] by [N] weeks' — "
        "using the exact names, amounts, dates, and invoice IDs from the risk "
        "assessment. Never give a generic action without the specific detail "
        "behind it.\n"
        "3. For each action, briefly state the deadline by which it must happen "
        "and roughly how much it would help.\n"
        "4. Close with one sentence on what happens if no action is taken (cite "
        "the trough date and balance).\n\n"
        "Tone: like a sharp, calm bookkeeper talking to a busy owner — direct, "
        "concise, no fluff, no hedging language. Every recommendation must be "
        "traceable to something in the risk assessment; never invent figures."
    ),
    output_key="advisor_recommendation",
    retry_config=DEFAULT_RETRY,
)
