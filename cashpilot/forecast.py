"""
Cashpilot — Phase 3: the forecasting engine.

Produces a forward daily cash projection by DECOMPOSING the future into three
parts, each handled according to how certain it is:

  1. Known commitments  (certain)   — scheduled obligations: payroll, rent, the
                                       roaster, VAT. Taken at face value.
  2. Expected receivables (near-certain) — outstanding invoices, credited on each
                                       customer's realistic payment date (which
                                       accounts for chronic late-payers).
  3. Predicted café revenue (uncertain) — learned from 12 months of history via a
                                       transparent day-of-week × seasonal-month
                                       decomposition. Its residual variance drives
                                       the confidence band.

Why decomposition rather than a black-box model? The advisor agent (Phase 4)
must EXPLAIN the forecast to a business owner — "you're short because the roaster
landed the same week as payroll while Harbour pays 25 days late." Every euro in
the projection is traceable to a cause, and the revenue band shows uncertainty
honestly instead of pretending the future is exact.

The engine learns the revenue model from data (no hard-coded generator
parameters), so it genuinely *predicts* the crisis rather than being told it.

Run:
    python -m cashpilot.tools.forecast
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date, timedelta
from math import sqrt

from ..data import loader


# --------------------------------------------------------------------------- #
# Revenue model — transparent seasonal decomposition learned from history
# --------------------------------------------------------------------------- #
class RevenueModel:
    """
    Classic multiplicative decomposition of daily café takings:
        predicted = overall_mean × day_of_week_factor × calendar_month_factor

    Day-of-week captures the weekday/weekend rhythm; calendar-month captures
    seasonality (summer dip, pre-Christmas peak). Because history spans a full
    year, the summer months we forecast into are learned from *last* summer —
    no leakage of how the data was generated.
    """

    def __init__(self, cafe: list[tuple[date, float]]):
        amounts = [a for _, a in cafe]
        self.overall = statistics.mean(amounts)

        dow = defaultdict(list)
        mon = defaultdict(list)
        for d, a in cafe:
            dow[d.weekday()].append(a)
            mon[d.month].append(a)
        self.dow_factor = {w: statistics.mean(v) / self.overall for w, v in dow.items()}
        self.mon_factor = {m: statistics.mean(v) / self.overall for m, v in mon.items()}

        # Residual std = day-level noise the model can't explain → band width.
        resid = [a - self.predict(d) for d, a in cafe]
        self.resid_std = statistics.pstdev(resid)

    def predict(self, d: date) -> float:
        return (
            self.overall
            * self.dow_factor.get(d.weekday(), 1.0)
            * self.mon_factor.get(d.month, 1.0)
        )


def _learn_revenue_model() -> RevenueModel:
    txns = loader.get_transactions()
    cafe = [
        (date.fromisoformat(t["date"]), t["amount"])
        for t in txns
        if t["type"] == "cafe_sales"
    ]
    return RevenueModel(cafe)


# --------------------------------------------------------------------------- #
# Forecast
# --------------------------------------------------------------------------- #
def build_forecast(
    horizon_days: int = 75,
    risk_threshold: float = 5_000.0,
    z: float = 1.28,  # ~80% confidence band
) -> dict:
    """
    Roll the cash position forward day by day and return a structured forecast.

    The expected line is the central projection. The confidence band widens with
    the square root of elapsed days (revenue uncertainty compounds), giving an
    optimistic (`high`) and pessimistic (`low`) path. `z` sets the band width:
    1.28 ≈ 80%, 1.64 ≈ 90%.

    Returns a dict with: origin, opening_balance, horizon_days, risk_threshold,
    a daily `series`, identified `shortfalls`, and a `summary`.
    """
    model = _learn_revenue_model()
    opening = loader.get_account_balance()["balance"]
    origin = loader.CURRENT_DATE

    # Bucket certain cashflows by date.
    out_by_date: dict[str, float] = defaultdict(float)
    for o in loader.get_scheduled_obligations(horizon_days):
        out_by_date[o["date"]] += o["amount"]
    in_by_date: dict[str, float] = defaultdict(float)
    receipt_label: dict[str, list] = defaultdict(list)
    for inv in loader.get_outstanding_invoices():
        pd = inv["expected_payment_date"]
        in_by_date[pd] += inv["amount"]
        receipt_label[pd].append((inv["customer"], inv["amount"], inv["invoice_id"]))

    series = []
    expected = opening
    cum_var = 0.0
    d = origin
    for _ in range(horizon_days):
        revenue = model.predict(d)
        outflow = out_by_date.get(d.isoformat(), 0.0)
        receipt = in_by_date.get(d.isoformat(), 0.0)
        expected += revenue + outflow + receipt
        cum_var += model.resid_std ** 2          # variance of cumulative revenue
        band = z * sqrt(cum_var)
        series.append(
            {
                "date": d.isoformat(),
                "expected_balance": round(expected, 2),
                "low_balance": round(expected - band, 2),     # pessimistic
                "high_balance": round(expected + band, 2),     # optimistic
                "predicted_revenue": round(revenue, 2),
                "scheduled_outflow": round(outflow, 2),
                "invoice_receipts": round(receipt, 2),
                "receipt_detail": receipt_label.get(d.isoformat(), []),
            }
        )
        d += timedelta(days=1)

    shortfalls = _find_shortfalls(series, risk_threshold)
    summary = _summarize(series, shortfalls, risk_threshold, opening)

    return {
        "origin": origin.isoformat(),
        "opening_balance": round(opening, 2),
        "horizon_days": horizon_days,
        "risk_threshold": risk_threshold,
        "series": series,
        "shortfalls": shortfalls,
        "summary": summary,
    }


def _find_shortfalls(series: list[dict], threshold: float) -> list[dict]:
    """
    Group consecutive days where the EXPECTED balance is below the threshold into
    discrete shortfall events. Severity uses the band: if even the optimistic
    (`high`) path is below zero, it's critical; if the expected path goes
    negative, it's severe; otherwise it's a warning (cash low but solvent).
    """
    events = []
    cur = None
    for row in series:
        if row["expected_balance"] < threshold:
            if cur is None:
                cur = {"start": row["date"], "end": row["date"],
                       "trough": row["expected_balance"], "trough_date": row["date"],
                       "worst_high": row["high_balance"]}
            else:
                cur["end"] = row["date"]
                if row["expected_balance"] < cur["trough"]:
                    cur["trough"] = row["expected_balance"]
                    cur["trough_date"] = row["date"]
                cur["worst_high"] = min(cur["worst_high"], row["high_balance"])
        elif cur is not None:
            events.append(cur)
            cur = None
    if cur is not None:
        events.append(cur)

    for e in events:
        if e["worst_high"] < 0:
            e["severity"] = "critical"      # negative even in the optimistic case
        elif e["trough"] < 0:
            e["severity"] = "severe"        # expected path goes negative
        else:
            e["severity"] = "warning"       # low but solvent
        e["trough"] = round(e["trough"], 2)
        e.pop("worst_high")
    return events


def _summarize(series, shortfalls, threshold, opening) -> dict:
    trough_row = min(series, key=lambda r: r["expected_balance"])
    end_row = series[-1]
    return {
        "lowest_point_date": trough_row["date"],
        "lowest_point_balance": trough_row["expected_balance"],
        "end_balance": end_row["expected_balance"],
        "recovers_by_horizon": end_row["expected_balance"] >= threshold,
        "shortfall_count": len(shortfalls),
        "has_real_crisis": any(s["severity"] in ("severe", "critical") for s in shortfalls),
    }


def _crisis_drivers(series: list[dict], shortfall: dict, lookback_days: int = 16) -> dict:
    """
    Explain WHY a shortfall happens: the largest committed outflows in the window
    leading up to and through the trough, plus any sizeable receipts the business
    is waiting on that haven't landed yet. This is the payload the advisor agent
    turns into plain-English cause-and-effect.
    """
    trough = date.fromisoformat(shortfall["trough_date"])
    window_start = (trough - timedelta(days=lookback_days)).isoformat()
    window_end = shortfall["end"]

    outflows = []
    for r in series:
        if window_start <= r["date"] <= window_end and r["scheduled_outflow"] < 0:
            outflows.append((r["date"], r["scheduled_outflow"]))
    # Largest individual outflow days drive the crisis.
    outflows.sort(key=lambda x: x[1])

    # Receipts the business is still owed that arrive AFTER the trough (i.e. too
    # late to help) — the classic "your money is stuck in late invoices" story.
    late_help = []
    for r in series:
        if r["date"] > shortfall["trough_date"] and r["invoice_receipts"] > 0:
            for cust, amt, iid in r["receipt_detail"]:
                late_help.append({"date": r["date"], "customer": cust,
                                  "amount": amt, "invoice_id": iid})

    return {
        "top_outflows": [{"date": d, "amount": round(a, 2)} for d, a in outflows[:4]],
        "receivables_arriving_after_trough": late_help[:4],
    }


def forecast_for_agent(horizon_days: int = 75) -> dict:
    """
    Compact, reasoning-friendly view of the forecast for the agents: the summary,
    each shortfall annotated with its drivers, and a weekly-sampled balance series
    (the full daily series is large and meant for charting, not agent context).
    """
    fc = build_forecast(horizon_days)
    for sf in fc["shortfalls"]:
        if sf["severity"] in ("severe", "critical"):
            sf["drivers"] = _crisis_drivers(fc["series"], sf)
    weekly = [
        {"date": r["date"], "expected_balance": r["expected_balance"],
         "low_balance": r["low_balance"], "high_balance": r["high_balance"]}
        for i, r in enumerate(fc["series"]) if i % 7 == 0
    ]
    return {
        "origin": fc["origin"],
        "opening_balance": fc["opening_balance"],
        "horizon_days": fc["horizon_days"],
        "risk_threshold": fc["risk_threshold"],
        "summary": fc["summary"],
        "shortfalls": fc["shortfalls"],
        "weekly_series": weekly,
    }


# --------------------------------------------------------------------------- #
# CLI: prove the engine predicts the crisis
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    fc = build_forecast()
    s = fc["summary"]
    print(f"Forecast from {fc['origin']}, opening €{fc['opening_balance']:,.2f}, "
          f"horizon {fc['horizon_days']}d\n")

    blocks = "▁▂▃▄▅▆▇█"
    lo = min(r["low_balance"] for r in fc["series"])
    hi = max(r["high_balance"] for r in fc["series"])
    print("Weekly expected cash (band shown as ±):")
    for i in range(0, len(fc["series"]), 7):
        r = fc["series"][i]
        frac = (r["expected_balance"] - lo) / (hi - lo) if hi > lo else 0
        bar = blocks[min(int(frac * 7), 7)]
        flag = " ⚠️" if r["expected_balance"] < fc["risk_threshold"] else ""
        spread = (r["high_balance"] - r["low_balance"]) / 2
        print(f"  {r['date']}  {bar}  €{r['expected_balance']:>9,.0f}  "
              f"(±€{spread:,.0f}){flag}")

    print(f"\nLowest point: {s['lowest_point_date']} → €{s['lowest_point_balance']:,.2f}")
    print(f"End of horizon: €{s['end_balance']:,.2f} "
          f"({'recovers' if s['recovers_by_horizon'] else 'still impaired'})")
    print(f"\nShortfall events: {s['shortfall_count']}")
    for e in fc["shortfalls"]:
        print(f"  [{e['severity']:>8}] {e['start']} → {e['end']}  "
              f"trough {e['trough_date']} €{e['trough']:,.0f}")
