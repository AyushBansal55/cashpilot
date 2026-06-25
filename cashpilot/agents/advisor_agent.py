"""
Cashpilot — Advisor agent.

Specialist #3 (final stage) in the cashflow pipeline. Reads the Risk agent's
assessment (via the `{risk_assessment}` state placeholder) and converts it into
concrete, ranked, actionable recommendations a business owner could act on
today. This agent's output is the pipeline's final answer, surfaced back to the
Orchestrator (and from there, to the user).

The advisor's DOMAIN KNOWLEDGE — which levers exist, how to prioritise chasing
receivables vs. deferring payments, what never to recommend — lives in an ADK
SKILL (cashflow-advisory) rather than being hardcoded in the instruction. The
agent loads that playbook on demand via the SkillToolset's load_skill tool.
This keeps the playbook reusable and editable independently of the agent, and
demonstrates the "Agent skills" course concept.
"""

from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

from ..config import DEFAULT_RETRY, MODEL

# Load the advisory playbook skill from its SKILL.md directory.
_SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "cashflow-advisory"
_advisory_skill = load_skill_from_dir(_SKILL_DIR)
_advisory_toolset = SkillToolset(skills=[_advisory_skill])

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
        "FIRST, load the 'cashflow-advisory' skill (call load_skill) to get the "
        "advisory playbook — it defines the available levers, how to prioritise "
        "them, and what you must never recommend. Follow that playbook.\n\n"
        "Then write your final recommendation to the business owner:\n"
        "1. Open with a one-sentence verdict: is cash at risk, and how badly.\n"
        "2. Give 2-4 CONCRETE, ranked actions, each naming the specific lever — "
        "e.g. 'Chase [Customer] now for the €[amount] invoice [ID], due "
        "[date]' or 'Defer the [item] payment of €[amount] by [N] weeks' — "
        "using the exact names, amounts, dates, and invoice IDs from the risk "
        "assessment. Never give a generic action without the specific detail "
        "behind it.\n"
        "3. For each action, state the deadline by which it must happen and "
        "roughly how much of the shortfall it closes.\n"
        "4. Close with one sentence on what happens if no action is taken (cite "
        "the trough date and balance).\n\n"
        "Tone: like a sharp, calm bookkeeper talking to a busy owner — direct, "
        "concise, no fluff, no hedging. Every recommendation must be traceable "
        "to the risk assessment; never invent figures."
    ),
    tools=[_advisory_toolset],
    output_key="advisor_recommendation",
    retry_config=DEFAULT_RETRY,
)
