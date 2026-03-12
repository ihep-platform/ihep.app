"""
EHR Integration Configuration Management

Loads partner configurations from YAML files, manages environment-specific
settings, retrieves credentials from GCP Secret Manager, and provides
typed access to Mirth Connect and rate-limit parameters.
"""

import os
import logging
import glob
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

import yaml
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Environment defaults
# ---------------------------------------------------------------------------

_ENV_DEFAULTS: Dict[str, Dict[str, Any]] = {
    'dev': {
        'log_level': 'DEBUG',
        'rate_limit_multiplier': 10.0,
        'mirth_connect': {
            'host': 'localhost',
            'port': 8443,
            'api_port': 8443,
            'use_ssl': False,
            'verify_ssl': False,
            'admin_user': 'admin',
            'default_channel_poll_interval_seconds': 30,
        },
        'sync_defaults': {
            'batch_size': 50,
            'max_retries': 3,
            'retry_delay_seconds': 5,
            'full_sync_page_size': 100,
        },
    },
    'staging': {
        'log_level': 'INFO',
        'rate_limit_multiplier': 2.0,
        'mirth_connect': {
            'host': os.getenv('MIRTH_HOST', 'mirth-staging.ihep.internal'),
            'port': 8443,
            'api_port': 8443,
            'use_ssl': True,
            'verify_ssl': True,
            'admin_user': 'mirth-service',
            'default_channel_poll_interval_seconds': 60,
        },
        'sync_defaults': {
            'batch_size': 200,
            'max_retries': 5,
            'retry_delay_seconds': 10,
            'full_sync_page_size': 500,
        },
    },
    'prod': {
        'log_level': 'WARNING',
        'rate_limit_multiplier': 1.0,
        'mirth_connect': {
            'host': os.getenv('MIRTH_HOST', 'mirth.ihep.internal'),
            'port': 8443,
            'api_port': 8443,
            'use_ssl': True,
            'verify_ssl': True,
            'admin_user': 'mirth-service',
            'default_channel_poll_interval_seconds': 120,
        },
        'sync_defaults': {
            'batch_size': 500,
            'max_retries': 5,
            'retry_delay_seconds': 30,
            'full_sync_page_size': 1000,
        },
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class MirthConnectConfig:
    """Configuration for the Mirth Connect integration engine."""

    host: str = 'localhost'
    port: int = 8443
    api_port: int = 8443
    use_ssl: bool = True
    verify_ssl: bool = True
    admin_user: str = 'admin'
    admin_password: str = ''  # populated from Secret Manager
    default_channel_poll_interval_seconds: int = 60

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MirthConnectConfig':
        """Create a MirthConnectConfig from a plain dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @property
    def base_url(self) -> str:
        scheme = 'https' if self.use_ssl else 'http'
        return f"{scheme}://{self.host}:{self.api_port}"


@dataclass
class PartnerRateLimits:
    """Per-partner rate-limit settings."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 20
    sync_requests_per_hour: int = 12

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PartnerRateLimits':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PartnerConfig:
    """Typed representation of a single EHR partner configuration."""

    partner_id: str
    name: str
    vendor: str
    fhir_version: str = 'R4'
    base_url: str = ''
    auth_type: str = 'oauth2'
    client_id: str = ''
    client_secret: str = ''  # populated from Secret Manager
    scopes: List[str] = field(default_factory=lambda: ['openid', 'fhirUser', 'patient/*.read'])
    webhook_url: str = ''
    webhook_secret: str = ''  # populated from Secret Manager
    webhook_source_id: str = ''
    bidirectional: bool = False
    enabled: bool = True
    rate_limits: PartnerRateLimits = field(default_factory=PartnerRateLimits)
    mirth_channel_ids: List[str] = field(default_factory=list)
    custom_extensions: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary (credentials excluded)."""
        return {
            'partner_id': self.partner_id,
            'name': self.name,
            'vendor': self.vendor,
            'fhir_version': self.fhir_version,
            'base_url': self.base_url,
            'auth_type': self.auth_type,
            'scopes': self.scopes,
            'bidirectional': self.bidirectional,
            'enabled': self.enabled,
            'mirth_channel_ids': self.mirth_channel_ids,
        }


# ---------------------------------------------------------------------------
# Secret Manager helpers
# ---------------------------------------------------------------------------

class SecretManagerClient:
    """Thin wrapper around GCP Secret Manager with local caching."""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv('GCP_PROJECT')
        self._client: Optional[secretmanager.SecretManagerServiceClient] = None
        self._cache: Dict[str, str] = {}

    @property
    def client(self) -> secretmanager.SecretManagerServiceClient:
        if self._client is None:
            self._client = secretmanager.SecretManagerServiceClient()
        return self._client

    def get_secret(self, secret_id: str, version: str = 'latest') -> str:
        """
        Retrieve a secret value from GCP Secret Manager.

        Results are cached in-process for the lifetime of this object to
        avoid redundant RPCs during a single service startup cycle.
        """
        cache_key = f"{secret_id}/{version}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self.project_id:
            logger.warning(
                f"GCP_PROJECT not set; cannot fetch secret '{secret_id}'. "
                "Falling back to environment variable."
            )
            env_value = os.getenv(secret_id.upper().replace('-', '_'), '')
            return env_value

        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
        try:
            response = self.client.access_secret_version(request={"name": name})
            value = response.payload.data.decode('UTF-8')
            self._cache[cache_key] = value
            return value
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{secret_id}': {type(e).__name__}")
            raise


# ---------------------------------------------------------------------------
# Main configuration class
# ---------------------------------------------------------------------------

class EHRConfig:
    """
    Central configuration for the EHR Integration spoke.

    Reads YAML partner definitions from *partners_config_path*, overlays
    environment-specific defaults, and populates credentials from GCP Secret
    Manager.
    """

    def __init__(
        self,
        environment: str = 'dev',
        partners_config_path: Optional[str] = None,
    ):
        self.environment = environment
        self.partners_config_path = partners_config_path or os.path.join(
            os.path.dirname(__file__), 'configs', 'ehr-partners'
        )
        self._env_config: Dict[str, Any] = _ENV_DEFAULTS.get(environment, _ENV_DEFAULTS['dev'])
        self._secret_manager = SecretManagerClient()
        self._partners: Dict[str, Dict[str, Any]] = {}
        self._partner_objects: Dict[str, PartnerConfig] = {}
        self._source_index: Dict[str, str] = {}  # webhook_source_id -> partner_id

        # Derived config objects
        self.mirth = MirthConnectConfig.from_dict(self._env_config.get('mirth_connect', {}))
        self.sync_defaults: Dict[str, Any] = self._env_config.get('sync_defaults', {})

        self._load_partners()
        self._populate_credentials()

    # -- partner loading -----------------------------------------------------

    def _load_partners(self) -> None:
        """Load all YAML partner config files from the partners directory."""
        if not os.path.isdir(self.partners_config_path):
            logger.warning(f"Partners config directory not found: {self.partners_config_path}")
            return

        yaml_files = sorted(glob.glob(os.path.join(self.partners_config_path, '*.yaml')))
        yaml_files += sorted(glob.glob(os.path.join(self.partners_config_path, '*.yml')))

        for filepath in yaml_files:
            try:
                with open(filepath, 'r') as fh:
                    data = yaml.safe_load(fh)
                if not data or not isinstance(data, dict):
                    continue

                partner_id = data.get('partner_id', os.path.splitext(os.path.basename(filepath))[0])
                data['partner_id'] = partner_id

                # Merge rate limits
                rate_data = data.pop('rate_limits', {})
                rate_limits = PartnerRateLimits.from_dict(rate_data)

                partner = PartnerConfig(
                    partner_id=partner_id,
                    name=data.get('name', partner_id),
                    vendor=data.get('vendor', 'generic'),
                    fhir_version=data.get('fhir_version', 'R4'),
                    base_url=data.get('base_url', ''),
                    auth_type=data.get('auth_type', 'oauth2'),
                    client_id=data.get('client_id', ''),
                    scopes=data.get('scopes', ['openid', 'fhirUser', 'patient/*.read']),
                    webhook_url=data.get('webhook_url', ''),
                    webhook_source_id=data.get('webhook_source_id', ''),
                    bidirectional=data.get('bidirectional', False),
                    enabled=data.get('enabled', True),
                    rate_limits=rate_limits,
                    mirth_channel_ids=data.get('mirth_channel_ids', []),
                    custom_extensions=data.get('custom_extensions', {}),
                )

                self._partner_objects[partner_id] = partner
                self._partners[partner_id] = {**partner.to_dict(), **data}

                if partner.webhook_source_id:
                    self._source_index[partner.webhook_source_id] = partner_id

                logger.info(f"Loaded partner config: {partner_id} (vendor={partner.vendor})")

            except yaml.YAMLError as e:
                logger.error(f"Failed to parse YAML config {filepath}: {e}")
            except Exception as e:
                logger.error(f"Error loading partner config {filepath}: {type(e).__name__}: {e}")

        logger.info(f"Loaded {len(self._partners)} EHR partner configurations")

    def _populate_credentials(self) -> None:
        """Fetch client secrets and webhook secrets from Secret Manager."""
        for pid, partner in self._partner_objects.items():
            # Client secret
            secret_id = f"ehr-{pid}-client-secret"
            try:
                partner.client_secret = self._secret_manager.get_secret(secret_id)
                self._partners[pid]['client_secret'] = partner.client_secret
            except Exception:
                logger.debug(f"No client secret found for partner {pid}")

            # Webhook secret
            wh_secret_id = f"ehr-{pid}-webhook-secret"
            try:
                partner.webhook_secret = self._secret_manager.get_secret(wh_secret_id)
                self._partners[pid]['webhook_secret'] = partner.webhook_secret
            except Exception:
                logger.debug(f"No webhook secret found for partner {pid}")

        # Mirth admin password
        try:
            self.mirth.admin_password = self._secret_manager.get_secret('mirth-admin-password')
        except Exception:
            self.mirth.admin_password = os.getenv('MIRTH_ADMIN_PASSWORD', '')

    # -- public accessors ----------------------------------------------------

    def get_partner(self, partner_id: str) -> Optional[Dict[str, Any]]:
        """Return the raw config dict for a partner, or None if not found."""
        return self._partners.get(partner_id)

    def get_partner_typed(self, partner_id: str) -> Optional[PartnerConfig]:
        """Return the typed PartnerConfig object, or None."""
        return self._partner_objects.get(partner_id)

    def get_partner_by_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Look up a partner config by its webhook_source_id."""
        partner_id = self._source_index.get(source_id)
        if partner_id:
            return self._partners.get(partner_id)
        return None

    def get_all_partners(self) -> Dict[str, Dict[str, Any]]:
        """Return all partner configs keyed by partner_id."""
        return dict(self._partners)

    def get_rate_limits(self, partner_id: str) -> PartnerRateLimits:
        """Return rate limits for a partner; falls back to defaults."""
        partner = self._partner_objects.get(partner_id)
        if partner:
            return partner.rate_limits
        return PartnerRateLimits()


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def load_partner_config(partner_id: str, environment: str = 'dev') -> Optional[Dict[str, Any]]:
    """
    Convenience function to load a single partner configuration.

    Useful for scripts and tests that only need one partner's settings.
    """
    config = EHRConfig(environment=environment)
    return config.get_partner(partner_id)
