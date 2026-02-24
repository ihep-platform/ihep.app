"""
Provider Onboarding Orchestrator

Central state machine that drives the automated EHR provider onboarding
workflow. Manages phase transitions, triggers actions at each phase
(communication, testing, configuration), persists state, and emits
events for downstream consumption.

Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import yaml

from onboarding.models import (
    OnboardingPhase,
    OnboardingStatus,
    OnboardingState,
    OnboardingEvent,
    ProviderProfile,
    PhaseState,
)

logger = logging.getLogger(__name__)

# Directory where onboarding state files are persisted
_STATE_DIR = os.getenv(
    "ONBOARDING_STATE_DIR",
    os.path.join(os.path.dirname(__file__), "..", "data", "onboarding"),
)


class OnboardingOrchestrator:
    """
    Drives the EHR provider onboarding lifecycle.

    Each provider has an ``OnboardingState`` that tracks which phase they
    are in, what tests have been run, and what communications have been
    sent.  The orchestrator exposes high-level actions (advance, revert,
    block, complete) that update state and emit events.

    Persistence is file-based (JSON) for simplicity; production
    deployments can swap in a database-backed store.
    """

    # Phase-specific checklists define what must be true before a phase
    # can be marked complete.
    PHASE_CHECKLISTS: Dict[str, Dict[str, str]] = {
        OnboardingPhase.DISCOVERY.value: {
            "provider_identified": "Provider organization identified and profiled",
            "vendor_confirmed": "EHR vendor and version confirmed",
            "contacts_collected": "Technical and administrative contacts collected",
        },
        OnboardingPhase.OUTREACH.value: {
            "initial_contact_sent": "Initial outreach communication sent",
            "response_received": "Response received from provider",
        },
        OnboardingPhase.ENGAGEMENT.value: {
            "integration_scope_agreed": "Data scope and sync mode agreed upon",
            "timeline_established": "Integration timeline established",
            "technical_poc_assigned": "Technical point of contact assigned",
        },
        OnboardingPhase.CREDENTIALING.value: {
            "sandbox_credentials_received": "Sandbox/dev credentials received from provider",
            "credentials_stored": "Credentials stored in Secret Manager",
            "partner_config_created": "Partner configuration YAML created",
        },
        OnboardingPhase.SANDBOX_TESTING.value: {
            "endpoint_reachable": "FHIR/API endpoint reachable",
            "authentication_successful": "Authentication flow successful",
            "capability_statement_valid": "FHIR CapabilityStatement retrieved and validated",
            "patient_read_successful": "Patient resource read successful",
        },
        OnboardingPhase.DATA_VALIDATION.value: {
            "field_mappings_verified": "Field mappings verified against live data",
            "data_completeness_checked": "Data completeness meets minimum thresholds",
            "transformation_pipeline_tested": "FHIR-to-IHEP transformation tested end-to-end",
            "validation_report_sent": "Validation report sent to provider",
        },
        OnboardingPhase.PRODUCTION_SETUP.value: {
            "production_credentials_received": "Production credentials received",
            "production_credentials_stored": "Production credentials stored in Secret Manager",
            "mirth_channel_configured": "Mirth Connect channel configured for production",
            "rate_limits_configured": "Rate limits set per provider agreement",
        },
        OnboardingPhase.INITIAL_SYNC.value: {
            "bulk_sync_completed": "Initial bulk data sync completed",
            "data_integrity_verified": "Synced data integrity verified",
            "record_counts_confirmed": "Record counts match expected totals",
        },
        OnboardingPhase.MONITORING_SETUP.value: {
            "health_checks_active": "Automated health checks running",
            "alerting_configured": "Alert thresholds and notification channels configured",
            "audit_logging_verified": "Audit logging confirmed for HIPAA compliance",
        },
        OnboardingPhase.GO_LIVE.value: {
            "stakeholder_approval": "Stakeholder sign-off received",
            "go_live_notification_sent": "Go-live notification sent to provider",
            "production_traffic_enabled": "Production data flow enabled",
        },
        OnboardingPhase.ACTIVE.value: {},
    }

    def __init__(self, state_dir: Optional[str] = None):
        self.state_dir = state_dir or _STATE_DIR
        os.makedirs(self.state_dir, exist_ok=True)
        self._states: Dict[str, OnboardingState] = {}
        self._load_all_states()

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _state_path(self, provider_id: str) -> str:
        return os.path.join(self.state_dir, f"{provider_id}.json")

    def _load_all_states(self) -> None:
        """Load all persisted onboarding states from disk."""
        if not os.path.isdir(self.state_dir):
            return
        for filename in os.listdir(self.state_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(self.state_dir, filename)
            try:
                with open(filepath, "r") as fh:
                    data = json.load(fh)
                state = self._deserialize_state(data)
                self._states[state.provider_id] = state
            except Exception as e:
                logger.error(f"Failed to load onboarding state from {filepath}: {e}")

    def _save_state(self, state: OnboardingState) -> None:
        """Persist a single provider's onboarding state to disk."""
        filepath = self._state_path(state.provider_id)
        try:
            with open(filepath, "w") as fh:
                json.dump(state.to_dict(), fh, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save onboarding state for {state.provider_id}: {e}")

    def _deserialize_state(self, data: Dict[str, Any]) -> OnboardingState:
        """Reconstruct an OnboardingState from a persisted dictionary."""
        profile_data = data.get("provider_profile")
        profile = None
        if profile_data:
            from onboarding.models import ProviderContact
            contacts = [
                ProviderContact(**c)
                for c in profile_data.pop("contacts", [])
            ]
            profile = ProviderProfile(**{
                k: v for k, v in profile_data.items()
                if k in ProviderProfile.__dataclass_fields__
            })
            profile.contacts = contacts

        phase_states = {}
        for key, ps_data in data.get("phase_states", {}).items():
            phase_states[key] = PhaseState(**{
                k: v for k, v in ps_data.items()
                if k in PhaseState.__dataclass_fields__
            })

        from onboarding.models import OnboardingEvent, ConnectionTest, CommunicationRecord
        events = [
            OnboardingEvent(**{
                k: v for k, v in e.items()
                if k in OnboardingEvent.__dataclass_fields__
            }) for e in data.get("events", [])
        ]
        tests = [
            ConnectionTest(**{
                k: v for k, v in t.items()
                if k in ConnectionTest.__dataclass_fields__
            }) for t in data.get("connection_tests", [])
        ]
        comms = [
            CommunicationRecord(**{
                k: v for k, v in c.items()
                if k in CommunicationRecord.__dataclass_fields__
            }) for c in data.get("communications", [])
        ]

        state = OnboardingState(
            provider_id=data["provider_id"],
            current_phase=data.get("current_phase", OnboardingPhase.DISCOVERY.value),
            overall_status=data.get("overall_status", OnboardingStatus.NOT_STARTED.value),
            provider_profile=profile,
            phase_states=phase_states,
            events=events,
            connection_tests=tests,
            communications=comms,
            partner_config_id=data.get("partner_config_id"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
        )
        return state

    # ------------------------------------------------------------------
    # Provider lifecycle
    # ------------------------------------------------------------------

    def register_provider(self, profile: ProviderProfile) -> OnboardingState:
        """
        Register a new provider and begin the onboarding workflow.

        Creates the OnboardingState, initialises phase checklists,
        records a ``provider_registered`` event, and persists state.
        """
        state = OnboardingState(
            provider_id=profile.provider_id,
            current_phase=OnboardingPhase.DISCOVERY.value,
            overall_status=OnboardingStatus.IN_PROGRESS.value,
            provider_profile=profile,
        )

        # Initialise checklists from the class-level definitions
        for phase_value, checklist_items in self.PHASE_CHECKLISTS.items():
            ps = state.get_phase_state(OnboardingPhase(phase_value))
            ps.checklist = {key: False for key in checklist_items}

        state.add_event(OnboardingEvent(
            provider_id=profile.provider_id,
            phase=OnboardingPhase.DISCOVERY.value,
            event_type="provider_registered",
            description=(
                f"Provider '{profile.organization_name}' registered for onboarding "
                f"(vendor: {profile.ehr_vendor})"
            ),
        ))

        # Mark discovery phase as in-progress
        discovery = state.get_phase_state(OnboardingPhase.DISCOVERY)
        discovery.status = OnboardingStatus.IN_PROGRESS.value
        discovery.started_at = datetime.utcnow().isoformat()

        self._states[profile.provider_id] = state
        self._save_state(state)
        logger.info(f"Provider registered for onboarding: {profile.provider_id}")
        return state

    def get_state(self, provider_id: str) -> Optional[OnboardingState]:
        """Retrieve the current onboarding state for a provider."""
        return self._states.get(provider_id)

    def get_all_states(self) -> Dict[str, OnboardingState]:
        """Return all onboarding states."""
        return dict(self._states)

    # ------------------------------------------------------------------
    # Checklist management
    # ------------------------------------------------------------------

    def complete_checklist_item(
        self,
        provider_id: str,
        phase: OnboardingPhase,
        item_key: str,
        actor: str = "system",
    ) -> OnboardingState:
        """
        Mark a checklist item as complete within a phase.

        If all items for the phase are now complete, the phase is
        automatically marked ``COMPLETED`` and the workflow advances
        to the next phase.
        """
        state = self._require_state(provider_id)
        ps = state.get_phase_state(phase)

        if item_key not in ps.checklist:
            raise ValueError(
                f"Unknown checklist item '{item_key}' for phase {phase.value}"
            )

        ps.checklist[item_key] = True
        state.add_event(OnboardingEvent(
            provider_id=provider_id,
            phase=phase.value,
            event_type="checklist_item_completed",
            description=f"Checklist item '{item_key}' completed",
            actor=actor,
            metadata={"item_key": item_key},
        ))

        # Auto-advance if all items are done
        if all(ps.checklist.values()):
            self._complete_phase(state, phase, actor)

        self._save_state(state)
        return state

    def update_checklist_items(
        self,
        provider_id: str,
        phase: OnboardingPhase,
        items: Dict[str, bool],
        actor: str = "system",
    ) -> OnboardingState:
        """Batch-update multiple checklist items at once."""
        state = self._require_state(provider_id)
        ps = state.get_phase_state(phase)

        for key, value in items.items():
            if key in ps.checklist:
                ps.checklist[key] = value

        if all(ps.checklist.values()):
            self._complete_phase(state, phase, actor)

        self._save_state(state)
        return state

    # ------------------------------------------------------------------
    # Phase transitions
    # ------------------------------------------------------------------

    def advance_phase(
        self,
        provider_id: str,
        actor: str = "system",
        force: bool = False,
    ) -> OnboardingState:
        """
        Advance the provider to the next onboarding phase.

        By default, all checklist items for the current phase must be
        complete.  Set ``force=True`` to skip the check (e.g. manual
        override by an admin).
        """
        state = self._require_state(provider_id)
        current = OnboardingPhase(state.current_phase)
        ps = state.get_phase_state(current)

        if not force and not all(ps.checklist.values()):
            incomplete = [k for k, v in ps.checklist.items() if not v]
            raise ValueError(
                f"Cannot advance from {current.value}: "
                f"incomplete checklist items: {incomplete}"
            )

        self._complete_phase(state, current, actor)
        self._save_state(state)
        return state

    def revert_phase(
        self,
        provider_id: str,
        target_phase: OnboardingPhase,
        reason: str = "",
        actor: str = "admin",
    ) -> OnboardingState:
        """
        Revert the provider to an earlier phase.

        Used when an issue is discovered that requires re-doing earlier
        steps (e.g. credentials rotated, endpoint changed).
        """
        state = self._require_state(provider_id)
        current = OnboardingPhase(state.current_phase)
        ordered = OnboardingPhase.ordered()

        if ordered.index(target_phase) >= ordered.index(current):
            raise ValueError(
                f"Cannot revert forward: current={current.value}, target={target_phase.value}"
            )

        state.current_phase = target_phase.value
        ps = state.get_phase_state(target_phase)
        ps.status = OnboardingStatus.IN_PROGRESS.value
        ps.started_at = datetime.utcnow().isoformat()
        ps.completed_at = None

        state.add_event(OnboardingEvent(
            provider_id=provider_id,
            phase=target_phase.value,
            event_type="phase_reverted",
            description=f"Reverted from {current.value} to {target_phase.value}: {reason}",
            actor=actor,
            metadata={"from_phase": current.value, "reason": reason},
        ))

        self._save_state(state)
        logger.info(
            f"Provider {provider_id} reverted from {current.value} to {target_phase.value}"
        )
        return state

    def block_phase(
        self,
        provider_id: str,
        reason: str,
        actor: str = "system",
    ) -> OnboardingState:
        """Mark the current phase as blocked with a reason."""
        state = self._require_state(provider_id)
        current = OnboardingPhase(state.current_phase)
        ps = state.get_phase_state(current)
        ps.status = OnboardingStatus.BLOCKED.value
        ps.blocked_reason = reason
        state.overall_status = OnboardingStatus.BLOCKED.value

        state.add_event(OnboardingEvent(
            provider_id=provider_id,
            phase=current.value,
            event_type="phase_blocked",
            description=f"Phase {current.value} blocked: {reason}",
            actor=actor,
            metadata={"reason": reason},
        ))

        self._save_state(state)
        logger.warning(f"Provider {provider_id} blocked at {current.value}: {reason}")
        return state

    def unblock_phase(
        self,
        provider_id: str,
        resolution: str = "",
        actor: str = "admin",
    ) -> OnboardingState:
        """Unblock the current phase and resume progress."""
        state = self._require_state(provider_id)
        current = OnboardingPhase(state.current_phase)
        ps = state.get_phase_state(current)
        ps.status = OnboardingStatus.IN_PROGRESS.value
        ps.blocked_reason = ""
        state.overall_status = OnboardingStatus.IN_PROGRESS.value

        state.add_event(OnboardingEvent(
            provider_id=provider_id,
            phase=current.value,
            event_type="phase_unblocked",
            description=f"Phase {current.value} unblocked: {resolution}",
            actor=actor,
            metadata={"resolution": resolution},
        ))

        self._save_state(state)
        return state

    def set_waiting_on_provider(
        self,
        provider_id: str,
        description: str = "",
    ) -> OnboardingState:
        """Mark the current phase as waiting on provider action."""
        state = self._require_state(provider_id)
        current = OnboardingPhase(state.current_phase)
        ps = state.get_phase_state(current)
        ps.status = OnboardingStatus.WAITING_ON_PROVIDER.value
        state.overall_status = OnboardingStatus.WAITING_ON_PROVIDER.value

        state.add_event(OnboardingEvent(
            provider_id=provider_id,
            phase=current.value,
            event_type="waiting_on_provider",
            description=description or f"Waiting on provider action in {current.display_name}",
        ))

        self._save_state(state)
        return state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _complete_phase(
        self,
        state: OnboardingState,
        phase: OnboardingPhase,
        actor: str,
    ) -> None:
        """Mark a phase as complete and advance to the next."""
        ps = state.get_phase_state(phase)
        ps.status = OnboardingStatus.COMPLETED.value
        ps.completed_at = datetime.utcnow().isoformat()

        state.add_event(OnboardingEvent(
            provider_id=state.provider_id,
            phase=phase.value,
            event_type="phase_completed",
            description=f"Phase '{phase.display_name}' completed",
            actor=actor,
        ))

        next_phase = phase.next_phase()
        if next_phase:
            state.current_phase = next_phase.value
            next_ps = state.get_phase_state(next_phase)
            next_ps.status = OnboardingStatus.IN_PROGRESS.value
            next_ps.started_at = datetime.utcnow().isoformat()
            state.overall_status = OnboardingStatus.IN_PROGRESS.value

            state.add_event(OnboardingEvent(
                provider_id=state.provider_id,
                phase=next_phase.value,
                event_type="phase_entered",
                description=f"Entered phase '{next_phase.display_name}'",
                actor=actor,
            ))
            logger.info(
                f"Provider {state.provider_id} advanced to {next_phase.value}"
            )
        else:
            # All phases complete
            state.overall_status = OnboardingStatus.COMPLETED.value
            logger.info(f"Provider {state.provider_id} onboarding complete")

    def _require_state(self, provider_id: str) -> OnboardingState:
        """Return the state or raise if the provider is not registered."""
        state = self._states.get(provider_id)
        if not state:
            raise ValueError(f"Provider not found: {provider_id}")
        return state

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def get_providers_in_phase(self, phase: OnboardingPhase) -> List[OnboardingState]:
        """Return all providers currently in a given phase."""
        return [
            s for s in self._states.values()
            if s.current_phase == phase.value
        ]

    def get_blocked_providers(self) -> List[OnboardingState]:
        """Return all providers whose onboarding is currently blocked."""
        return [
            s for s in self._states.values()
            if s.overall_status == OnboardingStatus.BLOCKED.value
        ]

    def get_waiting_providers(self) -> List[OnboardingState]:
        """Return all providers waiting on external action."""
        return [
            s for s in self._states.values()
            if s.overall_status in (
                OnboardingStatus.WAITING_ON_PROVIDER.value,
                OnboardingStatus.WAITING_ON_IHEP.value,
            )
        ]

    def get_active_providers(self) -> List[OnboardingState]:
        """Return all providers that have completed onboarding and are active."""
        return [
            s for s in self._states.values()
            if s.current_phase == OnboardingPhase.ACTIVE.value
        ]
