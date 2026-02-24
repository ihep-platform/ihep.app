"""
Provider Discovery

Automated system for discovering, profiling, and initiating outreach
to EHR providers. Manages the intake pipeline from provider identification
through initial engagement, including batch onboarding and automated
follow-up scheduling.

Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from onboarding.models import (
    OnboardingPhase,
    OnboardingStatus,
    OnboardingState,
    OnboardingEvent,
    ProviderProfile,
    ProviderContact,
    CommunicationType,
)
from onboarding.orchestrator import OnboardingOrchestrator
from onboarding.communication import CommunicationManager
from onboarding.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

# Vendor-specific configuration defaults
VENDOR_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "epic": {
        "auth_type": "smart_on_fhir",
        "fhir_version": "R4",
        "default_scopes": [
            "patient/Patient.read",
            "patient/Observation.read",
            "patient/Appointment.read",
            "patient/CarePlan.read",
            "launch/patient",
        ],
        "supported_resources": [
            "Patient", "Observation", "Appointment",
            "CarePlan", "Encounter", "DiagnosticReport",
        ],
        "data_scope": {
            "patients": True,
            "observations": True,
            "appointments": True,
            "care_plans": True,
            "medications": False,
            "encounters": True,
        },
    },
    "cerner": {
        "auth_type": "oauth2",
        "fhir_version": "R4",
        "default_scopes": [
            "patient/Patient.read",
            "patient/Observation.read",
            "patient/Appointment.read",
        ],
        "supported_resources": [
            "Patient", "Observation", "Appointment", "Encounter",
        ],
        "data_scope": {
            "patients": True,
            "observations": True,
            "appointments": True,
            "care_plans": True,
            "medications": False,
            "encounters": True,
        },
    },
    "allscripts": {
        "auth_type": "api_key",
        "fhir_version": "R4",
        "default_scopes": [],
        "supported_resources": [
            "Patient", "Observation", "Appointment",
        ],
        "data_scope": {
            "patients": True,
            "observations": True,
            "appointments": True,
            "care_plans": False,
            "medications": False,
            "encounters": False,
        },
    },
    "athenahealth": {
        "auth_type": "oauth2",
        "fhir_version": "R4",
        "default_scopes": [
            "patient/Patient.read",
            "patient/Observation.read",
            "patient/Appointment.read",
        ],
        "supported_resources": [
            "Patient", "Observation", "Appointment",
        ],
        "data_scope": {
            "patients": True,
            "observations": True,
            "appointments": True,
            "care_plans": False,
            "medications": False,
            "encounters": True,
        },
    },
}


class ProviderDiscovery:
    """
    Manages the discovery and intake pipeline for new EHR providers.

    Provides automated workflows for:
    - Creating provider profiles from intake data
    - Registering providers in the onboarding system
    - Initiating automated outreach communications
    - Batch-processing multiple providers
    - Scheduling follow-up for unresponsive providers
    - Running automated engagement cycles
    """

    def __init__(
        self,
        orchestrator: OnboardingOrchestrator,
        communication_manager: CommunicationManager,
        connection_manager: ConnectionManager,
    ):
        self.orchestrator = orchestrator
        self.comm_manager = communication_manager
        self.conn_manager = connection_manager

    # ------------------------------------------------------------------
    # Provider intake
    # ------------------------------------------------------------------

    def create_provider_profile(
        self,
        organization_name: str,
        ehr_vendor: str,
        contacts: Optional[List[Dict[str, str]]] = None,
        base_url: str = "",
        sync_mode: str = "bidirectional",
        **kwargs,
    ) -> ProviderProfile:
        """
        Create a provider profile from intake data.

        Applies vendor-specific defaults and validates required fields.
        """
        vendor_config = VENDOR_DEFAULTS.get(ehr_vendor, {})

        contact_objects = []
        if contacts:
            for i, c in enumerate(contacts):
                contact_objects.append(ProviderContact(
                    name=c.get("name", ""),
                    email=c.get("email", ""),
                    role=c.get("role", ""),
                    phone=c.get("phone", ""),
                    is_primary=(i == 0),
                ))

        profile = ProviderProfile(
            organization_name=organization_name,
            ehr_vendor=ehr_vendor,
            ehr_version=kwargs.get("ehr_version", ""),
            fhir_version=vendor_config.get("fhir_version", "R4"),
            organization_type=kwargs.get("organization_type", ""),
            size_category=kwargs.get("size_category", ""),
            location=kwargs.get("location", ""),
            npi=kwargs.get("npi", ""),
            contacts=contact_objects,
            technical_contact_email=kwargs.get("technical_contact_email", ""),
            administrative_contact_email=kwargs.get("administrative_contact_email", ""),
            base_url=base_url,
            auth_type=vendor_config.get("auth_type", "oauth2"),
            supported_resources=vendor_config.get("supported_resources", []),
            desired_sync_mode=sync_mode,
            desired_data_scope=vendor_config.get("data_scope", {}),
            notes=kwargs.get("notes", ""),
            tags=kwargs.get("tags", []),
        )

        return profile

    # ------------------------------------------------------------------
    # Automated onboarding initiation
    # ------------------------------------------------------------------

    def initiate_onboarding(
        self,
        profile: ProviderProfile,
        auto_outreach: bool = True,
    ) -> Dict[str, Any]:
        """
        Register a provider and optionally initiate automated outreach.

        This is the primary entry point for the automated onboarding
        pipeline. It:
        1. Registers the provider in the orchestrator
        2. Auto-completes discovery checklist items that can be inferred
        3. Advances to outreach phase
        4. Sends initial outreach communication
        """
        # Step 1: Register the provider
        state = self.orchestrator.register_provider(profile)

        # Step 2: Auto-complete discovery items from the profile
        discovery_items = {}
        if profile.organization_name and profile.ehr_vendor:
            discovery_items["provider_identified"] = True
            discovery_items["vendor_confirmed"] = True
        if profile.contacts:
            discovery_items["contacts_collected"] = True

        if discovery_items:
            self.orchestrator.update_checklist_items(
                provider_id=profile.provider_id,
                phase=OnboardingPhase.DISCOVERY,
                items=discovery_items,
                actor="system",
            )

        # Reload state after checklist updates (may have auto-advanced)
        state = self.orchestrator.get_state(profile.provider_id)

        # Step 3: Send initial outreach if we've advanced to outreach phase
        outreach_result = None
        if auto_outreach and state.current_phase == OnboardingPhase.OUTREACH.value:
            outreach_result = self._send_initial_outreach(state)

        result = {
            "provider_id": profile.provider_id,
            "organization_name": profile.organization_name,
            "current_phase": state.current_phase,
            "overall_status": state.overall_status,
            "completion_percentage": state.completion_percentage(),
            "outreach_sent": outreach_result is not None,
        }

        if outreach_result:
            result["outreach"] = {
                "communication_id": outreach_result.communication_id,
                "recipient": outreach_result.recipient,
                "status": outreach_result.status,
            }

        logger.info(
            f"Onboarding initiated for {profile.organization_name} "
            f"({profile.ehr_vendor}) -> {state.current_phase}"
        )
        return result

    def batch_initiate(
        self,
        providers: List[Dict[str, Any]],
        auto_outreach: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Batch-initiate onboarding for multiple providers.

        Each entry in ``providers`` should contain at minimum:
        - ``organization_name``
        - ``ehr_vendor``
        - ``contacts`` (list of dicts with name/email)
        """
        results = []
        for provider_data in providers:
            try:
                profile = self.create_provider_profile(**provider_data)
                result = self.initiate_onboarding(profile, auto_outreach)
                result["success"] = True
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Failed to initiate onboarding for "
                    f"{provider_data.get('organization_name', 'unknown')}: {e}"
                )
                results.append({
                    "organization_name": provider_data.get("organization_name", ""),
                    "success": False,
                    "error": str(e),
                })
        return results

    # ------------------------------------------------------------------
    # Engagement automation
    # ------------------------------------------------------------------

    def run_engagement_cycle(
        self,
        follow_up_after_days: int = 3,
        max_follow_ups: int = 3,
    ) -> Dict[str, Any]:
        """
        Run an automated engagement cycle across all onboarding providers.

        This is designed to be called periodically (e.g. daily via cron
        or Cloud Scheduler) to:
        1. Send follow-ups to providers waiting on response
        2. Escalate providers that have exceeded follow-up limits
        3. Run connection tests for providers in testing phases
        4. Advance providers that are ready for the next phase
        """
        all_states = self.orchestrator.get_all_states()
        cycle_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "providers_processed": 0,
            "follow_ups_sent": 0,
            "escalations": 0,
            "tests_run": 0,
            "phases_advanced": 0,
            "details": [],
        }

        for provider_id, state in all_states.items():
            if state.overall_status in (
                OnboardingStatus.COMPLETED.value,
                OnboardingStatus.FAILED.value,
            ):
                continue

            cycle_results["providers_processed"] += 1
            provider_result = {"provider_id": provider_id, "actions": []}

            # Check if follow-up is needed
            if state.overall_status == OnboardingStatus.WAITING_ON_PROVIDER.value:
                follow_up_result = self._check_and_send_follow_up(
                    state, follow_up_after_days, max_follow_ups
                )
                if follow_up_result:
                    provider_result["actions"].append(follow_up_result)
                    if follow_up_result.get("type") == "follow_up":
                        cycle_results["follow_ups_sent"] += 1
                    elif follow_up_result.get("type") == "escalation":
                        cycle_results["escalations"] += 1

            # Run connection tests for providers in testing phases
            if state.current_phase in (
                OnboardingPhase.SANDBOX_TESTING.value,
                OnboardingPhase.DATA_VALIDATION.value,
            ):
                test_result = self._run_phase_tests(state)
                if test_result:
                    provider_result["actions"].append(test_result)
                    cycle_results["tests_run"] += 1

            # Check if any phase can be auto-advanced
            auto_advance = self._check_auto_advance(state)
            if auto_advance:
                provider_result["actions"].append(auto_advance)
                cycle_results["phases_advanced"] += 1

            if provider_result["actions"]:
                cycle_results["details"].append(provider_result)

        logger.info(
            f"Engagement cycle complete: {cycle_results['providers_processed']} processed, "
            f"{cycle_results['follow_ups_sent']} follow-ups, "
            f"{cycle_results['tests_run']} tests, "
            f"{cycle_results['phases_advanced']} advances"
        )
        return cycle_results

    # ------------------------------------------------------------------
    # Provider connection setup
    # ------------------------------------------------------------------

    def setup_provider_connection(
        self,
        provider_id: str,
        credentials: Dict[str, str],
        connection_details: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Set up the API connection for a provider.

        This is called when a provider responds with their credentials.
        It:
        1. Stores credentials securely
        2. Generates and saves partner configuration
        3. Runs initial connection tests
        4. Updates onboarding state accordingly
        """
        state = self.orchestrator.get_state(provider_id)
        if not state:
            raise ValueError(f"Provider not found: {provider_id}")

        profile = state.provider_profile
        if not profile:
            raise ValueError(f"No profile for provider: {provider_id}")

        # Update profile with connection details
        if connection_details:
            if "base_url" in connection_details:
                profile.base_url = connection_details["base_url"]
            if "auth_type" in connection_details:
                profile.auth_type = connection_details["auth_type"]

        # Store credentials
        creds_stored = self.conn_manager.store_credentials(
            provider_id, credentials, state
        )

        # Generate and save partner config
        config = self.conn_manager.generate_partner_config(
            profile, connection_details
        )
        config_path = self.conn_manager.save_partner_config(config, state)

        # Update credentialing checklist
        cred_items = {
            "sandbox_credentials_received": True,
            "credentials_stored": creds_stored,
            "partner_config_created": True,
        }
        self.orchestrator.update_checklist_items(
            provider_id=provider_id,
            phase=OnboardingPhase.CREDENTIALING,
            items=cred_items,
            actor="system",
        )

        # Run initial connection tests
        state = self.orchestrator.get_state(provider_id)
        test_results = self.conn_manager.run_test_suite(state)

        # Update sandbox testing checklist based on test results
        test_items = {}
        for test in test_results:
            if test.test_type == "endpoint_reachability" and test.passed:
                test_items["endpoint_reachable"] = True
            elif test.test_type == "authentication" and test.passed:
                test_items["authentication_successful"] = True
            elif test.test_type == "fhir_capability" and test.passed:
                test_items["capability_statement_valid"] = True
            elif test.test_type == "patient_read" and test.passed:
                test_items["patient_read_successful"] = True

        if test_items:
            self.orchestrator.update_checklist_items(
                provider_id=provider_id,
                phase=OnboardingPhase.SANDBOX_TESTING,
                items=test_items,
                actor="system",
            )

        state = self.orchestrator.get_state(provider_id)
        passed = sum(1 for t in test_results if t.passed)
        total = len(test_results)

        return {
            "provider_id": provider_id,
            "credentials_stored": creds_stored,
            "config_path": config_path,
            "tests_passed": passed,
            "tests_total": total,
            "current_phase": state.current_phase,
            "completion_percentage": state.completion_percentage(),
            "test_summary": self.conn_manager.format_test_summary(test_results),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send_initial_outreach(self, state: OnboardingState):
        """Send the initial outreach communication."""
        record = self.comm_manager.create_communication(
            state,
            CommunicationType.INITIAL_OUTREACH.value,
        )
        sent = self.comm_manager.send_communication(state, record)

        if sent.status in ("sent", "delivered"):
            self.orchestrator.complete_checklist_item(
                state.provider_id,
                OnboardingPhase.OUTREACH,
                "initial_contact_sent",
                actor="system",
            )
            self.orchestrator.set_waiting_on_provider(
                state.provider_id,
                "Awaiting response to initial outreach",
            )

        # Save the updated state
        self.orchestrator._save_state(state)
        return sent

    def _check_and_send_follow_up(
        self,
        state: OnboardingState,
        follow_up_after_days: int,
        max_follow_ups: int,
    ) -> Optional[Dict[str, Any]]:
        """Check if a follow-up is needed and send it."""
        # Count existing follow-ups
        follow_up_count = sum(
            1 for c in state.communications
            if c.communication_type == CommunicationType.FOLLOW_UP.value
            and c.status in ("sent", "delivered")
        )

        if follow_up_count >= max_follow_ups:
            # Escalate instead of another follow-up
            record = self.comm_manager.create_communication(
                state,
                CommunicationType.ESCALATION.value,
                {
                    "blocked_reason": "No response after multiple follow-ups",
                    "blocked_duration": f"{follow_up_count * follow_up_after_days} days",
                    "action_required": "Direct engagement required",
                },
            )
            self.comm_manager.send_communication(state, record)
            self.orchestrator._save_state(state)
            return {"type": "escalation", "follow_up_count": follow_up_count}

        # Check if enough time has passed since last communication
        needs_follow_up = self.comm_manager.check_follow_ups_needed(
            [state], follow_up_after_days
        )

        if needs_follow_up:
            records = self.comm_manager.send_follow_ups(needs_follow_up)
            self.orchestrator._save_state(state)
            return {
                "type": "follow_up",
                "follow_up_number": follow_up_count + 1,
                "sent": len(records),
            }

        return None

    def _run_phase_tests(self, state: OnboardingState) -> Optional[Dict[str, Any]]:
        """Run connection tests appropriate for the current phase."""
        try:
            results = self.conn_manager.run_test_suite(state)
            self.orchestrator._save_state(state)
            passed = sum(1 for r in results if r.passed)
            return {
                "type": "connection_test",
                "passed": passed,
                "total": len(results),
            }
        except Exception as e:
            logger.error(f"Test suite failed for {state.provider_id}: {e}")
            return None

    def _check_auto_advance(self, state: OnboardingState) -> Optional[Dict[str, Any]]:
        """Check if the current phase can be automatically advanced."""
        current = OnboardingPhase(state.current_phase)
        ps = state.get_phase_state(current)

        if ps.status == OnboardingStatus.COMPLETED.value:
            return None  # Already advancing

        if not ps.checklist:
            return None

        if all(ps.checklist.values()):
            try:
                self.orchestrator.advance_phase(state.provider_id, actor="system")
                return {
                    "type": "auto_advance",
                    "from_phase": current.value,
                    "to_phase": state.current_phase,
                }
            except ValueError:
                return None

        return None
