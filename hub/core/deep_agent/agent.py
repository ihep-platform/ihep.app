#!/usr/bin/env python3
"""
IHEP Deep Agent factory — Claude Opus 4.6 primary + full subagent constellation.

Usage:
    from hub.core.deep_agent import build_ihep_agent

    agent = build_ihep_agent()          # defaults (full 29-agent constellation)
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

from .constellation import ALL_SUBAGENTS


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
        "You are the IHEP (Integrated Health Empowerment Platform) master orchestrator "
        "coordinating a constellation of specialized subagents.\n\n"
        "You orchestrate healthcare workflows, analyse patient data, manage "
        "EHR integrations, and ensure HIPAA compliance across all operations.\n\n"
        "Analyze each request and delegate to the most appropriate subagent(s) "
        "using the `task` tool. You may invoke multiple subagents in parallel "
        "for complex, multi-faceted tasks.\n\n"
        "Rules:\n"
        "- Never expose PHI in logs or external calls.\n"
        "- Validate all clinical assertions with evidence.\n"
        "- Delegate to specialized subagents for domain-specific analysis.\n"
        "- Follow HIPAA Safe Harbor de-identification before sharing data externally.\n"
        "- Synthesize subagent outputs into coherent, actionable responses."
    )

    # Agent name (shows in LangGraph traces)
    agent_name: str = "ihep-deep-agent"

    # Extra subagents beyond the default constellation
    extra_subagents: list[SubAgent] = field(default_factory=list)

    # Whether to include the full 29-agent constellation
    use_constellation: bool = True

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

    # Build subagent list: constellation + any extras
    if cfg.use_constellation:
        subagents: list[SubAgent] = [*ALL_SUBAGENTS, *cfg.extra_subagents]
    else:
        # Minimal mode: single Gemini subagent only
        gemini_subagent: SubAgent = {
            "name": cfg.gemini_name,
            "description": cfg.gemini_description,
            "system_prompt": cfg.gemini_system_prompt,
            "model": cfg.gemini_model,
        }
        subagents = [gemini_subagent, *cfg.extra_subagents]

    # Append subagent roster to system prompt so the orchestrator knows what's available
    roster = "\n".join(f"- {s['name']}: {s['description']}" for s in subagents)
    system_prompt = (
        f"{cfg.system_prompt}\n\n"
        f"Available subagents ({len(subagents)}):\n{roster}"
    )

    agent = create_deep_agent(
        model=cfg.primary_model,
        system_prompt=system_prompt,
        subagents=subagents,
        name=cfg.agent_name,
        debug=cfg.debug,
    )

    return agent
