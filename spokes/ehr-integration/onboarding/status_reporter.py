"""
Status Reporter

Generates readiness reports, health dashboards, and operational
summaries for EHR provider integrations. Provides both real-time
status checks and periodic aggregate reporting.

Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict

from onboarding.models import (
    OnboardingPhase,
    OnboardingStatus,
    OnboardingState,
    ConnectionTest,
    ConnectionTestType,
)

logger = logging.getLogger(__name__)


@dataclass
class ProviderHealthStatus:
    """Health status snapshot for a single active provider."""
    provider_id: str
    organization_name: str = ""
    ehr_vendor: str = ""
    connection_status: str = "unknown"  # healthy, degraded, down, unknown
    last_sync_time: Optional[str] = None
    last_test_time: Optional[str] = None
    tests_passing: int = 0
    tests_total: int = 0
    avg_response_time_ms: float = 0.0
    consecutive_failures: int = 0
    alerts: List[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingDashboard:
    """Aggregate dashboard data across all providers."""
    total_providers: int = 0
    by_phase: Dict[str, int] = field(default_factory=dict)
    by_status: Dict[str, int] = field(default_factory=dict)
    by_vendor: Dict[str, int] = field(default_factory=dict)
    active_count: int = 0
    blocked_count: int = 0
    waiting_count: int = 0
    avg_completion: float = 0.0
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    health_statuses: List[ProviderHealthStatus] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["health_statuses"] = [h.to_dict() for h in self.health_statuses]
        return result


@dataclass
class ReadinessReport:
    """Production readiness assessment for a single provider."""
    provider_id: str
    organization_name: str = ""
    ehr_vendor: str = ""
    is_ready: bool = False
    readiness_score: float = 0.0  # 0-100
    current_phase: str = ""
    completion_percentage: float = 0.0
    checklist_summary: Dict[str, Dict[str, bool]] = field(default_factory=dict)
    test_summary: Dict[str, bool] = field(default_factory=dict)
    blockers: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StatusReporter:
    """
    Generates status reports, health dashboards, and readiness
    assessments for the EHR provider onboarding system.
    """

    # Health thresholds
    RESPONSE_TIME_WARNING_MS = 5000
    RESPONSE_TIME_CRITICAL_MS = 15000
    FAILURE_THRESHOLD_DEGRADED = 2
    FAILURE_THRESHOLD_DOWN = 5

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Provider health checks
    # ------------------------------------------------------------------

    def assess_provider_health(
        self,
        state: OnboardingState,
        sync_state: Optional[Dict[str, Any]] = None,
    ) -> ProviderHealthStatus:
        """
        Assess the current health of an active provider integration.

        Examines recent test results, sync state, and response times
        to determine if the connection is healthy, degraded, or down.
        """
        profile = state.provider_profile
        health = ProviderHealthStatus(
            provider_id=state.provider_id,
            organization_name=profile.organization_name if profile else "",
            ehr_vendor=profile.ehr_vendor if profile else "",
        )

        # Analyze latest test results
        latest_tests = state.latest_test_results()
        if latest_tests:
            health.tests_total = len(latest_tests)
            health.tests_passing = sum(1 for t in latest_tests.values() if t.passed)
            health.last_test_time = max(
                t.executed_at for t in latest_tests.values()
            )

            # Calculate average response time
            response_times = [
                t.response_time_ms
                for t in latest_tests.values()
                if t.response_time_ms > 0
            ]
            if response_times:
                health.avg_response_time_ms = sum(response_times) / len(response_times)

        # Determine connection status
        if health.tests_total == 0:
            health.connection_status = "unknown"
            health.alerts.append("No connection tests have been run")
        elif health.tests_passing == health.tests_total:
            if health.avg_response_time_ms > self.RESPONSE_TIME_CRITICAL_MS:
                health.connection_status = "degraded"
                health.alerts.append(
                    f"High response time: {health.avg_response_time_ms:.0f}ms"
                )
            elif health.avg_response_time_ms > self.RESPONSE_TIME_WARNING_MS:
                health.connection_status = "degraded"
                health.alerts.append(
                    f"Elevated response time: {health.avg_response_time_ms:.0f}ms"
                )
            else:
                health.connection_status = "healthy"
        elif health.tests_passing > health.tests_total / 2:
            health.connection_status = "degraded"
            failing_tests = [
                t.test_name for t in latest_tests.values() if not t.passed
            ]
            health.alerts.append(f"Failing tests: {', '.join(failing_tests)}")
        else:
            health.connection_status = "down"
            health.alerts.append(
                f"Only {health.tests_passing}/{health.tests_total} tests passing"
            )

        # Incorporate sync state if available
        if sync_state:
            health.last_sync_time = sync_state.get("last_inbound_sync")
            health.consecutive_failures = sync_state.get("consecutive_failures", 0)

            if health.consecutive_failures >= self.FAILURE_THRESHOLD_DOWN:
                health.connection_status = "down"
                health.alerts.append(
                    f"{health.consecutive_failures} consecutive sync failures"
                )
            elif health.consecutive_failures >= self.FAILURE_THRESHOLD_DEGRADED:
                if health.connection_status == "healthy":
                    health.connection_status = "degraded"
                health.alerts.append(
                    f"{health.consecutive_failures} consecutive sync failures"
                )

        return health

    # ------------------------------------------------------------------
    # Dashboard generation
    # ------------------------------------------------------------------

    def generate_dashboard(
        self,
        states: Dict[str, OnboardingState],
        sync_states: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> OnboardingDashboard:
        """
        Generate an aggregate dashboard across all onboarding providers.

        Provides phase distribution, status breakdown, vendor counts,
        and health summaries.
        """
        dashboard = OnboardingDashboard(total_providers=len(states))

        # Initialize phase and status counters
        for phase in OnboardingPhase.ordered():
            dashboard.by_phase[phase.value] = 0
        for status in OnboardingStatus:
            dashboard.by_status[status.value] = 0

        completion_sum = 0.0

        for provider_id, state in states.items():
            # Phase distribution
            dashboard.by_phase[state.current_phase] = (
                dashboard.by_phase.get(state.current_phase, 0) + 1
            )

            # Status distribution
            dashboard.by_status[state.overall_status] = (
                dashboard.by_status.get(state.overall_status, 0) + 1
            )

            # Vendor distribution
            vendor = (
                state.provider_profile.ehr_vendor
                if state.provider_profile else "unknown"
            )
            dashboard.by_vendor[vendor] = dashboard.by_vendor.get(vendor, 0) + 1

            # Completion
            completion_sum += state.completion_percentage()

            # Health for active providers
            if state.current_phase == OnboardingPhase.ACTIVE.value:
                dashboard.active_count += 1
                sync_data = (
                    sync_states.get(provider_id) if sync_states else None
                )
                health = self.assess_provider_health(state, sync_data)
                dashboard.health_statuses.append(health)

        # Blocked and waiting counts
        dashboard.blocked_count = dashboard.by_status.get(
            OnboardingStatus.BLOCKED.value, 0
        )
        dashboard.waiting_count = (
            dashboard.by_status.get(OnboardingStatus.WAITING_ON_PROVIDER.value, 0)
            + dashboard.by_status.get(OnboardingStatus.WAITING_ON_IHEP.value, 0)
        )

        # Average completion
        if states:
            dashboard.avg_completion = round(completion_sum / len(states), 1)

        # Collect recent events (last 50 across all providers)
        all_events = []
        for state in states.values():
            for event in state.events:
                all_events.append({
                    "provider_id": state.provider_id,
                    "organization_name": (
                        state.provider_profile.organization_name
                        if state.provider_profile else ""
                    ),
                    **event.to_dict(),
                })
        all_events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        dashboard.recent_events = all_events[:50]

        return dashboard

    # ------------------------------------------------------------------
    # Readiness reports
    # ------------------------------------------------------------------

    def generate_readiness_report(
        self,
        state: OnboardingState,
    ) -> ReadinessReport:
        """
        Generate a production readiness assessment for a provider.

        Evaluates checklist completion, test results, and identifies
        blockers and recommendations.
        """
        profile = state.provider_profile
        report = ReadinessReport(
            provider_id=state.provider_id,
            organization_name=profile.organization_name if profile else "",
            ehr_vendor=profile.ehr_vendor if profile else "",
            current_phase=state.current_phase,
            completion_percentage=state.completion_percentage(),
        )

        # Collect checklist status across all phases
        total_items = 0
        completed_items = 0
        for phase_val, ps in state.phase_states.items():
            if ps.checklist:
                phase_summary = {}
                for item_key, done in ps.checklist.items():
                    phase_summary[item_key] = done
                    total_items += 1
                    if done:
                        completed_items += 1
                report.checklist_summary[phase_val] = phase_summary

        # Collect test results
        latest_tests = state.latest_test_results()
        for test_type, test in latest_tests.items():
            report.test_summary[test.test_name] = test.passed

        # Calculate readiness score
        checklist_score = (completed_items / total_items * 60) if total_items else 0
        test_score = 0
        if latest_tests:
            passing = sum(1 for t in latest_tests.values() if t.passed)
            test_score = (passing / len(latest_tests)) * 40
        report.readiness_score = round(checklist_score + test_score, 1)

        # Identify blockers
        current_ps = state.phase_states.get(state.current_phase)
        if current_ps and current_ps.status == OnboardingStatus.BLOCKED.value:
            report.blockers.append(
                f"Phase '{state.current_phase}' is blocked: {current_ps.blocked_reason}"
            )

        for test_type, test in latest_tests.items():
            if not test.passed:
                report.blockers.append(
                    f"Test '{test.test_name}' failing: {test.error_message}"
                )

        # Generate recommendations
        if not latest_tests:
            report.recommendations.append(
                "Run connection test suite to validate endpoint connectivity"
            )

        ordered_phases = OnboardingPhase.ordered()
        current_idx = next(
            (i for i, p in enumerate(ordered_phases) if p.value == state.current_phase),
            0,
        )
        if current_idx < len(ordered_phases) - 1:
            next_phase = ordered_phases[current_idx + 1] if current_idx + 1 < len(ordered_phases) else None
            if next_phase:
                next_ps = state.phase_states.get(next_phase.value)
                if next_ps:
                    incomplete = [
                        k for k, v in (state.phase_states.get(state.current_phase).checklist or {}).items()
                        if not v
                    ]
                    if incomplete:
                        report.recommendations.append(
                            f"Complete remaining items in '{state.current_phase}': "
                            f"{', '.join(incomplete)}"
                        )

        # Determine overall readiness
        report.is_ready = (
            report.readiness_score >= 80
            and not report.blockers
            and state.current_phase in (
                OnboardingPhase.GO_LIVE.value,
                OnboardingPhase.ACTIVE.value,
            )
        )

        return report

    # ------------------------------------------------------------------
    # Aggregate operations report
    # ------------------------------------------------------------------

    def generate_operations_summary(
        self,
        states: Dict[str, OnboardingState],
    ) -> Dict[str, Any]:
        """
        Generate an operations summary suitable for stakeholder reporting.

        Returns a structured overview of the entire EHR integration
        program status.
        """
        active = []
        onboarding = []
        blocked = []
        completed_recently = []

        cutoff = datetime.utcnow() - timedelta(days=7)

        for state in states.values():
            summary = state.to_summary()

            if state.current_phase == OnboardingPhase.ACTIVE.value:
                active.append(summary)
            elif state.overall_status == OnboardingStatus.BLOCKED.value:
                blocked.append(summary)
            else:
                onboarding.append(summary)

            # Check for recently completed phases
            for ps in state.phase_states.values():
                if ps.completed_at:
                    completed_time = datetime.fromisoformat(ps.completed_at)
                    if completed_time > cutoff:
                        completed_recently.append({
                            "provider_id": state.provider_id,
                            "organization_name": summary.get("organization_name", ""),
                            "phase": ps.phase,
                            "completed_at": ps.completed_at,
                        })

        completed_recently.sort(
            key=lambda x: x["completed_at"], reverse=True
        )

        return {
            "report_type": "operations_summary",
            "generated_at": datetime.utcnow().isoformat(),
            "totals": {
                "total_providers": len(states),
                "active": len(active),
                "onboarding": len(onboarding),
                "blocked": len(blocked),
            },
            "active_integrations": active,
            "in_progress_onboarding": onboarding,
            "blocked_providers": blocked,
            "recently_completed_phases": completed_recently[:20],
            "vendor_distribution": self._count_vendors(states),
        }

    def _count_vendors(
        self, states: Dict[str, OnboardingState]
    ) -> Dict[str, int]:
        """Count providers by EHR vendor."""
        counts: Dict[str, int] = {}
        for state in states.values():
            vendor = (
                state.provider_profile.ehr_vendor
                if state.provider_profile else "unknown"
            )
            counts[vendor] = counts.get(vendor, 0) + 1
        return counts
