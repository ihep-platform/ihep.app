"""
Abstract Base EHR Adapter

Defines the interface all vendor-specific EHR adapters must implement.

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseEHRAdapter(ABC):
    """Abstract base class for EHR system adapters."""

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._authenticated: bool = False
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self.logger = logging.getLogger(f"{__name__}.{type(self).__name__}")

    def configure(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._authenticated = False
        self._access_token = None
        self._token_expiry = None

    @abstractmethod
    def authenticate(self) -> bool: ...

    @abstractmethod
    def fetch_patient(self, patient_id: str) -> Dict[str, Any]: ...

    @abstractmethod
    def fetch_observations(
        self, patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        observation_codes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def push_observation(self, patient_id: str, observation: Dict[str, Any]) -> bool: ...

    @abstractmethod
    def subscribe_to_events(self, event_types: List[str], webhook_url: str) -> str: ...

    @abstractmethod
    def validate_connection(self) -> bool: ...

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]: ...

    def _ensure_authenticated(self) -> None:
        if self._authenticated and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return
        if not self.authenticate():
            raise ConnectionError("Authentication with EHR system failed")

    def _build_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers
