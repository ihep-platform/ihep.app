# IHEP FHIR Mapping Package
# =============================================================================
# Provides EHR vendor-specific FHIR resource mappers that transform vendor
# FHIR R4 (or proprietary) responses into the canonical IHEP resource format.
#
# Supported EHR Vendors:
#   - Epic (epic_to_ihep.py)       -- Epic FHIR R4 / MyChart
#   - Cerner (cerner_to_ihep.py)   -- Cerner Millennium FHIR R4
#   - Allscripts (allscripts_to_ihep.py) -- Allscripts Unity API
#   - athenahealth (athena_to_ihep.py)   -- athenahealth Marketplace API
#
# Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
# Co-Author: Claude by Anthropic
# =============================================================================

from data.fhir_mappings.epic_to_ihep import EpicToIHEPMapper
from data.fhir_mappings.cerner_to_ihep import CernerToIHEPMapper
from data.fhir_mappings.allscripts_to_ihep import AllscriptsToIHEPMapper
from data.fhir_mappings.athena_to_ihep import AthenaToIHEPMapper

__all__ = [
    "EpicToIHEPMapper",
    "CernerToIHEPMapper",
    "AllscriptsToIHEPMapper",
    "AthenaToIHEPMapper",
]

# Mapper registry for dynamic vendor resolution
MAPPER_REGISTRY = {
    "epic": EpicToIHEPMapper,
    "cerner": CernerToIHEPMapper,
    "allscripts": AllscriptsToIHEPMapper,
    "athenahealth": AthenaToIHEPMapper,
}


def get_mapper(vendor: str):
    """Return an instantiated mapper for the specified EHR vendor.

    Args:
        vendor: Lowercase vendor identifier (epic, cerner, allscripts, athenahealth).

    Returns:
        An instance of the appropriate mapper class.

    Raises:
        ValueError: If the vendor is not supported.
    """
    vendor_key = vendor.lower().strip()
    if vendor_key not in MAPPER_REGISTRY:
        supported = ", ".join(sorted(MAPPER_REGISTRY.keys()))
        raise ValueError(
            f"Unsupported EHR vendor '{vendor}'. Supported vendors: {supported}"
        )
    return MAPPER_REGISTRY[vendor_key]()
