"""
Procedural Registry Client

Validates agent actions against the Procedural Registry (POG framework).
Used by the orchestrator to enforce operational guidelines with tiered enforcement.
"""

import os
import logging
from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum

import aiohttp

logger = logging.getLogger(__name__)


class EnforcementLevel(Enum):
    ADVISORY = "advisory"  # Logged only, no action taken
    SOFT = "soft"  # Warning issued, action proceeds
    HARD = "hard"  # Action blocked if violated


@dataclass
class Violation:
    """A single rule violation"""
    procedure_id: str
    procedure_name: str
    rule_id: str
    message: str
    severity: str  # 'info', 'warning', 'error'


@dataclass
class ValidationResult:
    """Result of validating an action against procedures"""
    allowed: bool
    enforcement_level: EnforcementLevel
    violations: list[Violation]
    execution_ms: int

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def blocked(self) -> bool:
        return not self.allowed


class ProcedureClient:
    """
    Client for the Procedural Registry API.

    Validates agent actions against defined procedures with tiered enforcement:
    - advisory: Log violations only
    - soft: Warn but allow action
    - hard: Block action if violated
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the procedure client.

        Args:
            base_url: Base URL of the dashboard API (e.g., 'http://dashboard:3000')
                     Defaults to DASHBOARD_URL environment variable
        """
        self.base_url = base_url or os.getenv("DASHBOARD_URL", "http://dashboard.ihep-agents.svc.cluster.local:3000")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def validate(
        self,
        actor_type: str,
        actor_id: str,
        action: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate an action against applicable procedures.

        This is the main method for enforcing procedures. It:
        1. Finds procedures assigned to the actor
        2. Evaluates all rules
        3. Logs violations and execution metrics
        4. Returns whether the action is allowed

        Args:
            actor_type: Type of actor (e.g., 'agent', 'service', 'workflow')
            actor_id: Unique identifier of the actor
            action: The action being performed (e.g., 'send_email', 'deploy')
            context: Additional context for rule evaluation

        Returns:
            ValidationResult with allowed status and any violations

        Example:
            result = await client.validate(
                actor_type='agent',
                actor_id='investor-outreach',
                action='send_email',
                context={'approval_status': 'PENDING'}
            )
            if not result.allowed:
                logger.warning(f"Action blocked: {result.violations}")
        """
        session = await self._get_session()

        try:
            async with session.post(
                f"{self.base_url}/api/procedures/validate",
                json={
                    "actor_type": actor_type,
                    "actor_id": actor_id,
                    "action": action,
                    "context": context or {},
                },
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"Validation API error: {resp.status} - {error_text}")
                    # On API error, default to allowing the action (fail open)
                    return ValidationResult(
                        allowed=True,
                        enforcement_level=EnforcementLevel.ADVISORY,
                        violations=[],
                        execution_ms=0,
                    )

                data = await resp.json()

                violations = [
                    Violation(
                        procedure_id=v["procedure_id"],
                        procedure_name=v["procedure_name"],
                        rule_id=v["rule_id"],
                        message=v["message"],
                        severity=v["severity"],
                    )
                    for v in data.get("violations", [])
                ]

                return ValidationResult(
                    allowed=data.get("allowed", True),
                    enforcement_level=EnforcementLevel(data.get("enforcement_level", "advisory")),
                    violations=violations,
                    execution_ms=data.get("execution_ms", 0),
                )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to procedure registry: {e}")
            # On connection error, default to allowing the action (fail open)
            return ValidationResult(
                allowed=True,
                enforcement_level=EnforcementLevel.ADVISORY,
                violations=[],
                execution_ms=0,
            )

    async def would_block(
        self,
        actor_type: str,
        actor_id: str,
        action: str,
        context: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Quick check if an action would be blocked without logging.

        Use this for pre-flight checks before expensive operations.

        Args:
            actor_type: Type of actor
            actor_id: Unique identifier of the actor
            action: The action being performed
            context: Additional context for rule evaluation

        Returns:
            True if the action would be blocked, False otherwise
        """
        session = await self._get_session()

        try:
            async with session.post(
                f"{self.base_url}/api/procedures/validate?mode=would_block",
                json={
                    "actor_type": actor_type,
                    "actor_id": actor_id,
                    "action": action,
                    "context": context or {},
                },
            ) as resp:
                if resp.status != 200:
                    return False  # Fail open

                data = await resp.json()
                return data.get("would_block", False)

        except aiohttp.ClientError as e:
            logger.error(f"Failed to check procedure registry: {e}")
            return False  # Fail open

    async def check_violations(
        self,
        actor_type: str,
        actor_id: str,
        action: str,
        context: Optional[dict[str, Any]] = None,
    ) -> list[Violation]:
        """
        Get all violations for an action without logging.

        Useful for showing users what rules would be violated
        before they commit to an action.

        Args:
            actor_type: Type of actor
            actor_id: Unique identifier of the actor
            action: The action being performed
            context: Additional context for rule evaluation

        Returns:
            List of violations (may be empty)
        """
        session = await self._get_session()

        try:
            async with session.post(
                f"{self.base_url}/api/procedures/validate?mode=check",
                json={
                    "actor_type": actor_type,
                    "actor_id": actor_id,
                    "action": action,
                    "context": context or {},
                },
            ) as resp:
                if resp.status != 200:
                    return []

                data = await resp.json()
                return [
                    Violation(
                        procedure_id=v["procedure_id"],
                        procedure_name=v["procedure_name"],
                        rule_id=v["rule_id"],
                        message=v["message"],
                        severity=v["severity"],
                    )
                    for v in data.get("violations", [])
                ]

        except aiohttp.ClientError as e:
            logger.error(f"Failed to check violations: {e}")
            return []


# Convenience functions for common validation patterns

async def validate_agent_action(
    client: ProcedureClient,
    agent_id: str,
    action: str,
    context: Optional[dict[str, Any]] = None,
) -> ValidationResult:
    """Validate an agent action"""
    return await client.validate("agent", agent_id, action, context)


async def validate_workflow_step(
    client: ProcedureClient,
    workflow_id: str,
    step: str,
    context: Optional[dict[str, Any]] = None,
) -> ValidationResult:
    """Validate a workflow step transition"""
    return await client.validate("workflow", workflow_id, step, context)


async def validate_deployment(
    client: ProcedureClient,
    service_id: str,
    action: str = "deploy",
    context: Optional[dict[str, Any]] = None,
) -> ValidationResult:
    """Validate a deployment action"""
    return await client.validate("deployment", service_id, action, context)


async def validate_api_request(
    client: ProcedureClient,
    endpoint: str,
    context: Optional[dict[str, Any]] = None,
) -> ValidationResult:
    """Validate an API request"""
    return await client.validate("api", endpoint, "request", context)


# Example integration with orchestrator
"""
# In orchestrator.py:

from procedure_client import ProcedureClient, validate_agent_action

class Orchestrator:
    def __init__(self):
        self.procedure_client = ProcedureClient()

    async def process_agent_task(self, agent_id: str, task: dict):
        # Validate before executing
        result = await validate_agent_action(
            self.procedure_client,
            agent_id,
            task['action'],
            context={
                'approval_status': task.get('approval_status'),
                'task_type': task.get('type'),
                'priority': task.get('priority'),
            }
        )

        if not result.allowed:
            # Log blocked action
            logger.warning(
                f"Agent {agent_id} action {task['action']} blocked: "
                f"{[v.message for v in result.violations]}"
            )
            raise ActionBlockedError(result.violations)

        if result.has_violations:
            # Log warnings for soft violations
            for v in result.violations:
                logger.warning(
                    f"Procedure violation (soft): {v.procedure_name} - {v.message}"
                )

        # Proceed with action
        return await self._execute_task(agent_id, task)

    async def close(self):
        await self.procedure_client.close()
"""
