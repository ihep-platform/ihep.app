#!/usr/bin/env python3
"""
IHEP Deep Agent factory — Claude Opus 4.6 primary + Gemini subagent.

Usage:
    from hub.core.deep_agent import build_ihep_agent

    agent = build_ihep_agent()          # defaults
    agent = build_ihep_agent(           # custom
        IHEPAgentConfig(
            primary_model="anthropic:claude-opus-4-6",
            gemini_model="google_genai:gemini-2.5-pro",
        )
    )

    # Run the agent (LangGraph compiled graph)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Analyze this patient data…"}]},
        config={"configurable": {"thread_id": "session-1"}},
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field

from deepagents import create_deep_agent, SubAgent


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class IHEPAgentConfig:
    """Tunable knobs for the IHEP deep agent."""

    # Primary orchestrator
    primary_model: str = "anthropic:claude-opus-4-6"

    # Google Gemini subagent
    gemini_model: str = "google_genai:gemini-2.5-pro"
    gemini_name: str = "google"
    gemini_description: str = (
        "A Google Gemini research subagent. Delegate tasks that benefit "
        "from a second opinion, web-scale knowledge retrieval, large-context "
        "analysis, or cross-validation of clinical / regulatory information."
    )
    gemini_system_prompt: str = (
        "You are a research and cross-validation assistant embedded in the "
        "IHEP healthcare platform.\n\n"
        "Guidelines:\n"
        "- Provide thorough, evidence-based analysis.\n"
        "- Cite sources when possible.\n"
        "- Flag any HIPAA or compliance concerns you detect.\n"
        "- Return structured, concise findings to the primary agent.\n"
        "- When analysing clinical data, note confidence levels."
    )

    # Primary agent system prompt
    system_prompt: str = (
        "You are the IHEP (Integrated Health Empowerment Platform) AI agent.\n\n"
        "You orchestrate healthcare workflows, analyse patient data, manage "
        "EHR integrations, and ensure HIPAA compliance across all operations.\n\n"
        "You have access to a Google Gemini subagent (named 'google') that "
        "you can delegate research, cross-validation, and large-context "
        "analysis tasks to via the `task` tool.\n\n"
        "Rules:\n"
        "- Never expose PHI in logs or external calls.\n"
        "- Validate all clinical assertions with evidence.\n"
        "- Use the Gemini subagent for second-opinion analysis when appropriate.\n"
        "- Follow HIPAA Safe Harbor de-identification before sharing data externally."
    )

    # Agent name (shows in LangGraph traces)
    agent_name: str = "ihep-deep-agent"

    # Extra subagents beyond the Gemini one
    extra_subagents: list[SubAgent] = field(default_factory=list)

    debug: bool = False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_ihep_agent(config: IHEPAgentConfig | None = None):
    """
    Build and return a compiled LangGraph agent.

    Returns a ``CompiledStateGraph`` that can be invoked with:
        agent.invoke({"messages": [...]}, config={...})
    """
    cfg = config or IHEPAgentConfig()

    gemini_subagent: SubAgent = {
        "name": cfg.gemini_name,
        "description": cfg.gemini_description,
        "system_prompt": cfg.gemini_system_prompt,
        "model": cfg.gemini_model,
    }

    subagents: list[SubAgent] = [gemini_subagent, *cfg.extra_subagents]

    agent = create_deep_agent(
        model=cfg.primary_model,
        system_prompt=cfg.system_prompt,
        subagents=subagents,
        name=cfg.agent_name,
        debug=cfg.debug,
    )

    return agent
