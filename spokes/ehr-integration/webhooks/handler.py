"""
Webhook Event Handler

Processes incoming EHR webhook events with HMAC-SHA256 signature
verification, event type routing, GCP Pub/Sub integration for
asynchronous downstream processing, and automatic retry logic.
"""

import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)

# Event type constants
EVENT_TYPE_ADT = 'ADT'          # Admission/Discharge/Transfer
EVENT_TYPE_ORU = 'ORU'          # Observation Result
EVENT_TYPE_SIU = 'SIU'          # Scheduling
EVENT_TYPE_MDM = 'MDM'          # Medical Document Management
EVENT_TYPE_PATIENT = 'patient'
EVENT_TYPE_ENCOUNTER = 'encounter'
EVENT_TYPE_OBSERVATION = 'observation'
EVENT_TYPE_APPOINTMENT = 'appointment'

# Default retry configuration
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_RETRY_DELAY_SECONDS = 5
_DEFAULT_RETRY_BACKOFF_MULTIPLIER = 2.0

# GCP Pub/Sub configuration
_PUBSUB_PROJECT = None  # set from environment
_PUBSUB_TOPIC = 'ehr-webhook-events'


def _hash_identifier(identifier: str) -> str:
    """Hash identifier for safe logging (HIPAA compliance)."""
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


class WebhookEvent:
    """
    Represents a single inbound webhook event.

    Attributes:
        event_id: Unique event identifier.
        source: The originating EHR system identifier.
        event_type: Categorized event type (e.g. ``'patient.update'``).
        payload: Parsed event payload.
        raw_body: Original request body as a string.
        received_at: Timestamp when the event was received.
        status: Processing status (``'pending'``, ``'processing'``,
                ``'completed'``, ``'failed'``).
        retry_count: Number of processing attempts so far.
        error: Last error message if processing failed.
    """

    def __init__(
        self,
        source: str,
        event_type: str,
        payload: Dict[str, Any],
        raw_body: str = '',
    ) -> None:
        self.event_id: str = str(uuid.uuid4())
        self.source: str = source
        self.event_type: str = event_type
        self.payload: Dict[str, Any] = payload
        self.raw_body: str = raw_body
        self.received_at: str = datetime.utcnow().isoformat() + 'Z'
        self.status: str = 'pending'
        self.retry_count: int = 0
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the event to a dictionary for storage or Pub/Sub."""
        return {
            'event_id': self.event_id,
            'source': self.source,
            'event_type': self.event_type,
            'payload': self.payload,
            'received_at': self.received_at,
            'status': self.status,
            'retry_count': self.retry_count,
            'error': self.error,
        }


class WebhookHandler:
    """
    Central handler for incoming EHR webhook events.

    Responsibilities:
    - HMAC-SHA256 signature verification
    - Event classification and routing
    - Pub/Sub publishing for async processing
    - Synchronous processing with retry logic for critical events

    Usage::

        handler = WebhookHandler()
        result = handler.process_event(
            source='epic-prod',
            event_type='patient.update',
            payload=request_json,
            raw_body=request_body,
            partner_config=partner_config,
        )
    """

    def __init__(
        self,
        pubsub_project: Optional[str] = None,
        pubsub_topic: str = _PUBSUB_TOPIC,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        retry_delay_seconds: float = _DEFAULT_RETRY_DELAY_SECONDS,
        retry_backoff_multiplier: float = _DEFAULT_RETRY_BACKOFF_MULTIPLIER,
    ) -> None:
        self._pubsub_project = pubsub_project or _PUBSUB_PROJECT
        self._pubsub_topic = pubsub_topic
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._retry_backoff_multiplier = retry_backoff_multiplier
        self._publisher: Optional[pubsub_v1.PublisherClient] = None

        # Event routing table: event_type_prefix -> handler function
        self._route_handlers: Dict[str, Callable] = {}
        self._register_default_routes()

    # ------------------------------------------------------------------
    # Signature verification
    # ------------------------------------------------------------------

    @staticmethod
    def verify_signature(body: str, signature: str, secret: str) -> bool:
        """
        Verify an HMAC-SHA256 webhook signature.

        Args:
            body: The raw request body as a string.
            signature: The signature provided in the webhook header.
                       Supports both raw hex and ``sha256=<hex>`` formats.
            secret: The shared webhook secret for this partner.

        Returns:
            True if the signature is valid, False otherwise.
        """
        if not secret:
            logger.warning("Webhook secret is empty; signature verification skipped")
            return True

        if not signature:
            logger.warning("No signature provided for verification")
            return False

        # Strip optional prefix
        clean_signature = signature
        if clean_signature.startswith('sha256='):
            clean_signature = clean_signature[7:]
        elif clean_signature.startswith('SHA256='):
            clean_signature = clean_signature[7:]

        expected = hmac.new(
            secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, clean_signature)

    # ------------------------------------------------------------------
    # Event routing
    # ------------------------------------------------------------------

    def _register_default_routes(self) -> None:
        """Register default event type handlers."""
        self._route_handlers['ADT'] = self._handle_adt_event
        self._route_handlers['ORU'] = self._handle_oru_event
        self._route_handlers['SIU'] = self._handle_siu_event
        self._route_handlers['MDM'] = self._handle_mdm_event
        self._route_handlers['patient'] = self._handle_patient_event
        self._route_handlers['encounter'] = self._handle_encounter_event
        self._route_handlers['observation'] = self._handle_observation_event
        self._route_handlers['appointment'] = self._handle_appointment_event

    def register_route(self, event_type_prefix: str, handler: Callable) -> None:
        """
        Register a custom event handler for a given event type prefix.

        Args:
            event_type_prefix: Event type prefix to match (case-insensitive).
            handler: Callable that accepts a ``WebhookEvent`` and returns
                     a result dictionary.
        """
        self._route_handlers[event_type_prefix.lower()] = handler

    def _get_route_handler(self, event_type: str) -> Optional[Callable]:
        """Find the most specific handler for an event type."""
        # Try exact match first
        if event_type in self._route_handlers:
            return self._route_handlers[event_type]

        # Try prefix match (e.g. 'patient.update' matches 'patient')
        event_lower = event_type.lower()
        for prefix, handler in self._route_handlers.items():
            if event_lower.startswith(prefix.lower()):
                return handler

        # Try base type (before the dot)
        base_type = event_type.split('.')[0]
        if base_type in self._route_handlers:
            return self._route_handlers[base_type]

        return None

    # ------------------------------------------------------------------
    # Event processing
    # ------------------------------------------------------------------

    def process_event(
        self,
        source: str,
        event_type: str,
        payload: Dict[str, Any],
        raw_body: str = '',
        partner_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process an incoming webhook event.

        1. Creates a ``WebhookEvent`` object
        2. Routes to the appropriate type-specific handler
        3. Publishes to Pub/Sub for async downstream processing
        4. Returns the processing result

        Args:
            source: EHR system identifier.
            event_type: Event type string (e.g. ``'patient.update'``).
            payload: Parsed JSON payload.
            raw_body: Original request body string.
            partner_config: Partner configuration dictionary.

        Returns:
            Dictionary with ``event_id``, ``status``, and processing details.
        """
        event = WebhookEvent(
            source=source,
            event_type=event_type,
            payload=payload,
            raw_body=raw_body,
        )

        logger.info(
            "Processing webhook event: id=%s source=%s type=%s",
            event.event_id, _hash_identifier(source), event_type,
        )

        # Route to type-specific handler
        handler = self._get_route_handler(event_type)
        handler_result: Dict[str, Any] = {}

        if handler:
            try:
                event.status = 'processing'
                handler_result = self._execute_with_retry(handler, event)
                event.status = 'completed'
            except Exception as e:
                event.status = 'failed'
                event.error = f"{type(e).__name__}: {str(e)}"
                logger.error(
                    "Webhook handler failed for event %s: %s",
                    event.event_id, event.error,
                )
        else:
            logger.warning(
                "No handler registered for event type '%s'; publishing to Pub/Sub only",
                event_type,
            )
            event.status = 'unhandled'

        # Publish to Pub/Sub for async processing regardless of handler result
        self._publish_to_pubsub(event, partner_config)

        return {
            'event_id': event.event_id,
            'status': event.status,
            'event_type': event_type,
            'handler_result': handler_result,
            'retry_count': event.retry_count,
            'error': event.error,
        }

    def _execute_with_retry(
        self, handler: Callable, event: WebhookEvent
    ) -> Dict[str, Any]:
        """
        Execute a handler with automatic retry on failure.

        Uses exponential backoff between retries.

        Args:
            handler: The event handler callable.
            event: The webhook event.

        Returns:
            The handler's result dictionary.

        Raises:
            The last exception if all retries are exhausted.
        """
        last_exception: Optional[Exception] = None
        delay = self._retry_delay_seconds

        for attempt in range(self._max_retries + 1):
            try:
                result = handler(event)
                if attempt > 0:
                    logger.info(
                        "Handler succeeded on retry %d for event %s",
                        attempt, event.event_id,
                    )
                return result
            except Exception as e:
                last_exception = e
                event.retry_count = attempt + 1

                if attempt < self._max_retries:
                    logger.warning(
                        "Handler attempt %d/%d failed for event %s: %s. "
                        "Retrying in %.1fs",
                        attempt + 1, self._max_retries + 1,
                        event.event_id, e, delay,
                    )
                    time.sleep(delay)
                    delay *= self._retry_backoff_multiplier

        raise last_exception  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Pub/Sub publishing
    # ------------------------------------------------------------------

    def _get_publisher(self) -> Optional[pubsub_v1.PublisherClient]:
        """Lazily initialise the Pub/Sub publisher client."""
        if self._publisher is None and self._pubsub_project:
            try:
                self._publisher = pubsub_v1.PublisherClient()
            except Exception as e:
                logger.warning("Failed to initialise Pub/Sub publisher: %s", e)
        return self._publisher

    def _publish_to_pubsub(
        self, event: WebhookEvent, partner_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Publish a webhook event to GCP Pub/Sub for async downstream processing.

        Events that fail to publish are logged but do not cause the webhook
        endpoint to return an error (the synchronous handler result takes
        precedence).
        """
        publisher = self._get_publisher()
        if not publisher or not self._pubsub_project:
            logger.debug("Pub/Sub not configured; skipping event publish")
            return

        topic_path = publisher.topic_path(self._pubsub_project, self._pubsub_topic)

        message_data = json.dumps(
            event.to_dict(),
            default=str,
        ).encode('utf-8')

        attributes = {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'source': _hash_identifier(event.source),
            'received_at': event.received_at,
        }

        try:
            future = publisher.publish(
                topic_path,
                data=message_data,
                **attributes,
            )
            message_id = future.result(timeout=10)
            logger.debug(
                "Published webhook event %s to Pub/Sub: message_id=%s",
                event.event_id, message_id,
            )
        except Exception as e:
            logger.error(
                "Failed to publish webhook event %s to Pub/Sub: %s",
                event.event_id, e,
            )

    # ------------------------------------------------------------------
    # Type-specific handlers
    # ------------------------------------------------------------------

    def _handle_adt_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Handle ADT (Admission/Discharge/Transfer) events.

        ADT events signal patient movement through the healthcare facility
        and are critical for maintaining accurate patient status.
        """
        payload = event.payload
        resource_type = payload.get('resourceType', '')

        # Determine ADT sub-type from event_type or payload
        adt_action = event.event_type.split('^')[-1] if '^' in event.event_type else 'generic'

        logger.info(
            "Processing ADT event: id=%s action=%s resource=%s",
            event.event_id, adt_action, resource_type,
        )

        # Extract patient reference
        patient_ref = ''
        if resource_type == 'Bundle':
            for entry in payload.get('entry', []):
                res = entry.get('resource', {})
                if res.get('resourceType') == 'Patient':
                    patient_ref = res.get('id', '')
                    break
        elif resource_type == 'Patient':
            patient_ref = payload.get('id', '')

        return {
            'action': 'adt_processed',
            'adt_type': adt_action,
            'patient_ref': _hash_identifier(patient_ref) if patient_ref else '',
            'resource_type': resource_type,
        }

    def _handle_oru_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Handle ORU (Observation Result) events.

        ORU events deliver lab results and other clinical observations.
        """
        payload = event.payload
        observation_count = 0

        if payload.get('resourceType') == 'Bundle':
            observation_count = sum(
                1 for entry in payload.get('entry', [])
                if entry.get('resource', {}).get('resourceType') == 'Observation'
            )
        elif payload.get('resourceType') == 'Observation':
            observation_count = 1

        logger.info(
            "Processing ORU event: id=%s observations=%d",
            event.event_id, observation_count,
        )

        return {
            'action': 'oru_processed',
            'observation_count': observation_count,
        }

    def _handle_siu_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Handle SIU (Scheduling) events.

        SIU events notify about appointment creation, modification, and
        cancellation.
        """
        payload = event.payload
        appointment_count = 0

        if payload.get('resourceType') == 'Bundle':
            appointment_count = sum(
                1 for entry in payload.get('entry', [])
                if entry.get('resource', {}).get('resourceType') == 'Appointment'
            )
        elif payload.get('resourceType') == 'Appointment':
            appointment_count = 1

        logger.info(
            "Processing SIU event: id=%s appointments=%d",
            event.event_id, appointment_count,
        )

        return {
            'action': 'siu_processed',
            'appointment_count': appointment_count,
        }

    def _handle_mdm_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Handle MDM (Medical Document Management) events.

        MDM events signal document creation or updates (e.g. clinical
        notes, discharge summaries).
        """
        payload = event.payload

        logger.info("Processing MDM event: id=%s", event.event_id)

        return {
            'action': 'mdm_processed',
            'document_type': payload.get('type', {}).get('text', 'unknown'),
        }

    def _handle_patient_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle FHIR-style patient.* events."""
        sub_action = event.event_type.split('.')[-1] if '.' in event.event_type else 'update'

        logger.info(
            "Processing patient event: id=%s action=%s",
            event.event_id, sub_action,
        )

        return {
            'action': f'patient_{sub_action}',
            'resource_type': 'Patient',
        }

    def _handle_encounter_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle FHIR-style encounter.* events."""
        sub_action = event.event_type.split('.')[-1] if '.' in event.event_type else 'update'

        logger.info(
            "Processing encounter event: id=%s action=%s",
            event.event_id, sub_action,
        )

        return {
            'action': f'encounter_{sub_action}',
            'resource_type': 'Encounter',
        }

    def _handle_observation_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle FHIR-style observation.* events."""
        sub_action = event.event_type.split('.')[-1] if '.' in event.event_type else 'create'

        logger.info(
            "Processing observation event: id=%s action=%s",
            event.event_id, sub_action,
        )

        return {
            'action': f'observation_{sub_action}',
            'resource_type': 'Observation',
        }

    def _handle_appointment_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle FHIR-style appointment.* events."""
        sub_action = event.event_type.split('.')[-1] if '.' in event.event_type else 'book'

        logger.info(
            "Processing appointment event: id=%s action=%s",
            event.event_id, sub_action,
        )

        return {
            'action': f'appointment_{sub_action}',
            'resource_type': 'Appointment',
        }
