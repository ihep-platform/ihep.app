# IHEP Project Summary

## Project Overview

**IHEP** (Integrated Health Empowerment Program) is a comprehensive aftercare resource management application designed to empower patients managing chronic conditions. The platform features:

- **4-Twin Digital Twin Ecosystem** - Personalized health modeling with Health, Financial, Social, and Care twins
- **Financial Empowerment Module** - Tools for achieving financial stability during care journey
- **Resource Hub** - PubSub articles, support groups, community programs
- **Telehealth Services** - Video consultations and remote care
- **Dynamic Calendar** - Consolidated appointment, medication, and activity management

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Next.js 16.1.5 (App Router, Turbopack) |
| Language | TypeScript 5 (strict mode) |
| UI | React 19 |
| Styling | Tailwind CSS 4 |
| Components | Radix UI + shadcn/ui |
| Auth | NextAuth.js v4 (credentials provider) |
| State | TanStack Query |
| Charts | Recharts 3 |
| Forms | React Hook Form + Zod |
| Database | Drizzle ORM (25+ tables defined, DATABASE_URL not configured) |
| Testing | Vitest + React Testing Library (113 tests, 0 failures) |
| Crypto | @noble/post-quantum v0.5.4 (ML-KEM, ML-DSA), @stablelib (XChaCha20-Poly1305, HKDF-SHA512) |

## Project Structure

```
hiv-health-insights/
│
├── frontend/                          # Next.js 16.1.1 React Application
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── mfa/
│   │   ├── (dashboard)/
│   │   │   ├── overview/
│   │   │   ├── clinical-twin/
│   │   │   ├── behavioral-twin/
│   │   │   ├── social-twin/
│   │   │   └── financial-twin/          # NEW
│   │   ├── digital-twin-viewer/         # 3D Visualization
│   │   ├── opportunities/               # NEW - Income Generation
│   │   ├── benefits/                    # NEW - Benefits Matching
│   │   ├── resources/
│   │   ├── calendar/
│   │   ├── messages/
│   │   ├── community/
│   │   └── research-portal/
│   ├── components/
│   │   ├── auth/
│   │   ├── digital-twin/
│   │   │   ├── DigitalTwinCanvas.tsx    # Three.js Renderer
│   │   │   ├── ManifoldProjector.ts     # Dimensionality Reduction
│   │   │   └── USDZLoader.ts            # OpenUSD Integration
│   │   ├── financial/                   # NEW
│   │   │   ├── FinancialHealthScore.tsx
│   │   │   ├── OpportunityMatcher.tsx
│   │   │   ├── BenefitsOptimizer.tsx
│   │   │   └── IncomeStreamManager.tsx
│   │   ├── charts/
│   │   └── layout/
│   ├── lib/
│   │   ├── api-client.ts
│   │   ├── auth-provider.tsx
│   │   └── websocket-client.ts
│   ├── styles/
│   │   └── globals.css
│   └── public/
│       ├── models/                      # USD scene files
│       └── assets/
│
├── backend/                             # Microservices
│   ├── api-gateway/                     # Next.js API Routes
│   │   └── pages/api/
│   │       ├── auth/
│   │       ├── twins/
│   │       │   ├── clinical.ts
│   │       │   ├── behavioral.ts
│   │       │   ├── social.ts
│   │       │   └── financial.ts         # NEW
│   │       ├── opportunities/           # NEW
│   │       └── benefits/                # NEW
│   ├── services/                        # Python Microservices
│   │   ├── clinical-twin-service/
│   │   │   ├── app.py
│   │   │   ├── models.py
│   │   │   └── requirements.txt
│   │   ├── behavioral-twin-service/
│   │   ├── social-twin-service/
│   │   ├── financial-twin-service/      # NEW
│   │   │   ├── app.py
│   │   │   ├── financial_twin.py
│   │   │   ├── opportunity_matcher.py
│   │   │   ├── benefits_optimizer.py
│   │   │   └── health_finance_predictor.py
│   │   ├── digital-twin-synthesis/
│   │   │   ├── manifold_projection.py
│   │   │   ├── usd_generator.py
│   │   │   └── incremental_updater.py
│   │   ├── ml-inference/
│   │   │   ├── adherence_predictor.py
│   │   │   ├── risk_stratification.py
│   │   │   └── federated_trainer.py
│   │   └── morphogenetic-healing/
│   │       ├── reaction_diffusion.py
│   │       ├── anomaly_detector.py
│   │       └── self_healer.py
│   └── shared/
│       ├── database/
│       │   ├── models.py
│       │   └── migrations/
│       ├── auth/
│       └── utils/
│
├── infrastructure/                      # Terraform IaC
│   ├── modules/
│   │   ├── networking/
│   │   ├── security/
│   │   ├── compute/
│   │   ├── database/
│   │   ├── healthcare-api/
│   │   └── monitoring/
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   ├── main.tf
│   ├── variables.tf
│   └── terraform.tfvars
│
├── ml-models/                           # AI/ML Training
│   ├── adherence-prediction/
│   ├── risk-stratification/
│   ├── opportunity-matching/            # NEW
│   ├── health-finance-correlation/      # NEW
│   ├── federated-learning/
│   └── model-registry/
│
├── data/                                # Data Engineering
│   ├── etl-pipelines/
│   ├── fhir-transformers/
│   ├── data-quality/
│   └── synthetic-data-generation/
│
├── docs/                                # Comprehensive Documentation
│   ├── architecture/
│   │   ├── IHEP_Complete_Architecture_v2.docx
│   │   ├── IHEP_Phase_III_Security_Architecture.md
│   │   ├── IHEP_Phase_IV_Digital_Twin_Testing.md
│   │   └── Phase_4_Deployment_Architecture.docx
│   ├── financial/
│   │   ├── ihep-financial-health-twins.docx
│   │   ├── IHEP_30Year_Financial_Projections.md
│   │   └── ihep-financial-models.docx
│   ├── implementation/
│   │   ├── IHEP_PRODUCTION_VALIDATION_ROADMAP.docx
│   │   ├── IHEP_Phase_III_Implementation_Plan.md
│   │   └── morphogenetic-implementation.md
│   ├── business/
│   │   ├── IHEP_PROJECT_CHARTER.docx
│   │   ├── IHEP_Investor_Pitch_Deck.pdf
│   │   └── ihep-grant-applications.docx
│   ├── api/
│   │   └── api-reference.md
│   └── user-guides/
│
├── tests/                               # Comprehensive Testing
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── security/
│   └── performance/
│
├── scripts/                             # Automation
│   ├── deployment/
│   ├── database/
│   └── monitoring/
│
├── .github/
│   └── workflows/                       # CI/CD Pipelines
│       ├── test.yml
│       ├── security-scan.yml
│       ├── deploy-dev.yml
│       ├── deploy-staging.yml
│       └── deploy-production.yml
│
├── docker-compose.yml                   # Local Development
├── Dockerfile
├── .env.example
├── .gitignore
├── README.md
├── PROJECT_SUMMARY.md                   # This Document
└── LICENSE
```

## Current Version: 2.0.0-alpha

### Recent Changes (February 10, 2026 -- Session 8)
- Auth guards on all 19 API routes (getServerSession checks)
- Vitest test suite: 113 tests passing, 0 failures across 7 test files
- Error boundaries and loading skeletons throughout dashboard
- Password reset flow (4-step page, API route, mock store integration)
- Toast notifications wired to signup, login, calendar, wellness, opportunities
- Mobile navigation with active route highlighting and WCAG touch targets
- PQC framework fully operational (fixed sign/verify argument order, envelope encryption DEK loss, HKDF salt non-determinism)
- Custom 404 page with inline SVG (no Lucide icons -- Next.js 16.1.5 prerender constraint)
- Build: 65 pages compiled, 0 errors

### Previous Changes (February 9-10, 2026 -- Session 7)
- Repository reorganization: hub-and-spoke architecture
- Deleted 22 duplicate + 11 deprecated directories
- Scaffolded clinical-frontend/ and provider-frontend/ apps
- Created formal engineering documentation (PRD, Tech Specs, TDD)

## Development Commands

```bash
npm run dev          # Start development server (http://localhost:3000)
npm run build        # Production build (Next.js 16.1.5, Turbopack)
npm run start        # Start production server
npm run lint         # Run ESLint
npm test             # Run unit tests with Vitest (113 tests)
npm run test:watch   # Watch mode for development
npm run test:coverage # Generate coverage report
```

## Key Files for New Sessions

1. **SESSION_HANDOFF.md** - Detailed handoff from previous session
2. **TODO.md** - Current task list and priorities
3. **CLAUDE.md** - Project instructions and conventions

## Environment Variables

Required in `.env.local`:
- `SESSION_SECRET` - NextAuth session encryption
- `DATABASE_URL` - Database connection string
- `NEXTAUTH_URL` - NextAuth callback URL
- `NEXTAUTH_SECRET` - NextAuth secret

## Security Notes

- HIPAA compliance is a central concern
- All PHI must be encrypted in transit and at rest
- No PHI in logs, localStorage, or URL parameters
- 30-minute session timeout
- Audit logging required for PHI access

## Contact

This is an enterprise Human/AI Joint Venture Application with:
- 5 humans overseeing managed agentic clusters
- 25 agents per cluster (1 human / 5 agents ratio)
- Each cluster has an overseer agent
- Supervisory position manages team overseers
