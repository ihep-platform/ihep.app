"""
Epic EHR Adapter

Integrates with Epic's SMART on FHIR APIs using OAuth 2.0 with PKCE
for backend-service authentication. Supports FHIR R4 reads for Patient,
Observation, Appointment, and CarePlan resources, as well as write-back
and subscription management.

Reference documentation:
- https://fhir.epic.com/
- https://open.epic.com/
"""

import base64
import hashlib
import logging
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import jwt as pyjwt
import requests
from cryptography.hazmat.primitives import serialization

from adapters.base_adapter import BaseEHRAdapter

logger = logging.getLogger(__name__)

# Epic sandbox base URLs
_EPIC_SANDBOX_FHIR_BASE = 'https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4'
_EPIC_SANDBOX_TOKEN_URL = 'https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token'
_EPIC_SANDBOX_AUTH_URL = 'https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize'

# FHIR R4 resource paths
_RESOURCE_PATHS = {
    'Patient': 'Patient',
    'Observation': 'Observation',
    'Appointment': 'Appointment',
    'CarePlan': 'CarePlan',
    'Encounter': 'Encounter',
    'Condition': 'Condition',
    'MedicationRequest': 'MedicationRequest',
    'AllergyIntolerance': 'AllergyIntolerance',
}

# Default timeout for HTTP requests (seconds)
_REQUEST_TIMEOUT = 30


class EpicAdapter(BaseEHRAdapter):
    """
    Adapter for Epic Systems using SMART on FHIR (Backend Services).

    Authentication uses the *backend services* profile: the adapter signs
    a JWT with its private key, exchanges it at Epic's token endpoint for
    an access token, and uses that bearer token for subsequent FHIR calls.
    """

    def __init__(self) -> None:
        super().__init__()
        self._fhir_base_url: str = _EPIC_SANDBOX_FHIR_BASE
        self._token_url: str = _EPIC_SANDBOX_TOKEN_URL
        self._auth_url: str = _EPIC_SANDBOX_AUTH_URL
        self._client_id: str = ''
        self._private_key: Optional[bytes] = None
        self._refresh_token: Optional[str] = None
        self._token_refresh_buffer_seconds: int = 120  # refresh 2 min before expiry

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Inject Epic-specific configuration.

        Expected config keys:
            - base_url: FHIR R4 base URL (defaults to sandbox)
            - token_url: OAuth token endpoint
            - auth_url: OAuth authorisation endpoint
            - client_id: Registered SMART app client ID
            - client_secret: Private key PEM or JWK for backend-service auth
            - scopes: List of SMART scopes
        """
        super().configure(config)

        self._fhir_base_url = config.get('base_url', _EPIC_SANDBOX_FHIR_BASE).rstrip('/')
        self._token_url = config.get('token_url', _EPIC_SANDBOX_TOKEN_URL)
        self._auth_url = config.get('auth_url', _EPIC_SANDBOX_AUTH_URL)
        self._client_id = config.get('client_id', '')

        # The "client_secret" for Epic backend services is actually a PEM
        # private key used to sign the JWT assertion.
        raw_secret = config.get('client_secret', '')
        if raw_secret and '-----BEGIN' in raw_secret:
            self._private_key = raw_secret.encode('utf-8')
        elif raw_secret:
            # Assume base64-encoded PEM
            try:
                self._private_key = base64.b64decode(raw_secret)
            except Exception:
                self._private_key = raw_secret.encode('utf-8')

    # ------------------------------------------------------------------
    # Authentication (Backend Services with signed JWT assertion)
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """
        Authenticate using SMART Backend Services (OAuth 2.0 + signed JWT).

        Generates a client-assertion JWT signed with the private key,
        exchanges it at Epic's token endpoint, and stores the resulting
        access token.

        Returns:
            True on success, False on failure.
        """
        if not self._client_id:
            self.logger.error("Cannot authenticate: client_id not configured")
            return False

        if not self._private_key:
            self.logger.error("Cannot authenticate: private key not configured")
            return False

        try:
            now = datetime.utcnow()
            assertion_payload = {
                'iss': self._client_id,
                'sub': self._client_id,
                'aud': self._token_url,
                'jti': str(uuid.uuid4()),
                'iat': now,
                'exp': now + timedelta(minutes=5),
            }

            # Sign with RS384 (Epic's recommended algorithm)
            client_assertion = pyjwt.encode(
                assertion_payload,
                self._private_key,
                algorithm='RS384',
            )

            scopes = self._config.get('scopes', ['system/*.read'])
            token_data = {
                'grant_type': 'client_credentials',
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                'client_assertion': client_assertion,
                'scope': ' '.join(scopes) if isinstance(scopes, list) else scopes,
            }

            response = requests.post(
                self._token_url,
                data=token_data,
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

            self.logger.info("Epic authentication successful; token expires in %ds", expires_in)
            return True

        except requests.HTTPError as e:
            self.logger.error("Epic token request failed: HTTP %s - %s", e.response.status_code, e.response.text[:500])
            self._authenticated = False
            return False
        except Exception as e:
            self.logger.error("Epic authentication error: %s: %s", type(e).__name__, e)
            self._authenticated = False
            return False

    def _refresh_access_token(self) -> bool:
        """
        Refresh the access token using the stored refresh token.

        Falls back to full re-authentication if no refresh token is
        available or the refresh attempt fails.

        Returns:
            True on success.
        """
        if not self._refresh_token:
            return self.authenticate()

        try:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self._refresh_token,
                'client_id': self._client_id,
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
            if 'refresh_token' in token_response:
                self._refresh_token = token_response['refresh_token']
            self._authenticated = True

            self.logger.info("Epic token refreshed; new expiry in %ds", expires_in)
            return True

        except Exception as e:
            self.logger.warning("Token refresh failed (%s), performing full re-auth", e)
            return self.authenticate()

    # ------------------------------------------------------------------
    # FHIR helpers
    # ------------------------------------------------------------------

    def _fhir_get(self, resource_path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Execute a GET request against the FHIR R4 API.

        Handles token refresh and pagination transparently.

        Args:
            resource_path: Relative path appended to the FHIR base URL.
            params: Optional query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            ConnectionError: On network or HTTP errors.
            LookupError: On 404 responses.
            PermissionError: On 401/403 responses.
        """
        self._ensure_authenticated()
        url = f"{self._fhir_base_url}/{resource_path}"

        try:
            response = requests.get(
                url,
                params=params,
                headers=self._build_headers(),
                timeout=_REQUEST_TIMEOUT,
            )

            if response.status_code == 401:
                # Token may have expired between check and call; try once more
                self.logger.debug("Received 401; refreshing token and retrying")
                self._refresh_access_token()
                response = requests.get(
                    url,
                    params=params,
                    headers=self._build_headers(),
                    timeout=_REQUEST_TIMEOUT,
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
            self.logger.error("FHIR GET %s failed: %s", url, e)
            raise ConnectionError(f"Epic API request failed: {e}") from e

    def _fhir_post(self, resource_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a POST request against the FHIR R4 API.

        Args:
            resource_path: Relative path appended to the FHIR base URL.
            payload: JSON body to send.

        Returns:
            Parsed JSON response.
        """
        self._ensure_authenticated()
        url = f"{self._fhir_base_url}/{resource_path}"

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._build_headers(),
                timeout=_REQUEST_TIMEOUT,
            )

            if response.status_code == 401:
                self._refresh_access_token()
                response = requests.post(
                    url,
                    json=payload,
                    headers=self._build_headers(),
                    timeout=_REQUEST_TIMEOUT,
                )

            if response.status_code in (401, 403):
                raise PermissionError(f"Access denied: HTTP {response.status_code}")
            response.raise_for_status()

            return response.json()

        except PermissionError:
            raise
        except requests.RequestException as e:
            self.logger.error("FHIR POST %s failed: %s", url, e)
            raise ConnectionError(f"Epic API request failed: {e}") from e

    def _fhir_get_all_pages(self, resource_path: str, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all pages of a FHIR Bundle and return the flattened entries.

        Args:
            resource_path: Relative resource path.
            params: Query parameters for the initial request.

        Returns:
            A flat list of resource dictionaries extracted from the Bundle.
        """
        entries: List[Dict[str, Any]] = []
        bundle = self._fhir_get(resource_path, params)

        while True:
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', entry)
                entries.append(resource)

            # Follow pagination links
            next_url = None
            for link in bundle.get('link', []):
                if link.get('relation') == 'next':
                    next_url = link.get('url')
                    break

            if not next_url:
                break

            try:
                self._ensure_authenticated()
                response = requests.get(
                    next_url,
                    headers=self._build_headers(),
                    timeout=_REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                bundle = response.json()
            except Exception as e:
                self.logger.warning("Pagination request failed: %s", e)
                break

        return entries

    # ------------------------------------------------------------------
    # Epic extension processing
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_epic_extensions(resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract Epic-specific FHIR extensions into a flat dictionary.

        Epic may include proprietary extensions under the URL prefix
        ``http://open.epic.com/``. This helper normalises them.

        Args:
            resource: A FHIR resource dictionary.

        Returns:
            Dictionary mapping short extension names to their values.
        """
        extensions: Dict[str, Any] = {}
        for ext in resource.get('extension', []):
            url: str = ext.get('url', '')
            if 'epic.com' in url.lower():
                short_name = url.rsplit('/', 1)[-1]
                # Extensions can carry different value types
                for key in ('valueString', 'valueCode', 'valueBoolean',
                            'valueInteger', 'valueDateTime', 'valueReference'):
                    if key in ext:
                        extensions[short_name] = ext[key]
                        break
        return extensions

    # ------------------------------------------------------------------
    # Public API - data retrieval
    # ------------------------------------------------------------------

    def fetch_patient(self, patient_id: str) -> Dict[str, Any]:
        """Retrieve a FHIR R4 Patient resource from Epic."""
        self.logger.info("Fetching patient %s from Epic", hashlib.sha256(patient_id.encode()).hexdigest()[:12])
        resource = self._fhir_get(f"Patient/{patient_id}")
        resource['_epic_extensions'] = self._extract_epic_extensions(resource)
        return resource

    def fetch_observations(
        self,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        observation_codes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve FHIR R4 Observation resources from Epic."""
        params: Dict[str, str] = {'patient': patient_id, '_count': '100'}

        # Date range filter
        if start_date:
            params['date'] = f'ge{start_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'
        if end_date:
            date_param = params.get('date', '')
            end_str = f'le{end_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'
            params['date'] = f'{date_param}&date={end_str}' if date_param else end_str

        # Code filter (LOINC codes)
        if observation_codes:
            params['code'] = ','.join(observation_codes)

        observations = self._fhir_get_all_pages('Observation', params)
        for obs in observations:
            obs['_epic_extensions'] = self._extract_epic_extensions(obs)
        return observations

    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve FHIR R4 Appointment resources from Epic."""
        params: Dict[str, str] = {
            'patient': patient_id,
            'date': f'ge{datetime.utcnow().strftime("%Y-%m-%d")}',
            '_count': '50',
        }
        return self._fhir_get_all_pages('Appointment', params)

    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve FHIR R4 CarePlan resources from Epic."""
        params: Dict[str, str] = {
            'patient': patient_id,
            'status': 'active',
            '_count': '50',
        }
        return self._fhir_get_all_pages('CarePlan', params)

    # ------------------------------------------------------------------
    # Public API - write-back
    # ------------------------------------------------------------------

    def push_observation(self, patient_id: str, observation: Dict[str, Any]) -> bool:
        """
        Write a FHIR R4 Observation resource to Epic.

        Ensures the observation payload has required fields and POSTs it
        to the Observation endpoint.
        """
        required_keys = ('code', 'status')
        for key in required_keys:
            if key not in observation:
                raise ValueError(f"Observation payload missing required key: {key}")

        # Ensure the subject reference is set
        observation.setdefault('resourceType', 'Observation')
        observation.setdefault('subject', {'reference': f'Patient/{patient_id}'})

        try:
            result = self._fhir_post('Observation', observation)
            self.logger.info(
                "Observation pushed to Epic for patient %s: id=%s",
                hashlib.sha256(patient_id.encode()).hexdigest()[:12],
                result.get('id', 'unknown'),
            )
            return True
        except Exception as e:
            self.logger.error("Failed to push observation: %s", e)
            return False

    # ------------------------------------------------------------------
    # Public API - subscriptions
    # ------------------------------------------------------------------

    def subscribe_to_events(self, event_types: List[str], webhook_url: str) -> str:
        """
        Register a FHIR Subscription resource in Epic.

        Epic supports FHIR R4 Subscriptions with ``rest-hook`` channel type
        for real-time notifications.

        Args:
            event_types: Resource-level events, e.g. ``['Encounter']``.
            webhook_url: HTTPS callback URL.

        Returns:
            The logical id of the created Subscription resource.
        """
        # Build criteria from event types (Epic uses resource-level criteria)
        criteria_parts = []
        for event in event_types:
            resource_type = event.split('.')[0].capitalize()
            criteria_parts.append(resource_type)

        # Create one subscription per resource type
        subscription_ids: List[str] = []
        for criteria in criteria_parts:
            subscription_payload = {
                'resourceType': 'Subscription',
                'status': 'requested',
                'reason': 'IHEP Platform EHR integration',
                'criteria': criteria,
                'channel': {
                    'type': 'rest-hook',
                    'endpoint': webhook_url,
                    'payload': 'application/fhir+json',
                    'header': ['Content-Type: application/fhir+json'],
                },
            }
            try:
                result = self._fhir_post('Subscription', subscription_payload)
                sub_id = result.get('id', str(uuid.uuid4()))
                subscription_ids.append(sub_id)
                self.logger.info("Created Epic subscription %s for %s", sub_id, criteria)
            except Exception as e:
                self.logger.error("Failed to create subscription for %s: %s", criteria, e)

        combined_id = ','.join(subscription_ids) if subscription_ids else str(uuid.uuid4())
        return combined_id

    # ------------------------------------------------------------------
    # Public API - connection health
    # ------------------------------------------------------------------

    def validate_connection(self) -> bool:
        """
        Validate connectivity by fetching Epic's CapabilityStatement.

        Returns:
            True if the server responds with a valid CapabilityStatement.
        """
        try:
            self._ensure_authenticated()
            response = requests.get(
                f"{self._fhir_base_url}/metadata",
                headers=self._build_headers(),
                timeout=_REQUEST_TIMEOUT,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('resourceType') == 'CapabilityStatement'
            self.logger.warning("Epic metadata endpoint returned HTTP %s", response.status_code)
            return False
        except Exception as e:
            self.logger.error("Epic connection validation failed: %s", e)
            return False

    def get_capabilities(self) -> Dict[str, Any]:
        """Return capability metadata for the Epic adapter."""
        return {
            'vendor': 'epic',
            'fhir_version': 'R4',
            'supports_read': True,
            'supports_write': True,
            'supports_subscriptions': True,
            'auth_type': 'smart_backend_services',
            'supported_resources': [
                'Patient', 'Observation', 'Appointment', 'CarePlan',
                'Encounter', 'Condition', 'MedicationRequest', 'AllergyIntolerance',
            ],
            'supported_event_types': [
                'patient.update', 'encounter.discharge', 'observation.create',
                'appointment.book', 'appointment.cancel',
            ],
        }
