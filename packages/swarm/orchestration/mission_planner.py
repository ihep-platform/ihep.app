"""
Mission Planner for IHEP Swarm

Autonomous task decomposition and mission planning.

Author: Jason M Jarmacz | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import json
from typing import List, Dict, Any, Optional
from uuid import uuid4
from loguru import logger

from ..config.models import (
    Mission,
    Task,
    TeamEnum,
    TeamRoleEnum,
    StatusEnum,
    PriorityEnum,
)
from ..llm import OllamaClient


# Pre-defined mission templates for IHEP
MISSION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "fix_threejs": {
        "name": "Fix Three.js/Turbopack Bundling",
        "objective": "Resolve the Turbopack + Three.js bundling incompatibility that prevents 3D visualization",
        "team": TeamEnum.DIGITAL_TWIN,
        "priority": PriorityEnum.CRITICAL,
        "tasks": [
            {
                "description": "Analyze Turbopack vs Webpack architecture and identify root cause",
                "role": TeamRoleEnum.SYSTEM_ARCHITECT,
                "dependencies": [],
            },
            {
                "description": "Research alternative Three.js import patterns that work with Turbopack",
                "role": TeamRoleEnum.LEAD_DEVELOPER,
                "dependencies": [],
            },
            {
                "description": "Implement webpack configuration override in next.config.mjs",
                "role": TeamRoleEnum.CODING_AGENT,
                "dependencies": [0, 1],
            },
            {
                "description": "Test Three.js rendering with new configuration",
                "role": TeamRoleEnum.CODING_AGENT,
                "dependencies": [2],
            },
            {
                "description": "Verify WebSocket data streams work with new bundling",
                "role": TeamRoleEnum.API_AGENT,
                "dependencies": [3],
            },
            {
                "description": "Validate 3D visualization renders correctly across browsers",
                "role": TeamRoleEnum.UX_UI_DESIGNER,
                "dependencies": [3],
            },
            {
                "description": "Optimize asset loading performance",
                "role": TeamRoleEnum.NETWORK_ARCHITECT,
                "dependencies": [3],
            },
        ],
    },
    "database_integration": {
        "name": "Database Integration",
        "objective": "Configure PostgreSQL database and replace mock store with real persistence",
        "team": TeamEnum.CORE_LOGIC,
        "priority": PriorityEnum.CRITICAL,
        "tasks": [
            {
                "description": "Review and finalize Drizzle schema in src/shared/schema.ts",
                "role": TeamRoleEnum.SYSTEM_ARCHITECT,
                "dependencies": [],
            },
            {
                "description": "Create database migration scripts",
                "role": TeamRoleEnum.LEAD_DEVELOPER,
                "dependencies": [0],
            },
            {
                "description": "Implement repository pattern for data access",
                "role": TeamRoleEnum.CODING_AGENT,
                "dependencies": [1],
            },
            {
                "description": "Replace mockStore.ts with real database queries",
                "role": TeamRoleEnum.CODING_AGENT,
                "dependencies": [2],
            },
            {
                "description": "Add database queries to all API endpoints",
                "role": TeamRoleEnum.API_AGENT,
                "dependencies": [2],
            },
            {
                "description": "Create loading states and error handling UI",
                "role": TeamRoleEnum.UX_UI_DESIGNER,
                "dependencies": [4],
            },
            {
                "description": "Configure connection pooling and query optimization",
                "role": TeamRoleEnum.NETWORK_ARCHITECT,
                "dependencies": [4],
            },
        ],
    },
    "calendar_implementation": {
        "name": "Dynamic Calendar Implementation",
        "objective": "Build full calendar functionality with appointments API integration",
        "team": TeamEnum.MEMBER_RESOURCES,
        "priority": PriorityEnum.HIGH,
        "tasks": [
            {
                "description": "Design calendar data model with recurring events support",
                "role": TeamRoleEnum.SYSTEM_ARCHITECT,
                "dependencies": [],
            },
            {
                "description": "Integrate react-day-picker with appointments API",
                "role": TeamRoleEnum.LEAD_DEVELOPER,
                "dependencies": [0],
            },
            {
                "description": "Build appointment CRUD components",
                "role": TeamRoleEnum.CODING_AGENT,
                "dependencies": [1],
            },
            {
                "description": "Implement /api/appointments endpoints",
                "role": TeamRoleEnum.API_AGENT,
                "dependencies": [0],
            },
            {
                "description": "Design calendar UI with mobile responsiveness",
                "role": TeamRoleEnum.UX_UI_DESIGNER,
                "dependencies": [2],
            },
            {
                "description": "Implement external calendar sync (Google, Apple)",
                "role": TeamRoleEnum.NETWORK_ARCHITECT,
                "dependencies": [3],
            },
        ],
    },
    "lms_implementation": {
        "name": "Learning Management System",
        "objective": "Build peer mediator curriculum system with progress tracking",
        "team": TeamEnum.PEER_MEDIATOR,
        "priority": PriorityEnum.HIGH,
        "tasks": [
            {
                "description": "Design curriculum structure and learning paths",
                "role": TeamRoleEnum.SYSTEM_ARCHITECT,
                "dependencies": [],
            },
            {
                "description": "Build course module framework",
                "role": TeamRoleEnum.LEAD_DEVELOPER,
                "dependencies": [0],
            },
            {
                "description": "Implement assessment components and progress tracking",
                "role": TeamRoleEnum.CODING_AGENT,
                "dependencies": [1],
            },
            {
                "description": "Create certification and competency tracking APIs",
                "role": TeamRoleEnum.API_AGENT,
                "dependencies": [0],
            },
            {
                "description": "Design accessible learning interface",
                "role": TeamRoleEnum.UX_UI_DESIGNER,
                "dependencies": [1],
            },
            {
                "description": "Set up video streaming and content delivery",
                "role": TeamRoleEnum.NETWORK_ARCHITECT,
                "dependencies": [1],
            },
        ],
    },
    "opportunity_matching": {
        "name": "Opportunity Matching Engine",
        "objective": "Build income generation opportunity matching with external integrations",
        "team": TeamEnum.FINANCIAL_GENERATION,
        "priority": PriorityEnum.HIGH,
        "tasks": [
            {
                "description": "Design matching algorithm architecture",
                "role": TeamRoleEnum.SYSTEM_ARCHITECT,
                "dependencies": [],
            },
            {
                "description": "Integrate with Python opportunitymatcher.py service",
                "role": TeamRoleEnum.LEAD_DEVELOPER,
                "dependencies": [0],
            },
            {
                "description": "Build opportunity listing components",
                "role": TeamRoleEnum.CODING_AGENT,
                "dependencies": [1],
            },
            {
                "description": "Connect to gig platforms and job board APIs",
                "role": TeamRoleEnum.API_AGENT,
                "dependencies": [0],
            },
            {
                "description": "Design opportunity cards and filtering UI",
                "role": TeamRoleEnum.UX_UI_DESIGNER,
                "dependencies": [2],
            },
            {
                "description": "Implement rate limiting and caching for external APIs",
                "role": TeamRoleEnum.NETWORK_ARCHITECT,
                "dependencies": [3],
            },
        ],
    },
}


class MissionPlanner:
    """
    Autonomous mission planning for IHEP development teams.

    Decomposes objectives into actionable tasks with dependencies.
    """

    def __init__(self, llm_client: Optional[OllamaClient] = None):
        """
        Initialize mission planner.

        Args:
            llm_client: Ollama client for autonomous planning
        """
        self.llm_client = llm_client or OllamaClient()

    def create_mission_from_template(
        self,
        template_name: str,
        custom_constraints: Optional[Dict[str, Any]] = None,
    ) -> Mission:
        """
        Create mission from pre-defined template.

        Args:
            template_name: Name of template (fix_threejs, database_integration, etc.)
            custom_constraints: Additional constraints to apply

        Returns:
            Configured Mission object
        """
        template = MISSION_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")

        mission = Mission(
            id=str(uuid4()),
            name=template["name"],
            objective=template["objective"],
            assigned_team=template["team"],
            priority=template["priority"],
            constraints=custom_constraints or {},
            status=StatusEnum.STANDBY,
        )

        # Create tasks from template
        task_map = {}  # index -> task_id for dependency resolution
        for i, task_def in enumerate(template["tasks"]):
            task = Task(
                id=str(uuid4()),
                description=task_def["description"],
                status=StatusEnum.STANDBY,
                metadata={
                    "assigned_role": task_def["role"].value,
                    "mission_id": mission.id,
                },
            )

            # Resolve dependencies
            task.dependencies = [
                task_map[dep_idx] for dep_idx in task_def["dependencies"]
                if dep_idx in task_map
            ]

            task_map[i] = task.id
            mission.tasks.append(task)

        logger.info(f"Created mission from template: {mission.name} with {len(mission.tasks)} tasks")
        return mission

    def plan_custom_mission(
        self,
        objective: str,
        team: TeamEnum,
        priority: PriorityEnum = PriorityEnum.ROUTINE,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Mission:
        """
        Create mission with autonomous task decomposition.

        Uses LLM to decompose objective into tasks.

        Args:
            objective: Mission objective
            team: Assigned team
            priority: Mission priority
            constraints: Additional constraints

        Returns:
            Planned mission with decomposed tasks
        """
        mission = Mission(
            id=str(uuid4()),
            objective=objective,
            name=objective[:50] + "..." if len(objective) > 50 else objective,
            assigned_team=team,
            priority=priority,
            constraints=constraints or {},
            status=StatusEnum.STANDBY,
        )

        # Use LLM for task decomposition
        tasks = self._decompose_objective(objective, team, constraints)
        mission.tasks = tasks

        logger.info(f"Planned mission: {mission.name} with {len(tasks)} tasks")
        return mission

    def _decompose_objective(
        self,
        objective: str,
        team: TeamEnum,
        constraints: Optional[Dict[str, Any]],
    ) -> List[Task]:
        """
        Use LLM to decompose objective into tasks.
        """
        prompt = f"""Decompose the following objective into specific, actionable tasks for a development team.

OBJECTIVE: {objective}

TEAM ROLES:
- System Architect: Design and technical decisions
- Lead Developer: Implementation oversight
- Coding Agent: Feature development
- API Agent: Endpoint implementation
- UX/UI Designer: Interface design
- Network Architect: Infrastructure

CONSTRAINTS:
{json.dumps(constraints or {}, indent=2)}

For each task, specify:
1. description: Clear task description
2. role: Which team role should handle it (system_architect, lead_developer, coding_agent, api_agent, ux_ui_designer, network_architect)
3. dependencies: List of task indices this depends on (0-based)
4. complexity: low, medium, or high

Respond with a JSON array of task objects.
"""

        try:
            response = self.llm_client.query_for_task_decomposition(objective, constraints)
            tasks_data = self._parse_tasks_response(response)
        except Exception as e:
            logger.warning(f"LLM task decomposition failed: {e}, using default structure")
            tasks_data = self._default_task_structure(objective)

        # Convert to Task objects
        tasks = []
        task_map = {}

        for i, task_data in enumerate(tasks_data):
            task = Task(
                id=str(uuid4()),
                description=task_data.get("description", f"Task {i+1}"),
                status=StatusEnum.STANDBY,
                metadata={
                    "assigned_role": task_data.get("role", "coding_agent"),
                    "complexity": task_data.get("complexity", "medium"),
                },
            )

            # Resolve dependencies
            dep_indices = task_data.get("dependencies", [])
            task.dependencies = [
                task_map[dep_idx] for dep_idx in dep_indices
                if dep_idx in task_map
            ]

            task_map[i] = task.id
            tasks.append(task)

        return tasks

    def _parse_tasks_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into task list"""
        try:
            # Try to extract JSON from response
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Return empty list if parsing fails
        return []

    def _default_task_structure(self, objective: str) -> List[Dict[str, Any]]:
        """Default task structure when LLM fails"""
        return [
            {
                "description": f"Analyze requirements for: {objective}",
                "role": "system_architect",
                "dependencies": [],
                "complexity": "medium",
            },
            {
                "description": "Create implementation plan",
                "role": "lead_developer",
                "dependencies": [0],
                "complexity": "medium",
            },
            {
                "description": "Implement core functionality",
                "role": "coding_agent",
                "dependencies": [1],
                "complexity": "high",
            },
            {
                "description": "Implement API endpoints",
                "role": "api_agent",
                "dependencies": [1],
                "complexity": "medium",
            },
            {
                "description": "Design user interface",
                "role": "ux_ui_designer",
                "dependencies": [2],
                "complexity": "medium",
            },
            {
                "description": "Configure infrastructure",
                "role": "network_architect",
                "dependencies": [3],
                "complexity": "medium",
            },
        ]

    def get_available_templates(self) -> List[str]:
        """Get list of available mission templates"""
        return list(MISSION_TEMPLATES.keys())
