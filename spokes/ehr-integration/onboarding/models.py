"""
Onboarding Data Models

Defines the state machine phases, event log entries, provider profiles,
connection test results, and communication records that drive the
automated EHR provider onboarding workflow.

Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
"""

import uuid
import logging
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class OnboardingPhase(str, Enum):
    """
    Lifecycle phases for provider onboarding.

    The workflow progresses linearly through these phases, with the
    ability to revert to a previous phase if issues are discovered.
    """
    DISCOVERY = "discovery"
    OUTREACH = "outreach"
    ENGAGEMENT = "engagement"
    CREDENTIALING = "credentialing"
    SANDBOX_TESTING = "sandbox_testing"
    DATA_VALIDATION = "data_validation"
    PRODUCTION_SETUP = "production_setup"
    INITIAL_SYNC = "initial_sync"
    MONITORING_SETUP = "monitoring_setup"
    GO_LIVE = "go_live"
    ACTIVE = "active"

    @classmethod
    def ordered(cls) -> list:
        """Return phases in progression order."""
        return [
            cls.DISCOVERY,
            cls.OUTREACH,
            cls.ENGAGEMENT,
            cls.CREDENTIALING,
            cls.SANDBOX_TESTING,
            cls.DATA_VALIDATION,
            cls.PRODUCTION_SETUP,
            cls.INITIAL_SYNC,
            cls.MONITORING_SETUP,
            cls.GO_LIVE,
            cls.ACTIVE,
        ]

    def next_phase(self) -> Optional["OnboardingPhase"]:
        """Return the next phase in the sequence, or None if at the end."""
        ordered = self.ordered()
        idx = ordered.index(self)
        if idx + 1 < len(ordered):
            return ordered[idx + 1]
        return None

    def previous_phase(self) -> Optional["OnboardingPhase"]:
        """Return the previous phase, or None if at the beginning."""
        ordered = self.ordered()
        idx = ordered.index(self)
        if idx > 0:
            return ordered[idx - 1]
        return None

    @property
    def display_name(self) -> str:
        return self.value.replace("_", " ").title()


class OnboardingStatus(str, Enum):
    """Status within a given phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    WAITING_ON_PROVIDER = "waiting_on_provider"
    WAITING_ON_IHEP = "waiting_on_ihep"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CommunicationType(str, Enum):
    """Types of outbound communication."""
    INITIAL_OUTREACH = "initial_outreach"
    FOLLOW_UP = "follow_up"
    CREDENTIAL_REQUEST = "credential_request"
    SANDBOX_INVITATION = "sandbox_invitation"
    VALIDATION_REPORT = "validation_report"
    PRODUCTION_READINESS = "production_readiness"
    GO_LIVE_NOTIFICATION = "go_live_notification"
    STATUS_UPDATE = "status_update"
    ESCALATION = "escalation"
    HEALTH_ALERT = "health_alert"


class ConnectionTestType(str, Enum):
    """Categories of connection tests."""
    ENDPOINT_REACHABILITY = "endpoint_reachability"
    AUTHENTICATION = "authentication"
    FHIR_CAPABILITY = "fhir_capability"
    PATIENT_READ = "patient_read"
    OBSERVATION_READ = "observation_read"
    APPOINTMENT_READ = "appointment_read"
    WRITE_BACK = "write_back"
    WEBHOOK_DELIVERY = "webhook_delivery"
    RATE_LIMIT_COMPLIANCE = "rate_limit_compliance"
    DATA_COMPLETENESS = "data_completeness"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ProviderContact:
    """Contact person at an EHR provider or health system."""
    name: str
    email: str
    role: str = ""
    phone: str = ""
    is_primary: bool = False
    notes: str = ""


@dataclass
class ProviderProfile:
    """
    Complete profile of an EHR provider being onboarded.

    Captures organizational details, technical specifications,
    and contact information for the provider engagement.
    """
    provider_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_name: str = ""
    ehr_vendor: str = ""  # epic, cerner, allscripts, athenahealth, generic_fhir, hl7v2
    ehr_version: str = ""
    fhir_version: str = "R4"
    organization_type: str = ""  # hospital, clinic, health_system, practice
    size_category: str = ""  # small, medium, large, enterprise
    location: str = ""
    npi: str = ""  # National Provider Identifier
    contacts: List[ProviderContact] = field(default_factory=list)
    technical_contact_email: str = ""
    administrative_contact_email: str = ""
    base_url: str = ""
    auth_type: str = ""  # oauth2, smart_on_fhir, api_key, hl7_tcp
    supported_resources: List[str] = field(default_factory=list)
    desired_sync_mode: str = "bidirectional"
    desired_data_scope: Dict[str, bool] = field(default_factory=dict)
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def primary_contact(self) -> Optional[ProviderContact]:
        """Return the designated primary contact, or the first contact."""
        for c in self.contacts:
            if c.is_primary:
                return c
        return self.contacts[0] if self.contacts else None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingEvent:
    """
    Immutable record of an action or state change during onboarding.

    Events form an append-only audit trail for compliance and debugging.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str = ""
    phase: str = ""
    event_type: str = ""  # phase_entered, phase_completed, test_run, communication_sent, error, manual_override
    description: str = ""
    actor: str = "system"  # system, admin, provider
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConnectionTest:
    """Result of a single connection or integration test."""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str = ""
    test_type: str = ""  # From ConnectionTestType
    test_name: str = ""
    passed: bool = False
    response_time_ms: float = 0.0
    status_code: Optional[int] = None
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    executed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CommunicationRecord:
    """Record of a communication sent to or received from a provider."""
    communication_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str = ""
    communication_type: str = ""  # From CommunicationType
    channel: str = "email"  # email, webhook, pubsub, manual
    recipient: str = ""
    subject: str = ""
    body: str = ""
    template_id: str = ""
    status: str = "pending"  # pending, sent, delivered, failed, bounced
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PhaseState:
    """Tracks the status and metadata for a single onboarding phase."""
    phase: str
    status: str = OnboardingStatus.NOT_STARTED.value
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    blocked_reason: str = ""
    checklist: Dict[str, bool] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingState:
    """
    Complete onboarding state for a single provider.

    Aggregates the provider profile, current phase, per-phase status,
    event history, test results, and communication log into a single
    persistent record.
    """
    provider_id: str = ""
    current_phase: str = OnboardingPhase.DISCOVERY.value
    overall_status: str = OnboardingStatus.NOT_STARTED.value
    provider_profile: Optional[ProviderProfile] = None
    phase_states: Dict[str, PhaseState] = field(default_factory=dict)
    events: List[OnboardingEvent] = field(default_factory=list)
    connection_tests: List[ConnectionTest] = field(default_factory=list)
    communications: List[CommunicationRecord] = field(default_factory=list)
    partner_config_id: Optional[str] = None  # Link to partner_registry entry once created
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        """Initialize phase states for all phases if not already set."""
        if not self.phase_states:
            for phase in OnboardingPhase.ordered():
                self.phase_states[phase.value] = PhaseState(phase=phase.value)

    def get_phase_state(self, phase: OnboardingPhase) -> PhaseState:
        """Return the PhaseState for a given phase, creating it if needed."""
        if phase.value not in self.phase_states:
            self.phase_states[phase.value] = PhaseState(phase=phase.value)
        return self.phase_states[phase.value]

    def add_event(self, event: OnboardingEvent) -> None:
        """Append an event and update the timestamp."""
        self.events.append(event)
        self.updated_at = datetime.utcnow().isoformat()

    def add_test_result(self, test: ConnectionTest) -> None:
        """Record a connection test result."""
        self.connection_tests.append(test)
        self.updated_at = datetime.utcnow().isoformat()

    def add_communication(self, record: CommunicationRecord) -> None:
        """Record a communication."""
        self.communications.append(record)
        self.updated_at = datetime.utcnow().isoformat()

    def completion_percentage(self) -> float:
        """Calculate overall onboarding completion as a percentage."""
        phases = OnboardingPhase.ordered()
        completed = sum(
            1 for p in phases
            if self.phase_states.get(p.value, PhaseState(phase=p.value)).status
            in (OnboardingStatus.COMPLETED.value, OnboardingStatus.SKIPPED.value)
        )
        return round((completed / len(phases)) * 100, 1)

    def latest_test_results(self) -> Dict[str, ConnectionTest]:
        """Return the most recent test result for each test type."""
        latest: Dict[str, ConnectionTest] = {}
        for test in self.connection_tests:
            existing = latest.get(test.test_type)
            if not existing or test.executed_at > existing.executed_at:
                latest[test.test_type] = test
        return latest

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "current_phase": self.current_phase,
            "overall_status": self.overall_status,
            "provider_profile": self.provider_profile.to_dict() if self.provider_profile else None,
            "phase_states": {k: v.to_dict() for k, v in self.phase_states.items()},
            "events": [e.to_dict() for e in self.events],
            "connection_tests": [t.to_dict() for t in self.connection_tests],
            "communications": [c.to_dict() for c in self.communications],
            "partner_config_id": self.partner_config_id,
            "completion_percentage": self.completion_percentage(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_summary(self) -> Dict[str, Any]:
        """Compact summary for list views and dashboards."""
        profile = self.provider_profile
        latest_tests = self.latest_test_results()
        all_passing = all(t.passed for t in latest_tests.values()) if latest_tests else False
        return {
            "provider_id": self.provider_id,
            "organization_name": profile.organization_name if profile else "",
            "ehr_vendor": profile.ehr_vendor if profile else "",
            "current_phase": self.current_phase,
            "current_phase_display": OnboardingPhase(self.current_phase).display_name,
            "overall_status": self.overall_status,
            "completion_percentage": self.completion_percentage(),
            "connection_healthy": all_passing,
            "total_communications": len(self.communications),
            "total_tests": len(self.connection_tests),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
