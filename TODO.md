# IHEP Project TODO

Last Updated: February 10, 2026 (Session 7)

## Completed Tasks

- [x] Update landing page from HIV-specific to general healthcare aftercare
- [x] Update color scheme to greens, gold, amber (matching logo)
- [x] Remove calendar from public landing page (moved to members area)
- [x] Remove wellness dashboard from public landing page (moved to members area)
- [x] Add About section to landing page
- [x] Fix directory structure conflicts (app/ vs src/app/)
- [x] Install missing dependencies (Radix UI, shadcn utilities)
- [x] Fix TypeScript errors in shadcn/ui components
- [x] Fix bcrypt -> bcryptjs imports
- [x] Update calendar.tsx for react-day-picker v9
- [x] Update chart.tsx for recharts v3
- [x] Update resizable.tsx for react-resizable-panels v3
- [x] Fix Tailwind CSS v4 configuration
- [x] Add HSL CSS variables for theme
- [x] Get build passing
- [x] Fix Tailwind v4 CSS import syntax
- [x] Connect login modal form to NextAuth signIn()
- [x] Connect register modal form to /api/auth/register
- [x] Add form state management (useState for inputs)
- [x] Add error handling and loading states to forms
- [x] "Learn About Digital Twins" button scrolls to #digital-twin section
- [x] "Explore Digital Twin Program" button opens signup modal
- [x] Add logout functionality to dashboard
- [x] Move financials and opportunities under /dashboard route
- [x] Update theme colors consistently across all pages
- [x] Wellness page: Add Metric button opens functional modal
- [x] Calendar page: New Appointment button opens functional modal
- [x] Calendar page: Interactive calendar with clickable dates
- [x] Calendar page: Clicking appointment day shows appointment details
- [x] Opportunities page: Find Opportunities button with error handling
- [x] Fix Select dropdown transparency (solid white background)
- [x] Fix Select dropdown direction (opens downward)
- [x] Fix 29 Dependabot security vulnerabilities (Next.js, transformers, flask-cors, marshmallow, black)
- [x] Rename app/ to workspaces/ to fix Next.js App Router conflict
- [x] Remove duplicate postcss.config.js
- [x] Fix CSP blocking inline scripts in development mode
- [x] Add Contact form section to landing page (replaces footer scroll)
- [x] Update images.domains to images.remotePatterns (deprecation fix)
- [x] Fix hydration mismatch error (cleared .next cache)
- [x] Add AI chat modal to digital twin page (mock responses)
- [x] Add interactive SVG body visualization placeholder
- [x] Add body system status cards with popup details
- [x] Repository reorganization -- hub-and-spoke architecture (Session 7, Feb 9)
- [x] Delete 22 duplicate directories and 11 deprecated directories (Session 7, Feb 9)
- [x] Scaffold clinical-frontend/ and provider-frontend/ apps (Session 7, Feb 9)
- [x] Extract backend code to spokes/, core/, admin/, ml/, infrastructure/, data/ (Session 7, Feb 9)
- [x] Create formal engineering documentation suite (Session 7, Feb 10)
  - [x] Project Requirements Document (IEEE 830) -- 703 lines, 63 FRs, 33 NFRs
  - [x] Technical Specifications Document (IEEE 1233) -- 1,015 lines, 22 API specs
  - [x] Technical Design Document (IEEE 1016) -- 1,088 lines, architecture + math models

## High Priority

### Digital Twin 3D Integration (BLOCKED - Session 6)
- [x] Install Three.js dependency (`npm install three @types/three`)
- [x] Install three-usdz-loader (with --legacy-peer-deps)
- [x] Move `components/digital-twin/` to `src/components/digital-twin/`
- [x] Add type declarations (`src/types/three-addons.d.ts`)
- [x] Add COOP/COEP headers to next.config.mjs
- [x] Fixed 2D/3D toggle button (use plain HTML, not shadcn Button)
- [x] Fixed 2D/3D mode swap (conditions were inverted)
- [x] Disabled USDZ loader temporarily (causing "invalid zip data" errors)
- [ ] **BLOCKED: Turbopack + Three.js bundling error** - See SESSION_HANDOFF.md for details

### Database Connection
- [ ] Set DATABASE_URL environment variable
- [ ] Connect Drizzle ORM to PostgreSQL (schema already defined in src/shared/schema.ts, 25+ tables)
- [ ] Replace FileUserStore (src/lib/mockStore.ts) with database-backed user repository
- [ ] Run initial migrations against connected database
- [ ] Add seed data for development

### API Authentication Guards
- [ ] Add getServerSession(authOptions) checks to all API routes (currently most return mock data without auth)
- [ ] Implement RBAC checks per endpoint (patient vs provider vs admin)
- [ ] Add rate limiting to API endpoints

### Testing
- [ ] Set up Vitest + React Testing Library
- [ ] Add unit tests for authentication flow
- [ ] Add unit tests for form validation
- [ ] Add unit tests for EKF/CBF simulation modules
- [ ] Add E2E tests with Playwright for critical user journeys
- [ ] Add accessibility tests with axe-core

### Grant Applications (URGENT)
- [ ] **ARPA-H ADVOCATE TA2 Solution Summary -- due Feb 27, 2026**
- [ ] **CMS ACCESS BH Track application -- due Apr 1, 2026**
- [ ] NIH R21 (NIMHD) -- receipt date Jun 16, 2026

## Medium Priority

### Pre-Production Content
- [ ] Replace all placeholder/dummy text with real IHEP content
- [ ] Dashboard: Replace mock wellness metrics with real data integration
- [ ] Dashboard: Replace mock appointments with real calendar data
- [ ] Dashboard: Replace mock provider listings with real provider database
- [ ] Calendar: Remove hardcoded sample appointments
- [ ] Providers: Remove sample provider data (Dr. Sarah Chen, etc.)
- [ ] Resources: Replace sample educational resources with real content
- [ ] Financials: Connect to real financial data source
- [ ] Opportunities: Replace sample gig/training listings with real opportunities
- [ ] Landing page: Review all marketing copy for accuracy

### Features
- [ ] Implement appointment booking functionality (currently static data)
- [ ] Add real wellness metric tracking and data persistence
- [ ] Implement provider search and filtering with real data
- [ ] Add real-time digital twin data streams
- [ ] Implement password reset functionality
- [ ] Implement email verification flow

### User Experience
- [ ] Add loading skeletons throughout dashboard
- [ ] Implement proper error boundaries
- [ ] Add toast notifications for user actions
- [ ] Improve mobile navigation experience

## Low Priority / Future

### Infrastructure
- [ ] Configure GCP deployment (Cloud Run, BigQuery)
- [ ] Set up CI/CD pipeline
- [ ] Configure monitoring and logging (Sentry, Cloud Monitoring)
- [ ] Implement rate limiting with Upstash Redis

### Features
- [ ] Financial Empowerment Module enhancements
- [ ] PubSub articles feed integration
- [ ] Telehealth video integration (Twilio)
- [ ] Notification service (email/SMS with SendGrid/Twilio)

### Security & Compliance
- [ ] HIPAA compliance audit
- [ ] Implement audit logging for PHI access
- [ ] Add field-level encryption for sensitive data (PQC encryption code exists, needs integration)
- [ ] Security penetration testing
- [ ] Add CSRF protection for custom forms

## Notes

- Project version: 2.0.0-alpha (Next.js 16.1.5, React 19, TypeScript 5)
- Project uses `src/app/` as the main app directory
- Path alias `@/*` maps to `./src/*`
- Path alias `@shared/*` maps to `./src/shared/*`
- Authentication uses NextAuth.js v4 with credentials provider
- Mock store currently used for user data in development
- All dashboard pages protected with session check
- Drizzle ORM schema defined (25+ tables) but no database connected
- Three engineering documents provide full traceability: PRD -> Tech Specs -> TDD
- Repository reorganized into hub-and-spoke: ihep-application/ (hub) + spokes/ (16 services)
