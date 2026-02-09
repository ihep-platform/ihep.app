"""
Agent Factory for IHEP Swarm

Centralized factory for spawning agents and development teams.

Author: Jason M Jarmacz | jason@ihep.app
Co-Author: Claude by Anthropic
"""

from typing import Optional, Dict, List, Any
from uuid import uuid4
from loguru import logger

from .base_agent import BaseAgent
from .team_agent import TeamAgent
from ..config.models import (
    Agent,
    Team,
    Swarm,
    TeamEnum,
    TeamRoleEnum,
    RankEnum,
    MOSEnum,
    StatusEnum,
    TEAM_DESCRIPTIONS,
)
from ..llm import OllamaClient


class AgentFactory:
    """
    Factory for creating and managing IHEP development agents.

    Creates the 5-team structure with 6 agents per team:
    - System Architect [COL]
    - Lead Developer [MAJ]
    - Coding Agent [CPT]
    - API Agent [CPT]
    - UX/UI Designer [LT]
    - Network Architect [LT]
    """

    def __init__(self, llm_client: Optional[OllamaClient] = None):
        """
        Initialize agent factory.

        Args:
            llm_client: Shared Ollama client (created if not provided)
        """
        self.llm_client = llm_client or OllamaClient()
        self.active_agents: Dict[str, TeamAgent] = {}
        self.teams: Dict[TeamEnum, Team] = {}
        self.general: Optional[TeamAgent] = None
        self.agent_counter = 0

        logger.info("Agent Factory initialized")

    # =========================================================================
    # AGENT SPAWNING
    # =========================================================================

    def spawn_agent(
        self,
        role: TeamRoleEnum,
        team: TeamEnum,
        name: Optional[str] = None,
        commander_id: Optional[str] = None,
    ) -> TeamAgent:
        """
        Spawn a single agent with specified role and team.

        Args:
            role: Team role
            team: Team assignment
            name: Optional custom name
            commander_id: ID of commanding officer

        Returns:
            Newly created TeamAgent
        """
        agent = TeamAgent(
            role=role,
            team=team,
            llm_client=self.llm_client,
            name=name,
            commander_id=commander_id,
        )

        self.active_agents[agent.agent_id] = agent
        self.agent_counter += 1

        logger.info(f"Spawned agent: {agent.name} for {team.value}")
        return agent

    def spawn_general(self, name: str = "General Overseer") -> TeamAgent:
        """
        Spawn the General Overseer for the swarm.

        The General commands all 5 development teams.

        Args:
            name: General's name

        Returns:
            General agent
        """
        # Create a special general agent
        general = TeamAgent(
            role=TeamRoleEnum.SYSTEM_ARCHITECT,  # General uses architect capabilities
            team=TeamEnum.CORE_LOGIC,  # Attached to core logic
            llm_client=self.llm_client,
            name=name,
        )

        # Override rank to General
        general.rank = RankEnum.GENERAL
        general.mos = MOSEnum.SA_SYSTEM_ARCHITECT

        self.general = general
        self.active_agents[general.agent_id] = general

        logger.info(f"Spawned General: {general.name}")
        return general

    # =========================================================================
    # TEAM SPAWNING
    # =========================================================================

    def spawn_team(self, team_type: TeamEnum) -> Team:
        """
        Spawn a complete development team with 6 agents.

        Args:
            team_type: Type of team to spawn

        Returns:
            Newly created Team
        """
        team_info = TEAM_DESCRIPTIONS.get(team_type, {})
        team_num = list(TeamEnum).index(team_type) + 1

        logger.info(f"Spawning Team {team_num}: {team_info.get('name', team_type.value)}")

        # Create team object
        team = Team(
            id=str(uuid4()),
            name=team_info.get("name", f"Team {team_num}"),
            team_type=team_type,
            status=StatusEnum.STANDBY,
        )

        # Spawn each role
        # System Architect (team lead)
        sa = self.spawn_agent(
            TeamRoleEnum.SYSTEM_ARCHITECT,
            team_type,
            commander_id=self.general.agent_id if self.general else None,
        )
        team.system_architect = sa.agent_id

        # Lead Developer (reports to SA)
        ld = self.spawn_agent(
            TeamRoleEnum.LEAD_DEVELOPER,
            team_type,
            commander_id=sa.agent_id,
        )
        team.lead_developer = ld.agent_id
        sa.add_subordinate(ld.agent_id)

        # Coding Agent (reports to LD)
        ca = self.spawn_agent(
            TeamRoleEnum.CODING_AGENT,
            team_type,
            commander_id=ld.agent_id,
        )
        team.coding_agent = ca.agent_id
        ld.add_subordinate(ca.agent_id)

        # API Agent (reports to LD)
        aa = self.spawn_agent(
            TeamRoleEnum.API_AGENT,
            team_type,
            commander_id=ld.agent_id,
        )
        team.api_agent = aa.agent_id
        ld.add_subordinate(aa.agent_id)

        # UX/UI Designer (reports to SA)
        ux = self.spawn_agent(
            TeamRoleEnum.UX_UI_DESIGNER,
            team_type,
            commander_id=sa.agent_id,
        )
        team.ux_designer = ux.agent_id
        sa.add_subordinate(ux.agent_id)

        # Network Architect (reports to SA)
        na = self.spawn_agent(
            TeamRoleEnum.NETWORK_ARCHITECT,
            team_type,
            commander_id=sa.agent_id,
        )
        team.network_architect = na.agent_id
        sa.add_subordinate(na.agent_id)

        # Add General as commander's commander
        if self.general:
            self.general.add_subordinate(sa.agent_id)

        self.teams[team_type] = team
        logger.info(f"Team {team_num} spawned with {len(team.get_all_agents())} agents")

        return team

    def spawn_all_teams(self) -> Dict[TeamEnum, Team]:
        """
        Spawn all 5 development teams.

        Returns:
            Dictionary of team_type -> Team
        """
        # Spawn General first
        if not self.general:
            self.spawn_general()

        # Spawn each team
        for team_type in TeamEnum:
            self.spawn_team(team_type)

        logger.info(f"All teams spawned. Total agents: {len(self.active_agents)}")
        return self.teams

    # =========================================================================
    # SWARM MANAGEMENT
    # =========================================================================

    def create_swarm(self, name: str = "IHEP Development Swarm") -> Swarm:
        """
        Create complete swarm with General and all 5 teams.

        Args:
            name: Swarm name

        Returns:
            Initialized Swarm
        """
        # Spawn all teams if not already done
        if not self.teams:
            self.spawn_all_teams()

        swarm = Swarm(
            id=str(uuid4()),
            name=name,
            general_id=self.general.agent_id if self.general else None,
            teams={team_type: team.id for team_type, team in self.teams.items()},
            status=StatusEnum.STANDBY,
        )

        logger.info(f"Swarm created: {name} with {len(self.active_agents)} agents")
        return swarm

    # =========================================================================
    # AGENT QUERIES
    # =========================================================================

    def get_agent(self, agent_id: str) -> Optional[TeamAgent]:
        """Get agent by ID"""
        return self.active_agents.get(agent_id)

    def get_team(self, team_type: TeamEnum) -> Optional[Team]:
        """Get team by type"""
        return self.teams.get(team_type)

    def get_agents_by_role(self, role: TeamRoleEnum) -> List[TeamAgent]:
        """Get all agents with specified role"""
        return [a for a in self.active_agents.values() if a.role == role]

    def get_agents_by_team(self, team_type: TeamEnum) -> List[TeamAgent]:
        """Get all agents in specified team"""
        return [a for a in self.active_agents.values() if a.team == team_type]

    def get_available_agents(self) -> List[TeamAgent]:
        """Get agents in STANDBY or ACTIVE status"""
        return [
            a for a in self.active_agents.values()
            if a.status in [StatusEnum.STANDBY, StatusEnum.ACTIVE]
        ]

    def get_team_agents(self, team: Team) -> Dict[TeamRoleEnum, TeamAgent]:
        """Get all agents for a team indexed by role"""
        return {
            TeamRoleEnum.SYSTEM_ARCHITECT: self.get_agent(team.system_architect),
            TeamRoleEnum.LEAD_DEVELOPER: self.get_agent(team.lead_developer),
            TeamRoleEnum.CODING_AGENT: self.get_agent(team.coding_agent),
            TeamRoleEnum.API_AGENT: self.get_agent(team.api_agent),
            TeamRoleEnum.UX_UI_DESIGNER: self.get_agent(team.ux_designer),
            TeamRoleEnum.NETWORK_ARCHITECT: self.get_agent(team.network_architect),
        }

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get factory statistics"""
        return {
            "total_agents": len(self.active_agents),
            "total_teams": len(self.teams),
            "has_general": self.general is not None,
            "agents_by_status": {
                status.value: len([a for a in self.active_agents.values() if a.status == status])
                for status in StatusEnum
            },
            "agents_by_role": {
                role.value: len([a for a in self.active_agents.values() if a.role == role])
                for role in TeamRoleEnum
            },
            "teams": {
                team_type.value: {
                    "id": team.id,
                    "name": team.name,
                    "status": team.status.value,
                    "agent_count": len(team.get_all_agents()),
                }
                for team_type, team in self.teams.items()
            },
        }

    def __repr__(self) -> str:
        return f"<AgentFactory agents={len(self.active_agents)} teams={len(self.teams)}>"
