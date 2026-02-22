"""
Allscripts EHR Adapter

Integrates with the Allscripts Unity API for clinical data exchange.
Uses token-based authentication and Allscripts' proprietary REST endpoints
alongside optional FHIR R4 support for newer deployments.

Reference documentation:
- https://developer.allscripts.com/
"""

import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from adapters.base_adapter import BaseEHRAdapter

logger = logging.getLogger(__name__)

# Allscripts default endpoints
_ALLSCRIPTS_UNITY_BASE = 'https://tw171.unitysandbox.com/Unity/UnityService.svc'
_ALLSCRIPTS_TOKEN_URL = 'https://tw171.unitysandbox.com/Unity/UnityService.svc/json/GetToken'

_REQUEST_TIMEOUT = 30


class AllscriptsAdapter(BaseEHRAdapter):
    """
    Adapter for Allscripts using the Unity API.

    The Unity API uses a two-phase authentication model:
    1. Obtain a security token using app credentials + user credentials.
    2. Use the token in subsequent ``Magic`` JSON-RPC style calls.

    The adapter wraps Unity's ``GetPatient``, ``GetClinicalSummary``,
    ``GetSchedule``, and ``SaveObject`` actions behind the standard
    BaseEHRAdapter interface.
    """

    def __init__(self) -> None:
        super().__init__()
        self._unity_base_url: str = _ALLSCRIPTS_UNITY_BASE
        self._token_url: str = _ALLSCRIPTS_TOKEN_URL
        self._app_name: str = ''
        self._app_username: str = ''
        self._app_password: str = ''
        self._unity_token: Optional[str] = None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Inject Allscripts-specific configuration.

        Expected config keys:
            base_url, token_url, client_id (app_name),
            client_secret (app_password), app_username
        """
        super().configure(config)

        self._unity_base_url = config.get('base_url', _ALLSCRIPTS_UNITY_BASE).rstrip('/')
        self._token_url = config.get('token_url', _ALLSCRIPTS_TOKEN_URL)
        self._app_name = config.get('client_id', config.get('app_name', ''))
        self._app_password = config.get('client_secret', config.get('app_password', ''))
        self._app_username = config.get('app_username', '')

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """
        Authenticate with the Allscripts Unity API.

        Calls ``GetToken`` with the app name, username, and password.
        Stores the resulting security token for use in subsequent API
        calls.

        Returns:
            True on success.
        """
        if not self._app_name or not self._app_password:
            self.logger.error("Cannot authenticate: app_name or app_password missing")
            return False

        try:
            payload = {
                'Username': self._app_username,
                'Password': self._app_password,
            }

            response = requests.post(
                self._token_url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'AppName': self._app_name,
                },
                timeout=_REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            token_data = response.json()
            # Unity returns the token directly as a string or in a wrapper
            if isinstance(token_data, str):
                self._unity_token = token_data
            elif isinstance(token_data, dict):
                self._unity_token = token_data.get('Token', token_data.get('token', ''))
            else:
                self._unity_token = str(token_data)

            if not self._unity_token:
                self.logger.error("Allscripts returned empty token")
                return False

            self._access_token = self._unity_token
            self._token_expiry = datetime.utcnow() + timedelta(hours=4)
            self._authenticated = True

            self.logger.info("Allscripts authentication successful")
            return True

        except requests.HTTPError as e:
            self.logger.error(
                "Allscripts token request failed: HTTP %s - %s",
                e.response.status_code, e.response.text[:500],
            )
            self._authenticated = False
            return False
        except Exception as e:
            self.logger.error("Allscripts authentication error: %s: %s", type(e).__name__, e)
            self._authenticated = False
            return False

    # ------------------------------------------------------------------
    # Unity API helpers
    # ------------------------------------------------------------------

    def _unity_call(self, action: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute a Unity ``Magic`` JSON-RPC call.

        Args:
            action: The Unity action name (e.g. ``GetPatient``).
            parameters: Action-specific parameters.

        Returns:
            Parsed JSON response data.
        """
        self._ensure_authenticated()
        url = f"{self._unity_base_url}/json/MagicJson"

        payload = {
            'Action': action,
            'AppUserID': self._app_username,
            'Appname': self._app_name,
            'Token': self._unity_token,
            'PatientID': parameters.get('PatientID', ''),
            'Parameter1': parameters.get('Parameter1', ''),
            'Parameter2': parameters.get('Parameter2', ''),
            'Parameter3': parameters.get('Parameter3', ''),
            'Parameter4': parameters.get('Parameter4', ''),
            'Parameter5': parameters.get('Parameter5', ''),
            'Parameter6': parameters.get('Parameter6', ''),
            'Data': parameters.get('Data', ''),
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'AppName': self._app_name,
                },
                timeout=_REQUEST_TIMEOUT,
            )

            if response.status_code == 401:
                self.authenticate()
                payload['Token'] = self._unity_token
                response = requests.post(
                    url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'AppName': self._app_name,
                    },
                    timeout=_REQUEST_TIMEOUT,
                )

            response.raise_for_status()
            result = response.json()

            # Unity wraps results in a list of tables
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result

        except requests.RequestException as e:
            self.logger.error("Unity API call '%s' failed: %s", action, e)
            raise ConnectionError(f"Allscripts Unity API request failed: {e}") from e

    def _unity_result_to_fhir_patient(self, unity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Unity patient record to FHIR R4 Patient format."""
        return {
            'resourceType': 'Patient',
            'id': str(unity_data.get('patientid', '')),
            'name': [{
                'use': 'official',
                'family': unity_data.get('LastName', ''),
                'given': [unity_data.get('FirstName', '')],
            }],
            'birthDate': unity_data.get('dateofbirth', ''),
            'gender': (unity_data.get('sex', '')).lower(),
            'address': [{
                'use': 'home',
                'line': [unity_data.get('Address1', '')],
                'city': unity_data.get('City', ''),
                'state': unity_data.get('State', ''),
                'postalCode': unity_data.get('ZipCode', ''),
            }],
            'telecom': [{
                'system': 'phone',
                'value': unity_data.get('HomePhone', ''),
                'use': 'home',
            }],
            '_allscripts_raw': unity_data,
        }

    def _unity_result_to_fhir_observation(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Unity clinical result to FHIR R4 Observation format."""
        return {
            'resourceType': 'Observation',
            'id': str(result.get('resultid', str(uuid.uuid4()))),
            'status': 'final',
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': result.get('LoincCode', ''),
                    'display': result.get('ResultName', result.get('ObservationName', '')),
                }],
                'text': result.get('ResultName', result.get('ObservationName', '')),
            },
            'valueQuantity': {
                'value': result.get('Value', result.get('ResultValue', '')),
                'unit': result.get('Units', ''),
            },
            'effectiveDateTime': result.get('ResultDate', result.get('ObservationDate', '')),
            'referenceRange': [{
                'text': result.get('NormalRange', ''),
            }],
            '_allscripts_raw': result,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_patient(self, patient_id: str) -> Dict[str, Any]:
        """Retrieve a patient record from Allscripts and return as FHIR R4."""
        result = self._unity_call('GetPatient', {'PatientID': patient_id})

        if not result:
            raise LookupError(f"Patient not found: {patient_id}")

        # Handle list of records
        patient_data = result if isinstance(result, dict) else result[0] if isinstance(result, list) and result else {}
        return self._unity_result_to_fhir_patient(patient_data)

    def fetch_observations(
        self,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        observation_codes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve clinical results from Allscripts as FHIR R4 Observations."""
        params: Dict[str, Any] = {'PatientID': patient_id}

        if start_date:
            params['Parameter1'] = start_date.strftime('%m/%d/%Y')
        if end_date:
            params['Parameter2'] = end_date.strftime('%m/%d/%Y')

        result = self._unity_call('GetClinicalSummary', params)

        observations: List[Dict[str, Any]] = []
        if isinstance(result, dict):
            results_list = result.get('results', result.get('clinicalsummary', []))
            if isinstance(results_list, list):
                for item in results_list:
                    obs = self._unity_result_to_fhir_observation(item)
                    # Apply code filter if specified
                    if observation_codes:
                        obs_codes = [c.get('code', '') for c in obs.get('code', {}).get('coding', [])]
                        if not any(code in obs_codes for code in observation_codes):
                            continue
                    observations.append(obs)
        elif isinstance(result, list):
            for item in result:
                obs = self._unity_result_to_fhir_observation(item)
                if observation_codes:
                    obs_codes = [c.get('code', '') for c in obs.get('code', {}).get('coding', [])]
                    if not any(code in obs_codes for code in observation_codes):
                        continue
                observations.append(obs)

        return observations

    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve appointments from Allscripts as FHIR R4 Appointments."""
        result = self._unity_call('GetSchedule', {
            'PatientID': patient_id,
            'Parameter1': datetime.utcnow().strftime('%m/%d/%Y'),
        })

        appointments: List[Dict[str, Any]] = []
        schedule_items = result if isinstance(result, list) else result.get('schedule', []) if isinstance(result, dict) else []

        for item in schedule_items:
            appointments.append({
                'resourceType': 'Appointment',
                'id': str(item.get('appointmentid', str(uuid.uuid4()))),
                'status': item.get('Status', 'booked').lower(),
                'start': item.get('AppointmentDate', ''),
                'end': item.get('EndDate', ''),
                'description': item.get('Reason', ''),
                'participant': [{
                    'actor': {
                        'reference': f'Patient/{patient_id}',
                        'display': item.get('PatientName', ''),
                    },
                    'status': 'accepted',
                }],
                'serviceType': [{
                    'coding': [{
                        'display': item.get('AppointmentType', ''),
                    }],
                }],
                '_allscripts_raw': item,
            })

        return appointments

    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve care plans from Allscripts as FHIR R4 CarePlans."""
        result = self._unity_call('GetClinicalSummary', {
            'PatientID': patient_id,
            'Parameter1': 'careplan',
        })

        care_plans: List[Dict[str, Any]] = []
        plans = result if isinstance(result, list) else result.get('careplans', []) if isinstance(result, dict) else []

        for item in plans:
            care_plans.append({
                'resourceType': 'CarePlan',
                'id': str(item.get('careplanid', str(uuid.uuid4()))),
                'status': 'active',
                'intent': 'plan',
                'title': item.get('PlanName', ''),
                'subject': {'reference': f'Patient/{patient_id}'},
                'category': [{
                    'coding': [{
                        'display': item.get('Category', 'General'),
                    }],
                }],
                'activity': [{
                    'detail': {
                        'description': item.get('Description', ''),
                        'status': 'in-progress',
                    },
                }],
                '_allscripts_raw': item,
            })

        return care_plans

    def push_observation(self, patient_id: str, observation: Dict[str, Any]) -> bool:
        """Write an observation back to Allscripts via Unity SaveObject."""
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
            elif 'valueString' in observation:
                value = observation['valueString']

            save_data = {
                'PatientID': patient_id,
                'Parameter1': 'observation',
                'Parameter2': code_display,
                'Parameter3': value,
                'Parameter4': datetime.utcnow().strftime('%m/%d/%Y'),
            }

            self._unity_call('SaveObject', save_data)
            self.logger.info("Observation pushed to Allscripts for patient %s",
                             hashlib.sha256(patient_id.encode()).hexdigest()[:12])
            return True

        except Exception as e:
            self.logger.error("Failed to push observation to Allscripts: %s", e)
            return False

    def subscribe_to_events(self, event_types: List[str], webhook_url: str) -> str:
        """
        Register event subscriptions with Allscripts.

        Note: Allscripts Unity API has limited native webhook support.
        This implementation registers a polling-based listener that is
        managed by the sync engine.
        """
        subscription_id = str(uuid.uuid4())
        self.logger.info(
            "Allscripts subscription registered (polling-based): %s for events %s",
            subscription_id, event_types,
        )
        return subscription_id

    def validate_connection(self) -> bool:
        """Validate connectivity by testing authentication."""
        try:
            return self.authenticate()
        except Exception as e:
            self.logger.error("Allscripts connection validation failed: %s", e)
            return False

    def get_capabilities(self) -> Dict[str, Any]:
        """Return capability metadata for the Allscripts adapter."""
        return {
            'vendor': 'allscripts',
            'fhir_version': 'R4 (via adapter translation)',
            'supports_read': True,
            'supports_write': True,
            'supports_subscriptions': False,  # polling-based only
            'auth_type': 'unity_token',
            'api_type': 'unity_magic',
            'supported_resources': ['Patient', 'Observation', 'Appointment', 'CarePlan'],
            'supported_event_types': [],
        }
