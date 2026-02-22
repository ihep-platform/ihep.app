"""
Allscripts Unity API to IHEP Canonical Format Mapper
=============================================================================
Transforms Allscripts Unity API responses into the IHEP canonical FHIR R4
resource format.

Handles Allscripts-specific conventions:
  - Allscripts Unity API proprietary response structures (non-standard FHIR)
  - Allscripts internal patient identifiers and chart numbers
  - Non-standard field names and nested structures in Unity API
  - Allscripts-specific code systems and value sets
  - GetPatient, GetResults, and GetSchedule Unity API actions

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
=============================================================================
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Allscripts Unity API field name mappings
# The Unity API returns data in proprietary structures that differ from FHIR.
# These maps translate Unity field names to FHIR R4 equivalents.

UNITY_PATIENT_FIELD_MAP = {
    "patientid": "id",
    "PatientID": "id",
    "firstname": "given",
    "FirstName": "given",
    "middlename": "middle",
    "MiddleName": "middle",
    "lastname": "family",
    "LastName": "family",
    "dateofbirth": "birthDate",
    "DateOfBirth": "birthDate",
    "DOB": "birthDate",
    "sex": "gender",
    "Sex": "gender",
    "Gender": "gender",
    "mrn": "mrn",
    "MRN": "mrn",
    "ChartNumber": "mrn",
    "chartnumber": "mrn",
    "SSN": "ssn",
    "ssn": "ssn",
}

UNITY_GENDER_MAP = {
    "M": "male",
    "m": "male",
    "Male": "male",
    "male": "male",
    "F": "female",
    "f": "female",
    "Female": "female",
    "female": "female",
    "O": "other",
    "Other": "other",
    "other": "other",
    "U": "unknown",
    "Unknown": "unknown",
    "unknown": "unknown",
    "Undifferentiated": "other",
}

UNITY_OBSERVATION_STATUS_MAP = {
    "Final": "final",
    "final": "final",
    "F": "final",
    "Preliminary": "preliminary",
    "preliminary": "preliminary",
    "P": "preliminary",
    "Corrected": "corrected",
    "corrected": "corrected",
    "C": "corrected",
    "Cancelled": "cancelled",
    "cancelled": "cancelled",
    "X": "cancelled",
    "In Progress": "registered",
    "Pending": "registered",
}

UNITY_APPOINTMENT_STATUS_MAP = {
    "Scheduled": "booked",
    "scheduled": "booked",
    "Confirmed": "booked",
    "confirmed": "booked",
    "Checked In": "checked-in",
    "checked-in": "checked-in",
    "Arrived": "arrived",
    "arrived": "arrived",
    "Completed": "fulfilled",
    "completed": "fulfilled",
    "Cancelled": "cancelled",
    "cancelled": "cancelled",
    "No Show": "noshow",
    "noshow": "noshow",
    "Pending": "pending",
    "pending": "pending",
}

MAPPING_VERSION = "1.0.0"


class AllscriptsToIHEPMapper:
    """Maps Allscripts Unity API responses to IHEP canonical FHIR R4 format.

    The Allscripts Unity API uses a proprietary response format that differs
    significantly from standard FHIR. This mapper handles the translation
    of patient (GetPatient), observation (GetResults), and appointment
    (GetSchedule) responses into the IHEP canonical format.
    """

    def __init__(self, source_system_id: str = "allscripts"):
        """Initialize the Allscripts mapper.

        Args:
            source_system_id: Identifier for the source Allscripts system instance.
        """
        self.source_system_id = source_system_id
        self.mapping_version = MAPPING_VERSION
        logger.info(
            "AllscriptsToIHEPMapper initialized for source system: %s",
            source_system_id,
        )

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def _get_nested(data: Dict, *keys: str, default: Any = None) -> Any:
        """Safely extract a nested value from a dictionary.

        Handles the inconsistent nesting patterns in Allscripts Unity responses.

        Args:
            data: Source dictionary.
            *keys: Sequence of keys to traverse.
            default: Default value if the path does not exist.

        Returns:
            The value at the nested path, or the default.
        """
        current = data
        for key in keys:
            if isinstance(current, dict):
                # Try exact key first, then case-insensitive lookup
                if key in current:
                    current = current[key]
                else:
                    found = False
                    for k in current:
                        if k.lower() == key.lower():
                            current = current[k]
                            found = True
                            break
                    if not found:
                        return default
            elif isinstance(current, list) and current:
                current = current[0]
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            else:
                return default
        return current

    @staticmethod
    def _parse_allscripts_date(date_str: Optional[str]) -> Optional[str]:
        """Parse Allscripts date formats into ISO 8601.

        Allscripts returns dates in various formats:
        - MM/DD/YYYY
        - MM/DD/YYYY HH:MM:SS
        - YYYY-MM-DD
        - YYYY-MM-DDTHH:MM:SS

        Returns:
            ISO 8601 date string or None if parsing fails.
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        # Already in ISO format
        if "T" in date_str or (len(date_str) == 10 and date_str[4] == "-"):
            return date_str

        date_formats = [
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %I:%M:%S %p",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y%m%d",
            "%Y%m%d%H%M%S",
        ]

        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                if ":" in date_str or len(date_str) > 10:
                    return parsed.isoformat()
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.warning("Failed to parse Allscripts date: %s", date_str)
        return date_str

    # -------------------------------------------------------------------------
    # Patient Mapping
    # -------------------------------------------------------------------------

    def map_patient(self, allscripts_patient: Dict[str, Any]) -> Dict[str, Any]:
        """Map an Allscripts Unity GetPatient response to IHEP canonical format.

        The Unity GetPatient response uses proprietary field names and
        structures. This method extracts patient demographics, identifiers,
        and contact information from the non-standard format.

        Args:
            allscripts_patient: Raw Allscripts Unity API patient response.

        Returns:
            IHEP canonical Patient resource dictionary.

        Raises:
            ValueError: If required fields cannot be extracted.
        """
        if not allscripts_patient:
            raise ValueError("Allscripts patient data cannot be empty")

        ihep_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Extract the patient data -- Unity may nest it under different keys
        patient_data = allscripts_patient
        if "getpatientinfo" in {k.lower() for k in allscripts_patient}:
            patient_data = self._get_nested(
                allscripts_patient, "getpatientinfo", default=allscripts_patient
            )
        elif "PatientInfo" in allscripts_patient:
            patient_data = allscripts_patient["PatientInfo"]

        # Handle list responses (Unity sometimes returns arrays)
        if isinstance(patient_data, list):
            if not patient_data:
                raise ValueError("Allscripts patient data list is empty")
            patient_data = patient_data[0]

        allscripts_id = str(
            self._get_nested(patient_data, "patientid", default="")
            or self._get_nested(patient_data, "PatientID", default="")
            or self._get_nested(patient_data, "ID", default="")
        )

        logger.debug(
            "Mapping Allscripts Patient %s -> IHEP Patient %s",
            allscripts_id,
            ihep_id,
        )

        ihep_patient: Dict[str, Any] = {
            "resourceType": "Patient",
            "id": ihep_id,
            "meta": {
                "source": f"urn:ehr:allscripts:{self.source_system_id}",
                "lastUpdated": now,
                "versionId": "1",
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient",
                    "https://ihep.app/fhir/StructureDefinition/ihep-patient",
                ],
            },
            "active": True,
        }

        # Map identifiers
        ihep_patient["identifier"] = self._map_patient_identifiers(
            patient_data, allscripts_id
        )

        # Map name
        ihep_patient["name"] = self._map_patient_name(patient_data)

        # Birth date (required)
        birth_date_raw = (
            self._get_nested(patient_data, "dateofbirth")
            or self._get_nested(patient_data, "DateOfBirth")
            or self._get_nested(patient_data, "DOB")
        )
        birth_date = self._parse_allscripts_date(birth_date_raw)
        if not birth_date:
            raise ValueError(
                "Patient birthDate is required but missing from Allscripts data"
            )
        # Ensure date-only format for birthDate
        ihep_patient["birthDate"] = birth_date[:10]

        # Gender (required)
        gender_raw = (
            self._get_nested(patient_data, "sex")
            or self._get_nested(patient_data, "Sex")
            or self._get_nested(patient_data, "Gender")
            or self._get_nested(patient_data, "gender")
        )
        if not gender_raw:
            raise ValueError(
                "Patient gender is required but missing from Allscripts data"
            )
        ihep_patient["gender"] = UNITY_GENDER_MAP.get(
            str(gender_raw).strip(), "unknown"
        )

        # Address (optional)
        address = self._map_patient_address(patient_data)
        if address:
            ihep_patient["address"] = [address]

        # Telecom (optional)
        telecoms = self._map_patient_telecoms(patient_data)
        if telecoms:
            ihep_patient["telecom"] = telecoms

        # IHEP extensions
        ihep_patient["extension"] = [
            {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-consent-status",
                "valueCode": "pending",
            },
            {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-data-sharing-preferences",
                "extension": [
                    {"url": "share-with-providers", "valueBoolean": True},
                    {"url": "share-with-researchers", "valueBoolean": False},
                    {"url": "share-with-payers", "valueBoolean": False},
                    {"url": "share-demographics", "valueBoolean": True},
                    {"url": "share-lab-results", "valueBoolean": True},
                    {"url": "share-medications", "valueBoolean": True},
                    {"url": "share-diagnoses", "valueBoolean": True},
                    {"url": "share-mental-health", "valueBoolean": False},
                    {"url": "share-substance-use", "valueBoolean": False},
                    {"url": "share-hiv-status", "valueBoolean": False},
                ],
            },
        ]

        logger.info(
            "Successfully mapped Allscripts Patient %s -> IHEP Patient %s",
            allscripts_id,
            ihep_id,
        )
        return ihep_patient

    def _map_patient_identifiers(
        self, patient_data: Dict, allscripts_id: str
    ) -> List[Dict]:
        """Extract and map identifiers from Allscripts Unity response."""
        identifiers = []

        # IHEP platform identifier
        identifiers.append(
            {
                "system": "https://ihep.app/fhir/sid/ihep-id",
                "value": str(uuid.uuid4()),
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PI",
                            "display": "Patient Internal Identifier",
                        }
                    ]
                },
                "use": "official",
            }
        )

        # MRN / Chart Number
        mrn = (
            self._get_nested(patient_data, "MRN")
            or self._get_nested(patient_data, "mrn")
            or self._get_nested(patient_data, "ChartNumber")
            or self._get_nested(patient_data, "chartnumber")
        )
        if mrn:
            identifiers.append(
                {
                    "system": f"urn:ehr:allscripts:{self.source_system_id}:mrn",
                    "value": str(mrn),
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                                "display": "Medical Record Number",
                            }
                        ]
                    },
                    "use": "usual",
                }
            )

        # SSN (if present -- store last 4 only for safety)
        ssn = self._get_nested(patient_data, "SSN") or self._get_nested(
            patient_data, "ssn"
        )
        if ssn and len(str(ssn)) >= 4:
            identifiers.append(
                {
                    "system": "http://hl7.org/fhir/sid/us-ssn",
                    "value": str(ssn)[-4:],
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "SS",
                                "display": "Social Security Number (last 4)",
                            }
                        ]
                    },
                    "use": "official",
                }
            )

        # Allscripts internal patient ID cross-reference
        if allscripts_id:
            identifiers.append(
                {
                    "system": f"urn:ehr:allscripts:{self.source_system_id}:patient-id",
                    "value": allscripts_id,
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "PI",
                                "display": "Allscripts Patient ID",
                            }
                        ]
                    },
                    "use": "secondary",
                }
            )

        return identifiers

    def _map_patient_name(self, patient_data: Dict) -> List[Dict]:
        """Extract and map patient name from Allscripts Unity response.

        Unity returns name components as flat fields (FirstName, LastName, etc.)
        rather than the FHIR HumanName structure.
        """
        first_name = str(
            self._get_nested(patient_data, "FirstName")
            or self._get_nested(patient_data, "firstname")
            or ""
        ).strip()

        middle_name = str(
            self._get_nested(patient_data, "MiddleName")
            or self._get_nested(patient_data, "middlename")
            or ""
        ).strip()

        last_name = str(
            self._get_nested(patient_data, "LastName")
            or self._get_nested(patient_data, "lastname")
            or ""
        ).strip()

        prefix = str(
            self._get_nested(patient_data, "Prefix")
            or self._get_nested(patient_data, "Title")
            or ""
        ).strip()

        suffix = str(
            self._get_nested(patient_data, "Suffix") or ""
        ).strip()

        if not last_name and not first_name:
            # Try the full name field
            full_name = str(
                self._get_nested(patient_data, "PatientName")
                or self._get_nested(patient_data, "Name")
                or ""
            ).strip()

            if not full_name:
                raise ValueError("Patient name is required but missing")

            # Parse "Last, First Middle" or "First Last" format
            if "," in full_name:
                parts = full_name.split(",", 1)
                last_name = parts[0].strip()
                given_parts = parts[1].strip().split()
                first_name = given_parts[0] if given_parts else ""
                middle_name = " ".join(given_parts[1:]) if len(given_parts) > 1 else ""
            else:
                parts = full_name.split()
                if len(parts) >= 2:
                    first_name = parts[0]
                    last_name = parts[-1]
                    middle_name = " ".join(parts[1:-1]) if len(parts) > 2 else ""
                else:
                    last_name = full_name

        given = [first_name] if first_name else []
        if middle_name:
            given.append(middle_name)

        name_entry: Dict[str, Any] = {
            "use": "official",
            "family": last_name,
            "given": given if given else [last_name],
        }

        if prefix:
            name_entry["prefix"] = [prefix]
        if suffix:
            name_entry["suffix"] = [suffix]

        name_entry["text"] = " ".join(
            filter(None, [prefix, first_name, middle_name, last_name, suffix])
        )

        return [name_entry]

    def _map_patient_address(self, patient_data: Dict) -> Optional[Dict]:
        """Extract and map address from Allscripts Unity flat fields."""
        line1 = str(
            self._get_nested(patient_data, "Address1")
            or self._get_nested(patient_data, "address1")
            or self._get_nested(patient_data, "AddressLine1")
            or ""
        ).strip()

        line2 = str(
            self._get_nested(patient_data, "Address2")
            or self._get_nested(patient_data, "address2")
            or self._get_nested(patient_data, "AddressLine2")
            or ""
        ).strip()

        city = str(
            self._get_nested(patient_data, "City")
            or self._get_nested(patient_data, "city")
            or ""
        ).strip()

        state = str(
            self._get_nested(patient_data, "State")
            or self._get_nested(patient_data, "state")
            or ""
        ).strip()

        postal_code = str(
            self._get_nested(patient_data, "ZipCode")
            or self._get_nested(patient_data, "Zip")
            or self._get_nested(patient_data, "zipcode")
            or self._get_nested(patient_data, "PostalCode")
            or ""
        ).strip()

        if not any([line1, city, state, postal_code]):
            return None

        address: Dict[str, Any] = {
            "use": "home",
            "type": "physical",
            "country": "US",
        }

        lines = [line1]
        if line2:
            lines.append(line2)
        address["line"] = [l for l in lines if l]

        if city:
            address["city"] = city
        if state:
            address["state"] = state
        if postal_code:
            address["postalCode"] = postal_code

        return address

    def _map_patient_telecoms(self, patient_data: Dict) -> List[Dict]:
        """Extract and map telecom entries from Allscripts Unity flat fields."""
        telecoms = []

        # Home phone
        home_phone = (
            self._get_nested(patient_data, "HomePhone")
            or self._get_nested(patient_data, "homephone")
            or self._get_nested(patient_data, "Phone")
        )
        if home_phone:
            telecoms.append(
                {"system": "phone", "value": str(home_phone), "use": "home", "rank": 1}
            )

        # Work phone
        work_phone = (
            self._get_nested(patient_data, "WorkPhone")
            or self._get_nested(patient_data, "workphone")
        )
        if work_phone:
            telecoms.append(
                {"system": "phone", "value": str(work_phone), "use": "work", "rank": 3}
            )

        # Mobile phone
        mobile_phone = (
            self._get_nested(patient_data, "MobilePhone")
            or self._get_nested(patient_data, "CellPhone")
            or self._get_nested(patient_data, "cellphone")
        )
        if mobile_phone:
            telecoms.append(
                {"system": "phone", "value": str(mobile_phone), "use": "mobile", "rank": 2}
            )

        # Email
        email = (
            self._get_nested(patient_data, "Email")
            or self._get_nested(patient_data, "email")
            or self._get_nested(patient_data, "EmailAddress")
        )
        if email:
            telecoms.append(
                {"system": "email", "value": str(email), "use": "home", "rank": 1}
            )

        return telecoms

    # -------------------------------------------------------------------------
    # Observation Mapping
    # -------------------------------------------------------------------------

    def map_observation(
        self, allscripts_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map an Allscripts Unity GetResults response to IHEP Observation.

        Unity GetResults returns lab results in a proprietary flat structure
        with fields like ResultName, ResultValue, Units, NormalRange, etc.

        Args:
            allscripts_result: Raw Allscripts Unity result record.

        Returns:
            IHEP canonical Observation resource dictionary.

        Raises:
            ValueError: If required fields cannot be extracted.
        """
        if not allscripts_result:
            raise ValueError("Allscripts result data cannot be empty")

        ihep_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Extract result data -- Unity may nest under different keys
        result_data = allscripts_result
        if isinstance(result_data, list):
            if not result_data:
                raise ValueError("Allscripts result data list is empty")
            result_data = result_data[0]

        allscripts_id = str(
            self._get_nested(result_data, "ResultID")
            or self._get_nested(result_data, "resultid")
            or self._get_nested(result_data, "OrderID")
            or ""
        )

        logger.debug(
            "Mapping Allscripts Result %s -> IHEP Observation %s",
            allscripts_id,
            ihep_id,
        )

        ihep_obs: Dict[str, Any] = {
            "resourceType": "Observation",
            "id": ihep_id,
            "meta": {
                "source": f"urn:ehr:allscripts:{self.source_system_id}",
                "lastUpdated": now,
                "versionId": "1",
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab",
                    "https://ihep.app/fhir/StructureDefinition/ihep-observation",
                ],
            },
        }

        # Status
        status_raw = (
            self._get_nested(result_data, "ResultStatus")
            or self._get_nested(result_data, "Status")
            or "Final"
        )
        ihep_obs["status"] = UNITY_OBSERVATION_STATUS_MAP.get(
            str(status_raw).strip(), "final"
        )

        # Category -- determine from order type or default to laboratory
        order_type = (
            self._get_nested(result_data, "OrderType")
            or self._get_nested(result_data, "Category")
            or "Lab"
        )
        category_code = "laboratory"
        order_type_lower = str(order_type).lower()
        if "vital" in order_type_lower:
            category_code = "vital-signs"
        elif "imaging" in order_type_lower or "radiology" in order_type_lower:
            category_code = "imaging"

        ihep_obs["category"] = [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": category_code,
                        "display": category_code.replace("-", " ").title(),
                    }
                ]
            }
        ]

        # Code -- map result name to LOINC if available
        result_name = (
            self._get_nested(result_data, "ResultName")
            or self._get_nested(result_data, "TestName")
            or self._get_nested(result_data, "ObservationName")
        )
        loinc_code = (
            self._get_nested(result_data, "LOINC")
            or self._get_nested(result_data, "LoincCode")
            or self._get_nested(result_data, "LOINCCode")
        )

        if not result_name and not loinc_code:
            raise ValueError("Observation code (ResultName or LOINC) is required")

        code_entry: Dict[str, Any] = {"coding": []}
        if loinc_code:
            code_entry["coding"].append(
                {
                    "system": "http://loinc.org",
                    "code": str(loinc_code),
                    "display": str(result_name or ""),
                }
            )
        if result_name:
            code_entry["text"] = str(result_name)
            # Add Allscripts internal code if no LOINC
            if not loinc_code:
                internal_code = (
                    self._get_nested(result_data, "TestCode")
                    or self._get_nested(result_data, "ObservationCode")
                    or ""
                )
                code_entry["coding"].append(
                    {
                        "system": f"urn:ehr:allscripts:{self.source_system_id}:test-code",
                        "code": str(internal_code) if internal_code else str(result_name),
                        "display": str(result_name),
                    }
                )

        ihep_obs["code"] = code_entry

        # Subject -- extract patient reference
        patient_id = (
            self._get_nested(result_data, "PatientID")
            or self._get_nested(result_data, "patientid")
            or ""
        )
        ihep_obs["subject"] = {
            "reference": f"Patient/{patient_id}" if patient_id else "Patient/unknown",
        }

        # Effective date/time
        result_date = (
            self._get_nested(result_data, "ResultDate")
            or self._get_nested(result_data, "ObservationDate")
            or self._get_nested(result_data, "CollectionDate")
        )
        effective_dt = self._parse_allscripts_date(str(result_date) if result_date else None)
        if effective_dt:
            ihep_obs["effectiveDateTime"] = effective_dt

        # Issued date
        issued_date = self._get_nested(result_data, "VerifiedDate") or self._get_nested(
            result_data, "ReportDate"
        )
        issued_dt = self._parse_allscripts_date(str(issued_date) if issued_date else None)
        if issued_dt:
            ihep_obs["issued"] = issued_dt

        # Value -- handle different Unity value formats
        self._map_result_value(result_data, ihep_obs)

        # Reference range
        normal_range = (
            self._get_nested(result_data, "NormalRange")
            or self._get_nested(result_data, "ReferenceRange")
            or self._get_nested(result_data, "NormalLow")
        )
        if normal_range:
            ihep_obs["referenceRange"] = self._parse_reference_range(
                result_data
            )

        # Interpretation / abnormal flag
        abnormal_flag = (
            self._get_nested(result_data, "AbnormalFlag")
            or self._get_nested(result_data, "Flag")
        )
        if abnormal_flag:
            ihep_obs["interpretation"] = self._map_abnormal_flag(
                str(abnormal_flag)
            )

        # Performer
        ordering_provider = (
            self._get_nested(result_data, "OrderingProvider")
            or self._get_nested(result_data, "Provider")
        )
        if ordering_provider:
            ihep_obs["performer"] = [
                {
                    "reference": "Practitioner/unknown",
                    "display": str(ordering_provider),
                }
            ]

        # IHEP extensions
        ihep_obs["extension"] = [
            {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-data-quality-score",
                "extension": [
                    {"url": "overall-score", "valueDecimal": 0.75},
                    {"url": "completeness", "valueDecimal": 0.80},
                    {"url": "accuracy", "valueDecimal": 0.85},
                    {"url": "timeliness", "valueDecimal": 0.70},
                    {"url": "conformance", "valueDecimal": 0.72},
                    {"url": "assessment-timestamp", "valueDateTime": now},
                ],
            },
            {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-source-system",
                "extension": [
                    {"url": "system-id", "valueString": self.source_system_id},
                    {"url": "system-name", "valueString": "Allscripts Unity"},
                    {"url": "system-version", "valueString": "Unity API v2"},
                    {"url": "extraction-timestamp", "valueDateTime": now},
                    {"url": "mapping-version", "valueString": self.mapping_version},
                    {"url": "original-resource-id", "valueString": allscripts_id},
                ],
            },
        ]

        logger.info(
            "Successfully mapped Allscripts Result %s -> IHEP Observation %s",
            allscripts_id,
            ihep_id,
        )
        return ihep_obs

    def _map_result_value(
        self, result_data: Dict, ihep_obs: Dict[str, Any]
    ) -> None:
        """Extract and normalize the result value from Allscripts Unity format.

        Unity returns values as flat fields: ResultValue, Units, etc.
        """
        result_value = self._get_nested(result_data, "ResultValue") or self._get_nested(
            result_data, "Value"
        )

        if result_value is None:
            return

        result_value_str = str(result_value).strip()
        units = str(
            self._get_nested(result_data, "Units")
            or self._get_nested(result_data, "Unit")
            or ""
        ).strip()

        # Try to parse as numeric
        try:
            # Handle comparators (e.g., "<20", ">=100")
            comparator = None
            numeric_str = result_value_str
            for comp in [">=", "<=", ">", "<"]:
                if numeric_str.startswith(comp):
                    comparator = comp
                    numeric_str = numeric_str[len(comp):].strip()
                    break

            numeric_value = float(numeric_str)

            ihep_obs["valueQuantity"] = {
                "value": numeric_value,
                "unit": units if units else "1",
                "system": "http://unitsofmeasure.org",
                "code": units if units else "1",
            }
            if comparator:
                ihep_obs["valueQuantity"]["comparator"] = comparator

        except (ValueError, TypeError):
            # Non-numeric value -- store as string
            ihep_obs["valueString"] = result_value_str

    def _parse_reference_range(self, result_data: Dict) -> List[Dict]:
        """Parse Allscripts reference range from flat fields."""
        range_entry: Dict[str, Any] = {}

        # Try structured low/high first
        normal_low = self._get_nested(result_data, "NormalLow") or self._get_nested(
            result_data, "ReferenceLow"
        )
        normal_high = self._get_nested(result_data, "NormalHigh") or self._get_nested(
            result_data, "ReferenceHigh"
        )
        units = str(
            self._get_nested(result_data, "Units")
            or self._get_nested(result_data, "Unit")
            or ""
        ).strip()

        if normal_low is not None:
            try:
                range_entry["low"] = {
                    "value": float(normal_low),
                    "unit": units,
                    "system": "http://unitsofmeasure.org",
                    "code": units,
                }
            except (ValueError, TypeError):
                pass

        if normal_high is not None:
            try:
                range_entry["high"] = {
                    "value": float(normal_high),
                    "unit": units,
                    "system": "http://unitsofmeasure.org",
                    "code": units,
                }
            except (ValueError, TypeError):
                pass

        # Fall back to text range
        normal_range = self._get_nested(
            result_data, "NormalRange"
        ) or self._get_nested(result_data, "ReferenceRange")
        if normal_range:
            range_entry["text"] = str(normal_range)

            # Try to parse "low-high" format
            if not range_entry.get("low") and "-" in str(normal_range):
                parts = str(normal_range).split("-", 1)
                try:
                    range_entry["low"] = {
                        "value": float(parts[0].strip()),
                        "unit": units,
                    }
                    range_entry["high"] = {
                        "value": float(parts[1].strip()),
                        "unit": units,
                    }
                except (ValueError, TypeError, IndexError):
                    pass

        return [range_entry] if range_entry else []

    @staticmethod
    def _map_abnormal_flag(flag: str) -> List[Dict]:
        """Map Allscripts abnormal flag to FHIR interpretation codes."""
        flag_map = {
            "H": ("H", "High"),
            "HH": ("HH", "Critical High"),
            "L": ("L", "Low"),
            "LL": ("LL", "Critical Low"),
            "A": ("A", "Abnormal"),
            "AA": ("AA", "Critical Abnormal"),
            "N": ("N", "Normal"),
            ">": ("H", "High"),
            "<": ("L", "Low"),
            "High": ("H", "High"),
            "Low": ("L", "Low"),
            "Normal": ("N", "Normal"),
            "Critical": ("AA", "Critical Abnormal"),
            "Abnormal": ("A", "Abnormal"),
        }

        code, display = flag_map.get(flag.strip(), ("A", "Abnormal"))

        return [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": code,
                        "display": display,
                    }
                ]
            }
        ]

    # -------------------------------------------------------------------------
    # Appointment Mapping
    # -------------------------------------------------------------------------

    def map_appointment(
        self, allscripts_appt: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map an Allscripts Unity GetSchedule response to IHEP Appointment.

        Unity GetSchedule returns appointments with proprietary field names
        and flat structures.

        Args:
            allscripts_appt: Raw Allscripts Unity schedule record.

        Returns:
            IHEP canonical Appointment resource dictionary.

        Raises:
            ValueError: If required fields cannot be extracted.
        """
        if not allscripts_appt:
            raise ValueError("Allscripts appointment data cannot be empty")

        ihep_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        appt_data = allscripts_appt
        if isinstance(appt_data, list):
            if not appt_data:
                raise ValueError("Allscripts appointment data list is empty")
            appt_data = appt_data[0]

        allscripts_id = str(
            self._get_nested(appt_data, "AppointmentID")
            or self._get_nested(appt_data, "ScheduleID")
            or self._get_nested(appt_data, "ID")
            or ""
        )

        logger.debug(
            "Mapping Allscripts Appointment %s -> IHEP Appointment %s",
            allscripts_id,
            ihep_id,
        )

        ihep_appt: Dict[str, Any] = {
            "resourceType": "Appointment",
            "id": ihep_id,
            "meta": {
                "source": f"urn:ehr:allscripts:{self.source_system_id}",
                "lastUpdated": now,
                "versionId": "1",
                "profile": [
                    "https://ihep.app/fhir/StructureDefinition/ihep-appointment"
                ],
            },
        }

        # Status
        status_raw = (
            self._get_nested(appt_data, "AppointmentStatus")
            or self._get_nested(appt_data, "Status")
            or "Scheduled"
        )
        ihep_appt["status"] = UNITY_APPOINTMENT_STATUS_MAP.get(
            str(status_raw).strip(), "booked"
        )

        # Service type
        appt_type_name = (
            self._get_nested(appt_data, "AppointmentType")
            or self._get_nested(appt_data, "VisitType")
            or self._get_nested(appt_data, "Type")
            or ""
        )
        if appt_type_name:
            ihep_appt["serviceType"] = [
                {
                    "coding": [
                        {
                            "system": f"urn:ehr:allscripts:{self.source_system_id}:appointment-type",
                            "code": str(appt_type_name),
                            "display": str(appt_type_name),
                        }
                    ],
                    "text": str(appt_type_name),
                }
            ]

        # Appointment type classification
        type_text = str(appt_type_name).lower()
        matched_code = "ROUTINE"
        for key, code in {
            "follow": "FOLLOWUP",
            "walk": "WALKIN",
            "urgent": "EMERGENCY",
            "emergency": "EMERGENCY",
            "physical": "CHECKUP",
            "wellness": "CHECKUP",
            "checkup": "CHECKUP",
        }.items():
            if key in type_text:
                matched_code = code
                break

        ihep_appt["appointmentType"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0276",
                    "code": matched_code,
                    "display": matched_code.replace("_", " ").title(),
                }
            ],
            "text": str(appt_type_name) if appt_type_name else matched_code.title(),
        }

        # Reason
        reason = (
            self._get_nested(appt_data, "Reason")
            or self._get_nested(appt_data, "ChiefComplaint")
            or self._get_nested(appt_data, "ReasonForVisit")
        )
        if reason:
            ihep_appt["reasonCode"] = [
                {"text": str(reason)}
            ]

        # Description
        description = (
            self._get_nested(appt_data, "Description")
            or self._get_nested(appt_data, "Comments")
        )
        if description:
            ihep_appt["description"] = str(description)

        # Start time (required)
        start_date = (
            self._get_nested(appt_data, "AppointmentDate")
            or self._get_nested(appt_data, "Date")
        )
        start_time = (
            self._get_nested(appt_data, "AppointmentTime")
            or self._get_nested(appt_data, "StartTime")
            or self._get_nested(appt_data, "Time")
        )

        start_dt = None
        if start_date:
            combined = str(start_date)
            if start_time:
                combined = f"{start_date} {start_time}"
            start_dt = self._parse_allscripts_date(combined)

        if not start_dt:
            raise ValueError(
                "Appointment start time is required but missing from Allscripts data"
            )
        ihep_appt["start"] = start_dt

        # End time / duration
        duration = (
            self._get_nested(appt_data, "Duration")
            or self._get_nested(appt_data, "Minutes")
        )
        if duration:
            try:
                ihep_appt["minutesDuration"] = int(duration)
            except (ValueError, TypeError):
                pass

        end_time = self._get_nested(appt_data, "EndTime")
        if end_time and start_date:
            end_dt = self._parse_allscripts_date(f"{start_date} {end_time}")
            if end_dt:
                ihep_appt["end"] = end_dt

        # Participants
        participants = []

        # Patient participant
        patient_id = (
            self._get_nested(appt_data, "PatientID")
            or self._get_nested(appt_data, "patientid")
        )
        patient_name = (
            self._get_nested(appt_data, "PatientName")
            or self._get_nested(appt_data, "Patient")
        )
        participants.append(
            {
                "actor": {
                    "reference": f"Patient/{patient_id}" if patient_id else "Patient/unknown",
                    "display": str(patient_name) if patient_name else "",
                },
                "status": "accepted",
                "required": "required",
                "type": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": "SBJ",
                                "display": "Subject",
                            }
                        ]
                    }
                ],
            }
        )

        # Provider participant
        provider_name = (
            self._get_nested(appt_data, "ProviderName")
            or self._get_nested(appt_data, "Provider")
            or self._get_nested(appt_data, "Doctor")
        )
        provider_id = self._get_nested(appt_data, "ProviderID")
        if provider_name or provider_id:
            participants.append(
                {
                    "actor": {
                        "reference": (
                            f"Practitioner/{provider_id}"
                            if provider_id
                            else "Practitioner/unknown"
                        ),
                        "display": str(provider_name) if provider_name else "",
                    },
                    "status": "accepted",
                    "required": "required",
                    "type": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                    "code": "ATND",
                                    "display": "Attender",
                                }
                            ]
                        }
                    ],
                }
            )

        # Location participant
        location = (
            self._get_nested(appt_data, "Location")
            or self._get_nested(appt_data, "Facility")
            or self._get_nested(appt_data, "Office")
        )
        if location:
            participants.append(
                {
                    "actor": {
                        "reference": "Location/unknown",
                        "display": str(location),
                    },
                    "status": "accepted",
                    "required": "information-only",
                    "type": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                    "code": "LOC",
                                    "display": "Location",
                                }
                            ]
                        }
                    ],
                }
            )

        ihep_appt["participant"] = participants

        # Detect virtual visit
        is_virtual = any(
            kw in type_text
            for kw in ["telehealth", "video", "virtual", "phone", "remote"]
        )
        if not is_virtual and description:
            is_virtual = any(
                kw in str(description).lower()
                for kw in ["telehealth", "video", "virtual"]
            )

        ihep_appt["extension"] = [
            {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-virtual-visit",
                "extension": [
                    {"url": "is-virtual", "valueBoolean": is_virtual},
                ],
            }
        ]

        if is_virtual:
            ihep_appt["extension"][0]["extension"].extend(
                [
                    {"url": "platform", "valueString": "Allscripts Telehealth"},
                    {"url": "requires-video", "valueBoolean": True},
                    {"url": "requires-audio", "valueBoolean": True},
                    {"url": "patient-device-check-status", "valueCode": "pending"},
                ]
            )
            ihep_appt["extension"].append(
                {
                    "url": "https://ihep.app/fhir/StructureDefinition/ihep-telehealth-link",
                    "extension": [
                        {"url": "session-id", "valueString": str(uuid.uuid4())},
                        {"url": "max-participants", "valueInteger": 5},
                        {"url": "encryption-level", "valueCode": "e2e-256"},
                    ],
                }
            )

        logger.info(
            "Successfully mapped Allscripts Appointment %s -> IHEP Appointment %s",
            allscripts_id,
            ihep_id,
        )
        return ihep_appt

    # -------------------------------------------------------------------------
    # Bundle Processing
    # -------------------------------------------------------------------------

    def map_bundle(
        self, allscripts_bundle: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process an Allscripts Unity batch response and map each record.

        Allscripts Unity does not use FHIR Bundles natively. This method
        handles both standard FHIR Bundles (if received via an intermediary)
        and Unity-style batch responses with arrays of records.

        Args:
            allscripts_bundle: Allscripts batch response or FHIR Bundle.

        Returns:
            List of mapped IHEP canonical resources.
        """
        if not allscripts_bundle:
            raise ValueError("Allscripts bundle/batch data cannot be empty")

        mapped_resources: List[Dict[str, Any]] = []

        # Handle standard FHIR Bundle format
        if allscripts_bundle.get("resourceType") == "Bundle":
            entries = allscripts_bundle.get("entry", [])
            resource_mappers = {
                "Patient": self.map_patient,
                "Observation": self.map_observation,
                "Appointment": self.map_appointment,
            }
            for idx, entry in enumerate(entries):
                resource = entry.get("resource", {})
                rtype = resource.get("resourceType", "")
                mapper = resource_mappers.get(rtype)
                if mapper:
                    try:
                        mapped_resources.append(mapper(resource))
                    except (ValueError, KeyError, TypeError) as exc:
                        logger.error(
                            "Failed to map %s at entry %d: %s", rtype, idx, exc
                        )
            return mapped_resources

        # Handle Unity-style batch responses
        # Patients
        patients = allscripts_bundle.get("patients") or allscripts_bundle.get(
            "Patients", []
        )
        if isinstance(patients, list):
            for patient in patients:
                try:
                    mapped_resources.append(self.map_patient(patient))
                except (ValueError, KeyError, TypeError) as exc:
                    logger.error("Failed to map Allscripts patient: %s", exc)

        # Results/Observations
        results = (
            allscripts_bundle.get("results")
            or allscripts_bundle.get("Results")
            or allscripts_bundle.get("observations")
            or allscripts_bundle.get("Observations", [])
        )
        if isinstance(results, list):
            for result in results:
                try:
                    mapped_resources.append(self.map_observation(result))
                except (ValueError, KeyError, TypeError) as exc:
                    logger.error("Failed to map Allscripts result: %s", exc)

        # Appointments/Schedule
        appointments = (
            allscripts_bundle.get("appointments")
            or allscripts_bundle.get("Appointments")
            or allscripts_bundle.get("schedule")
            or allscripts_bundle.get("Schedule", [])
        )
        if isinstance(appointments, list):
            for appt in appointments:
                try:
                    mapped_resources.append(self.map_appointment(appt))
                except (ValueError, KeyError, TypeError) as exc:
                    logger.error("Failed to map Allscripts appointment: %s", exc)

        logger.info(
            "Mapped %d resources from Allscripts batch response",
            len(mapped_resources),
        )
        return mapped_resources
