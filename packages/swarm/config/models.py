"""
IHEP Agent Swarm Data Models

Defines all enums, data classes, and models for the agent swarm system.
Adapted from AgentXFoundry military structure for healthcare domain.

Author: Jason M Jarmacz | jason@ihep.app
Co-Author: Claude by Anthropic
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4


# =============================================================================
# ENUMS
# =============================================================================

class RankEnum(str, Enum):
    """Military-style ranks for agent hierarchy"""
    # General Officer (Swarm Commander)
    GENERAL = "GEN"

    # Senior Officers (System Architects)
    COLONEL = "COL"

    # Field Officers (Lead Developers)
    MAJOR = "MAJ"

    # Company Officers (Coding/API Agents)
    CAPTAIN = "CPT"

    # Junior Officers (UX/Network Architects)
    LIEUTENANT = "LT"


class TeamRoleEnum(str, Enum):
    """Team roles within each development team"""
    SYSTEM_ARCHITECT = "system_architect"
    LEAD_DEVELOPER = "lead_developer"
    CODING_AGENT = "coding_agent"
    API_AGENT = "api_agent"
    UX_UI_DESIGNER = "ux_ui_designer"
    NETWORK_ARCHITECT = "network_architect"


class MOSEnum(str, Enum):
    """Military Occupational Specialty codes adapted for IHEP"""
    # System Architecture
    SA_SYSTEM_ARCHITECT = "18B-SA"

    # Development
    LD_LEAD_DEVELOPER = "12B-LD"
    CD_CODING_AGENT = "12B-CD"

    # API & Integration
    API_AGENT = "25B-API"

    # User Experience
    UX_DESIGNER = "42A-UX"

    # Infrastructure
    NET_ARCHITECT = "25B-NET"

    # Healthcare-Specific
    CLINICAL_DATA = "68W-CD"
    HIPAA_COMPLIANCE = "35L-HIPAA"
    HEALTH_ANALYST = "35F-HC"


class StatusEnum(str, Enum):
    """Agent and mission status states"""
    STANDBY = "standby"
    ACTIVE = "active"
    ENGAGED = "engaged"
    COMPLETE = "complete"
    FAILED = "failed"
    BLOCKED = "blocked"


class PriorityEnum(str, Enum):
    """Mission priority levels"""
    CRITICAL = "critical"
    URGENT = "urgent"
    HIGH = "high"
    ROUTINE = "routine"
    LOW = "low"


class TeamEnum(str, Enum):
    """The 5 IHEP development teams"""
    DIGITAL_TWIN = "team_1_digital_twin"
    MEMBER_RESOURCES = "team_2_member_resources"
    PEER_MEDIATOR = "team_3_peer_mediator"
    FINANCIAL_GENERATION = "team_4_financial_generation"
    CORE_LOGIC = "team_5_core_logic"


# =============================================================================
# ROLE-TO-RANK MAPPING
# =============================================================================

ROLE_TO_RANK: Dict[TeamRoleEnum, RankEnum] = {
    TeamRoleEnum.SYSTEM_ARCHITECT: RankEnum.COLONEL,
    TeamRoleEnum.LEAD_DEVELOPER: RankEnum.MAJOR,
    TeamRoleEnum.CODING_AGENT: RankEnum.CAPTAIN,
    TeamRoleEnum.API_AGENT: RankEnum.CAPTAIN,
    TeamRoleEnum.UX_UI_DESIGNER: RankEnum.LIEUTENANT,
    TeamRoleEnum.NETWORK_ARCHITECT: RankEnum.LIEUTENANT,
}

ROLE_TO_MOS: Dict[TeamRoleEnum, MOSEnum] = {
    TeamRoleEnum.SYSTEM_ARCHITECT: MOSEnum.SA_SYSTEM_ARCHITECT,
    TeamRoleEnum.LEAD_DEVELOPER: MOSEnum.LD_LEAD_DEVELOPER,
    TeamRoleEnum.CODING_AGENT: MOSEnum.CD_CODING_AGENT,
    TeamRoleEnum.API_AGENT: MOSEnum.API_AGENT,
    TeamRoleEnum.UX_UI_DESIGNER: MOSEnum.UX_DESIGNER,
    TeamRoleEnum.NETWORK_ARCHITECT: MOSEnum.NET_ARCHITECT,
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Task:
    """Atomic unit of work assigned to an agent"""
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    assigned_to: Optional[str] = None  # agent_id
    status: StatusEnum = StatusEnum.STANDBY
    dependencies: List[str] = field(default_factory=list)  # task_ids
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def is_ready(self, completed_tasks: set) -> bool:
        """Check if all dependencies are met"""
        return all(dep in completed_tasks for dep in self.dependencies)


@dataclass
class Mission:
    """High-level objective with decomposed tasks"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    objective: str = ""
    description: Optional[str] = None
    priority: PriorityEnum = PriorityEnum.ROUTINE
    status: StatusEnum = StatusEnum.STANDBY
    assigned_team: Optional[TeamEnum] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    tasks: List[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None


@dataclass
class Agent:
    """Individual agent in the swarm"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    rank: RankEnum = RankEnum.LIEUTENANT
    role: TeamRoleEnum = TeamRoleEnum.CODING_AGENT
    mos: MOSEnum = MOSEnum.CD_CODING_AGENT
    team: Optional[TeamEnum] = None
    status: StatusEnum = StatusEnum.STANDBY
    commander_id: Optional[str] = None
    subordinates: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    current_mission: Optional[str] = None
    performance_score: float = 1.0
    tasks_completed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def is_officer(self) -> bool:
        """Check if agent is an officer rank"""
        return self.rank in [RankEnum.GENERAL, RankEnum.COLONEL, RankEnum.MAJOR]

    def can_command(self, subordinate_rank: RankEnum) -> bool:
        """Check if this agent can command the given rank"""
        rank_order = [RankEnum.LIEUTENANT, RankEnum.CAPTAIN, RankEnum.MAJOR,
                      RankEnum.COLONEL, RankEnum.GENERAL]
        return rank_order.index(self.rank) > rank_order.index(subordinate_rank)


@dataclass
class Team:
    """Development team with 6 specialized agents"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    team_type: TeamEnum = TeamEnum.CORE_LOGIC
    system_architect: Optional[str] = None  # agent_id
    lead_developer: Optional[str] = None
    coding_agent: Optional[str] = None
    api_agent: Optional[str] = None
    ux_designer: Optional[str] = None
    network_architect: Optional[str] = None
    current_mission: Optional[str] = None
    missions_completed: int = 0
    status: StatusEnum = StatusEnum.STANDBY
    created_at: datetime = field(default_factory=datetime.now)

    def get_all_agents(self) -> List[str]:
        """Return list of all agent IDs in the team"""
        agents = []
        for agent_id in [self.system_architect, self.lead_developer,
                         self.coding_agent, self.api_agent,
                         self.ux_designer, self.network_architect]:
            if agent_id:
                agents.append(agent_id)
        return agents

    def is_complete(self) -> bool:
        """Check if all team roles are filled"""
        return all([
            self.system_architect,
            self.lead_developer,
            self.coding_agent,
            self.api_agent,
            self.ux_designer,
            self.network_architect,
        ])


@dataclass
class Swarm:
    """Complete swarm with General and 5 development teams"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "IHEP Development Swarm"
    general_id: Optional[str] = None
    teams: Dict[TeamEnum, str] = field(default_factory=dict)  # team_type -> team_id
    active_missions: List[str] = field(default_factory=list)
    completed_missions: List[str] = field(default_factory=list)
    status: StatusEnum = StatusEnum.STANDBY
    created_at: datetime = field(default_factory=datetime.now)
    activated_at: Optional[datetime] = None


# =============================================================================
# COMMUNICATION MODELS
# =============================================================================

@dataclass
class Order:
    """Command from superior to subordinate"""
    id: str = field(default_factory=lambda: str(uuid4()))
    from_agent: str = ""
    to_agent: str = ""
    order_type: str = "mission"  # mission, frago, status_request
    content: str = ""
    task_id: Optional[str] = None
    mission_id: Optional[str] = None
    issued_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None


@dataclass
class SitRep:
    """Situation Report from subordinate to superior"""
    id: str = field(default_factory=lambda: str(uuid4()))
    from_agent: str = ""
    to_agent: Optional[str] = None  # None = broadcast to commander
    status: StatusEnum = StatusEnum.ACTIVE
    current_task: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    blockers: List[str] = field(default_factory=list)
    reported_at: datetime = field(default_factory=datetime.now)


@dataclass
class CasRep:
    """Casualty Report for task/agent failures"""
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    failure_type: str = "error"  # error, timeout, resource_exhaustion
    error_message: str = ""
    task_id: Optional[str] = None
    stack_trace: Optional[str] = None
    reported_at: datetime = field(default_factory=datetime.now)
    recovery_action: Optional[str] = None


# =============================================================================
# TEAM DESCRIPTIONS
# =============================================================================

TEAM_DESCRIPTIONS: Dict[TeamEnum, Dict[str, str]] = {
    TeamEnum.DIGITAL_TWIN: {
        "name": "Digital Twin System",
        "description": "Clinical, Behavioral, Social, Financial Twins with 3D Visualization",
        "focus": "Three.js, WebGL, Real-time data streaming, USDZ models",
    },
    TeamEnum.MEMBER_RESOURCES: {
        "name": "Member Resources",
        "description": "Dynamic Calendar, Financial Empowerment Tools, Resource Feeds, Case Studies",
        "focus": "Calendar integration, PubSub feeds, Educational content",
    },
    TeamEnum.PEER_MEDIATOR: {
        "name": "Peer Mediator Curriculum",
        "description": "Training Modules, Certification, Progress Tracking, Community Support",
        "focus": "LMS, Video streaming, Assessment systems",
    },
    TeamEnum.FINANCIAL_GENERATION: {
        "name": "Financial Generation Module",
        "description": "Opportunity Matching, Benefits Optimizer, Income Tracking, Gig Integration",
        "focus": "Matching algorithms, External API integration, Financial calculations",
    },
    TeamEnum.CORE_LOGIC: {
        "name": "Core Logic",
        "description": "Authentication, Database, API Gateway, Shared Services, Deployment",
        "focus": "PostgreSQL, NextAuth, REST APIs, GCP infrastructure",
    },
}
