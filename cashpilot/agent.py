"""
Cashpilot — root agent definition.

This is the single entry point ADK looks for (`root_agent`). As of Phase 2 it is
a single agent equipped with the financial-data MCP tools, so it can already
answer real questions about the business's cash, invoices, and commitments. In
Phase 4 this becomes the Orchestrator that delegates to the Forecasting, Risk,
and Advisor sub-agents — the MCP toolset defined here will be shared with them.

Run it:
    adk run cashpilot         # interactive CLI
    adk web .                 # browser chat UI at http://localhost:8000
"""

import sys
from pathlib import Path

from google.adk import Agent
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

from .config import MODEL

# Project root = the directory that contains the `cashpilot` package, i.e. the
# folder holding requirements.txt. The MCP server is launched as a subprocess
# from here so its `import cashpilot...` statements resolve.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Financial-data tools, served by our standalone MCP server (cashpilot.mcp_server).
# ADK spawns the server as a subprocess and speaks MCP over stdio. Using
# sys.executable guarantees the server runs in the same virtualenv as the agent.
# ---------------------------------------------------------------------------
financial_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["-m", "cashpilot.mcp_server"],
            cwd=str(PROJECT_ROOT),
        ),
    ),
)

root_agent = Agent(
    name="cashpilot",
    model=MODEL,
    description=(
        "Cashpilot: a cashflow forecasting and advisory agent for small "
        "businesses."
    ),
    instruction=(
        "You are Cashpilot, an AI cashflow advisor for a small business. You "
        "have tools to read the business's current cash balance, transaction "
        "history, outstanding invoices, and scheduled future obligations.\n\n"
        "When the user asks about their cash situation:\n"
        "1. Call get_account_balance to see where they stand today.\n"
        "2. Use get_outstanding_invoices and get_scheduled_obligations to "
        "understand incoming and outgoing money.\n"
        "3. Reason about whether cash is at risk in the coming weeks, and name "
        "specific dates, amounts, invoices, and counterparties — never vague "
        "generalities.\n\n"
        "Always ground every number in a tool result; never invent figures. Be "
        "concise, practical, and plain-spoken, like a sharp bookkeeper talking "
        "to a busy owner. (Forecasting and multi-agent advisory logic arrive in "
        "later phases; for now, answer directly from the tools.)"
    ),
    tools=[financial_tools],
)
