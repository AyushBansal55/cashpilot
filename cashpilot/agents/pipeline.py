"""
Cashpilot — the cashflow advisory pipeline.

A SequentialAgent that runs the three specialists in a fixed order:
    forecasting_agent -> risk_agent -> advisor_agent

Each agent's output_key writes to session state, and ADK auto-injects those
values into the next agent's `{placeholder}` instruction text — that's how
data flows down the pipeline without any tool wiring between the specialists.

This pipeline IS the multi-agent system. It is exposed to the Orchestrator
(cashpilot/agent.py) as a single callable via AgentTool, so the Orchestrator
can decide WHEN a question warrants running the full forecast -> risk -> advice
chain versus answering a simple lookup directly from the MCP tools.
"""

from google.adk.agents import SequentialAgent

from .advisor_agent import advisor_agent
from .forecasting_agent import forecasting_agent
from .risk_agent import risk_agent

cashflow_pipeline = SequentialAgent(
    name="cashflow_pipeline",
    description=(
        "Runs a full cashflow analysis: forecasts the cash position, assesses "
        "the urgency and causes of any shortfall, and produces concrete, dated "
        "recommendations. Use this for any question about future cash risk, "
        "whether the business might run short, or what action to take."
    ),
    sub_agents=[forecasting_agent, risk_agent, advisor_agent],
)
