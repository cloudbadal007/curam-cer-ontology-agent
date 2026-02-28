"""
LangChain-based eligibility determination agent.

Orchestrates MCP tools with LLM reasoning. Returns structured
EligibilityDecision objects. Supports batch and parallel-run validation.
"""

from curam_cer_agent.agent.eligibility_agent import EligibilityAgent

__all__ = ["EligibilityAgent"]
