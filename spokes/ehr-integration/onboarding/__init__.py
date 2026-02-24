"""
IHEP EHR Provider Onboarding System

Automated workflow for discovering, engaging, connecting, and monitoring
EHR provider integrations. Manages the full lifecycle from initial outreach
through production go-live and ongoing health monitoring.

Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
"""

from onboarding.models import (
    OnboardingPhase,
    OnboardingStatus,
    ProviderProfile,
    OnboardingEvent,
    OnboardingState,
    ConnectionTest,
    CommunicationRecord,
)
from onboarding.orchestrator import OnboardingOrchestrator
from onboarding.communication import CommunicationManager
from onboarding.connection_manager import ConnectionManager
from onboarding.status_reporter import StatusReporter
from onboarding.provider_discovery import ProviderDiscovery

__all__ = [
    "OnboardingPhase",
    "OnboardingStatus",
    "ProviderProfile",
    "OnboardingEvent",
    "OnboardingState",
    "ConnectionTest",
    "CommunicationRecord",
    "OnboardingOrchestrator",
    "CommunicationManager",
    "ConnectionManager",
    "StatusReporter",
    "ProviderDiscovery",
]
