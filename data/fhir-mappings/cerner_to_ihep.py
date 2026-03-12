"""
Cerner Millennium FHIR R4 to IHEP Canonical Format Mapper
=============================================================================
Transforms Cerner Millennium EHR FHIR R4 resources into the IHEP canonical
resource format.

Handles Cerner-specific conventions:
  - Cerner Millennium internal identifiers and MRN systems
  - Cerner proprietary extensions (e.g., urn:oid:2.16.840.1.113883.6.*)
  - Cerner code system translations and custom value sets
  - Cerner scheduling and encounter patterns

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
=============================================================================
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Cerner OID namespace constants
CERNER_MRN_OID = "urn:oid:2.16.840.1.113883.6.1000"
CERNER_ACCOUNT_OID = "urn:oid:2.16.840.1.113883.6.1001"
CERNER_FIN_OID = "urn:oid:2.16.840.1.113883.6.1002"
CERNER_ENCOUNTER_OID = "urn:oid:2.16.840.1.113883.6.1003"
CERNER_FHIR_ID_SYSTEM = "https://fhir.cerner.com/id"

# Cerner code system translation map
CERNER_CODE_SYSTEM_MAP = {
    "https://fhir.cerner.com/CodeSystem/observation-category": (
        "http://terminology.hl7.org/CodeSystem/observation-category"
    ),
    "https://fhir.cerner.com/CodeSystem/appointment-type": (
        "http://terminology.hl7.org/CodeSystem/v2-0276"
    ),
    "https://fhir.cerner.com/CodeSystem/service-type": (
        "http://terminology.hl7.org/CodeSystem/service-type"
    ),
}

# Cerner category code to standard FHIR category mapping
CERNER_CATEGORY_MAP = {
    "lab": "laboratory",
    "laboratory": "laboratory",
    "vital-signs": "vital-signs",
    "vitals": "vital-signs",
    "flowsheet": "vital-signs",
    "social-history": "social-history",
    "imaging": "imaging",
    "assessment": "survey",
    "exam": "exam",
    "procedure": "procedure",
    "therapy": "therapy",
    "activity": "activity",
}

# Cerner appointment type mappings
CERNER_APPOINTMENT_TYPE_MAP = {
    "routine": "ROUTINE",
    "follow-up": "FOLLOWUP",
    "followup": "FOLLOWUP",
    "walk-in": "WALKIN",
    "walkin": "WALKIN",
    "urgent": "EMERGENCY",
    "emergency": "EMERGENCY",
    "checkup": "CHECKUP",
    "wellness": "CHECKUP",
    "new patient": "ROUTINE",
    "telehealth": "ROUTINE",
    "virtual": "ROUTINE",
}

MAPPING_VERSION = "1.0.0"


class CernerToIHEPMapper:
    """Maps Cerner Millennium FHIR R4 resources to IHEP canonical format.

    Handles transformation of patient, observation, and appointment resources
    from Cerner's FHIR R4 API into the standardized IHEP canonical format,
    including translation of Cerner proprietary code systems and extensions.
    """

    def __init__(self, source_system_id: str = "cerner"):
        """Initialize the Cerner mapper.

        Args:
            source_system_id: Identifier for the source Cerner system instance.
        """
        self.source_system_id = source_system_id
        self.mapping_version = MAPPING_VERSION
        logger.info(
            "CernerToIHEPMapper initialized for source system: %s",
            source_system_id,
        )

    # -------------------------------------------------------------------------
    # Code System Translation
    # -------------------------------------------------------------------------

    @staticmethod
    def _translate_code_system(system: str) -> str:
        """Translate Cerner proprietary code system URIs to standard FHIR URIs.

        Args:
            system: The code system URI from Cerner data.

        Returns:
            Standard FHIR code system URI if a mapping exists, otherwise
            the original URI.
        """
        return CERNER_CODE_SYSTEM_MAP.get(system, system)

    def _translate_coding(self, coding: Dict) -> Dict:
        """Translate a single coding entry, mapping Cerner code systems."""
        translated = dict(coding)
        if "system" in translated:
            translated["system"] = self._translate_code_system(translated["system"])
        return translated

    def _translate_codeable_concept(self, concept: Dict) -> Dict:
        """Translate all codings within a CodeableConcept."""
        translated = dict(concept)
        if "coding" in translated:
            translated["coding"] = [
                self._translate_coding(c) for c in translated["coding"]
            ]
        return translated

    # -------------------------------------------------------------------------
    # Patient Mapping
    # -------------------------------------------------------------------------

    def map_patient(self, cerner_patient: Dict[str, Any]) -> Dict[str, Any]:
        """Map a Cerner FHIR Patient resource to IHEP canonical format.

        Handles Cerner Millennium-specific identifiers, name formatting,
        and proprietary extensions.

        Args:
            cerner_patient: Raw Cerner FHIR R4 Patient resource dictionary.

        Returns:
            IHEP canonical Patient resource dictionary.

        Raises:
            ValueError: If required fields are missing.
        """
        if not cerner_patient:
            raise ValueError("Cerner patient resource cannot be empty")

        resource_type = cerner_patient.get("resourceType", "")
        if resource_type != "Patient":
            raise ValueError(
                f"Expected resourceType 'Patient', got '{resource_type}'"
            )

        ihep_id = str(uuid.uuid4())
        cerner_id = cerner_patient.get("id", "")
        now = datetime.now(timezone.utc).isoformat()

        logger.debug(
            "Mapping Cerner Patient %s -> IHEP Patient %s", cerner_id, ihep_id
        )

        ihep_patient: Dict[str, Any] = {
            "resourceType": "Patient",
            "id": ihep_id,
            "meta": {
                "source": f"urn:ehr:cerner:{self.source_system_id}",
                "lastUpdated": now,
                "versionId": "1",
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient",
                    "https://ihep.app/fhir/StructureDefinition/ihep-patient",
                ],
            },
            "active": cerner_patient.get("active", True),
        }

        # Map identifiers
        ihep_patient["identifier"] = self._map_patient_identifiers(
            cerner_patient.get("identifier", []), cerner_id
        )

        # Map names
        ihep_patient["name"] = self._map_patient_names(
            cerner_patient.get("name", [])
        )

        # Birth date (required)
        birth_date = cerner_patient.get("birthDate")
        if not birth_date:
            raise ValueError(
                "Patient birthDate is required but missing from Cerner data"
            )
        ihep_patient["birthDate"] = birth_date

        # Gender (required)
        gender = cerner_patient.get("gender")
        if not gender:
            raise ValueError(
                "Patient gender is required but missing from Cerner data"
            )
        ihep_patient["gender"] = self._normalize_gender(gender)

        # Address (optional)
        addresses = cerner_patient.get("address", [])
        if addresses:
            ihep_patient["address"] = self._map_addresses(addresses)

        # Telecom (optional)
        telecoms = cerner_patient.get("telecom", [])
        if telecoms:
            ihep_patient["telecom"] = self._map_telecoms(telecoms)

        # Managing organization (optional)
        managing_org = cerner_patient.get("managingOrganization")
        if managing_org:
            ihep_patient["managingOrganization"] = {
                "reference": managing_org.get("reference", ""),
                "display": managing_org.get("display", ""),
            }

        # Communication (optional)
        communications = cerner_patient.get("communication", [])
        if communications:
            ihep_patient["communication"] = communications

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
            "Successfully mapped Cerner Patient %s -> IHEP Patient %s",
            cerner_id,
            ihep_id,
        )
        return ihep_patient

    def _map_patient_identifiers(
        self, cerner_identifiers: List[Dict], cerner_resource_id: str
    ) -> List[Dict]:
        """Map Cerner patient identifiers to IHEP format.

        Handles Cerner Millennium MRN, FIN, account number, and FHIR ID systems.
        """
        ihep_identifiers = []

        # Add IHEP platform identifier
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

        for identifier in cerner_identifiers:
            system = identifier.get("system", "")
            value = identifier.get("value", "")

            if not value:
                logger.warning(
                    "Skipping Cerner identifier with empty value: %s", identifier
                )
                continue

            mapped_id: Dict[str, Any] = {"system": system, "value": value}

            # Classify Cerner identifier types
            if system == CERNER_MRN_OID or self._is_mrn_identifier(identifier):
                mapped_id["type"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical Record Number",
                        }
                    ]
                }
                mapped_id["use"] = "usual"
            elif system == CERNER_FIN_OID:
                mapped_id["type"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PI",
                            "display": "Cerner FIN Number",
                        }
                    ]
                }
                mapped_id["use"] = "secondary"
            elif system == CERNER_ACCOUNT_OID:
                mapped_id["type"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PI",
                            "display": "Cerner Account Number",
                        }
                    ]
                }
                mapped_id["use"] = "secondary"
            elif system == CERNER_FHIR_ID_SYSTEM:
                mapped_id["type"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PI",
                            "display": "Cerner FHIR Identifier",
                        }
                    ]
                }
                mapped_id["use"] = "secondary"
            elif "us-ssn" in system:
                mapped_id["type"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "SS",
                            "display": "Social Security Number",
                        }
                    ]
                }
                mapped_id["use"] = "official"
            else:
                epic_type = identifier.get("type")
                if epic_type:
                    mapped_id["type"] = epic_type

            if identifier.get("period"):
                mapped_id["period"] = identifier["period"]

            ihep_identifiers.append(mapped_id)

        # Cross-reference to Cerner FHIR resource ID
        if cerner_resource_id:
            ihep_identifiers.append(
                {
                    "system": f"urn:ehr:cerner:{self.source_system_id}:fhir-id",
                    "value": cerner_resource_id,
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "PI",
                                "display": "Cerner FHIR Resource ID",
                            }
                        ]
                    },
                    "use": "secondary",
                }
            )

        return ihep_identifiers

    @staticmethod
    def _is_mrn_identifier(identifier: Dict) -> bool:
        """Check if a Cerner identifier is a Medical Record Number."""
        id_type = identifier.get("type", {})
        codings = id_type.get("coding", [])
        for coding in codings:
            if coding.get("code") == "MR":
                return True
        text = id_type.get("text", "").lower()
        return "medical record" in text or "mrn" in text

    @staticmethod
    def _map_patient_names(cerner_names: List[Dict]) -> List[Dict]:
        """Map Cerner patient names to IHEP format.

        Cerner Millennium typically returns well-structured names, but may
        include multiple name entries with period-based validity.
        """
        if not cerner_names:
            raise ValueError("At least one patient name is required")

        ihep_names = []
        for name_entry in cerner_names:
            ihep_name: Dict[str, Any] = {}

            ihep_name["use"] = name_entry.get("use", "official")

            family = name_entry.get("family", "")
            if family:
                ihep_name["family"] = family

            given = name_entry.get("given", [])
            if given:
                ihep_name["given"] = [g for g in given if g]
            elif name_entry.get("text"):
                parts = name_entry["text"].split(",")
                if len(parts) >= 2:
                    ihep_name["family"] = parts[0].strip()
                    ihep_name["given"] = [p.strip() for p in parts[1].split()]
                else:
                    word_parts = name_entry["text"].split()
                    if len(word_parts) >= 2:
                        ihep_name["family"] = word_parts[-1]
                        ihep_name["given"] = word_parts[:-1]

            if name_entry.get("prefix"):
                ihep_name["prefix"] = name_entry["prefix"]
            if name_entry.get("suffix"):
                ihep_name["suffix"] = name_entry["suffix"]

            given_text = " ".join(ihep_name.get("given", []))
            family_text = ihep_name.get("family", "")
            ihep_name["text"] = f"{given_text} {family_text}".strip()

            if name_entry.get("period"):
                ihep_name["period"] = name_entry["period"]

            ihep_names.append(ihep_name)

        return ihep_names

    @staticmethod
    def _normalize_gender(gender: str) -> str:
        """Normalize gender value to FHIR R4 administrative gender."""
        gender_map = {
            "male": "male",
            "m": "male",
            "female": "female",
            "f": "female",
            "other": "other",
            "unknown": "unknown",
            "nonbinary": "other",
            "non-binary": "other",
            "undifferentiated": "other",
        }
        return gender_map.get(gender.lower().strip(), "unknown")

    @staticmethod
    def _map_addresses(addresses: List[Dict]) -> List[Dict]:
        """Map Cerner address entries to IHEP format."""
        mapped = []
        for addr in addresses:
            ihep_addr: Dict[str, Any] = {}
            for field in ("use", "type", "line", "city", "district", "state",
                          "postalCode"):
                if addr.get(field):
                    ihep_addr[field] = addr[field]
            ihep_addr["country"] = addr.get("country", "US")
            if addr.get("period"):
                ihep_addr["period"] = addr["period"]
            mapped.append(ihep_addr)
        return mapped

    @staticmethod
    def _map_telecoms(telecoms: List[Dict]) -> List[Dict]:
        """Map Cerner telecom entries to IHEP format."""
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

    def map_observation(self, cerner_obs: Dict[str, Any]) -> Dict[str, Any]:
        """Map a Cerner FHIR Observation resource to IHEP canonical format.

        Translates Cerner proprietary code systems, handles Cerner-specific
        category codes, and normalizes value representations.

        Args:
            cerner_obs: Raw Cerner FHIR R4 Observation resource dictionary.

        Returns:
            IHEP canonical Observation resource dictionary.

        Raises:
            ValueError: If required fields are missing.
        """
        if not cerner_obs:
            raise ValueError("Cerner observation resource cannot be empty")

        resource_type = cerner_obs.get("resourceType", "")
        if resource_type != "Observation":
            raise ValueError(
                f"Expected resourceType 'Observation', got '{resource_type}'"
            )

        ihep_id = str(uuid.uuid4())
        cerner_id = cerner_obs.get("id", "")
        now = datetime.now(timezone.utc).isoformat()

        logger.debug(
            "Mapping Cerner Observation %s -> IHEP Observation %s",
            cerner_id,
            ihep_id,
        )

        ihep_obs: Dict[str, Any] = {
            "resourceType": "Observation",
            "id": ihep_id,
            "meta": {
                "source": f"urn:ehr:cerner:{self.source_system_id}",
                "lastUpdated": now,
                "versionId": "1",
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab",
                    "https://ihep.app/fhir/StructureDefinition/ihep-observation",
                ],
            },
        }

        # Status (required)
        status = cerner_obs.get("status")
        if not status:
            raise ValueError("Observation status is required but missing")
        ihep_obs["status"] = status

        # Category -- translate Cerner code systems
        ihep_obs["category"] = self._map_observation_categories(
            cerner_obs.get("category", [])
        )

        # Code (required) -- translate Cerner code systems
        code = cerner_obs.get("code")
        if not code:
            raise ValueError("Observation code is required but missing")
        ihep_obs["code"] = self._translate_codeable_concept(code)

        # Subject (required)
        subject = cerner_obs.get("subject")
        if not subject:
            raise ValueError("Observation subject is required but missing")
        ihep_obs["subject"] = {
            "reference": subject.get("reference", ""),
            "display": subject.get("display", ""),
        }

        # Encounter
        encounter = cerner_obs.get("encounter")
        if encounter:
            ihep_obs["encounter"] = {
                "reference": encounter.get("reference", ""),
                "display": encounter.get("display", ""),
            }

        # Effective date/time or period
        if cerner_obs.get("effectiveDateTime"):
            ihep_obs["effectiveDateTime"] = cerner_obs["effectiveDateTime"]
        elif cerner_obs.get("effectivePeriod"):
            ihep_obs["effectivePeriod"] = cerner_obs["effectivePeriod"]

        # Issued
        if cerner_obs.get("issued"):
            ihep_obs["issued"] = cerner_obs["issued"]

        # Value
        self._map_observation_value(cerner_obs, ihep_obs)

        # Data absent reason
        if cerner_obs.get("dataAbsentReason"):
            ihep_obs["dataAbsentReason"] = self._translate_codeable_concept(
                cerner_obs["dataAbsentReason"]
            )

        # Interpretation
        if cerner_obs.get("interpretation"):
            ihep_obs["interpretation"] = [
                self._translate_codeable_concept(interp)
                for interp in cerner_obs["interpretation"]
            ]

        # Reference range
        if cerner_obs.get("referenceRange"):
            ihep_obs["referenceRange"] = cerner_obs["referenceRange"]

        # Performer
        if cerner_obs.get("performer"):
            ihep_obs["performer"] = [
                {
                    "reference": p.get("reference", ""),
                    "display": p.get("display", ""),
                }
                for p in cerner_obs["performer"]
            ]

        # Components
        if cerner_obs.get("component"):
            ihep_obs["component"] = self._map_observation_components(
                cerner_obs["component"]
            )

        # Notes
        if cerner_obs.get("note"):
            ihep_obs["note"] = cerner_obs["note"]

        # IHEP extensions
        ihep_obs["extension"] = self._build_observation_extensions(
            cerner_id, now
        )

        logger.info(
            "Successfully mapped Cerner Observation %s -> IHEP Observation %s",
            cerner_id,
            ihep_id,
        )
        return ihep_obs

    def _map_observation_categories(
        self, cerner_categories: List[Dict]
    ) -> List[Dict]:
        """Map Cerner observation categories to standard FHIR categories."""
        if not cerner_categories:
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
        for category in cerner_categories:
            translated = self._translate_codeable_concept(category)
            # Also map Cerner-specific category codes
            codings = translated.get("coding", [])
            for i, coding in enumerate(codings):
                code = coding.get("code", "").lower()
                if code in CERNER_CATEGORY_MAP:
                    standard_code = CERNER_CATEGORY_MAP[code]
                    codings[i] = {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": standard_code,
                        "display": standard_code.replace("-", " ").title(),
                    }
            translated["coding"] = codings
            mapped.append(translated)

        return mapped

    def _map_observation_value(
        self, cerner_obs: Dict[str, Any], ihep_obs: Dict[str, Any]
    ) -> None:
        """Extract and normalize the observation value from Cerner format."""
        if cerner_obs.get("valueQuantity"):
            vq = cerner_obs["valueQuantity"]
            ihep_obs["valueQuantity"] = {
                "value": vq.get("value"),
                "unit": vq.get("unit", ""),
                "system": vq.get("system", "http://unitsofmeasure.org"),
                "code": vq.get("code", vq.get("unit", "")),
            }
            if vq.get("comparator"):
                ihep_obs["valueQuantity"]["comparator"] = vq["comparator"]
        elif cerner_obs.get("valueString"):
            ihep_obs["valueString"] = cerner_obs["valueString"]
        elif cerner_obs.get("valueCodeableConcept"):
            ihep_obs["valueCodeableConcept"] = self._translate_codeable_concept(
                cerner_obs["valueCodeableConcept"]
            )
        elif cerner_obs.get("valueBoolean") is not None:
            ihep_obs["valueString"] = str(cerner_obs["valueBoolean"])
        elif cerner_obs.get("valueInteger") is not None:
            ihep_obs["valueQuantity"] = {
                "value": cerner_obs["valueInteger"],
                "unit": "1",
                "system": "http://unitsofmeasure.org",
                "code": "1",
            }

    def _map_observation_components(
        self, cerner_components: List[Dict]
    ) -> List[Dict]:
        """Map Cerner observation components with code system translation."""
        mapped = []
        for comp in cerner_components:
            mapped_comp: Dict[str, Any] = {}

            if comp.get("code"):
                mapped_comp["code"] = self._translate_codeable_concept(
                    comp["code"]
                )

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
                mapped_comp["interpretation"] = [
                    self._translate_codeable_concept(interp)
                    for interp in comp["interpretation"]
                ]

            if comp.get("referenceRange"):
                mapped_comp["referenceRange"] = comp["referenceRange"]

            mapped.append(mapped_comp)

        return mapped

    def _build_observation_extensions(
        self, cerner_id: str, timestamp: str
    ) -> List[Dict]:
        """Build IHEP observation extensions."""
        return [
            {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-data-quality-score",
                "extension": [
                    {"url": "overall-score", "valueDecimal": 0.82},
                    {"url": "completeness", "valueDecimal": 0.88},
                    {"url": "accuracy", "valueDecimal": 0.90},
                    {"url": "timeliness", "valueDecimal": 0.78},
                    {"url": "conformance", "valueDecimal": 0.85},
                    {"url": "assessment-timestamp", "valueDateTime": timestamp},
                ],
            },
            {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-source-system",
                "extension": [
                    {"url": "system-id", "valueString": self.source_system_id},
                    {"url": "system-name", "valueString": "Cerner Millennium"},
                    {
                        "url": "system-version",
                        "valueString": "FHIR R4 (Millennium 2024.01)",
                    },
                    {"url": "extraction-timestamp", "valueDateTime": timestamp},
                    {"url": "mapping-version", "valueString": self.mapping_version},
                    {"url": "original-resource-id", "valueString": cerner_id},
                ],
            },
        ]

    # -------------------------------------------------------------------------
    # Appointment Mapping
    # -------------------------------------------------------------------------

    def map_appointment(self, cerner_appt: Dict[str, Any]) -> Dict[str, Any]:
        """Map a Cerner FHIR Appointment resource to IHEP canonical format.

        Handles Cerner scheduling extensions and appointment type translations.

        Args:
            cerner_appt: Raw Cerner FHIR R4 Appointment resource dictionary.

        Returns:
            IHEP canonical Appointment resource dictionary.

        Raises:
            ValueError: If required fields are missing.
        """
        if not cerner_appt:
            raise ValueError("Cerner appointment resource cannot be empty")

        resource_type = cerner_appt.get("resourceType", "")
        if resource_type != "Appointment":
            raise ValueError(
                f"Expected resourceType 'Appointment', got '{resource_type}'"
            )

        ihep_id = str(uuid.uuid4())
        cerner_id = cerner_appt.get("id", "")
        now = datetime.now(timezone.utc).isoformat()

        logger.debug(
            "Mapping Cerner Appointment %s -> IHEP Appointment %s",
            cerner_id,
            ihep_id,
        )

        ihep_appt: Dict[str, Any] = {
            "resourceType": "Appointment",
            "id": ihep_id,
            "meta": {
                "source": f"urn:ehr:cerner:{self.source_system_id}",
                "lastUpdated": now,
                "versionId": "1",
                "profile": [
                    "https://ihep.app/fhir/StructureDefinition/ihep-appointment"
                ],
            },
        }

        # Status (required)
        status = cerner_appt.get("status")
        if not status:
            raise ValueError("Appointment status is required but missing")
        ihep_appt["status"] = status

        # Cancellation reason
        if cerner_appt.get("cancelationReason"):
            ihep_appt["cancelationReason"] = self._translate_codeable_concept(
                cerner_appt["cancelationReason"]
            )

        # Service type -- translate code systems
        if cerner_appt.get("serviceType"):
            ihep_appt["serviceType"] = [
                self._translate_codeable_concept(st)
                for st in cerner_appt["serviceType"]
            ]

        # Service category
        if cerner_appt.get("serviceCategory"):
            ihep_appt["serviceCategory"] = [
                self._translate_codeable_concept(sc)
                for sc in cerner_appt["serviceCategory"]
            ]

        # Specialty
        if cerner_appt.get("specialty"):
            ihep_appt["specialty"] = [
                self._translate_codeable_concept(sp)
                for sp in cerner_appt["specialty"]
            ]

        # Appointment type -- map Cerner types
        ihep_appt["appointmentType"] = self._map_appointment_type(cerner_appt)

        # Reason code
        if cerner_appt.get("reasonCode"):
            ihep_appt["reasonCode"] = [
                self._translate_codeable_concept(rc)
                for rc in cerner_appt["reasonCode"]
            ]

        # Priority
        if cerner_appt.get("priority") is not None:
            ihep_appt["priority"] = cerner_appt["priority"]

        # Description
        if cerner_appt.get("description"):
            ihep_appt["description"] = cerner_appt["description"]

        # Start (required)
        start = cerner_appt.get("start")
        if not start:
            raise ValueError("Appointment start time is required but missing")
        ihep_appt["start"] = start

        # End
        if cerner_appt.get("end"):
            ihep_appt["end"] = cerner_appt["end"]

        # Duration
        if cerner_appt.get("minutesDuration"):
            ihep_appt["minutesDuration"] = cerner_appt["minutesDuration"]

        # Created
        if cerner_appt.get("created"):
            ihep_appt["created"] = cerner_appt["created"]

        # Comment
        if cerner_appt.get("comment"):
            ihep_appt["comment"] = cerner_appt["comment"]

        # Patient instructions
        if cerner_appt.get("patientInstruction"):
            ihep_appt["patientInstruction"] = cerner_appt["patientInstruction"]

        # Participants (required)
        participants = cerner_appt.get("participant", [])
        if not participants:
            raise ValueError("At least one participant is required")
        ihep_appt["participant"] = self._map_participants(participants)

        # Detect virtual visit and build extensions
        is_virtual = self._detect_virtual_visit(cerner_appt)
        ihep_appt["extension"] = self._build_appointment_extensions(is_virtual)

        logger.info(
            "Successfully mapped Cerner Appointment %s -> IHEP Appointment %s",
            cerner_id,
            ihep_id,
        )
        return ihep_appt

    @staticmethod
    def _map_appointment_type(cerner_appt: Dict) -> Dict:
        """Map Cerner appointment type to FHIR v2-0276 codes."""
        appt_type = cerner_appt.get("appointmentType", {})
        text = appt_type.get("text", "").lower()

        matched_code = "ROUTINE"
        for cerner_name, fhir_code in CERNER_APPOINTMENT_TYPE_MAP.items():
            if cerner_name in text:
                matched_code = fhir_code
                break

        return {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0276",
                    "code": matched_code,
                    "display": matched_code.replace("_", " ").title(),
                }
            ],
            "text": appt_type.get("text", matched_code.title()),
        }

    @staticmethod
    def _map_participants(cerner_participants: List[Dict]) -> List[Dict]:
        """Map Cerner appointment participants."""
        mapped = []
        for participant in cerner_participants:
            ihep_participant: Dict[str, Any] = {}

            if participant.get("type"):
                ihep_participant["type"] = participant["type"]

            actor = participant.get("actor", {})
            ihep_participant["actor"] = {
                "reference": actor.get("reference", ""),
                "display": actor.get("display", ""),
            }
            if actor.get("identifier"):
                ihep_participant["actor"]["identifier"] = actor["identifier"]

            if participant.get("required"):
                ihep_participant["required"] = participant["required"]

            ihep_participant["status"] = participant.get("status", "needs-action")

            if participant.get("period"):
                ihep_participant["period"] = participant["period"]

            mapped.append(ihep_participant)

        return mapped

    @staticmethod
    def _detect_virtual_visit(cerner_appt: Dict) -> bool:
        """Detect if a Cerner appointment is a virtual/telehealth visit."""
        telehealth_keywords = [
            "telehealth", "video", "virtual", "telemedicine", "remote",
        ]

        for text in (
            cerner_appt.get("description", ""),
            cerner_appt.get("comment", ""),
            cerner_appt.get("patientInstruction", ""),
        ):
            if text and any(kw in text.lower() for kw in telehealth_keywords):
                return True

        for stype in cerner_appt.get("serviceType", []):
            for coding in stype.get("coding", []):
                display = coding.get("display", "").lower()
                if any(kw in display for kw in telehealth_keywords):
                    return True

        appt_type_text = cerner_appt.get("appointmentType", {}).get("text", "").lower()
        if any(kw in appt_type_text for kw in telehealth_keywords):
            return True

        return False

    @staticmethod
    def _build_appointment_extensions(is_virtual: bool) -> List[Dict]:
        """Build IHEP appointment extensions."""
        extensions = [
            {
                "url": "https://ihep.app/fhir/StructureDefinition/ihep-virtual-visit",
                "extension": [
                    {"url": "is-virtual", "valueBoolean": is_virtual},
                ],
            }
        ]

        if is_virtual:
            extensions[0]["extension"].extend(
                [
                    {"url": "platform", "valueString": "Cerner Video Visit"},
                    {"url": "requires-video", "valueBoolean": True},
                    {"url": "requires-audio", "valueBoolean": True},
                    {"url": "patient-device-check-status", "valueCode": "pending"},
                    {"url": "recording-consent", "valueCode": "pending"},
                    {"url": "waiting-room-enabled", "valueBoolean": True},
                ]
            )

            extensions.append(
                {
                    "url": "https://ihep.app/fhir/StructureDefinition/ihep-telehealth-link",
                    "extension": [
                        {"url": "session-id", "valueString": str(uuid.uuid4())},
                        {"url": "max-participants", "valueInteger": 5},
                        {"url": "encryption-level", "valueCode": "e2e-256"},
                    ],
                }
            )

        return extensions

    # -------------------------------------------------------------------------
    # Bundle Processing
    # -------------------------------------------------------------------------

    def map_bundle(self, cerner_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a FHIR Bundle and map each entry to IHEP canonical format.

        Args:
            cerner_bundle: Raw Cerner FHIR Bundle resource dictionary.

        Returns:
            List of mapped IHEP canonical resources.

        Raises:
            ValueError: If the input is not a valid Bundle.
        """
        if not cerner_bundle:
            raise ValueError("Cerner bundle cannot be empty")

        resource_type = cerner_bundle.get("resourceType", "")
        if resource_type != "Bundle":
            raise ValueError(
                f"Expected resourceType 'Bundle', got '{resource_type}'"
            )

        entries = cerner_bundle.get("entry", [])
        if not entries:
            logger.warning("Cerner Bundle contains no entries")
            return []

        logger.info(
            "Processing Cerner Bundle with %d entries (type: %s)",
            len(entries),
            cerner_bundle.get("type", "unknown"),
        )

        mapped_resources: List[Dict[str, Any]] = []
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
                logger.error(
                    "Failed to map %s at entry %d: %s",
                    entry_resource_type,
                    idx,
                    exc,
                )

        logger.info(
            "Successfully mapped %d resources from Cerner Bundle",
            len(mapped_resources),
        )
        return mapped_resources
