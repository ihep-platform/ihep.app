"""
Bidirectional Sync Engine for EHR Integration

Handles scheduled and on-demand synchronization of data between
IHEP and connected EHR systems. Supports inbound pulls, outbound
pushes, and conflict resolution.

Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class SyncState:
    """Tracks the state of synchronization for a partner."""
    partner_id: str
    last_inbound_sync: Optional[str] = None
    last_outbound_sync: Optional[str] = None
    last_inbound_cursor: Optional[str] = None
    last_outbound_cursor: Optional[str] = None
    inbound_total_synced: int = 0
    outbound_total_synced: int = 0
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    status: str = "idle"  # idle, syncing, error

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    partner_id: str
    direction: str  # inbound, outbound
    resources_processed: int = 0
    resources_created: int = 0
    resources_updated: int = 0
    resources_failed: int = 0
    conflicts: int = 0
    error: Optional[str] = None
    duration_seconds: float = 0.0
    cursor: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class InboundSync:
    """
    Pull data from EHR systems into IHEP.

    Supports:
    - Scheduled incremental sync (using _lastUpdated cursors)
    - Bulk initial sync for new partners
    - On-demand sync triggered by API
    """

    def __init__(self, adapter_registry, config):
        self.adapter_registry = adapter_registry
        self.config = config
        self.sync_states: Dict[str, SyncState] = {}

    def get_sync_state(self, partner_id: str) -> SyncState:
        """Get or create sync state for a partner."""
        if partner_id not in self.sync_states:
            self.sync_states[partner_id] = SyncState(partner_id=partner_id)
        return self.sync_states[partner_id]

    def sync_partner(
        self,
        partner_id: str,
        resource_types: Optional[List[str]] = None,
        force_full: bool = False
    ) -> SyncResult:
        """
        Pull data from a single EHR partner.

        Args:
            partner_id: Partner identifier
            resource_types: Specific resource types to sync (default: all enabled)
            force_full: Force a full sync instead of incremental

        Returns:
            SyncResult with details of the operation
        """
        start_time = datetime.utcnow()
        state = self.get_sync_state(partner_id)
        state.status = "syncing"

        result = SyncResult(
            success=False,
            partner_id=partner_id,
            direction="inbound"
        )

        try:
            # Get partner config and adapter
            partner_config = self.config.get_partner(partner_id)
            if not partner_config:
                raise ValueError(f"Partner not found: {partner_id}")

            vendor = partner_config.get('ehr_vendor')
            adapter = self.adapter_registry.get_adapter(vendor)
            if not adapter:
                raise ValueError(f"No adapter for vendor: {vendor}")

            # Configure adapter with partner credentials
            adapter.configure(partner_config.get('connection', {}))

            # Authenticate
            if not adapter.authenticate():
                raise ConnectionError(f"Authentication failed for partner {partner_id}")

            # Determine resource types to sync
            data_scope = partner_config.get('data_scope', {})
            if resource_types is None:
                resource_types = []
                if data_scope.get('patients', True):
                    resource_types.append('Patient')
                if data_scope.get('observations', True):
                    resource_types.append('Observation')
                if data_scope.get('appointments', True):
                    resource_types.append('Appointment')
                if data_scope.get('care_plans', False):
                    resource_types.append('CarePlan')

            # Determine sync parameters
            since = None
            if not force_full and state.last_inbound_sync:
                since = state.last_inbound_sync

            # Sync each resource type
            for resource_type in resource_types:
                try:
                    count = self._sync_resource_type(
                        adapter, partner_id, resource_type, since
                    )
                    result.resources_processed += count
                    result.resources_created += count
                except Exception as e:
                    logger.error(
                        f"Error syncing {resource_type} for {partner_id}: {e}"
                    )
                    result.resources_failed += 1

            # Update state
            state.last_inbound_sync = datetime.utcnow().isoformat()
            state.inbound_total_synced += result.resources_processed
            state.consecutive_failures = 0
            state.status = "idle"

            result.success = True
            result.duration_seconds = (
                datetime.utcnow() - start_time
            ).total_seconds()

            logger.info(
                f"Inbound sync complete for {partner_id}: "
                f"{result.resources_processed} resources processed"
            )

        except Exception as e:
            state.last_error = str(e)
            state.consecutive_failures += 1
            state.status = "error"
            result.error = str(e)
            result.duration_seconds = (
                datetime.utcnow() - start_time
            ).total_seconds()
            logger.error(f"Inbound sync failed for {partner_id}: {e}")

        return result

    def _sync_resource_type(
        self,
        adapter,
        partner_id: str,
        resource_type: str,
        since: Optional[str] = None
    ) -> int:
        """Sync a specific resource type from the EHR."""
        count = 0
        batch_size = self.config.get_sync_batch_size(partner_id)

        logger.info(
            f"Syncing {resource_type} for {partner_id} "
            f"(since={since}, batch_size={batch_size})"
        )

        if resource_type == 'Patient':
            # For patients, we typically search by _lastUpdated
            resources = adapter.search_patients(
                since=since, count=batch_size
            ) if hasattr(adapter, 'search_patients') else []
            count = len(resources)
        elif resource_type == 'Observation':
            resources = adapter.search_observations(
                since=since, count=batch_size
            ) if hasattr(adapter, 'search_observations') else []
            count = len(resources)
        elif resource_type == 'Appointment':
            resources = adapter.search_appointments(
                since=since, count=batch_size
            ) if hasattr(adapter, 'search_appointments') else []
            count = len(resources)

        return count

    def bulk_initial_sync(self, partner_id: str) -> SyncResult:
        """Perform initial bulk sync for a new partner."""
        logger.info(f"Starting bulk initial sync for {partner_id}")
        return self.sync_partner(partner_id, force_full=True)


class OutboundSync:
    """
    Push IHEP data back to EHR systems.

    Handles writing observations, care plans, and other data
    from IHEP back to the originating or subscribing EHR system.
    """

    def __init__(self, adapter_registry, config):
        self.adapter_registry = adapter_registry
        self.config = config
        self.sync_states: Dict[str, SyncState] = {}

    def push_to_partner(
        self,
        partner_id: str,
        resources: List[Dict[str, Any]]
    ) -> SyncResult:
        """
        Push resources to a specific EHR partner.

        Args:
            partner_id: Target partner identifier
            resources: List of IHEP canonical resources to push

        Returns:
            SyncResult with details
        """
        start_time = datetime.utcnow()
        result = SyncResult(
            success=False,
            partner_id=partner_id,
            direction="outbound"
        )

        try:
            partner_config = self.config.get_partner(partner_id)
            if not partner_config:
                raise ValueError(f"Partner not found: {partner_id}")

            # Check if outbound is allowed
            sync_mode = partner_config.get('sync', {}).get('mode', 'inbound_only')
            if sync_mode == 'inbound_only':
                raise PermissionError(
                    f"Outbound sync not allowed for {partner_id} "
                    f"(mode: {sync_mode})"
                )

            vendor = partner_config.get('ehr_vendor')
            adapter = self.adapter_registry.get_adapter(vendor)
            if not adapter:
                raise ValueError(f"No adapter for vendor: {vendor}")

            adapter.configure(partner_config.get('connection', {}))

            if not adapter.authenticate():
                raise ConnectionError(f"Auth failed for {partner_id}")

            # Push each resource
            for resource in resources:
                try:
                    resource_type = resource.get('ihep_resource_type', 'Unknown')
                    success = self._push_resource(adapter, resource)
                    result.resources_processed += 1
                    if success:
                        result.resources_created += 1
                    else:
                        result.resources_failed += 1
                except Exception as e:
                    logger.error(
                        f"Failed to push resource to {partner_id}: {e}"
                    )
                    result.resources_failed += 1

            result.success = result.resources_failed == 0
            result.duration_seconds = (
                datetime.utcnow() - start_time
            ).total_seconds()

            logger.info(
                f"Outbound sync to {partner_id}: "
                f"{result.resources_created}/{result.resources_processed} succeeded"
            )

        except Exception as e:
            result.error = str(e)
            result.duration_seconds = (
                datetime.utcnow() - start_time
            ).total_seconds()
            logger.error(f"Outbound sync failed for {partner_id}: {e}")

        return result

    def _push_resource(self, adapter, resource: Dict) -> bool:
        """Push a single resource to the EHR."""
        resource_type = resource.get('ihep_resource_type', '')
        patient_id = resource.get('source_id', '')

        if resource_type == 'Observation':
            return adapter.push_observation(patient_id, resource)
        elif resource_type == 'CarePlan':
            return adapter.push_care_plan(
                patient_id, resource
            ) if hasattr(adapter, 'push_care_plan') else False

        logger.warning(f"Unsupported outbound resource type: {resource_type}")
        return False


class ConflictResolver:
    """
    Resolve data conflicts between IHEP and EHR systems.

    Strategies:
    - ehr_wins: EHR data always takes precedence
    - ihep_wins: IHEP data always takes precedence
    - newest_wins: Most recently updated data wins
    - manual: Flag for manual review
    """

    DEFAULT_STRATEGY = "newest_wins"

    def __init__(self, strategy: str = None):
        self.strategy = strategy or self.DEFAULT_STRATEGY

    def resolve(
        self,
        ihep_resource: Dict,
        ehr_resource: Dict,
        resource_type: str
    ) -> Dict:
        """
        Resolve a conflict between IHEP and EHR versions of a resource.

        Returns the winning resource with conflict metadata.
        """
        if self.strategy == "ehr_wins":
            winner = ehr_resource
            source = "ehr"
        elif self.strategy == "ihep_wins":
            winner = ihep_resource
            source = "ihep"
        elif self.strategy == "newest_wins":
            ihep_updated = ihep_resource.get('meta', {}).get(
                'last_updated', '1970-01-01'
            )
            ehr_updated = ehr_resource.get('meta', {}).get(
                'last_updated', '1970-01-01'
            )
            if ihep_updated >= ehr_updated:
                winner = ihep_resource
                source = "ihep"
            else:
                winner = ehr_resource
                source = "ehr"
        else:
            # Manual review - return both with flag
            return {
                "conflict": True,
                "resolution": "manual",
                "ihep_version": ihep_resource,
                "ehr_version": ehr_resource,
                "resource_type": resource_type,
                "detected_at": datetime.utcnow().isoformat()
            }

        winner["_conflict_resolution"] = {
            "strategy": self.strategy,
            "winner": source,
            "resolved_at": datetime.utcnow().isoformat()
        }

        return winner


class BidirectionalSync:
    """
    Orchestrates bidirectional sync between IHEP and EHR partners.

    Combines InboundSync, OutboundSync, and ConflictResolver
    to provide a unified sync interface.
    """

    def __init__(self, adapter_registry, config):
        self.inbound = InboundSync(adapter_registry, config)
        self.outbound = OutboundSync(adapter_registry, config)
        self.conflict_resolver = ConflictResolver()
        self.config = config

    def sync_partner(
        self,
        partner_id: str,
        direction: str = "bidirectional",
        resource_types: Optional[List[str]] = None,
        force_full: bool = False
    ) -> Dict[str, SyncResult]:
        """
        Perform sync with a partner.

        Args:
            partner_id: Partner to sync
            direction: inbound, outbound, or bidirectional
            resource_types: Specific types to sync
            force_full: Force full (non-incremental) sync

        Returns:
            Dict with 'inbound' and/or 'outbound' SyncResult
        """
        results = {}

        if direction in ("inbound", "bidirectional"):
            results["inbound"] = self.inbound.sync_partner(
                partner_id,
                resource_types=resource_types,
                force_full=force_full
            )

        if direction in ("outbound", "bidirectional"):
            # For outbound, we need to gather pending IHEP changes
            pending_resources = self._get_pending_outbound(partner_id)
            if pending_resources:
                results["outbound"] = self.outbound.push_to_partner(
                    partner_id, pending_resources
                )
            else:
                results["outbound"] = SyncResult(
                    success=True,
                    partner_id=partner_id,
                    direction="outbound",
                    resources_processed=0
                )

        return results

    def sync_all_partners(
        self,
        direction: str = "bidirectional"
    ) -> Dict[str, Dict[str, SyncResult]]:
        """Sync all enabled partners."""
        all_results = {}

        partners = self.config.get_enabled_partners()
        for partner in partners:
            partner_id = partner.get('id')
            sync_mode = partner.get('sync', {}).get('mode', 'inbound_only')

            # Respect partner's configured sync mode
            effective_direction = direction
            if sync_mode == 'inbound_only' and direction == 'bidirectional':
                effective_direction = 'inbound'
            elif sync_mode == 'outbound_only' and direction == 'bidirectional':
                effective_direction = 'outbound'

            try:
                all_results[partner_id] = self.sync_partner(
                    partner_id, direction=effective_direction
                )
            except Exception as e:
                logger.error(f"Sync failed for partner {partner_id}: {e}")
                all_results[partner_id] = {
                    "error": SyncResult(
                        success=False,
                        partner_id=partner_id,
                        direction=effective_direction,
                        error=str(e)
                    )
                }

        return all_results

    def get_sync_status(self, partner_id: str) -> Dict:
        """Get current sync status for a partner."""
        inbound_state = self.inbound.get_sync_state(partner_id)
        return {
            "partner_id": partner_id,
            "inbound": inbound_state.to_dict(),
            "status": inbound_state.status
        }

    def _get_pending_outbound(self, partner_id: str) -> List[Dict]:
        """
        Get IHEP resources pending outbound sync to a partner.
        In production, this queries the database for changes since
        the last outbound sync timestamp.
        """
        # Placeholder for database query
        return []
