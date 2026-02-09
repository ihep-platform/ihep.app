"""
Base Agent Class for IHEP Swarm

Provides core functionality for all agents in the swarm.

Author: Jason M Jarmacz | jason@ihep.app
Co-Author: Claude by Anthropic
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
from loguru import logger

from ..config.models import (
    Agent,
    Task,
    StatusEnum,
    RankEnum,
    TeamRoleEnum,
    MOSEnum,
    Order,
    SitRep,
    CasRep,
)
from ..llm import OllamaClient


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the IHEP swarm.

    Provides core functionality including:
    - LLM access for task execution
    - Status management
    - Communication (orders, sitreps, casreps)
    - Task execution framework
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "",
        rank: RankEnum = RankEnum.LIEUTENANT,
        role: TeamRoleEnum = TeamRoleEnum.CODING_AGENT,
        mos: MOSEnum = MOSEnum.CD_CODING_AGENT,
        llm_client: Optional[OllamaClient] = None,
        commander_id: Optional[str] = None,
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Unique identifier (auto-generated if not provided)
            name: Human-readable agent name
            rank: Military rank for hierarchy
            role: Team role (system_architect, lead_developer, etc.)
            mos: Military Occupational Specialty
            llm_client: Shared Ollama client for LLM access
            commander_id: ID of commanding officer
        """
        self.agent_id = agent_id or str(uuid4())
        self.name = name or f"Agent-{self.agent_id[:8]}"
        self.rank = rank
        self.role = role
        self.mos = mos
        self.llm_client = llm_client or OllamaClient()
        self.commander_id = commander_id

        # Status tracking
        self.status = StatusEnum.STANDBY
        self.current_task: Optional[Task] = None
        self.current_mission_id: Optional[str] = None

        # Performance metrics
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.performance_score = 1.0

        # Subordinates (for officers)
        self.subordinates: List[str] = []

        # Metadata
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.now()

        logger.info(f"Agent initialized: {self.name} [{self.rank.value}] ({self.mos.value})")

    # =========================================================================
    # ABSTRACT METHODS
    # =========================================================================

    @abstractmethod
    def execute_task(self, task: Task) -> Any:
        """
        Execute assigned task.

        Must be implemented by subclasses with role-specific logic.

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        pass

    @abstractmethod
    def build_task_prompt(self, task: Task) -> str:
        """
        Build LLM prompt for task execution.

        Must be implemented by subclasses with role-specific prompting.

        Args:
            task: Task to build prompt for

        Returns:
            Formatted prompt string
        """
        pass

    # =========================================================================
    # LLM INTERACTION
    # =========================================================================

    def query_llm(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Query the LLM with role-appropriate settings.

        Args:
            prompt: User prompt
            model: Model to use (auto-selected if not specified)
            system_prompt: Optional system context

        Returns:
            LLM response
        """
        # Select model based on role if not specified
        if model is None:
            model = self._get_default_model()

        return self.llm_client.query(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=self._get_temperature(),
        )

    def _get_default_model(self) -> str:
        """Get default model based on agent role"""
        if self.role in [TeamRoleEnum.CODING_AGENT, TeamRoleEnum.API_AGENT]:
            return "codellama"
        elif self.role == TeamRoleEnum.SYSTEM_ARCHITECT:
            # Use larger model if available
            if self.llm_client.is_model_available("llama3:70b"):
                return "llama3:70b"
            return "llama3"
        else:
            return "llama3"

    def _get_temperature(self) -> float:
        """Get temperature based on agent role"""
        if self.role in [TeamRoleEnum.CODING_AGENT, TeamRoleEnum.API_AGENT]:
            return 0.3  # More deterministic for code
        elif self.role == TeamRoleEnum.SYSTEM_ARCHITECT:
            return 0.5  # Balanced for analysis
        elif self.role == TeamRoleEnum.UX_UI_DESIGNER:
            return 0.7  # More creative
        else:
            return 0.5  # Default

    # =========================================================================
    # TASK MANAGEMENT
    # =========================================================================

    def assign_task(self, task: Task) -> bool:
        """
        Assign a task to this agent.

        Args:
            task: Task to assign

        Returns:
            True if assignment successful
        """
        if self.status == StatusEnum.ENGAGED:
            logger.warning(f"{self.name} is already engaged on another task")
            return False

        self.current_task = task
        task.assigned_to = self.agent_id
        task.status = StatusEnum.ACTIVE
        self.status = StatusEnum.ENGAGED

        logger.info(f"{self.name} assigned task: {task.description[:50]}...")
        return True

    def complete_task(self, result: Any) -> Task:
        """
        Mark current task as complete.

        Args:
            result: Task result

        Returns:
            Completed task
        """
        if not self.current_task:
            raise ValueError("No task currently assigned")

        self.current_task.status = StatusEnum.COMPLETE
        self.current_task.result = result
        self.current_task.completed_at = datetime.now()

        self.tasks_completed += 1
        self._update_performance_score(success=True)

        completed_task = self.current_task
        self.current_task = None
        self.status = StatusEnum.ACTIVE

        logger.info(f"{self.name} completed task: {completed_task.id}")
        return completed_task

    def fail_task(self, error: str) -> Task:
        """
        Mark current task as failed.

        Args:
            error: Error message

        Returns:
            Failed task
        """
        if not self.current_task:
            raise ValueError("No task currently assigned")

        self.current_task.status = StatusEnum.FAILED
        self.current_task.error = error
        self.current_task.completed_at = datetime.now()

        self.tasks_failed += 1
        self._update_performance_score(success=False)

        failed_task = self.current_task
        self.current_task = None
        self.status = StatusEnum.ACTIVE

        logger.error(f"{self.name} failed task: {failed_task.id} - {error}")
        return failed_task

    def _update_performance_score(self, success: bool):
        """Update agent performance score based on task outcome"""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks > 0:
            # Weighted average favoring recent performance
            current_rate = self.tasks_completed / total_tasks
            self.performance_score = 0.8 * self.performance_score + 0.2 * (1.0 if success else 0.0)

    # =========================================================================
    # COMMUNICATION
    # =========================================================================

    def receive_order(self, order: Order) -> bool:
        """
        Receive and acknowledge an order from commander.

        Args:
            order: Order from superior

        Returns:
            True if order acknowledged
        """
        order.acknowledged_at = datetime.now()
        logger.info(f"{self.name} received order from {order.from_agent}: {order.order_type}")
        return True

    def report_sitrep(self) -> SitRep:
        """
        Generate situation report for commander.

        Returns:
            SitRep with current status
        """
        progress = 0.0
        if self.current_task:
            # Estimate progress (could be enhanced with actual tracking)
            progress = 0.5 if self.status == StatusEnum.ENGAGED else 0.0

        return SitRep(
            from_agent=self.agent_id,
            to_agent=self.commander_id,
            status=self.status,
            current_task=self.current_task.id if self.current_task else None,
            progress=progress,
            message=f"{self.name} status: {self.status.value}",
            blockers=[],
        )

    def report_casrep(self, error: Exception, task: Optional[Task] = None) -> CasRep:
        """
        Generate casualty report for failure.

        Args:
            error: Exception that caused failure
            task: Task that failed (if applicable)

        Returns:
            CasRep with failure details
        """
        import traceback

        return CasRep(
            agent_id=self.agent_id,
            failure_type="error",
            error_message=str(error),
            task_id=task.id if task else None,
            stack_trace=traceback.format_exc(),
        )

    # =========================================================================
    # HIERARCHY
    # =========================================================================

    def add_subordinate(self, subordinate_id: str):
        """Add agent to subordinate list"""
        if subordinate_id not in self.subordinates:
            self.subordinates.append(subordinate_id)
            logger.debug(f"{self.name} added subordinate: {subordinate_id}")

    def remove_subordinate(self, subordinate_id: str):
        """Remove agent from subordinate list"""
        if subordinate_id in self.subordinates:
            self.subordinates.remove(subordinate_id)

    def can_command(self, subordinate_rank: RankEnum) -> bool:
        """Check if this agent can command given rank"""
        rank_order = [
            RankEnum.LIEUTENANT,
            RankEnum.CAPTAIN,
            RankEnum.MAJOR,
            RankEnum.COLONEL,
            RankEnum.GENERAL,
        ]
        try:
            return rank_order.index(self.rank) > rank_order.index(subordinate_rank)
        except ValueError:
            return False

    def is_officer(self) -> bool:
        """Check if agent is officer rank"""
        return self.rank in [RankEnum.GENERAL, RankEnum.COLONEL, RankEnum.MAJOR]

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary for persistence"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "rank": self.rank.value,
            "role": self.role.value,
            "mos": self.mos.value,
            "status": self.status.value,
            "commander_id": self.commander_id,
            "subordinates": self.subordinates,
            "current_task_id": self.current_task.id if self.current_task else None,
            "current_mission_id": self.current_mission_id,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "performance_score": self.performance_score,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Agent {self.name} [{self.rank.value}] ({self.role.value}) - {self.status.value}>"
