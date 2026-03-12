"""
HL7 v2.x Legacy Adapter

Parses/generates HL7 v2.x messages (ADT, ORU, SIU) with FHIR R4 conversion
and TCP/MLLP transport for legacy EHR systems.

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import logging
import socket
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from adapters.base_adapter import BaseEHRAdapter

logger = logging.getLogger(__name__)

MLLP_START_BLOCK = b"\x0b"
MLLP_END_BLOCK = b"\x1c"
MLLP_CARRIAGE_RETURN = b"\x0d"
_REQUEST_TIMEOUT = 30


class HL7v2Adapter(BaseEHRAdapter):
    """Adapter for HL7 v2.x legacy EHR integrations via TCP/MLLP."""

    def __init__(self) -> None:
        super().__init__()
        self._mllp_host: str = ""
        self._mllp_port: int = 0
        self._sending_facility: str = "IHEP"
        self._sending_application: str = "IHEP_EHR_INTEGRATION"
        self._receiving_facility: str = ""
        self._receiving_application: str = ""
        self._hl7_version: str = "2.5.1"

    def configure(self, config: Dict[str, Any]) -> None:
        super().configure(config)
        self._mllp_host = config.get("mllp_host", config.get("base_url", ""))
        self._mllp_port = int(config.get("mllp_port", 2575))
        self._sending_facility = config.get("sending_facility", "IHEP")
        self._sending_application = config.get("sending_application", "IHEP_EHR_INTEGRATION")
        self._receiving_facility = config.get("receiving_facility", "")
        self._receiving_application = config.get("receiving_application", "")
        self._hl7_version = config.get("hl7_version", "2.5.1")

    def authenticate(self) -> bool:
        if not self._mllp_host:
            self._authenticated = True
            return True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(_REQUEST_TIMEOUT)
            sock.connect((self._mllp_host, self._mllp_port))
            sock.close()
            self._authenticated = True
            self._token_expiry = datetime.utcnow() + timedelta(hours=24)
            return True
        except (socket.error, OSError) as e:
            self.logger.error("MLLP connection failed to %s:%d: %s", self._mllp_host, self._mllp_port, e)
            self._authenticated = False
            return False

    def _mllp_send(self, message: str) -> str:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(_REQUEST_TIMEOUT)
        sock.connect((self._mllp_host, self._mllp_port))
        try:
            framed = MLLP_START_BLOCK + message.encode("utf-8") + MLLP_END_BLOCK + MLLP_CARRIAGE_RETURN
            sock.sendall(framed)
            data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                if MLLP_END_BLOCK in data:
                    break
            response = data.replace(MLLP_START_BLOCK, b"").replace(MLLP_END_BLOCK, b"").replace(MLLP_CARRIAGE_RETURN, b"")
            return response.decode("utf-8", errors="replace")
        finally:
            sock.close()

    def parse_hl7_message(self, raw_message: str) -> Dict[str, Any]:
        segments = raw_message.strip().split("\r")
        if not segments or len(segments) == 1:
            segments = raw_message.strip().split("\n")
        parsed: Dict[str, Any] = {"segments": {}, "message_type": "", "message_control_id": "", "z_segments": {}}
        for seg_str in segments:
            if not seg_str.strip():
                continue
            fields = seg_str.split("|")
            seg_type = fields[0].strip()
            if seg_type == "MSH":
                parsed["segments"]["MSH"] = self._parse_msh(fields)
                parsed["message_type"] = parsed["segments"]["MSH"].get("message_type", "")
                parsed["message_control_id"] = parsed["segments"]["MSH"].get("message_control_id", "")
            elif seg_type == "PID":
                parsed["segments"]["PID"] = self._parse_pid(fields)
            elif seg_type == "OBX":
                parsed["segments"].setdefault("OBX", [])
                parsed["segments"]["OBX"].append(self._parse_obx(fields))
            elif seg_type == "SCH":
                parsed["segments"]["SCH"] = self._parse_sch(fields)
            elif seg_type.startswith("Z"):
                parsed["z_segments"][seg_type] = {"raw": seg_str, "fields": fields[1:]}
        return parsed

    def _safe_field(self, fields: list, index: int, default: str = "") -> str:
        return fields[index] if index < len(fields) else default

    def _parse_msh(self, fields: list) -> Dict[str, str]:
        return {
            "sending_application": self._safe_field(fields, 2),
            "sending_facility": self._safe_field(fields, 3),
            "receiving_application": self._safe_field(fields, 4),
            "receiving_facility": self._safe_field(fields, 5),
            "datetime": self._safe_field(fields, 6),
            "message_type": self._safe_field(fields, 8),
            "message_control_id": self._safe_field(fields, 9),
            "version_id": self._safe_field(fields, 11),
        }

    def _parse_pid(self, fields: list) -> Dict[str, str]:
        name_field = self._safe_field(fields, 5)
        parts = name_field.split("^") if name_field else ["", ""]
        return {
            "patient_id": self._safe_field(fields, 2),
            "patient_id_list": self._safe_field(fields, 3),
            "family_name": parts[0] if parts else "",
            "given_name": parts[1] if len(parts) > 1 else "",
            "date_of_birth": self._safe_field(fields, 7),
            "sex": self._safe_field(fields, 8),
            "address": self._safe_field(fields, 11),
            "phone_home": self._safe_field(fields, 13),
        }

    def _parse_obx(self, fields: list) -> Dict[str, str]:
        return {
            "value_type": self._safe_field(fields, 2),
            "observation_identifier": self._safe_field(fields, 3),
            "observation_value": self._safe_field(fields, 5),
            "units": self._safe_field(fields, 6),
            "references_range": self._safe_field(fields, 7),
            "abnormal_flags": self._safe_field(fields, 8),
            "effective_datetime": self._safe_field(fields, 14),
        }

    def _parse_sch(self, fields: list) -> Dict[str, str]:
        return {
            "filler_appointment_id": self._safe_field(fields, 2),
            "appointment_reason": self._safe_field(fields, 7),
            "appointment_type": self._safe_field(fields, 8),
            "appointment_timing_quantity": self._safe_field(fields, 11),
        }

    def _parse_hl7_datetime(self, hl7_dt: str) -> str:
        if not hl7_dt:
            return ""
        hl7_dt = hl7_dt.strip()
        try:
            if len(hl7_dt) >= 14:
                return datetime.strptime(hl7_dt[:14], "%Y%m%d%H%M%S").strftime("%Y-%m-%dT%H:%M:%SZ")
            elif len(hl7_dt) >= 8:
                return datetime.strptime(hl7_dt[:8], "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            pass
        return hl7_dt

    def generate_ack(self, parsed_message: Dict[str, Any], ack_code: str = "AA", error_message: str = "") -> str:
        msh = parsed_message.get("segments", {}).get("MSH", {})
        now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        control_id = str(uuid.uuid4())[:20]
        lines = [
            f"MSH|^~\\&|{self._sending_application}|{self._sending_facility}|{msh.get('sending_application', '')}|{msh.get('sending_facility', '')}|{now}||ACK|{control_id}|P|{self._hl7_version}",
            f"MSA|{ack_code}|{msh.get('message_control_id', '')}|{error_message}",
        ]
        return "\r".join(lines)

    def hl7_to_fhir_patient(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        pid = parsed.get("segments", {}).get("PID", {})
        dob = pid.get("date_of_birth", "")
        if len(dob) >= 8:
            dob = f"{dob[:4]}-{dob[4:6]}-{dob[6:8]}"
        sex_map = {"M": "male", "F": "female", "O": "other", "U": "unknown"}
        addr_raw = pid.get("address", "")
        addr_parts = addr_raw.split("^") if addr_raw else []
        return {
            "resourceType": "Patient",
            "id": pid.get("patient_id_list", pid.get("patient_id", str(uuid.uuid4()))),
            "name": [{"use": "official", "family": pid.get("family_name", ""), "given": [pid.get("given_name", "")]}],
            "birthDate": dob,
            "gender": sex_map.get(pid.get("sex", "U").upper(), "unknown"),
            "address": [{"use": "home", "line": [addr_parts[0]] if addr_parts else [], "city": addr_parts[2] if len(addr_parts) > 2 else "", "state": addr_parts[3] if len(addr_parts) > 3 else "", "postalCode": addr_parts[4] if len(addr_parts) > 4 else ""}],
            "telecom": [{"system": "phone", "value": pid.get("phone_home", ""), "use": "home"}] if pid.get("phone_home") else [],
        }

    def hl7_to_fhir_observations(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        pid = parsed.get("segments", {}).get("PID", {})
        patient_id = pid.get("patient_id_list", pid.get("patient_id", ""))
        observations = []
        for obx in parsed.get("segments", {}).get("OBX", []):
            obs_parts = obx.get("observation_identifier", "").split("^")
            code = obs_parts[0] if obs_parts else ""
            display = obs_parts[1] if len(obs_parts) > 1 else ""
            obs: Dict[str, Any] = {
                "resourceType": "Observation", "id": str(uuid.uuid4()), "status": "final",
                "subject": {"reference": f"Patient/{patient_id}"},
                "code": {"coding": [{"system": "http://loinc.org", "code": code, "display": display}], "text": display or code},
                "effectiveDateTime": self._parse_hl7_datetime(obx.get("effective_datetime", "")),
            }
            if obx.get("value_type") == "NM":
                try:
                    obs["valueQuantity"] = {"value": float(obx.get("observation_value", "")), "unit": obx.get("units", "")}
                except ValueError:
                    obs["valueString"] = obx.get("observation_value", "")
            else:
                obs["valueString"] = obx.get("observation_value", "")
            observations.append(obs)
        return observations

    def fetch_patient(self, patient_id: str) -> Dict[str, Any]:
        if not self._mllp_host:
            raise NotImplementedError("HL7 v2.x adapter in receive-only mode")
        now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        control_id = str(uuid.uuid4())[:20]
        query = f"MSH|^~\\&|{self._sending_application}|{self._sending_facility}|{self._receiving_application}|{self._receiving_facility}|{now}||QBP^Q22|{control_id}|P|{self._hl7_version}\rQPD|IHE PIX Query|{control_id}|{patient_id}^^^&MRN\rRCP|I|1^RD"
        response = self._mllp_send(query)
        return self.hl7_to_fhir_patient(self.parse_hl7_message(response))

    def fetch_observations(self, patient_id: str, start_date=None, end_date=None, observation_codes=None) -> List[Dict[str, Any]]:
        raise NotImplementedError("HL7 v2.x observations arrive via inbound ORU^R01 messages")

    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("HL7 v2.x appointments arrive via inbound SIU messages")

    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("Care plans not supported in HL7 v2.x")

    def push_observation(self, patient_id: str, observation: Dict[str, Any]) -> bool:
        if not self._mllp_host:
            raise NotImplementedError("MLLP host not configured")
        for key in ("code", "status"):
            if key not in observation:
                raise ValueError(f"Observation missing required key: {key}")
        now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        control_id = str(uuid.uuid4())[:20]
        coding = observation.get("code", {}).get("coding", [{}])
        code = coding[0].get("code", "") if coding else ""
        display = coding[0].get("display", "") if coding else ""
        value = str(observation.get("valueQuantity", {}).get("value", "")) if "valueQuantity" in observation else observation.get("valueString", "")
        units = observation.get("valueQuantity", {}).get("unit", "") if "valueQuantity" in observation else ""
        value_type = "NM" if "valueQuantity" in observation else "ST"
        msg = f"MSH|^~\\&|{self._sending_application}|{self._sending_facility}|{self._receiving_application}|{self._receiving_facility}|{now}||ORU^R01|{control_id}|P|{self._hl7_version}\rPID|||{patient_id}^^^&MRN\rOBR|1||{control_id}|{code}^{display}^LN\rOBX|1|{value_type}|{code}^{display}^LN||{value}|{units}|||||F"
        try:
            response = self._mllp_send(msg)
            return "MSA|AA" in response or "MSA|CA" in response or not response.strip()
        except Exception as e:
            self.logger.error("Failed to push observation via HL7: %s", e)
            return False

    def subscribe_to_events(self, event_types: List[str], webhook_url: str) -> str:
        return str(uuid.uuid4())

    def validate_connection(self) -> bool:
        if not self._mllp_host:
            return True
        return self.authenticate()

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "vendor": "hl7v2", "fhir_version": "R4 (via adapter conversion)",
            "protocol": "HL7 v2.x / MLLP", "hl7_version": self._hl7_version,
            "supports_read": bool(self._mllp_host), "supports_write": bool(self._mllp_host),
            "supports_subscriptions": False, "supports_inbound_messages": True,
            "auth_type": "connection_level",
            "supported_message_types": ["ADT", "ORU", "SIU"],
            "supported_resources": ["Patient", "Observation", "Appointment"],
        }
