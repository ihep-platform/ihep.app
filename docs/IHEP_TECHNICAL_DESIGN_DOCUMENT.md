# IHEP Technical Design Document

**Document Identifier:** IHEP-TDD-2026-001
**Version:** 1.0
**Date:** 2026-02-10
**Status:** Draft
**Author:** Jason M Jarmacz | Evolution Strategist | jason@ihep.app
**Co-Author:** Claude by Anthropic

**Standard:** IEEE 1016-2009 (Software Design Description)
**Classification:** Internal -- Confidential

---

## Revision History

| Version | Date       | Author        | Description            |
|---------|------------|---------------|------------------------|
| 1.0     | 2026-02-10 | J. Jarmacz / Claude | Initial release |

---

## Table of Contents

1. [Design Overview](#1-design-overview)
2. [System Architecture](#2-system-architecture)
3. [Component Design](#3-component-design)
4. [Data Architecture](#4-data-architecture)
5. [Authentication Design](#5-authentication-design)
6. [Security Design](#6-security-design)
7. [Digital Twin Design](#7-digital-twin-design)
8. [Mathematical Models](#8-mathematical-models)
9. [Integration Design](#9-integration-design)
10. [Error Handling and Resilience](#10-error-handling-and-resilience)
11. [Build and Deployment Design](#11-build-and-deployment-design)

---

## 1. Design Overview

### 1.1 Architectural Style

IHEP uses a **hub-and-spoke architecture** with a **server-side rendered single-page application** pattern. The architectural style combines:

- **Hub-and-Spoke**: The Next.js application (`ihep-application/`) is the hub. Sixteen backend services (`spokes/`) provide domain-specific computation. The hub aggregates data from spokes and presents it to the user.

- **Component-Based UI**: React 19 functional components with hooks, organized by feature domain.

- **API-First**: All data access flows through Next.js API Route Handlers at `/api/*`, creating a clean separation between rendering and data layers.

- **Server-First Rendering**: Next.js App Router defaults to Server Components. Interactive elements are explicitly marked with `'use client'`.

### 1.2 Design Rationale

| Decision | Rationale |
|----------|-----------|
| Next.js App Router (not Pages Router) | Server Components reduce client bundle, streaming SSR improves perceived performance, native React 19 support |
| TypeScript strict mode | Enterprise healthcare application requires type safety to prevent runtime errors with PHI |
| File-based mock store (development) | Eliminates database dependency during UI development; schema pre-defined for migration |
| Post-quantum cryptography | Future-proofing PHI encryption against quantum computing threats per NIST recommendations |
| shadcn/ui component library | Unstyled Radix primitives with Tailwind; full source control, no runtime dependency on third-party component CDN |
| Standalone output | Self-contained deployment artifact for Cloud Run containerization |

### 1.3 Design Constraints

1. All components MUST be functional components (no class components).
2. All API routes MUST validate input using Zod schemas at the boundary.
3. No PHI SHALL traverse client-side storage (localStorage, sessionStorage, cookies, URL params).
4. Three.js rendering MUST be excluded from server-side builds (`ssr: false` dynamic imports or Webpack externals).
5. All mathematical models MUST be verifiable against published formulas with proofs.

---

## 2. System Architecture

### 2.1 Hub-and-Spoke Model

```
+-------------------------------------------------------------------+
|                        IHEP Hub (Next.js 16.1.5)                  |
|                                                                   |
|  +------------------+  +------------------+  +------------------+ |
|  | Server           |  | Client           |  | API Routes       | |
|  | Components       |  | Components       |  | (/api/*)         | |
|  | (RSC)            |  | ('use client')   |  | Route Handlers   | |
|  +--------+---------+  +--------+---------+  +--------+---------+ |
|           |                      |                     |          |
|           +----------+-----------+---------------------+          |
|                      |                                            |
|  +-------------------+--------------------+                       |
|  |          Data Layer                    |                       |
|  |  mockStore (dev) | db (production)     |                       |
|  +-------------------+--------------------+                       |
+-------------------------------------------------------------------+
         |                    |                    |
         v                    v                    v
+--------+------+   +--------+------+   +---------+-----+
| Spoke:        |   | Spoke:        |   | Spoke:        |
| auth          |   | clinical      |   | financial     |
| (planned)     |   | (planned)     |   | (planned)     |
+---------------+   +---------------+   +---------------+
```

**Current State:** The hub operates self-contained with all 22 API endpoints returning mock data. No spoke services are connected. The hub is designed so that API route handlers can be redirected to spoke service URLs when they become available.

### 2.2 Next.js App Router Architecture

The application uses the Next.js 16 App Router with the following structural conventions:

```
src/app/
  layout.tsx              # Root layout (AuthProvider, Inter font, metadata)
  page.tsx                # Landing page (/)
  globals.css             # Global styles (Tailwind base)
  providers.tsx           # Client-side providers wrapper

  auth/
    login/page.tsx        # /auth/login
    signup/page.tsx       # /auth/signup
  login/page.tsx          # /login (alias)
  register/page.tsx       # /register (alias)

  dashboard/
    layout.tsx            # Dashboard layout (nav, auth guard, user menu)
    page.tsx              # /dashboard (overview)
    wellness/page.tsx     # /dashboard/wellness
    calendar/page.tsx     # /dashboard/calendar
    ...
    digital-twin/
      page.tsx            # /dashboard/digital-twin (overview)
      clinical/page.tsx   # /dashboard/digital-twin/clinical
      ...

  api/
    auth/
      [...nextauth]/route.ts  # NextAuth handler
      register/route.ts       # Registration
    twins/
      mock-data.ts             # Shared mock data builder
      clinical/route.ts        # Twin endpoints
      ...
    health/route.ts            # Health check
    ...
```

**Server vs Client Component Partitioning:**

| Component Type | Pattern | Usage |
|---------------|---------|-------|
| Server Component | Default (no directive) | Page components, layouts without interactivity, data fetching |
| Client Component | `'use client'` directive | Dashboard layout (useSession, useState, useRouter), forms, 3D canvas, charts |

### 2.3 Deployment Architecture

**Current (Development):**

```
Developer Machine
  |
  +-- npm run dev (localhost:3000)
  |     |
  |     +-- Next.js Dev Server (Webpack or Turbopack)
  |     +-- File-based mock store (data/mock-users.json)
  |     +-- .env.local (secrets)
```

**Target (Production):**

```
GCP Project
  |
  +-- Cloud Run
  |     |
  |     +-- Docker Container (standalone Next.js)
  |     +-- Port 3000
  |     +-- Auto-scaling: 0 to N instances
  |
  +-- Cloud SQL (PostgreSQL 15)
  |     +-- Connection via DATABASE_URL
  |     +-- SSL required
  |
  +-- Cloud Storage
  |     +-- Static assets
  |     +-- USDZ model files
  |
  +-- Secret Manager
  |     +-- SESSION_SECRET
  |     +-- DATABASE_URL
  |     +-- OAuth credentials
  |
  +-- Cloud CDN
        +-- /_next/static/* (immutable, 1-year cache)
```

---

## 3. Component Design

### 3.1 Page Component Hierarchy

The application has 41 page routes organized in the following hierarchy:

```
RootLayout (src/app/layout.tsx)
  |-- AuthProvider (wraps entire app)
  |
  |-- Landing Page (/)
  |-- About (/about)
  |-- Auth Pages
  |     |-- Login (/auth/login, /login)
  |     |-- Signup (/auth/signup, /register)
  |
  |-- Dashboard (requires auth)
  |     |-- DashboardLayout (src/app/dashboard/layout.tsx)
  |     |     |-- Top navigation bar (desktop)
  |     |     |-- Bottom navigation bar (mobile)
  |     |     |-- User menu dropdown
  |     |
  |     |-- Overview (/dashboard)
  |     |-- Wellness (/dashboard/wellness)
  |     |-- Calendar (/dashboard/calendar)
  |     |-- Opportunities (/dashboard/opportunities)
  |     |-- Financials (/dashboard/financials)
  |     |-- Resources (/dashboard/resources)
  |     |-- Providers (/dashboard/providers)
  |     |-- Health Monitor (/dashboard/health-monitor)
  |     |-- Digital Twin
  |           |-- Overview (/dashboard/digital-twin)
  |           |-- Clinical (/dashboard/digital-twin/clinical)
  |           |-- Behavioral (/dashboard/digital-twin/behavioral)
  |           |-- Social (/dashboard/digital-twin/social)
  |           |-- Financial (/dashboard/digital-twin/financial)
  |           |-- Personal (/dashboard/digital-twin/personal)
  |
  |-- Public Pages
  |     |-- Community (/community)
  |     |-- Education (/education)
  |     |-- Events (/events)
  |     |-- Forum (/forum)
  |     |-- Resources (/resources)
  |     |-- Rewards (/rewards)
  |     |-- Support (/support, /support/kb/[slug])
  |
  |-- Legal Pages (/legal/privacy, /legal/terms, /legal/compliance,
  |                 /legal/ai-governance, /legal/trust)
  |
  |-- Specialized Pages
        |-- Digital Twin Viewer (/digital-twin-viewer)
        |-- Financial Twin (/financial-twin)
        |-- Financials (/financials)
        |-- Opportunities (/opportunities)
        |-- Investor Dashboard (/investor-dashboard)
        |-- Procedural Registry (/procedural-registry)
        |-- Admin Peer Mediators (/admin/peer-mediators)
        |-- Research Portal Peer Mediators (/research-portal/peer-mediators)
```

### 3.2 UI Component Library

The application includes 49 shadcn/ui components built on Radix UI primitives, located in `src/components/ui/`:

| Category | Components |
|----------|-----------|
| Layout | `accordion`, `aspect-ratio`, `card`, `collapsible`, `resizable`, `scroll-area`, `separator`, `sheet`, `sidebar`, `tabs` |
| Navigation | `breadcrumb`, `dropdown-menu`, `menubar`, `navigation-menu`, `pagination` |
| Forms | `button`, `calendar`, `checkbox`, `form`, `input`, `input-otp`, `label`, `radio-group`, `select`, `slider`, `switch`, `textarea`, `toggle`, `toggle-group` |
| Feedback | `alert`, `alert-dialog`, `badge`, `dialog`, `drawer`, `hover-card`, `popover`, `progress`, `skeleton`, `spinner`, `toast`, `toaster`, `tooltip` |
| Data Display | `avatar`, `carousel`, `chart`, `context-menu`, `command`, `table` |
| Custom | `switch-role` |

All UI components follow the shadcn/ui pattern: unstyled Radix primitives composed with Tailwind CSS classes via `class-variance-authority` and `tailwind-merge`.

### 3.3 Feature Components

| Domain | Component | File | Type | Purpose |
|--------|-----------|------|------|---------|
| Auth | AuthProvider | `src/components/auth/AuthProvider.tsx` | Client | NextAuth SessionProvider wrapper |
| Auth | ProtectedRoute | `src/components/auth/ProtectedRoute.tsx` | Client | Route guard component |
| Dashboard | Dashboard | `src/components/Dashboard.tsx` | Client | Main dashboard composition |
| Dashboard | AppointmentCard | `src/components/dashboard/AppointmentCard.tsx` | Client | Appointment display card |
| Dashboard | HealthChart | `src/components/dashboard/HealthChart.tsx` | Client | Health metric chart |
| Dashboard | WellnessMetrics | `src/components/dashboard/WellnessMetrics.tsx` | Client | Wellness metric grid |
| Digital Twin | DigitalTwinCanvas | `src/components/digital-twin/DigitalTwinCanvas.tsx` | Client | Three.js WebGL humanoid |
| Digital Twin | DigitalTwinViewer | `src/components/digital-twin/DigitalTwinViewer.tsx` | Client | Viewer container |
| Digital Twin | HealthDataStream | `src/components/digital-twin/HealthDataStream.tsx` | Client | Real-time data display |
| Digital Twin | IHEPDigitalTwinRenderer | `src/components/digital-twin/IHEPDigitalTwinRenderer.ts` | Client | Extended renderer class |
| Calendar | CalendarView | `src/components/calendar/CalendarView.tsx` | Client | Calendar grid component |
| AI | ChatInterface | `src/components/ai/ChatInterface.tsx` | Client | AI chat component |
| Research | ResearchDashboard | `src/components/research/ResearchDashboard.tsx` | Client | Research portal view |
| Legal | LegalDocument | `src/components/LegalDocument.tsx` | Server | Legal page template |
| Layout | Header | `src/app/components/Header.tsx` | Client | Public page header |
| Layout | Footer | `src/app/components/Footer.tsx` | Server | Public page footer |
| Layout | MainLayout | `src/app/components/MainLayout.tsx` | Client | Public page layout wrapper |

### 3.4 Server vs Client Component Decision Matrix

| Criterion | Server Component | Client Component |
|-----------|-----------------|-----------------|
| User interaction (onClick, onChange) | -- | Required |
| useState, useEffect | -- | Required |
| useSession (NextAuth) | -- | Required |
| useRouter (navigation) | -- | Required |
| Data fetching (async/await) | Preferred | Via TanStack Query |
| Three.js / WebGL | -- | Required |
| Chart rendering | -- | Required |
| Static content (legal pages) | Preferred | -- |
| Metadata export | Required | -- |
| Form handling | -- | Required |

---

## 4. Data Architecture

### 4.1 Current Data Layer: File-Based JSON Mock Store

The `FileUserStore` class (`src/lib/mockStore.ts`) implements a lazy-loaded, file-persisted user store for development:

```
FileUserStore
  |
  |-- users: MockUser[]         (in-memory cache)
  |-- nextId: number            (auto-increment counter)
  |-- loaded: boolean           (lazy-load guard)
  |
  |-- ensureLoaded()            (reads data/mock-users.json on first access)
  |-- bootstrap()               (seeds demo user if file missing)
  |-- persist()                 (writes full array to JSON file)
  |-- getUserByUsername()       (linear scan by username)
  |-- getUserByEmail()          (linear scan by email)
  |-- createUser()              (append + persist)
```

**Lifecycle:**

1. First API request triggers `ensureLoaded()`
2. `ensureLoaded()` attempts to read `data/mock-users.json`
3. If file exists: parse JSON, hydrate `createdAt` strings to Date objects, set `nextId`
4. If file missing: call `bootstrap()` to seed demo user, write initial JSON
5. All mutations (`createUser`) call `persist()` to write the full array back to disk

### 4.2 State Management

| Layer | Technology | Scope |
|-------|-----------|-------|
| Server state | TanStack React Query v5 | API data caching, deduplication, background refetch |
| Auth state | NextAuth.js `useSession()` | Session object, loading/authenticated status |
| UI state | React `useState` / `useReducer` | Component-local state (menus, forms, toggles) |
| URL state | Next.js App Router | Route parameters, search params |
| Form state | React Hook Form v7 | Form values, validation errors, dirty tracking |

### 4.3 Data Flow: Request Lifecycle

```
User Action (click, form submit)
        |
        v
Client Component (React)
        |
        +-- For GET: TanStack useQuery(queryKey, queryFn)
        |       queryFn calls fetch('/api/...')
        |       Response cached by queryKey
        |       Stale data served while revalidating
        |
        +-- For POST: TanStack useMutation(mutationFn)
                mutationFn calls fetch('/api/...', {method: 'POST'})
                onSuccess: invalidateQueries(queryKey)
        |
        v
Next.js API Route Handler (src/app/api/.../route.ts)
        |
        +-- Validate input (Zod schema)
        +-- Check authentication (getServerSession -- planned)
        +-- Process request
        |
        v
Data Layer
        |
        +-- Development: mockStore.getUserByUsername() etc.
        +-- Production:  db.select().from(users).where(...) (planned)
        |
        v
Response (NextResponse.json())
        |
        v
Client Component receives JSON
        |
        v
React re-renders with new data
```

### 4.4 Database Migration Path

The system is designed for zero-downtime migration from mock store to PostgreSQL:

1. The Drizzle ORM schema (`src/shared/schema.ts`) mirrors the mock store data structure
2. The `src/lib/db.ts` module exports `db` (Drizzle instance) or `null` (when no DB configured)
3. API routes can be updated incrementally: each route checks `isDatabaseAvailable()` and falls back to mock store
4. Migration scripts: `npm run db:generate` (SQL) -> `npm run db:migrate` (apply)

---

## 5. Authentication Design

### 5.1 NextAuth.js Flow

```
User visits /login
        |
        v
Login Form (Client Component)
        |-- username, password fields
        |-- Submit calls signIn('credentials', {...})
        |
        v
NextAuth POST /api/auth/callback/credentials
        |
        v
CredentialsProvider.authorize()
        |-- mockStore.getUserByUsername(username)
        |-- bcrypt.compare(password, user.password)
        |-- Returns user object or null
        |
        v
NextAuth JWT Callback
        |-- Encodes user data into JWT claims
        |-- Sets role, username, firstName, lastName
        |
        v
Set-Cookie: next-auth.session-token=<JWT>
        |-- HttpOnly, Secure, SameSite=Lax
        |-- Expires: 30 minutes
        |
        v
Redirect to /dashboard
```

### 5.2 JWT Token Lifecycle

```
                    +----------------+
                    |  Login         |
                    +--------+-------+
                             |
                    +--------v-------+
                    |  JWT Created   |
                    |  exp = now +   |
                    |  1800 seconds  |
                    +--------+-------+
                             |
                    +--------v-------+
                    |  Active        |
                    |  (30 min)      |
                    +--------+-------+
                             |
              +--------------+--------------+
              |                             |
    +---------v---------+         +---------v---------+
    |  User Activity    |         |  No Activity      |
    |  (extends via     |         |  (token expires)  |
    |  NextAuth session |         +---------+---------+
    |  refresh)         |                   |
    +---------+---------+         +---------v---------+
              |                   |  Redirect to      |
              +----> loop        |  /login            |
                                  +-------------------+
```

### 5.3 Protected Route Pattern

The dashboard layout (`src/app/dashboard/layout.tsx`) implements client-side route protection:

```typescript
// 1. Check session status
const { data: session, status } = useSession()

// 2. Redirect unauthenticated
useEffect(() => {
  if (status === 'unauthenticated') {
    router.push('/login')
  }
}, [status, router])

// 3. Show loading while checking
if (status === 'loading') return <Spinner />

// 4. Guard against null session
if (!session) return null

// 5. Render dashboard with navigation
return <DashboardShell>{children}</DashboardShell>
```

### 5.4 Role-Based Access Control Design

| Role | Access Scope | Current Implementation |
|------|-------------|----------------------|
| `patient` | Own data, public resources, community | Default role on registration |
| `provider` | Assigned patient data, provider tools | Manually assigned |
| `admin` | All data, user management, system config | Registration blocked (requires institutional approval) |

RBAC is enforced at two levels:
1. **Client-side**: Conditional rendering based on `session.user.role`
2. **Server-side**: `getServerSession(authOptions)` check in API routes (planned)

---

## 6. Security Design

### 6.1 Seven-Layer Defense Model

The IHEP security architecture implements defense-in-depth across seven layers:

```
Layer 7: Application Security
  |-- Input validation (Zod schemas)
  |-- Output encoding (React auto-escaping)
  |-- RBAC enforcement
  |
Layer 6: Session Security
  |-- JWT with 30-minute expiry
  |-- HttpOnly, Secure cookies
  |-- CSRF protection (NextAuth built-in)
  |
Layer 5: Data Security
  |-- Field-level PQC encryption (PHI)
  |-- bcrypt password hashing (cost 12)
  |-- Constant-time comparisons
  |
Layer 4: Transport Security
  |-- TLS 1.3 (Cloud Run enforced)
  |-- HSTS with preload
  |-- upgrade-insecure-requests
  |
Layer 3: Content Security
  |-- CSP (strict, no unsafe-eval in prod)
  |-- X-Frame-Options: DENY
  |-- X-Content-Type-Options: nosniff
  |-- COOP/COEP for isolation
  |
Layer 2: Infrastructure Security
  |-- GCP VPC networking
  |-- Cloud SQL with SSL
  |-- Secret Manager for credentials
  |
Layer 1: Audit and Monitoring
  |-- HIPAA audit log schema
  |-- PHI access tracking
  |-- Error logging (no PHI in logs)
```

### 6.2 PHI Handling Patterns

**Branded Types (TypeScript):**

```typescript
type PatientId = string & { readonly __brand: 'PatientId' }
type EncryptedPHI = string & { readonly __brand: 'EncryptedPHI' }
```

**Field-Level Encryption:**

The `HybridEncryption` class (`src/lib/crypto/pqc-hybrid-encryption.ts`) provides `encryptPHI()` and `decryptPHI()` methods that encrypt individual object fields while leaving non-sensitive fields in plaintext. Encrypted fields are marked with a `{field}_encrypted: true` flag.

**PHI Data Flow:**

```
User Input (browser)
    |
    v
API Route Handler (validate with Zod)
    |
    v
Encrypt PHI Fields (HybridEncryption.encryptPHI)
    |-- Generates random DEK
    |-- Encrypts field with XChaCha20-Poly1305
    |-- Wraps DEK with Kyber KEM
    |
    v
Store Encrypted Record (database)
    |
    v (on retrieval)
Decrypt PHI Fields (HybridEncryption.decryptPHI)
    |-- Unwraps DEK with Kyber secret key
    |-- Decrypts field with XChaCha20-Poly1305
    |
    v
Return to Client (memory-only, no client storage)
```

### 6.3 Audit Logging Architecture

The audit log schema (`src/shared/schema.ts:425-437`) captures:

```
audit_logs
  |-- id (serial PK)
  |-- timestamp (default NOW)
  |-- userId (FK -> users.id)
  |-- eventType (PHI_ACCESS | PHI_MODIFICATION | PHI_DELETION |
  |               AUTHENTICATION | AUTHORIZATION | SYSTEM_EVENT)
  |-- resourceType (e.g., "patient_record", "appointment")
  |-- resourceId (string)
  |-- action (e.g., "read", "write", "delete")
  |-- description (human-readable)
  |-- ipAddress (string)
  |-- success (boolean)
  |-- additionalInfo (JSONB, optional)
```

### 6.4 Post-Quantum Cryptography Integration

The PQC subsystem (`src/lib/crypto/`) provides three levels of abstraction:

```
KyberKEM (pqc-kyber.ts)
  |-- Key generation (generateKeyPair)
  |-- Encapsulation (encapsulate)
  |-- Decapsulation (decapsulate)
  |-- Key derivation (deriveKey via HKDF-SHA512)
  |
  v
HybridKEM (pqc-kyber.ts)
  |-- Combines Kyber with context-bound HKDF
  |-- Context string: "IHEP-Hybrid-KEM-v1"
  |
  v
HybridEncryption (pqc-hybrid-encryption.ts)
  |-- encrypt(plaintext, publicKey, keyId) -> EncryptedData
  |-- decrypt(encrypted, secretKey) -> DecryptedData
  |-- encryptPHI(data, fields, publicKey, keyId) -> encrypted object
  |-- decryptPHI(data, fields, secretKey) -> decrypted object
  |-- reencrypt(encrypted, oldKey, newPubKey, newKeyId) -> re-encrypted
  |
  v
MultiRecipientEncryption (pqc-hybrid-encryption.ts)
  |-- encryptForMultiple(plaintext, recipients[]) -> EncryptedData[]
```

---

## 7. Digital Twin Design

### 7.1 Five-Pillar Architecture

Each digital twin pillar represents a distinct dimension of patient health:

| Pillar | Focus | Key Metrics | Score Range |
|--------|-------|------------|-------------|
| Clinical | Medical treatment adherence and lab results | Adherence %, Vitals stability %, Labs currency % | 0-100 |
| Behavioral | Lifestyle patterns and mental health | Sleep quality, Activity level, Mood frequency | 0-100 |
| Social | Support network and social determinants | Support touches, Group attendance, Housing stability | 0-100 |
| Financial | Economic health and opportunity access | Benefits utilization, Cash flow buffer, Opportunities | 0-100 |
| Personal | Goal achievement and engagement | Goal completion, Engagement %, Sentiment score | 0-100 |

### 7.2 Three.js Rendering Pipeline

```
DigitalTwinCanvas Component Mount
        |
        v
Initialize Three.js Scene
  |-- Scene (transparent background)
  |-- PerspectiveCamera (FOV 75, z=5)
  |-- WebGLRenderer (antialias, alpha)
  |
  v
Construct Humanoid Group
  |-- Head: SphereGeometry(r=0.3) at y=1.8
  |-- Body: CapsuleGeometry(r=0.4, h=1.2) at y=0.6
  |-- Left Arm: CapsuleGeometry(r=0.15, h=0.8) at (-0.6, 0.8, 0)
  |-- Right Arm: CapsuleGeometry(r=0.15, h=0.8) at (0.6, 0.8, 0)
  |-- Left Leg: CapsuleGeometry(r=0.2, h=1.0) at (-0.2, -0.7, 0)
  |-- Right Leg: CapsuleGeometry(r=0.2, h=1.0) at (0.2, -0.7, 0)
  |-- Material: MeshStandardMaterial (emissive, transparent)
  |
  v
Add Lighting
  |-- AmbientLight (white, intensity 0.5)
  |-- PointLight (white, intensity 1.0, position (2,2,2))
  |-- PointLight (blue, intensity 0.5, position (-2,1,-2))
  |
  v
Animation Loop (60fps)
  |-- Rotation: group.rotation.y += 0.002 (per frame)
  |-- Pulsation: scale = 1 + sin(t * pulseSpeed * 2pi) * 0.03
  |       pulseSpeed = 0.5 + normalizedHR * 2.0
  |       normalizedHR = clamp((heartRate - 40) / 80, 0, 1)
  |-- Color mapping:
  |       healthScore >= 80: green (0x00ff88)
  |       healthScore >= 50: orange (0xffaa00)
  |       healthScore <  50: red (0xff3300)
  |-- Opacity: max(0.3, 1 - viralLoad/1000)
  |
  v
Cleanup on Unmount
  |-- cancelAnimationFrame
  |-- Remove renderer DOM element
  |-- Dispose renderer
```

### 7.3 USDZ/USD Asset Loading

The build pipeline supports OpenUSD assets through Webpack configuration:

- `.usdz`, `.usda`, `.usdc` files treated as `asset/resource` (generates URL, copies to output)
- `three-usdz-loader` package transpiled for browser compatibility
- SharedArrayBuffer enabled via COOP/COEP headers (required for WASM-based USDZ parsing)

### 7.4 Morphogenetic Agent Design

The morphogenetic framework (referenced from `core/security/`) defines three agent types:

| Agent | Role | Analogy |
|-------|------|---------|
| Weaver | Constructs and maintains data flows | Tissue formation |
| Builder | Assembles composite views from twin data | Organ assembly |
| Scavenger | Detects and removes anomalous data | Immune response |

These agents operate on the reaction-diffusion pattern where health state changes propagate through the twin system via partial differential equations. The agents are implemented in the core security module and communicate with the hub via spoke service APIs.

---

## 8. Mathematical Models

### 8.1 Extended Kalman Filter (EKF)

**Location:** `src/lib/simulation/ekf.ts`

The EKF estimates the patient's health state vector from noisy observations. The state vector represents position and velocity in a health parameter space.

**State Vector:**

```
x = [px, py, vx, vy]^T
```

Where `px, py` represent health parameter positions and `vx, vy` represent rates of change.

**Dynamics Model (constant acceleration):**

```
px(k+1) = px(k) + vx(k)*dt + 0.5*ax*dt^2
py(k+1) = py(k) + vy(k)*dt + 0.5*ay*dt^2
vx(k+1) = vx(k) + ax*dt
vy(k+1) = vy(k) + ay*dt
```

Where `dt = 1/60` (one frame at 60fps).

**State Transition Jacobian F:**

```
F = | 1  0  dt  0 |
    | 0  1  0  dt |
    | 0  0  1   0 |
    | 0  0  0   1 |
```

**Measurement Model H (observes position only):**

```
H = | 1  0  0  0 |
    | 0  1  0  0 |
```

**Noise Parameters:**

```
Process noise Q = diag(2, 2, 6, 6)
Measurement noise R = diag(30, 30)
Initial covariance P0 = 200 * I_4
```

**EKF Step (predict + update):**

```
Predict:
  x_pred = f(x, a)                    // Dynamics model
  P_pred = F * P * F^T + Q            // Covariance prediction

Update:
  y = z - H * x_pred                  // Innovation (measurement residual)
  S = H * P_pred * H^T + R            // Innovation covariance
  K = P_pred * H^T * S^{-1}           // Kalman gain
  x_new = x_pred + K * y              // State update
  P_new = (I - K * H) * P_pred        // Covariance update
```

**Verification:** The EKF implementation follows the standard formulation from Welch & Bishop (2006), "An Introduction to the Kalman Filter." The 2x2 matrix inversion uses the closed-form formula `det = ad - bc`.

### 8.2 Control Barrier Functions (CBF)

**Location:** `src/lib/simulation/cbf.ts`

CBFs enforce safety constraints by modifying control inputs to keep the system within a defined safe set.

**Barrier Function:**

```
h(x) = ||p - c|| - r - eps
```

Where:
- `p` = current position (health state)
- `c` = obstacle center (danger zone)
- `r` = obstacle radius
- `eps` = safety margin

Safety condition: `h(x) >= 0`

**CBF Constraint:**

```
dh/dt >= -alpha * h(x)
```

Where `alpha` controls aggressiveness (default: 3.5). This ensures the barrier function remains non-negative.

**Time Derivative:**

```
dh/dt = n . v

where n = (p - c) / ||p - c||  (unit normal away from obstacle)
```

**Control Modification:**

When the nominal control `a_nom` violates the CBF constraint (`n . a_nom < b`), the control is projected:

```
b = -dh - alpha * h
correction = (b - n . a_nom) / (n . n + epsilon)
a_adjusted = a_nom + n * correction
```

**Verification:** The CBF formulation follows Ames et al. (2017), "Control Barrier Function Based Quadratic Programs for Safety Critical Systems." The projection computes the minimum-norm correction to satisfy the affine constraint `n . a >= b`.

### 8.3 Matrix Operations Library

**Location:** `src/lib/simulation/math.ts`

| Function | Signature | Operation |
|----------|-----------|-----------|
| `matEye(n, s)` | `(number, number) => Matrix` | Scaled identity matrix `s * I_n` |
| `matAdd(A, B)` | `(Matrix, Matrix) => Matrix` | Element-wise addition |
| `matSub(A, B)` | `(Matrix, Matrix) => Matrix` | Element-wise subtraction |
| `matMul(A, B)` | `(Matrix, Matrix) => Matrix` | Standard matrix multiplication O(n^3) |
| `matVec(A, x)` | `(Matrix, Vector) => Vector` | Matrix-vector product |
| `matT(A)` | `(Matrix) => Matrix` | Transpose |
| `matInv2(A)` | `(Matrix) => Matrix` | 2x2 inverse via `det = ad - bc` |
| `hypot(x, y)` | `(number, number) => number` | Euclidean distance `sqrt(x^2 + y^2)` |

All operations use `Float64Array` for vectors (64-bit IEEE 754 double precision) and `number[][]` for matrices.

---

## 9. Integration Design

### 9.1 Backend Spoke Service Communication

The hub communicates with spoke services via HTTP. Currently, all data is mocked within the hub's API routes. When spokes are deployed:

```
Hub API Route                     Spoke Service
+-------------------+            +-------------------+
| GET /api/twins/   | ---------> | clinical spoke    |
|   clinical        |   HTTP     | GET /v1/snapshot  |
+-------------------+            +-------------------+

Pattern:
1. Hub API route receives client request
2. Route handler calls spoke service URL (env-configured)
3. Spoke returns domain data
4. Hub aggregates/transforms and returns to client
```

**Spoke Registry (planned):**

| Spoke | Purpose | Port |
|-------|---------|------|
| api-gateway | Request routing and rate limiting | 8080 |
| auth | User management and token validation | 8081 |
| clinical | Clinical twin computation | 8082 |
| financial | Financial twin and opportunity matching | 8083 |
| digital-twin | Twin synthesis and 3D model generation | 8084 |
| wellness | Wellness metric aggregation | 8085 |
| providers | Provider directory and matching | 8086 |
| calendar | Appointment scheduling | 8087 |
| notifications | Push and email notifications | 8088 |
| health-monitor | Real-time vital sign processing | 8089 |
| resources | Resource directory and search | 8090 |
| telehealth | Video call coordination | 8091 |
| gig-finder | Employment opportunity matching | 8092 |
| investor-dashboard | Investor metrics | 8093 |
| research | Research data management | 8094 |
| provider-search | Provider search indexing | 8095 |

### 9.2 FHIR Adapter Pattern

The FHIR integration follows the adapter pattern:

```
Hub API Route
    |
    v
FHIR Adapter (spoke)
    |-- Translates IHEP domain objects to FHIR R4 resources
    |-- Translates FHIR R4 resources to IHEP domain objects
    |
    v
External EHR System (Epic, Cerner, etc.)
```

**Mapped FHIR Resources:**

| IHEP Entity | FHIR Resource |
|------------|---------------|
| User (patient) | Patient |
| Twin metrics | Observation |
| Appointment | Appointment |
| Provider | Practitioner |
| Health monitor vitals | Observation (vital-signs) |

### 9.3 EHR Integration Architecture

```
+---------+     +---------+     +----------+
| IHEP    |     | FHIR    |     | EHR      |
| Hub     |---->| Adapter |---->| System   |
|         |     | Spoke   |     | (Epic/   |
|         |<----|         |<----| Cerner)  |
+---------+     +---------+     +----------+
                    |
                    v
              +-----------+
              | FHIR R4   |
              | Resources |
              +-----------+
```

---

## 10. Error Handling and Resilience

### 10.1 Error Boundary Hierarchy

```
RootLayout (src/app/layout.tsx)
    |-- No error boundary (renders globally)
    |
    +-- DashboardLayout (src/app/dashboard/layout.tsx)
    |     |-- Session error: redirect to /login
    |     |-- Loading state: spinner component
    |     |
    |     +-- Individual Page Components
    |           |-- API errors caught by TanStack Query
    |           |-- Render errors caught by React error boundaries (planned)
    |
    +-- API Route Handlers
          |-- Zod validation errors: HTTP 400 with formatted messages
          |-- Business logic errors: HTTP 4xx with message
          |-- Unhandled exceptions: HTTP 500 with generic message
          |-- No PHI in error responses
```

### 10.2 Graceful Degradation Strategy

| Failure | Degradation |
|---------|-------------|
| Database unavailable | Falls back to file-based mock store (dev only) |
| WebGL not supported | Display 2D fallback for digital twin (planned) |
| API endpoint fails | TanStack Query shows stale cached data + error indicator |
| Session expired | Client-side redirect to /login |
| JavaScript disabled | Server-rendered HTML (limited interactivity) |
| Spoke service down | Hub returns cached data or graceful error message |

### 10.3 Loading and Suspense Patterns

| Pattern | Implementation | Location |
|---------|---------------|----------|
| Session loading | Conditional spinner render | `src/app/dashboard/layout.tsx:41-49` |
| Page loading | `loading.tsx` files (planned) | Each route segment |
| Data loading | TanStack Query `isLoading` state | Client components |
| Component loading | `dynamic()` with loading prop | Heavy components (Three.js) |

---

## 11. Build and Deployment Design

### 11.1 Turbopack Build Pipeline

```
Source Files (TypeScript + TSX)
        |
        v
TypeScript Compilation (strict mode)
  |-- Path alias resolution (@/* -> ./src/*)
  |-- Type checking (tsc --noEmit)
  |
  v
Turbopack / Webpack Bundling
  |-- Server Components -> Server bundle
  |-- Client Components -> Client bundle (code-split)
  |-- API Routes -> Server functions
  |-- Three.js -> Transpiled, externalized on server
  |-- GLSL shaders -> Asset source
  |-- USDZ files -> Asset resource
  |
  v
React Compiler Optimization
  |-- Automatic memoization
  |-- Component optimization
  |
  v
Standalone Output (.next/standalone/)
  |-- server.js (self-contained Node.js server)
  |-- node_modules (minimal, traced dependencies)
  |-- .next/static/ (client assets)
  |-- public/ (static files)
```

### 11.2 Standalone Output Packaging

The `output: 'standalone'` configuration produces a self-contained deployment artifact:

```
.next/standalone/
  |-- server.js          # Entry point (Node.js)
  |-- node_modules/      # Traced minimal dependencies
  |-- package.json       # Minimal package descriptor
  |
  +-- .next/
        |-- static/      # Client-side assets (JS, CSS)
        |-- server/      # Server-side compiled pages
```

The `outputFileTracingRoot` is set to `__dirname` to force correct dependency tracing in the monorepo context.

### 11.3 Environment Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NODE_ENV` | No | `development` | Runtime environment |
| `SESSION_SECRET` | Yes (prod) | -- | NextAuth JWT signing secret |
| `DATABASE_URL` | Yes (prod) | -- | PostgreSQL connection string |
| `DB_POOL_SIZE` | No | `10` | Database connection pool size |
| `GOOGLE_CLIENT_ID` | No | -- | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | -- | Google OAuth client secret |
| `NEXT_PUBLIC_APP_URL` | No | `https://ihep.app` | Public-facing URL |

### 11.4 CI/CD Pipeline Design

The CI/CD pipeline targets GitHub Actions with the following stages:

```
Push to Branch
        |
        v
Stage 1: Lint + Type Check
  |-- eslint (src/**/*.{ts,tsx})
  |-- tsc --noEmit
  |
  v
Stage 2: Unit Tests
  |-- vitest run
  |-- Coverage threshold: 80%
  |
  v
Stage 3: Build
  |-- next build
  |-- Verify standalone output
  |
  v
Stage 4: Security Scan
  |-- npm audit
  |-- OSV scanner
  |
  v
Stage 5: Deploy (per environment)
  |-- dev: auto-deploy on main
  |-- staging: manual approval
  |-- production: manual approval + smoke tests
```

---

**End of Document**
