"""
IHEP Integration Gateway - Flask Application

REST API for bidirectional EHR integration. Receives inbound data from
Mirth Connect channels, triggers sync cycles, manages partner connections,
and processes webhook events from external EHR systems.

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import hashlib
import logging
import os
from datetime import datetime
from functools import wraps
from typing import Any, Dict

import jwt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import AppConfig, load_config
from adapters import AdapterRegistry
from webhooks.handler import WebhookHandler
from sync.bidirectional_sync import BidirectionalSync
from transformers.fhir_normalizer import FHIRNormalizer

logger = logging.getLogger(__name__)


def create_app(config: AppConfig = None) -> Flask:
    """Application factory for the Integration Gateway."""
    app = Flask(__name__)

    if config is None:
        config = load_config()

    app.config["IHEP"] = config

    # CORS
    CORS(app, origins=config.cors_origins)

    # Rate limiting
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[
            f"{config.global_rate_limit.requests_per_minute}/minute",
            f"{config.global_rate_limit.requests_per_hour}/hour",
        ],
        storage_uri="memory://",
    )

    # Shared services
    adapter_registry = AdapterRegistry()
    webhook_handler = WebhookHandler(
        pubsub_project=config.gcp_project_id,
        pubsub_topic=config.pubsub_topic_inbound,
    )
    normalizer = FHIRNormalizer()
    sync_engine = BidirectionalSync(adapter_registry, config)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _get_jwt_secret() -> str:
        secret = os.getenv("JWT_SECRET")
        if secret:
            return secret
        resolved = config.secret_client.get_secret("jwt-secret")
        if resolved:
            return resolved
        raise ValueError("JWT_SECRET not configured")

    def _hash_id(identifier: str) -> str:
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Bearer token required"}), 401
            token = auth_header.split(" ", 1)[1]
            try:
                secret = _get_jwt_secret()
                payload = jwt.decode(token, secret, algorithms=["HS256"])
                if payload.get("type") != "access":
                    return jsonify({"error": "Invalid token type"}), 401
                kwargs["current_user"] = payload
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
        return decorated

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "integration-gateway",
            "environment": config.environment,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "partners": len(config.partners),
        }), 200

    # ------------------------------------------------------------------
    # Inbound data from Mirth channels
    # ------------------------------------------------------------------

    @app.route("/api/v1/ehr/inbound", methods=["POST"])
    @limiter.limit("100/minute")
    @require_auth
    def receive_inbound_data(current_user: Dict[str, Any] = None):
        """Receive transformed data from Mirth Connect channels."""
        data = request.json
        if not data:
            return jsonify({"error": "Request body required"}), 400

        channel_id = data.get("channel_id")
        message_type = data.get("message_type")
        partner_id = data.get("partner_id")
        payload = data.get("payload")
        metadata = data.get("metadata", {})

        if not all([channel_id, message_type, partner_id, payload]):
            return jsonify({
                "error": "channel_id, message_type, partner_id, and payload required"
            }), 400

        partner = config.partners.get(partner_id)
        if not partner:
            logger.warning("Inbound data for unknown partner: %s", _hash_id(partner_id))
            return jsonify({"error": "Unknown partner_id"}), 404

        if not partner.enabled:
            return jsonify({"error": "Partner is disabled"}), 403

        adapter = adapter_registry.get_adapter(partner.vendor)
        if not adapter:
            return jsonify({"error": "Unsupported EHR vendor"}), 400

        # Normalize the inbound payload
        normalized = normalizer.normalize(payload, vendor=partner.vendor)

        logger.info(
            "Inbound data processed: partner=%s type=%s channel=%s",
            _hash_id(partner_id), message_type, channel_id,
        )

        return jsonify({
            "success": True,
            "data": {
                "partner_id": partner_id,
                "message_type": message_type,
                "status": "processed",
            },
        }), 200

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    @app.route("/api/v1/ehr/sync/<partner_id>", methods=["POST"])
    @limiter.limit("10/5minutes")
    @require_auth
    def trigger_sync(partner_id: str, current_user: Dict[str, Any] = None):
        """Trigger a synchronization cycle with a specific EHR partner."""
        partner = config.partners.get(partner_id)
        if not partner:
            return jsonify({"error": "Partner not found"}), 404

        data = request.json or {}
        direction = data.get("direction", "bidirectional")
        resource_types = data.get("resource_types")
        force_full = data.get("force_full", False)

        results = sync_engine.sync_partner(
            partner_id,
            direction=direction,
            resource_types=resource_types,
            force_full=force_full,
        )

        logger.info(
            "Sync triggered: partner=%s direction=%s",
            _hash_id(partner_id), direction,
        )

        serialized = {}
        for key, result in results.items():
            serialized[key] = result.to_dict()

        return jsonify({
            "success": True,
            "data": {
                "partner_id": partner_id,
                "direction": direction,
                "started_at": datetime.utcnow().isoformat() + "Z",
                "results": serialized,
            },
        }), 202

    # ------------------------------------------------------------------
    # Partners
    # ------------------------------------------------------------------

    @app.route("/api/v1/ehr/partners", methods=["GET"])
    @limiter.limit("30/minute")
    @require_auth
    def list_partners(current_user: Dict[str, Any] = None):
        """List all configured EHR partners."""
        partner_list = []
        for pid, pcfg in config.partners.items():
            adapter = adapter_registry.get_adapter(pcfg.vendor)
            capabilities = adapter.get_capabilities() if adapter else {}
            partner_list.append({
                "partner_id": pid,
                "display_name": pcfg.display_name,
                "vendor": pcfg.vendor,
                "fhir_version": pcfg.fhir_version,
                "enabled": pcfg.enabled,
                "capabilities": capabilities,
            })

        return jsonify({
            "success": True,
            "data": {"partners": partner_list, "total": len(partner_list)},
        }), 200

    # ------------------------------------------------------------------
    # Partner status
    # ------------------------------------------------------------------

    @app.route("/api/v1/ehr/status/<partner_id>", methods=["GET"])
    @limiter.limit("60/minute")
    @require_auth
    def get_partner_status(partner_id: str, current_user: Dict[str, Any] = None):
        """Get connection status and health metrics for an EHR partner."""
        partner = config.partners.get(partner_id)
        if not partner:
            return jsonify({"error": "Partner not found"}), 404

        adapter = adapter_registry.get_adapter(partner.vendor)
        if not adapter:
            return jsonify({"error": "Unsupported EHR vendor"}), 400

        adapter.configure({
            "base_url": partner.base_url,
            "client_id": partner.client_id,
            "client_secret": partner.client_secret,
        })

        connection_valid = False
        connection_error = None
        try:
            connection_valid = adapter.validate_connection()
        except Exception as e:
            connection_error = type(e).__name__

        sync_status = sync_engine.get_sync_status(partner_id)

        return jsonify({
            "success": True,
            "data": {
                "partner_id": partner_id,
                "display_name": partner.display_name,
                "vendor": partner.vendor,
                "connection": {
                    "status": "connected" if connection_valid else "disconnected",
                    "error": connection_error,
                    "last_checked": datetime.utcnow().isoformat() + "Z",
                },
                "sync": sync_status,
                "capabilities": adapter.get_capabilities(),
                "enabled": partner.enabled,
            },
        }), 200

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    @app.route("/api/v1/ehr/webhooks", methods=["POST"])
    @limiter.limit("200/minute")
    def receive_webhook():
        """Receive incoming EHR webhook events with HMAC verification."""
        signature = request.headers.get("X-Webhook-Signature", "")
        source = request.headers.get("X-Webhook-Source", "")
        event_type = request.headers.get("X-Webhook-Event", "")

        if not source:
            return jsonify({"error": "X-Webhook-Source header required"}), 400

        raw_body = request.get_data(as_text=True)
        if not raw_body:
            return jsonify({"error": "Request body required"}), 400

        # Look up partner by webhook source
        partner = None
        for pcfg in config.partners.values():
            if pcfg.webhook_secret_key and pcfg.partner_id == source:
                partner = pcfg
                break

        if not partner:
            logger.warning("Webhook from unknown source: %s", _hash_id(source))
            return jsonify({"error": "Unknown webhook source"}), 403

        # Verify signature
        if partner.webhook_secret_key and not webhook_handler.verify_signature(
            raw_body, signature, partner.webhook_secret_key
        ):
            logger.warning("Invalid webhook signature from: %s", _hash_id(source))
            return jsonify({"error": "Invalid signature"}), 403

        payload = request.json
        result = webhook_handler.process_event(
            source=source,
            event_type=event_type,
            payload=payload,
            raw_body=raw_body,
        )

        logger.info(
            "Webhook processed: source=%s event=%s id=%s",
            _hash_id(source), event_type, result.get("event_id"),
        )

        return jsonify({
            "success": True,
            "data": {
                "event_id": result.get("event_id"),
                "status": result.get("status", "accepted"),
            },
        }), 200

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(error):
        logger.error("Internal server error: %s", error)
        return jsonify({"error": "Internal server error"}), 500

    return app


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    cfg = load_config()
    application = create_app(cfg)
    application.run(host=cfg.host, port=cfg.port, debug=cfg.debug)
