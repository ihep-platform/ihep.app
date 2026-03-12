"""
FHIR Resource Normalizer

Transforms vendor-specific FHIR R4 resources into the IHEP canonical
format. Handles differences across Epic, Cerner, Allscripts, athenahealth,
and HL7 v2.x-derived resources, including:

- Extension processing and flattening
- Code system normalization (LOINC, SNOMED CT, ICD-10)
- Identifier standardization
- Resource validation against JSON schemas
"""

import copy
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import jsonschema

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Code system URIs
# ---------------------------------------------------------------------------

CODE_SYSTEMS = {
    'loinc': 'http://loinc.org',
    'snomed': 'http://snomed.info/sct',
    'icd10': 'http://hl7.org/fhir/sid/icd-10-cm',
    'icd10_who': 'http://hl7.org/fhir/sid/icd-10',
    'rxnorm': 'http://www.nlm.nih.gov/research/umls/rxnorm',
    'cpt': 'http://www.ama-assn.org/go/cpt',
    'ndc': 'http://hl7.org/fhir/sid/ndc',
    'cvx': 'http://hl7.org/fhir/sid/cvx',
    'ucum': 'http://unitsofmeasure.org',
}

# Known vendor extension URL prefixes to strip during normalization
_VENDOR_EXTENSION_PREFIXES = (
    'http://open.epic.com/',
    'http://fhir.epic.com/',
    'https://fhir.cerner.com/',
    'http://cerner.com/',
    'http://oracle.com/fhir/',
    'http://allscripts.com/',
    'http://athenahealth.com/',
)

# IHEP canonical extension namespace
_IHEP_EXTENSION_NS = 'https://ihep.app/fhir/extensions'

# Default resource schemas directory
_SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), '..', 'schemas')


# ---------------------------------------------------------------------------
# FHIR Normalizer
# ---------------------------------------------------------------------------

class FHIRNormalizer:
    """
    Normalizes vendor-specific FHIR R4 resources into the IHEP canonical format.

    The normalizer applies the following transformations in order:
    1. Vendor extension extraction and remapping
    2. Code system normalization (ensure standard URIs)
    3. Identifier deduplication and standardization
    4. Date format normalization to ISO 8601
    5. Name and address structure normalization
    6. Optional validation against JSON Schema

    Usage::

        normalizer = FHIRNormalizer()
        canonical = normalizer.normalize(epic_patient, vendor='epic')
        errors = normalizer.validate(canonical, 'Patient')
    """

    def __init__(self, schemas_dir: Optional[str] = None) -> None:
        self._schemas_dir = schemas_dir or _SCHEMAS_DIR
        self._schemas: Dict[str, dict] = {}
        self._load_schemas()

    # ------------------------------------------------------------------
    # Schema loading
    # ------------------------------------------------------------------

    def _load_schemas(self) -> None:
        """Load JSON Schema files from the schemas directory."""
        if not os.path.isdir(self._schemas_dir):
            logger.debug("Schemas directory not found: %s; validation will be skipped", self._schemas_dir)
            return

        for filename in os.listdir(self._schemas_dir):
            if filename.endswith('.json'):
                resource_type = filename.replace('.schema.json', '').replace('.json', '')
                filepath = os.path.join(self._schemas_dir, filename)
                try:
                    with open(filepath, 'r') as fh:
                        self._schemas[resource_type] = json.load(fh)
                    logger.debug("Loaded schema for %s", resource_type)
                except Exception as e:
                    logger.warning("Failed to load schema %s: %s", filepath, e)

    # ------------------------------------------------------------------
    # Main normalization entry point
    # ------------------------------------------------------------------

    def normalize(
        self,
        resource: Dict[str, Any],
        vendor: str = 'generic',
        preserve_raw: bool = False,
    ) -> Dict[str, Any]:
        """
        Normalize a vendor-specific FHIR R4 resource to IHEP canonical format.

        Args:
            resource: The FHIR R4 resource dictionary.
            vendor: The vendor identifier (``'epic'``, ``'cerner'``,
                    ``'allscripts'``, ``'athenahealth'``, ``'hl7v2'``).
            preserve_raw: If True, the original vendor resource is stored
                          under ``_vendor_raw`` in the output.

        Returns:
            A normalized FHIR R4 resource dictionary with IHEP canonical
            extensions and standardized coding.
        """
        if not resource or not isinstance(resource, dict):
            logger.warning("normalize() called with empty or non-dict resource")
            return resource

        # Work on a deep copy to avoid mutating the input
        normalized = copy.deepcopy(resource)

        # Determine resource type
        resource_type = normalized.get('resourceType', '')

        # Step 1: Extract and remap vendor extensions
        normalized = self._normalize_extensions(normalized, vendor)

        # Step 2: Normalize code systems
        normalized = self._normalize_code_systems(normalized)

        # Step 3: Standardize identifiers
        normalized = self._normalize_identifiers(normalized, vendor)

        # Step 4: Normalize datetime fields
        normalized = self._normalize_datetimes(normalized)

        # Step 5: Normalize names
        if resource_type == 'Patient':
            normalized = self._normalize_patient(normalized)

        # Step 6: Normalize observations
        if resource_type == 'Observation':
            normalized = self._normalize_observation(normalized)

        # Add IHEP metadata
        normalized['meta'] = normalized.get('meta', {})
        normalized['meta']['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        normalized['meta']['source'] = f'ehr-integration/{vendor}'
        normalized['meta'].setdefault('profile', [])
        ihep_profile = f'{_IHEP_EXTENSION_NS}/{resource_type}'
        if ihep_profile not in normalized['meta']['profile']:
            normalized['meta']['profile'].append(ihep_profile)

        # Preserve raw vendor data if requested
        if preserve_raw:
            normalized['_vendor_raw'] = resource

        # Remove vendor-specific private keys (those starting with _)
        keys_to_remove = [k for k in normalized if k.startswith('_') and k not in ('_vendor_raw',)]
        for key in keys_to_remove:
            del normalized[key]

        return normalized

    def normalize_bundle(
        self,
        resources: List[Dict[str, Any]],
        vendor: str = 'generic',
    ) -> List[Dict[str, Any]]:
        """
        Normalize a list of FHIR resources.

        Args:
            resources: List of FHIR resource dictionaries.
            vendor: Vendor identifier.

        Returns:
            List of normalized resources.
        """
        return [self.normalize(r, vendor=vendor) for r in resources]

    # ------------------------------------------------------------------
    # Extension normalization
    # ------------------------------------------------------------------

    def _normalize_extensions(self, resource: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        """
        Extract vendor-specific extensions and remap to IHEP namespace.

        Vendor extensions are moved from the standard ``extension`` array
        into an ``_ihep_extensions`` dictionary for easy programmatic
        access, and the original vendor extension URLs are replaced with
        IHEP-namespaced equivalents.
        """
        extensions = resource.get('extension', [])
        if not extensions:
            return resource

        ihep_extensions: Dict[str, Any] = {}
        standard_extensions: List[Dict[str, Any]] = []

        for ext in extensions:
            url = ext.get('url', '')

            is_vendor = any(url.startswith(prefix) for prefix in _VENDOR_EXTENSION_PREFIXES)

            if is_vendor:
                # Remap to IHEP namespace
                short_name = url.rsplit('/', 1)[-1]
                value = self._extract_extension_value(ext)
                ihep_extensions[short_name] = value

                # Create IHEP-namespaced copy
                ihep_ext = dict(ext)
                ihep_ext['url'] = f'{_IHEP_EXTENSION_NS}/{vendor}/{short_name}'
                standard_extensions.append(ihep_ext)
            else:
                standard_extensions.append(ext)

        resource['extension'] = standard_extensions

        # Store extracted extensions for easy access
        if ihep_extensions:
            resource.setdefault('_ihep_vendor_extensions', {})
            resource['_ihep_vendor_extensions'].update(ihep_extensions)

        return resource

    @staticmethod
    def _extract_extension_value(ext: Dict[str, Any]) -> Any:
        """Extract the value from a FHIR extension, regardless of type."""
        for key in ('valueString', 'valueCode', 'valueBoolean', 'valueInteger',
                    'valueDecimal', 'valueDateTime', 'valueDate', 'valueReference',
                    'valueCoding', 'valueCodeableConcept', 'valueQuantity',
                    'valuePeriod', 'valueIdentifier', 'valueUri'):
            if key in ext:
                return ext[key]
        return None

    # ------------------------------------------------------------------
    # Code system normalization
    # ------------------------------------------------------------------

    def _normalize_code_systems(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively normalize code system URIs throughout the resource.

        Ensures that coding elements use the canonical URIs defined in
        ``CODE_SYSTEMS`` rather than vendor-specific alternatives.
        """
        return self._walk_and_normalize_codings(resource)

    def _walk_and_normalize_codings(self, obj: Any) -> Any:
        """Recursively walk a structure and normalize coding elements."""
        if isinstance(obj, dict):
            # If this dict looks like a coding element, normalize its system
            if 'system' in obj and 'code' in obj:
                obj['system'] = self._canonical_system(obj['system'])

            # Recurse into values
            for key, value in obj.items():
                obj[key] = self._walk_and_normalize_codings(value)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._walk_and_normalize_codings(item)

        return obj

    @staticmethod
    def _canonical_system(system: str) -> str:
        """Map a possibly non-standard code system URI to its canonical form."""
        if not system:
            return system

        system_lower = system.lower().strip()

        # Map common variants to canonical URIs
        loinc_variants = ('loinc', 'http://loinc.org', 'urn:oid:2.16.840.1.113883.6.1')
        if any(v in system_lower for v in loinc_variants):
            return CODE_SYSTEMS['loinc']

        snomed_variants = ('snomed', 'sct', 'http://snomed.info/sct', 'urn:oid:2.16.840.1.113883.6.96')
        if any(v in system_lower for v in snomed_variants):
            return CODE_SYSTEMS['snomed']

        icd10_variants = ('icd-10', 'icd10', 'urn:oid:2.16.840.1.113883.6.90')
        if any(v in system_lower for v in icd10_variants):
            return CODE_SYSTEMS['icd10']

        rxnorm_variants = ('rxnorm', 'urn:oid:2.16.840.1.113883.6.88')
        if any(v in system_lower for v in rxnorm_variants):
            return CODE_SYSTEMS['rxnorm']

        return system

    # ------------------------------------------------------------------
    # Identifier normalization
    # ------------------------------------------------------------------

    def _normalize_identifiers(self, resource: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        """
        Standardize the ``identifier`` array.

        Ensures each identifier has a ``system`` and ``value``, deduplicates
        entries, and adds the vendor as the source system when missing.
        """
        identifiers = resource.get('identifier', [])
        if not identifiers:
            return resource

        seen: Set[Tuple[str, str]] = set()
        normalized_ids: List[Dict[str, Any]] = []

        for ident in identifiers:
            system = ident.get('system', f'urn:oid:{vendor}')
            value = ident.get('value', '')

            if not value:
                continue

            key = (system, value)
            if key in seen:
                continue
            seen.add(key)

            ident['system'] = system
            normalized_ids.append(ident)

        resource['identifier'] = normalized_ids
        return resource

    # ------------------------------------------------------------------
    # DateTime normalization
    # ------------------------------------------------------------------

    def _normalize_datetimes(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all date/datetime fields use ISO 8601 format with timezone.

        Handles common non-standard formats from various EHR systems.
        """
        datetime_fields = (
            'birthDate', 'effectiveDateTime', 'effectivePeriod',
            'issued', 'start', 'end', 'authoredOn', 'recordedDate',
            'onsetDateTime', 'abatementDateTime', 'lastUpdated',
        )

        for field in datetime_fields:
            if field in resource and isinstance(resource[field], str):
                resource[field] = self._normalize_datetime_str(resource[field])

        # Handle nested period objects
        for field in ('effectivePeriod', 'period'):
            if field in resource and isinstance(resource[field], dict):
                for sub_field in ('start', 'end'):
                    if sub_field in resource[field] and isinstance(resource[field][sub_field], str):
                        resource[field][sub_field] = self._normalize_datetime_str(
                            resource[field][sub_field]
                        )

        return resource

    @staticmethod
    def _normalize_datetime_str(dt_str: str) -> str:
        """
        Normalize a datetime string to ISO 8601 format.

        Handles formats like:
        - ``20240115`` -> ``2024-01-15``
        - ``01/15/2024`` -> ``2024-01-15``
        - ``2024-01-15T10:30:00`` -> ``2024-01-15T10:30:00Z``
        """
        if not dt_str or not dt_str.strip():
            return dt_str

        dt_str = dt_str.strip()

        # Already properly formatted
        if 'T' in dt_str and (dt_str.endswith('Z') or '+' in dt_str[10:]):
            return dt_str

        formats_to_try = [
            ('%Y%m%d%H%M%S', '%Y-%m-%dT%H:%M:%SZ'),
            ('%Y%m%d%H%M', '%Y-%m-%dT%H:%M:00Z'),
            ('%Y%m%d', '%Y-%m-%d'),
            ('%m/%d/%Y %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'),
            ('%m/%d/%Y %H:%M', '%Y-%m-%dT%H:%M:00Z'),
            ('%m/%d/%Y', '%Y-%m-%d'),
            ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'),
            ('%Y-%m-%d', '%Y-%m-%d'),
        ]

        for in_fmt, out_fmt in formats_to_try:
            try:
                dt = datetime.strptime(dt_str[:len(datetime.now().strftime(in_fmt))], in_fmt)
                return dt.strftime(out_fmt)
            except (ValueError, TypeError):
                continue

        # Return as-is if we cannot parse
        return dt_str

    # ------------------------------------------------------------------
    # Resource-specific normalization
    # ------------------------------------------------------------------

    def _normalize_patient(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Patient-specific normalization rules."""
        # Ensure name array has proper structure
        names = patient.get('name', [])
        for name in names:
            # Ensure 'given' is always a list
            if 'given' in name and isinstance(name['given'], str):
                name['given'] = [name['given']]
            # Remove empty string entries
            if 'given' in name:
                name['given'] = [g for g in name['given'] if g]
            # Ensure 'use' is set
            name.setdefault('use', 'official')

        # Normalize gender
        gender = patient.get('gender', '')
        gender_map = {
            'm': 'male', 'f': 'female', 'o': 'other', 'u': 'unknown',
            'male': 'male', 'female': 'female', 'other': 'other',
            'unknown': 'unknown', 'undifferentiated': 'other',
        }
        patient['gender'] = gender_map.get(gender.lower(), 'unknown') if gender else 'unknown'

        # Ensure telecom items have system and use
        for telecom in patient.get('telecom', []):
            telecom.setdefault('system', 'phone')
            telecom.setdefault('use', 'home')
            # Remove empty value entries
            if not telecom.get('value'):
                continue

        # Filter out empty telecom entries
        patient['telecom'] = [t for t in patient.get('telecom', []) if t.get('value')]

        return patient

    def _normalize_observation(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Observation-specific normalization rules."""
        # Ensure category is present with standard coding
        categories = observation.get('category', [])
        if not categories:
            # Infer category from code system if possible
            code = observation.get('code', {})
            codings = code.get('coding', [])
            inferred_category = 'laboratory'  # default
            for coding in codings:
                system = coding.get('system', '')
                if system == CODE_SYSTEMS['loinc']:
                    # Vital signs LOINC codes start with certain prefixes
                    loinc_code = coding.get('code', '')
                    vital_signs_codes = {
                        '8867-4', '8310-5', '8462-4', '8480-6', '8302-2',
                        '29463-7', '59408-5', '9279-1', '2708-6',
                    }
                    if loinc_code in vital_signs_codes:
                        inferred_category = 'vital-signs'
                        break

            observation['category'] = [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': inferred_category,
                    'display': inferred_category.replace('-', ' ').title(),
                }],
            }]

        # Normalize status values
        status_map = {
            'f': 'final', 'p': 'preliminary', 'c': 'corrected',
            'a': 'amended', 'cancelled': 'cancelled', 'entered-in-error': 'entered-in-error',
            'final': 'final', 'preliminary': 'preliminary', 'registered': 'registered',
            'corrected': 'corrected', 'amended': 'amended',
        }
        raw_status = observation.get('status', 'final').lower()
        observation['status'] = status_map.get(raw_status, 'final')

        return observation

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(
        self, resource: Dict[str, Any], resource_type: Optional[str] = None
    ) -> List[str]:
        """
        Validate a FHIR resource against its JSON Schema.

        Args:
            resource: The FHIR resource dictionary to validate.
            resource_type: Override the resource type for schema lookup.

        Returns:
            A list of validation error messages. An empty list indicates
            the resource is valid.
        """
        rtype = resource_type or resource.get('resourceType', '')
        if not rtype:
            return ['Missing resourceType']

        schema = self._schemas.get(rtype)
        if not schema:
            logger.debug("No schema available for %s; skipping validation", rtype)
            return []

        errors: List[str] = []
        try:
            validator = jsonschema.Draft7Validator(schema)
            for error in validator.iter_errors(resource):
                path = ' -> '.join(str(p) for p in error.absolute_path)
                errors.append(f"{path}: {error.message}" if path else error.message)
        except jsonschema.SchemaError as e:
            logger.error("Invalid JSON Schema for %s: %s", rtype, e)
            errors.append(f"Schema error: {e.message}")

        return errors

    def is_valid(self, resource: Dict[str, Any], resource_type: Optional[str] = None) -> bool:
        """Return True if the resource passes schema validation."""
        return len(self.validate(resource, resource_type)) == 0
