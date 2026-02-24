"""
Epic EHR Adapter

SMART on FHIR R4 integration using OAuth 2.0 Backend Services (signed JWT).

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import base64
import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import jwt as pyjwt
import requests

from adapters.base_adapter import BaseEHRAdapter

logger = logging.getLogger(__name__)

_EPIC_SANDBOX_FHIR_BASE = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
_EPIC_SANDBOX_TOKEN_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
_REQUEST_TIMEOUT = 30


class EpicAdapter(BaseEHRAdapter):
    """Adapter for Epic Systems using SMART Backend Services."""

    def __init__(self) -> None:
        super().__init__()
        self._fhir_base_url: str = _EPIC_SANDBOX_FHIR_BASE
        self._token_url: str = _EPIC_SANDBOX_TOKEN_URL
        self._client_id: str = ""
        self._private_key: Optional[bytes] = None

    def configure(self, config: Dict[str, Any]) -> None:
        super().configure(config)
        self._fhir_base_url = config.get("base_url", _EPIC_SANDBOX_FHIR_BASE).rstrip("/")
        self._token_url = config.get("token_url", _EPIC_SANDBOX_TOKEN_URL)
        self._client_id = config.get("client_id", "")
        raw_secret = config.get("client_secret", "")
        if raw_secret and "-----BEGIN" in raw_secret:
            self._private_key = raw_secret.encode("utf-8")
        elif raw_secret:
            try:
                self._private_key = base64.b64decode(raw_secret)
            except Exception:
                self._private_key = raw_secret.encode("utf-8")

    def authenticate(self) -> bool:
        if not self._client_id or not self._private_key:
            self.logger.error("Cannot authenticate: missing client_id or private key")
            return False
        try:
            now = datetime.utcnow()
            assertion = pyjwt.encode(
                {"iss": self._client_id, "sub": self._client_id,
                 "aud": self._token_url, "jti": str(uuid.uuid4()),
                 "iat": now, "exp": now + timedelta(minutes=5)},
                self._private_key, algorithm="RS384",
            )
            scopes = self._config.get("scopes", ["system/*.read"])
            resp = requests.post(self._token_url, data={
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": assertion,
                "scope": " ".join(scopes) if isinstance(scopes, list) else scopes,
            }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
            token_data = resp.json()
            self._access_token = token_data.get("access_token")
            self._token_expiry = datetime.utcnow() + timedelta(seconds=int(token_data.get("expires_in", 3600)))
            self._authenticated = True
            return True
        except Exception as e:
            self.logger.error("Epic authentication failed: %s", e)
            self._authenticated = False
            return False

    def _fhir_get(self, path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        self._ensure_authenticated()
        url = f"{self._fhir_base_url}/{path}"
        resp = requests.get(url, params=params, headers=self._build_headers(), timeout=_REQUEST_TIMEOUT)
        if resp.status_code == 401:
            self.authenticate()
            resp = requests.get(url, params=params, headers=self._build_headers(), timeout=_REQUEST_TIMEOUT)
        if resp.status_code == 404:
            raise LookupError(f"Resource not found: {path}")
        if resp.status_code in (401, 403):
            raise PermissionError(f"Access denied: HTTP {resp.status_code}")
        resp.raise_for_status()
        return resp.json()

    def _fhir_post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_authenticated()
        url = f"{self._fhir_base_url}/{path}"
        resp = requests.post(url, json=payload, headers=self._build_headers(), timeout=_REQUEST_TIMEOUT)
        if resp.status_code == 401:
            self.authenticate()
            resp = requests.post(url, json=payload, headers=self._build_headers(), timeout=_REQUEST_TIMEOUT)
        if resp.status_code in (401, 403):
            raise PermissionError(f"Access denied: HTTP {resp.status_code}")
        resp.raise_for_status()
        return resp.json()

    def _fhir_get_all_pages(self, path: str, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        bundle = self._fhir_get(path, params)
        while True:
            for entry in bundle.get("entry", []):
                entries.append(entry.get("resource", entry))
            next_url = None
            for link in bundle.get("link", []):
                if link.get("relation") == "next":
                    next_url = link.get("url")
                    break
            if not next_url:
                break
            try:
                self._ensure_authenticated()
                resp = requests.get(next_url, headers=self._build_headers(), timeout=_REQUEST_TIMEOUT)
                resp.raise_for_status()
                bundle = resp.json()
            except Exception:
                break
        return entries

    def fetch_patient(self, patient_id: str) -> Dict[str, Any]:
        return self._fhir_get(f"Patient/{patient_id}")

    def fetch_observations(self, patient_id: str, start_date=None, end_date=None, observation_codes=None) -> List[Dict[str, Any]]:
        params: Dict[str, str] = {"patient": patient_id, "_count": "100"}
        if start_date:
            params["date"] = f'ge{start_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'
        if end_date:
            end_str = f'le{end_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'
            params["date"] = f'{params.get("date", "")}&date={end_str}' if "date" in params else end_str
        if observation_codes:
            params["code"] = ",".join(observation_codes)
        return self._fhir_get_all_pages("Observation", params)

    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        return self._fhir_get_all_pages("Appointment", {
            "patient": patient_id,
            "date": f'ge{datetime.utcnow().strftime("%Y-%m-%d")}',
            "_count": "50",
        })

    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]:
        return self._fhir_get_all_pages("CarePlan", {"patient": patient_id, "status": "active", "_count": "50"})

    def push_observation(self, patient_id: str, observation: Dict[str, Any]) -> bool:
        for key in ("code", "status"):
            if key not in observation:
                raise ValueError(f"Observation missing required key: {key}")
        observation.setdefault("resourceType", "Observation")
        observation.setdefault("subject", {"reference": f"Patient/{patient_id}"})
        try:
            self._fhir_post("Observation", observation)
            return True
        except Exception as e:
            self.logger.error("Failed to push observation: %s", e)
            return False

    def subscribe_to_events(self, event_types: List[str], webhook_url: str) -> str:
        ids = []
        for event in event_types:
            resource_type = event.split(".")[0].capitalize()
            try:
                result = self._fhir_post("Subscription", {
                    "resourceType": "Subscription", "status": "requested",
                    "reason": "IHEP Platform EHR integration", "criteria": resource_type,
                    "channel": {"type": "rest-hook", "endpoint": webhook_url, "payload": "application/fhir+json"},
                })
                ids.append(result.get("id", str(uuid.uuid4())))
            except Exception as e:
                self.logger.error("Failed to create subscription for %s: %s", resource_type, e)
        return ",".join(ids) if ids else str(uuid.uuid4())

    def validate_connection(self) -> bool:
        try:
            self._ensure_authenticated()
            resp = requests.get(f"{self._fhir_base_url}/metadata", headers=self._build_headers(), timeout=_REQUEST_TIMEOUT)
            return resp.status_code == 200 and resp.json().get("resourceType") == "CapabilityStatement"
        except Exception:
            return False

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "vendor": "epic", "fhir_version": "R4",
            "supports_read": True, "supports_write": True, "supports_subscriptions": True,
            "auth_type": "smart_backend_services",
            "supported_resources": ["Patient", "Observation", "Appointment", "CarePlan", "Encounter", "Condition", "MedicationRequest", "AllergyIntolerance"],
            "supported_event_types": ["patient.update", "encounter.discharge", "observation.create", "appointment.book", "appointment.cancel"],
        }
