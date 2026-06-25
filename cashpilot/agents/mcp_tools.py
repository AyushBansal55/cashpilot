"""
Cashpilot — shared MCP toolset factory.

Both the root orchestrator and the forecasting sub-agent need the financial
data tools. Each gets its OWN MCPToolset instance (rather than sharing one
object) so their underlying MCP sessions/subprocesses stay independent —
simpler to reason about than a shared singleton, at negligible cost since the
server starts in well under a second.
"""

import sys
from pathlib import Path

from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

# Project root = the directory holding requirements.txt, two levels up from
# this file (cashpilot/agents/mcp_tools.py -> cashpilot/ -> project root).
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def build_financial_toolset() -> MCPToolset:
    """
    Return a fresh MCPToolset connected to our standalone MCP server
    (cashpilot.mcp_server), spawned as a subprocess over stdio. Exposes:
    get_account_balance, get_transactions, get_outstanding_invoices,
    get_scheduled_obligations, run_forecast.
    """
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=["-m", "cashpilot.mcp_server"],
                cwd=str(PROJECT_ROOT),
            ),
        ),
    )
