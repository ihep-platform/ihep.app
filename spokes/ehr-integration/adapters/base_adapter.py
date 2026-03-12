"""
Abstract Base EHR Adapter

Defines the contract that all vendor-specific EHR adapters must implement.
Each method maps to a core integration capability (authentication, patient
data retrieval, observation read/write, appointment listing, care plan
access, event subscription, and connection health).
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseEHRAdapter(ABC):
    """
    Abstract base class for Electronic Health Record system adapters.

    Subclasses implement vendor-specific logic for authentication, FHIR/REST
    data retrieval, and event subscription.  All public methods include full
    type hints and raise ``NotImplementedError`` if the vendor does not
    support a particular capability.

    Typical lifecycle::

        adapter = EpicAdapter()
        adapter.configure(partner_config)   # inject credentials / URLs
        adapter.authenticate()              # obtain access token
        patient = adapter.fetch_patient('12345')
    """

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._authenticated: bool = False
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self.logger = logging.getLogger(f"{__name__}.{type(self).__name__}")

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Inject partner-specific configuration into the adapter.

        The *config* dictionary typically contains keys such as ``base_url``,
        ``client_id``, ``client_secret``, ``scopes``, and vendor-specific
        extensions.  Subclasses may override this method to perform
        additional validation.

        Args:
            config: Partner configuration dictionary.
        """
        self._config = config
        self._authenticated = False
        self._access_token = None
        self._token_expiry = None
        self.logger.debug("Adapter configured for partner '%s'", config.get('partner_id', 'unknown'))

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Perform authentication with the EHR system.

        Implementations should obtain an access token (e.g. via OAuth 2.0)
        and store it internally so that subsequent API calls can use it.
        Token refresh logic should be handled transparently.

        Returns:
            True if authentication succeeded, False otherwise.

        Raises:
            ConnectionError: If the EHR system is unreachable.
            ValueError: If required credentials are missing from config.
        """
        ...

    # ------------------------------------------------------------------
    # Patient data
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch_patient(self, patient_id: str) -> Dict[str, Any]:
        """
        Retrieve a FHIR R4 Patient resource by identifier.

        Args:
            patient_id: The patient's identifier within the EHR system.
                        This may be a FHIR logical id or a system-specific
                        MRN depending on the vendor.

        Returns:
            A dictionary representing the FHIR R4 Patient resource,
            including ``resourceType``, ``id``, ``name``, ``birthDate``,
            ``gender``, ``address``, ``telecom``, and any vendor-specific
            extensions.

        Raises:
            LookupError: If the patient is not found.
            PermissionError: If the current token lacks sufficient scope.
            ConnectionError: If the EHR system is unreachable.
        """
        ...

    # ------------------------------------------------------------------
    # Observations (labs, vitals, etc.)
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch_observations(
        self,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        observation_codes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve FHIR R4 Observation resources for a patient.

        Observations encompass laboratory results, vital signs, social
        history items, and other clinical measurements.

        Args:
            patient_id: The patient's identifier within the EHR system.
            start_date: Optional lower bound for the observation effective
                        date (inclusive).
            end_date: Optional upper bound for the observation effective
                      date (inclusive).
            observation_codes: Optional list of LOINC or SNOMED codes to
                               filter by.  When omitted, all available
                               observation categories are returned.

        Returns:
            A list of dictionaries, each representing a FHIR R4
            Observation resource with fields such as ``code``, ``value``,
            ``effectiveDateTime``, ``status``, and ``category``.

        Raises:
            LookupError: If the patient is not found.
            PermissionError: If the current token lacks sufficient scope.
            ConnectionError: If the EHR system is unreachable.
        """
        ...

    # ------------------------------------------------------------------
    # Appointments
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve FHIR R4 Appointment resources for a patient.

        Args:
            patient_id: The patient's identifier within the EHR system.

        Returns:
            A list of dictionaries, each representing a FHIR R4
            Appointment resource with fields such as ``status``, ``start``,
            ``end``, ``participant``, ``serviceType``, and ``description``.

        Raises:
            LookupError: If the patient is not found.
            PermissionError: If the current token lacks sufficient scope.
            ConnectionError: If the EHR system is unreachable.
        """
        ...

    # ------------------------------------------------------------------
    # Care plans
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch_care_plans(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve FHIR R4 CarePlan resources for a patient.

        Args:
            patient_id: The patient's identifier within the EHR system.

        Returns:
            A list of dictionaries, each representing a FHIR R4 CarePlan
            resource with fields such as ``status``, ``intent``,
            ``category``, ``activity``, ``goal``, and ``period``.

        Raises:
            LookupError: If the patient is not found.
            PermissionError: If the current token lacks sufficient scope.
            ConnectionError: If the EHR system is unreachable.
        """
        ...

    # ------------------------------------------------------------------
    # Write-back
    # ------------------------------------------------------------------

    @abstractmethod
    def push_observation(
        self, patient_id: str, observation: Dict[str, Any]
    ) -> bool:
        """
        Write a FHIR R4 Observation resource back to the EHR system.

        Args:
            patient_id: The patient's identifier within the EHR system.
            observation: A dictionary representing the FHIR R4 Observation
                         resource to create or update.  Must include at
                         minimum ``code``, ``value``, and ``status``.

        Returns:
            True if the observation was accepted by the EHR system.

        Raises:
            ValueError: If the observation payload is invalid.
            PermissionError: If the current token lacks write scope.
            ConnectionError: If the EHR system is unreachable.
        """
        ...

    # ------------------------------------------------------------------
    # Subscriptions / webhooks
    # ------------------------------------------------------------------

    @abstractmethod
    def subscribe_to_events(
        self, event_types: List[str], webhook_url: str
    ) -> str:
        """
        Register a webhook subscription with the EHR system.

        Args:
            event_types: List of event types to subscribe to.  Typical
                         values include ``'patient.update'``,
                         ``'encounter.discharge'``, ``'observation.create'``.
            webhook_url: The HTTPS URL that the EHR system should POST
                         event notifications to.

        Returns:
            A subscription identifier that can be used to manage or
            cancel the subscription.

        Raises:
            ValueError: If the event types are not supported by the vendor.
            PermissionError: If the current token lacks subscription scope.
            ConnectionError: If the EHR system is unreachable.
        """
        ...

    # ------------------------------------------------------------------
    # Connection health
    # ------------------------------------------------------------------

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Verify that the adapter can reach the EHR system and that
        credentials are valid.

        This is a lightweight health-check (e.g. hitting the server's
        metadata or capability-statement endpoint).

        Returns:
            True if the connection is healthy, False otherwise.
        """
        ...

    # ------------------------------------------------------------------
    # Capabilities
    # ------------------------------------------------------------------

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return a dictionary describing the adapter's capabilities.

        The result informs callers which operations are supported so that
        unsupported calls can be avoided at the orchestration layer.

        Returns:
            A dictionary with boolean flags and metadata, for example::

                {
                    "vendor": "epic",
                    "fhir_version": "R4",
                    "supports_read": True,
                    "supports_write": True,
                    "supports_subscriptions": True,
                    "supported_resources": ["Patient", "Observation", ...],
                    "supported_event_types": ["patient.update", ...],
                }
        """
        ...

    # ------------------------------------------------------------------
    # Helpers available to subclasses
    # ------------------------------------------------------------------

    def _ensure_authenticated(self) -> None:
        """
        Ensure that a valid access token is available.

        Calls ``authenticate()`` if no token exists or the current token
        has expired.

        Raises:
            ConnectionError: If authentication fails.
        """
        if self._authenticated and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return

        self.logger.debug("Access token missing or expired; re-authenticating")
        if not self.authenticate():
            raise ConnectionError("Authentication with EHR system failed")

    def _build_headers(self) -> Dict[str, str]:
        """
        Build standard HTTP headers for FHIR API requests.

        Returns:
            Dictionary of HTTP headers including Authorization and
            content-type for FHIR JSON.
        """
        headers: Dict[str, str] = {
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json',
        }
        if self._access_token:
            headers['Authorization'] = f'Bearer {self._access_token}'
        return headers
