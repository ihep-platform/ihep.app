"""
Team Agent Class for IHEP Swarm

Role-specific agent implementations for the 5 development teams.

Author: Jason M Jarmacz | jason@ihep.app
Co-Author: Claude by Anthropic
"""

from typing import Optional, Dict, Any
from loguru import logger

from .base_agent import BaseAgent
from ..config.models import (
    Task,
    StatusEnum,
    RankEnum,
    TeamRoleEnum,
    MOSEnum,
    TeamEnum,
    ROLE_TO_RANK,
    ROLE_TO_MOS,
)
from ..llm import OllamaClient


class TeamAgent(BaseAgent):
    """
    Concrete agent implementation for IHEP development teams.

    Each agent has a specific role within their team:
    - System Architect: Design and technical decisions
    - Lead Developer: Implementation oversight
    - Coding Agent: Feature development
    - API Agent: Endpoint implementation
    - UX/UI Designer: Interface design
    - Network Architect: Infrastructure
    """

    def __init__(
        self,
        role: TeamRoleEnum,
        team: TeamEnum,
        llm_client: Optional[OllamaClient] = None,
        name: Optional[str] = None,
        commander_id: Optional[str] = None,
    ):
        """
        Initialize team agent with role-specific configuration.

        Args:
            role: Team role (system_architect, lead_developer, etc.)
            team: Team assignment (digital_twin, member_resources, etc.)
            llm_client: Shared Ollama client
            name: Optional custom name
            commander_id: ID of supervising agent
        """
        # Get rank and MOS from role
        rank = ROLE_TO_RANK.get(role, RankEnum.LIEUTENANT)
        mos = ROLE_TO_MOS.get(role, MOSEnum.CD_CODING_AGENT)

        # Generate role-appropriate name if not provided
        if not name:
            team_num = list(TeamEnum).index(team) + 1
            name = f"T{team_num}-{role.value.replace('_', '-').title()}"

        super().__init__(
            name=name,
            rank=rank,
            role=role,
            mos=mos,
            llm_client=llm_client,
            commander_id=commander_id,
        )

        self.team = team
        self.specialization = self._get_specialization()

    def _get_specialization(self) -> Dict[str, Any]:
        """Get role-specific specialization configuration"""
        specializations = {
            TeamRoleEnum.SYSTEM_ARCHITECT: {
                "focus": "architecture",
                "skills": ["system design", "technical decisions", "documentation"],
                "output_types": ["design docs", "architecture diagrams", "technical specs"],
            },
            TeamRoleEnum.LEAD_DEVELOPER: {
                "focus": "implementation",
                "skills": ["code review", "implementation strategy", "team coordination"],
                "output_types": ["implementation plans", "code reviews", "technical guidance"],
            },
            TeamRoleEnum.CODING_AGENT: {
                "focus": "development",
                "skills": ["feature development", "bug fixes", "testing"],
                "output_types": ["source code", "unit tests", "documentation"],
            },
            TeamRoleEnum.API_AGENT: {
                "focus": "integration",
                "skills": ["API design", "endpoint implementation", "data contracts"],
                "output_types": ["API endpoints", "schemas", "integration code"],
            },
            TeamRoleEnum.UX_UI_DESIGNER: {
                "focus": "user experience",
                "skills": ["UI design", "accessibility", "user flows"],
                "output_types": ["component designs", "style guides", "accessibility specs"],
            },
            TeamRoleEnum.NETWORK_ARCHITECT: {
                "focus": "infrastructure",
                "skills": ["networking", "deployment", "performance"],
                "output_types": ["infrastructure configs", "deployment scripts", "monitoring"],
            },
        }
        return specializations.get(self.role, {})

    def build_task_prompt(self, task: Task) -> str:
        """
        Build role-specific prompt for task execution.

        Args:
            task: Task to build prompt for

        Returns:
            Formatted prompt with role context
        """
        role_context = self._get_role_context()
        team_context = self._get_team_context()

        prompt = f"""You are a {self.role.value.replace('_', ' ')} on the {team_context['name']} team.

ROLE CONTEXT:
{role_context}

TEAM FOCUS:
{team_context['description']}
Technical Focus: {team_context['focus']}

TASK:
{task.description}

CONSTRAINTS:
{task.metadata.get('constraints', 'None specified')}

DEPENDENCIES:
{task.metadata.get('dependencies', 'None')}

Please provide your output in a structured format appropriate for your role.
If generating code, ensure it follows best practices and includes proper error handling.
If generating documentation, use clear markdown formatting.
"""
        return prompt

    def _get_role_context(self) -> str:
        """Get role-specific context for prompts"""
        contexts = {
            TeamRoleEnum.SYSTEM_ARCHITECT: """
As System Architect, you are responsible for:
- Designing system architecture and component interactions
- Making technical decisions on frameworks and patterns
- Ensuring scalability, security, and maintainability
- Creating technical specifications and documentation
Output should include clear diagrams (in mermaid/ASCII), rationale, and implementation guidelines.
""",
            TeamRoleEnum.LEAD_DEVELOPER: """
As Lead Developer, you are responsible for:
- Overseeing implementation of architectural decisions
- Reviewing code and ensuring quality standards
- Coordinating work across team members
- Resolving technical blockers
Output should include implementation strategies, code review feedback, and technical guidance.
""",
            TeamRoleEnum.CODING_AGENT: """
As Coding Agent, you are responsible for:
- Implementing features according to specifications
- Writing clean, well-tested code
- Fixing bugs and addressing code review feedback
- Creating unit tests and documentation
Output should be production-ready code with tests and inline documentation.
""",
            TeamRoleEnum.API_AGENT: """
As API Agent, you are responsible for:
- Designing and implementing REST/GraphQL endpoints
- Creating data contracts and schemas
- Integrating with external services
- Ensuring API security and performance
Output should include endpoint code, OpenAPI specs, and integration tests.
""",
            TeamRoleEnum.UX_UI_DESIGNER: """
As UX/UI Designer, you are responsible for:
- Designing user interfaces and experiences
- Ensuring accessibility (WCAG 2.1 AA compliance)
- Creating component specifications
- Defining user flows and interactions
Output should include component designs, style definitions, and accessibility considerations.
""",
            TeamRoleEnum.NETWORK_ARCHITECT: """
As Network Architect, you are responsible for:
- Designing infrastructure and networking
- Creating deployment configurations
- Optimizing performance and reliability
- Setting up monitoring and logging
Output should include infrastructure configs, deployment scripts, and monitoring specifications.
""",
        }
        return contexts.get(self.role, "General development tasks")

    def _get_team_context(self) -> Dict[str, str]:
        """Get team-specific context"""
        from ..config.models import TEAM_DESCRIPTIONS
        return TEAM_DESCRIPTIONS.get(self.team, {
            "name": "Unknown Team",
            "description": "General development",
            "focus": "Various tasks",
        })

    def execute_task(self, task: Task) -> Any:
        """
        Execute assigned task using role-appropriate approach.

        Args:
            task: Task to execute

        Returns:
            Task result (code, documentation, or analysis)
        """
        try:
            # Assign task to self
            if not self.assign_task(task):
                return {"error": "Failed to assign task"}

            logger.info(f"{self.name} executing task: {task.description[:50]}...")

            # Build role-specific prompt
            prompt = self.build_task_prompt(task)

            # Execute based on role
            if self.role in [TeamRoleEnum.CODING_AGENT, TeamRoleEnum.API_AGENT]:
                result = self._execute_code_task(prompt, task)
            elif self.role == TeamRoleEnum.SYSTEM_ARCHITECT:
                result = self._execute_analysis_task(prompt, task)
            elif self.role == TeamRoleEnum.LEAD_DEVELOPER:
                result = self._execute_review_task(prompt, task)
            elif self.role == TeamRoleEnum.UX_UI_DESIGNER:
                result = self._execute_design_task(prompt, task)
            elif self.role == TeamRoleEnum.NETWORK_ARCHITECT:
                result = self._execute_infra_task(prompt, task)
            else:
                result = self._execute_general_task(prompt, task)

            # Complete task
            completed = self.complete_task(result)
            return result

        except Exception as e:
            logger.error(f"{self.name} task execution failed: {e}")
            casrep = self.report_casrep(e, task)
            self.fail_task(str(e))
            return {"error": str(e), "casrep": casrep.id}

    def _execute_code_task(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Execute code generation task"""
        # Use codellama for code tasks
        response = self.llm_client.query_for_code(prompt)

        return {
            "type": "code",
            "content": response,
            "language": task.metadata.get("language", "typescript"),
            "agent": self.name,
            "role": self.role.value,
        }

    def _execute_analysis_task(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Execute analysis/architecture task"""
        response = self.llm_client.query_for_analysis(prompt)

        return {
            "type": "analysis",
            "content": response,
            "agent": self.name,
            "role": self.role.value,
        }

    def _execute_review_task(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Execute code review task"""
        review_prompt = f"""
{prompt}

Provide a structured code review with:
1. Summary of changes
2. Issues found (if any)
3. Suggestions for improvement
4. Security considerations
5. Approval status (APPROVED/NEEDS_CHANGES/REJECTED)
"""
        response = self.query_llm(review_prompt)

        return {
            "type": "review",
            "content": response,
            "agent": self.name,
            "role": self.role.value,
        }

    def _execute_design_task(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Execute UI/UX design task"""
        design_prompt = f"""
{prompt}

Provide design specifications including:
1. Component structure (React/Next.js)
2. Tailwind CSS classes for styling
3. Accessibility attributes (ARIA)
4. Responsive breakpoints
5. State management requirements
"""
        response = self.query_llm(design_prompt, temperature=0.7)

        return {
            "type": "design",
            "content": response,
            "agent": self.name,
            "role": self.role.value,
        }

    def _execute_infra_task(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Execute infrastructure task"""
        infra_prompt = f"""
{prompt}

Provide infrastructure specifications including:
1. Configuration files (Terraform, Docker, K8s)
2. Environment variables
3. Security considerations
4. Monitoring and logging setup
5. Scaling configuration
"""
        response = self.query_llm(infra_prompt)

        return {
            "type": "infrastructure",
            "content": response,
            "agent": self.name,
            "role": self.role.value,
        }

    def _execute_general_task(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Execute general task"""
        response = self.query_llm(prompt)

        return {
            "type": "general",
            "content": response,
            "agent": self.name,
            "role": self.role.value,
        }

    def __repr__(self) -> str:
        team_num = list(TeamEnum).index(self.team) + 1
        return f"<TeamAgent {self.name} [Team {team_num}] ({self.role.value}) - {self.status.value}>"
