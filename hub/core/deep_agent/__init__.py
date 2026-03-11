#!/usr/bin/env python3
"""
IHEP Deep Agent — Multi-Model Orchestration

Primary model:  Claude Opus 4.6 (Anthropic)
Subagent:       Gemini (Google) for research and cross-validation

Uses the `deepagents` library (LangGraph-based) to wire a primary
Claude agent that can delegate tasks to a Gemini subagent via the
built-in `task` tool.
"""

from .agent import build_ihep_agent, IHEPAgentConfig

__all__ = ["build_ihep_agent", "IHEPAgentConfig"]
