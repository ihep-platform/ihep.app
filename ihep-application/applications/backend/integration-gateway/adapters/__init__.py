"""
EHR Adapter Registry

Maps vendor names to concrete adapter implementations, allowing the gateway
to remain vendor-agnostic when processing inbound/outbound data.

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import logging
from typing import Dict, Optional, Type

from adapters.base_adapter import BaseEHRAdapter
from adapters.epic_adapter import EpicAdapter
from adapters.cerner_adapter import CernerAdapter
from adapters.allscripts_adapter import AllscriptsAdapter
from adapters.athena_adapter import AthenaAdapter
from adapters.hl7v2_adapter import HL7v2Adapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """Central registry of EHR vendor adapters."""

    def __init__(self) -> None:
        self._adapters: Dict[str, Type[BaseEHRAdapter]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register("epic", EpicAdapter)
        self.register("cerner", CernerAdapter)
        self.register("oracle_health", CernerAdapter)
        self.register("allscripts", AllscriptsAdapter)
        self.register("athena", AthenaAdapter)
        self.register("athenahealth", AthenaAdapter)
        self.register("hl7v2", HL7v2Adapter)
        self.register("hl7", HL7v2Adapter)
        logger.info("Adapter registry initialised with %d vendor mappings", len(self._adapters))

    def register(self, vendor_name: str, adapter_class: Type[BaseEHRAdapter]) -> None:
        if not (isinstance(adapter_class, type) and issubclass(adapter_class, BaseEHRAdapter)):
            raise TypeError(f"adapter_class must subclass BaseEHRAdapter, got {adapter_class!r}")
        self._adapters[vendor_name.strip().lower()] = adapter_class

    def get_adapter(self, vendor_name: str) -> Optional[BaseEHRAdapter]:
        if not vendor_name:
            return None
        key = vendor_name.strip().lower()
        adapter_class = self._adapters.get(key)
        if adapter_class is None:
            logger.warning("No adapter registered for vendor '%s'", vendor_name)
            return None
        try:
            return adapter_class()
        except Exception as e:
            logger.error("Failed to instantiate adapter for '%s': %s", vendor_name, e)
            return None

    def list_vendors(self) -> list:
        return sorted(self._adapters.keys())

    def has_vendor(self, vendor_name: str) -> bool:
        return vendor_name.strip().lower() in self._adapters
