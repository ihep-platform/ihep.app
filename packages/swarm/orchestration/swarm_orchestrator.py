"""
Swarm Orchestrator for IHEP Development Teams

Manages mission lifecycle and team coordination.

Author: Jason M Jarmacz | jason@ihep.app
Co-Author: Claude by Anthropic
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from ..config.models import (
    Mission,
    Task,
    Team,
    Swarm,
    TeamEnum,
    TeamRoleEnum,
    StatusEnum,
    PriorityEnum,
)
from ..core import AgentFactory, TeamAgent
from ..llm import OllamaClient
from .mission_planner import MissionPlanner


class SwarmOrchestrator:
    """
    Orchestrates the IHEP development swarm.

    Manages:
    - Swarm lifecycle (creation, activation, disbanding)
    - Mission assignment and execution
    - Task distribution to team agents
    - Inter-team coordination
    - Progress monitoring and reporting
    """

    def __init__(
        self,
        llm_client: Optional[OllamaClient] = None,
        auto_init: bool = False,
    ):
        """
        Initialize swarm orchestrator.

        Args:
            llm_client: Shared Ollama client
            auto_init: Automatically initialize swarm on creation
        """
        self.llm_client = llm_client or OllamaClient()
        self.agent_factory = AgentFactory(self.llm_client)
        self.mission_planner = MissionPlanner(self.llm_client)

        self.swarm: Optional[Swarm] = None
        self.active_missions: Dict[str, Mission] = {}
        self.completed_missions: Dict[str, Mission] = {}
        self.mission_results: Dict[str, Dict[str, Any]] = {}

        if auto_init:
            self.initialize_swarm()

        logger.info("Swarm Orchestrator initialized")

    # =========================================================================
    # SWARM LIFECYCLE
    # =========================================================================

    def initialize_swarm(self, name: str = "IHEP Development Swarm") -> Swarm:
        """
        Initialize the complete development swarm.

        Creates General and 5 development teams (31 agents total).

        Args:
            name: Swarm name

        Returns:
            Initialized Swarm
        """
        logger.info(f"Initializing swarm: {name}")

        self.swarm = self.agent_factory.create_swarm(name)
        self.swarm.status = StatusEnum.ACTIVE
        self.swarm.activated_at = datetime.now()

        # Activate all teams
        for team_type in TeamEnum:
            team = self.agent_factory.get_team(team_type)
            if team:
                team.status = StatusEnum.ACTIVE

        logger.info(
            f"Swarm initialized with {len(self.agent_factory.active_agents)} agents "
            f"across {len(self.agent_factory.teams)} teams"
        )

        return self.swarm

    def get_swarm_status(self) -> Dict[str, Any]:
        """Get current swarm status"""
        if not self.swarm:
            return {"status": "not_initialized"}

        return {
            "swarm_id": self.swarm.id,
            "name": self.swarm.name,
            "status": self.swarm.status.value,
            "general": self.agent_factory.general.name if self.agent_factory.general else None,
            "teams": {
                team_type.value: {
                    "status": team.status.value,
                    "current_mission": team.current_mission,
                    "agents": len(team.get_all_agents()),
                }
                for team_type, team in self.agent_factory.teams.items()
            },
            "active_missions": len(self.active_missions),
            "completed_missions": len(self.completed_missions),
            "total_agents": len(self.agent_factory.active_agents),
        }

    # =========================================================================
    # MISSION MANAGEMENT
    # =========================================================================

    def create_mission(
        self,
        template_name: Optional[str] = None,
        objective: Optional[str] = None,
        team: Optional[TeamEnum] = None,
        priority: PriorityEnum = PriorityEnum.ROUTINE,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Mission:
        """
        Create a new mission.

        Either use a template name or provide objective for custom planning.

        Args:
            template_name: Pre-defined template (fix_threejs, database_integration, etc.)
            objective: Custom objective for autonomous planning
            team: Team assignment (required for custom objectives)
            priority: Mission priority
            constraints: Additional constraints

        Returns:
            Created Mission
        """
        if template_name:
            mission = self.mission_planner.create_mission_from_template(
                template_name, constraints
            )
        elif objective and team:
            mission = self.mission_planner.plan_custom_mission(
                objective, team, priority, constraints
            )
        else:
            raise ValueError("Provide either template_name or (objective + team)")

        self.active_missions[mission.id] = mission
        logger.info(f"Created mission: {mission.name} ({mission.id})")

        return mission

    def assign_mission(self, mission_id: str) -> bool:
        """
        Assign mission to its designated team.

        Args:
            mission_id: Mission ID to assign

        Returns:
            True if assignment successful
        """
        mission = self.active_missions.get(mission_id)
        if not mission:
            logger.error(f"Mission not found: {mission_id}")
            return False

        team = self.agent_factory.get_team(mission.assigned_team)
        if not team:
            logger.error(f"Team not found: {mission.assigned_team}")
            return False

        # Check if team is available
        if team.current_mission:
            logger.warning(f"Team {mission.assigned_team.value} already has active mission")
            return False

        team.current_mission = mission_id
        mission.status = StatusEnum.ACTIVE
        mission.started_at = datetime.now()

        logger.info(f"Assigned mission {mission.name} to {team.name}")
        return True

    def execute_mission(self, mission_id: str) -> Dict[str, Any]:
        """
        Execute a mission with the assigned team.

        Distributes tasks to team members and executes with dependency awareness.

        Args:
            mission_id: Mission ID to execute

        Returns:
            Mission execution results
        """
        mission = self.active_missions.get(mission_id)
        if not mission:
            return {"error": f"Mission not found: {mission_id}"}

        if mission.status != StatusEnum.ACTIVE:
            # Assign first
            if not self.assign_mission(mission_id):
                return {"error": "Failed to assign mission"}

        team = self.agent_factory.get_team(mission.assigned_team)
        if not team:
            return {"error": f"Team not found: {mission.assigned_team}"}

        logger.info(f"Executing mission: {mission.name}")

        # Get team agents
        team_agents = self.agent_factory.get_team_agents(team)

        # Execute task graph
        results = self._execute_task_graph(mission, team_agents)

        # Complete mission
        mission.status = StatusEnum.COMPLETE
        mission.completed_at = datetime.now()
        mission.result = results

        # Move to completed
        del self.active_missions[mission_id]
        self.completed_missions[mission_id] = mission
        self.mission_results[mission_id] = results

        # Free up team
        team.current_mission = None
        team.missions_completed += 1

        logger.info(f"Mission completed: {mission.name}")
        return results

    def _execute_task_graph(
        self,
        mission: Mission,
        team_agents: Dict[TeamRoleEnum, TeamAgent],
    ) -> Dict[str, Any]:
        """
        Execute tasks respecting dependency graph.

        Args:
            mission: Mission to execute
            team_agents: Dictionary of role -> agent

        Returns:
            Task execution results
        """
        results = []
        completed_task_ids = set()
        max_iterations = len(mission.tasks) * 2  # Prevent infinite loops

        iteration = 0
        while len(completed_task_ids) < len(mission.tasks) and iteration < max_iterations:
            iteration += 1
            tasks_executed = 0

            for task in mission.tasks:
                if task.id in completed_task_ids:
                    continue

                # Check if dependencies are met
                if not task.is_ready(completed_task_ids):
                    continue

                # Get assigned role and find agent
                role_str = task.metadata.get("assigned_role", "coding_agent")
                try:
                    role = TeamRoleEnum(role_str)
                except ValueError:
                    role = TeamRoleEnum.CODING_AGENT

                agent = team_agents.get(role)
                if not agent:
                    logger.warning(f"No agent for role {role}, using coding agent")
                    agent = team_agents.get(TeamRoleEnum.CODING_AGENT)

                if not agent:
                    logger.error(f"No agent available for task: {task.id}")
                    task.status = StatusEnum.FAILED
                    task.error = "No agent available"
                    completed_task_ids.add(task.id)
                    results.append({
                        "task_id": task.id,
                        "success": False,
                        "error": "No agent available",
                    })
                    continue

                # Execute task
                logger.info(f"Agent {agent.name} executing task: {task.description[:50]}...")
                try:
                    result = agent.execute_task(task)
                    results.append({
                        "task_id": task.id,
                        "success": True,
                        "result": result,
                        "agent": agent.name,
                    })
                except Exception as e:
                    logger.error(f"Task execution failed: {e}")
                    results.append({
                        "task_id": task.id,
                        "success": False,
                        "error": str(e),
                        "agent": agent.name,
                    })

                completed_task_ids.add(task.id)
                tasks_executed += 1

            # Check for deadlock
            if tasks_executed == 0 and len(completed_task_ids) < len(mission.tasks):
                remaining = [t for t in mission.tasks if t.id not in completed_task_ids]
                logger.warning(f"Potential deadlock detected. Remaining tasks: {len(remaining)}")
                break

        return {
            "mission_id": mission.id,
            "mission_name": mission.name,
            "total_tasks": len(mission.tasks),
            "completed_tasks": len(completed_task_ids),
            "task_results": results,
            "success": len(completed_task_ids) == len(mission.tasks),
        }

    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================

    def assign_initial_missions(self) -> Dict[TeamEnum, str]:
        """
        Assign initial missions to all 5 teams.

        Returns:
            Dictionary of team -> mission_id
        """
        assignments = {}

        # Team 1: Digital Twin - Fix Three.js
        m1 = self.create_mission(template_name="fix_threejs")
        self.assign_mission(m1.id)
        assignments[TeamEnum.DIGITAL_TWIN] = m1.id

        # Team 2: Member Resources - Calendar
        m2 = self.create_mission(template_name="calendar_implementation")
        self.assign_mission(m2.id)
        assignments[TeamEnum.MEMBER_RESOURCES] = m2.id

        # Team 3: Peer Mediator - LMS
        m3 = self.create_mission(template_name="lms_implementation")
        self.assign_mission(m3.id)
        assignments[TeamEnum.PEER_MEDIATOR] = m3.id

        # Team 4: Financial Generation - Opportunity Matching
        m4 = self.create_mission(template_name="opportunity_matching")
        self.assign_mission(m4.id)
        assignments[TeamEnum.FINANCIAL_GENERATION] = m4.id

        # Team 5: Core Logic - Database
        m5 = self.create_mission(template_name="database_integration")
        self.assign_mission(m5.id)
        assignments[TeamEnum.CORE_LOGIC] = m5.id

        logger.info(f"Assigned initial missions to all {len(assignments)} teams")
        return assignments

    def execute_all_missions(self) -> Dict[str, Dict[str, Any]]:
        """
        Execute all active missions.

        Returns:
            Dictionary of mission_id -> results
        """
        results = {}
        mission_ids = list(self.active_missions.keys())

        for mission_id in mission_ids:
            result = self.execute_mission(mission_id)
            results[mission_id] = result

        return results

    # =========================================================================
    # REPORTING
    # =========================================================================

    def get_mission_status(self, mission_id: str) -> Dict[str, Any]:
        """Get status of specific mission"""
        mission = self.active_missions.get(mission_id) or self.completed_missions.get(mission_id)
        if not mission:
            return {"error": f"Mission not found: {mission_id}"}

        return {
            "id": mission.id,
            "name": mission.name,
            "status": mission.status.value,
            "team": mission.assigned_team.value if mission.assigned_team else None,
            "priority": mission.priority.value,
            "total_tasks": len(mission.tasks),
            "tasks_by_status": {
                status.value: len([t for t in mission.tasks if t.status == status])
                for status in StatusEnum
            },
            "started_at": mission.started_at.isoformat() if mission.started_at else None,
            "completed_at": mission.completed_at.isoformat() if mission.completed_at else None,
        }

    def get_all_mission_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all missions"""
        all_missions = {**self.active_missions, **self.completed_missions}
        return {
            mission_id: self.get_mission_status(mission_id)
            for mission_id in all_missions
        }
