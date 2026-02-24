"""
Webhook Event Handler

Processes incoming EHR webhook events with HMAC-SHA256 signature
verification, event type routing, GCP Pub/Sub publishing, and retry logic.

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
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

_DEFAULT_MAX_RETRIES = 3
_DEFAULT_RETRY_DELAY = 5
_DEFAULT_BACKOFF_MULTIPLIER = 2.0


def _hash_identifier(identifier: str) -> str:
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


class WebhookEvent:
    """Represents a single inbound webhook event."""

    def __init__(self, source: str, event_type: str, payload: Dict[str, Any], raw_body: str = "") -> None:
        self.event_id: str = str(uuid.uuid4())
        self.source: str = source
        self.event_type: str = event_type
        self.payload: Dict[str, Any] = payload
        self.raw_body: str = raw_body
        self.received_at: str = datetime.utcnow().isoformat() + "Z"
        self.status: str = "pending"
        self.retry_count: int = 0
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id, "source": self.source,
            "event_type": self.event_type, "payload": self.payload,
            "received_at": self.received_at, "status": self.status,
            "retry_count": self.retry_count, "error": self.error,
        }


class WebhookHandler:
    """Central handler for incoming EHR webhook events."""

    def __init__(
        self,
        pubsub_project: Optional[str] = None,
        pubsub_topic: str = "ehr-webhook-events",
        max_retries: int = _DEFAULT_MAX_RETRIES,
        retry_delay_seconds: float = _DEFAULT_RETRY_DELAY,
        retry_backoff_multiplier: float = _DEFAULT_BACKOFF_MULTIPLIER,
    ) -> None:
        self._pubsub_project = pubsub_project
        self._pubsub_topic = pubsub_topic
        self._max_retries = max_retries
        self._retry_delay = retry_delay_seconds
        self._retry_backoff = retry_backoff_multiplier
        self._publisher: Optional[pubsub_v1.PublisherClient] = None
        self._route_handlers: Dict[str, Callable] = {}
        self._register_default_routes()

    @staticmethod
    def verify_signature(body: str, signature: str, secret: str) -> bool:
        if not secret:
            return True
        if not signature:
            return False
        clean = signature
        if clean.startswith("sha256=") or clean.startswith("SHA256="):
            clean = clean[7:]
        expected = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, clean)

    def _register_default_routes(self) -> None:
        self._route_handlers["ADT"] = self._handle_adt_event
        self._route_handlers["ORU"] = self._handle_oru_event
        self._route_handlers["SIU"] = self._handle_siu_event
        self._route_handlers["MDM"] = self._handle_mdm_event
        self._route_handlers["patient"] = self._handle_patient_event
        self._route_handlers["encounter"] = self._handle_encounter_event
        self._route_handlers["observation"] = self._handle_observation_event
        self._route_handlers["appointment"] = self._handle_appointment_event

    def register_route(self, event_type_prefix: str, handler: Callable) -> None:
        self._route_handlers[event_type_prefix.lower()] = handler

    def _get_route_handler(self, event_type: str) -> Optional[Callable]:
        if event_type in self._route_handlers:
            return self._route_handlers[event_type]
        event_lower = event_type.lower()
        for prefix, handler in self._route_handlers.items():
            if event_lower.startswith(prefix.lower()):
                return handler
        base_type = event_type.split(".")[0]
        if base_type in self._route_handlers:
            return self._route_handlers[base_type]
        return None

    def process_event(
        self, source: str, event_type: str, payload: Dict[str, Any],
        raw_body: str = "", partner_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        event = WebhookEvent(source=source, event_type=event_type, payload=payload, raw_body=raw_body)
        logger.info("Processing webhook: id=%s source=%s type=%s", event.event_id, _hash_identifier(source), event_type)

        handler = self._get_route_handler(event_type)
        handler_result: Dict[str, Any] = {}

        if handler:
            try:
                event.status = "processing"
                handler_result = self._execute_with_retry(handler, event)
                event.status = "completed"
            except Exception as e:
                event.status = "failed"
                event.error = f"{type(e).__name__}: {e}"
                logger.error("Webhook handler failed for %s: %s", event.event_id, event.error)
        else:
            event.status = "unhandled"

        self._publish_to_pubsub(event)

        return {
            "event_id": event.event_id, "status": event.status,
            "event_type": event_type, "handler_result": handler_result,
            "retry_count": event.retry_count, "error": event.error,
        }

    def _execute_with_retry(self, handler: Callable, event: WebhookEvent) -> Dict[str, Any]:
        last_exc: Optional[Exception] = None
        delay = self._retry_delay
        for attempt in range(self._max_retries + 1):
            try:
                return handler(event)
            except Exception as e:
                last_exc = e
                event.retry_count = attempt + 1
                if attempt < self._max_retries:
                    time.sleep(delay)
                    delay *= self._retry_backoff
        raise last_exc  # type: ignore[misc]

    def _get_publisher(self) -> Optional[pubsub_v1.PublisherClient]:
        if self._publisher is None and self._pubsub_project:
            try:
                self._publisher = pubsub_v1.PublisherClient()
            except Exception as e:
                logger.warning("Failed to init Pub/Sub publisher: %s", e)
        return self._publisher

    def _publish_to_pubsub(self, event: WebhookEvent) -> None:
        publisher = self._get_publisher()
        if not publisher or not self._pubsub_project:
            return
        topic_path = publisher.topic_path(self._pubsub_project, self._pubsub_topic)
        data = json.dumps(event.to_dict(), default=str).encode("utf-8")
        try:
            future = publisher.publish(topic_path, data=data,
                                        event_id=event.event_id, event_type=event.event_type,
                                        source=_hash_identifier(event.source))
            future.result(timeout=10)
        except Exception as e:
            logger.error("Failed to publish event %s to Pub/Sub: %s", event.event_id, e)

    # -- Type-specific handlers ------------------------------------------------

    def _handle_adt_event(self, event: WebhookEvent) -> Dict[str, Any]:
        adt_action = event.event_type.split("^")[-1] if "^" in event.event_type else "generic"
        return {"action": "adt_processed", "adt_type": adt_action, "resource_type": event.payload.get("resourceType", "")}

    def _handle_oru_event(self, event: WebhookEvent) -> Dict[str, Any]:
        count = 0
        p = event.payload
        if p.get("resourceType") == "Bundle":
            count = sum(1 for e in p.get("entry", []) if e.get("resource", {}).get("resourceType") == "Observation")
        elif p.get("resourceType") == "Observation":
            count = 1
        return {"action": "oru_processed", "observation_count": count}

    def _handle_siu_event(self, event: WebhookEvent) -> Dict[str, Any]:
        count = 0
        p = event.payload
        if p.get("resourceType") == "Bundle":
            count = sum(1 for e in p.get("entry", []) if e.get("resource", {}).get("resourceType") == "Appointment")
        elif p.get("resourceType") == "Appointment":
            count = 1
        return {"action": "siu_processed", "appointment_count": count}

    def _handle_mdm_event(self, event: WebhookEvent) -> Dict[str, Any]:
        return {"action": "mdm_processed", "document_type": event.payload.get("type", {}).get("text", "unknown")}

    def _handle_patient_event(self, event: WebhookEvent) -> Dict[str, Any]:
        sub = event.event_type.split(".")[-1] if "." in event.event_type else "update"
        return {"action": f"patient_{sub}", "resource_type": "Patient"}

    def _handle_encounter_event(self, event: WebhookEvent) -> Dict[str, Any]:
        sub = event.event_type.split(".")[-1] if "." in event.event_type else "update"
        return {"action": f"encounter_{sub}", "resource_type": "Encounter"}

    def _handle_observation_event(self, event: WebhookEvent) -> Dict[str, Any]:
        sub = event.event_type.split(".")[-1] if "." in event.event_type else "create"
        return {"action": f"observation_{sub}", "resource_type": "Observation"}

    def _handle_appointment_event(self, event: WebhookEvent) -> Dict[str, Any]:
        sub = event.event_type.split(".")[-1] if "." in event.event_type else "book"
        return {"action": f"appointment_{sub}", "resource_type": "Appointment"}
