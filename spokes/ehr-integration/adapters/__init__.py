"""
EHR Adapter Registry

Provides a central registry that maps vendor names to their concrete adapter
implementations. The factory method ``get_adapter`` instantiates the correct
adapter for a given EHR vendor, allowing the rest of the spoke to remain
vendor-agnostic.
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
    """
    Central registry of EHR vendor adapters.

    Each vendor name (case-insensitive) is mapped to a concrete
    ``BaseEHRAdapter`` subclass.  Calling ``get_adapter`` returns a *new*
    instance of the appropriate adapter, ready to be configured with
    partner-specific credentials via ``adapter.configure(partner_config)``.

    Usage::

        registry = AdapterRegistry()
        adapter = registry.get_adapter('epic')
        adapter.configure(partner_config_dict)
        patient = adapter.fetch_patient('patient-123')
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, Type[BaseEHRAdapter]] = {}
        self._register_defaults()

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------

    def _register_defaults(self) -> None:
        """Register all built-in vendor adapters."""
        self.register('epic', EpicAdapter)
        self.register('cerner', CernerAdapter)
        self.register('oracle_health', CernerAdapter)  # Cerner rebranded
        self.register('allscripts', AllscriptsAdapter)
        self.register('athena', AthenaAdapter)
        self.register('athenahealth', AthenaAdapter)
        self.register('hl7v2', HL7v2Adapter)
        self.register('hl7', HL7v2Adapter)

        logger.info(
            "Adapter registry initialised with %d vendor mappings",
            len(self._adapters),
        )

    def register(self, vendor_name: str, adapter_class: Type[BaseEHRAdapter]) -> None:
        """
        Register an adapter class for a vendor name.

        Args:
            vendor_name: Case-insensitive vendor identifier (e.g. ``'epic'``).
            adapter_class: A concrete subclass of ``BaseEHRAdapter``.

        Raises:
            TypeError: If *adapter_class* is not a subclass of ``BaseEHRAdapter``.
        """
        if not (isinstance(adapter_class, type) and issubclass(adapter_class, BaseEHRAdapter)):
            raise TypeError(
                f"adapter_class must be a subclass of BaseEHRAdapter, "
                f"got {adapter_class!r}"
            )
        key = vendor_name.strip().lower()
        self._adapters[key] = adapter_class
        logger.debug("Registered adapter '%s' -> %s", key, adapter_class.__name__)

    def unregister(self, vendor_name: str) -> bool:
        """
        Remove a vendor adapter from the registry.

        Returns:
            True if the adapter was found and removed, False otherwise.
        """
        key = vendor_name.strip().lower()
        if key in self._adapters:
            del self._adapters[key]
            logger.debug("Unregistered adapter '%s'", key)
            return True
        return False

    # ------------------------------------------------------------------
    # Factory method
    # ------------------------------------------------------------------

    def get_adapter(self, vendor_name: str) -> Optional[BaseEHRAdapter]:
        """
        Create and return a new adapter instance for *vendor_name*.

        Args:
            vendor_name: Case-insensitive vendor identifier.

        Returns:
            A new ``BaseEHRAdapter`` subclass instance, or ``None`` if no
            adapter is registered for the given vendor.
        """
        if not vendor_name:
            logger.warning("get_adapter called with empty vendor_name")
            return None

        key = vendor_name.strip().lower()
        adapter_class = self._adapters.get(key)

        if adapter_class is None:
            logger.warning("No adapter registered for vendor '%s'", vendor_name)
            return None

        try:
            instance = adapter_class()
            logger.debug("Created adapter instance for vendor '%s': %s", key, type(instance).__name__)
            return instance
        except Exception as e:
            logger.error(
                "Failed to instantiate adapter for vendor '%s': %s: %s",
                vendor_name, type(e).__name__, e,
            )
            return None

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_vendors(self) -> list:
        """Return a sorted list of registered vendor names."""
        return sorted(self._adapters.keys())

    def has_vendor(self, vendor_name: str) -> bool:
        """Return True if an adapter is registered for *vendor_name*."""
        return vendor_name.strip().lower() in self._adapters

    def __contains__(self, vendor_name: str) -> bool:
        return self.has_vendor(vendor_name)

    def __len__(self) -> int:
        return len(self._adapters)

    def __repr__(self) -> str:
        vendors = ', '.join(self.list_vendors())
        return f"<AdapterRegistry vendors=[{vendors}]>"
