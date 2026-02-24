"""
EHR Integration Spoke Service
Provides bidirectional integration with Electronic Health Record systems
including Epic, Cerner, Allscripts, athenahealth, and HL7 v2.x legacy systems.

Implements FHIR R4 standard with vendor-specific adapters, data normalization,
webhook event processing, and bidirectional sync capabilities.
"""

import os
import logging
import hashlib
from typing import Dict, Optional, Any
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify
import jwt
import yaml
from google.cloud import secretmanager

from shared.security.audit import AuditLogger
from shared.utils.rate_limit import rate_limit

from config import EHRConfig, load_partner_config
from adapters import AdapterRegistry
from webhooks.handler import WebhookHandler
from sync.bidirectional_sync import InboundSync, OutboundSync, SyncState
from onboarding.orchestrator import OnboardingOrchestrator
from onboarding.communication import CommunicationManager
from onboarding.connection_manager import ConnectionManager
from onboarding.status_reporter import StatusReporter
from onboarding.provider_discovery import ProviderDiscovery
from onboarding.models import OnboardingPhase, ProviderProfile, ProviderContact

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = 'HS256'
GCP_PROJECT = os.getenv('GCP_PROJECT')
SERVICE_PORT = int(os.getenv('EHR_SERVICE_PORT', '8093'))

# Initialize Flask app
app = Flask(__name__)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize utilities
audit_logger = AuditLogger()
adapter_registry = AdapterRegistry()
webhook_handler = WebhookHandler()


def _hash_identifier(identifier: str) -> str:
    """Hash an identifier for safe logging (HIPAA compliance)."""
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


def _get_jwt_secret() -> str:
    """Retrieve JWT secret from environment or GCP Secret Manager."""
    if JWT_SECRET:
        return JWT_SECRET
    if GCP_PROJECT:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{GCP_PROJECT}/secrets/jwt-secret/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')
    raise ValueError("JWT_SECRET or GCP_PROJECT must be configured")


def require_auth(f):
    """
    Decorator for JWT authentication on protected endpoints.
    Extracts and verifies the Bearer token from the Authorization header,
    then injects the decoded token payload into the wrapped function as
    the 'current_user' keyword argument.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header with Bearer token required'}), 401

        token = auth_header.split(' ', 1)[1]
        try:
            secret = _get_jwt_secret()
            payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])

            if payload.get('type') != 'access':
                return jsonify({'error': 'Invalid token type'}), 401

            kwargs['current_user'] = payload
            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token presented: {type(e).__name__}")
            return jsonify({'error': 'Invalid token'}), 401

    return decorated


def _load_ehr_config() -> EHRConfig:
    """Load EHR configuration from environment and YAML."""
    env = os.getenv('ENVIRONMENT', 'dev')
    config_path = os.getenv(
        'EHR_CONFIG_PATH',
        os.path.join(os.path.dirname(__file__), 'configs', 'ehr-partners')
    )
    return EHRConfig(environment=env, partners_config_path=config_path)


# Load configuration at startup
ehr_config = _load_ehr_config()

# Initialize onboarding system
onboarding_orchestrator = OnboardingOrchestrator()
onboarding_comm_manager = CommunicationManager()
onboarding_conn_manager = ConnectionManager()
onboarding_status_reporter = StatusReporter()
onboarding_discovery = ProviderDiscovery(
    orchestrator=onboarding_orchestrator,
    communication_manager=onboarding_comm_manager,
    connection_manager=onboarding_conn_manager,
)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    Returns service name and current timestamp for orchestrator liveness probes.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'ehr-integration-service',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/v1/ehr/inbound', methods=['POST'])
@rate_limit(limit=100, per=60)
@require_auth
def receive_inbound_data(current_user: Dict[str, Any] = None):
    """
    Receive data from Mirth Connect channels.

    This endpoint is the primary ingestion point for data arriving through
    Mirth integration channels. Mirth destinations POST transformed payloads
    here after channel-level filtering and routing.

    Request body:
        {
            "channel_id": "mirth-channel-uuid",
            "message_type": "ADT|ORU|SIU|MDM",
            "partner_id": "partner-identifier",
            "payload": { ... FHIR or HL7 transformed data ... },
            "metadata": {
                "source_system": "Epic",
                "message_id": "original-message-id",
                "timestamp": "ISO-8601"
            }
        }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        channel_id = data.get('channel_id')
        message_type = data.get('message_type')
        partner_id = data.get('partner_id')
        payload = data.get('payload')
        metadata = data.get('metadata', {})

        if not all([channel_id, message_type, partner_id, payload]):
            return jsonify({
                'error': 'channel_id, message_type, partner_id, and payload are required'
            }), 400

        # Validate partner exists
        partner_config = ehr_config.get_partner(partner_id)
        if not partner_config:
            logger.warning(f"Inbound data for unknown partner: {_hash_identifier(partner_id)}")
            return jsonify({'error': 'Unknown partner_id'}), 404

        # Get the appropriate adapter and normalize the data
        adapter = adapter_registry.get_adapter(partner_config.get('vendor', 'generic'))
        if not adapter:
            logger.error(f"No adapter found for vendor: {partner_config.get('vendor')}")
            return jsonify({'error': 'Unsupported EHR vendor'}), 400

        # Process the inbound data through the sync engine
        sync_engine = InboundSync(adapter=adapter, config=partner_config)
        result = sync_engine.process_inbound_message(
            message_type=message_type,
            payload=payload,
            metadata=metadata
        )

        # Audit log the data access
        audit_logger.log(
            user_id=current_user.get('user_id', 'system'),
            action='EHR_INBOUND_RECEIVE',
            resource='EHRData',
            outcome='SUCCESS',
            details={
                'partner_id': _hash_identifier(partner_id),
                'channel_id': channel_id,
                'message_type': message_type,
                'record_count': result.get('record_count', 0)
            }
        )

        logger.info(
            f"Inbound data processed: partner={_hash_identifier(partner_id)} "
            f"type={message_type} records={result.get('record_count', 0)}"
        )

        return jsonify({
            'success': True,
            'data': {
                'message_id': result.get('message_id'),
                'record_count': result.get('record_count', 0),
                'status': result.get('status', 'processed')
            }
        }), 200

    except ValueError as e:
        logger.warning(f"Validation error on inbound data: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error processing inbound data: {type(e).__name__}: {str(e)}")
        audit_logger.log(
            user_id=current_user.get('user_id', 'system') if current_user else 'system',
            action='EHR_INBOUND_RECEIVE',
            resource='EHRData',
            outcome='FAILURE',
            details={'error': type(e).__name__}
        )
        return jsonify({'error': 'Failed to process inbound data'}), 500


@app.route('/api/v1/ehr/sync/<partner_id>', methods=['POST'])
@rate_limit(limit=10, per=300)
@require_auth
def trigger_sync(partner_id: str, current_user: Dict[str, Any] = None):
    """
    Trigger a synchronization cycle with a specific EHR partner.

    Initiates either a full or incremental sync depending on request parameters
    and prior sync state. The sync runs asynchronously; this endpoint returns
    a tracking identifier that can be polled via the status endpoint.

    Request body (optional):
        {
            "sync_type": "full|incremental",
            "resource_types": ["Patient", "Observation", "Appointment"],
            "since": "ISO-8601 timestamp for incremental cutoff"
        }
    """
    try:
        partner_config = ehr_config.get_partner(partner_id)
        if not partner_config:
            return jsonify({'error': 'Partner not found'}), 404

        data = request.json or {}
        sync_type = data.get('sync_type', 'incremental')
        resource_types = data.get('resource_types', ['Patient', 'Observation', 'Appointment'])
        since = data.get('since')

        # Get adapter for this partner
        adapter = adapter_registry.get_adapter(partner_config.get('vendor'))
        if not adapter:
            return jsonify({'error': 'Unsupported EHR vendor'}), 400

        # Configure adapter with partner credentials
        adapter.configure(partner_config)

        # Validate connection before starting sync
        if not adapter.validate_connection():
            logger.error(f"Connection validation failed for partner {_hash_identifier(partner_id)}")
            return jsonify({'error': 'Unable to connect to partner EHR system'}), 503

        # Initialize sync state
        sync_state = SyncState(
            partner_id=partner_id,
            sync_type=sync_type,
            resource_types=resource_types,
            since=since
        )

        # Run bidirectional sync
        inbound_sync = InboundSync(adapter=adapter, config=partner_config)
        outbound_sync = OutboundSync(adapter=adapter, config=partner_config)

        sync_result = inbound_sync.execute(sync_state)

        # If partner supports bidirectional, also push outbound
        if partner_config.get('bidirectional', False):
            outbound_result = outbound_sync.execute(sync_state)
            sync_result['outbound'] = outbound_result

        # Audit log
        audit_logger.log(
            user_id=current_user.get('user_id', 'system'),
            action='EHR_SYNC_TRIGGER',
            resource='EHRSync',
            outcome='SUCCESS',
            details={
                'partner_id': _hash_identifier(partner_id),
                'sync_type': sync_type,
                'resource_types': resource_types
            }
        )

        logger.info(
            f"Sync triggered: partner={_hash_identifier(partner_id)} "
            f"type={sync_type} resources={resource_types}"
        )

        return jsonify({
            'success': True,
            'data': {
                'sync_id': sync_result.get('sync_id'),
                'partner_id': partner_id,
                'sync_type': sync_type,
                'status': sync_result.get('status', 'in_progress'),
                'started_at': datetime.utcnow().isoformat(),
                'records_processed': sync_result.get('records_processed', 0)
            }
        }), 202

    except Exception as e:
        logger.error(f"Sync trigger error for partner {_hash_identifier(partner_id)}: {type(e).__name__}")
        audit_logger.log(
            user_id=current_user.get('user_id', 'system') if current_user else 'system',
            action='EHR_SYNC_TRIGGER',
            resource='EHRSync',
            outcome='FAILURE',
            details={
                'partner_id': _hash_identifier(partner_id),
                'error': type(e).__name__
            }
        )
        return jsonify({'error': 'Failed to trigger sync'}), 500


@app.route('/api/v1/ehr/partners', methods=['GET'])
@rate_limit(limit=30, per=60)
@require_auth
def list_partners(current_user: Dict[str, Any] = None):
    """
    List all connected EHR partners.

    Returns a summary of each configured EHR partner including vendor type,
    connection status, and supported capabilities. Sensitive connection
    credentials are never included in the response.
    """
    try:
        partners = ehr_config.get_all_partners()
        partner_list = []

        for pid, config in partners.items():
            adapter = adapter_registry.get_adapter(config.get('vendor'))
            capabilities = adapter.get_capabilities() if adapter else {}

            partner_list.append({
                'partner_id': pid,
                'name': config.get('name', 'Unknown'),
                'vendor': config.get('vendor', 'unknown'),
                'fhir_version': config.get('fhir_version', 'R4'),
                'bidirectional': config.get('bidirectional', False),
                'capabilities': capabilities,
                'enabled': config.get('enabled', True)
            })

        audit_logger.log(
            user_id=current_user.get('user_id', 'system'),
            action='EHR_PARTNERS_LIST',
            resource='EHRPartner',
            outcome='SUCCESS',
            details={'count': len(partner_list)}
        )

        return jsonify({
            'success': True,
            'data': {
                'partners': partner_list,
                'total': len(partner_list)
            }
        }), 200

    except Exception as e:
        logger.error(f"Error listing partners: {type(e).__name__}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve partner list'}), 500


@app.route('/api/v1/ehr/webhooks', methods=['POST'])
@rate_limit(limit=200, per=60)
def receive_webhook():
    """
    Receive incoming EHR webhook events.

    This endpoint accepts webhook notifications from EHR systems (e.g., Epic
    Subscriptions, Cerner CDS Hooks). Authentication is performed via HMAC
    signature verification rather than JWT since the caller is an external
    EHR system, not an IHEP user.

    Request headers:
        X-Webhook-Signature: HMAC-SHA256 signature of the request body
        X-Webhook-Source: Identifier of the sending EHR system
        X-Webhook-Event: Event type (e.g., patient.update, encounter.discharge)

    Request body:
        Vendor-specific webhook payload (typically FHIR Bundle or notification)
    """
    try:
        # Extract webhook metadata from headers
        signature = request.headers.get('X-Webhook-Signature', '')
        source = request.headers.get('X-Webhook-Source', '')
        event_type = request.headers.get('X-Webhook-Event', '')

        if not source:
            return jsonify({'error': 'X-Webhook-Source header is required'}), 400

        raw_body = request.get_data(as_text=True)
        if not raw_body:
            return jsonify({'error': 'Request body is required'}), 400

        # Verify the webhook signature
        partner_config = ehr_config.get_partner_by_source(source)
        if not partner_config:
            logger.warning(f"Webhook from unknown source: {_hash_identifier(source)}")
            return jsonify({'error': 'Unknown webhook source'}), 403

        webhook_secret = partner_config.get('webhook_secret', '')
        if webhook_secret and not webhook_handler.verify_signature(
            raw_body, signature, webhook_secret
        ):
            logger.warning(f"Invalid webhook signature from source: {_hash_identifier(source)}")
            audit_logger.log(
                user_id='system',
                action='EHR_WEBHOOK_RECEIVE',
                resource='Webhook',
                outcome='FAILURE',
                details={
                    'source': _hash_identifier(source),
                    'reason': 'invalid_signature'
                }
            )
            return jsonify({'error': 'Invalid webhook signature'}), 403

        # Process the webhook event
        payload = request.json
        result = webhook_handler.process_event(
            source=source,
            event_type=event_type,
            payload=payload,
            raw_body=raw_body,
            partner_config=partner_config
        )

        audit_logger.log(
            user_id='system',
            action='EHR_WEBHOOK_RECEIVE',
            resource='Webhook',
            outcome='SUCCESS',
            details={
                'source': _hash_identifier(source),
                'event_type': event_type,
                'event_id': result.get('event_id')
            }
        )

        logger.info(
            f"Webhook processed: source={_hash_identifier(source)} "
            f"event={event_type} id={result.get('event_id')}"
        )

        return jsonify({
            'success': True,
            'data': {
                'event_id': result.get('event_id'),
                'status': result.get('status', 'accepted')
            }
        }), 200

    except ValueError as e:
        logger.warning(f"Webhook validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Webhook processing error: {type(e).__name__}: {str(e)}")
        return jsonify({'error': 'Failed to process webhook'}), 500


@app.route('/api/v1/ehr/status/<partner_id>', methods=['GET'])
@rate_limit(limit=60, per=60)
@require_auth
def get_partner_status(partner_id: str, current_user: Dict[str, Any] = None):
    """
    Get the connection status and health metrics for a specific EHR partner.

    Returns current connectivity state, last successful sync timestamp,
    error counts, and throughput metrics. Used by the dashboard and
    alerting systems to monitor integration health.
    """
    try:
        partner_config = ehr_config.get_partner(partner_id)
        if not partner_config:
            return jsonify({'error': 'Partner not found'}), 404

        adapter = adapter_registry.get_adapter(partner_config.get('vendor'))
        if not adapter:
            return jsonify({'error': 'Unsupported EHR vendor'}), 400

        # Configure adapter and check connection
        adapter.configure(partner_config)
        connection_valid = False
        connection_error = None

        try:
            connection_valid = adapter.validate_connection()
        except Exception as conn_err:
            connection_error = type(conn_err).__name__

        # Load sync state for this partner
        sync_state = SyncState.load(partner_id)

        status_data = {
            'partner_id': partner_id,
            'name': partner_config.get('name', 'Unknown'),
            'vendor': partner_config.get('vendor', 'unknown'),
            'connection': {
                'status': 'connected' if connection_valid else 'disconnected',
                'error': connection_error,
                'last_checked': datetime.utcnow().isoformat()
            },
            'sync': {
                'last_sync_time': sync_state.last_sync_time if sync_state else None,
                'last_sync_status': sync_state.last_status if sync_state else None,
                'records_synced': sync_state.total_records if sync_state else 0,
                'error_count': sync_state.error_count if sync_state else 0
            },
            'capabilities': adapter.get_capabilities(),
            'enabled': partner_config.get('enabled', True)
        }

        audit_logger.log(
            user_id=current_user.get('user_id', 'system'),
            action='EHR_STATUS_CHECK',
            resource='EHRPartner',
            outcome='SUCCESS',
            details={'partner_id': _hash_identifier(partner_id)}
        )

        return jsonify({
            'success': True,
            'data': status_data
        }), 200

    except Exception as e:
        logger.error(
            f"Status check error for partner {_hash_identifier(partner_id)}: "
            f"{type(e).__name__}: {str(e)}"
        )
        return jsonify({'error': 'Failed to retrieve partner status'}), 500


# ---------------------------------------------------------------------------
# Onboarding API Endpoints
# ---------------------------------------------------------------------------

@app.route('/api/v1/onboarding/providers', methods=['POST'])
@rate_limit(limit=20, per=60)
@require_auth
def register_provider(current_user: Dict[str, Any] = None):
    """
    Register a new EHR provider and initiate the onboarding workflow.

    Accepts provider details, creates a profile, registers with the
    onboarding orchestrator, and optionally sends initial outreach.

    Request body:
        {
            "organization_name": "Example Health System",
            "ehr_vendor": "epic",
            "contacts": [{"name": "Jane Doe", "email": "jane@example.com", "role": "IT Director"}],
            "base_url": "https://fhir.example.com/api/FHIR/R4",
            "sync_mode": "bidirectional",
            "auto_outreach": true,
            "organization_type": "hospital",
            "size_category": "large",
            "location": "Chicago, IL",
            "npi": "1234567890",
            "notes": "Priority integration partner"
        }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        organization_name = data.get('organization_name')
        ehr_vendor = data.get('ehr_vendor')
        if not organization_name or not ehr_vendor:
            return jsonify({
                'error': 'organization_name and ehr_vendor are required'
            }), 400

        profile = onboarding_discovery.create_provider_profile(
            organization_name=organization_name,
            ehr_vendor=ehr_vendor,
            contacts=data.get('contacts', []),
            base_url=data.get('base_url', ''),
            sync_mode=data.get('sync_mode', 'bidirectional'),
            organization_type=data.get('organization_type', ''),
            size_category=data.get('size_category', ''),
            location=data.get('location', ''),
            npi=data.get('npi', ''),
            notes=data.get('notes', ''),
            tags=data.get('tags', []),
        )

        result = onboarding_discovery.initiate_onboarding(
            profile,
            auto_outreach=data.get('auto_outreach', True),
        )

        audit_logger.log(
            user_id=current_user.get('user_id', 'system'),
            action='ONBOARDING_PROVIDER_REGISTERED',
            resource='OnboardingProvider',
            outcome='SUCCESS',
            details={
                'provider_id': _hash_identifier(result['provider_id']),
                'vendor': ehr_vendor,
            }
        )

        return jsonify({'success': True, 'data': result}), 201

    except Exception as e:
        logger.error(f"Provider registration error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to register provider'}), 500


@app.route('/api/v1/onboarding/providers/batch', methods=['POST'])
@rate_limit(limit=5, per=60)
@require_auth
def batch_register_providers(current_user: Dict[str, Any] = None):
    """
    Batch-register multiple EHR providers for onboarding.

    Request body:
        {
            "providers": [
                {"organization_name": "...", "ehr_vendor": "epic", "contacts": [...]},
                {"organization_name": "...", "ehr_vendor": "cerner", "contacts": [...]}
            ],
            "auto_outreach": true
        }
    """
    try:
        data = request.json
        if not data or 'providers' not in data:
            return jsonify({'error': 'providers list is required'}), 400

        results = onboarding_discovery.batch_initiate(
            providers=data['providers'],
            auto_outreach=data.get('auto_outreach', True),
        )

        audit_logger.log(
            user_id=current_user.get('user_id', 'system'),
            action='ONBOARDING_BATCH_REGISTER',
            resource='OnboardingProvider',
            outcome='SUCCESS',
            details={'count': len(results)}
        )

        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'total': len(results),
                'successful': sum(1 for r in results if r.get('success')),
            }
        }), 201

    except Exception as e:
        logger.error(f"Batch registration error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to batch register providers'}), 500


@app.route('/api/v1/onboarding/providers', methods=['GET'])
@rate_limit(limit=30, per=60)
@require_auth
def list_onboarding_providers(current_user: Dict[str, Any] = None):
    """
    List all providers in the onboarding pipeline with summary status.

    Query parameters:
        phase: Filter by onboarding phase
        status: Filter by overall status
        vendor: Filter by EHR vendor
    """
    try:
        all_states = onboarding_orchestrator.get_all_states()

        # Apply filters
        phase_filter = request.args.get('phase')
        status_filter = request.args.get('status')
        vendor_filter = request.args.get('vendor')

        summaries = []
        for state in all_states.values():
            if phase_filter and state.current_phase != phase_filter:
                continue
            if status_filter and state.overall_status != status_filter:
                continue
            if vendor_filter and state.provider_profile:
                if state.provider_profile.ehr_vendor != vendor_filter:
                    continue
            summaries.append(state.to_summary())

        return jsonify({
            'success': True,
            'data': {
                'providers': summaries,
                'total': len(summaries),
            }
        }), 200

    except Exception as e:
        logger.error(f"List onboarding providers error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to list providers'}), 500


@app.route('/api/v1/onboarding/providers/<provider_id>', methods=['GET'])
@rate_limit(limit=60, per=60)
@require_auth
def get_onboarding_provider(provider_id: str, current_user: Dict[str, Any] = None):
    """
    Get the full onboarding state for a specific provider.

    Returns phase details, checklist status, test results,
    communication history, and event log.
    """
    try:
        state = onboarding_orchestrator.get_state(provider_id)
        if not state:
            return jsonify({'error': 'Provider not found'}), 404

        return jsonify({
            'success': True,
            'data': state.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Get provider error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to retrieve provider'}), 500


@app.route('/api/v1/onboarding/providers/<provider_id>/advance', methods=['POST'])
@rate_limit(limit=10, per=60)
@require_auth
def advance_onboarding_phase(provider_id: str, current_user: Dict[str, Any] = None):
    """
    Advance a provider to the next onboarding phase.

    Request body (optional):
        {"force": false}
    """
    try:
        data = request.json or {}
        force = data.get('force', False)

        state = onboarding_orchestrator.advance_phase(
            provider_id=provider_id,
            actor=current_user.get('user_id', 'admin'),
            force=force,
        )

        audit_logger.log(
            user_id=current_user.get('user_id', 'system'),
            action='ONBOARDING_PHASE_ADVANCED',
            resource='OnboardingProvider',
            outcome='SUCCESS',
            details={
                'provider_id': _hash_identifier(provider_id),
                'new_phase': state.current_phase,
            }
        )

        return jsonify({
            'success': True,
            'data': {
                'provider_id': provider_id,
                'current_phase': state.current_phase,
                'completion_percentage': state.completion_percentage(),
            }
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Phase advance error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to advance phase'}), 500


@app.route('/api/v1/onboarding/providers/<provider_id>/checklist', methods=['PATCH'])
@rate_limit(limit=30, per=60)
@require_auth
def update_checklist(provider_id: str, current_user: Dict[str, Any] = None):
    """
    Update checklist items for a provider's current phase.

    Request body:
        {
            "phase": "credentialing",
            "items": {
                "sandbox_credentials_received": true,
                "credentials_stored": true
            }
        }
    """
    try:
        data = request.json
        if not data or 'phase' not in data or 'items' not in data:
            return jsonify({'error': 'phase and items are required'}), 400

        phase = OnboardingPhase(data['phase'])
        state = onboarding_orchestrator.update_checklist_items(
            provider_id=provider_id,
            phase=phase,
            items=data['items'],
            actor=current_user.get('user_id', 'admin'),
        )

        return jsonify({
            'success': True,
            'data': {
                'provider_id': provider_id,
                'current_phase': state.current_phase,
                'phase_checklist': state.get_phase_state(phase).to_dict(),
                'completion_percentage': state.completion_percentage(),
            }
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Checklist update error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to update checklist'}), 500


@app.route('/api/v1/onboarding/providers/<provider_id>/connect', methods=['POST'])
@rate_limit(limit=10, per=60)
@require_auth
def setup_connection(provider_id: str, current_user: Dict[str, Any] = None):
    """
    Set up the API connection for a provider with credentials.

    Stores credentials, generates partner config, and runs connection tests.

    Request body:
        {
            "credentials": {
                "client_id": "...",
                "client_secret": "..."
            },
            "connection_details": {
                "base_url": "https://fhir.example.com/api/FHIR/R4",
                "auth_url": "https://fhir.example.com/oauth2/authorize",
                "token_url": "https://fhir.example.com/oauth2/token"
            }
        }
    """
    try:
        data = request.json
        if not data or 'credentials' not in data:
            return jsonify({'error': 'credentials are required'}), 400

        result = onboarding_discovery.setup_provider_connection(
            provider_id=provider_id,
            credentials=data['credentials'],
            connection_details=data.get('connection_details'),
        )

        audit_logger.log(
            user_id=current_user.get('user_id', 'system'),
            action='ONBOARDING_CONNECTION_SETUP',
            resource='OnboardingProvider',
            outcome='SUCCESS',
            details={
                'provider_id': _hash_identifier(provider_id),
                'tests_passed': result['tests_passed'],
                'tests_total': result['tests_total'],
            }
        )

        return jsonify({'success': True, 'data': result}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Connection setup error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to set up connection'}), 500


@app.route('/api/v1/onboarding/providers/<provider_id>/test', methods=['POST'])
@rate_limit(limit=10, per=300)
@require_auth
def run_connection_tests(provider_id: str, current_user: Dict[str, Any] = None):
    """
    Run the connection test suite for a provider.

    Returns detailed test results including response times and errors.
    """
    try:
        state = onboarding_orchestrator.get_state(provider_id)
        if not state:
            return jsonify({'error': 'Provider not found'}), 404

        results = onboarding_conn_manager.run_test_suite(state)
        onboarding_orchestrator._save_state(state)

        passed = sum(1 for r in results if r.passed)
        total = len(results)

        return jsonify({
            'success': True,
            'data': {
                'provider_id': provider_id,
                'tests_passed': passed,
                'tests_total': total,
                'summary': onboarding_conn_manager.format_test_summary(results),
                'results': [r.to_dict() for r in results],
            }
        }), 200

    except Exception as e:
        logger.error(f"Connection test error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to run tests'}), 500


@app.route('/api/v1/onboarding/providers/<provider_id>/communicate', methods=['POST'])
@rate_limit(limit=10, per=60)
@require_auth
def send_communication(provider_id: str, current_user: Dict[str, Any] = None):
    """
    Send a communication to a provider.

    Request body:
        {
            "communication_type": "follow_up",
            "custom_message": "Optional additional message"
        }
    """
    try:
        data = request.json or {}
        comm_type = data.get('communication_type')
        if not comm_type:
            return jsonify({'error': 'communication_type is required'}), 400

        state = onboarding_orchestrator.get_state(provider_id)
        if not state:
            return jsonify({'error': 'Provider not found'}), 404

        extra = {}
        if data.get('custom_message'):
            extra['custom_message'] = data['custom_message']

        record = onboarding_comm_manager.create_communication(
            state, comm_type, extra
        )
        sent = onboarding_comm_manager.send_communication(state, record)
        onboarding_orchestrator._save_state(state)

        return jsonify({
            'success': True,
            'data': {
                'communication_id': sent.communication_id,
                'type': sent.communication_type,
                'recipient': sent.recipient,
                'status': sent.status,
                'subject': sent.subject,
            }
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Communication error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to send communication'}), 500


@app.route('/api/v1/onboarding/dashboard', methods=['GET'])
@rate_limit(limit=30, per=60)
@require_auth
def onboarding_dashboard(current_user: Dict[str, Any] = None):
    """
    Get the onboarding dashboard with aggregate metrics.

    Returns phase distribution, status breakdown, vendor counts,
    active provider health, and recent events.
    """
    try:
        all_states = onboarding_orchestrator.get_all_states()
        dashboard = onboarding_status_reporter.generate_dashboard(all_states)

        return jsonify({
            'success': True,
            'data': dashboard.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Dashboard error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to generate dashboard'}), 500


@app.route('/api/v1/onboarding/providers/<provider_id>/readiness', methods=['GET'])
@rate_limit(limit=30, per=60)
@require_auth
def provider_readiness(provider_id: str, current_user: Dict[str, Any] = None):
    """
    Get a production readiness assessment for a provider.

    Returns readiness score, blockers, and recommendations.
    """
    try:
        state = onboarding_orchestrator.get_state(provider_id)
        if not state:
            return jsonify({'error': 'Provider not found'}), 404

        report = onboarding_status_reporter.generate_readiness_report(state)

        return jsonify({
            'success': True,
            'data': report.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Readiness report error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to generate readiness report'}), 500


@app.route('/api/v1/onboarding/operations', methods=['GET'])
@rate_limit(limit=10, per=60)
@require_auth
def operations_summary(current_user: Dict[str, Any] = None):
    """
    Get an operations summary across all EHR integrations.

    Returns active integrations, in-progress onboarding, blocked
    providers, and recent completions.
    """
    try:
        all_states = onboarding_orchestrator.get_all_states()
        summary = onboarding_status_reporter.generate_operations_summary(all_states)

        return jsonify({
            'success': True,
            'data': summary
        }), 200

    except Exception as e:
        logger.error(f"Operations summary error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to generate operations summary'}), 500


@app.route('/api/v1/onboarding/engagement-cycle', methods=['POST'])
@rate_limit(limit=5, per=3600)
@require_auth
def run_engagement_cycle(current_user: Dict[str, Any] = None):
    """
    Trigger an automated engagement cycle.

    Sends follow-ups, runs tests, and advances providers as appropriate.
    Designed to be called by Cloud Scheduler or manually by admins.

    Request body (optional):
        {
            "follow_up_after_days": 3,
            "max_follow_ups": 3
        }
    """
    try:
        data = request.json or {}
        result = onboarding_discovery.run_engagement_cycle(
            follow_up_after_days=data.get('follow_up_after_days', 3),
            max_follow_ups=data.get('max_follow_ups', 3),
        )

        audit_logger.log(
            user_id=current_user.get('user_id', 'system'),
            action='ONBOARDING_ENGAGEMENT_CYCLE',
            resource='OnboardingProvider',
            outcome='SUCCESS',
            details={
                'providers_processed': result['providers_processed'],
                'follow_ups_sent': result['follow_ups_sent'],
                'tests_run': result['tests_run'],
            }
        )

        return jsonify({'success': True, 'data': result}), 200

    except Exception as e:
        logger.error(f"Engagement cycle error: {type(e).__name__}: {e}")
        return jsonify({'error': 'Failed to run engagement cycle'}), 500


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({'error': 'Method not allowed'}), 405


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Production: use gunicorn
    # gunicorn -w 4 -b 0.0.0.0:8093 app:app
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)
