"""Cashpilot package.

The package __init__ deliberately does NOT import the agent module, so the data
layer (cashpilot.data.*) and the MCP server can be used without pulling in ADK
or requiring a Gemini key. ADK discovers `root_agent` by importing
`cashpilot.agent` directly.
"""
