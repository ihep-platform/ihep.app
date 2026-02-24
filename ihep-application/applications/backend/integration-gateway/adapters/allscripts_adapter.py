"""
Allscripts EHR Adapter

Unity API integration with FHIR R4 translation layer.

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from adapters.base_adapter import BaseEHRAdapter

logger = logging.getLogger(__name__)

_ALLSCRIPTS_UNITY_BASE = "https://tw171.unitysandbox.com/Unity/UnityService.svc"
_ALLSCRIPTS_TOKEN_URL = "https://tw171.unitysandbox.com/Unity/UnityService.svc/json/GetToken"
_REQUEST_TIMEOUT = 30


class AllscriptsAdapter(BaseEHRAdapter):
    """Adapter for Allscripts using the Unity API."""

    def __init__(self) -> None:
        super().__init__()
        self._unity_base_url: str = _ALLSCRIPTS_UNITY_BASE
        self._token_url: str = _ALLSCRIPTS_TOKEN_URL
        self._app_name: str = ""
        self._app_username: str = ""
        self._app_password: str = ""
        self._unity_token: Optional[str] = None

    def configure(self, config: Dict[str, Any]) -> None:
        super().configure(config)
        self._unity_base_url = config.get("base_url", _ALLSCRIPTS_UNITY_BASE).rstrip("/")
        self._token_url = config.get("token_url", _ALLSCRIPTS_TOKEN_URL)
        self._app_name = config.get("client_id", config.get("app_name", ""))
        self._app_password = config.get("client_secret", config.get("app_password", ""))
        self._app_username = config.get("app_username", "")

    def authenticate(self) -> bool:
        if not self._app_name or not self._app_password:
            self.logger.error("Cannot authenticate: missing app credentials")
            return False
        try:
            resp = requests.post(self._token_url, json={
                "Username": self._app_username, "Password": self._app_password,
            }, headers={"Content-Type": "application/json", "AppName": self._app_name}, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
            token_data = resp.json()
            if isinstance(token_data, str):
                self._unity_token = token_data
            elif isinstance(token_data, dict):
                self._unity_token = token_data.get("Token", token_data.get("token", ""))
            else:
                self._unity_token = str(token_data)
            if not self._unity_token:
                return False
            self._access_token = self._unity_token
            self._token_expiry = datetime.utcnow() + timedelta(hours=4)
            self._authenticated = True
            return True
        except Exception as e:
            self.logger.error("Allscripts authentication failed: %s", e)
            self._authenticated = False
            return False

    def _unity_call(self, action: str, parameters: Dict[str, Any]) -> Any:
        self._ensure_authenticated()
        url = f"{self._unity_base_url}/json/MagicJson"
        payload = {
            "Action": action, "AppUserID": self._app_username,
            "Appname": self._app_name, "Token": self._unity_token,
            "PatientID": parameters.get("PatientID", ""),
            "Parameter1": parameters.get("Parameter1", ""),
            "Parameter2": parameters.get("Parameter2", ""),
            "Parameter3": parameters.get("Parameter3", ""),
            "Parameter4": parameters.get("Parameter4", ""),
            "Parameter5": parameters.get("Parameter5", ""),
            "Parameter6": parameters.get("Parameter6", ""),
            "Data": parameters.get("Data", ""),
        }
        resp = requests.post(url, json=payload, headers={
            "Content-Type": "application/json", "AppName": self._app_name,
        }, timeout=_REQUEST_TIMEOUT)
        if resp.status_code == 401:
            self.authenticate()
            payload["Token"] = self._unity_token
            resp = requests.post(url, json=payload, headers={
                "Content-Type": "application/json", "AppName": self._app_name,
            }, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        result = resp.json()
        return result[0] if isinstance(result, list) and result else result

    def _to_fhir_patient(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "resourceType": "Patient",
            "id": str(data.get("patientid", "")),
            "name": [{"use": "official", "family": data.get("LastName", ""), "given": [data.get("FirstName", "")]}],
            "birthDate": data.get("dateofbirth", ""),
            "gender": data.get("sex", "").lower(),
            "address": [{"use": "home", "line": [data.get("Address1", "")], "city": data.get("City", ""), "state": data.get("State", ""), "postalCode": data.get("ZipCode", "")}],
            "telecom": [{"system": "phone", "value": data.get("HomePhone", ""), "use": "home"}],
        }

    def _to_fhir_observation(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "resourceType": "Observation",
            "id": str(result.get("resultid", str(uuid.uuid4()))),
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": result.get("LoincCode", ""), "display": result.get("ResultName", "")}], "text": result.get("ResultName", "")},
            "valueQuantity": {"value": result.get("Value", ""), "unit": result.get("Units", "")},
            "effectiveDateTime": result.get("ResultDate", ""),
        }

    def fetch_patient(self, patient_id: str) -> Dict[str, Any]:
        result = self._unity_call("GetPatient", {"PatientID": patient_id})
        if not result:
            raise LookupError(f"Patient not found: {patient_id}")
        data = result if isinstance(result, dict) else result[0] if isinstance(result, list) and result else {}
        return self._to_fhir_patient(data)

    def fetch_observations(self, patient_id: str, start_date=None, end_date=None, observation_codes=None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"PatientID": patient_id}
        if start_date:
            params["Parameter1"] = start_date.strftime("%m/%d/%Y")
        if end_date:
            params["Parameter2"] = end_date.strftime("%m/%d/%Y")
        result = self._unity_call("GetClinicalSummary", params)
        observations = []
        items = result.get("results", []) if isinstance(result, dict) else result if isinstance(result, list) else []
        for item in items:
            obs = self._to_fhir_observation(item)
            if observation_codes:
                codes = [c.get("code", "") for c in obs.get("code", {}).get("coding", [])]
                if not any(c in codes for c in observation_codes):
                    continue
            observations.append(obs)
        return observations

    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        result = self._unity_call("GetSchedule", {"PatientID": patient_id, "Parameter1": datetime.utcnow().strftime("%m/%d/%Y")})
        items = result if isinstance(result, list) else result.get("schedule", []) if isinstance(result, dict) else []
        return [{
            "resourceType": "Appointment", "id": str(item.get("appointmentid", str(uuid.uuid4()))),
            "status": item.get("Status", "booked").lower(),
            "start": item.get("AppointmentDate", ""), "description": item.get("Reason", ""),
            "participant": [{"actor": {"reference": f"Patient/{patient_id}"}, "status": "accepted"}],
        } for item in items]

    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]:
        result = self._unity_call("GetClinicalSummary", {"PatientID": patient_id, "Parameter1": "careplan"})
        items = result if isinstance(result, list) else result.get("careplans", []) if isinstance(result, dict) else []
        return [{
            "resourceType": "CarePlan", "id": str(item.get("careplanid", str(uuid.uuid4()))),
            "status": "active", "intent": "plan", "title": item.get("PlanName", ""),
            "subject": {"reference": f"Patient/{patient_id}"},
        } for item in items]

    def push_observation(self, patient_id: str, observation: Dict[str, Any]) -> bool:
        for key in ("code", "status"):
            if key not in observation:
                raise ValueError(f"Observation missing required key: {key}")
        try:
            coding = observation.get("code", {}).get("coding", [])
            display = coding[0].get("display", "") if coding else ""
            value = str(observation.get("valueQuantity", {}).get("value", "")) if "valueQuantity" in observation else observation.get("valueString", "")
            self._unity_call("SaveObject", {"PatientID": patient_id, "Parameter1": "observation", "Parameter2": display, "Parameter3": value, "Parameter4": datetime.utcnow().strftime("%m/%d/%Y")})
            return True
        except Exception as e:
            self.logger.error("Failed to push observation to Allscripts: %s", e)
            return False

    def subscribe_to_events(self, event_types: List[str], webhook_url: str) -> str:
        return str(uuid.uuid4())

    def validate_connection(self) -> bool:
        try:
            return self.authenticate()
        except Exception:
            return False

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "vendor": "allscripts", "fhir_version": "R4 (via adapter translation)",
            "supports_read": True, "supports_write": True, "supports_subscriptions": False,
            "auth_type": "unity_token", "api_type": "unity_magic",
            "supported_resources": ["Patient", "Observation", "Appointment", "CarePlan"],
        }
