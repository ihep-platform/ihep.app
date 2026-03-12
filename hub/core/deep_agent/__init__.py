#!/usr/bin/env python3
"""
IHEP Deep Agent — Multi-Model Orchestration

Primary model:  Claude Opus 4.6 (Anthropic)
Subagents:      29-agent constellation including Gemini research,
                domain experts, code specialists, and more.

Uses the `deepagents` library (LangGraph-based) to wire a primary
Claude agent that can delegate tasks to specialized subagents via the
built-in `task` tool.
"""

from .agent import build_ihep_agent, IHEPAgentConfig
from .constellation import ALL_SUBAGENTS

__all__ = ["build_ihep_agent", "IHEPAgentConfig", "ALL_SUBAGENTS"]
