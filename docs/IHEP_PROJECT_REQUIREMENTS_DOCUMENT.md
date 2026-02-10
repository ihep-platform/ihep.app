# IHEP Project Requirements Document

**Document Identifier:** IHEP-PRD-2026-001
**Version:** 1.0
**Date:** 2026-02-10
**Status:** Draft
**Author:** Jason M Jarmacz | Evolution Strategist | jason@ihep.app
**Co-Author:** Claude by Anthropic

**Standard:** IEEE 830-1998 (Software Requirements Specification)
**Classification:** Internal -- Confidential

---

## Revision History

| Version | Date       | Author        | Description            |
|---------|------------|---------------|------------------------|
| 1.0     | 2026-02-10 | J. Jarmacz / Claude | Initial release |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Specific Requirements](#3-specific-requirements)
4. [Requirements Traceability Matrix](#4-requirements-traceability-matrix)
5. [Appendices](#5-appendices)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the software requirements for the Integrated Health Empowerment Program (IHEP), version 2.0.0-alpha. It defines the functional and non-functional requirements for the patient-facing web application (the "hub") and its interactions with backend spoke services. This document is intended for the development team, quality assurance, regulatory reviewers, and project stakeholders. It follows the structure prescribed by IEEE 830-1998.

The key words "SHALL", "SHOULD", "MAY", "MUST", and "MUST NOT" in this document are to be interpreted as described in RFC 2119.

### 1.2 Scope

IHEP is a healthcare aftercare resource management application designed to empower patients managing life-altering conditions, with an initial focus on HIV/AIDS aftercare. The system provides:

- A 5-pillar Digital Twin Ecosystem (clinical, behavioral, social, financial, personal)
- Financial empowerment tools (opportunity matching, benefits optimization, personal finance tracking)
- Calendar-based appointment and event management
- Provider search and telehealth integration
- Community resources, education, and peer support
- Gamification and rewards for health engagement
- Post-quantum cryptographic protection of PHI

The system SHALL NOT be used as a diagnostic tool or replace clinical decision-making. It SHALL serve as a supplemental aftercare coordination platform.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|-----------|
| IHEP | Integrated Health Empowerment Program |
| PHI | Protected Health Information (as defined by HIPAA) |
| PQC | Post-Quantum Cryptography |
| KEM | Key Encapsulation Mechanism |
| EKF | Extended Kalman Filter |
| CBF | Control Barrier Function |
| FHIR | Fast Healthcare Interoperability Resources (HL7 standard) |
| RBAC | Role-Based Access Control |
| Twin | A digital representation of a patient's health dimension |
| Hub | The patient-facing Next.js frontend application (`ihep-application/`) |
| Spoke | A backend microservice providing domain-specific functionality |
| DEK | Data Encryption Key |
| HKDF | HMAC-based Key Derivation Function |
| CSP | Content Security Policy |
| HSTS | HTTP Strict Transport Security |
| JWT | JSON Web Token |
| SLA | Service Level Agreement |
| WCAG | Web Content Accessibility Guidelines |

### 1.4 References

| ID | Title | Version |
|----|-------|---------|
| REF-01 | IEEE 830-1998, Recommended Practice for Software Requirements Specifications | 1998 |
| REF-02 | RFC 2119, Key words for use in RFCs to Indicate Requirement Levels | 1997 |
| REF-03 | HIPAA Security Rule, 45 CFR Part 164 | 2013 |
| REF-04 | NIST FIPS 203, Module-Lattice-Based Key-Encapsulation Mechanism Standard | 2024 |
| REF-05 | WCAG 2.1, Web Content Accessibility Guidelines | 2018 |
| REF-06 | HL7 FHIR R4, Fast Healthcare Interoperability Resources | 4.0.1 |
| REF-07 | IHEP Technical Specifications Document (IHEP-TS-2026-001) | 1.0 |
| REF-08 | IHEP Technical Design Document (IHEP-TDD-2026-001) | 1.0 |

### 1.5 Overview

Section 2 provides a general description of the product, its users, and constraints. Section 3 specifies functional and non-functional requirements with unique identifiers for traceability. Section 4 provides a requirements traceability matrix mapping requirements to implementation artifacts. Section 5 contains the glossary and supporting appendices.

---

## 2. Overall Description

### 2.1 Product Perspective

IHEP is a standalone web application that operates within a hub-and-spoke architecture:

- **Hub** (`ihep-application/`): A Next.js 16.1.5 frontend application providing the patient-facing user interface, API route handlers, and client-side rendering. This is the primary deliverable described in this document.
- **Spokes** (`spokes/`): Sixteen backend microservices providing domain-specific computation (authentication, clinical data, financial modeling, digital twin synthesis, etc.). These are referenced but not fully specified here.
- **Core** (`core/`): Shared libraries for security, cryptography, storage, and utility functions consumed by both hub and spokes.

The system currently operates in development mode with file-based mock data storage (`data/mock-users.json`). Production deployment targets Google Cloud Platform (Cloud Run, Cloud SQL, BigQuery).

```
+------------------+       +------------------+
|   Patient        |       |   Provider       |
|   Browser        |       |   Browser        |
+--------+---------+       +--------+---------+
         |                          |
         v                          v
+--------+--------------------------+---------+
|          IHEP Hub (Next.js 16.1.5)          |
|  - 41 page routes                           |
|  - 22 API endpoints                         |
|  - NextAuth.js authentication               |
|  - React 19 + TypeScript 5 (strict)         |
+--------+------------------------------------+
         |
         v
+--------+------------------------------------+
|          Backend Spokes (16 services)       |
|  api-gateway | auth | clinical | financial  |
|  digital-twin | wellness | providers | ...  |
+---------+-----------------------------------+
          |
          v
+---------+-----------------------------------+
|         Data Layer                          |
|  Mock Store (dev) | Cloud SQL (production)  |
|  BigQuery (analytics) | Cloud Storage       |
+---------------------------------------------+
```

### 2.2 Product Functions

The major functions of the IHEP application are:

1. **Authentication and Authorization** -- Secure user registration, login, session management, and role-based access control.
2. **Patient Dashboard** -- Centralized overview of health metrics, appointments, wellness data, and action items.
3. **5-Pillar Digital Twin Ecosystem** -- Clinical, behavioral, social, financial, and personal digital twin views with composite scoring, trend analysis, and actionable insights.
4. **3D Digital Twin Visualization** -- WebGL-based humanoid rendering reflecting real-time health metrics.
5. **Calendar and Appointments** -- Scheduling, viewing, and managing healthcare appointments and events.
6. **Wellness Tracking** -- Monitoring and displaying wellness metrics over time.
7. **Financial Empowerment** -- Opportunity matching, benefits optimization, personal finance tracking, and focus group management.
8. **Resource Hub** -- Searchable directory of healthcare resources, clinics, pharmacies, and support groups.
9. **Provider Management** -- Provider search, listing, and contact capabilities.
10. **Health Monitoring** -- Real-time vital sign monitoring with alert generation.
11. **Community and Peer Support** -- Forums, events, education, and community group management.
12. **Support System** -- Contact forms and searchable knowledge base.
13. **Gamification** -- Points, achievements, rewards, and streaks for health engagement.
14. **Legal and Compliance** -- Privacy policy, terms of service, AI governance, and trust framework.
15. **Administration** -- Peer mediator management and investor dashboard.
16. **Procedural Registry** -- Procedure tracking and predictability engine.

### 2.3 User Characteristics

| User Class | Description | Technical Proficiency | Access Level |
|-----------|-------------|----------------------|-------------|
| Patient | Primary user. Individuals managing aftercare for life-altering conditions. | Low to moderate. Mobile-first. | Own data only. |
| Provider | Healthcare professionals (physicians, therapists, social workers). | Moderate. Desktop and mobile. | Assigned patient data. |
| Admin | System administrators and institutional staff. | High. Desktop-primary. | All data. User management. |
| Peer Mediator | Trained peer support specialists. | Moderate. Mobile and desktop. | Assigned peer groups. |
| Researcher | Academic and clinical researchers. | High. Desktop-primary. | De-identified aggregate data. |

### 2.4 Constraints

1. **Regulatory**: The system MUST comply with HIPAA Security Rule (45 CFR Part 164) for all PHI handling.
2. **Technology**: The frontend MUST use Next.js App Router with React Server Components and TypeScript in strict mode.
3. **Security**: All PHI MUST be encrypted in transit (TLS 1.3) and at rest (AES-256 or post-quantum equivalent).
4. **Data Residency**: All PHI MUST be stored within the United States.
5. **Accessibility**: The system MUST conform to WCAG 2.1 Level AA.
6. **Session Duration**: Authenticated sessions MUST expire after 30 minutes of inactivity.
7. **Budget**: Development operates under pre-revenue constraints; initial deployment targets GCP free/low-cost tiers.
8. **Standards**: All mathematical models MUST be verifiable with trusted published formulas.

### 2.5 Assumptions and Dependencies

**Assumptions:**
1. Users have access to a modern web browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+).
2. Users have a stable internet connection (minimum 1 Mbps downstream).
3. Initial deployment will use mock data; production database migration is a separate project phase.
4. The Google Cloud Platform project will be provisioned before production deployment.

**Dependencies:**
1. NextAuth.js v4 for authentication (dependency: `next-auth@^4.24.13`).
2. Three.js v0.182 for 3D rendering (dependency: `three@^0.182.0`).
3. @noble/post-quantum v0.5.4 for PQC operations (dependency: `@noble/post-quantum@^0.5.4`).
4. Drizzle ORM v0.45 for database operations (dependency: `drizzle-orm@^0.45.1`).
5. Zod v4 for input validation (dependency: `zod@^4.2.1`).
6. Backend spoke services for production data (currently mocked).

---

## 3. Specific Requirements

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces

**UI-001**: The system SHALL provide a responsive web interface optimized for viewport widths from 320px (mobile) to 2560px (4K desktop).

**UI-002**: The system SHALL use the Inter font family loaded via `next/font/google` with `display: swap` for performance.

**UI-003**: The system SHALL implement a purple-to-pink gradient color scheme (`from-purple-600 to-pink-600`) as the primary brand identity.

**UI-004**: The system SHALL provide glassmorphism visual effects (backdrop blur, semi-transparent backgrounds) for card and navigation components.

**UI-005**: The system SHALL display a persistent top navigation bar on desktop and a fixed bottom navigation bar on mobile viewports within the dashboard.

**UI-006**: The dashboard navigation SHALL include links to: Dashboard, Wellness, Calendar, Opportunities, Financials, Resources, Providers, and Digital Twin.

**UI-007**: The system SHALL display the authenticated user's full name (firstName + lastName) or username in the top navigation bar.

#### 3.1.2 Hardware Interfaces

**HW-001**: The system SHALL operate on any device with a WebGL 2.0-capable GPU for digital twin 3D rendering.

**HW-002**: The system SHOULD degrade gracefully on devices without WebGL support by displaying a 2D fallback representation.

#### 3.1.3 Software Interfaces

**SW-001**: The system SHALL expose a RESTful API via Next.js API routes at the `/api/*` path prefix.

**SW-002**: The system SHALL integrate with NextAuth.js v4 for authentication, exposing the NextAuth endpoint at `/api/auth/[...nextauth]`.

**SW-003**: The system SHALL provide a health check endpoint at `GET /api/health` returning JSON with status, timestamp, uptime, environment, and version fields.

**SW-004**: The system SHALL integrate with the Drizzle ORM for database operations when a `DATABASE_URL` environment variable is configured.

**SW-005**: The system SHALL fall back to file-based mock storage (`FileUserStore` class in `src/lib/mockStore.ts`) when no database is configured in development.

#### 3.1.4 Communication Interfaces

**CI-001**: All client-server communication SHALL use HTTPS (TLS 1.3 minimum in production).

**CI-002**: The system SHALL enforce HSTS with `max-age=63072000; includeSubDomains; preload`.

**CI-003**: The system SHALL set `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp` headers for SharedArrayBuffer support (required by USDZ WASM loader).

**CI-004**: Static assets under `/_next/static/` and `/assets/` SHALL be served with `Cache-Control: public, max-age=31536000, immutable`.

### 3.2 Functional Requirements

#### 3.2.1 FR-AUTH: Authentication and Authorization

**FR-AUTH-001**: The system SHALL provide a user registration endpoint at `POST /api/auth/register` that accepts username, password, email, firstName, lastName, role, and optional profile fields.

**FR-AUTH-002**: The system SHALL validate registration passwords against the following policy: minimum 12 characters, at least one uppercase letter, one lowercase letter, one digit, and one special character from the set `@$!%*?&#^_-.+=\/~`.

**FR-AUTH-003**: The system SHALL hash passwords using bcrypt with a cost factor of 12 (OWASP 2024 recommendation) before storage.

**FR-AUTH-004**: The system SHALL reject registration attempts with duplicate usernames (HTTP 400) or duplicate email addresses (HTTP 400).

**FR-AUTH-005**: The system SHALL reject registration attempts with `role: 'admin'` with HTTP 403 and the message "Administrator accounts require institutional approval."

**FR-AUTH-006**: The system SHALL provide a login page at `/auth/login` (and `/login` as an alias) accepting username and password credentials.

**FR-AUTH-007**: The system SHALL authenticate users via NextAuth.js CredentialsProvider by comparing the provided password against the bcrypt-hashed password in the data store.

**FR-AUTH-008**: The system SHALL issue JWT session tokens with a maximum age of 30 minutes (1800 seconds).

**FR-AUTH-009**: The JWT token SHALL contain the following claims: `sub` (user ID), `role`, `username`, `firstName`, `lastName`, and optionally `email`.

**FR-AUTH-010**: The system SHALL redirect unauthenticated users attempting to access `/dashboard/*` routes to the `/login` page.

**FR-AUTH-011**: The system SHALL support Google OAuth sign-in when `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` environment variables are configured.

**FR-AUTH-012**: The system SHOULD support Apple OAuth sign-in in a future release (currently disabled pending async client secret generation).

**FR-AUTH-013**: The system SHALL provide a registration page at `/auth/signup` (and `/register` as an alias).

**FR-AUTH-014**: The system SHALL strip the password field from all user data returned in API responses.

#### 3.2.2 FR-DASH: Dashboard

**FR-DASH-001**: The system SHALL provide a main dashboard page at `/dashboard` displaying an overview of the patient's health status.

**FR-DASH-002**: The dashboard layout SHALL include a sidebar/top navigation with links to all dashboard sub-sections.

**FR-DASH-003**: The system SHALL display a loading spinner while the session is being validated on dashboard pages.

**FR-DASH-004**: The system SHALL render a user menu dropdown showing the user's name with options to navigate to Dashboard, My Wellness, or Sign Out.

#### 3.2.3 FR-TWIN: Digital Twin Ecosystem

**FR-TWIN-001**: The system SHALL implement five digital twin pillars: `clinical`, `behavioral`, `social`, `financial`, and `personal`.

**FR-TWIN-002**: Each twin pillar SHALL expose a REST endpoint returning a `TwinSnapshot` object containing: `pillar` (enum), `score` (0-100), `trend` (up/stable/down), `metrics` (array), `insights` (array), and `lastUpdated` (ISO 8601 timestamp).

**FR-TWIN-003**: The system SHALL provide the following twin API endpoints:
- `GET /api/twins/clinical`
- `GET /api/twins/behavioral`
- `GET /api/twins/social`
- `GET /api/twins/financial`
- `GET /api/twins/personal`
- `GET /api/twins/summary` (returns all five snapshots)

**FR-TWIN-004**: Each twin metric SHALL include: `name` (string), `value` (number), `unit` (string, optional), and `status` (ok/warning/critical).

**FR-TWIN-005**: Each twin insight SHALL include: `title`, `summary`, `recommendation`, and `severity` (low/medium/high).

**FR-TWIN-006**: The system SHALL provide dashboard pages for each twin pillar:
- `/dashboard/digital-twin` (overview)
- `/dashboard/digital-twin/clinical`
- `/dashboard/digital-twin/behavioral`
- `/dashboard/digital-twin/social`
- `/dashboard/digital-twin/financial`
- `/dashboard/digital-twin/personal`

**FR-TWIN-007**: The system SHALL provide a standalone 3D digital twin viewer at `/digital-twin-viewer`.

**FR-TWIN-008**: The 3D digital twin viewer SHALL render a humanoid form using Three.js WebGL that:
- Rotates slowly on the Y axis
- Pulsates based on the patient's heart rate
- Changes color based on health score (green >= 80, orange >= 50, red < 50)
- Adjusts opacity based on viral load when available

**FR-TWIN-009**: The system SHALL provide a financial twin standalone page at `/financial-twin`.

#### 3.2.4 FR-CAL: Calendar and Appointments

**FR-CAL-001**: The system SHALL provide a calendar view at `/dashboard/calendar`.

**FR-CAL-002**: The system SHALL provide a `GET /api/calendar/events` endpoint returning an array of calendar events, each containing: `id`, `title`, `provider`, `specialty`, `datetime`, `durationMinutes`, `location`, and `type` (In-Person or Telehealth).

**FR-CAL-003**: The system SHALL provide a `POST /api/calendar/events` endpoint to create new calendar events, returning the created event with HTTP 201.

**FR-CAL-004**: Calendar events SHALL support both In-Person and Telehealth types.

#### 3.2.5 FR-WELL: Wellness Tracking

**FR-WELL-001**: The system SHALL provide a wellness tracking page at `/dashboard/wellness`.

**FR-WELL-002**: The wellness module SHALL display health metrics including trends over time.

#### 3.2.6 FR-FIN: Financial Empowerment

**FR-FIN-001**: The system SHALL provide financial dashboards at `/dashboard/financials` and `/financials`.

**FR-FIN-002**: The system SHALL provide an opportunities page at `/dashboard/opportunities` and `/opportunities`.

**FR-FIN-003**: The system SHALL provide a `GET /api/financial/opportunities` endpoint returning an array of opportunities, each containing: `id`, `title`, `category`, `payout`, `matchScore` (0-100), and `status` (new/in-progress/applied).

**FR-FIN-004**: The system SHALL provide a `GET /api/financial/benefits` endpoint for benefits optimization data.

**FR-FIN-005**: The system SHALL provide a `GET /api/financial/personal-finance` endpoint for personal finance tracking data.

**FR-FIN-006**: The system SHALL provide a `GET /api/financial/focus-groups` endpoint for focus group management data.

#### 3.2.7 FR-RES: Resources Hub

**FR-RES-001**: The system SHALL provide a resources page at `/dashboard/resources` and `/resources`.

**FR-RES-002**: The system SHALL provide a `GET /api/resources/search` endpoint returning an array of resource results, each containing: `id`, `name`, `category`, `distanceMiles`, `address`, and `rating`.

**FR-RES-003**: Resources SHALL include categories such as Clinic, Peer Support, Diagnostics, and Pharmacy.

#### 3.2.8 FR-PROV: Provider Management

**FR-PROV-001**: The system SHALL provide a provider listing page at `/dashboard/providers`.

**FR-PROV-002**: The system SHALL provide a `GET /api/providers/list` endpoint returning an array of provider records, each containing: `id`, `userId`, `firstName`, `lastName`, `title`, `specialty`, `licenseNumber`, `email`, `phone`, `bio`, `yearsOfExperience`, `languages`, `acceptingNewPatients`, `rating`, `reviewCount`, and `location` (facility name, address, city, state, zip).

**FR-PROV-003**: The system SHALL provide a `POST /api/providers/contact` endpoint for initiating contact with a provider.

#### 3.2.9 FR-HLTH: Health Monitoring

**FR-HLTH-001**: The system SHALL provide a health monitoring page at `/dashboard/health-monitor`.

**FR-HLTH-002**: The system SHALL provide a `GET /api/health/monitor` endpoint returning: `overall` (0-100 composite score), `trend` (up/stable/down), `vitals` (array of name/value/status), and `alerts` (array of strings).

**FR-HLTH-003**: Vital metrics SHALL include at minimum: heart rate, blood pressure, SpO2, temperature, and HRV.

**FR-HLTH-004**: The system SHALL generate alerts when vital metrics deviate from baseline.

#### 3.2.10 FR-TELE: Telehealth

**FR-TELE-001**: The system SHOULD provide telehealth video call integration in a future release.

**FR-TELE-002**: Calendar events with `type: 'Telehealth'` SHALL be rendered with distinct visual indicators.

#### 3.2.11 FR-COMM: Community

**FR-COMM-001**: The system SHALL provide a community page at `/community`.

**FR-COMM-002**: The system SHALL provide a forum at `/forum` with category-based discussions.

**FR-COMM-003**: The system SHALL provide an events page at `/events` for community events.

**FR-COMM-004**: The system SHALL provide an education page at `/education` for educational content.

**FR-COMM-005**: The system SHALL provide a rewards page at `/rewards` for gamification features.

#### 3.2.12 FR-SUPP: Support

**FR-SUPP-001**: The system SHALL provide a support page at `/support`.

**FR-SUPP-002**: The system SHALL provide a `POST /api/support/contact` endpoint for submitting support inquiries.

**FR-SUPP-003**: The system SHALL provide a `GET /api/support/kb` endpoint for retrieving knowledge base articles.

**FR-SUPP-004**: The system SHALL provide a dynamic knowledge base article page at `/support/kb/[slug]`.

#### 3.2.13 FR-ADMIN: Administration

**FR-ADMIN-001**: The system SHALL provide an admin peer mediators page at `/admin/peer-mediators`.

**FR-ADMIN-002**: The system SHALL provide a `GET /api/peer-mediators/admin` endpoint for administrative management of peer mediators.

**FR-ADMIN-003**: The system SHALL provide a `GET /api/peer-mediators/curriculum` endpoint for peer mediator curriculum management.

**FR-ADMIN-004**: The system SHALL provide a research portal peer mediators page at `/research-portal/peer-mediators`.

**FR-ADMIN-005**: The system SHALL provide an investor dashboard at `/investor-dashboard`.

#### 3.2.14 FR-LEGAL: Legal and Compliance

**FR-LEGAL-001**: The system SHALL provide the following legal pages:
- `/legal/privacy` -- Privacy policy
- `/legal/terms` -- Terms of service
- `/legal/compliance` -- Compliance information
- `/legal/ai-governance` -- AI governance policy
- `/legal/trust` -- Trust framework

**FR-LEGAL-002**: Legal pages SHALL be publicly accessible without authentication.

#### 3.2.15 FR-PROC: Procedural Registry

**FR-PROC-001**: The system SHALL provide a procedural registry page at `/procedural-registry`.

**FR-PROC-002**: The procedural registry SHALL track medical procedures with predictability scoring.

#### 3.2.16 FR-GAME: Gamification

**FR-GAME-001**: The system SHALL implement a points-based gamification system where users earn points for completing health activities.

**FR-GAME-002**: The system SHALL track: total points, available points, lifetime points, current streak, and longest streak per user.

**FR-GAME-003**: The system SHALL support achievements at three difficulty levels (easy, medium, hard) across categories: physical, mental, medication, appointment, education, and streak.

**FR-GAME-004**: The system SHALL support redeemable rewards in categories: discount, gift card, merchandise, badge, and feature unlock.

**FR-GAME-005**: The system SHALL maintain a full points transaction ledger with types: earned, spent, expired, bonus, and adjustment.

### 3.3 Non-Functional Requirements

#### 3.3.1 NFR-SEC: Security

**NFR-SEC-001**: The system SHALL encrypt all data in transit using TLS 1.3 or higher.

**NFR-SEC-002**: The system SHALL encrypt all PHI at rest using AES-256 or post-quantum equivalent (XChaCha20-Poly1305).

**NFR-SEC-003**: The system SHALL implement post-quantum cryptography using ML-KEM (Kyber) at NIST Security Level 3 (768-bit) as the default, with Level 1 (512-bit) and Level 5 (1024-bit) as configurable options.

**NFR-SEC-004**: The PQC key encapsulation SHALL use HKDF-SHA512 for key derivation with the context string `IHEP-Hybrid-KEM-v1`.

**NFR-SEC-005**: The system SHALL implement field-level encryption for PHI using the `HybridEncryption.encryptPHI()` method.

**NFR-SEC-006**: The system SHALL enforce the following Content Security Policy in production:
`default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; form-action 'self'; upgrade-insecure-requests`

**NFR-SEC-007**: The system SHALL set `X-Frame-Options: DENY` to prevent clickjacking.

**NFR-SEC-008**: The system SHALL set `X-Content-Type-Options: nosniff` to prevent MIME type sniffing.

**NFR-SEC-009**: The system SHALL set `Referrer-Policy: strict-origin-when-cross-origin`.

**NFR-SEC-010**: The system SHALL NOT expose the `X-Powered-By` header (`poweredByHeader: false` in Next.js config).

**NFR-SEC-011**: The system SHALL validate all user input at API boundaries using Zod schemas.

**NFR-SEC-012**: The system SHALL use parameterized queries exclusively; no string concatenation of user input into database queries.

**NFR-SEC-013**: The system SHALL implement constant-time comparison for cryptographic operations to prevent timing attacks.

**NFR-SEC-014**: The system SHALL NOT store PHI in localStorage, sessionStorage, URL parameters, or query strings.

**NFR-SEC-015**: The system SHALL NOT log PHI in application logs or error tracking.

#### 3.3.2 NFR-PERF: Performance

**NFR-PERF-001**: The system SHALL achieve a Largest Contentful Paint (LCP) of less than 2.5 seconds on a 4G connection.

**NFR-PERF-002**: The system SHALL achieve a First Input Delay (FID) of less than 100 milliseconds.

**NFR-PERF-003**: The system SHALL achieve a Cumulative Layout Shift (CLS) of less than 0.1.

**NFR-PERF-004**: The system SHALL serve static assets with one-year immutable cache headers.

**NFR-PERF-005**: The system SHALL use `next/font` for font loading with `display: swap` to prevent FOIT.

**NFR-PERF-006**: The system SHALL exclude Three.js from server-side bundling (SSR) since WebGL is not available in Node.js.

**NFR-PERF-007**: The system SHALL use React Compiler (`reactCompiler: true`) for automatic performance optimizations.

#### 3.3.3 NFR-SCALE: Scalability

**NFR-SCALE-001**: The system SHALL support a minimum of 100 concurrent authenticated users in its initial deployment.

**NFR-SCALE-002**: The system SHALL use standalone output mode (`output: 'standalone'`) for containerized deployment.

**NFR-SCALE-003**: The database connection pool SHALL be configurable via the `DB_POOL_SIZE` environment variable (default: 10).

#### 3.3.4 NFR-AVAIL: Availability

**NFR-AVAIL-001**: The system SHALL target 99.5% uptime (approximately 3.65 hours downtime per month).

**NFR-AVAIL-002**: The system SHALL provide a health check endpoint (`GET /api/health`) for liveness and readiness probes.

**NFR-AVAIL-003**: The health check SHALL report: status (healthy/degraded), timestamp, uptime, environment, and version.

#### 3.3.5 NFR-ACCESS: Accessibility

**NFR-ACCESS-001**: The system SHALL conform to WCAG 2.1 Level AA.

**NFR-ACCESS-002**: All interactive elements SHALL be keyboard navigable (Tab, Enter, Space, Arrow keys).

**NFR-ACCESS-003**: All icon buttons SHALL have ARIA labels.

**NFR-ACCESS-004**: Text content SHALL maintain a color contrast ratio of at least 4.5:1 against its background.

**NFR-ACCESS-005**: UI components SHALL maintain a contrast ratio of at least 3:1 against adjacent colors.

**NFR-ACCESS-006**: The system SHALL set `lang="en"` on the `<html>` element.

#### 3.3.6 NFR-COMPAT: Compatibility

**NFR-COMPAT-001**: The system SHALL support the following browsers: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+.

**NFR-COMPAT-002**: The system SHALL provide responsive layouts for mobile (320px+), tablet (768px+), and desktop (1024px+) viewports.

**NFR-COMPAT-003**: The system SHALL degrade gracefully when JavaScript is disabled, displaying appropriate fallback content.

#### 3.3.7 NFR-AUDIT: Audit Trail

**NFR-AUDIT-001**: The system SHALL maintain an audit log of all PHI access events.

**NFR-AUDIT-002**: Each audit log entry SHALL contain: timestamp, userId, eventType, resourceType, resourceId, action, description, ipAddress, success flag, and optional additionalInfo (JSONB).

**NFR-AUDIT-003**: The system SHALL support the following audit event types: PHI_ACCESS, PHI_MODIFICATION, PHI_DELETION, AUTHENTICATION, AUTHORIZATION, SYSTEM_EVENT.

**NFR-AUDIT-004**: Audit logs SHALL be retained for a minimum of 7 years (2555 days) per HIPAA requirements.

#### 3.3.8 NFR-DATA: Data Integrity and Retention

**NFR-DATA-001**: The system SHALL validate all data at API boundaries before processing or storage.

**NFR-DATA-002**: The system SHALL use typed ORM schemas (Drizzle with Zod) to enforce data integrity at the application layer.

**NFR-DATA-003**: User passwords SHALL be stored as bcrypt hashes with a cost factor of 12; plaintext passwords SHALL NOT be persisted.

**NFR-DATA-004**: The system SHALL persist mock store data to `data/mock-users.json` with atomic write operations.

---

## 4. Requirements Traceability Matrix

### 4.1 Functional Requirements to Implementation

| Requirement ID | Component/Page | API Endpoint | Source File |
|---------------|---------------|-------------|-------------|
| FR-AUTH-001 | Registration page | POST /api/auth/register | `src/app/api/auth/register/route.ts` |
| FR-AUTH-006 | Login page | POST /api/auth/[...nextauth] | `src/app/auth/login/page.tsx` |
| FR-AUTH-007 | -- | POST /api/auth/[...nextauth] | `src/lib/auth/options.ts` |
| FR-AUTH-010 | Dashboard layout | -- | `src/app/dashboard/layout.tsx` |
| FR-DASH-001 | Dashboard overview | -- | `src/app/dashboard/page.tsx` |
| FR-TWIN-002 | -- | GET /api/twins/{pillar} | `src/app/api/twins/mock-data.ts` |
| FR-TWIN-003 | -- | GET /api/twins/summary | `src/app/api/twins/summary/route.ts` |
| FR-TWIN-006 | Twin pages | -- | `src/app/dashboard/digital-twin/*/page.tsx` |
| FR-TWIN-008 | 3D viewer | -- | `src/components/digital-twin/DigitalTwinCanvas.tsx` |
| FR-CAL-002 | Calendar | GET /api/calendar/events | `src/app/api/calendar/events/route.ts` |
| FR-CAL-003 | Calendar | POST /api/calendar/events | `src/app/api/calendar/events/route.ts` |
| FR-FIN-003 | Opportunities | GET /api/financial/opportunities | `src/app/api/financial/opportunities/route.ts` |
| FR-FIN-004 | Financials | GET /api/financial/benefits | `src/app/api/financial/benefits/route.ts` |
| FR-FIN-005 | Financials | GET /api/financial/personal-finance | `src/app/api/financial/personal-finance/route.ts` |
| FR-RES-002 | Resources | GET /api/resources/search | `src/app/api/resources/search/route.ts` |
| FR-PROV-002 | Providers | GET /api/providers/list | `src/app/api/providers/list/route.ts` |
| FR-HLTH-002 | Health monitor | GET /api/health/monitor | `src/app/api/health/monitor/route.ts` |
| FR-SUPP-002 | Support | POST /api/support/contact | `src/app/api/support/contact/route.ts` |
| FR-SUPP-003 | Support KB | GET /api/support/kb | `src/app/api/support/kb/route.ts` |
| FR-ADMIN-002 | Admin | GET /api/peer-mediators/admin | `src/app/api/peer-mediators/admin/route.ts` |

### 4.2 Non-Functional Requirements to Implementation

| Requirement ID | Implementation Artifact | Source File |
|---------------|------------------------|-------------|
| NFR-SEC-003 | KyberKEM class | `src/lib/crypto/pqc-kyber.ts` |
| NFR-SEC-005 | HybridEncryption.encryptPHI() | `src/lib/crypto/pqc-hybrid-encryption.ts` |
| NFR-SEC-006 | CSP header configuration | `next.config.mjs:73-74` |
| NFR-SEC-011 | Zod schema validation | `src/app/api/auth/register/route.ts:6-21` |
| NFR-PERF-005 | Inter font configuration | `src/app/layout.tsx:6-9` |
| NFR-PERF-007 | React Compiler | `next.config.mjs:12` |
| NFR-AUDIT-002 | auditLogs table schema | `src/shared/schema.ts:425-437` |
| NFR-DATA-002 | Drizzle + Zod schemas | `src/shared/schema.ts` |
| NFR-DATA-004 | FileUserStore.persist() | `src/lib/mockStore.ts:69-75` |

---

## 5. Appendices

### 5.1 Glossary

| Term | Definition |
|------|-----------|
| Aftercare | Ongoing medical care and support following initial treatment for a life-altering condition. |
| Digital Twin | A computational model representing a specific dimension of a patient's health, updated with real-time and historical data. |
| Hub | The central patient-facing web application that aggregates data and services from backend spokes. |
| Spoke | A backend microservice providing domain-specific data processing and business logic. |
| Morphogenetic Agent | An autonomous software agent that monitors and adjusts system behavior based on biological pattern-formation principles. |
| Peer Mediator | A trained individual who provides peer support and facilitation for patients in aftercare programs. |
| Mock Store | A file-based data persistence layer (`data/mock-users.json`) used in development when no production database is configured. |

### 5.2 Acronyms

See Section 1.3 for the complete acronym list.

### 5.3 Page Route Inventory

The following 41 page routes exist in the `ihep-application/src/app/` directory:

| # | Route | Authentication Required |
|---|-------|------------------------|
| 1 | `/` | No |
| 2 | `/about` | No |
| 3 | `/auth/login` | No |
| 4 | `/auth/signup` | No |
| 5 | `/login` | No |
| 6 | `/register` | No |
| 7 | `/community` | No |
| 8 | `/education` | No |
| 9 | `/events` | No |
| 10 | `/forum` | No |
| 11 | `/resources` | No |
| 12 | `/rewards` | No |
| 13 | `/support` | No |
| 14 | `/support/kb/[slug]` | No |
| 15 | `/legal/privacy` | No |
| 16 | `/legal/terms` | No |
| 17 | `/legal/compliance` | No |
| 18 | `/legal/ai-governance` | No |
| 19 | `/legal/trust` | No |
| 20 | `/investor-dashboard` | No |
| 21 | `/procedural-registry` | No |
| 22 | `/digital-twin-viewer` | No |
| 23 | `/financial-twin` | No |
| 24 | `/financials` | No |
| 25 | `/opportunities` | No |
| 26 | `/dashboard` | Yes |
| 27 | `/dashboard/wellness` | Yes |
| 28 | `/dashboard/calendar` | Yes |
| 29 | `/dashboard/opportunities` | Yes |
| 30 | `/dashboard/financials` | Yes |
| 31 | `/dashboard/resources` | Yes |
| 32 | `/dashboard/providers` | Yes |
| 33 | `/dashboard/health-monitor` | Yes |
| 34 | `/dashboard/digital-twin` | Yes |
| 35 | `/dashboard/digital-twin/clinical` | Yes |
| 36 | `/dashboard/digital-twin/behavioral` | Yes |
| 37 | `/dashboard/digital-twin/social` | Yes |
| 38 | `/dashboard/digital-twin/financial` | Yes |
| 39 | `/dashboard/digital-twin/personal` | Yes |
| 40 | `/admin/peer-mediators` | Yes |
| 41 | `/research-portal/peer-mediators` | Yes |

### 5.4 API Endpoint Inventory

The following 22 API route handlers exist in `ihep-application/src/app/api/`:

| # | Method | Path | Auth |
|---|--------|------|------|
| 1 | GET/POST | `/api/auth/[...nextauth]` | No (handles auth) |
| 2 | POST | `/api/auth/register` | No |
| 3 | GET | `/api/health` | No |
| 4 | GET | `/api/health/monitor` | No |
| 5 | GET | `/api/twins/clinical` | No |
| 6 | GET | `/api/twins/behavioral` | No |
| 7 | GET | `/api/twins/social` | No |
| 8 | GET | `/api/twins/financial` | No |
| 9 | GET | `/api/twins/personal` | No |
| 10 | GET | `/api/twins/summary` | No |
| 11 | GET/POST | `/api/calendar/events` | No |
| 12 | GET | `/api/financial/opportunities` | No |
| 13 | GET | `/api/financial/benefits` | No |
| 14 | GET | `/api/financial/personal-finance` | No |
| 15 | GET | `/api/financial/focus-groups` | No |
| 16 | GET | `/api/resources/search` | No |
| 17 | GET | `/api/providers/list` | No |
| 18 | POST | `/api/providers/contact` | No |
| 19 | POST | `/api/support/contact` | No |
| 20 | GET | `/api/support/kb` | No |
| 21 | GET | `/api/peer-mediators/admin` | No |
| 22 | GET | `/api/peer-mediators/curriculum` | No |

**Note:** API endpoints currently lack authentication guards. This is a known gap; production deployment SHALL require session validation on all endpoints except `/api/auth/*` and `/api/health`.

---

**End of Document**
