"""
Command & Control Router for IHEP Swarm

Handles communication routing between agents.

Author: Jason M Jarmacz | jason@ihep.app
Co-Author: Claude by Anthropic
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from ..config.models import Order, SitRep, CasRep, StatusEnum
from ..core import AgentFactory, TeamAgent


class C2Router:
    """
    Command and Control Router for agent communication.

    Routes:
    - Orders: Superior -> Subordinate
    - SitReps: Subordinate -> Superior
    - CasReps: Failed agent -> Chain of command
    """

    def __init__(self, agent_factory: AgentFactory):
        """
        Initialize C2 router.

        Args:
            agent_factory: Factory for agent lookups
        """
        self.agent_factory = agent_factory
        self.order_log: List[Order] = []
        self.sitrep_log: List[SitRep] = []
        self.casrep_log: List[CasRep] = []

    def route_order(self, order: Order) -> bool:
        """
        Route order from superior to subordinate.

        Args:
            order: Order to route

        Returns:
            True if order delivered successfully
        """
        # Validate sender exists
        from_agent = self.agent_factory.get_agent(order.from_agent)
        if not from_agent:
            logger.error(f"Order sender not found: {order.from_agent}")
            return False

        # Validate recipient exists
        to_agent = self.agent_factory.get_agent(order.to_agent)
        if not to_agent:
            logger.error(f"Order recipient not found: {order.to_agent}")
            return False

        # Validate chain of command
        if not from_agent.can_command(to_agent.rank):
            logger.warning(
                f"Chain of command violation: {from_agent.rank.value} cannot command {to_agent.rank.value}"
            )
            # Still deliver but log warning

        # Deliver order
        success = to_agent.receive_order(order)
        self.order_log.append(order)

        logger.debug(f"Order routed: {from_agent.name} -> {to_agent.name}: {order.order_type}")
        return success

    def route_sitrep(self, sitrep: SitRep) -> bool:
        """
        Route situation report up chain of command.

        Args:
            sitrep: SitRep to route

        Returns:
            True if sitrep delivered
        """
        from_agent = self.agent_factory.get_agent(sitrep.from_agent)
        if not from_agent:
            logger.error(f"SitRep sender not found: {sitrep.from_agent}")
            return False

        # If no specific recipient, send to commander
        if not sitrep.to_agent and from_agent.commander_id:
            sitrep.to_agent = from_agent.commander_id

        self.sitrep_log.append(sitrep)

        logger.debug(
            f"SitRep: {from_agent.name} reports {sitrep.status.value} "
            f"(progress: {sitrep.progress:.0%})"
        )
        return True

    def route_casrep(self, casrep: CasRep) -> bool:
        """
        Route casualty report up chain of command.

        Args:
            casrep: CasRep to route

        Returns:
            True if casrep logged
        """
        agent = self.agent_factory.get_agent(casrep.agent_id)
        agent_name = agent.name if agent else "Unknown"

        self.casrep_log.append(casrep)

        logger.warning(
            f"CasRep: {agent_name} - {casrep.failure_type}: {casrep.error_message[:100]}"
        )

        # If agent has commander, notify them
        if agent and agent.commander_id:
            commander = self.agent_factory.get_agent(agent.commander_id)
            if commander:
                logger.info(f"Notifying commander {commander.name} of casualty")

        return True

    def broadcast_to_team(self, team_type: str, message: str) -> int:
        """
        Broadcast message to all agents in a team.

        Args:
            team_type: Team type enum value
            message: Message to broadcast

        Returns:
            Number of agents notified
        """
        from ..config.models import TeamEnum

        try:
            team_enum = TeamEnum(team_type)
        except ValueError:
            logger.error(f"Invalid team type: {team_type}")
            return 0

        agents = self.agent_factory.get_agents_by_team(team_enum)
        for agent in agents:
            logger.debug(f"Broadcast to {agent.name}: {message[:50]}...")

        return len(agents)

    def get_team_sitreps(self, team_type: str) -> List[SitRep]:
        """Get all sitreps from a specific team"""
        from ..config.models import TeamEnum

        try:
            team_enum = TeamEnum(team_type)
        except ValueError:
            return []

        agent_ids = [
            a.agent_id for a in self.agent_factory.get_agents_by_team(team_enum)
        ]

        return [s for s in self.sitrep_log if s.from_agent in agent_ids]

    def get_recent_casreps(self, limit: int = 10) -> List[CasRep]:
        """Get most recent casualty reports"""
        return sorted(
            self.casrep_log,
            key=lambda c: c.reported_at,
            reverse=True
        )[:limit]

    def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics"""
        return {
            "total_orders": len(self.order_log),
            "total_sitreps": len(self.sitrep_log),
            "total_casreps": len(self.casrep_log),
            "sitreps_by_status": {
                status.value: len([s for s in self.sitrep_log if s.status == status])
                for status in StatusEnum
            },
            "casreps_by_type": self._count_casreps_by_type(),
        }

    def _count_casreps_by_type(self) -> Dict[str, int]:
        """Count casreps by failure type"""
        counts: Dict[str, int] = {}
        for casrep in self.casrep_log:
            counts[casrep.failure_type] = counts.get(casrep.failure_type, 0) + 1
        return counts
