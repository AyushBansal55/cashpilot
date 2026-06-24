"""
Phase 1 validation — confirm the planted cashflow story actually appears.

This is NOT the product forecaster (that's Phase 3). It's a deliberately simple
deterministic projection that reads the SAME data the real tools will use (via
loader.py) and verifies the intended shape appears: a few near-misses where cash
dips low but stays solvent, then a real crisis where it goes negative and does
not self-recover within the horizon. It also prints the answer key (crisis
dates) we use when rehearsing the demo.

Run:
    python -m cashpilot.data.validate
"""

from __future__ import annotations

from datetime import timedelta

from .generate import seasonal_factor
from .loader import (
    CURRENT_DATE,
    get_account_balance,
    get_outstanding_invoices,
    get_scheduled_obligations,
)

RISK_THRESHOLD = 5_000.0
HORIZON_DAYS = 75  # Jun 1 -> Aug 14: frames the July crisis


def expected_cafe(d) -> float:
    """Expected daily cafe takings (no noise — this is a forecast)."""
    base = 940.0 if d.weekday() >= 5 else 660.0
    return base * seasonal_factor(d)


def main():
    balance = get_account_balance()["balance"]

    # Bucket known outflows and expected invoice receipts by date.
    out_by_date: dict[str, float] = {}
    for o in get_scheduled_obligations(HORIZON_DAYS):
        out_by_date[o["date"]] = out_by_date.get(o["date"], 0.0) + o["amount"]
    in_by_date: dict[str, float] = {}
    for i in get_outstanding_invoices():
        pd = i["expected_payment_date"]
        in_by_date[pd] = in_by_date.get(pd, 0.0) + i["amount"]

    print(f"Forecast origin {CURRENT_DATE}: opening €{balance:,.0f}\n")

    trace = []
    d = CURRENT_DATE
    for _ in range(HORIZON_DAYS):
        balance += expected_cafe(d)
        balance += out_by_date.get(d.isoformat(), 0.0)
        balance += in_by_date.get(d.isoformat(), 0.0)
        trace.append((d, balance))
        d += timedelta(days=1)

    # Weekly sparkline.
    lo = min(b for _, b in trace)
    hi = max(b for _, b in trace)
    blocks = "▁▂▃▄▅▆▇█"
    print("Weekly cash trajectory:")
    for i in range(0, len(trace), 7):
        dt, bal = trace[i]
        frac = (bal - lo) / (hi - lo) if hi > lo else 0
        bar = blocks[min(int(frac * 7), 7)]
        flag = " ⚠️" if bal < RISK_THRESHOLD else ""
        print(f"  {dt}  {bar}  €{bal:>9,.0f}{flag}")

    # Daily-resolution near-miss / crisis detection.
    near, crises = [], []
    for i in range(1, len(trace) - 1):
        dd, b = trace[i]
        if b <= trace[i - 1][1] and b < trace[i + 1][1]:  # local min
            if 0 <= b < RISK_THRESHOLD * 2:
                near.append((dd, b))
            elif b < 0:
                crises.append((dd, b))
    trough = min(trace, key=lambda x: x[1])
    days_neg = sum(1 for _, b in trace if b < 0)
    end_d, end_b = trace[-1]

    print(f"\nRisk threshold: €{RISK_THRESHOLD:,.0f}")
    print(f"Near-misses (dip low, stay solvent): {len(near)}")
    for dd, b in near:
        print(f"  {dd}  →  €{b:>9,.0f}")
    print(f"\nReal crisis: {days_neg} days negative, trough {trough[0]} €{trough[1]:,.0f}")
    print(f"End of horizon {end_d}: €{end_b:,.0f} "
          f"({'recovered' if end_b >= RISK_THRESHOLD else 'still impaired — intervention needed'})")


if __name__ == "__main__":
    main()
