"""
Bidirectional Sync Engine for EHR Integration

Handles inbound pulls, outbound pushes, and conflict resolution
between IHEP and connected EHR systems.

Author: Jason M Jarmacz | Evolution Strategist | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SyncState:
    """Tracks sync state for a partner."""

    partner_id: str
    last_inbound_sync: Optional[str] = None
    last_outbound_sync: Optional[str] = None
    inbound_total_synced: int = 0
    outbound_total_synced: int = 0
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    status: str = "idle"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool
    partner_id: str
    direction: str
    resources_processed: int = 0
    resources_created: int = 0
    resources_updated: int = 0
    resources_failed: int = 0
    conflicts: int = 0
    error: Optional[str] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


class InboundSync:
    """Pull data from EHR systems into IHEP."""

    def __init__(self, adapter_registry, config) -> None:
        self.adapter_registry = adapter_registry
        self.config = config
        self.sync_states: Dict[str, SyncState] = {}

    def get_sync_state(self, partner_id: str) -> SyncState:
        if partner_id not in self.sync_states:
            self.sync_states[partner_id] = SyncState(partner_id=partner_id)
        return self.sync_states[partner_id]

    def sync_partner(
        self,
        partner_id: str,
        resource_types: Optional[List[str]] = None,
        force_full: bool = False,
    ) -> SyncResult:
        start_time = datetime.utcnow()
        state = self.get_sync_state(partner_id)
        state.status = "syncing"

        result = SyncResult(success=False, partner_id=partner_id, direction="inbound")

        try:
            partner = self.config.partners.get(partner_id)
            if not partner:
                raise ValueError(f"Partner not found: {partner_id}")

            adapter = self.adapter_registry.get_adapter(partner.vendor)
            if not adapter:
                raise ValueError(f"No adapter for vendor: {partner.vendor}")

            adapter.configure({
                "base_url": partner.base_url,
                "client_id": partner.client_id,
                "client_secret": partner.client_secret,
                "mllp_host": partner.mllp_host,
                "mllp_port": partner.mllp_port,
            })

            if not adapter.authenticate():
                raise ConnectionError(f"Authentication failed for {partner_id}")

            if resource_types is None:
                resource_types = ["Patient", "Observation", "Appointment"]

            since = None
            if not force_full and state.last_inbound_sync:
                since = state.last_inbound_sync

            for resource_type in resource_types:
                try:
                    count = self._sync_resource_type(adapter, resource_type, since)
                    result.resources_processed += count
                    result.resources_created += count
                except Exception as e:
                    logger.error("Error syncing %s for %s: %s", resource_type, partner_id, e)
                    result.resources_failed += 1

            state.last_inbound_sync = datetime.utcnow().isoformat()
            state.inbound_total_synced += result.resources_processed
            state.consecutive_failures = 0
            state.status = "idle"
            result.success = True

        except Exception as e:
            state.last_error = str(e)
            state.consecutive_failures += 1
            state.status = "error"
            result.error = str(e)
            logger.error("Inbound sync failed for %s: %s", partner_id, e)

        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result

    def _sync_resource_type(self, adapter, resource_type: str, since: Optional[str]) -> int:
        if resource_type == "Patient" and hasattr(adapter, "search_patients"):
            return len(adapter.search_patients(since=since))
        elif resource_type == "Observation" and hasattr(adapter, "search_observations"):
            return len(adapter.search_observations(since=since))
        elif resource_type == "Appointment" and hasattr(adapter, "search_appointments"):
            return len(adapter.search_appointments(since=since))
        return 0


class OutboundSync:
    """Push IHEP data back to EHR systems."""

    def __init__(self, adapter_registry, config) -> None:
        self.adapter_registry = adapter_registry
        self.config = config

    def push_to_partner(self, partner_id: str, resources: List[Dict[str, Any]]) -> SyncResult:
        start_time = datetime.utcnow()
        result = SyncResult(success=False, partner_id=partner_id, direction="outbound")

        try:
            partner = self.config.partners.get(partner_id)
            if not partner:
                raise ValueError(f"Partner not found: {partner_id}")

            adapter = self.adapter_registry.get_adapter(partner.vendor)
            if not adapter:
                raise ValueError(f"No adapter for vendor: {partner.vendor}")

            adapter.configure({
                "base_url": partner.base_url,
                "client_id": partner.client_id,
                "client_secret": partner.client_secret,
            })

            if not adapter.authenticate():
                raise ConnectionError(f"Auth failed for {partner_id}")

            for resource in resources:
                try:
                    resource_type = resource.get("resourceType", "")
                    result.resources_processed += 1
                    if resource_type == "Observation":
                        patient_id = resource.get("subject", {}).get("reference", "").replace("Patient/", "")
                        if adapter.push_observation(patient_id, resource):
                            result.resources_created += 1
                        else:
                            result.resources_failed += 1
                    else:
                        result.resources_failed += 1
                except Exception as e:
                    logger.error("Failed to push resource to %s: %s", partner_id, e)
                    result.resources_failed += 1

            result.success = result.resources_failed == 0

        except Exception as e:
            result.error = str(e)
            logger.error("Outbound sync failed for %s: %s", partner_id, e)

        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result


class ConflictResolver:
    """Resolve data conflicts between IHEP and EHR systems."""

    DEFAULT_STRATEGY = "newest_wins"

    def __init__(self, strategy: str = None) -> None:
        self.strategy = strategy or self.DEFAULT_STRATEGY

    def resolve(self, ihep_resource: Dict, ehr_resource: Dict, resource_type: str) -> Dict:
        if self.strategy == "ehr_wins":
            winner, source = ehr_resource, "ehr"
        elif self.strategy == "ihep_wins":
            winner, source = ihep_resource, "ihep"
        elif self.strategy == "newest_wins":
            ihep_ts = ihep_resource.get("meta", {}).get("last_updated", "1970-01-01")
            ehr_ts = ehr_resource.get("meta", {}).get("last_updated", "1970-01-01")
            if ihep_ts >= ehr_ts:
                winner, source = ihep_resource, "ihep"
            else:
                winner, source = ehr_resource, "ehr"
        else:
            return {
                "conflict": True, "resolution": "manual",
                "ihep_version": ihep_resource, "ehr_version": ehr_resource,
                "resource_type": resource_type,
                "detected_at": datetime.utcnow().isoformat(),
            }

        winner["_conflict_resolution"] = {
            "strategy": self.strategy, "winner": source,
            "resolved_at": datetime.utcnow().isoformat(),
        }
        return winner


class BidirectionalSync:
    """Orchestrates bidirectional sync between IHEP and EHR partners."""

    def __init__(self, adapter_registry, config) -> None:
        self.inbound = InboundSync(adapter_registry, config)
        self.outbound = OutboundSync(adapter_registry, config)
        self.conflict_resolver = ConflictResolver()
        self.config = config

    def sync_partner(
        self,
        partner_id: str,
        direction: str = "bidirectional",
        resource_types: Optional[List[str]] = None,
        force_full: bool = False,
    ) -> Dict[str, SyncResult]:
        results = {}

        if direction in ("inbound", "bidirectional"):
            results["inbound"] = self.inbound.sync_partner(
                partner_id, resource_types=resource_types, force_full=force_full,
            )

        if direction in ("outbound", "bidirectional"):
            pending = self._get_pending_outbound(partner_id)
            if pending:
                results["outbound"] = self.outbound.push_to_partner(partner_id, pending)
            else:
                results["outbound"] = SyncResult(
                    success=True, partner_id=partner_id, direction="outbound",
                )

        return results

    def get_sync_status(self, partner_id: str) -> Dict:
        state = self.inbound.get_sync_state(partner_id)
        return state.to_dict()

    def _get_pending_outbound(self, partner_id: str) -> List[Dict]:
        return []
