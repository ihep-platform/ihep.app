"""
HL7 v2.x Legacy Adapter

Provides parsing and generation of HL7 v2.x messages (ADT, ORU, SIU)
with conversion to/from FHIR R4 resources. Supports TCP/MLLP connectivity
for direct HL7 feeds and generates proper ACK/NAK responses.

This adapter is used for legacy EHR systems that have not yet adopted
FHIR APIs, as well as for receiving real-time feeds through Mirth Connect
channels that expose HL7 v2.x interfaces.

Reference:
- HL7 v2.x specification (http://www.hl7.org/)
- hl7apy library documentation
"""

import hashlib
import logging
import socket
import struct
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from adapters.base_adapter import BaseEHRAdapter

logger = logging.getLogger(__name__)

# MLLP framing characters
MLLP_START_BLOCK = b'\x0b'    # VT (vertical tab)
MLLP_END_BLOCK = b'\x1c'      # FS (file separator)
MLLP_CARRIAGE_RETURN = b'\x0d'  # CR

_REQUEST_TIMEOUT = 30  # seconds


class HL7v2Adapter(BaseEHRAdapter):
    """
    Adapter for HL7 v2.x legacy EHR integrations.

    Handles parsing of inbound HL7 v2.x messages (ADT^A01-A08, ORU^R01,
    SIU^S12-S17) and converts them to FHIR R4 resources. Also supports
    outbound message generation and TCP/MLLP transport.

    Custom Z-segments are preserved in the parsed output under the
    ``_z_segments`` key for downstream processing.
    """

    def __init__(self) -> None:
        super().__init__()
        self._mllp_host: str = ''
        self._mllp_port: int = 0
        self._sending_facility: str = 'IHEP'
        self._sending_application: str = 'IHEP_EHR_INTEGRATION'
        self._receiving_facility: str = ''
        self._receiving_application: str = ''
        self._socket: Optional[socket.socket] = None
        self._hl7_version: str = '2.5.1'

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Inject HL7 v2.x specific configuration.

        Expected config keys:
            mllp_host, mllp_port, sending_facility, sending_application,
            receiving_facility, receiving_application, hl7_version
        """
        super().configure(config)

        self._mllp_host = config.get('mllp_host', config.get('base_url', ''))
        self._mllp_port = int(config.get('mllp_port', 2575))
        self._sending_facility = config.get('sending_facility', 'IHEP')
        self._sending_application = config.get('sending_application', 'IHEP_EHR_INTEGRATION')
        self._receiving_facility = config.get('receiving_facility', '')
        self._receiving_application = config.get('receiving_application', '')
        self._hl7_version = config.get('hl7_version', '2.5.1')

    # ------------------------------------------------------------------
    # Authentication (HL7 v2 uses connection-level trust)
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """
        HL7 v2.x does not use token-based authentication.

        Authentication is handled at the transport level (e.g. VPN, TLS,
        IP whitelisting). This method validates that a TCP/MLLP connection
        can be established.

        Returns:
            True if the MLLP connection can be established.
        """
        if not self._mllp_host:
            self.logger.info("No MLLP host configured; operating in receive-only mode")
            self._authenticated = True
            return True

        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(_REQUEST_TIMEOUT)
            test_socket.connect((self._mllp_host, self._mllp_port))
            test_socket.close()
            self._authenticated = True
            self._token_expiry = datetime.utcnow() + timedelta(hours=24)
            self.logger.info("MLLP connection validated: %s:%d", self._mllp_host, self._mllp_port)
            return True
        except (socket.error, OSError) as e:
            self.logger.error("MLLP connection failed to %s:%d: %s", self._mllp_host, self._mllp_port, e)
            self._authenticated = False
            return False

    # ------------------------------------------------------------------
    # MLLP transport
    # ------------------------------------------------------------------

    def _mllp_connect(self) -> socket.socket:
        """Establish a TCP/MLLP connection."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(_REQUEST_TIMEOUT)
        sock.connect((self._mllp_host, self._mllp_port))
        return sock

    def _mllp_send(self, message: str) -> str:
        """
        Send an HL7 message over MLLP and return the response.

        Frames the message with MLLP start/end block characters,
        sends over TCP, and reads the response.

        Args:
            message: Raw HL7 v2.x message string.

        Returns:
            The response message (typically an ACK or NAK).
        """
        sock = self._mllp_connect()
        try:
            # Frame the message with MLLP envelope
            framed = MLLP_START_BLOCK + message.encode('utf-8') + MLLP_END_BLOCK + MLLP_CARRIAGE_RETURN
            sock.sendall(framed)

            # Read response
            response_data = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if MLLP_END_BLOCK in response_data:
                    break

            # Strip MLLP framing
            response = response_data.replace(MLLP_START_BLOCK, b'').replace(MLLP_END_BLOCK, b'').replace(MLLP_CARRIAGE_RETURN, b'')
            return response.decode('utf-8', errors='replace')

        finally:
            sock.close()

    # ------------------------------------------------------------------
    # HL7 v2.x message parsing
    # ------------------------------------------------------------------

    def parse_hl7_message(self, raw_message: str) -> Dict[str, Any]:
        """
        Parse a raw HL7 v2.x message into a structured dictionary.

        Uses segment-level parsing to extract MSH, PID, PV1, OBR, OBX,
        SCH, and custom Z-segments.

        Args:
            raw_message: The raw HL7 message string with segment delimiters.

        Returns:
            Dictionary with parsed segments and metadata.
        """
        segments = raw_message.strip().split('\r')
        if not segments:
            segments = raw_message.strip().split('\n')

        parsed: Dict[str, Any] = {
            'segments': {},
            'message_type': '',
            'message_control_id': '',
            'z_segments': {},
            'raw': raw_message,
        }

        for segment_str in segments:
            if not segment_str.strip():
                continue

            fields = segment_str.split('|')
            segment_type = fields[0].strip()

            if segment_type == 'MSH':
                parsed['segments']['MSH'] = self._parse_msh(fields)
                parsed['message_type'] = parsed['segments']['MSH'].get('message_type', '')
                parsed['message_control_id'] = parsed['segments']['MSH'].get('message_control_id', '')

            elif segment_type == 'PID':
                parsed['segments']['PID'] = self._parse_pid(fields)

            elif segment_type == 'PV1':
                parsed['segments']['PV1'] = self._parse_pv1(fields)

            elif segment_type == 'OBR':
                parsed['segments'].setdefault('OBR', [])
                parsed['segments']['OBR'].append(self._parse_obr(fields))

            elif segment_type == 'OBX':
                parsed['segments'].setdefault('OBX', [])
                parsed['segments']['OBX'].append(self._parse_obx(fields))

            elif segment_type == 'SCH':
                parsed['segments']['SCH'] = self._parse_sch(fields)

            elif segment_type.startswith('Z'):
                # Custom Z-segments
                parsed['z_segments'][segment_type] = {
                    'raw': segment_str,
                    'fields': fields[1:],
                }

        return parsed

    def _safe_field(self, fields: list, index: int, default: str = '') -> str:
        """Safely extract a field from an HL7 segment by index."""
        try:
            return fields[index] if index < len(fields) else default
        except (IndexError, TypeError):
            return default

    def _parse_msh(self, fields: list) -> Dict[str, str]:
        """Parse MSH (Message Header) segment."""
        # MSH has the field separator as field[1], so indices are offset
        return {
            'field_separator': '|',
            'encoding_characters': self._safe_field(fields, 1),
            'sending_application': self._safe_field(fields, 2),
            'sending_facility': self._safe_field(fields, 3),
            'receiving_application': self._safe_field(fields, 4),
            'receiving_facility': self._safe_field(fields, 5),
            'datetime': self._safe_field(fields, 6),
            'security': self._safe_field(fields, 7),
            'message_type': self._safe_field(fields, 8),
            'message_control_id': self._safe_field(fields, 9),
            'processing_id': self._safe_field(fields, 10),
            'version_id': self._safe_field(fields, 11),
        }

    def _parse_pid(self, fields: list) -> Dict[str, str]:
        """Parse PID (Patient Identification) segment."""
        # Extract name components from PID-5 (family^given^middle)
        name_field = self._safe_field(fields, 5)
        name_parts = name_field.split('^') if name_field else ['', '']

        return {
            'set_id': self._safe_field(fields, 1),
            'patient_id': self._safe_field(fields, 2),
            'patient_id_list': self._safe_field(fields, 3),
            'alternate_patient_id': self._safe_field(fields, 4),
            'patient_name': name_field,
            'family_name': name_parts[0] if len(name_parts) > 0 else '',
            'given_name': name_parts[1] if len(name_parts) > 1 else '',
            'middle_name': name_parts[2] if len(name_parts) > 2 else '',
            'date_of_birth': self._safe_field(fields, 7),
            'sex': self._safe_field(fields, 8),
            'race': self._safe_field(fields, 10),
            'address': self._safe_field(fields, 11),
            'phone_home': self._safe_field(fields, 13),
            'phone_business': self._safe_field(fields, 14),
            'language': self._safe_field(fields, 15),
            'marital_status': self._safe_field(fields, 16),
            'ssn': self._safe_field(fields, 19),
        }

    def _parse_pv1(self, fields: list) -> Dict[str, str]:
        """Parse PV1 (Patient Visit) segment."""
        return {
            'set_id': self._safe_field(fields, 1),
            'patient_class': self._safe_field(fields, 2),
            'assigned_location': self._safe_field(fields, 3),
            'admission_type': self._safe_field(fields, 4),
            'attending_doctor': self._safe_field(fields, 7),
            'referring_doctor': self._safe_field(fields, 8),
            'hospital_service': self._safe_field(fields, 10),
            'admit_datetime': self._safe_field(fields, 44),
            'discharge_datetime': self._safe_field(fields, 45),
        }

    def _parse_obr(self, fields: list) -> Dict[str, str]:
        """Parse OBR (Observation Request) segment."""
        return {
            'set_id': self._safe_field(fields, 1),
            'placer_order_number': self._safe_field(fields, 2),
            'filler_order_number': self._safe_field(fields, 3),
            'universal_service_id': self._safe_field(fields, 4),
            'observation_datetime': self._safe_field(fields, 7),
            'observation_end_datetime': self._safe_field(fields, 8),
            'ordering_provider': self._safe_field(fields, 16),
            'result_status': self._safe_field(fields, 25),
        }

    def _parse_obx(self, fields: list) -> Dict[str, str]:
        """Parse OBX (Observation/Result) segment."""
        return {
            'set_id': self._safe_field(fields, 1),
            'value_type': self._safe_field(fields, 2),
            'observation_identifier': self._safe_field(fields, 3),
            'observation_sub_id': self._safe_field(fields, 4),
            'observation_value': self._safe_field(fields, 5),
            'units': self._safe_field(fields, 6),
            'references_range': self._safe_field(fields, 7),
            'abnormal_flags': self._safe_field(fields, 8),
            'observation_result_status': self._safe_field(fields, 11),
            'effective_datetime': self._safe_field(fields, 14),
        }

    def _parse_sch(self, fields: list) -> Dict[str, str]:
        """Parse SCH (Scheduling) segment."""
        return {
            'placer_appointment_id': self._safe_field(fields, 1),
            'filler_appointment_id': self._safe_field(fields, 2),
            'event_reason': self._safe_field(fields, 6),
            'appointment_reason': self._safe_field(fields, 7),
            'appointment_type': self._safe_field(fields, 8),
            'appointment_duration': self._safe_field(fields, 9),
            'appointment_timing_quantity': self._safe_field(fields, 11),
            'placer_contact_person': self._safe_field(fields, 12),
            'filler_contact_person': self._safe_field(fields, 16),
        }

    # ------------------------------------------------------------------
    # ACK/NAK generation
    # ------------------------------------------------------------------

    def generate_ack(
        self, parsed_message: Dict[str, Any], ack_code: str = 'AA', error_message: str = ''
    ) -> str:
        """
        Generate an HL7 ACK (Acknowledgement) message.

        Args:
            parsed_message: The parsed inbound message dictionary.
            ack_code: ACK code - 'AA' (accept), 'AE' (error), 'AR' (reject).
            error_message: Optional error description for AE/AR responses.

        Returns:
            A formatted HL7 ACK message string.
        """
        msh = parsed_message.get('segments', {}).get('MSH', {})
        now = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        control_id = str(uuid.uuid4())[:20]

        ack_segments = [
            f"MSH|^~\\&|{self._sending_application}|{self._sending_facility}|"
            f"{msh.get('sending_application', '')}|{msh.get('sending_facility', '')}|"
            f"{now}||ACK|{control_id}|P|{self._hl7_version}",
            f"MSA|{ack_code}|{msh.get('message_control_id', '')}|"
            f"{error_message}",
        ]

        if ack_code != 'AA' and error_message:
            ack_segments.append(
                f"ERR|||{ack_code}|E|{error_message}"
            )

        return '\r'.join(ack_segments)

    # ------------------------------------------------------------------
    # FHIR R4 conversion
    # ------------------------------------------------------------------

    def hl7_to_fhir_patient(self, parsed_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert parsed HL7 PID segment to a FHIR R4 Patient resource.

        Args:
            parsed_message: Output from ``parse_hl7_message``.

        Returns:
            FHIR R4 Patient resource dictionary.
        """
        pid = parsed_message.get('segments', {}).get('PID', {})

        # Parse date of birth (HL7 format: YYYYMMDD)
        dob = pid.get('date_of_birth', '')
        if len(dob) >= 8:
            dob = f"{dob[:4]}-{dob[4:6]}-{dob[6:8]}"

        # Map HL7 sex codes to FHIR gender
        sex_map = {'M': 'male', 'F': 'female', 'O': 'other', 'U': 'unknown'}
        gender = sex_map.get(pid.get('sex', 'U').upper(), 'unknown')

        # Parse address (HL7 uses ^ delimiter: street^other^city^state^zip^country)
        address_raw = pid.get('address', '')
        addr_parts = address_raw.split('^') if address_raw else []

        patient: Dict[str, Any] = {
            'resourceType': 'Patient',
            'id': pid.get('patient_id_list', pid.get('patient_id', str(uuid.uuid4()))),
            'name': [{
                'use': 'official',
                'family': pid.get('family_name', ''),
                'given': [n for n in [pid.get('given_name', ''), pid.get('middle_name', '')] if n],
            }],
            'birthDate': dob,
            'gender': gender,
            'address': [{
                'use': 'home',
                'line': [addr_parts[0]] if len(addr_parts) > 0 else [],
                'city': addr_parts[2] if len(addr_parts) > 2 else '',
                'state': addr_parts[3] if len(addr_parts) > 3 else '',
                'postalCode': addr_parts[4] if len(addr_parts) > 4 else '',
                'country': addr_parts[5] if len(addr_parts) > 5 else '',
            }],
            'telecom': [],
        }

        if pid.get('phone_home'):
            patient['telecom'].append({
                'system': 'phone', 'value': pid['phone_home'], 'use': 'home',
            })
        if pid.get('phone_business'):
            patient['telecom'].append({
                'system': 'phone', 'value': pid['phone_business'], 'use': 'work',
            })

        # Preserve Z-segments
        if parsed_message.get('z_segments'):
            patient['_z_segments'] = parsed_message['z_segments']

        return patient

    def hl7_to_fhir_observations(self, parsed_message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert parsed HL7 OBX segments to FHIR R4 Observation resources.

        Typically used with ORU^R01 messages containing lab results.

        Args:
            parsed_message: Output from ``parse_hl7_message``.

        Returns:
            List of FHIR R4 Observation resource dictionaries.
        """
        pid = parsed_message.get('segments', {}).get('PID', {})
        patient_id = pid.get('patient_id_list', pid.get('patient_id', ''))
        obx_list = parsed_message.get('segments', {}).get('OBX', [])
        obr_list = parsed_message.get('segments', {}).get('OBR', [])

        observations: List[Dict[str, Any]] = []

        for obx in obx_list:
            # Parse observation identifier (format: code^display^system)
            obs_id_raw = obx.get('observation_identifier', '')
            obs_parts = obs_id_raw.split('^') if obs_id_raw else ['', '']

            code = obs_parts[0] if len(obs_parts) > 0 else ''
            display = obs_parts[1] if len(obs_parts) > 1 else ''
            system = obs_parts[2] if len(obs_parts) > 2 else 'http://loinc.org'

            # Parse value based on value_type
            value_type = obx.get('value_type', 'ST')
            value_raw = obx.get('observation_value', '')

            observation: Dict[str, Any] = {
                'resourceType': 'Observation',
                'id': str(uuid.uuid4()),
                'status': 'final',
                'subject': {'reference': f'Patient/{patient_id}'},
                'code': {
                    'coding': [{
                        'system': system if '/' in system else 'http://loinc.org',
                        'code': code,
                        'display': display,
                    }],
                    'text': display or code,
                },
                'effectiveDateTime': self._parse_hl7_datetime(
                    obx.get('effective_datetime', '')
                ),
            }

            # Set value based on type
            if value_type == 'NM':  # Numeric
                try:
                    observation['valueQuantity'] = {
                        'value': float(value_raw),
                        'unit': obx.get('units', ''),
                    }
                except ValueError:
                    observation['valueString'] = value_raw
            elif value_type == 'ST':  # String
                observation['valueString'] = value_raw
            elif value_type == 'CE':  # Coded entry
                val_parts = value_raw.split('^')
                observation['valueCodeableConcept'] = {
                    'coding': [{
                        'code': val_parts[0] if val_parts else '',
                        'display': val_parts[1] if len(val_parts) > 1 else '',
                    }],
                }
            else:
                observation['valueString'] = value_raw

            # Reference range
            if obx.get('references_range'):
                observation['referenceRange'] = [{'text': obx['references_range']}]

            # Abnormal flags
            if obx.get('abnormal_flags'):
                flag_map = {
                    'H': 'high', 'L': 'low', 'A': 'abnormal',
                    'HH': 'critically-high', 'LL': 'critically-low',
                    'N': 'normal',
                }
                observation['interpretation'] = [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                        'code': obx['abnormal_flags'],
                        'display': flag_map.get(obx['abnormal_flags'], obx['abnormal_flags']),
                    }],
                }]

            observations.append(observation)

        return observations

    def hl7_to_fhir_appointment(self, parsed_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert parsed HL7 SCH/SIU segment to a FHIR R4 Appointment resource.

        Args:
            parsed_message: Output from ``parse_hl7_message``.

        Returns:
            FHIR R4 Appointment resource dictionary.
        """
        pid = parsed_message.get('segments', {}).get('PID', {})
        sch = parsed_message.get('segments', {}).get('SCH', {})
        patient_id = pid.get('patient_id_list', pid.get('patient_id', ''))

        # Parse timing quantity (start^end)
        timing = sch.get('appointment_timing_quantity', '')
        timing_parts = timing.split('^') if timing else ['', '']

        return {
            'resourceType': 'Appointment',
            'id': sch.get('filler_appointment_id', str(uuid.uuid4())),
            'status': 'booked',
            'start': self._parse_hl7_datetime(timing_parts[0]) if timing_parts else '',
            'end': self._parse_hl7_datetime(timing_parts[1]) if len(timing_parts) > 1 else '',
            'description': sch.get('appointment_reason', ''),
            'serviceType': [{
                'coding': [{
                    'display': sch.get('appointment_type', ''),
                }],
            }],
            'participant': [{
                'actor': {
                    'reference': f'Patient/{patient_id}',
                    'display': f"{pid.get('given_name', '')} {pid.get('family_name', '')}".strip(),
                },
                'status': 'accepted',
            }],
        }

    def _parse_hl7_datetime(self, hl7_dt: str) -> str:
        """
        Convert an HL7 datetime string to ISO 8601 format.

        HL7 uses YYYYMMDDHHMMSS format; this converts to YYYY-MM-DDTHH:MM:SSZ.
        """
        if not hl7_dt:
            return ''

        hl7_dt = hl7_dt.strip()
        try:
            if len(hl7_dt) >= 14:
                dt = datetime.strptime(hl7_dt[:14], '%Y%m%d%H%M%S')
                return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            elif len(hl7_dt) >= 12:
                dt = datetime.strptime(hl7_dt[:12], '%Y%m%d%H%M')
                return dt.strftime('%Y-%m-%dT%H:%M:00Z')
            elif len(hl7_dt) >= 8:
                dt = datetime.strptime(hl7_dt[:8], '%Y%m%d')
                return dt.strftime('%Y-%m-%d')
            else:
                return hl7_dt
        except ValueError:
            return hl7_dt

    # ------------------------------------------------------------------
    # Public API - BaseEHRAdapter implementation
    # ------------------------------------------------------------------

    def fetch_patient(self, patient_id: str) -> Dict[str, Any]:
        """
        Fetch patient data by sending a QBP^Q22 query over MLLP.

        For HL7 v2.x, patient data is typically pushed (ADT messages)
        rather than pulled. This method sends a query if the remote
        system supports it, or raises NotImplementedError.
        """
        if not self._mllp_host:
            raise NotImplementedError(
                "HL7 v2.x adapter in receive-only mode; patient queries require MLLP host"
            )

        now = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        control_id = str(uuid.uuid4())[:20]

        query_msg = (
            f"MSH|^~\\&|{self._sending_application}|{self._sending_facility}|"
            f"{self._receiving_application}|{self._receiving_facility}|"
            f"{now}||QBP^Q22|{control_id}|P|{self._hl7_version}\r"
            f"QPD|IHE PIX Query|{control_id}|{patient_id}^^^&MRN\r"
            f"RCP|I|1^RD"
        )

        response = self._mllp_send(query_msg)
        parsed = self.parse_hl7_message(response)
        return self.hl7_to_fhir_patient(parsed)

    def fetch_observations(
        self,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        observation_codes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        HL7 v2.x observations are received via ORU^R01 messages.

        This method is not applicable for pull-based queries in most
        HL7 v2.x implementations. Observations arrive through inbound
        message processing.
        """
        raise NotImplementedError(
            "HL7 v2.x observations are received via inbound ORU^R01 messages, "
            "not queried. Use parse_hl7_message() + hl7_to_fhir_observations() instead."
        )

    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        HL7 v2.x appointments are received via SIU messages.

        Not applicable for pull-based queries.
        """
        raise NotImplementedError(
            "HL7 v2.x appointments are received via inbound SIU messages, "
            "not queried. Use parse_hl7_message() + hl7_to_fhir_appointment() instead."
        )

    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]:
        """Care plans are not available in HL7 v2.x."""
        raise NotImplementedError("Care plans are not supported in HL7 v2.x")

    def push_observation(self, patient_id: str, observation: Dict[str, Any]) -> bool:
        """
        Send an ORU^R01 message with an observation to the remote system.

        Converts the FHIR Observation to HL7 v2.x format and transmits
        via MLLP.
        """
        if not self._mllp_host:
            raise NotImplementedError("MLLP host not configured; cannot push observations")

        for key in ('code', 'status'):
            if key not in observation:
                raise ValueError(f"Observation missing required key: {key}")

        now = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        control_id = str(uuid.uuid4())[:20]

        # Extract observation details
        coding = observation.get('code', {}).get('coding', [{}])
        code = coding[0].get('code', '') if coding else ''
        display = coding[0].get('display', '') if coding else ''

        value = ''
        units = ''
        value_type = 'ST'
        if 'valueQuantity' in observation:
            value = str(observation['valueQuantity'].get('value', ''))
            units = observation['valueQuantity'].get('unit', '')
            value_type = 'NM'
        elif 'valueString' in observation:
            value = observation['valueString']

        oru_msg = (
            f"MSH|^~\\&|{self._sending_application}|{self._sending_facility}|"
            f"{self._receiving_application}|{self._receiving_facility}|"
            f"{now}||ORU^R01|{control_id}|P|{self._hl7_version}\r"
            f"PID|||{patient_id}^^^&MRN\r"
            f"OBR|1||{control_id}|{code}^{display}^LN\r"
            f"OBX|1|{value_type}|{code}^{display}^LN||{value}|{units}|||||F"
        )

        try:
            response = self._mllp_send(oru_msg)
            parsed_response = self.parse_hl7_message(response)
            msa = parsed_response.get('segments', {}).get('MSA', {})

            # Check if response is empty (possible with some systems)
            if not response.strip():
                self.logger.warning("Empty ACK response from MLLP host")
                return True  # Assume success for fire-and-forget systems

            # Look for ACK in the response
            if 'MSA|AA' in response or 'MSA|CA' in response:
                self.logger.info("Observation pushed successfully via HL7 v2.x")
                return True

            self.logger.warning("Observation push received non-AA ACK: %s", response[:200])
            return False

        except Exception as e:
            self.logger.error("Failed to push observation via HL7: %s", e)
            return False

    def subscribe_to_events(self, event_types: List[str], webhook_url: str) -> str:
        """
        HL7 v2.x does not support webhook subscriptions.

        Event delivery is managed by the sending system's interface engine
        (e.g. Mirth Connect). Returns a tracking ID for the subscription
        configuration.
        """
        subscription_id = str(uuid.uuid4())
        self.logger.info(
            "HL7 v2.x subscription registered (managed by Mirth): %s for events %s",
            subscription_id, event_types,
        )
        return subscription_id

    def validate_connection(self) -> bool:
        """Validate MLLP connectivity."""
        if not self._mllp_host:
            self.logger.info("No MLLP host configured; receive-only mode is valid")
            return True
        return self.authenticate()

    def get_capabilities(self) -> Dict[str, Any]:
        """Return capability metadata for the HL7 v2.x adapter."""
        return {
            'vendor': 'hl7v2',
            'fhir_version': 'R4 (via adapter conversion)',
            'protocol': 'HL7 v2.x / MLLP',
            'hl7_version': self._hl7_version,
            'supports_read': bool(self._mllp_host),
            'supports_write': bool(self._mllp_host),
            'supports_subscriptions': False,
            'supports_inbound_messages': True,
            'auth_type': 'connection_level',
            'supported_message_types': ['ADT', 'ORU', 'SIU'],
            'supported_resources': ['Patient', 'Observation', 'Appointment'],
            'supported_event_types': [
                'ADT^A01', 'ADT^A02', 'ADT^A03', 'ADT^A04',
                'ADT^A08', 'ORU^R01', 'SIU^S12', 'SIU^S14', 'SIU^S15',
            ],
            'supports_z_segments': True,
        }
