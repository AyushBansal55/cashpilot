"""
Cashpilot — Phase 1: data access layer.

A thin, stable interface over the synthetic CSVs. Everything downstream — the
MCP tools (Phase 2), the forecaster (Phase 3) — reads through these functions
rather than touching CSVs directly, so the storage format can change without
breaking callers.

Three kinds of data:
  1. Transactions  — historical ledger (what already happened).
  2. Invoices      — wholesale receivables, paid + outstanding.
  3. Scheduled obligations — KNOWN future commitments (recurring bills + the
     one-off roaster purchase and VAT). These are deterministic, so the
     forecaster treats them as certainties rather than predictions.

All amounts are EUR. Inflows are positive, outflows negative.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

# Forecast origin — "today" from the agent's perspective (anchored, see generate.py).
CURRENT_DATE = date(2026, 6, 1)


# --------------------------------------------------------------------------- #
# Transactions & balance
# --------------------------------------------------------------------------- #
@dataclass
class Transaction:
    date: str
    type: str
    counterparty: str
    amount: float
    balance_after: float


def get_transactions(start: str | None = None, end: str | None = None) -> list[dict]:
    """
    Return historical transactions, optionally filtered to an inclusive
    [start, end] date range (ISO strings). Newest data is the closing position.
    """
    rows = []
    with open(DATA_DIR / "transactions.csv") as f:
        for r in csv.DictReader(f):
            if start and r["date"] < start:
                continue
            if end and r["date"] > end:
                continue
            rows.append(
                asdict(
                    Transaction(
                        date=r["date"],
                        type=r["type"],
                        counterparty=r["counterparty"],
                        amount=float(r["amount"]),
                        balance_after=float(r["balance_after"]),
                    )
                )
            )
    return rows


def get_account_balance() -> dict:
    """Current cash position = balance after the most recent transaction."""
    rows = get_transactions()
    latest = rows[-1]
    return {
        "as_of": latest["date"],
        "balance": latest["balance_after"],
        "currency": "EUR",
    }


# --------------------------------------------------------------------------- #
# Invoices (receivables)
# --------------------------------------------------------------------------- #
def get_outstanding_invoices() -> list[dict]:
    """
    Unpaid wholesale invoices, sorted by due date. `expected_late_days` encodes
    each customer's typical payment behaviour (e.g. Harbour Hotel Group pays
    ~25 days late — the driver of the forecast crisis).
    """
    out = []
    with open(DATA_DIR / "invoices.csv") as f:
        for r in csv.DictReader(f):
            if r["status"] != "outstanding":
                continue
            late = int(r["expected_late_days"]) if r["expected_late_days"] else 0
            due = date.fromisoformat(r["due_date"])
            out.append(
                {
                    "invoice_id": r["invoice_id"],
                    "customer": r["customer"],
                    "issue_date": r["issue_date"],
                    "due_date": r["due_date"],
                    "amount": float(r["amount"]),
                    "expected_late_days": late,
                    "expected_payment_date": (due + timedelta(days=late)).isoformat(),
                    "days_overdue": max((CURRENT_DATE - due).days, 0),
                }
            )
    out.sort(key=lambda i: i["due_date"])
    return out


# --------------------------------------------------------------------------- #
# Scheduled future obligations (known commitments)
# --------------------------------------------------------------------------- #
# One-off known future payments. The roaster purchase is the planned capital
# outlay that, colliding with summer's revenue dip and a late key receivable,
# triggers the crisis. These are exactly the items the forecaster sums forward.
ONE_OFF_OBLIGATIONS = [
    {"date": "2026-07-14", "label": "New roaster purchase", "amount": -13_000.0,
     "category": "capex", "deferrable": True},
    {"date": "2026-07-19", "label": "Quarterly VAT return", "amount": -7_400.0,
     "category": "tax", "deferrable": False},
]


def _recurring_on(d: date) -> list[dict]:
    """Known recurring commitments that fall on date `d` (negative = outflow)."""
    items = []
    if d.day == 1:
        items.append({"label": "Rent (Capel St)", "amount": -3_500.0, "category": "rent"})
        items.append({"label": "Utilities (est.)", "amount": -470.0, "category": "utilities"})
    if d.day == 3:
        items.append({"label": "Business insurance", "amount": -650.0, "category": "insurance"})
    if d.day == 5:
        items.append({"label": "Equipment finance", "amount": -2_800.0, "category": "loan"})
    if d.day == 8:
        items.append({"label": "Packaging", "amount": -820.0, "category": "supplier"})
    if d.day == 25:
        items.append({"label": "Staff payroll", "amount": -22_500.0, "category": "payroll"})
    if d.weekday() == 0:  # Monday
        items.append({"label": "Dairy supplier", "amount": -600.0, "category": "supplier"})
    if d.weekday() == 4:  # Friday
        items.append({"label": "Card processing fees", "amount": -380.0, "category": "fees"})
    # Green coffee beans every ~14 days, anchored to a known cadence.
    if (d - date(2026, 6, 2)).days % 14 == 0:
        items.append({"label": "Green coffee beans", "amount": -4_050.0, "category": "supplier"})
    return items


def get_scheduled_obligations(horizon_days: int = 75) -> list[dict]:
    """
    All known committed outflows from CURRENT_DATE over the horizon: recurring
    bills plus the one-off capex/tax items. Returned sorted by date. The
    forecaster treats these as certain (unlike revenue, which is predicted).
    """
    obligations = []
    d = CURRENT_DATE
    for _ in range(horizon_days):
        for item in _recurring_on(d):
            obligations.append({"date": d.isoformat(), **item, "deferrable": False})
        d += timedelta(days=1)
    horizon_end = (CURRENT_DATE + timedelta(days=horizon_days)).isoformat()
    for o in ONE_OFF_OBLIGATIONS:
        if CURRENT_DATE.isoformat() <= o["date"] < horizon_end:
            obligations.append(dict(o))
    obligations.sort(key=lambda x: x["date"])
    return obligations


if __name__ == "__main__":
    bal = get_account_balance()
    inv = get_outstanding_invoices()
    obl = get_scheduled_obligations()
    print(f"Balance as of {bal['as_of']}: €{bal['balance']:,.2f}")
    print(f"Outstanding invoices: {len(inv)} (total €{sum(i['amount'] for i in inv):,.0f})")
    print(f"Scheduled obligations (75d): {len(obl)} "
          f"(total €{sum(o['amount'] for o in obl):,.0f})")
    print("\nNext 5 outstanding invoices:")
    for i in inv[:5]:
        print(f"  {i['invoice_id']}  {i['customer']:<22} €{i['amount']:>8,.0f}  "
              f"due {i['due_date']}  expect {i['expected_payment_date']}")
