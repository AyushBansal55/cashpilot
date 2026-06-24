"""
Cashpilot — Phase 2 test: exercise the MCP server over the real protocol.

This spawns cashpilot.mcp_server as a subprocess, connects as an MCP client over
stdio, lists the advertised tools, and calls each one — exactly as the ADK agent
will. Running this BEFORE involving any agent or Gemini key lets us confirm the
server boundary works in isolation (the same discipline that de-risked Phase 1).

Run:
    python -m cashpilot.test_mcp
"""

from __future__ import annotations

import json

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SERVER = StdioServerParameters(
    command=sys.executable,
    args=["-m", "cashpilot.mcp_server"],
    cwd=str(PROJECT_ROOT),
)


async def main() -> None:
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            print(f"Server advertises {len(tools)} tools:")
            for t in tools:
                print(f"  • {t.name}")
            print()

            def unwrap(res):
                """Normalize FastMCP results: dict/scalar returns arrive as
                content text; list returns arrive in structuredContent as
                {"result": [...]}."""
                sc = res.structuredContent
                if sc is not None:
                    if isinstance(sc, dict) and set(sc.keys()) == {"result"}:
                        return sc["result"]
                    return sc
                return json.loads(res.content[0].text)

            # 1. Balance
            bal = unwrap(await session.call_tool("get_account_balance", {}))
            print(f"get_account_balance → €{bal['balance']:,.2f} as of {bal['as_of']}")

            # 2. Outstanding invoices
            invoices = unwrap(await session.call_tool("get_outstanding_invoices", {}))
            first = invoices[0]
            print(f"get_outstanding_invoices → {len(invoices)} invoices; "
                  f"first: {first['invoice_id']} {first['customer']} €{first['amount']:,.0f}")

            # 3. Scheduled obligations
            obligations = unwrap(
                await session.call_tool("get_scheduled_obligations", {"horizon_days": 75})
            )
            total = sum(o["amount"] for o in obligations)
            print(f"get_scheduled_obligations → {len(obligations)} items, total €{total:,.0f}")

            # 4. Transactions (date-filtered)
            txns = unwrap(
                await session.call_tool(
                    "get_transactions",
                    {"start_date": "2026-05-01", "end_date": "2026-05-31"},
                )
            )
            print(f"get_transactions (May 2026) → {len(txns)} rows")

            print("\n✓ All four MCP tools responded correctly over the protocol.")


if __name__ == "__main__":
    asyncio.run(main())
