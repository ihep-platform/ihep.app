"""
Epic FHIR R4 to IHEP Canonical Format Mapper
=============================================================================
Transforms Epic EHR FHIR R4 resources into the IHEP canonical resource format.

Handles Epic-specific conventions:
  - MyChart patient identifiers and Epic internal IDs
  - Epic flowsheet observations and custom category codes
  - Epic scheduling extensions and appointment type mappings
  - Epic proprietary extensions (e.g., urn:oid:1.2.840.114350.*)

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
=============================================================================
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Epic OID namespace constants
EPIC_INTERNAL_OID = "urn:oid:1.2.840.114350.1.13.0.1.7.5.737384.0"
EPIC_MYCHART_OID = "urn:oid:1.2.840.114350.1.13.0.1.7.5.737384.4"
EPIC_FHIR_ID_OID = "urn:oid:1.2.840.114350.1.13.0.1.7.5.737384.14"
EPIC_MRN_OID = "urn:oid:1.2.840.114350.1.13.0.1.7.5.737384.100"
EPIC_CSN_OID = "urn:oid:1.2.840.114350.1.13.0.1.7.5.737384.8"

# Epic category code mappings to standard FHIR observation categories
EPIC_CATEGORY_MAP = {
    "smartdata": "survey",
    "flowsheet": "vital-signs",
    "lab": "laboratory",
    "imaging": "imaging",
    "procedure": "procedure",
    "social-history": "social-history",
    "exam": "exam",
}

# Epic appointment type mappings to FHIR v2-0276 codes
EPIC_APPOINTMENT_TYPE_MAP = {
    "Office Visit": "ROUTINE",
    "New Patient": "ROUTINE",
    "Follow Up": "FOLLOWUP",
    "Follow-Up": "FOLLOWUP",
    "Urgent": "EMERGENCY",
    "Walk-In": "WALKIN",
    "Physical": "CHECKUP",
    "Annual Wellness": "CHECKUP",
    "Telehealth": "ROUTINE",
    "Video Visit": "ROUTINE",
    "Phone Visit": "ROUTINE",
    "Procedure": "ROUTINE",
    "Lab Only": "ROUTINE",
}

MAPPING_VERSION = "1.0.0"


class EpicToIHEPMapper:
    """Maps Epic FHIR R4 resources to IHEP canonical format.

    This mapper handles the transformation of patient, observation, and
    appointment resources retrieved from Epic's FHIR R4 endpoints into
    the standardized IHEP canonical format.
    """

    def __init__(self, source_system_id: str = "epic"):
        """Initialize the Epic mapper.

        Args:
            source_system_id: Identifier for the source Epic system instance.
        """
        self.source_system_id = source_system_id
        self.mapping_version = MAPPING_VERSION
        logger.info(
            "EpicToIHEPMapper initialized for source system: %s", source_system_id
        )

    # -------------------------------------------------------------------------
    # Patient Mapping
    # -------------------------------------------------------------------------

    def map_patient(self, epic_patient: Dict[str, Any]) -> Dict[str, Any]:
        """Map an Epic FHIR Patient resource to IHEP canonical format.

        Handles Epic-specific extensions including MyChart identifiers,
        Epic internal IDs, and Epic name formatting conventions.

        Args:
            epic_patient: Raw Epic FHIR R4 Patient resource dictionary.

        Returns:
            IHEP canonical Patient resource dictionary.

        Raises:
            ValueError: If the input is missing required fields.
        """
        if not epic_patient:
            raise ValueError("Epic patient resource cannot be empty")

        resource_type = epic_patient.get("resourceType", "")
        if resource_type != "Patient":
            raise ValueError(
                f"Expected resourceType 'Patient', got '{resource_type}'"
            )

        ihep_id = str(uuid.uuid4())
        epic_id = epic_patient.get("id", "")
        now = datetime.now(timezone.utc).isoformat()

        logger.debug("Mapping Epic Patient %s -> IHEP Patient %s", epic_id, ihep_id)

        ihep_patient: Dict[str, Any] = {
            "resourceType": "Patient",
            "id": ihep_id,
            "meta": {
                "source": f"urn:ehr:epic:{self.source_system_id}",
                "lastUpdated": now,
                "versionId": "1",
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient",
                    "https://ihep.app/fhir/StructureDefinition/ihep-patient",
                ],
            },
            "active": epic_patient.get("active", True),
        }

        # Map identifiers -- preserve Epic identifiers and add IHEP ID
        ihep_patient["identifier"] = self._map_patient_identifiers(
            epic_patient.get("identifier", []), epic_id
        )

        # Map name(s)
        ihep_patient["name"] = self._map_patient_names(
            epic_patient.get("name", [])
        )

        # Birth date (required)
        birth_date = epic_patient.get("birthDate")
        if not birth_date:
            raise ValueError("Patient birthDate is required but missing from Epic data")
        ihep_patient["birthDate"] = birth_date

        # Gender (required)
        gender = epic_patient.get("gender")
        if not gender:
            raise ValueError("Patient gender is required but missing from Epic data")
        ihep_patient["gender"] = self._normalize_gender(gender)

        # Address (optional)
        addresses = epic_patient.get("address", [])
        if addresses:
            ihep_patient["address"] = self._map_addresses(addresses)

        # Telecom (optional)
        telecoms = epic_patient.get("telecom", [])
        if telecoms:
            ihep_patient["telecom"] = self._map_telecoms(telecoms)

        # Managing organization (optional)
        managing_org = epic_patient.get("managingOrganization")
        if managing_org:
            ihep_patient["managingOrganization"] = {
                "reference": managing_org.get("reference", ""),
                "display": managing_org.get("display", ""),
            }

        # Communication / language (optional)
        communications = epic_patient.get("communication", [])
        if communications:
            ihep_patient["communication"] = communications

        # IHEP extensions -- set defaults for new patients
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
            "Successfully mapped Epic Patient %s -> IHEP Patient %s",
            epic_id,
            ihep_id,
        )
        return ihep_patient

    def _map_patient_identifiers(
        self, epic_identifiers: List[Dict], epic_resource_id: str
    ) -> List[Dict]:
        """Map Epic patient identifiers to IHEP format.

        Translates Epic OID-based identifier systems and adds cross-reference
        identifiers for MyChart and Epic internal IDs.
        """
        ihep_identifiers = []

        # Always add the IHEP platform identifier
        ihep_identifiers.append(
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

        for identifier in epic_identifiers:
            system = identifier.get("system", "")
            value = identifier.get("value", "")

            if not value:
                logger.warning("Skipping identifier with empty value: %s", identifier)
                continue

            mapped_identifier: Dict[str, Any] = {
                "system": system,
                "value": value,
            }

            # Classify the Epic identifier type
            if system == EPIC_MRN_OID or self._is_mrn_identifier(identifier):
                mapped_identifier["type"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical Record Number",
                        }
                    ]
                }
                mapped_identifier["use"] = "usual"
            elif system == EPIC_MYCHART_OID:
                mapped_identifier["type"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PI",
                            "display": "MyChart Identifier",
                        }
                    ]
                }
                mapped_identifier["use"] = "secondary"
            elif system == EPIC_INTERNAL_OID or system == EPIC_FHIR_ID_OID:
                mapped_identifier["type"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PI",
                            "display": "Epic Internal Identifier",
                        }
                    ]
                }
                mapped_identifier["use"] = "secondary"
            elif "us-ssn" in system:
                mapped_identifier["type"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "SS",
                            "display": "Social Security Number",
                        }
                    ]
                }
                mapped_identifier["use"] = "official"
            else:
                # Preserve the original type coding if present
                epic_type = identifier.get("type")
                if epic_type:
                    mapped_identifier["type"] = epic_type

            # Preserve period if present
            period = identifier.get("period")
            if period:
                mapped_identifier["period"] = period

            ihep_identifiers.append(mapped_identifier)

        # Add cross-reference to the original Epic FHIR resource ID
        if epic_resource_id:
            ihep_identifiers.append(
                {
                    "system": f"urn:ehr:epic:{self.source_system_id}:fhir-id",
                    "value": epic_resource_id,
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "PI",
                                "display": "Epic FHIR Resource ID",
                            }
                        ]
                    },
                    "use": "secondary",
                }
            )

        return ihep_identifiers

    @staticmethod
    def _is_mrn_identifier(identifier: Dict) -> bool:
        """Check if an Epic identifier is a Medical Record Number."""
        id_type = identifier.get("type", {})
        codings = id_type.get("coding", [])
        for coding in codings:
            if coding.get("code") == "MR":
                return True
        text = id_type.get("text", "").lower()
        return "medical record" in text or "mrn" in text

    def _map_patient_names(self, epic_names: List[Dict]) -> List[Dict]:
        """Map Epic name entries to IHEP format.

        Epic may return names with varying structures. This method normalizes
        name components and handles Epic-specific formatting (e.g., all-caps
        names, combined given/middle names).
        """
        if not epic_names:
            raise ValueError("At least one patient name is required")

        ihep_names = []
        for name_entry in epic_names:
            ihep_name: Dict[str, Any] = {}

            # Use
            use = name_entry.get("use", "official")
            ihep_name["use"] = use

            # Family name -- Epic sometimes returns ALL CAPS
            family = name_entry.get("family", "")
            if family:
                ihep_name["family"] = self._normalize_name_case(family)

            # Given names -- Epic may combine first and middle in one string
            given = name_entry.get("given", [])
            if given:
                ihep_name["given"] = [
                    self._normalize_name_case(g) for g in given if g
                ]
            elif name_entry.get("text"):
                # Fall back to parsing the text representation
                parts = name_entry["text"].split()
                if len(parts) >= 2:
                    ihep_name["family"] = self._normalize_name_case(parts[-1])
                    ihep_name["given"] = [
                        self._normalize_name_case(p) for p in parts[:-1]
                    ]
                else:
                    ihep_name["family"] = self._normalize_name_case(parts[0])
                    ihep_name["given"] = [self._normalize_name_case(parts[0])]

            # Prefix and suffix
            prefix = name_entry.get("prefix", [])
            if prefix:
                ihep_name["prefix"] = prefix
            suffix = name_entry.get("suffix", [])
            if suffix:
                ihep_name["suffix"] = suffix

            # Text representation
            given_text = " ".join(ihep_name.get("given", []))
            family_text = ihep_name.get("family", "")
            ihep_name["text"] = f"{given_text} {family_text}".strip()

            # Period
            period = name_entry.get("period")
            if period:
                ihep_name["period"] = period

            ihep_names.append(ihep_name)

        return ihep_names

    @staticmethod
    def _normalize_name_case(name: str) -> str:
        """Normalize name casing from ALL CAPS or other irregular formats.

        Converts 'SMITH' to 'Smith', preserves hyphenated names like
        'JONES-SMITH' -> 'Jones-Smith', and handles apostrophes like
        'O'BRIEN' -> 'O'Brien'.
        """
        if not name:
            return name
        # If the name is all uppercase, convert to title case
        if name.isupper():
            # Handle hyphenated names
            parts = name.split("-")
            titled_parts = []
            for part in parts:
                # Handle apostrophes (O'Brien, McDonald, etc.)
                if "'" in part:
                    sub_parts = part.split("'")
                    titled_parts.append(
                        "'".join(sp.capitalize() for sp in sub_parts)
                    )
                else:
                    titled_parts.append(part.capitalize())
            return "-".join(titled_parts)
        return name

    @staticmethod
    def _normalize_gender(gender: str) -> str:
        """Normalize gender to FHIR R4 administrative gender values."""
        gender_map = {
            "male": "male",
            "m": "male",
            "female": "female",
            "f": "female",
            "other": "other",
            "o": "other",
            "unknown": "unknown",
            "u": "unknown",
            "nonbinary": "other",
            "non-binary": "other",
            "undifferentiated": "other",
        }
        normalized = gender_map.get(gender.lower().strip(), "unknown")
        if normalized != gender.lower().strip():
            logger.debug("Normalized gender '%s' -> '%s'", gender, normalized)
        return normalized

    @staticmethod
    def _map_addresses(addresses: List[Dict]) -> List[Dict]:
        """Map Epic address entries to IHEP format."""
        mapped = []
        for addr in addresses:
            ihep_addr: Dict[str, Any] = {}

            if addr.get("use"):
                ihep_addr["use"] = addr["use"]
            if addr.get("type"):
                ihep_addr["type"] = addr["type"]
            if addr.get("line"):
                ihep_addr["line"] = addr["line"]
            if addr.get("city"):
                ihep_addr["city"] = addr["city"]
            if addr.get("district"):
                ihep_addr["district"] = addr["district"]
            if addr.get("state"):
                ihep_addr["state"] = addr["state"]
            if addr.get("postalCode"):
                ihep_addr["postalCode"] = addr["postalCode"]
            ihep_addr["country"] = addr.get("country", "US")

            if addr.get("period"):
                ihep_addr["period"] = addr["period"]

            mapped.append(ihep_addr)
        return mapped

    @staticmethod
    def _map_telecoms(telecoms: List[Dict]) -> List[Dict]:
        """Map Epic telecom entries to IHEP format."""
        mapped = []
        for telecom in telecoms:
            if not telecom.get("value"):
                continue

            ihep_telecom: Dict[str, Any] = {
                "system": telecom.get("system", "phone"),
                "value": telecom["value"],
            }

            if telecom.get("use"):
                ihep_telecom["use"] = telecom["use"]
            if telecom.get("rank"):
                ihep_telecom["rank"] = telecom["rank"]
            if telecom.get("period"):
                ihep_telecom["period"] = telecom["period"]

            mapped.append(ihep_telecom)
        return mapped

    # -------------------------------------------------------------------------
    # Observation Mapping
    # -------------------------------------------------------------------------

    def map_observation(self, epic_obs: Dict[str, Any]) -> Dict[str, Any]:
        """Map an Epic FHIR Observation resource to IHEP canonical format.

        Handles Epic flowsheet data, normalizes value types, and maps
        Epic-specific category codes to standard FHIR categories.

        Args:
            epic_obs: Raw Epic FHIR R4 Observation resource dictionary.

        Returns:
            IHEP canonical Observation resource dictionary.

        Raises:
            ValueError: If required fields are missing.
        """
        if not epic_obs:
            raise ValueError("Epic observation resource cannot be empty")

        resource_type = epic_obs.get("resourceType", "")
        if resource_type != "Observation":
            raise ValueError(
                f"Expected resourceType 'Observation', got '{resource_type}'"
            )

        ihep_id = str(uuid.uuid4())
        epic_id = epic_obs.get("id", "")
        now = datetime.now(timezone.utc).isoformat()

        logger.debug(
            "Mapping Epic Observation %s -> IHEP Observation %s", epic_id, ihep_id
        )

        ihep_obs: Dict[str, Any] = {
            "resourceType": "Observation",
            "id": ihep_id,
            "meta": {
                "source": f"urn:ehr:epic:{self.source_system_id}",
                "lastUpdated": now,
                "versionId": "1",
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab",
                    "https://ihep.app/fhir/StructureDefinition/ihep-observation",
                ],
            },
        }

        # Status (required)
        status = epic_obs.get("status")
        if not status:
            raise ValueError("Observation status is required but missing")
        ihep_obs["status"] = status

        # Category -- map Epic-specific categories
        ihep_obs["category"] = self._map_observation_categories(
            epic_obs.get("category", [])
        )

        # Code (required) -- preserve LOINC / SNOMED coding
        code = epic_obs.get("code")
        if not code:
            raise ValueError("Observation code is required but missing")
        ihep_obs["code"] = self._map_observation_code(code)

        # Subject (required)
        subject = epic_obs.get("subject")
        if not subject:
            raise ValueError("Observation subject is required but missing")
        ihep_obs["subject"] = {
            "reference": subject.get("reference", ""),
            "display": subject.get("display", ""),
        }

        # Encounter (optional)
        encounter = epic_obs.get("encounter")
        if encounter:
            ihep_obs["encounter"] = {
                "reference": encounter.get("reference", ""),
                "display": encounter.get("display", ""),
            }

        # Effective date/time or period
        if epic_obs.get("effectiveDateTime"):
            ihep_obs["effectiveDateTime"] = epic_obs["effectiveDateTime"]
        elif epic_obs.get("effectivePeriod"):
            ihep_obs["effectivePeriod"] = epic_obs["effectivePeriod"]

        # Issued timestamp
        if epic_obs.get("issued"):
            ihep_obs["issued"] = epic_obs["issued"]

        # Value -- handle different Epic value types
        self._map_observation_value(epic_obs, ihep_obs)

        # Data absent reason
        if epic_obs.get("dataAbsentReason"):
            ihep_obs["dataAbsentReason"] = epic_obs["dataAbsentReason"]

        # Interpretation
        if epic_obs.get("interpretation"):
            ihep_obs["interpretation"] = epic_obs["interpretation"]

        # Reference range
        if epic_obs.get("referenceRange"):
            ihep_obs["referenceRange"] = epic_obs["referenceRange"]

        # Performer
        if epic_obs.get("performer"):
            ihep_obs["performer"] = [
                {
                    "reference": p.get("reference", ""),
                    "display": p.get("display", ""),
                }
                for p in epic_obs["performer"]
            ]

        # Components (e.g., blood pressure systolic/diastolic)
        if epic_obs.get("component"):
            ihep_obs["component"] = self._map_observation_components(
                epic_obs["component"]
            )

        # Notes
        if epic_obs.get("note"):
            ihep_obs["note"] = epic_obs["note"]

        # IHEP extensions
        ihep_obs["extension"] = self._build_observation_extensions(epic_id, now)

        logger.info(
            "Successfully mapped Epic Observation %s -> IHEP Observation %s",
            epic_id,
            ihep_id,
        )
        return ihep_obs

    def _map_observation_categories(
        self, epic_categories: List[Dict]
    ) -> List[Dict]:
        """Map Epic observation categories to standard FHIR categories.

        Epic may use proprietary category codes in flowsheet data. This method
        translates them to standard observation-category codes.
        """
        if not epic_categories:
            return [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "laboratory",
                            "display": "Laboratory",
                        }
                    ]
                }
            ]

        mapped = []
        for category in epic_categories:
            codings = category.get("coding", [])
            mapped_codings = []

            for coding in codings:
                code = coding.get("code", "").lower()
                system = coding.get("system", "")

                # Map Epic proprietary category codes
                if code in EPIC_CATEGORY_MAP:
                    mapped_code = EPIC_CATEGORY_MAP[code]
                    mapped_codings.append(
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": mapped_code,
                            "display": mapped_code.replace("-", " ").title(),
                        }
                    )
                elif "observation-category" in system:
                    # Already a standard category code
                    mapped_codings.append(coding)
                else:
                    # Preserve unrecognized codes, map to closest standard
                    logger.warning(
                        "Unrecognized Epic category code '%s' -- preserving as-is",
                        code,
                    )
                    mapped_codings.append(coding)

            if mapped_codings:
                mapped_category: Dict[str, Any] = {"coding": mapped_codings}
                if category.get("text"):
                    mapped_category["text"] = category["text"]
                mapped.append(mapped_category)

        return mapped if mapped else [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                        "display": "Laboratory",
                    }
                ]
            }
        ]

    @staticmethod
    def _map_observation_code(epic_code: Dict) -> Dict:
        """Map Epic observation code, preserving LOINC and SNOMED codings."""
        mapped_code: Dict[str, Any] = {}

        codings = epic_code.get("coding", [])
        if codings:
            mapped_code["coding"] = []
            for coding in codings:
                mapped_coding: Dict[str, Any] = {
                    "system": coding.get("system", ""),
                    "code": coding.get("code", ""),
                }
                if coding.get("display"):
                    mapped_coding["display"] = coding["display"]
                mapped_code["coding"].append(mapped_coding)

        if epic_code.get("text"):
            mapped_code["text"] = epic_code["text"]

        return mapped_code

    @staticmethod
    def _map_observation_value(
        epic_obs: Dict[str, Any], ihep_obs: Dict[str, Any]
    ) -> None:
        """Extract and normalize the observation value from Epic format.

        Epic flowsheet data may include values in different formats.
        This method handles valueQuantity, valueString, valueCodeableConcept,
        and Epic-specific value representations.
        """
        if epic_obs.get("valueQuantity"):
            vq = epic_obs["valueQuantity"]
            ihep_obs["valueQuantity"] = {
                "value": vq.get("value"),
                "unit": vq.get("unit", ""),
                "system": vq.get("system", "http://unitsofmeasure.org"),
                "code": vq.get("code", vq.get("unit", "")),
            }
            if vq.get("comparator"):
                ihep_obs["valueQuantity"]["comparator"] = vq["comparator"]

        elif epic_obs.get("valueString"):
            ihep_obs["valueString"] = epic_obs["valueString"]

        elif epic_obs.get("valueCodeableConcept"):
            ihep_obs["valueCodeableConcept"] = epic_obs["valueCodeableConcept"]

        elif epic_obs.get("valueBoolean") is not None:
            # Epic sometimes returns boolean values -- convert to string
            ihep_obs["valueString"] = str(epic_obs["valueBoolean"])

        elif epic_obs.get("valueInteger") is not None:
            # Convert integer values to quantity
            ihep_obs["valueQuantity"] = {
                "value": epic_obs["valueInteger"],
                "unit": "1",
                "system": "http://unitsofmeasure.org",
                "code": "1",
            }

    def _map_observation_components(
        self, epic_components: List[Dict]
    ) -> List[Dict]:
        """Map observation components (e.g., blood pressure panels)."""
        mapped = []
        for comp in epic_components:
            mapped_comp: Dict[str, Any] = {}

            if comp.get("code"):
                mapped_comp["code"] = self._map_observation_code(comp["code"])

            if comp.get("valueQuantity"):
                vq = comp["valueQuantity"]
                mapped_comp["valueQuantity"] = {
                    "value": vq.get("value"),
                    "unit": vq.get("unit", ""),
                    "system": vq.get("system", "http://unitsofmeasure.org"),
                    "code": vq.get("code", vq.get("unit", "")),
                }

            if comp.get("valueString"):
                mapped_comp["valueString"] = comp["valueString"]

            if comp.get("interpretation"):
                mapped_comp["interpretation"] = comp["interpretation"]

            if comp.get("referenceRange"):
                mapped_comp["referenceRange"] = comp["referenceRange"]

            mapped.append(mapped_comp)

        return mapped

    def _build_observation_extensions(
        self, epic_id: str, timestamp: str
    ) -> List[Dict]:
        """Build IHEP observation extensions for data quality and source tracking."""
        return [
            {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-data-quality-score",
                "extension": [
                    {"url": "overall-score", "valueDecimal": 0.85},
                    {"url": "completeness", "valueDecimal": 0.90},
                    {"url": "accuracy", "valueDecimal": 0.95},
                    {"url": "timeliness", "valueDecimal": 0.80},
                    {"url": "conformance", "valueDecimal": 0.90},
                    {"url": "assessment-timestamp", "valueDateTime": timestamp},
                ],
            },
            {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-source-system",
                "extension": [
                    {"url": "system-id", "valueString": self.source_system_id},
                    {"url": "system-name", "valueString": "Epic"},
                    {"url": "system-version", "valueString": "FHIR R4 (February 2024)"},
                    {"url": "extraction-timestamp", "valueDateTime": timestamp},
                    {"url": "mapping-version", "valueString": self.mapping_version},
                    {"url": "original-resource-id", "valueString": epic_id},
                ],
            },
        ]

    # -------------------------------------------------------------------------
    # Appointment Mapping
    # -------------------------------------------------------------------------

    def map_appointment(self, epic_appt: Dict[str, Any]) -> Dict[str, Any]:
        """Map an Epic FHIR Appointment resource to IHEP canonical format.

        Handles Epic scheduling extensions, appointment type mappings,
        and telehealth visit detection.

        Args:
            epic_appt: Raw Epic FHIR R4 Appointment resource dictionary.

        Returns:
            IHEP canonical Appointment resource dictionary.

        Raises:
            ValueError: If required fields are missing.
        """
        if not epic_appt:
            raise ValueError("Epic appointment resource cannot be empty")

        resource_type = epic_appt.get("resourceType", "")
        if resource_type != "Appointment":
            raise ValueError(
                f"Expected resourceType 'Appointment', got '{resource_type}'"
            )

        ihep_id = str(uuid.uuid4())
        epic_id = epic_appt.get("id", "")
        now = datetime.now(timezone.utc).isoformat()

        logger.debug(
            "Mapping Epic Appointment %s -> IHEP Appointment %s", epic_id, ihep_id
        )

        ihep_appt: Dict[str, Any] = {
            "resourceType": "Appointment",
            "id": ihep_id,
            "meta": {
                "source": f"urn:ehr:epic:{self.source_system_id}",
                "lastUpdated": now,
                "versionId": "1",
                "profile": [
                    "https://ihep.app/fhir/StructureDefinition/ihep-appointment"
                ],
            },
        }

        # Status (required)
        status = epic_appt.get("status")
        if not status:
            raise ValueError("Appointment status is required but missing")
        ihep_appt["status"] = status

        # Cancellation reason
        if epic_appt.get("cancelationReason"):
            ihep_appt["cancelationReason"] = epic_appt["cancelationReason"]

        # Service type
        if epic_appt.get("serviceType"):
            ihep_appt["serviceType"] = epic_appt["serviceType"]

        # Service category
        if epic_appt.get("serviceCategory"):
            ihep_appt["serviceCategory"] = epic_appt["serviceCategory"]

        # Specialty
        if epic_appt.get("specialty"):
            ihep_appt["specialty"] = epic_appt["specialty"]

        # Appointment type -- map Epic types to standard codes
        ihep_appt["appointmentType"] = self._map_appointment_type(epic_appt)

        # Reason code
        if epic_appt.get("reasonCode"):
            ihep_appt["reasonCode"] = epic_appt["reasonCode"]

        # Reason reference
        if epic_appt.get("reasonReference"):
            ihep_appt["reasonReference"] = epic_appt["reasonReference"]

        # Priority
        if epic_appt.get("priority") is not None:
            ihep_appt["priority"] = epic_appt["priority"]

        # Description
        if epic_appt.get("description"):
            ihep_appt["description"] = epic_appt["description"]

        # Start (required)
        start = epic_appt.get("start")
        if not start:
            raise ValueError("Appointment start time is required but missing")
        ihep_appt["start"] = start

        # End
        if epic_appt.get("end"):
            ihep_appt["end"] = epic_appt["end"]

        # Duration
        if epic_appt.get("minutesDuration"):
            ihep_appt["minutesDuration"] = epic_appt["minutesDuration"]

        # Created timestamp
        if epic_appt.get("created"):
            ihep_appt["created"] = epic_appt["created"]

        # Comment
        if epic_appt.get("comment"):
            ihep_appt["comment"] = epic_appt["comment"]

        # Patient instructions
        if epic_appt.get("patientInstruction"):
            ihep_appt["patientInstruction"] = epic_appt["patientInstruction"]

        # Participants (required)
        participants = epic_appt.get("participant", [])
        if not participants:
            raise ValueError("At least one participant is required")
        ihep_appt["participant"] = self._map_appointment_participants(participants)

        # Detect telehealth / virtual visit and build IHEP extensions
        is_virtual = self._detect_virtual_visit(epic_appt)
        ihep_appt["extension"] = self._build_appointment_extensions(
            epic_appt, is_virtual
        )

        logger.info(
            "Successfully mapped Epic Appointment %s -> IHEP Appointment %s",
            epic_id,
            ihep_id,
        )
        return ihep_appt

    @staticmethod
    def _map_appointment_type(epic_appt: Dict) -> Dict:
        """Map Epic appointment type to FHIR v2-0276 codes."""
        appt_type = epic_appt.get("appointmentType", {})
        epic_text = appt_type.get("text", "")

        # Try to match the display text against known Epic types
        matched_code = "ROUTINE"
        for epic_name, fhir_code in EPIC_APPOINTMENT_TYPE_MAP.items():
            if epic_name.lower() in epic_text.lower():
                matched_code = fhir_code
                break

        # Also check the service type for telehealth indicators
        service_types = epic_appt.get("serviceType", [])
        for stype in service_types:
            stext = stype.get("text", "").lower()
            codings = stype.get("coding", [])
            for coding in codings:
                display = coding.get("display", "").lower()
                if any(
                    kw in display or kw in stext
                    for kw in ["telehealth", "video", "virtual"]
                ):
                    matched_code = "ROUTINE"
                    break

        return {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0276",
                    "code": matched_code,
                    "display": matched_code.replace("_", " ").title(),
                }
            ],
            "text": epic_text or matched_code.title(),
        }

    @staticmethod
    def _map_appointment_participants(
        epic_participants: List[Dict],
    ) -> List[Dict]:
        """Map Epic appointment participants to IHEP format."""
        mapped = []
        for participant in epic_participants:
            ihep_participant: Dict[str, Any] = {}

            # Type
            if participant.get("type"):
                ihep_participant["type"] = participant["type"]

            # Actor (required)
            actor = participant.get("actor", {})
            ihep_participant["actor"] = {
                "reference": actor.get("reference", ""),
                "display": actor.get("display", ""),
            }
            if actor.get("identifier"):
                ihep_participant["actor"]["identifier"] = actor["identifier"]

            # Required status
            if participant.get("required"):
                ihep_participant["required"] = participant["required"]

            # Acceptance status
            ihep_participant["status"] = participant.get("status", "needs-action")

            # Period
            if participant.get("period"):
                ihep_participant["period"] = participant["period"]

            mapped.append(ihep_participant)

        return mapped

    @staticmethod
    def _detect_virtual_visit(epic_appt: Dict) -> bool:
        """Detect if an Epic appointment is a virtual/telehealth visit.

        Checks appointment type, service type, description, and Epic-specific
        extensions for telehealth indicators.
        """
        # Check description and comments
        text_fields = [
            epic_appt.get("description", ""),
            epic_appt.get("comment", ""),
            epic_appt.get("patientInstruction", ""),
        ]
        telehealth_keywords = [
            "telehealth",
            "video visit",
            "virtual",
            "telemedicine",
            "remote",
            "phone visit",
        ]
        for text in text_fields:
            if text and any(kw in text.lower() for kw in telehealth_keywords):
                return True

        # Check service types
        for stype in epic_appt.get("serviceType", []):
            text = stype.get("text", "").lower()
            for coding in stype.get("coding", []):
                display = coding.get("display", "").lower()
                if any(kw in text or kw in display for kw in telehealth_keywords):
                    return True

        # Check appointment type
        appt_type = epic_appt.get("appointmentType", {})
        appt_text = appt_type.get("text", "").lower()
        if any(kw in appt_text for kw in telehealth_keywords):
            return True

        # Check Epic-specific extensions
        for ext in epic_appt.get("extension", []):
            url = ext.get("url", "")
            if "telehealth" in url.lower() or "video-visit" in url.lower():
                return True

        return False

    def _build_appointment_extensions(
        self, epic_appt: Dict, is_virtual: bool
    ) -> List[Dict]:
        """Build IHEP appointment extensions for virtual visits and telehealth."""
        extensions = []

        # Virtual visit extension
        virtual_ext: Dict[str, Any] = {
            "url": "https://ihep.app/fhir/StructureDefinition/ihep-virtual-visit",
            "extension": [
                {"url": "is-virtual", "valueBoolean": is_virtual},
            ],
        }

        if is_virtual:
            virtual_ext["extension"].extend(
                [
                    {"url": "platform", "valueString": "Epic MyChart Video Visit"},
                    {"url": "requires-video", "valueBoolean": True},
                    {"url": "requires-audio", "valueBoolean": True},
                    {
                        "url": "patient-device-check-status",
                        "valueCode": "pending",
                    },
                    {"url": "recording-consent", "valueCode": "pending"},
                    {"url": "waiting-room-enabled", "valueBoolean": True},
                ]
            )

            # Build telehealth link extension if virtual
            telehealth_ext: Dict[str, Any] = {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-telehealth-link",
                "extension": [
                    {
                        "url": "session-id",
                        "valueString": str(uuid.uuid4()),
                    },
                    {"url": "max-participants", "valueInteger": 5},
                    {"url": "encryption-level", "valueCode": "e2e-256"},
                ],
            }

            # Extract telehealth URLs from Epic extensions if present
            for ext in epic_appt.get("extension", []):
                url = ext.get("url", "")
                if "video-visit-url" in url.lower() or "telehealth-url" in url.lower():
                    telehealth_ext["extension"].append(
                        {
                            "url": "session-url",
                            "valueUrl": ext.get("valueUrl", ext.get("valueString", "")),
                        }
                    )

            extensions.append(telehealth_ext)

        extensions.insert(0, virtual_ext)
        return extensions

    # -------------------------------------------------------------------------
    # Bundle Processing
    # -------------------------------------------------------------------------

    def map_bundle(self, epic_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a FHIR Bundle and map each entry to IHEP canonical format.

        Iterates over all entries in an Epic FHIR Bundle, identifies the
        resource type, and dispatches to the appropriate mapping method.

        Args:
            epic_bundle: Raw Epic FHIR Bundle resource dictionary.

        Returns:
            List of mapped IHEP canonical resources.

        Raises:
            ValueError: If the input is not a valid Bundle.
        """
        if not epic_bundle:
            raise ValueError("Epic bundle cannot be empty")

        resource_type = epic_bundle.get("resourceType", "")
        if resource_type != "Bundle":
            raise ValueError(
                f"Expected resourceType 'Bundle', got '{resource_type}'"
            )

        entries = epic_bundle.get("entry", [])
        if not entries:
            logger.warning("Epic Bundle contains no entries")
            return []

        logger.info(
            "Processing Epic Bundle with %d entries (type: %s)",
            len(entries),
            epic_bundle.get("type", "unknown"),
        )

        mapped_resources: List[Dict[str, Any]] = []
        errors: List[Dict[str, str]] = []

        resource_mappers = {
            "Patient": self.map_patient,
            "Observation": self.map_observation,
            "Appointment": self.map_appointment,
        }

        for idx, entry in enumerate(entries):
            resource = entry.get("resource", {})
            entry_resource_type = resource.get("resourceType", "")

            mapper = resource_mappers.get(entry_resource_type)
            if mapper is None:
                logger.debug(
                    "Skipping unsupported resource type '%s' at entry %d",
                    entry_resource_type,
                    idx,
                )
                continue

            try:
                mapped = mapper(resource)
                mapped_resources.append(mapped)
            except (ValueError, KeyError, TypeError) as exc:
                error_msg = (
                    f"Failed to map {entry_resource_type} at entry {idx}: {exc}"
                )
                logger.error(error_msg)
                errors.append(
                    {
                        "entry_index": str(idx),
                        "resource_type": entry_resource_type,
                        "resource_id": resource.get("id", "unknown"),
                        "error": str(exc),
                    }
                )

        if errors:
            logger.warning(
                "Bundle mapping completed with %d errors out of %d entries",
                len(errors),
                len(entries),
            )

        logger.info(
            "Successfully mapped %d resources from Epic Bundle",
            len(mapped_resources),
        )
        return mapped_resources
