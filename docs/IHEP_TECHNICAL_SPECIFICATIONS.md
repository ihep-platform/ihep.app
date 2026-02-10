# IHEP Technical Specifications Document

**Document Identifier:** IHEP-TS-2026-001
**Version:** 1.0
**Date:** 2026-02-10
**Status:** Draft
**Author:** Jason M Jarmacz | Evolution Strategist | jason@ihep.app
**Co-Author:** Claude by Anthropic

**Standard:** IEEE 1233 (System Requirements Specification) + Traditional Technical Specification Format
**Classification:** Internal -- Confidential

---

## Revision History

| Version | Date       | Author        | Description            |
|---------|------------|---------------|------------------------|
| 1.0     | 2026-02-10 | J. Jarmacz / Claude | Initial release |

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack Specification](#2-technology-stack-specification)
3. [API Specifications](#3-api-specifications)
4. [Data Model Specifications](#4-data-model-specifications)
5. [Authentication Specification](#5-authentication-specification)
6. [Security Specifications](#6-security-specifications)
7. [Data Persistence Specification](#7-data-persistence-specification)
8. [External Interface Specifications](#8-external-interface-specifications)
9. [Error Handling Specification](#9-error-handling-specification)

---

## 1. System Overview

### 1.1 Architecture Overview

IHEP uses a hub-and-spoke architecture. The hub is a Next.js 16.1.5 application that serves as the patient-facing frontend, API gateway, and server-side rendering engine. Backend spokes are planned microservices for domain-specific computation.

```
                     Internet
                        |
                  +-----+-----+
                  |   GCP LB  |
                  +-----+-----+
                        |
               +--------+--------+
               | Cloud Run       |
               | (Next.js Hub)   |
               |   Port 3000     |
               +--------+--------+
                        |
          +-------------+-------------+
          |             |             |
    +-----+-----+ +----+----+ +-----+-----+
    | Cloud SQL | | BigQuery| | Cloud     |
    | (Postgres)| | (Anlytc)| | Storage   |
    +-----------+ +---------+ +-----------+
```

### 1.2 Deployment Topology

| Component | Current (Development) | Target (Production) |
|-----------|----------------------|-------------------|
| Frontend + API | `npm run dev` (localhost:3000) | GCP Cloud Run (standalone container) |
| Database | File-based mock store (`data/mock-users.json`) | GCP Cloud SQL (PostgreSQL 15) |
| Analytics | Not configured | GCP BigQuery |
| File Storage | Local filesystem | GCP Cloud Storage |
| Secrets | `.env.local` file | GCP Secret Manager |
| CDN | Next.js built-in | GCP Cloud CDN |
| DNS | localhost | Custom domain via GCP Cloud DNS |

### 1.3 Build Configuration

The application produces a standalone output suitable for containerized deployment:

- **Build command:** `next build`
- **Output mode:** `standalone` (self-contained Node.js server)
- **Bundler:** Turbopack (default for Next.js 16), Webpack available via `--webpack` flag
- **React Compiler:** Enabled (`reactCompiler: true`)
- **Transpile packages:** `three`, `three-usdz-loader`

---

## 2. Technology Stack Specification

### 2.1 Runtime Dependencies

| Package | Version | Purpose | Justification |
|---------|---------|---------|--------------|
| `next` | 16.1.5 | Application framework | App Router, Server Components, API routes, standalone output |
| `react` | 19.2.3 | UI library | Component model, hooks, concurrent features |
| `react-dom` | 19.2.3 | DOM renderer | Browser rendering for React components |
| `typescript` | ^5 | Language | Strict type safety for enterprise healthcare application |
| `next-auth` | ^4.24.13 | Authentication | JWT sessions, credential + OAuth providers |
| `bcryptjs` | ^3.0.3 | Password hashing | OWASP-recommended bcrypt with configurable cost factor |
| `zod` | ^4.2.1 | Schema validation | Runtime type checking at API boundaries |
| `drizzle-orm` | ^0.45.1 | Database ORM | Type-safe PostgreSQL queries |
| `postgres` | ^3.4.8 | PostgreSQL driver | Connection pooling, prepared statements |
| `three` | ^0.182.0 | 3D rendering | WebGL-based digital twin humanoid visualization |
| `three-usdz-loader` | ^1.0.9 | USD asset loading | OpenUSD scene file parsing for 3D assets |
| `@noble/post-quantum` | ^0.5.4 | Post-quantum cryptography | ML-KEM (Kyber) key encapsulation per FIPS 203 |
| `@stablelib/xchacha20poly1305` | ^2.0.1 | Symmetric encryption | AEAD cipher for PHI encryption |
| `@stablelib/hkdf` | ^2.0.1 | Key derivation | HKDF-SHA512 for deriving encryption keys from KEM shared secrets |
| `@stablelib/sha512` | ^2.0.1 | Hashing | SHA-512 for metadata integrity verification |
| `@stablelib/random` | ^2.0.1 | Secure random | Cryptographically secure random byte generation |
| `@tanstack/react-query` | ^5.90.20 | Server state management | Caching, deduplication, optimistic updates |
| `@tanstack/react-table` | ^8.21.3 | Table rendering | Data table with sorting, filtering, pagination |
| `@hookform/resolvers` | ^5.2.2 | Form validation bridge | Connects React Hook Form with Zod schemas |
| `react-hook-form` | ^7.71.1 | Form management | Uncontrolled forms with validation |
| `framer-motion` | ^12.26.2 | Animation | Page transitions, component animations |
| `recharts` | ^3.6.0 | Charts | Health metric visualizations |
| `chart.js` | ^4.5.1 | Charts | Additional chart types |
| `react-chartjs-2` | ^5.3.1 | Chart.js bridge | React wrapper for Chart.js |
| `lucide-react` | ^0.563.0 | Icons | Consistent icon set |
| `date-fns` | ^4.1.0 | Date utilities | Date formatting and manipulation |
| `axios` | ^1.13.2 | HTTP client | API requests from client components |
| `jsonwebtoken` | ^9.0.3 | JWT handling | Token generation and verification |
| `class-variance-authority` | ^0.7.1 | Component variants | Type-safe CSS class variants for shadcn/ui |
| `clsx` | ^2.1.1 | Class merging | Conditional CSS class composition |
| `tailwind-merge` | ^3.4.0 | Tailwind merging | Conflict-free Tailwind class merging |
| `cmdk` | ^1.1.1 | Command palette | Keyboard-accessible command menu |
| `vaul` | ^1.1.2 | Drawer | Mobile-friendly drawer component |
| `embla-carousel-react` | ^8.6.0 | Carousel | Touch-friendly carousel |
| `input-otp` | ^1.4.2 | OTP input | One-time password input component |
| `react-day-picker` | ^9.13.0 | Date picker | Calendar date selection |
| `react-resizable-panels` | ^4.5.1 | Resizable panels | Adjustable panel layouts |

### 2.2 Radix UI Primitives

The following Radix UI primitives are installed and used via shadcn/ui component wrappers:

`accordion`, `alert-dialog`, `aspect-ratio`, `avatar`, `checkbox`, `collapsible`, `context-menu`, `dialog`, `dropdown-menu`, `hover-card`, `label`, `menubar`, `navigation-menu`, `popover`, `progress`, `radio-group`, `scroll-area`, `select`, `separator`, `slider`, `slot`, `switch`, `tabs`, `toast`, `toggle`, `toggle-group`, `tooltip`

### 2.3 Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `vitest` | ^4.0.16 | Unit test runner |
| `@testing-library/react` | ^16.3.1 | React component testing |
| `@testing-library/jest-dom` | ^6.9.1 | DOM assertion matchers |
| `@testing-library/user-event` | ^14.6.1 | User interaction simulation |
| `jsdom` | ^27.4.0 | DOM environment for tests |
| `drizzle-kit` | ^0.31.8 | Database migration tooling |
| `eslint` | ^9 | Code linting |
| `eslint-config-next` | 16.1.3 | Next.js lint rules |
| `tailwindcss` | ^4 | CSS utility framework |
| `@tailwindcss/postcss` | ^4 | PostCSS integration |
| `babel-plugin-react-compiler` | 1.0.0 | React Compiler Babel plugin |
| `esbuild` | ^0.27.2 | JavaScript bundler (for Drizzle Kit) |

### 2.4 TypeScript Configuration

```
Target:          ES2017
Module:          esnext
Module Resolution: bundler
Strict Mode:     true
JSX:             react-jsx
Incremental:     true
Path Aliases:    @/* -> ./src/*, @shared/* -> ./src/shared/*
Excludes:        node_modules, scripts, tests
```

---

## 3. API Specifications

All API routes are implemented as Next.js Route Handlers in `src/app/api/`. Unless noted, all endpoints currently return mock data and lack authentication guards.

### 3.1 Authentication Endpoints

#### 3.1.1 NextAuth Handler

| Field | Value |
|-------|-------|
| **Path** | `/api/auth/[...nextauth]` |
| **Methods** | GET, POST |
| **Auth Required** | No (this IS the auth handler) |
| **Source** | `src/app/api/auth/[...nextauth]/route.ts` |
| **Description** | NextAuth.js catch-all handler for sign-in, sign-out, session, CSRF, and callback operations. |

#### 3.1.2 User Registration

| Field | Value |
|-------|-------|
| **Path** | `/api/auth/register` |
| **Method** | POST |
| **Auth Required** | No |
| **Source** | `src/app/api/auth/register/route.ts` |

**Request Schema (Zod):**

```typescript
{
  username: string     // min 3 chars
  password: string     // min 12 chars, complexity regex
  email: string        // valid email format
  firstName: string    // min 1 char
  lastName: string     // min 1 char
  role: string         // default: 'patient'
  profilePicture?: string
  phone?: string
  preferredContactMethod?: string
}
```

**Response (201 Created):**

```typescript
{
  user: {
    id: number
    username: string
    email: string
    firstName: string
    lastName: string
    role: string
    profilePicture: string | null
    phone: string | null
    preferredContactMethod: string | null
    createdAt: string  // ISO 8601
  }
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Validation failure | `{ message: string, errors: ZodIssue[] }` |
| 400 | Duplicate username | `{ message: "Username already exists" }` |
| 400 | Duplicate email | `{ message: "Email address is already registered..." }` |
| 403 | Role is 'admin' | `{ message: "Administrator accounts require institutional approval..." }` |
| 500 | Server error | `{ message: "Registration failed" }` |

### 3.2 Health Check Endpoints

#### 3.2.1 System Health

| Field | Value |
|-------|-------|
| **Path** | `/api/health` |
| **Method** | GET |
| **Auth Required** | No |
| **Source** | `src/app/api/health/route.ts` |

**Response (200 OK):**

```typescript
{
  status: "healthy"
  timestamp: string     // ISO 8601
  uptime: number        // process uptime in seconds
  environment: string   // "development" | "production"
  version: string       // e.g. "1.1.0-alpha"
}
```

#### 3.2.2 Health Monitor

| Field | Value |
|-------|-------|
| **Path** | `/api/health/monitor` |
| **Method** | GET |
| **Auth Required** | No (should be Yes in production) |
| **Source** | `src/app/api/health/monitor/route.ts` |

**Response (200 OK):**

```typescript
{
  overall: number              // 0-100 composite score
  trend: "up" | "stable" | "down"
  vitals: Array<{
    name: string               // e.g. "Heart rate", "BP", "SpO2"
    value: string              // e.g. "72 bpm", "122/78"
    status: "ok" | "warning" | "critical"
  }>
  alerts: string[]             // e.g. ["HRV slightly low vs baseline..."]
}
```

### 3.3 Digital Twin Endpoints

All twin endpoints use the shared mock data builder in `src/app/api/twins/mock-data.ts`.

#### 3.3.1 Individual Twin Snapshot

| Field | Value |
|-------|-------|
| **Path** | `/api/twins/{clinical|behavioral|social|financial|personal}` |
| **Method** | GET |
| **Auth Required** | No (should be Yes in production) |
| **Source** | `src/app/api/twins/{pillar}/route.ts` |

**Response (200 OK):**

```typescript
{
  pillar: "clinical" | "behavioral" | "social" | "financial" | "personal"
  score: number                // 0-100
  trend: "up" | "stable" | "down"
  metrics: Array<{
    name: string
    value: number
    unit?: string
    status: "ok" | "warning" | "critical"
  }>
  insights: Array<{
    title: string
    summary: string
    recommendation: string
    severity: "low" | "medium" | "high"
  }>
  lastUpdated: string          // ISO 8601
}
```

#### 3.3.2 Twin Summary

| Field | Value |
|-------|-------|
| **Path** | `/api/twins/summary` |
| **Method** | GET |
| **Auth Required** | No (should be Yes in production) |
| **Source** | `src/app/api/twins/summary/route.ts` |

**Response (200 OK):**

```typescript
{
  snapshots: TwinSnapshot[]    // Array of 5 twin snapshots (see 3.3.1)
}
```

### 3.4 Calendar Endpoints

#### 3.4.1 Calendar Events

| Field | Value |
|-------|-------|
| **Path** | `/api/calendar/events` |
| **Methods** | GET, POST |
| **Auth Required** | No (should be Yes in production) |
| **Source** | `src/app/api/calendar/events/route.ts` |

**GET Response (200 OK):**

```typescript
{
  events: Array<{
    id: string
    title: string
    provider: string
    specialty: string
    datetime: string           // ISO 8601
    durationMinutes: number
    location: string
    type: "In-Person" | "Telehealth"
  }>
}
```

**POST Request:**

```typescript
{
  title?: string               // default: "New appointment"
  provider?: string            // default: "TBD"
  specialty?: string           // default: "General"
  datetime?: string            // default: now
  durationMinutes?: number     // default: 30
  location?: string            // default: "Virtual"
  type?: "In-Person" | "Telehealth"  // default: "Telehealth"
}
```

**POST Response (201 Created):**

```typescript
{
  event: CalendarEvent         // same shape as GET items
}
```

### 3.5 Financial Endpoints

#### 3.5.1 Opportunities

| Field | Value |
|-------|-------|
| **Path** | `/api/financial/opportunities` |
| **Method** | GET |
| **Source** | `src/app/api/financial/opportunities/route.ts` |

**Response (200 OK):**

```typescript
{
  opportunities: Array<{
    id: string
    title: string
    category: string           // e.g. "Part-time", "Remote", "Peer work"
    payout: string             // e.g. "$22/hr", "$150/week"
    matchScore: number         // 0-100
    status: "new" | "in-progress" | "applied"
  }>
}
```

#### 3.5.2 Benefits, Personal Finance, Focus Groups

| Path | Method | Response Shape |
|------|--------|---------------|
| `/api/financial/benefits` | GET | Domain-specific benefits data |
| `/api/financial/personal-finance` | GET | Personal finance tracking data |
| `/api/financial/focus-groups` | GET | Focus group management data |

### 3.6 Resources Endpoint

| Field | Value |
|-------|-------|
| **Path** | `/api/resources/search` |
| **Method** | GET |
| **Source** | `src/app/api/resources/search/route.ts` |

**Response (200 OK):**

```typescript
{
  results: Array<{
    id: string
    name: string
    category: string           // "Clinic", "Peer Support", "Diagnostics", "Pharmacy"
    distanceMiles: number
    address: string
    rating: number             // e.g. 4.7
  }>
}
```

### 3.7 Provider Endpoints

#### 3.7.1 Provider List

| Field | Value |
|-------|-------|
| **Path** | `/api/providers/list` |
| **Method** | GET |
| **Source** | `src/app/api/providers/list/route.ts` |

**Response (200 OK):**

```typescript
{
  providers: Array<{
    id: string
    userId: string
    firstName: string
    lastName: string
    title: string              // e.g. "MD", "LCSW"
    specialty: string
    licenseNumber: string
    email: string
    phone: string
    bio: string
    yearsOfExperience: number
    languages: string[]
    acceptingNewPatients: boolean
    rating: number
    reviewCount: number
    location: {
      facilityName: string
      address: string
      city: string
      state: string
      zipCode: string
    }
    createdAt: string          // ISO 8601
    updatedAt: string          // ISO 8601
  }>
}
```

#### 3.7.2 Provider Contact

| Field | Value |
|-------|-------|
| **Path** | `/api/providers/contact` |
| **Method** | POST |
| **Source** | `src/app/api/providers/contact/route.ts` |

### 3.8 Support Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/api/support/contact` | POST | Submit support inquiry |
| `/api/support/kb` | GET | Retrieve knowledge base articles |

### 3.9 Peer Mediator Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/api/peer-mediators/admin` | GET | Administrative peer mediator management |
| `/api/peer-mediators/curriculum` | GET | Peer mediator curriculum content |

---

## 4. Data Model Specifications

### 4.1 Current Data Layer: Mock Store

The development data layer uses `FileUserStore` (defined in `src/lib/mockStore.ts`), which persists user records to `data/mock-users.json`.

**MockUser Record Structure:**

```typescript
{
  id: number                   // Auto-incrementing integer
  username: string             // Unique
  password: string             // bcrypt hash (12 rounds)
  email: string                // Unique
  firstName: string
  lastName: string
  role: string                 // "patient" | "provider" | "admin"
  profilePicture: string | null
  phone: string | null
  preferredContactMethod: string | null
  createdAt: Date              // Serialized as ISO 8601 string
}
```

**FileUserStore Operations:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `getUserByUsername` | `(username: string) => Promise<MockUser \| null>` | Lookup by username |
| `getUserByEmail` | `(email: string) => Promise<MockUser \| null>` | Lookup by email |
| `createUser` | `(data: Omit<MockUser, 'id' \| 'createdAt'>) => Promise<MockUser>` | Create and persist |

### 4.2 Domain Entity Schemas (Drizzle ORM)

The full database schema is defined in `src/shared/schema.ts` using Drizzle ORM's PostgreSQL table builders. The schema is not yet connected to a live database.

#### 4.2.1 Core Entities

| Table | Primary Key | Key Columns | Foreign Keys |
|-------|------------|------------|-------------|
| `users` | `id` (serial) | username (unique), email (unique), role, firstName, lastName | -- |
| `resources` | `id` (serial) | name, category, contactInfo, isVirtual, rating | -- |
| `events` | `id` (serial) | title, startTime, endTime, isVirtual, category | hostId -> users.id |
| `appointments` | `id` (serial) | patientId, providerId, startTime, endTime, type, status | patientId -> users.id, providerId -> users.id |
| `messages` | `id` (serial) | senderId, recipientId, subject, content, isRead | senderId -> users.id, recipientId -> users.id |
| `notifications` | `id` (serial) | userId, title, message, type, isRead | userId -> users.id |
| `educational_content` | `id` (serial) | title, content, category, featured | authorId -> users.id |

#### 4.2.2 Community Entities

| Table | Primary Key | Key Columns | Foreign Keys |
|-------|------------|------------|-------------|
| `community_groups` | `id` (serial) | name, description, memberCount, isPublic | -- |
| `discussions` | `id` (serial) | title, content, replyCount, likes | authorId -> users.id, groupId -> community_groups.id |
| `forum_categories` | `id` (serial) | name, slug (unique), postCount, displayOrder | -- |
| `forum_posts` | `id` (serial) | title, content, commentCount, likes, isPinned | authorId -> users.id, categoryId -> forum_categories.id |
| `forum_comments` | `id` (serial) | content, likes, medicalRelevance (0-10) | authorId -> users.id, postId -> forum_posts.id |

#### 4.2.3 Gamification Entities

| Table | Primary Key | Key Columns | Foreign Keys |
|-------|------------|------------|-------------|
| `health_activities` | `id` (serial) | name, category, pointsValue, frequency | -- |
| `achievements` | `id` (serial) | name, level (1-3), pointsRequired, category | -- |
| `rewards` | `id` (serial) | name, category, pointsCost, inventory | -- |
| `user_points` | `id` (serial) | totalPoints, availablePoints, currentStreak | userId -> users.id |
| `user_activities` | `id` (serial) | completedAt, pointsEarned, verificationStatus | userId -> users.id, activityId -> health_activities.id |
| `user_achievements` | `id` (serial) | unlockedAt | userId -> users.id, achievementId -> achievements.id |
| `user_rewards` | `id` (serial) | status, code, expiresAt | userId -> users.id, rewardId -> rewards.id |
| `points_transactions` | `id` (serial) | amount, type, description, sourceType | userId -> users.id |

#### 4.2.4 Compliance and Governance Entities

| Table | Primary Key | Key Columns | Foreign Keys |
|-------|------------|------------|-------------|
| `audit_logs` | `id` (serial) | timestamp, eventType, action, ipAddress, success | userId -> users.id |
| `ai_governance_config` | `id` (serial) | organizationId, aiModel, moderationLevel | -- |
| `ai_risk_assessments` | `id` (serial) | riskScore (0-100), riskCategory, confidence | reviewedBy -> users.id |
| `compliance_monitoring` | `id` (serial) | framework, complianceStatus, severity, riskLevel | assignedTo -> users.id |
| `ai_decision_logs` | `id` (serial) | decisionType, confidence, decision, reasoning | overriddenBy -> users.id |
| `regulatory_templates` | `id` (serial) | name, framework, retentionPeriod | createdBy -> users.id |
| `neural_metrics` | `id` (serial) | modelName, metricType, value, status | -- |
| `automation_rules` | `id` (serial) | triggerType, actionType, priority, successRate | createdBy -> users.id |
| `wellness_tips` | `id` (serial) | content, category, aiGenerated, wasHelpful | userId -> users.id |

#### 4.2.5 Twin Types (TypeScript)

Defined in `src/types/twins.ts`:

```typescript
type TwinPillar = 'clinical' | 'behavioral' | 'social' | 'financial' | 'personal'
type TwinTrend = 'up' | 'stable' | 'down'
type TwinStatus = 'ok' | 'warning' | 'critical'

interface TwinMetric {
  name: string
  value: number
  unit?: string
  status: TwinStatus
}

interface TwinInsight {
  title: string
  summary: string
  recommendation: string
  severity: 'low' | 'medium' | 'high'
}

interface TwinSnapshot {
  pillar: TwinPillar
  score: number        // 0-100
  trend: TwinTrend
  metrics: TwinMetric[]
  insights: TwinInsight[]
  lastUpdated: string  // ISO 8601
}

interface TwinSummary {
  snapshots: TwinSnapshot[]
}
```

### 4.3 Database Migration Path

The system currently operates on file-based mock storage. The Drizzle ORM schema in `src/shared/schema.ts` defines the production database structure. Migration to a live PostgreSQL database requires:

1. Configuring `DATABASE_URL` environment variable
2. Running `npm run db:generate` to generate migration SQL
3. Running `npm run db:migrate` to apply migrations
4. Switching API routes from `mockStore` to Drizzle ORM queries

---

## 5. Authentication Specification

### 5.1 NextAuth.js Configuration

| Parameter | Value | Source |
|-----------|-------|--------|
| Secret | `process.env.SESSION_SECRET` | `.env.local` |
| Session strategy | `jwt` | `src/lib/auth/options.ts:73` |
| Session maxAge | 1800 seconds (30 minutes) | `src/lib/auth/options.ts:73` |
| Sign-in page | `/login` | `src/lib/auth/options.ts:74` |

### 5.2 Credential Provider Contract

**Input:**

```typescript
{
  username: string   // Label: "Username"
  password: string   // Label: "Password", type: "password"
}
```

**Authorization Flow:**

1. Validate `credentials.username` and `credentials.password` are non-empty
2. Retrieve user via `mockStore.getUserByUsername(credentials.username)`
3. If user not found, return `null` (401)
4. Compare password with `bcrypt.compare(credentials.password, user.password)`
5. If comparison fails, return `null` (401)
6. Return user object (without password) for JWT encoding

### 5.3 JWT Token Structure

**Encoding (jwt callback):**

```typescript
{
  sub: string           // user.id (stringified)
  role: string          // user.role, default: "patient"
  username: string      // user.username
  firstName: string     // user.firstName
  lastName: string      // user.lastName
  email?: string        // Set for OAuth users
  iat: number           // Issued-at timestamp
  exp: number           // Expiration timestamp (iat + 1800)
}
```

**Session Projection (session callback):**

```typescript
{
  user: {
    id: string          // from token.sub
    role: string        // from token.role
    username: string    // from token.username
    firstName: string   // from token.firstName
    lastName: string    // from token.lastName
    email?: string      // from token.email (if present)
  }
}
```

### 5.4 OAuth Provider Contracts

**Google OAuth (conditional):**
- Enabled when `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are both set
- Standard Google OAuth 2.0 flow
- User name parsed from `user.name` (split on space: first word = firstName, rest = lastName)
- Role defaults to `'patient'`

**Apple OAuth (planned, currently disabled):**
- Requires: `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY`
- Blocked by async client secret generation requirement

### 5.5 Password Policy

| Rule | Specification |
|------|--------------|
| Minimum length | 12 characters |
| Uppercase | At least 1 uppercase letter (A-Z) |
| Lowercase | At least 1 lowercase letter (a-z) |
| Digit | At least 1 digit (0-9) |
| Special character | At least 1 from: `@$!%*?&#^_-.+=\/~` |
| Allowed characters | `A-Za-z\d@$!%*?&#^_\-.,()+=\/~[\]{}|\`` |
| Hash algorithm | bcrypt |
| Cost factor | 12 |

---

## 6. Security Specifications

### 6.1 Encryption at Rest

| Layer | Algorithm | Key Size | Implementation |
|-------|-----------|----------|----------------|
| PHI field encryption | XChaCha20-Poly1305 | 256-bit | `src/lib/crypto/pqc-hybrid-encryption.ts` |
| Key wrapping | ML-KEM (Kyber) | Level 3 (768) | `src/lib/crypto/pqc-kyber.ts` |
| Key derivation | HKDF-SHA512 | 256-bit output | `@stablelib/hkdf` |
| Password storage | bcrypt | 12 rounds | `bcryptjs` |
| Metadata integrity | SHA-512 | 512-bit digest | `@stablelib/sha512` |

### 6.2 Encryption in Transit

| Protocol | Version | Configuration |
|----------|---------|---------------|
| TLS | 1.3 (minimum) | Enforced by GCP Cloud Run |
| HSTS | -- | `max-age=63072000; includeSubDomains; preload` |

### 6.3 Post-Quantum Cryptography

**ML-KEM (Kyber) Parameters:**

| Security Level | Public Key Size | Secret Key Size | Ciphertext Size | Shared Secret Size |
|---------------|----------------|----------------|-----------------|-------------------|
| Level 1 (Kyber512) | 800 bytes | 1,632 bytes | 768 bytes | 32 bytes |
| Level 3 (Kyber768) | 1,184 bytes | 2,400 bytes | 1,088 bytes | 32 bytes |
| Level 5 (Kyber1024) | 1,568 bytes | 3,168 bytes | 1,568 bytes | 32 bytes |

**Default:** Level 3 (Kyber768) -- 192-bit classical security equivalent.

**Hybrid Encryption Flow:**

```
Encrypt:
  1. Generate random DEK (32 bytes)
  2. Encrypt plaintext with XChaCha20-Poly1305(DEK, nonce=24 bytes)
  3. Encapsulate DEK recipient's Kyber public key -> (kyber_ciphertext, shared_secret)
  4. Derive wrapping key from shared_secret via HKDF-SHA512(info="IHEP-DEK-Wrapping-v1")
  5. Wrap DEK with XChaCha20-Poly1305(wrapping_key, nonce=24 bytes)
  6. Compute metadata hash (SHA-512)
  7. Return {ciphertext, kyber_ciphertext, nonce, algorithm, keyId, timestamp, metadataHash}

Decrypt:
  1. Verify metadata integrity (constant-time SHA-512 comparison)
  2. Decapsulate shared_secret from kyber_ciphertext using recipient's Kyber secret key
  3. Derive wrapping key from shared_secret via HKDF-SHA512(info="IHEP-DEK-Wrapping-v1")
  4. Decrypt ciphertext with XChaCha20-Poly1305(wrapping_key, nonce)
  5. Return plaintext
```

### 6.4 Content Security Policy

**Production CSP:**

```
default-src 'self';
base-uri 'self';
frame-ancestors 'none';
object-src 'none';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data: blob:;
font-src 'self' data:;
connect-src 'self';
form-action 'self';
upgrade-insecure-requests
```

**Development CSP:** Adds `'unsafe-inline' 'unsafe-eval'` to `script-src` and `ws: wss:` to `connect-src` for hot reload.

### 6.5 Security Headers

| Header | Value |
|--------|-------|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `X-Frame-Options` | `DENY` |
| `Content-Security-Policy` | See Section 6.4 |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Embedder-Policy` | `require-corp` |
| `X-Powered-By` | Removed (Next.js `poweredByHeader: false`) |

### 6.6 Rate Limiting

Rate limiting is planned but not yet implemented. The specification calls for:

- Technology: Upstash Redis with `@upstash/ratelimit`
- Algorithm: Sliding window
- Default limit: 10 requests per 10 seconds per authenticated user
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 7. Data Persistence Specification

### 7.1 Current: File-Based Mock Store

| Property | Value |
|----------|-------|
| Storage file | `data/mock-users.json` |
| Format | JSON array of `PersistedUser` objects |
| Write strategy | Full file overwrite via `fs.writeFile` |
| Bootstrap | Auto-seeds demo user on first access if file missing |
| ID generation | Auto-incrementing integer (max existing + 1) |
| Date serialization | ISO 8601 strings |
| Thread safety | Single-process only (no file locking) |

### 7.2 Database Connection Scaffolding

Defined in `src/lib/db.ts`:

| Property | Value |
|----------|-------|
| ORM | Drizzle ORM with `drizzle-orm/postgres-js` driver |
| Driver | `postgres` (porsager/postgres) |
| Pool size | `DB_POOL_SIZE` env var, default 10 |
| Idle timeout | 20 seconds |
| Connect timeout | 10 seconds |
| SSL | Required in production, disabled in development |
| Prepared statements | Enabled |
| Null fallback | Returns `null` for `db` when `DATABASE_URL` is not set |

**Availability Check:**

```typescript
isDatabaseAvailable(): boolean          // Returns true if db is not null
checkDatabaseConnection(): Promise<{    // Executes SELECT 1 ping
  healthy: boolean
  latency?: number
  error?: string
}>
```

### 7.3 Production Path

When `DATABASE_URL` is configured, the system transitions from mock store to Drizzle ORM. The API routes need to be updated to use `db` instead of `mockStore`. The database schema is pre-defined in `src/shared/schema.ts` with 25+ tables.

---

## 8. External Interface Specifications

### 8.1 FHIR R4 Integration Points

FHIR integration is planned but not yet implemented. The target specification is:

- Standard: HL7 FHIR R4 (4.0.1)
- Resources: Patient, Observation, Appointment, MedicationRequest, Condition
- Transport: HTTPS with Bearer token authentication
- Format: JSON (application/fhir+json)

### 8.2 EHR Adapter Interfaces

EHR adapters are planned as spoke services. The interface contract specifies:

- Adapter pattern: Each EHR system (Epic, Cerner, etc.) will have a dedicated spoke adapter
- Communication: Internal HTTP between hub and spoke services
- Data format: Normalized FHIR resources

### 8.3 Three.js / USDZ Rendering Pipeline

| Component | File | Purpose |
|-----------|------|---------|
| DigitalTwinCanvas | `src/components/digital-twin/DigitalTwinCanvas.tsx` | WebGL humanoid rendering |
| DigitalTwinViewer | `src/components/digital-twin/DigitalTwinViewer.tsx` | Viewer container |
| HealthDataStream | `src/components/digital-twin/HealthDataStream.tsx` | Real-time data feed |
| IHEPDigitalTwinRenderer | `src/components/digital-twin/IHEPDigitalTwinRenderer.ts` | Extended renderer |

**DigitalTwinCanvas Props:**

```typescript
{
  healthScore: number      // 0-100, controls humanoid color
  heartRate: number        // BPM, controls pulsation frequency
  viralLoad?: number       // copies/mL, controls opacity
  cd4Count?: number        // cells/uL, reserved for future use
}
```

**WebGL Configuration:**

| Property | Value |
|----------|-------|
| Renderer | WebGLRenderer (antialias, alpha) |
| Camera | PerspectiveCamera (FOV 75, near 0.1, far 1000) |
| Geometry | SphereGeometry (head), CapsuleGeometry (body, arms, legs) |
| Material | MeshStandardMaterial (emissive, transparent) |
| Lighting | AmbientLight (0.5) + PointLight (1.0) + back PointLight (0.5) |
| Animation | 60fps requestAnimationFrame loop |

**USDZ File Support:**

- File types handled by Webpack: `.usdz`, `.usda`, `.usdc` (as asset/resource)
- GLSL shader types: `.glsl`, `.vs`, `.fs`, `.vert`, `.frag` (as asset/source)
- SharedArrayBuffer required (COOP/COEP headers configured)

### 8.4 WebSocket Specification

WebSocket integration for real-time health data streaming is planned. The specification targets:

- Protocol: WSS (WebSocket Secure)
- Use case: Real-time vital sign streaming to DigitalTwinCanvas
- Fallback: HTTP polling at 5-second intervals

### 8.5 Image Remote Patterns

The Next.js image optimization supports these remote hosts:

| Protocol | Hostname |
|----------|----------|
| HTTPS | `images.unsplash.com` |
| HTTPS | `via.placeholder.com` |

---

## 9. Error Handling Specification

### 9.1 HTTP Status Code Usage

| Code | Usage |
|------|-------|
| 200 | Successful GET request |
| 201 | Successful resource creation (POST) |
| 400 | Validation failure, duplicate resource, malformed request |
| 401 | Missing or invalid authentication |
| 403 | Insufficient permissions (e.g., admin role creation) |
| 404 | Resource not found |
| 429 | Rate limit exceeded (planned) |
| 500 | Internal server error |
| 503 | Service degraded (health check) |

### 9.2 Error Response Format

**Validation Error (Zod):**

```typescript
{
  message: string           // Semicolon-separated field:message pairs
  errors: Array<{           // Raw Zod issue array
    code: string
    path: string[]
    message: string
  }>
}
```

**Business Logic Error:**

```typescript
{
  message: string           // Human-readable error description
}
```

**Server Error:**

```typescript
{
  message: string           // Generic message (no internal details exposed)
}
```

### 9.3 Client-Side Error Handling

| Pattern | Location | Behavior |
|---------|----------|----------|
| Session loading | Dashboard layout | Displays spinner while `status === 'loading'` |
| Unauthenticated redirect | Dashboard layout | `router.push('/login')` when `status === 'unauthenticated'` |
| Null session guard | Dashboard layout | Returns `null` (renders nothing) if session is falsy |

### 9.4 Error Logging Policy

- Server errors SHALL be logged with error type only (no user input data)
- PHI SHALL NOT appear in any log output
- Error tracking integration (Sentry) is planned but not yet configured

---

**End of Document**
