"""
Cashpilot — Phase 2: MCP server.

Exposes the business's financial data as Model Context Protocol (MCP) tools that
the ADK agents call. Running this as a real, standalone MCP server (speaking the
protocol over stdio) — rather than wiring the loader functions in-process — is a
deliberate choice: it cleanly demonstrates the "MCP Server" course concept, and
it gives Phase 5 a single, well-defined boundary at which to enforce security
(every tool call crosses this server, so guarding it guards everything).

Four tools, each a thin wrapper over the Phase 1 data loader:
  • get_account_balance       — current cash position
  • get_transactions          — historical ledger (optionally date-filtered)
  • get_outstanding_invoices  — unpaid receivables + expected payment dates
  • get_scheduled_obligations — known future commitments over a horizon

The docstrings below are not just documentation — the Gemini agents read them to
decide *when* to call each tool, so they are written for the model's benefit.

Run standalone (stdio transport):
    python -m cashpilot.mcp_server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .data import loader

# The server name surfaces in ADK traces and tool namespacing.
mcp = FastMCP("cashpilot-financial-data")


@mcp.tool()
def get_account_balance() -> dict:
    """
    Return the business's current cash position (the balance after the most
    recent transaction). Use this first when the user asks about how much cash
    they have now, or as the starting point for any forecast.

    Returns: {"as_of": ISO date, "balance": float (EUR), "currency": "EUR"}
    """
    return loader.get_account_balance()


@mcp.tool()
def get_transactions(start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """
    Return historical transactions (inflows positive, outflows negative), each
    with a running balance. Optionally filter to an inclusive date range using
    ISO dates (YYYY-MM-DD). Use this to analyse spending patterns, recurring
    costs, or revenue trends. Omit both dates to get the full 12-month history.

    Args:
        start_date: earliest date to include, e.g. "2026-03-01" (optional).
        end_date:   latest date to include, e.g. "2026-05-31" (optional).
    """
    return loader.get_transactions(start_date, end_date)


@mcp.tool()
def get_outstanding_invoices() -> list[dict]:
    """
    Return unpaid wholesale invoices (money owed TO the business), sorted by due
    date. Each invoice includes the amount, due date, days overdue, and an
    `expected_payment_date` that accounts for the customer's typical lateness.
    Use this to identify receivables the owner could chase to improve cash, and
    to know when incoming payments will realistically land.
    """
    return loader.get_outstanding_invoices()


@mcp.tool()
def get_scheduled_obligations(horizon_days: int = 75) -> list[dict]:
    """
    Return known future outflows the business is committed to over the next
    `horizon_days` days: recurring bills (rent, payroll, suppliers, loan) plus
    one-off items (e.g. a planned equipment purchase, tax payments). Amounts are
    negative (outflows). The `deferrable` flag indicates whether a payment could
    realistically be delayed — useful when recommending how to avoid a shortfall.

    Args:
        horizon_days: how many days ahead to include (default 75).
    """
    return loader.get_scheduled_obligations(horizon_days)


@mcp.tool()
def run_forecast(horizon_days: int = 75) -> dict:
    """
    Project the business's daily cash position forward over `horizon_days` and
    return a structured forecast. This is the core analytical tool — call it to
    determine whether and when cash is at risk.

    The result contains:
      • summary — lowest point (date + balance), end balance, whether cash
        recovers by the horizon, and whether a real crisis exists.
      • shortfalls — each period where cash drops below the safe threshold, with a
        severity ("warning" = low but solvent, "severe" = expected to go negative,
        "critical" = negative even in the optimistic case) and, for real crises,
        `drivers` explaining the cause: the largest committed outflows in the
        run-up, and any large receivables that arrive too late to help.
      • weekly_series — expected balance with optimistic/pessimistic band, sampled
        weekly, for charting and trend description.

    Use the `drivers` to explain WHY cash is short (e.g. a big purchase colliding
    with payroll while a key invoice is paid late), and use the shortfall dates to
    be specific. Recommendations should target the drivers.

    Args:
        horizon_days: forecast length in days (default 75).
    """
    from .tools.forecast import forecast_for_agent
    return forecast_for_agent(horizon_days)


if __name__ == "__main__":
    # Default transport is stdio, which is what ADK's StdioConnectionParams uses.
    mcp.run()
