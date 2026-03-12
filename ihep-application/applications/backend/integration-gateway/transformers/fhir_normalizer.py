"""
FHIR Resource Normalizer

Transforms vendor-specific FHIR R4 resources into the IHEP canonical format.
Handles extension processing, code system normalization, identifier
standardization, and resource validation.

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import copy
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import jsonschema

logger = logging.getLogger(__name__)

CODE_SYSTEMS = {
    "loinc": "http://loinc.org",
    "snomed": "http://snomed.info/sct",
    "icd10": "http://hl7.org/fhir/sid/icd-10-cm",
    "rxnorm": "http://www.nlm.nih.gov/research/umls/rxnorm",
    "cpt": "http://www.ama-assn.org/go/cpt",
    "ucum": "http://unitsofmeasure.org",
}

_VENDOR_EXTENSION_PREFIXES = (
    "http://open.epic.com/",
    "http://fhir.epic.com/",
    "https://fhir.cerner.com/",
    "http://cerner.com/",
    "http://oracle.com/fhir/",
    "http://allscripts.com/",
    "http://athenahealth.com/",
)

_IHEP_EXTENSION_NS = "https://ihep.app/fhir/extensions"
_SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")


class FHIRNormalizer:
    """Normalizes vendor-specific FHIR R4 resources to IHEP canonical format."""

    def __init__(self, schemas_dir: Optional[str] = None) -> None:
        self._schemas_dir = schemas_dir or _SCHEMAS_DIR
        self._schemas: Dict[str, dict] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        if not os.path.isdir(self._schemas_dir):
            return
        for filename in os.listdir(self._schemas_dir):
            if filename.endswith(".json"):
                resource_type = filename.replace(".schema.json", "").replace(".json", "")
                filepath = os.path.join(self._schemas_dir, filename)
                try:
                    with open(filepath, "r") as fh:
                        self._schemas[resource_type] = json.load(fh)
                except Exception as e:
                    logger.warning("Failed to load schema %s: %s", filepath, e)

    def normalize(
        self, resource: Dict[str, Any], vendor: str = "generic", preserve_raw: bool = False,
    ) -> Dict[str, Any]:
        if not resource or not isinstance(resource, dict):
            return resource

        normalized = copy.deepcopy(resource)
        resource_type = normalized.get("resourceType", "")

        normalized = self._normalize_extensions(normalized, vendor)
        normalized = self._normalize_code_systems(normalized)
        normalized = self._normalize_identifiers(normalized, vendor)
        normalized = self._normalize_datetimes(normalized)

        if resource_type == "Patient":
            normalized = self._normalize_patient(normalized)
        if resource_type == "Observation":
            normalized = self._normalize_observation(normalized)

        normalized["meta"] = normalized.get("meta", {})
        normalized["meta"]["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
        normalized["meta"]["source"] = f"integration-gateway/{vendor}"
        normalized["meta"].setdefault("profile", [])
        ihep_profile = f"{_IHEP_EXTENSION_NS}/{resource_type}"
        if ihep_profile not in normalized["meta"]["profile"]:
            normalized["meta"]["profile"].append(ihep_profile)

        if preserve_raw:
            normalized["_vendor_raw"] = resource

        keys_to_remove = [k for k in normalized if k.startswith("_") and k != "_vendor_raw"]
        for key in keys_to_remove:
            del normalized[key]

        return normalized

    def normalize_bundle(self, resources: List[Dict[str, Any]], vendor: str = "generic") -> List[Dict[str, Any]]:
        return [self.normalize(r, vendor=vendor) for r in resources]

    def _normalize_extensions(self, resource: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        extensions = resource.get("extension", [])
        if not extensions:
            return resource

        ihep_extensions: Dict[str, Any] = {}
        standard_extensions: List[Dict[str, Any]] = []

        for ext in extensions:
            url = ext.get("url", "")
            is_vendor = any(url.startswith(prefix) for prefix in _VENDOR_EXTENSION_PREFIXES)
            if is_vendor:
                short_name = url.rsplit("/", 1)[-1]
                value = self._extract_extension_value(ext)
                ihep_extensions[short_name] = value
                ihep_ext = dict(ext)
                ihep_ext["url"] = f"{_IHEP_EXTENSION_NS}/{vendor}/{short_name}"
                standard_extensions.append(ihep_ext)
            else:
                standard_extensions.append(ext)

        resource["extension"] = standard_extensions
        return resource

    @staticmethod
    def _extract_extension_value(ext: Dict[str, Any]) -> Any:
        for key in ("valueString", "valueCode", "valueBoolean", "valueInteger",
                     "valueDecimal", "valueDateTime", "valueDate", "valueReference",
                     "valueCoding", "valueCodeableConcept", "valueQuantity"):
            if key in ext:
                return ext[key]
        return None

    def _normalize_code_systems(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        return self._walk_and_normalize_codings(resource)

    def _walk_and_normalize_codings(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            if "system" in obj and "code" in obj:
                obj["system"] = self._canonical_system(obj["system"])
            for key, value in obj.items():
                obj[key] = self._walk_and_normalize_codings(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._walk_and_normalize_codings(item)
        return obj

    @staticmethod
    def _canonical_system(system: str) -> str:
        if not system:
            return system
        system_lower = system.lower().strip()
        if any(v in system_lower for v in ("loinc", "urn:oid:2.16.840.1.113883.6.1")):
            return CODE_SYSTEMS["loinc"]
        if any(v in system_lower for v in ("snomed", "sct", "urn:oid:2.16.840.1.113883.6.96")):
            return CODE_SYSTEMS["snomed"]
        if any(v in system_lower for v in ("icd-10", "icd10", "urn:oid:2.16.840.1.113883.6.90")):
            return CODE_SYSTEMS["icd10"]
        if any(v in system_lower for v in ("rxnorm", "urn:oid:2.16.840.1.113883.6.88")):
            return CODE_SYSTEMS["rxnorm"]
        return system

    def _normalize_identifiers(self, resource: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        identifiers = resource.get("identifier", [])
        if not identifiers:
            return resource
        seen: Set[Tuple[str, str]] = set()
        normalized_ids: List[Dict[str, Any]] = []
        for ident in identifiers:
            system = ident.get("system", f"urn:oid:{vendor}")
            value = ident.get("value", "")
            if not value:
                continue
            key = (system, value)
            if key in seen:
                continue
            seen.add(key)
            ident["system"] = system
            normalized_ids.append(ident)
        resource["identifier"] = normalized_ids
        return resource

    def _normalize_datetimes(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        dt_fields = (
            "birthDate", "effectiveDateTime", "issued", "start", "end",
            "authoredOn", "recordedDate", "onsetDateTime", "abatementDateTime",
        )
        for f in dt_fields:
            if f in resource and isinstance(resource[f], str):
                resource[f] = self._normalize_datetime_str(resource[f])
        for f in ("effectivePeriod", "period"):
            if f in resource and isinstance(resource[f], dict):
                for sub in ("start", "end"):
                    if sub in resource[f] and isinstance(resource[f][sub], str):
                        resource[f][sub] = self._normalize_datetime_str(resource[f][sub])
        return resource

    @staticmethod
    def _normalize_datetime_str(dt_str: str) -> str:
        if not dt_str or not dt_str.strip():
            return dt_str
        dt_str = dt_str.strip()
        if "T" in dt_str and (dt_str.endswith("Z") or "+" in dt_str[10:]):
            return dt_str
        formats = [
            ("%Y%m%d%H%M%S", "%Y-%m-%dT%H:%M:%SZ"),
            ("%Y%m%d", "%Y-%m-%d"),
            ("%m/%d/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"),
            ("%m/%d/%Y", "%Y-%m-%d"),
            ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"),
            ("%Y-%m-%d", "%Y-%m-%d"),
        ]
        for in_fmt, out_fmt in formats:
            try:
                dt = datetime.strptime(dt_str[:len(datetime.now().strftime(in_fmt))], in_fmt)
                return dt.strftime(out_fmt)
            except (ValueError, TypeError):
                continue
        return dt_str

    def _normalize_patient(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        for name in patient.get("name", []):
            if "given" in name and isinstance(name["given"], str):
                name["given"] = [name["given"]]
            if "given" in name:
                name["given"] = [g for g in name["given"] if g]
            name.setdefault("use", "official")

        gender = patient.get("gender", "")
        gender_map = {"m": "male", "f": "female", "o": "other", "u": "unknown",
                       "male": "male", "female": "female", "other": "other", "unknown": "unknown"}
        patient["gender"] = gender_map.get(gender.lower(), "unknown") if gender else "unknown"

        patient["telecom"] = [t for t in patient.get("telecom", []) if t.get("value")]
        return patient

    def _normalize_observation(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        if not observation.get("category"):
            observation["category"] = [{
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory", "display": "Laboratory"}],
            }]

        status_map = {"f": "final", "p": "preliminary", "c": "corrected", "a": "amended",
                       "final": "final", "preliminary": "preliminary", "registered": "registered",
                       "corrected": "corrected", "amended": "amended"}
        raw_status = observation.get("status", "final").lower()
        observation["status"] = status_map.get(raw_status, "final")
        return observation

    def validate(self, resource: Dict[str, Any], resource_type: Optional[str] = None) -> List[str]:
        rtype = resource_type or resource.get("resourceType", "")
        if not rtype:
            return ["Missing resourceType"]
        schema = self._schemas.get(rtype)
        if not schema:
            return []
        errors: List[str] = []
        try:
            validator = jsonschema.Draft7Validator(schema)
            for error in validator.iter_errors(resource):
                path = " -> ".join(str(p) for p in error.absolute_path)
                errors.append(f"{path}: {error.message}" if path else error.message)
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")
        return errors

    def is_valid(self, resource: Dict[str, Any], resource_type: Optional[str] = None) -> bool:
        return len(self.validate(resource, resource_type)) == 0
