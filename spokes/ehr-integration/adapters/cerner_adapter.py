"""
Cerner / Oracle Health EHR Adapter

Integrates with Cerner's FHIR R4 APIs (Millennium platform) using
OAuth 2.0 client-credentials flow via the Cerner Code developer program.

Reference documentation:
- https://fhir.cerner.com/
- https://code.cerner.com/
"""

import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from adapters.base_adapter import BaseEHRAdapter

logger = logging.getLogger(__name__)

# Cerner sandbox endpoints
_CERNER_SANDBOX_FHIR_BASE = 'https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d'
_CERNER_SANDBOX_TOKEN_URL = 'https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v1/token'
_CERNER_SANDBOX_AUTH_URL = 'https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v1/personas/provider/authorize'

_REQUEST_TIMEOUT = 30


class CernerAdapter(BaseEHRAdapter):
    """
    Adapter for Cerner / Oracle Health using FHIR R4 and the Millennium API.

    Authentication uses the standard OAuth 2.0 client-credentials grant.
    The adapter also supports Cerner-specific resource extensions and the
    legacy Millennium REST API for operations not yet available via FHIR.
    """

    def __init__(self) -> None:
        super().__init__()
        self._fhir_base_url: str = _CERNER_SANDBOX_FHIR_BASE
        self._token_url: str = _CERNER_SANDBOX_TOKEN_URL
        self._auth_url: str = _CERNER_SANDBOX_AUTH_URL
        self._client_id: str = ''
        self._client_secret: str = ''
        self._tenant_id: str = ''
        self._refresh_token: Optional[str] = None
        self._millennium_base_url: str = ''

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Inject Cerner-specific configuration.

        Expected config keys:
            base_url, token_url, auth_url, client_id, client_secret,
            tenant_id, scopes, millennium_base_url
        """
        super().configure(config)

        self._fhir_base_url = config.get('base_url', _CERNER_SANDBOX_FHIR_BASE).rstrip('/')
        self._token_url = config.get('token_url', _CERNER_SANDBOX_TOKEN_URL)
        self._auth_url = config.get('auth_url', _CERNER_SANDBOX_AUTH_URL)
        self._client_id = config.get('client_id', '')
        self._client_secret = config.get('client_secret', '')
        self._tenant_id = config.get('tenant_id', '')
        self._millennium_base_url = config.get('millennium_base_url', '').rstrip('/')

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """
        Authenticate via OAuth 2.0 client-credentials flow.

        Returns:
            True on success.
        """
        if not self._client_id or not self._client_secret:
            self.logger.error("Cannot authenticate: client_id or client_secret missing")
            return False

        try:
            scopes = self._config.get('scopes', ['system/Patient.read', 'system/Observation.read'])
            data = {
                'grant_type': 'client_credentials',
                'client_id': self._client_id,
                'client_secret': self._client_secret,
                'scope': ' '.join(scopes) if isinstance(scopes, list) else scopes,
            }

            response = requests.post(
                self._token_url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=_REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            token_response = response.json()
            self._access_token = token_response.get('access_token')
            expires_in = int(token_response.get('expires_in', 3600))
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            self._refresh_token = token_response.get('refresh_token')
            self._authenticated = True

            self.logger.info("Cerner authentication successful; token expires in %ds", expires_in)
            return True

        except requests.HTTPError as e:
            self.logger.error(
                "Cerner token request failed: HTTP %s - %s",
                e.response.status_code, e.response.text[:500],
            )
            self._authenticated = False
            return False
        except Exception as e:
            self.logger.error("Cerner authentication error: %s: %s", type(e).__name__, e)
            self._authenticated = False
            return False

    # ------------------------------------------------------------------
    # FHIR helpers
    # ------------------------------------------------------------------

    def _fhir_get(self, resource_path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute a FHIR GET request with automatic token refresh."""
        self._ensure_authenticated()
        url = f"{self._fhir_base_url}/{resource_path}"

        try:
            response = requests.get(
                url, params=params, headers=self._build_headers(), timeout=_REQUEST_TIMEOUT,
            )

            if response.status_code == 401:
                self.authenticate()
                response = requests.get(
                    url, params=params, headers=self._build_headers(), timeout=_REQUEST_TIMEOUT,
                )

            if response.status_code == 404:
                raise LookupError(f"Resource not found: {resource_path}")
            if response.status_code in (401, 403):
                raise PermissionError(f"Access denied: HTTP {response.status_code}")
            response.raise_for_status()
            return response.json()

        except (LookupError, PermissionError):
            raise
        except requests.RequestException as e:
            raise ConnectionError(f"Cerner API request failed: {e}") from e

    def _fhir_post(self, resource_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a FHIR POST request."""
        self._ensure_authenticated()
        url = f"{self._fhir_base_url}/{resource_path}"

        try:
            response = requests.post(
                url, json=payload, headers=self._build_headers(), timeout=_REQUEST_TIMEOUT,
            )

            if response.status_code == 401:
                self.authenticate()
                response = requests.post(
                    url, json=payload, headers=self._build_headers(), timeout=_REQUEST_TIMEOUT,
                )

            if response.status_code in (401, 403):
                raise PermissionError(f"Access denied: HTTP {response.status_code}")
            response.raise_for_status()
            return response.json()

        except PermissionError:
            raise
        except requests.RequestException as e:
            raise ConnectionError(f"Cerner API request failed: {e}") from e

    def _fhir_get_all_pages(self, resource_path: str, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Retrieve all pages of a FHIR Bundle."""
        entries: List[Dict[str, Any]] = []
        bundle = self._fhir_get(resource_path, params)

        while True:
            for entry in bundle.get('entry', []):
                entries.append(entry.get('resource', entry))

            next_url = None
            for link in bundle.get('link', []):
                if link.get('relation') == 'next':
                    next_url = link.get('url')
                    break

            if not next_url:
                break

            try:
                self._ensure_authenticated()
                resp = requests.get(next_url, headers=self._build_headers(), timeout=_REQUEST_TIMEOUT)
                resp.raise_for_status()
                bundle = resp.json()
            except Exception as e:
                self.logger.warning("Pagination failed: %s", e)
                break

        return entries

    # ------------------------------------------------------------------
    # Millennium API helpers
    # ------------------------------------------------------------------

    def _millennium_get(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Execute a GET against the Cerner Millennium REST API.

        Used for operations not available through the FHIR interface.
        """
        if not self._millennium_base_url:
            raise NotImplementedError("Millennium API base URL not configured")

        self._ensure_authenticated()
        url = f"{self._millennium_base_url}/{endpoint.lstrip('/')}"

        try:
            headers = {
                'Authorization': f'Bearer {self._access_token}',
                'Accept': 'application/json',
            }
            response = requests.get(url, params=params, headers=headers, timeout=_REQUEST_TIMEOUT)

            if response.status_code == 401:
                self.authenticate()
                headers['Authorization'] = f'Bearer {self._access_token}'
                response = requests.get(url, params=params, headers=headers, timeout=_REQUEST_TIMEOUT)

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            raise ConnectionError(f"Millennium API request failed: {e}") from e

    # ------------------------------------------------------------------
    # Cerner-specific resource handling
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_cerner_extensions(resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Cerner-specific extensions from a FHIR resource."""
        extensions: Dict[str, Any] = {}
        for ext in resource.get('extension', []):
            url: str = ext.get('url', '')
            if 'cerner.com' in url.lower() or 'oracle.com' in url.lower():
                short_name = url.rsplit('/', 1)[-1]
                for key in ('valueString', 'valueCode', 'valueBoolean',
                            'valueInteger', 'valueDateTime', 'valueReference',
                            'valueCoding', 'valueCodeableConcept'):
                    if key in ext:
                        extensions[short_name] = ext[key]
                        break
        return extensions

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_patient(self, patient_id: str) -> Dict[str, Any]:
        """Retrieve a FHIR R4 Patient resource from Cerner."""
        resource = self._fhir_get(f"Patient/{patient_id}")
        resource['_cerner_extensions'] = self._extract_cerner_extensions(resource)
        return resource

    def fetch_observations(
        self,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        observation_codes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve FHIR R4 Observation resources from Cerner."""
        params: Dict[str, str] = {'patient': patient_id, '_count': '100'}

        if start_date:
            params['date'] = f'ge{start_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'
        if end_date:
            end_str = f'le{end_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'
            existing = params.get('date', '')
            params['date'] = f'{existing}&date={end_str}' if existing else end_str

        if observation_codes:
            # Cerner supports LOINC code filter
            params['code'] = ','.join(observation_codes)

        observations = self._fhir_get_all_pages('Observation', params)
        for obs in observations:
            obs['_cerner_extensions'] = self._extract_cerner_extensions(obs)
        return observations

    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve FHIR R4 Appointment resources from Cerner."""
        params: Dict[str, str] = {
            'patient': patient_id,
            'date': f'ge{datetime.utcnow().strftime("%Y-%m-%d")}',
            '_count': '50',
        }
        return self._fhir_get_all_pages('Appointment', params)

    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve FHIR R4 CarePlan resources from Cerner."""
        params: Dict[str, str] = {
            'patient': patient_id,
            'status': 'active',
            '_count': '50',
        }
        return self._fhir_get_all_pages('CarePlan', params)

    def push_observation(self, patient_id: str, observation: Dict[str, Any]) -> bool:
        """Write a FHIR R4 Observation resource to Cerner."""
        for key in ('code', 'status'):
            if key not in observation:
                raise ValueError(f"Observation missing required key: {key}")

        observation.setdefault('resourceType', 'Observation')
        observation.setdefault('subject', {'reference': f'Patient/{patient_id}'})

        try:
            result = self._fhir_post('Observation', observation)
            self.logger.info("Observation pushed to Cerner: id=%s", result.get('id', 'unknown'))
            return True
        except Exception as e:
            self.logger.error("Failed to push observation to Cerner: %s", e)
            return False

    def subscribe_to_events(self, event_types: List[str], webhook_url: str) -> str:
        """Register a FHIR Subscription with Cerner."""
        subscription_ids: List[str] = []
        for event in event_types:
            resource_type = event.split('.')[0].capitalize()
            payload = {
                'resourceType': 'Subscription',
                'status': 'requested',
                'reason': 'IHEP Platform EHR Integration',
                'criteria': resource_type,
                'channel': {
                    'type': 'rest-hook',
                    'endpoint': webhook_url,
                    'payload': 'application/fhir+json',
                },
            }
            try:
                result = self._fhir_post('Subscription', payload)
                sub_id = result.get('id', str(uuid.uuid4()))
                subscription_ids.append(sub_id)
                self.logger.info("Created Cerner subscription %s for %s", sub_id, resource_type)
            except Exception as e:
                self.logger.error("Failed to create Cerner subscription for %s: %s", resource_type, e)

        return ','.join(subscription_ids) if subscription_ids else str(uuid.uuid4())

    def validate_connection(self) -> bool:
        """Validate connectivity by fetching the CapabilityStatement."""
        try:
            self._ensure_authenticated()
            response = requests.get(
                f"{self._fhir_base_url}/metadata",
                headers=self._build_headers(),
                timeout=_REQUEST_TIMEOUT,
            )
            if response.status_code == 200:
                return response.json().get('resourceType') == 'CapabilityStatement'
            return False
        except Exception as e:
            self.logger.error("Cerner connection validation failed: %s", e)
            return False

    def get_capabilities(self) -> Dict[str, Any]:
        """Return capability metadata for the Cerner adapter."""
        return {
            'vendor': 'cerner',
            'fhir_version': 'R4',
            'supports_read': True,
            'supports_write': True,
            'supports_subscriptions': True,
            'supports_millennium_api': bool(self._millennium_base_url),
            'auth_type': 'oauth2_client_credentials',
            'supported_resources': [
                'Patient', 'Observation', 'Appointment', 'CarePlan',
                'Encounter', 'Condition', 'MedicationRequest',
            ],
            'supported_event_types': [
                'patient.update', 'encounter.discharge', 'observation.create',
            ],
        }
