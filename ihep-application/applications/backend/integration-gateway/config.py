"""
IHEP Integration Gateway - Configuration Management

Loads partner configurations from YAML files, manages environment-based
settings (dev/staging/prod), integrates with GCP Secret Manager for
credentials, and defines rate-limit configs per partner.

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

VALID_ENVIRONMENTS = ("dev", "staging", "prod")
_ENV = os.getenv("IHEP_ENV", "dev").lower()
if _ENV not in VALID_ENVIRONMENTS:
    logger.warning("Unknown IHEP_ENV '%s', falling back to 'dev'", _ENV)
    _ENV = "dev"


class SecretManagerClient:
    """Thin wrapper around Google Cloud Secret Manager.
    Falls back to environment variables when running outside GCP."""

    def __init__(self, project_id: Optional[str] = None) -> None:
        self._project_id = project_id or os.getenv("GCP_PROJECT_ID", "")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google.cloud import secretmanager
                self._client = secretmanager.SecretManagerServiceClient()
            except Exception as exc:
                logger.warning("Could not initialise Secret Manager client: %s", exc)
        return self._client

    def get_secret(self, secret_id: str, version: str = "latest") -> Optional[str]:
        client = self._get_client()
        if client and self._project_id:
            try:
                name = f"projects/{self._project_id}/secrets/{secret_id}/versions/{version}"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data.decode("utf-8")
            except Exception as exc:
                logger.error("Secret Manager lookup failed for '%s': %s", secret_id, exc)
        env_key = secret_id.upper().replace("-", "_")
        value = os.getenv(env_key)
        if value:
            logger.debug("Resolved secret '%s' from env var '%s'", secret_id, env_key)
        return value


@dataclass
class RateLimitConfig:
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    retry_after_seconds: int = 60


@dataclass
class PartnerConfig:
    partner_id: str
    vendor: str
    display_name: str = ""
    base_url: str = ""
    auth_type: str = "oauth2"
    client_id_secret: str = ""
    client_secret_secret: str = ""
    private_key_secret: str = ""
    scopes: List[str] = field(default_factory=list)
    fhir_version: str = "R4"
    mllp_host: str = ""
    mllp_port: int = 2575
    webhook_secret_key: str = ""
    enabled: bool = True
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    extra: Dict[str, Any] = field(default_factory=dict)
    _client_id: Optional[str] = field(default=None, repr=False)
    _client_secret: Optional[str] = field(default=None, repr=False)
    _private_key: Optional[str] = field(default=None, repr=False)

    def resolve_credentials(self, secret_client: SecretManagerClient) -> None:
        if self.client_id_secret:
            self._client_id = secret_client.get_secret(self.client_id_secret)
        if self.client_secret_secret:
            self._client_secret = secret_client.get_secret(self.client_secret_secret)
        if self.private_key_secret:
            self._private_key = secret_client.get_secret(self.private_key_secret)

    @property
    def client_id(self) -> Optional[str]:
        return self._client_id

    @property
    def client_secret(self) -> Optional[str]:
        return self._client_secret

    @property
    def private_key(self) -> Optional[str]:
        return self._private_key


@dataclass
class AppConfig:
    environment: str = _ENV
    debug: bool = _ENV == "dev"
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", "8080"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO" if _ENV != "dev" else "DEBUG")
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "")
    pubsub_topic_inbound: str = os.getenv("PUBSUB_TOPIC_INBOUND", "ihep-ehr-inbound-events")
    pubsub_topic_outbound: str = os.getenv("PUBSUB_TOPIC_OUTBOUND", "ihep-ehr-outbound-events")
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "ihep_integration_logs")
    cors_origins: List[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","))
    global_rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    partners: Dict[str, PartnerConfig] = field(default_factory=dict)
    _secret_client: Optional[SecretManagerClient] = field(default=None, repr=False)

    @property
    def secret_client(self) -> SecretManagerClient:
        if self._secret_client is None:
            self._secret_client = SecretManagerClient(self.gcp_project_id)
        return self._secret_client


_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent / "config"


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        logger.warning("Config file not found: %s", path)
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    logger.info("Loaded config from %s", path)
    return data


def _parse_rate_limit(raw: Dict[str, Any]) -> RateLimitConfig:
    return RateLimitConfig(
        requests_per_minute=raw.get("requests_per_minute", 60),
        requests_per_hour=raw.get("requests_per_hour", 1000),
        burst_size=raw.get("burst_size", 10),
        retry_after_seconds=raw.get("retry_after_seconds", 60),
    )


def _parse_partner(partner_id: str, raw: Dict[str, Any]) -> PartnerConfig:
    rate_raw = raw.pop("rate_limit", {})
    rate_cfg = _parse_rate_limit(rate_raw) if rate_raw else RateLimitConfig()
    scopes = raw.pop("scopes", [])
    if isinstance(scopes, str):
        scopes = [s.strip() for s in scopes.split(",")]
    extra = raw.pop("extra", {})
    return PartnerConfig(
        partner_id=partner_id, vendor=raw.get("vendor", "unknown"),
        display_name=raw.get("display_name", partner_id),
        base_url=raw.get("base_url", ""), auth_type=raw.get("auth_type", "oauth2"),
        client_id_secret=raw.get("client_id_secret", ""),
        client_secret_secret=raw.get("client_secret_secret", ""),
        private_key_secret=raw.get("private_key_secret", ""),
        scopes=scopes, fhir_version=raw.get("fhir_version", "R4"),
        mllp_host=raw.get("mllp_host", ""), mllp_port=int(raw.get("mllp_port", 2575)),
        webhook_secret_key=raw.get("webhook_secret_key", ""),
        enabled=raw.get("enabled", True), rate_limit=rate_cfg, extra=extra,
    )


def load_config(config_dir: Optional[str] = None, environment: Optional[str] = None) -> AppConfig:
    """Build the full AppConfig from YAML files and environment variables."""
    env = environment or _ENV
    cfg_dir = Path(config_dir) if config_dir else _DEFAULT_CONFIG_DIR
    base_raw = _load_yaml(cfg_dir / "base.yaml")
    env_raw = _load_yaml(cfg_dir / f"{env}.yaml")
    merged: Dict[str, Any] = {**base_raw, **env_raw}
    global_rl_raw = merged.pop("global_rate_limit", {})
    app_cfg = AppConfig(
        environment=env, debug=merged.get("debug", env == "dev"),
        host=merged.get("host", "0.0.0.0"),
        port=int(merged.get("port", os.getenv("PORT", "8080"))),
        log_level=merged.get("log_level", "INFO"),
        gcp_project_id=merged.get("gcp_project_id", os.getenv("GCP_PROJECT_ID", "")),
        pubsub_topic_inbound=merged.get("pubsub_topic_inbound", os.getenv("PUBSUB_TOPIC_INBOUND", "ihep-ehr-inbound-events")),
        pubsub_topic_outbound=merged.get("pubsub_topic_outbound", os.getenv("PUBSUB_TOPIC_OUTBOUND", "ihep-ehr-outbound-events")),
        bigquery_dataset=merged.get("bigquery_dataset", os.getenv("BIGQUERY_DATASET", "ihep_integration_logs")),
        cors_origins=merged.get("cors_origins", ["http://localhost:3000"]),
        global_rate_limit=_parse_rate_limit(global_rl_raw) if global_rl_raw else RateLimitConfig(),
    )
    inline_partners: Dict[str, Any] = merged.get("partners", {})
    for pid, praw in inline_partners.items():
        app_cfg.partners[pid] = _parse_partner(pid, dict(praw))
    partners_dir = cfg_dir / "partners"
    if partners_dir.is_dir():
        for pfile in sorted(partners_dir.glob("*.yaml")):
            pdata = _load_yaml(pfile)
            pid = pfile.stem
            if pdata:
                app_cfg.partners[pid] = _parse_partner(pid, pdata)
    for partner in app_cfg.partners.values():
        try:
            partner.resolve_credentials(app_cfg.secret_client)
        except Exception as exc:
            logger.error("Failed to resolve credentials for partner '%s': %s", partner.partner_id, exc)
    logger.info("Configuration loaded: env=%s, partners=%d", app_cfg.environment, len(app_cfg.partners))
    return app_cfg
