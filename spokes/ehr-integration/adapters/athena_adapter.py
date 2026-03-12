"""
athenahealth EHR Adapter

Integrates with the athenahealth APIs (athenaClinicals, athenaCoordinator)
for patient data, encounters, appointments, and clinical results.
Uses OAuth 2.0 client-credentials authentication.

Reference documentation:
- https://docs.athenahealth.com/api/
"""

import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from adapters.base_adapter import BaseEHRAdapter

logger = logging.getLogger(__name__)

# athenahealth sandbox endpoints
_ATHENA_SANDBOX_BASE = 'https://api.preview.platform.athenahealth.com'
_ATHENA_SANDBOX_TOKEN_URL = 'https://api.preview.platform.athenahealth.com/oauth2/v1/token'
_ATHENA_API_VERSION = 'v1'

_REQUEST_TIMEOUT = 30


class AthenaAdapter(BaseEHRAdapter):
    """
    Adapter for athenahealth using the athenaClinicals and athenaCoordinator APIs.

    Authentication uses OAuth 2.0 client-credentials grant. The adapter
    translates athena-proprietary JSON responses into FHIR R4 format for
    downstream consistency.
    """

    def __init__(self) -> None:
        super().__init__()
        self._base_url: str = _ATHENA_SANDBOX_BASE
        self._token_url: str = _ATHENA_SANDBOX_TOKEN_URL
        self._api_version: str = _ATHENA_API_VERSION
        self._client_id: str = ''
        self._client_secret: str = ''
        self._practice_id: str = ''

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Inject athenahealth-specific configuration.

        Expected config keys:
            base_url, token_url, client_id, client_secret, practice_id
        """
        super().configure(config)

        self._base_url = config.get('base_url', _ATHENA_SANDBOX_BASE).rstrip('/')
        self._token_url = config.get('token_url', _ATHENA_SANDBOX_TOKEN_URL)
        self._api_version = config.get('api_version', _ATHENA_API_VERSION)
        self._client_id = config.get('client_id', '')
        self._client_secret = config.get('client_secret', '')
        self._practice_id = config.get('practice_id', '')

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
            data = {
                'grant_type': 'client_credentials',
                'scope': 'athena/service/Athenanet.MDP.*',
            }
            response = requests.post(
                self._token_url,
                data=data,
                auth=(self._client_id, self._client_secret),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=_REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            token_response = response.json()
            self._access_token = token_response.get('access_token')
            expires_in = int(token_response.get('expires_in', 3600))
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            self._authenticated = True

            self.logger.info("athenahealth authentication successful; token expires in %ds", expires_in)
            return True

        except requests.HTTPError as e:
            self.logger.error(
                "athena token request failed: HTTP %s - %s",
                e.response.status_code, e.response.text[:500],
            )
            self._authenticated = False
            return False
        except Exception as e:
            self.logger.error("athena authentication error: %s: %s", type(e).__name__, e)
            self._authenticated = False
            return False

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _api_url(self, endpoint: str) -> str:
        """Build a full API URL for the given endpoint."""
        practice_segment = f"/{self._practice_id}" if self._practice_id else ''
        return f"{self._base_url}/{self._api_version}{practice_segment}/{endpoint.lstrip('/')}"

    def _api_get(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute a GET request against the athena API."""
        self._ensure_authenticated()
        url = self._api_url(endpoint)

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

            if response.status_code == 404:
                raise LookupError(f"Resource not found: {endpoint}")
            if response.status_code in (401, 403):
                raise PermissionError(f"Access denied: HTTP {response.status_code}")

            response.raise_for_status()
            return response.json()

        except (LookupError, PermissionError):
            raise
        except requests.RequestException as e:
            raise ConnectionError(f"athena API request failed: {e}") from e

    def _api_post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a POST request against the athena API."""
        self._ensure_authenticated()
        url = self._api_url(endpoint)

        try:
            headers = {
                'Authorization': f'Bearer {self._access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            response = requests.post(url, json=payload, headers=headers, timeout=_REQUEST_TIMEOUT)

            if response.status_code == 401:
                self.authenticate()
                headers['Authorization'] = f'Bearer {self._access_token}'
                response = requests.post(url, json=payload, headers=headers, timeout=_REQUEST_TIMEOUT)

            if response.status_code in (401, 403):
                raise PermissionError(f"Access denied: HTTP {response.status_code}")

            response.raise_for_status()
            return response.json() if response.content else {}

        except PermissionError:
            raise
        except requests.RequestException as e:
            raise ConnectionError(f"athena API request failed: {e}") from e

    def _api_get_all_pages(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Retrieve all pages from a paginated athena API endpoint."""
        all_items: List[Dict[str, Any]] = []
        current_params = dict(params or {})
        current_params.setdefault('limit', '100')
        current_params.setdefault('offset', '0')

        while True:
            result = self._api_get(endpoint, current_params)

            # athena returns results in various top-level keys
            items = []
            for key in ('patients', 'results', 'appointments', 'encounters',
                        'observations', 'careplans', 'data', 'totalcount'):
                if key in result and isinstance(result[key], list):
                    items = result[key]
                    break
            if not items and isinstance(result, list):
                items = result

            all_items.extend(items)

            # Check for next page
            next_offset = result.get('next')
            total = result.get('totalcount', 0)
            if next_offset and len(all_items) < total:
                current_params['offset'] = str(int(current_params['offset']) + int(current_params['limit']))
            else:
                break

        return all_items

    # ------------------------------------------------------------------
    # Response transformation helpers
    # ------------------------------------------------------------------

    def _to_fhir_patient(self, athena_patient: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an athena patient record to FHIR R4 Patient format."""
        return {
            'resourceType': 'Patient',
            'id': str(athena_patient.get('patientid', '')),
            'name': [{
                'use': 'official',
                'family': athena_patient.get('lastname', ''),
                'given': [athena_patient.get('firstname', '')],
                'suffix': [athena_patient.get('suffix', '')] if athena_patient.get('suffix') else [],
            }],
            'birthDate': athena_patient.get('dob', ''),
            'gender': athena_patient.get('sex', '').lower(),
            'address': [{
                'use': 'home',
                'line': [
                    athena_patient.get('address1', ''),
                    athena_patient.get('address2', ''),
                ],
                'city': athena_patient.get('city', ''),
                'state': athena_patient.get('state', ''),
                'postalCode': athena_patient.get('zip', ''),
            }],
            'telecom': [
                {'system': 'phone', 'value': athena_patient.get('homephone', ''), 'use': 'home'},
                {'system': 'phone', 'value': athena_patient.get('mobilephone', ''), 'use': 'mobile'},
                {'system': 'email', 'value': athena_patient.get('email', ''), 'use': 'home'},
            ],
            'identifier': [{
                'system': 'athenahealth',
                'value': str(athena_patient.get('patientid', '')),
            }],
            '_athena_raw': athena_patient,
        }

    def _to_fhir_observation(self, result: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Convert an athena clinical result to FHIR R4 Observation format."""
        return {
            'resourceType': 'Observation',
            'id': str(result.get('resultid', result.get('clinicalresultid', str(uuid.uuid4())))),
            'status': 'final',
            'subject': {'reference': f'Patient/{patient_id}'},
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': result.get('loinc', ''),
                    'display': result.get('description', result.get('clinicalresultname', '')),
                }],
                'text': result.get('description', result.get('clinicalresultname', '')),
            },
            'valueQuantity': {
                'value': result.get('value', result.get('resultvalue', '')),
                'unit': result.get('units', ''),
            },
            'effectiveDateTime': result.get('resultdate', result.get('datetime', '')),
            'referenceRange': [{
                'text': result.get('referencerange', result.get('normalrange', '')),
            }],
            'category': [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': result.get('category', 'laboratory'),
                }],
            }],
            '_athena_raw': result,
        }

    def _to_fhir_appointment(self, appt: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Convert an athena appointment to FHIR R4 Appointment format."""
        status_map = {
            'f': 'fulfilled',
            'x': 'cancelled',
            'o': 'booked',
            '2': 'checked-in',
            '3': 'arrived',
            '4': 'fulfilled',
        }
        raw_status = str(appt.get('appointmentstatus', 'o')).lower()
        fhir_status = status_map.get(raw_status, 'booked')

        return {
            'resourceType': 'Appointment',
            'id': str(appt.get('appointmentid', str(uuid.uuid4()))),
            'status': fhir_status,
            'start': appt.get('date', '') + 'T' + appt.get('starttime', '00:00'),
            'end': appt.get('date', '') + 'T' + appt.get('endtime', appt.get('starttime', '00:00')),
            'description': appt.get('appointmenttype', ''),
            'participant': [
                {
                    'actor': {'reference': f'Patient/{patient_id}'},
                    'status': 'accepted',
                },
                {
                    'actor': {
                        'reference': f'Practitioner/{appt.get("providerid", "")}',
                        'display': appt.get('providername', ''),
                    },
                    'status': 'accepted',
                },
            ],
            'serviceType': [{
                'coding': [{
                    'display': appt.get('appointmenttype', ''),
                }],
            }],
            '_athena_raw': appt,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_patient(self, patient_id: str) -> Dict[str, Any]:
        """Retrieve a patient from athenahealth and return as FHIR R4."""
        result = self._api_get(f'patients/{patient_id}')

        # athena may return a list
        if isinstance(result, list):
            if not result:
                raise LookupError(f"Patient not found: {patient_id}")
            result = result[0]
        elif isinstance(result, dict) and 'patients' in result:
            patients = result['patients']
            if not patients:
                raise LookupError(f"Patient not found: {patient_id}")
            result = patients[0]

        return self._to_fhir_patient(result)

    def fetch_observations(
        self,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        observation_codes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve clinical results from athenahealth as FHIR R4 Observations."""
        params: Dict[str, str] = {}

        if start_date:
            params['startdate'] = start_date.strftime('%m/%d/%Y')
        if end_date:
            params['enddate'] = end_date.strftime('%m/%d/%Y')

        # Fetch lab results from athenaClinicals
        raw_results = self._api_get_all_pages(
            f'patients/{patient_id}/labresults',
            params,
        )

        observations = []
        for item in raw_results:
            obs = self._to_fhir_observation(item, patient_id)
            if observation_codes:
                obs_codes = [c.get('code', '') for c in obs.get('code', {}).get('coding', [])]
                if not any(code in obs_codes for code in observation_codes):
                    continue
            observations.append(obs)

        return observations

    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve appointments from athenahealth as FHIR R4 Appointments."""
        params: Dict[str, str] = {
            'startdate': datetime.utcnow().strftime('%m/%d/%Y'),
            'enddate': (datetime.utcnow() + timedelta(days=365)).strftime('%m/%d/%Y'),
        }

        raw_appts = self._api_get_all_pages(
            f'patients/{patient_id}/appointments',
            params,
        )

        return [self._to_fhir_appointment(appt, patient_id) for appt in raw_appts]

    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve care plans from athenahealth as FHIR R4 CarePlans."""
        # athena exposes care plans via the encounter/chart endpoint
        try:
            raw_plans = self._api_get_all_pages(f'patients/{patient_id}/chartalert')
        except LookupError:
            return []

        care_plans: List[Dict[str, Any]] = []
        for item in raw_plans:
            care_plans.append({
                'resourceType': 'CarePlan',
                'id': str(item.get('chartalertid', str(uuid.uuid4()))),
                'status': 'active',
                'intent': 'plan',
                'title': item.get('note', ''),
                'subject': {'reference': f'Patient/{patient_id}'},
                'category': [{
                    'coding': [{
                        'display': item.get('alerttype', 'General'),
                    }],
                }],
                '_athena_raw': item,
            })

        return care_plans

    def push_observation(self, patient_id: str, observation: Dict[str, Any]) -> bool:
        """Write an observation back to athenahealth."""
        for key in ('code', 'status'):
            if key not in observation:
                raise ValueError(f"Observation missing required key: {key}")

        try:
            code_display = ''
            coding = observation.get('code', {}).get('coding', [])
            if coding:
                code_display = coding[0].get('display', '')

            value = ''
            if 'valueQuantity' in observation:
                value = str(observation['valueQuantity'].get('value', ''))

            payload = {
                'clinicalresultname': code_display,
                'resultvalue': value,
                'resultdate': datetime.utcnow().strftime('%m/%d/%Y'),
            }

            self._api_post(f'patients/{patient_id}/labresults', payload)
            self.logger.info(
                "Observation pushed to athena for patient %s",
                hashlib.sha256(patient_id.encode()).hexdigest()[:12],
            )
            return True

        except Exception as e:
            self.logger.error("Failed to push observation to athena: %s", e)
            return False

    def subscribe_to_events(self, event_types: List[str], webhook_url: str) -> str:
        """
        Register webhook subscriptions with athenahealth.

        athenahealth supports changed-data subscriptions via their
        ``/changedpatients`` and similar endpoints. This adapter registers
        a subscription configuration that the sync engine polls.
        """
        try:
            payload = {
                'eventtype': ','.join(event_types),
                'callbackurl': webhook_url,
            }
            result = self._api_post('subscriptions', payload)
            sub_id = result.get('subscriptionid', str(uuid.uuid4()))
            self.logger.info("athena subscription created: %s", sub_id)
            return str(sub_id)
        except Exception as e:
            self.logger.warning("athena subscription creation failed: %s; using polling", e)
            return str(uuid.uuid4())

    def validate_connection(self) -> bool:
        """Validate connectivity by calling the ping endpoint."""
        try:
            self._ensure_authenticated()
            url = f"{self._base_url}/{self._api_version}/ping"
            response = requests.get(
                url,
                headers={
                    'Authorization': f'Bearer {self._access_token}',
                    'Accept': 'application/json',
                },
                timeout=_REQUEST_TIMEOUT,
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error("athena connection validation failed: %s", e)
            return False

    def get_capabilities(self) -> Dict[str, Any]:
        """Return capability metadata for the athenahealth adapter."""
        return {
            'vendor': 'athenahealth',
            'fhir_version': 'R4 (via adapter translation)',
            'supports_read': True,
            'supports_write': True,
            'supports_subscriptions': True,
            'auth_type': 'oauth2_client_credentials',
            'api_type': 'athena_rest',
            'supported_resources': [
                'Patient', 'Observation', 'Appointment', 'CarePlan', 'Encounter',
            ],
            'supported_event_types': [
                'patient.update', 'appointment.create', 'appointment.cancel',
                'encounter.close', 'labresult.create',
            ],
        }
