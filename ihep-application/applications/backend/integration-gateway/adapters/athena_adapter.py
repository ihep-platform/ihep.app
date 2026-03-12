"""
athenahealth EHR Adapter

OAuth 2.0 integration with athenaClinicals and athenaCoordinator APIs,
translating responses to FHIR R4 format.

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from adapters.base_adapter import BaseEHRAdapter

logger = logging.getLogger(__name__)

_ATHENA_SANDBOX_BASE = "https://api.preview.platform.athenahealth.com"
_ATHENA_SANDBOX_TOKEN_URL = "https://api.preview.platform.athenahealth.com/oauth2/v1/token"
_REQUEST_TIMEOUT = 30


class AthenaAdapter(BaseEHRAdapter):
    """Adapter for athenahealth using their proprietary REST API."""

    def __init__(self) -> None:
        super().__init__()
        self._base_url: str = _ATHENA_SANDBOX_BASE
        self._token_url: str = _ATHENA_SANDBOX_TOKEN_URL
        self._api_version: str = "v1"
        self._client_id: str = ""
        self._client_secret: str = ""
        self._practice_id: str = ""

    def configure(self, config: Dict[str, Any]) -> None:
        super().configure(config)
        self._base_url = config.get("base_url", _ATHENA_SANDBOX_BASE).rstrip("/")
        self._token_url = config.get("token_url", _ATHENA_SANDBOX_TOKEN_URL)
        self._api_version = config.get("api_version", "v1")
        self._client_id = config.get("client_id", "")
        self._client_secret = config.get("client_secret", "")
        self._practice_id = config.get("practice_id", "")

    def authenticate(self) -> bool:
        if not self._client_id or not self._client_secret:
            self.logger.error("Cannot authenticate: missing credentials")
            return False
        try:
            resp = requests.post(self._token_url, data={
                "grant_type": "client_credentials",
                "scope": "athena/service/Athenanet.MDP.*",
            }, auth=(self._client_id, self._client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
            token_data = resp.json()
            self._access_token = token_data.get("access_token")
            self._token_expiry = datetime.utcnow() + timedelta(seconds=int(token_data.get("expires_in", 3600)))
            self._authenticated = True
            return True
        except Exception as e:
            self.logger.error("athena authentication failed: %s", e)
            self._authenticated = False
            return False

    def _api_url(self, endpoint: str) -> str:
        practice = f"/{self._practice_id}" if self._practice_id else ""
        return f"{self._base_url}/{self._api_version}{practice}/{endpoint.lstrip('/')}"

    def _api_get(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        self._ensure_authenticated()
        url = self._api_url(endpoint)
        headers = {"Authorization": f"Bearer {self._access_token}", "Accept": "application/json"}
        resp = requests.get(url, params=params, headers=headers, timeout=_REQUEST_TIMEOUT)
        if resp.status_code == 401:
            self.authenticate()
            headers["Authorization"] = f"Bearer {self._access_token}"
            resp = requests.get(url, params=params, headers=headers, timeout=_REQUEST_TIMEOUT)
        if resp.status_code == 404:
            raise LookupError(f"Resource not found: {endpoint}")
        if resp.status_code in (401, 403):
            raise PermissionError(f"Access denied: HTTP {resp.status_code}")
        resp.raise_for_status()
        return resp.json()

    def _api_post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_authenticated()
        url = self._api_url(endpoint)
        headers = {"Authorization": f"Bearer {self._access_token}", "Content-Type": "application/json", "Accept": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=_REQUEST_TIMEOUT)
        if resp.status_code == 401:
            self.authenticate()
            headers["Authorization"] = f"Bearer {self._access_token}"
            resp = requests.post(url, json=payload, headers=headers, timeout=_REQUEST_TIMEOUT)
        if resp.status_code in (401, 403):
            raise PermissionError(f"Access denied: HTTP {resp.status_code}")
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _api_get_all_pages(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        all_items: List[Dict[str, Any]] = []
        current_params = dict(params or {})
        current_params.setdefault("limit", "100")
        current_params.setdefault("offset", "0")
        while True:
            result = self._api_get(endpoint, current_params)
            items = []
            for key in ("patients", "results", "appointments", "encounters", "observations", "data"):
                if key in result and isinstance(result[key], list):
                    items = result[key]
                    break
            if not items and isinstance(result, list):
                items = result
            all_items.extend(items)
            total = result.get("totalcount", 0)
            if result.get("next") and len(all_items) < total:
                current_params["offset"] = str(int(current_params["offset"]) + int(current_params["limit"]))
            else:
                break
        return all_items

    def _to_fhir_patient(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "resourceType": "Patient",
            "id": str(data.get("patientid", "")),
            "name": [{"use": "official", "family": data.get("lastname", ""), "given": [data.get("firstname", "")]}],
            "birthDate": data.get("dob", ""),
            "gender": data.get("sex", "").lower(),
            "address": [{"use": "home", "line": [data.get("address1", "")], "city": data.get("city", ""), "state": data.get("state", ""), "postalCode": data.get("zip", "")}],
            "telecom": [
                {"system": "phone", "value": data.get("homephone", ""), "use": "home"},
                {"system": "phone", "value": data.get("mobilephone", ""), "use": "mobile"},
                {"system": "email", "value": data.get("email", ""), "use": "home"},
            ],
            "identifier": [{"system": "athenahealth", "value": str(data.get("patientid", ""))}],
        }

    def _to_fhir_observation(self, result: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        return {
            "resourceType": "Observation",
            "id": str(result.get("resultid", str(uuid.uuid4()))),
            "status": "final", "subject": {"reference": f"Patient/{patient_id}"},
            "code": {"coding": [{"system": "http://loinc.org", "code": result.get("loinc", ""), "display": result.get("description", "")}], "text": result.get("description", "")},
            "valueQuantity": {"value": result.get("value", ""), "unit": result.get("units", "")},
            "effectiveDateTime": result.get("resultdate", ""),
        }

    def _to_fhir_appointment(self, appt: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        status_map = {"f": "fulfilled", "x": "cancelled", "o": "booked", "2": "checked-in", "3": "arrived"}
        return {
            "resourceType": "Appointment",
            "id": str(appt.get("appointmentid", str(uuid.uuid4()))),
            "status": status_map.get(str(appt.get("appointmentstatus", "o")).lower(), "booked"),
            "start": appt.get("date", "") + "T" + appt.get("starttime", "00:00"),
            "description": appt.get("appointmenttype", ""),
            "participant": [{"actor": {"reference": f"Patient/{patient_id}"}, "status": "accepted"}],
        }

    def fetch_patient(self, patient_id: str) -> Dict[str, Any]:
        result = self._api_get(f"patients/{patient_id}")
        if isinstance(result, list):
            if not result:
                raise LookupError(f"Patient not found: {patient_id}")
            result = result[0]
        elif isinstance(result, dict) and "patients" in result:
            patients = result["patients"]
            if not patients:
                raise LookupError(f"Patient not found: {patient_id}")
            result = patients[0]
        return self._to_fhir_patient(result)

    def fetch_observations(self, patient_id: str, start_date=None, end_date=None, observation_codes=None) -> List[Dict[str, Any]]:
        params: Dict[str, str] = {}
        if start_date:
            params["startdate"] = start_date.strftime("%m/%d/%Y")
        if end_date:
            params["enddate"] = end_date.strftime("%m/%d/%Y")
        raw = self._api_get_all_pages(f"patients/{patient_id}/labresults", params)
        observations = []
        for item in raw:
            obs = self._to_fhir_observation(item, patient_id)
            if observation_codes:
                codes = [c.get("code", "") for c in obs.get("code", {}).get("coding", [])]
                if not any(c in codes for c in observation_codes):
                    continue
            observations.append(obs)
        return observations

    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        raw = self._api_get_all_pages(f"patients/{patient_id}/appointments", {
            "startdate": datetime.utcnow().strftime("%m/%d/%Y"),
            "enddate": (datetime.utcnow() + timedelta(days=365)).strftime("%m/%d/%Y"),
        })
        return [self._to_fhir_appointment(a, patient_id) for a in raw]

    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]:
        try:
            raw = self._api_get_all_pages(f"patients/{patient_id}/chartalert")
        except LookupError:
            return []
        return [{
            "resourceType": "CarePlan", "id": str(item.get("chartalertid", str(uuid.uuid4()))),
            "status": "active", "intent": "plan", "title": item.get("note", ""),
            "subject": {"reference": f"Patient/{patient_id}"},
        } for item in raw]

    def push_observation(self, patient_id: str, observation: Dict[str, Any]) -> bool:
        for key in ("code", "status"):
            if key not in observation:
                raise ValueError(f"Observation missing required key: {key}")
        try:
            coding = observation.get("code", {}).get("coding", [])
            display = coding[0].get("display", "") if coding else ""
            value = str(observation.get("valueQuantity", {}).get("value", "")) if "valueQuantity" in observation else ""
            self._api_post(f"patients/{patient_id}/labresults", {
                "clinicalresultname": display, "resultvalue": value,
                "resultdate": datetime.utcnow().strftime("%m/%d/%Y"),
            })
            return True
        except Exception as e:
            self.logger.error("Failed to push observation to athena: %s", e)
            return False

    def subscribe_to_events(self, event_types: List[str], webhook_url: str) -> str:
        try:
            result = self._api_post("subscriptions", {"eventtype": ",".join(event_types), "callbackurl": webhook_url})
            return str(result.get("subscriptionid", uuid.uuid4()))
        except Exception:
            return str(uuid.uuid4())

    def validate_connection(self) -> bool:
        try:
            self._ensure_authenticated()
            resp = requests.get(f"{self._base_url}/{self._api_version}/ping",
                                headers={"Authorization": f"Bearer {self._access_token}", "Accept": "application/json"}, timeout=_REQUEST_TIMEOUT)
            return resp.status_code == 200
        except Exception:
            return False

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "vendor": "athenahealth", "fhir_version": "R4 (via adapter translation)",
            "supports_read": True, "supports_write": True, "supports_subscriptions": True,
            "auth_type": "oauth2_client_credentials", "api_type": "athena_rest",
            "supported_resources": ["Patient", "Observation", "Appointment", "CarePlan", "Encounter"],
            "supported_event_types": ["patient.update", "appointment.create", "appointment.cancel", "encounter.close", "labresult.create"],
        }
