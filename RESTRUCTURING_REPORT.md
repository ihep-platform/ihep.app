# IHEP Hub-and-Spoke Restructuring Report

**Date:** 2026-01-17
**Commits:** 7404b7d, 882ac3d, a583539, 7690c64, + restoration commits

---

## IMPORTANT: Restoration Notice

During the initial cleanup phase, 63 files were incorrectly identified as legacy/duplicate and removed. These have been restored from git history. The following categories were affected:

### Restored Files

1. **Research Components** (restored to src/components/)
   - `src/components/research/ResearchDashboard.tsx`
   - `src/components/calendar/CalendarView.tsx`
   - `src/components/digital-twin/TwinDashboard.tsx`

2. **Simulation Library** (restored to src/lib/simulation/)
   - `src/lib/simulation/cbf.ts` - Control Barrier Functions
   - `src/lib/simulation/ekf.ts` - Extended Kalman Filter
   - `src/lib/simulation/math.ts` - Mathematical utilities

3. **Type Declarations** (restored to src/types/)
   - `src/types/images.d.ts`
   - `src/types/next-auth.d.ts`
   - `src/types/storage.d.ts`
   - `src/types/ws.d.ts`

4. **Peer Mediator Curriculum** (restored to spokes/research/curriculum/)
   - Full FastAPI backend for financial literacy curriculum

5. **Strategic Intelligence** (restored and moved to docs/strategic-intelligence/)
   - Business model documents
   - Investment terms
   - Market opportunity analysis
   - Risk management frameworks
   - Partnership proposals

6. **Proposal Mailer** (restored and moved to spokes/notifications/investor-outreach/)
   - Investor outreach email automation

7. **Visualization JS Files** (restored to spokes/digital-twin/visualization/)
   - `Digital_Twin_Renderer.js`
   - `Three_Rendering_Engine.js`
   - `dt-optimization.js`

### OpenUSD Partnership Support

The project maintains a partnership with OpenUSD. The following have been updated:
- Removed `OpenUSD/` from .gitignore (clone into project as needed)
- Removed USD file extensions (*.usdz, *.usda, *.usdc) from .gitignore
- USD scene files are welcome in the repository

---

## 1. Summary of Changes

### Repository Size Reduction
- **Before:** ~2.4 GB
- **After:** ~600 MB (excluding node_modules)
- **Reduction:** ~75%

### Commits Made
1. `7404b7d` - chore(cleanup): remove vendor code and legacy directories
2. `882ac3d` - refactor: consolidate code into hub-and-spoke architecture
3. `a583539` - fix: resolve Chart.js TypeScript type errors
4. `7690c64` - fix: remove investor-dashboard from gitignore

---

## 2. Files and Folders Removed

### 2.1 Vendor Code (1.2+ GB)
| Directory | Size | Reason |
|-----------|------|--------|
| `three.js-master/` | 610 MB | Use npm package `three@^0.182.0` |
| `OpenUSD/` | 544 MB | Use prebuilt binaries or Docker |
| `venv/` | 48 MB | Python virtualenv (regenerate in CI/CD) |
| `frontend/public/models/` | - | Empty placeholder |
| `models/medgemma-4b-it/` | - | Empty model directory |

### 2.2 Legacy/Backup Directories
| Directory | Size | Content |
|-----------|------|---------|
| `app_backup/` | 276 KB | Old app structure, docker-compose, backend services |
| `workspaces/` | 624 KB | Failed monorepo attempt |
| `Strategic_Intelligence/` | 316 KB | Intelligence reports, source documents |
| `investor-dashboard/` (root) | 204 KB | Legacy copy (active one is in src/app/) |
| `curriculum-backend/` | 52 KB | Legacy backend module |
| `proposal-mailer/` | 60 KB | Legacy email service |
| `fragmented_database/` | - | Empty/legacy database files |

### 2.3 Orphaned Frontend Code (Root Level)
| Directory | Size | Reason |
|-----------|------|--------|
| `/components/` | 120 KB | Root-level duplicates of src/components |
| `/lib/` | 92 KB | Root-level duplicates of src/lib |
| `/types/` | 16 KB | Root-level duplicates of src/types |
| `/frontend/` | 40 KB | Old frontend folder |
| `/applications/frontend/` | - | Failed monorepo structure |

### 2.4 Redundant Terraform/Infrastructure
| File/Directory | Size | Action |
|----------------|------|--------|
| `/main.tf` (root) | 4 KB | Removed (scaffolding) |
| `/cloud-armour-terraform.tf` | 12 KB | Moved to gcp/terraform/cloud-armor.tf |
| `/infrastructure/` (root) | 12 KB | Removed (empty scaffolding) |
| `/applications/infrastructure/` | 63 KB | Removed (scaffolding) |
| `/applications/main.tf` | - | Removed (scaffolding) |
| `/applications/financial-twin.tf` | 36 KB | Removed (merged) |
| `/workspaces/infrastructure/` | 8 KB | Removed with workspaces/ |

---

## 3. Files and Folders Moved/Consolidated

### 3.1 Hub (Central Infrastructure)
| Source | Destination |
|--------|-------------|
| `applications/backend/app.py` | `hub/gateway/app.py` |
| `applications/backend/auth-service/` | `hub/auth/` |
| `applications/backend/integration-gateway/` | `hub/gateway/ehr/` |
| `applications/backend/morphogenetic_security/` | `hub/core/security/` |
| `services/analytics-api/` | `hub/gateway/analytics/` |
| `iam_service/` (Go) | `hub/auth/iam/` |
| `mirth-connect/` | `hub/gateway/ehr/mirth-connect/` |
| `trust_framework/` | `hub/core/security/` |

### 3.2 Spokes (Domain Modules)
| Source | Destination |
|--------|-------------|
| `patient_twin_service/` | `spokes/digital-twin/` |
| `services/twin-api/` | `spokes/digital-twin/` |
| `services/financial-api/` | `spokes/digital-twin/financial/api/` |
| `applications/backend/financial-twin-service/` | `spokes/digital-twin/financial/` |
| `services/calendar.api/` | `spokes/calendar/api/` |
| `services/health-api/` | `spokes/wellness/api/` |
| `services/community-api/` | `spokes/resources/community/` |
| `resource_catalog_service/` | `spokes/resources/api/` |
| `services/research-api/` | `spokes/research/api/` |
| `notification_service/` (Go) | `spokes/notifications/api/` |
| `services/notification-api/` | `spokes/notifications/api/` |
| `services/chat-api/` | `spokes/telehealth/messaging/` |
| `services/synthesis/` | `spokes/digital-twin/synthesis/` |

### 3.3 ML/AI
| Source | Destination |
|--------|-------------|
| `training_datasets/` | `ml/training/datasets/` |
| `ai_inference_service/` | `ml/inference/` |
| `models/*.py` | `ml/models/` |

### 3.4 Configuration & Documentation
| Source | Destination |
|--------|-------------|
| `yaml/` | `configs/` |
| `json/` | `configs/` |
| `config/` | `configs/` |
| `markdown/` | `docs/` |
| `images/` | `public/images/` |
| `*.html` (root) | `public/` |

### 3.5 Packages
| Source | Destination |
|--------|-------------|
| `swarm/` | `packages/swarm/` |
| `javascript/` (visualization) | `spokes/digital-twin/visualization/` |
| `javascript/` (scripts) | `scripts/` |
| `python/` (various) | Distributed to appropriate hub/spokes |

---

## 4. Hub-and-Spoke Architecture

The directory structure implements a hub-and-spoke pattern where all spokes communicate through the central hub:

```
                                    ┌─────────────────┐
                                    │    CALENDAR     │
                                    │   appointments  │
                                    └────────┬────────┘
                                             │
         ┌─────────────────┐                 │                 ┌─────────────────┐
         │  DIGITAL-TWIN   │                 │                 │    WELLNESS     │
         │  4-twin system  │                 │                 │  health metrics │
         └────────┬────────┘                 │                 └────────┬────────┘
                  │                          │                          │
                  │           ┌──────────────┴──────────────┐           │
                  │           │                             │           │
                  ├───────────┤            HUB              ├───────────┤
                  │           │                             │           │
                  │           │  ┌───────────────────────┐  │           │
                  │           │  │  gateway (API)        │  │           │
                  │           │  │  auth (IAM/JWT)       │  │           │
                  │           │  │  core (security)      │  │           │
                  │           │  │  storage (DB)         │  │           │
                  │           │  │  events (pubsub)      │  │           │
                  │           │  └───────────────────────┘  │           │
                  │           │                             │           │
                  │           └──────────────┬──────────────┘           │
                  │                          │                          │
         ┌────────┴────────┐                 │                 ┌────────┴────────┐
         │    RESEARCH     │                 │                 │    RESOURCES    │
         │   curriculum    │                 │                 │   providers     │
         └─────────────────┘                 │                 └─────────────────┘
                                             │
                                    ┌────────┴────────┐
                                    │  NOTIFICATIONS  │
                                    │  investor mail  │
                                    └────────┬────────┘
                                             │
                                    ┌────────┴────────┐
                                    │   TELEHEALTH    │
                                    │  video/messaging│
                                    └─────────────────┘
```

**Key Principles:**
- **Hub** = Central infrastructure (gateway, auth, core, storage, events)
- **Spokes** = Domain modules that ONLY communicate via the hub
- **Omnidirectional Flow** = Any spoke can send/receive through the hub

For detailed architecture documentation, see: [docs/architecture/HUB_AND_SPOKE_ARCHITECTURE.md](docs/architecture/HUB_AND_SPOKE_ARCHITECTURE.md)

---

## 5. Directory Structure

```
ihep-application/
├── hub/                          # CENTRAL HUB
│   ├── auth/                     # Authentication (Go IAM, Python auth)
│   ├── core/                     # Shared kernel (security, crypto, utils)
│   ├── events/                   # Event bus (pubsub, websocket)
│   ├── gateway/                  # API Gateway (Flask, EHR adapters)
│   └── storage/                  # Storage abstractions
│
├── spokes/                       # DOMAIN SPOKES
│   ├── calendar/                 # Calendar & appointments
│   ├── digital-twin/             # 4-Twin ecosystem
│   │   ├── behavioral/           # Behavioral health twin
│   │   ├── clinical/             # Clinical health twin
│   │   ├── financial/            # Financial health twin
│   │   ├── social/               # Social determinants twin
│   │   ├── synthesis/            # Twin aggregation
│   │   └── visualization/        # 3D rendering (Three.js)
│   ├── notifications/            # Notification service
│   │   ├── api/                  # Go notification service
│   │   ├── investor-outreach/    # Proposal mailer (Python)
│   │   └── templates/            # Email/SMS templates
│   ├── research/                 # Research portal
│   │   ├── api/                  # Research API
│   │   └── curriculum/           # Peer mediator curriculum (FastAPI)
│   ├── resources/                # Resource discovery
│   ├── telehealth/               # Video & messaging
│   └── wellness/                 # Health monitoring
│
├── packages/                     # SHARED PACKAGES
│   ├── config/                   # Shared configs
│   ├── hooks/                    # React hooks
│   ├── swarm/                    # AI orchestration
│   ├── types/                    # TypeScript types
│   └── ui/                       # shadcn/ui components
│
├── ml/                           # ML/AI
│   ├── inference/                # AI inference service
│   ├── models/                   # Model definitions
│   └── training/                 # Training datasets
│
├── data/                         # DATA LAYER
│   ├── etl-pipelines/
│   ├── fhir/
│   ├── migrations/
│   ├── schemas/
│   └── synthetic/
│
├── src/                          # NEXT.JS FRONTEND (unchanged)
│   ├── app/                      # App Router pages
│   ├── components/               # React components
│   ├── hooks/                    # Frontend hooks
│   ├── lib/                      # Utilities
│   └── types/                    # Frontend types
│
├── configs/                      # Configuration files
├── docs/                         # Documentation
│   ├── strategic-intelligence/   # Business strategy docs
│   ├── architecture/             # System architecture
│   ├── compliance/               # HIPAA, legal docs
│   └── runbooks/                 # Operational guides
├── gcp/                          # GCP deployment
├── k8s/                          # Kubernetes manifests
├── public/                       # Static assets
├── scripts/                      # Automation scripts
├── terraform/                    # Infrastructure as Code
└── tests/                        # Test suites
```

---

## 5. Missing Components (To Be Created)

### 5.1 Hub - Empty Directories Needing Implementation

| Directory | Purpose | Priority |
|-----------|---------|----------|
| `hub/core/types/` | Shared TypeScript/Python type definitions | High |
| `hub/core/constants/` | Configuration constants, feature flags | Medium |
| `hub/gateway/middleware/` | Auth, rate limiting, HIPAA audit middleware | High |
| `hub/gateway/routes/` | Centralized route definitions | High |
| `hub/auth/nextauth/` | NextAuth.js configuration (move from src/lib) | High |
| `hub/auth/jwt/` | JWT handling utilities | High |
| `hub/auth/mfa/` | Multi-factor authentication | Medium |
| `hub/storage/prisma/` | Prisma schema and client | High |
| `hub/storage/redis/` | Redis cache layer | Medium |
| `hub/storage/bigquery/` | BigQuery analytics client | Medium |
| `hub/events/pubsub/` | GCP Pub/Sub integration | Medium |
| `hub/events/websocket/` | Real-time WebSocket server | Medium |

### 5.2 Spokes - Empty Directories Needing Implementation

| Directory | Purpose | Priority |
|-----------|---------|----------|
| `spokes/calendar/components/` | Calendar UI components | Low |
| `spokes/wellness/metrics/` | Health metric calculations | Medium |
| `spokes/wellness/components/` | Wellness UI components | Low |
| `spokes/resources/providers/` | Provider directory service | Medium |
| `spokes/telehealth/video/` | Video consultation service | High |
| `spokes/notifications/templates/` | Email/SMS templates | Medium |

### 5.3 Packages - Need Population

| Package | Status | Action Needed |
|---------|--------|---------------|
| `packages/ui/` | Empty | Move src/components/ui/* here |
| `packages/types/` | Empty | Extract shared types from src/types |
| `packages/hooks/` | Empty | Extract shared hooks from src/hooks |
| `packages/config/` | Empty | Create shared ESLint, TypeScript configs |

### 5.4 Infrastructure Files Needed

| File | Purpose |
|------|---------|
| `hub/gateway/middleware/auth.py` | Authentication middleware |
| `hub/gateway/middleware/rate_limit.py` | Rate limiting middleware |
| `hub/gateway/middleware/hipaa_audit.py` | HIPAA audit logging |
| `hub/storage/prisma/schema.prisma` | Database schema |
| `hub/events/pubsub/client.py` | Pub/Sub client wrapper |
| `hub/events/websocket/server.py` | WebSocket server |

### 5.5 Integration Work Needed

1. **NextAuth Migration**: Move `src/lib/auth/` to `hub/auth/nextauth/`
2. **Prisma Setup**: Create schema in `hub/storage/prisma/`
3. **API Gateway Routes**: Define centralized routes in `hub/gateway/routes/`
4. **Package Extraction**: Extract shared code to `packages/`
5. **Import Path Updates**: Update all imports to use new hub/spoke paths

---

## 6. Configuration Updates Made

### 6.1 tsconfig.json
Updated excludes to prevent TypeScript from compiling hub/spoke backend code:
```json
"exclude": [
  "node_modules",
  "hub",
  "spokes",
  "packages/swarm",
  "ml",
  "data",
  "configs",
  "gcp",
  "terraform",
  "k8s",
  "scripts",
  "tests"
]
```

### 6.2 package.json
Already configured with workspaces:
```json
"workspaces": ["packages/*", "hub/*", "spokes/*"]
```

### 6.3 turbo.json
Turborepo configuration for monorepo builds already in place.

### 6.4 .gitignore
Updated with:
- Vendor code exclusions (three.js-master, OpenUSD, venv)
- Large binary file patterns (*.usdz, *.glb, *.safetensors, etc.)
- Legacy directory prevention

---

## 7. Verification Status

| Check | Status |
|-------|--------|
| `npm run build` | PASS (62 routes generated) |
| `npm run dev` | PASS (starts on port 3000/3002) |
| TypeScript compilation | PASS |
| Git push origin | PASS |
| Git push ihep | PASS |

---

## 8. Next Steps (Recommended Priority)

### Immediate (High Priority)
1. Populate `hub/storage/prisma/schema.prisma` with database models
2. Create `hub/gateway/middleware/` implementations
3. Move NextAuth config to `hub/auth/nextauth/`
4. Create `hub/core/types/` with shared type definitions

### Short-term (Medium Priority)
1. Extract UI components to `packages/ui/`
2. Implement `hub/events/pubsub/` for event-driven architecture
3. Create `spokes/telehealth/video/` service
4. Populate `spokes/wellness/metrics/` with health calculations

### Long-term (Lower Priority)
1. Set up Redis caching in `hub/storage/redis/`
2. Implement WebSocket server in `hub/events/websocket/`
3. Create notification templates in `spokes/notifications/templates/`
4. Full package extraction to `packages/`

---

**Report Generated By:** Claude Opus 4.5
**For:** Jason M Jarmacz | Evolution Strategist
