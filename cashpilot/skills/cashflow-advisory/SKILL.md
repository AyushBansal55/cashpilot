---
name: cashflow-advisory
license: Apache-2.0
metadata:
  author: cashpilot
  version: "1.0"
description: |
  Domain playbook for advising a small business on how to survive a forecast
  cash shortfall. Defines the available levers, how to prioritise them, and the
  principles for turning a risk assessment into concrete, ranked actions. Load
  this skill before writing cashflow recommendations.
---

# Skill: cashflow-advisory

This skill encodes the practical know-how a seasoned small-business bookkeeper
uses to steer a company away from a cash crunch. It does not fetch data — it
tells you how to reason about a shortfall once the forecast and risk assessment
are known.

## 1. The levers (in order of preference)

When a shortfall is forecast, only a few real levers exist. Prefer the ones that
are cheapest and least damaging to the business first:

1. **Accelerate receivables.** Chase the largest, most-overdue, or latest-
   arriving outstanding invoices so cash lands *before* the trough. This is the
   best lever: it uses money the business is already owed. Target invoices whose
   expected payment date falls after the trough — pulling them earlier directly
   fills the gap.
2. **Defer deferrable outflows.** Push back non-essential or flexible payments
   (e.g. a discretionary equipment purchase) to *after* the cash recovers. Never
   suggest deferring payroll or statutory tax (VAT) — those carry legal and
   staff-trust consequences.
3. **Smooth timing.** Where a large outflow lands days before a large receipt,
   negotiating a short payment-terms extension with a supplier can bridge the
   gap without any real cost.
4. **Inject external cash (last resort).** An overdraft or short-term facility.
   Flag it only if levers 1-3 cannot close the gap, and note it has a cost.

## 2. How to prioritise

- Rank actions by **impact per unit of effort/cost**: a single large overdue
  invoice beats chasing several tiny ones.
- Respect the **action deadline**: an action only helps if it can take effect
  before the trough date. State the deadline for every recommendation.
- Quantify each action's contribution: roughly how much of the shortfall it
  closes (e.g. "chasing this €11,200 invoice covers ~73% of the €15.4k gap").
- Stop once the cumulative impact closes the gap; don't pile on unnecessary
  actions.

## 3. What never to recommend

- Deferring or skipping **payroll** or **tax/VAT** payments.
- Anything that relies on a number, customer, invoice, or date not present in
  the risk assessment. Every recommendation must be traceable.
- Vague advice ("improve cash flow", "cut costs") with no specific lever.

## 4. Output shape

A good recommendation: a one-line verdict, then 2-4 ranked, specific actions —
each naming the exact customer/invoice/payment, amount, and deadline, plus its
approximate contribution — and one closing line stating the consequence of
inaction (citing the trough date and balance).
