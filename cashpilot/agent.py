"""
Cashpilot — root agent (the Orchestrator).

This is the single entry point ADK looks for (`root_agent`). As of Phase 4 it
is a true multi-agent system:

  • For simple lookups ("what's my balance?", "show me outstanding invoices")
    the Orchestrator answers directly using the financial-data MCP tools.
  • For anything about future risk or advice ("am I going to run out of
    money?", "what should I do?") the Orchestrator delegates to
    `cashflow_pipeline` — a SequentialAgent of three specialists (Forecasting
    -> Risk -> Advisor) wrapped as a callable tool via AgentTool.

This split keeps trivial questions fast and cheap while routing real analysis
through the full reasoning pipeline — and it gives a clean, demonstrable
multi-agent architecture (the ADK rubric concept) on top of the MCP server
(Phase 2) and forecasting engine (Phase 3).

Run it:
    adk run cashpilot         # interactive CLI
    adk web .                 # browser chat UI at http://localhost:8000
"""

from google.adk import Agent
from google.adk.tools import AgentTool

from .agents.mcp_tools import build_financial_toolset
from .agents.pipeline import cashflow_pipeline
from .config import DEFAULT_RETRY, MODEL
from .security.guards import after_tool_guard, before_tool_guard

root_agent = Agent(
    name="cashpilot",
    model=MODEL,
    description=(
        "Cashpilot: a multi-agent cashflow forecasting and advisory system "
        "for small businesses."
    ),
    instruction=(
        "You are Cashpilot, an AI cashflow advisor for a small business.\n\n"
        "You have two ways to help:\n"
        "1. DIRECT LOOKUP TOOLS (get_account_balance, get_transactions, "
        "get_outstanding_invoices, get_scheduled_obligations, run_forecast) — "
        "use these for simple factual questions about current balance, "
        "history, or invoices.\n"
        "2. The cashflow_pipeline TOOL — a full forecast -> risk -> advice "
        "pipeline. Use this whenever the user asks about future risk, whether "
        "they might run out of cash, or what they should DO about their cash "
        "position. Call it with no arguments; it runs the full analysis "
        "internally and returns a complete recommendation.\n\n"
        "When you call cashflow_pipeline, present its final recommendation to "
        "the user clearly — do not just paste raw output, but also do not drop "
        "any of its specific dates, amounts, or names. For simple lookups, "
        "answer directly and concisely from the relevant tool.\n\n"
        "Always ground every number in a tool result; never invent figures. Be "
        "concise, practical, and plain-spoken, like a sharp bookkeeper talking "
        "to a busy owner."
    ),
    tools=[
        build_financial_toolset(),
        AgentTool(agent=cashflow_pipeline),
    ],
    retry_config=DEFAULT_RETRY,
    before_tool_callback=before_tool_guard,
    after_tool_callback=after_tool_guard,
)
