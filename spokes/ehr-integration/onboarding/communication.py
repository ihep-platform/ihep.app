"""
Communication Manager

Handles automated outreach, follow-ups, and status notifications
throughout the EHR provider onboarding lifecycle. Generates
communications from templates, records delivery status, and manages
follow-up scheduling.

Supports email (via GCP Pub/Sub to a mail service), in-app notifications,
and webhook callbacks.

Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from string import Template

from onboarding.models import (
    OnboardingPhase,
    OnboardingState,
    CommunicationType,
    CommunicationRecord,
    ProviderProfile,
    OnboardingEvent,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Communication templates
# ---------------------------------------------------------------------------

TEMPLATES: Dict[str, Dict[str, str]] = {
    CommunicationType.INITIAL_OUTREACH.value: {
        "subject": "IHEP Platform - EHR Integration Partnership Inquiry",
        "body": (
            "Dear $contact_name,\n\n"
            "I'm reaching out from the IHEP Platform regarding a potential "
            "EHR integration partnership with $organization_name.\n\n"
            "IHEP provides a comprehensive health engagement platform that "
            "integrates with Electronic Health Record systems to enable "
            "seamless bidirectional data exchange using FHIR R4 standards.\n\n"
            "We would like to explore connecting with your $ehr_vendor system "
            "to enable:\n"
            "- Patient demographic synchronization\n"
            "- Clinical observation data exchange\n"
            "- Appointment scheduling integration\n"
            "- Real-time event notifications via webhooks\n\n"
            "Our integration supports SMART on FHIR, OAuth 2.0, and HL7 v2.x "
            "protocols, and we have established sandbox environments for "
            "testing.\n\n"
            "Could we schedule a brief call to discuss the integration scope "
            "and technical requirements?\n\n"
            "Best regards,\n"
            "IHEP Integration Team\n"
            "integration@ihep.app"
        ),
    },
    CommunicationType.FOLLOW_UP.value: {
        "subject": "IHEP Platform - Follow Up: EHR Integration Partnership",
        "body": (
            "Dear $contact_name,\n\n"
            "I wanted to follow up on our previous communication regarding "
            "EHR integration between IHEP and $organization_name.\n\n"
            "We're ready to proceed with the next steps whenever your team "
            "is available. The current status of our integration setup is:\n\n"
            "- Current Phase: $current_phase\n"
            "- Completion: $completion_percentage%\n\n"
            "$custom_message\n\n"
            "Please let us know if you need any additional information or "
            "if there are any blockers on your end.\n\n"
            "Best regards,\n"
            "IHEP Integration Team\n"
            "integration@ihep.app"
        ),
    },
    CommunicationType.CREDENTIAL_REQUEST.value: {
        "subject": "IHEP Platform - Sandbox Credentials Request for $ehr_vendor Integration",
        "body": (
            "Dear $contact_name,\n\n"
            "We are ready to begin sandbox testing for the $ehr_vendor "
            "integration with $organization_name.\n\n"
            "To proceed, we need the following credentials:\n\n"
            "1. Sandbox/Development FHIR API base URL\n"
            "2. OAuth 2.0 Client ID and Client Secret\n"
            "   (or API key, depending on your authentication model)\n"
            "3. Any required tenant or practice identifiers\n"
            "4. Available OAuth scopes for our integration\n"
            "5. Webhook endpoint configuration details (if applicable)\n\n"
            "All credentials will be stored securely using Google Cloud "
            "Secret Manager with encryption at rest and strict access "
            "controls.\n\n"
            "Our technical specifications:\n"
            "- FHIR Version: R4\n"
            "- Auth: SMART on FHIR / OAuth 2.0 Backend Services\n"
            "- IHEP Application ID: $provider_id\n\n"
            "Please share credentials through your preferred secure "
            "channel.\n\n"
            "Best regards,\n"
            "IHEP Integration Team\n"
            "integration@ihep.app"
        ),
    },
    CommunicationType.SANDBOX_INVITATION.value: {
        "subject": "IHEP Platform - Sandbox Environment Ready for $organization_name",
        "body": (
            "Dear $contact_name,\n\n"
            "Great news! Your sandbox environment for the $ehr_vendor "
            "integration is configured and ready for testing.\n\n"
            "Sandbox Details:\n"
            "- Mirth Channel: $mirth_channel\n"
            "- Inbound Endpoint: $inbound_endpoint\n"
            "- Webhook URL: $webhook_url\n\n"
            "We will begin automated connectivity testing shortly and will "
            "share the results with you.\n\n"
            "Next steps:\n"
            "1. Confirm the sandbox endpoints are accessible\n"
            "2. We'll run our automated test suite\n"
            "3. Review the validation report together\n\n"
            "Best regards,\n"
            "IHEP Integration Team\n"
            "integration@ihep.app"
        ),
    },
    CommunicationType.VALIDATION_REPORT.value: {
        "subject": "IHEP Platform - Integration Validation Report for $organization_name",
        "body": (
            "Dear $contact_name,\n\n"
            "Please find below the validation report for the $ehr_vendor "
            "integration with $organization_name.\n\n"
            "Test Results Summary:\n"
            "$test_summary\n\n"
            "Detailed Results:\n"
            "$test_details\n\n"
            "$action_items\n\n"
            "Please review the results and let us know if you have any "
            "questions or if any adjustments are needed.\n\n"
            "Best regards,\n"
            "IHEP Integration Team\n"
            "integration@ihep.app"
        ),
    },
    CommunicationType.PRODUCTION_READINESS.value: {
        "subject": "IHEP Platform - Production Readiness for $organization_name",
        "body": (
            "Dear $contact_name,\n\n"
            "All sandbox testing has been completed successfully for the "
            "$ehr_vendor integration with $organization_name.\n\n"
            "Completion Summary:\n"
            "- Sandbox Tests Passed: $tests_passed/$tests_total\n"
            "- Data Validation: $data_validation_status\n"
            "- Completion: $completion_percentage%\n\n"
            "We are now ready to move to production. To proceed, we need:\n\n"
            "1. Production FHIR API endpoint URL\n"
            "2. Production OAuth 2.0 credentials\n"
            "3. Production webhook configuration\n"
            "4. Any production-specific rate limit requirements\n"
            "5. Go-live approval from your team\n\n"
            "Best regards,\n"
            "IHEP Integration Team\n"
            "integration@ihep.app"
        ),
    },
    CommunicationType.GO_LIVE_NOTIFICATION.value: {
        "subject": "IHEP Platform - Integration Go-Live: $organization_name",
        "body": (
            "Dear $contact_name,\n\n"
            "We are pleased to confirm that the $ehr_vendor integration "
            "between IHEP and $organization_name is now LIVE in production.\n\n"
            "Integration Details:\n"
            "- Partner ID: $provider_id\n"
            "- Sync Mode: $sync_mode\n"
            "- Data Scope: $data_scope\n"
            "- Go-Live Date: $go_live_date\n\n"
            "Monitoring is active and we will proactively notify you of "
            "any connectivity issues.\n\n"
            "For support, please contact integration@ihep.app.\n\n"
            "Best regards,\n"
            "IHEP Integration Team\n"
            "integration@ihep.app"
        ),
    },
    CommunicationType.STATUS_UPDATE.value: {
        "subject": "IHEP Platform - Integration Status Update: $organization_name",
        "body": (
            "Dear $contact_name,\n\n"
            "Here is a status update for the $ehr_vendor integration "
            "with $organization_name.\n\n"
            "Current Status:\n"
            "- Phase: $current_phase\n"
            "- Status: $overall_status\n"
            "- Completion: $completion_percentage%\n\n"
            "$custom_message\n\n"
            "Best regards,\n"
            "IHEP Integration Team\n"
            "integration@ihep.app"
        ),
    },
    CommunicationType.ESCALATION.value: {
        "subject": "IHEP Platform - ESCALATION: $organization_name Integration Blocked",
        "body": (
            "Dear $contact_name,\n\n"
            "The $ehr_vendor integration with $organization_name has "
            "encountered an issue that requires attention.\n\n"
            "Issue Details:\n"
            "- Phase: $current_phase\n"
            "- Blocked Reason: $blocked_reason\n"
            "- Duration Blocked: $blocked_duration\n\n"
            "Required Action:\n"
            "$action_required\n\n"
            "Please respond at your earliest convenience so we can "
            "resolve this and proceed with the integration.\n\n"
            "Best regards,\n"
            "IHEP Integration Team\n"
            "integration@ihep.app"
        ),
    },
    CommunicationType.HEALTH_ALERT.value: {
        "subject": "IHEP Platform - Health Alert: $organization_name Integration",
        "body": (
            "Dear $contact_name,\n\n"
            "Our monitoring system has detected an issue with the "
            "$ehr_vendor integration for $organization_name.\n\n"
            "Alert Details:\n"
            "- Issue: $alert_description\n"
            "- Detected At: $alert_timestamp\n"
            "- Severity: $alert_severity\n\n"
            "Our team is investigating. We will provide an update "
            "within $sla_hours hours.\n\n"
            "Best regards,\n"
            "IHEP Integration Team\n"
            "integration@ihep.app"
        ),
    },
}

# Map phases to the communications that should be triggered
PHASE_COMMUNICATIONS: Dict[str, str] = {
    OnboardingPhase.OUTREACH.value: CommunicationType.INITIAL_OUTREACH.value,
    OnboardingPhase.CREDENTIALING.value: CommunicationType.CREDENTIAL_REQUEST.value,
    OnboardingPhase.SANDBOX_TESTING.value: CommunicationType.SANDBOX_INVITATION.value,
    OnboardingPhase.DATA_VALIDATION.value: CommunicationType.VALIDATION_REPORT.value,
    OnboardingPhase.PRODUCTION_SETUP.value: CommunicationType.PRODUCTION_READINESS.value,
    OnboardingPhase.GO_LIVE.value: CommunicationType.GO_LIVE_NOTIFICATION.value,
}


class CommunicationManager:
    """
    Generates, sends, and tracks communications for provider onboarding.

    Communications are generated from templates with variable substitution,
    delivered via GCP Pub/Sub (which routes to the appropriate delivery
    channel), and recorded in the onboarding state for audit purposes.
    """

    def __init__(self, pubsub_topic: Optional[str] = None):
        self.pubsub_topic = pubsub_topic or os.getenv(
            "PUBSUB_TOPIC_COMMUNICATIONS",
            "ihep-onboarding-communications",
        )
        self._publisher = None

    # ------------------------------------------------------------------
    # Template rendering
    # ------------------------------------------------------------------

    def render_template(
        self,
        communication_type: str,
        variables: Dict[str, str],
    ) -> Dict[str, str]:
        """
        Render a communication template with the given variables.

        Returns a dict with ``subject`` and ``body`` keys.
        Missing variables are replaced with empty strings.
        """
        template_def = TEMPLATES.get(communication_type)
        if not template_def:
            raise ValueError(f"Unknown communication type: {communication_type}")

        # Use safe_substitute to avoid KeyError on missing variables
        subject_tmpl = Template(template_def["subject"])
        body_tmpl = Template(template_def["body"])

        return {
            "subject": subject_tmpl.safe_substitute(variables),
            "body": body_tmpl.safe_substitute(variables),
        }

    def build_variables(
        self,
        state: OnboardingState,
        extra: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Build template variables from the onboarding state."""
        profile = state.provider_profile
        contact = profile.primary_contact() if profile else None

        variables = {
            "provider_id": state.provider_id,
            "organization_name": profile.organization_name if profile else "",
            "ehr_vendor": profile.ehr_vendor if profile else "",
            "contact_name": contact.name if contact else "Integration Team",
            "contact_email": contact.email if contact else "",
            "current_phase": OnboardingPhase(state.current_phase).display_name,
            "overall_status": state.overall_status,
            "completion_percentage": str(state.completion_percentage()),
            "custom_message": "",
        }

        if extra:
            variables.update(extra)

        return variables

    # ------------------------------------------------------------------
    # Communication generation
    # ------------------------------------------------------------------

    def generate_phase_communication(
        self,
        state: OnboardingState,
        extra_variables: Optional[Dict[str, str]] = None,
    ) -> Optional[CommunicationRecord]:
        """
        Generate the appropriate communication for the current phase.

        Returns a ``CommunicationRecord`` ready to be sent, or None
        if no communication is mapped to the current phase.
        """
        comm_type = PHASE_COMMUNICATIONS.get(state.current_phase)
        if not comm_type:
            return None

        return self.create_communication(state, comm_type, extra_variables)

    def create_communication(
        self,
        state: OnboardingState,
        communication_type: str,
        extra_variables: Optional[Dict[str, str]] = None,
    ) -> CommunicationRecord:
        """Create a communication record from a template."""
        variables = self.build_variables(state, extra_variables)
        rendered = self.render_template(communication_type, variables)

        profile = state.provider_profile
        contact = profile.primary_contact() if profile else None
        recipient = contact.email if contact else (
            profile.technical_contact_email if profile else ""
        )

        record = CommunicationRecord(
            provider_id=state.provider_id,
            communication_type=communication_type,
            channel="email",
            recipient=recipient,
            subject=rendered["subject"],
            body=rendered["body"],
            template_id=communication_type,
            status="pending",
            metadata={"variables": variables},
        )

        return record

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    def send_communication(
        self,
        state: OnboardingState,
        record: CommunicationRecord,
    ) -> CommunicationRecord:
        """
        Send a communication and update the record status.

        In production, this publishes to GCP Pub/Sub where a mail
        delivery service picks it up.  In dev/test, it logs the
        communication.
        """
        try:
            delivered = self._deliver(record)
            if delivered:
                record.status = "sent"
                record.sent_at = datetime.utcnow().isoformat()
            else:
                record.status = "failed"
                record.error_message = "Delivery returned false"

        except Exception as e:
            record.status = "failed"
            record.error_message = str(e)
            logger.error(
                f"Failed to send communication {record.communication_id} "
                f"to {record.recipient}: {e}"
            )

        state.add_communication(record)
        state.add_event(OnboardingEvent(
            provider_id=state.provider_id,
            phase=state.current_phase,
            event_type="communication_sent",
            description=(
                f"{record.communication_type} sent to {record.recipient} "
                f"(status: {record.status})"
            ),
            metadata={
                "communication_id": record.communication_id,
                "type": record.communication_type,
                "status": record.status,
            },
        ))

        return record

    def send_phase_communication(
        self,
        state: OnboardingState,
        extra_variables: Optional[Dict[str, str]] = None,
    ) -> Optional[CommunicationRecord]:
        """Generate and send the communication for the current phase."""
        record = self.generate_phase_communication(state, extra_variables)
        if record:
            return self.send_communication(state, record)
        return None

    # ------------------------------------------------------------------
    # Follow-up scheduling
    # ------------------------------------------------------------------

    def check_follow_ups_needed(
        self,
        states: List[OnboardingState],
        follow_up_after_days: int = 3,
    ) -> List[OnboardingState]:
        """
        Identify providers who need a follow-up communication.

        A follow-up is needed when:
        - The provider is in WAITING_ON_PROVIDER status
        - The last communication was sent more than ``follow_up_after_days`` ago
        """
        needs_follow_up = []
        cutoff = datetime.utcnow() - timedelta(days=follow_up_after_days)

        for state in states:
            if state.overall_status != "waiting_on_provider":
                continue

            # Find last communication
            last_comm = None
            for comm in reversed(state.communications):
                if comm.status in ("sent", "delivered"):
                    last_comm = comm
                    break

            if not last_comm:
                needs_follow_up.append(state)
                continue

            sent_at = datetime.fromisoformat(last_comm.sent_at) if last_comm.sent_at else None
            if sent_at and sent_at < cutoff:
                needs_follow_up.append(state)

        return needs_follow_up

    def send_follow_ups(
        self,
        states: List[OnboardingState],
        custom_message: str = "",
    ) -> List[CommunicationRecord]:
        """Send follow-up communications to all providers that need them."""
        results = []
        for state in states:
            record = self.create_communication(
                state,
                CommunicationType.FOLLOW_UP.value,
                {"custom_message": custom_message},
            )
            sent = self.send_communication(state, record)
            results.append(sent)
        return results

    # ------------------------------------------------------------------
    # Delivery (abstracted for swappable backends)
    # ------------------------------------------------------------------

    def _deliver(self, record: CommunicationRecord) -> bool:
        """
        Deliver a communication via the configured channel.

        Production: Publishes to GCP Pub/Sub topic for async delivery.
        Development: Logs the communication content.
        """
        environment = os.getenv("ENVIRONMENT", "dev")

        if environment == "dev":
            logger.info(
                f"[DEV] Communication {record.communication_type} "
                f"to {record.recipient}:\n"
                f"  Subject: {record.subject}\n"
                f"  Body length: {len(record.body)} chars"
            )
            return True

        # Production: publish to Pub/Sub
        try:
            message_data = {
                "communication_id": record.communication_id,
                "channel": record.channel,
                "recipient": record.recipient,
                "subject": record.subject,
                "body": record.body,
                "metadata": record.metadata,
            }

            if self._publisher is None:
                from google.cloud import pubsub_v1
                self._publisher = pubsub_v1.PublisherClient()

            topic_path = self._publisher.topic_path(
                os.getenv("GCP_PROJECT", ""),
                self.pubsub_topic,
            )
            future = self._publisher.publish(
                topic_path,
                json.dumps(message_data).encode("utf-8"),
                communication_type=record.communication_type,
                provider_id=record.provider_id,
            )
            future.result(timeout=10)
            logger.info(
                f"Communication published to Pub/Sub: {record.communication_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Pub/Sub delivery failed: {e}")
            raise
