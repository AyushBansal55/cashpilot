# Cashpilot 💸

**An ADK-native multi-agent cashflow forecasting & advisory agent for small businesses.**

> Submission for the Google × Kaggle *Vibecoding Agents – Capstone Project* (Agents for Business track).

---

## The problem

Most small businesses don't fail because they're unprofitable — they fail because they run out of cash without seeing it coming. Owners are too busy running the business to model their float, and a single late invoice or mistimed supplier payment can trigger a shortfall.

## The solution

Cashpilot connects to a business's transaction history and:

1. **Forecasts** the daily cash position for the next 30–90 days.
2. **Flags** the specific dates where cash drops into the danger zone.
3. **Advises** with concrete, ranked actions — which invoices to chase, which payments to defer — grounded in the business's actual receivables and payables.

## Why agents?

Cashflow advice isn't a fixed script — it's *forecast → assess risk → reason about trade-offs → recommend*. That chain maps naturally onto a team of specialist agents that delegate and build on each other's output.

## Architecture

A root **Orchestrator** (ADK `Workflow`) coordinates three specialist agents, all on Gemini, reaching data through an **MCP server**:

```
                 ┌─────────────────────┐
   user ───────▶ │   Orchestrator       │
                 │   (root_agent)       │
                 └──────────┬───────────┘
            ┌───────────────┼────────────────┐
            ▼               ▼                ▼
   ┌────────────┐   ┌────────────┐   ┌────────────┐
   │ Forecasting│   │   Risk     │   │  Advisor   │
   │   agent    │   │   agent    │   │   agent    │
   └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
         └────────────────┴────────────────┘
                          ▼
              ┌───────────────────────┐
              │   MCP server (tools)  │
              │  get_transactions     │
              │  get_account_balance  │
              │  get_outstanding_     │
              │    invoices           │
              │  run_forecast         │
              └───────────────────────┘
```

Tool calls pass through ADK `before_tool_callback` hooks that enforce the **security layer** (prompt-injection defense + PII handling).

## Course concepts demonstrated

The rubric requires ≥3 of 6. Cashpilot targets **5**:

| Concept | How |
|---|---|
| Multi-agent system (ADK) | Orchestrator + 3 specialist agents via `Workflow` |
| MCP Server | Financial data tools exposed over MCP |
| Agent skills | Advisory playbook as an ADK `SkillToolset` |
| Security features | `before_tool_callback` guards vs. tool-injection |
| Deployability | One-command containerized deploy to Cloud Run |

## Setup

```bash
# 1. Clone, then create and activate a virtual environment
python3 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure secrets
cp .env.example .env
# ...then edit .env and paste your Gemini API key

# 4. Run it
adk run cashpilot      # interactive CLI
# or
adk web .              # browser chat UI → http://localhost:8000
```

## Build status

- [x] **Phase 0** — Scaffold + hello-world agent (you are here)
- [x] **Phase 1** — Synthetic SME transaction dataset (done)
- [x] **Phase 2** — MCP server + financial tools (done)
- [x] **Phase 3** — Forecasting engine (done)
- [x] **Phase 4** — Multi-agent orchestration (done)
- [x] **Phase 5** — Security layer (done)
- [x] **Phase 6** — Agent skill (advisory playbook) (done)
- [ ] **Phase 7** — Deploy + UI
- [ ] **Phase 8** — Writeup, video, cover image

## License

CC-BY 4.0 (per competition winner license terms).
