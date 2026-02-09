# IHEP Hub-and-Spoke Architecture

**Version:** 1.0.0
**Last Updated:** 2026-01-17
**Author:** Jason M Jarmacz | Evolution Strategist
**Co-Author:** Claude by Anthropic

---

## Overview

The IHEP platform uses a **hub-and-spoke architecture** that enables omnidirectional resource flow between domain modules. This design ensures:

- **Centralized Security**: All PHI flows through audited, encrypted channels
- **Loose Coupling**: Spokes are independent and can be deployed/scaled separately
- **Single Source of Truth**: Shared state managed by the hub
- **HIPAA Compliance**: Centralized audit logging and access control

---

## Architecture Diagram

```
                                    ┌─────────────────┐
                                    │    CALENDAR     │
                                    │   appointments  │
                                    │   scheduling    │
                                    └────────┬────────┘
                                             │
                                             │
         ┌─────────────────┐                 │                 ┌─────────────────┐
         │  DIGITAL-TWIN   │                 │                 │    WELLNESS     │
         │                 │                 │                 │                 │
         │  - clinical     │                 │                 │  - metrics      │
         │  - behavioral   │                 │                 │  - tracking     │
         │  - social       │                 │                 │  - insights     │
         │  - financial    │                 │                 │                 │
         │  - synthesis    │                 │                 └────────┬────────┘
         │  - visualization│                 │                          │
         └────────┬────────┘                 │                          │
                  │                          │                          │
                  │           ┌──────────────┴──────────────┐           │
                  │           │                             │           │
                  ├───────────┤            HUB              ├───────────┤
                  │           │                             │           │
                  │           │  ┌───────────────────────┐  │           │
                  │           │  │       GATEWAY         │  │           │
                  │           │  │  - API routing        │  │           │
                  │           │  │  - EHR adapters       │  │           │
                  │           │  │  - Rate limiting      │  │           │
                  │           │  └───────────────────────┘  │           │
                  │           │                             │           │
                  │           │  ┌───────────────────────┐  │           │
                  │           │  │        AUTH           │  │           │
                  │           │  │  - IAM service        │  │           │
                  │           │  │  - JWT tokens         │  │           │
                  │           │  │  - MFA                │  │           │
                  │           │  └───────────────────────┘  │           │
                  │           │                             │           │
                  │           │  ┌───────────────────────┐  │           │
                  │           │  │        CORE           │  │           │
                  │           │  │  - Security engine    │  │           │
                  │           │  │  - Cryptography       │  │           │
                  │           │  │  - HIPAA audit        │  │           │
                  │           │  │  - Validation         │  │           │
                  │           │  └───────────────────────┘  │           │
                  │           │                             │           │
                  │           │  ┌───────────────────────┐  │           │
                  │           │  │       STORAGE         │  │           │
                  │           │  │  - Prisma/PostgreSQL  │  │           │
                  │           │  │  - Redis cache        │  │           │
                  │           │  │  - BigQuery analytics │  │           │
                  │           │  └───────────────────────┘  │           │
                  │           │                             │           │
                  │           │  ┌───────────────────────┐  │           │
                  │           │  │       EVENTS          │  │           │
                  │           │  │  - Pub/Sub messaging  │  │           │
                  │           │  │  - WebSocket server   │  │           │
                  │           │  │  - Event sourcing     │  │           │
                  │           │  └───────────────────────┘  │           │
                  │           │                             │           │
                  │           └──────────────┬──────────────┘           │
                  │                          │                          │
         ┌────────┴────────┐                 │                 ┌────────┴────────┐
         │    RESEARCH     │                 │                 │    RESOURCES    │
         │                 │                 │                 │                 │
         │  - portal       │                 │                 │  - providers    │
         │  - curriculum   │                 │                 │  - community    │
         │  - peer mediator│                 │                 │  - programs     │
         └─────────────────┘                 │                 └─────────────────┘
                                             │
                                    ┌────────┴────────┐
                                    │  NOTIFICATIONS  │
                                    │                 │
                                    │  - email/SMS    │
                                    │  - investor     │
                                    │  - templates    │
                                    └────────┬────────┘
                                             │
                                    ┌────────┴────────┐
                                    │   TELEHEALTH    │
                                    │                 │
                                    │  - video calls  │
                                    │  - messaging    │
                                    │  - scheduling   │
                                    └─────────────────┘
```

---

## Hub Components

### Gateway (`hub/gateway/`)
The API gateway is the single entry point for all external requests.

| Component | Purpose |
|-----------|---------|
| `app.py` | Flask application entry point |
| `ehr/adapters/` | EHR integration (Epic, Cerner, Allscripts, Athena) |
| `analytics/` | Analytics API endpoints |
| `middleware/` | Auth, rate limiting, HIPAA audit |

### Auth (`hub/auth/`)
Centralized authentication and authorization.

| Component | Purpose |
|-----------|---------|
| `iam/` | Go-based IAM service |
| `app.py` | Python auth API |
| `nextauth/` | NextAuth.js configuration |
| `jwt/` | JWT token handling |
| `mfa/` | Multi-factor authentication |

### Core (`hub/core/`)
Shared kernel with security and utilities.

| Component | Purpose |
|-----------|---------|
| `security/` | Morphogenetic security framework, HIPAA compliance |
| `crypto/` | Encryption, zero-trust, envelope encryption |
| `utils/` | Rate limiting, validation, shared utilities |
| `types/` | Shared type definitions |

### Storage (`hub/storage/`)
Database and caching abstractions.

| Component | Purpose |
|-----------|---------|
| `prisma/` | Database schema and client |
| `redis/` | Cache layer |
| `bigquery/` | Analytics data warehouse |

### Events (`hub/events/`)
Event-driven communication backbone.

| Component | Purpose |
|-----------|---------|
| `pubsub/` | GCP Pub/Sub integration |
| `websocket/` | Real-time updates |

---

## Spoke Modules

### Digital Twin (`spokes/digital-twin/`)
The 4-Twin health modeling system.

```
digital-twin/
├── clinical/          # Clinical health twin (labs, vitals, medications)
├── behavioral/        # Behavioral health twin (mental health, habits)
├── social/            # Social determinants twin (support, environment)
├── financial/         # Financial health twin (benefits, opportunities)
├── synthesis/         # Twin aggregation and manifold projection
└── visualization/     # Three.js 3D rendering
```

### Calendar (`spokes/calendar/`)
Appointment and scheduling management.

### Wellness (`spokes/wellness/`)
Health metrics tracking and insights.

### Research (`spokes/research/`)
Research portal and peer mediator curriculum.

```
research/
├── api/               # Research portal API
└── curriculum/        # Peer mediator financial literacy curriculum
```

### Resources (`spokes/resources/`)
Provider directory and community resources.

```
resources/
├── api/               # Resource catalog API
├── providers/         # Provider directory
└── community/         # Community programs and support
```

### Notifications (`spokes/notifications/`)
Multi-channel notification system.

```
notifications/
├── api/               # Go notification service
├── investor-outreach/ # Proposal mailer for investors
└── templates/         # Email/SMS templates
```

### Telehealth (`spokes/telehealth/`)
Video consultation and secure messaging.

```
telehealth/
├── video/             # Video call service
└── messaging/         # Secure messaging
```

---

## Data Flow Patterns

### 1. Request Flow (Synchronous)

```
Client Request
      │
      ▼
┌─────────────┐
│   Gateway   │ ─── Authentication ───▶ Auth Service
└─────────────┘
      │
      ▼
┌─────────────┐
│    Core     │ ─── Validation ───▶ Input Sanitization
└─────────────┘     Encryption       PHI Protection
      │
      ▼
┌─────────────┐
│   Spoke     │ ─── Business Logic
└─────────────┘
      │
      ▼
┌─────────────┐
│   Storage   │ ─── Database Query
└─────────────┘
      │
      ▼
   Response
```

### 2. Event Flow (Asynchronous)

```
Spoke A                     Hub                      Spoke B
   │                         │                          │
   │  ──── Publish Event ───▶│                          │
   │                         │                          │
   │                    ┌────┴────┐                     │
   │                    │ Pub/Sub │                     │
   │                    └────┬────┘                     │
   │                         │                          │
   │                         │◀─── Subscribe ───────────│
   │                         │                          │
   │                         │──── Deliver Event ──────▶│
   │                         │                          │
```

### 3. Cross-Spoke Communication

Spokes NEVER communicate directly. All cross-spoke data flows through the hub:

```
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ Digital Twin │          │     HUB      │          │   Calendar   │
│              │          │              │          │              │
│  "Patient    │ ────────▶│  Events Bus  │─────────▶│  "Schedule   │
│   needs      │          │              │          │   follow-up" │
│   follow-up" │          │  (Pub/Sub)   │          │              │
└──────────────┘          └──────────────┘          └──────────────┘
```

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────────┐
│                        Layer 7: Application                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Input Validation                      │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │              Authentication (JWT/MFA)            │    │    │
│  │  │  ┌─────────────────────────────────────────┐    │    │    │
│  │  │  │         Authorization (RBAC)             │    │    │    │
│  │  │  │  ┌─────────────────────────────────┐    │    │    │    │
│  │  │  │  │      Encryption (AES-256)        │    │    │    │    │
│  │  │  │  │  ┌─────────────────────────┐    │    │    │    │    │
│  │  │  │  │  │    Audit Logging        │    │    │    │    │    │
│  │  │  │  │  │  ┌─────────────────┐    │    │    │    │    │    │
│  │  │  │  │  │  │      PHI        │    │    │    │    │    │    │
│  │  │  │  │  │  └─────────────────┘    │    │    │    │    │    │
│  │  │  │  │  └─────────────────────────┘    │    │    │    │    │
│  │  │  │  └─────────────────────────────────┘    │    │    │    │
│  │  │  └─────────────────────────────────────────┘    │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### HIPAA Compliance Points

| Layer | Control | Location |
|-------|---------|----------|
| Transport | TLS 1.3 | Gateway |
| Authentication | JWT + MFA | Auth Service |
| Authorization | RBAC | Core Security |
| Encryption | AES-256 | Core Crypto |
| Audit | All PHI access logged | Core Security |
| Data Minimization | Field-level encryption | Storage |

---

## Deployment Architecture

```
                        ┌─────────────────────────────────────┐
                        │         Google Cloud Platform        │
                        └─────────────────────────────────────┘
                                          │
                        ┌─────────────────┼─────────────────┐
                        │                 │                 │
                        ▼                 ▼                 ▼
                 ┌────────────┐   ┌────────────┐   ┌────────────┐
                 │ Cloud Run  │   │ Cloud Run  │   │ Cloud Run  │
                 │  (Gateway) │   │  (Spokes)  │   │   (Auth)   │
                 └────────────┘   └────────────┘   └────────────┘
                        │                 │                 │
                        └─────────────────┼─────────────────┘
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         │                                │                                │
         ▼                                ▼                                ▼
  ┌────────────┐                  ┌────────────┐                  ┌────────────┐
  │ Cloud SQL  │                  │  Pub/Sub   │                  │  BigQuery  │
  │ (Primary)  │                  │  (Events)  │                  │ (Analytics)│
  └────────────┘                  └────────────┘                  └────────────┘
```

---

## Directory Structure

```
ihep-application/
├── hub/                          # CENTRAL HUB
│   ├── auth/                     # Authentication services
│   ├── core/                     # Security, crypto, utilities
│   ├── events/                   # Pub/Sub, WebSocket
│   ├── gateway/                  # API Gateway, EHR adapters
│   └── storage/                  # Database abstractions
│
├── spokes/                       # DOMAIN SPOKES
│   ├── calendar/                 # Appointments
│   ├── digital-twin/             # 4-Twin ecosystem
│   ├── notifications/            # Email/SMS, investor outreach
│   ├── research/                 # Portal, curriculum
│   ├── resources/                # Providers, community
│   ├── telehealth/               # Video, messaging
│   └── wellness/                 # Health tracking
│
├── src/                          # NEXT.JS FRONTEND
│   ├── app/                      # App Router pages
│   ├── components/               # React components
│   └── lib/                      # Utilities, hooks
│
├── docs/                         # DOCUMENTATION
│   ├── architecture/             # This document
│   └── strategic-intelligence/   # Business strategy
│
└── infrastructure/               # DEPLOYMENT
    ├── terraform/                # IaC
    ├── gcp/                      # GCP configs
    └── k8s/                      # Kubernetes
```

---

## Key Principles

1. **Hub is the Single Point of Control**
   - All authentication flows through `hub/auth/`
   - All data access flows through `hub/gateway/`
   - All events flow through `hub/events/`

2. **Spokes are Independent**
   - Each spoke can be deployed independently
   - Spokes have their own API, components, and data models
   - Spokes only depend on the hub, never on other spokes

3. **Omnidirectional Flow**
   - Any spoke can communicate with any other spoke
   - Communication always routes through the hub
   - The hub orchestrates and secures all data flow

4. **Security by Design**
   - PHI never leaves the encrypted boundary
   - All access is authenticated, authorized, and audited
   - Zero-trust architecture throughout

---

## Related Documents

- [RESTRUCTURING_REPORT.md](../RESTRUCTURING_REPORT.md) - Migration details
- [IHEP_Phase_III_Security_Architecture.md](../IHEP_Phase_III_Security_Architecture.md) - Security deep-dive
- [Phase_4_Deployment_Architecture.md](../Phase_4_Deployment_Architecture_on_Google_Cloud_Platform.md) - GCP deployment

---

**Document Status:** Active
**Review Cycle:** Quarterly
