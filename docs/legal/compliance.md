# Compliance & Legal Overview

This document summarizes compliance expectations for the IHEP platform. It is referenced directly by the `/legal/compliance` route.

## Scope
- HIPAA-aligned safeguards for PHI.
- Consent, auditing, and access control across digital twins, messaging, and financial modules.
- Data residency and retention expectations for production deployments.

## Controls (Summary)
- **Access control:** Role-based access, least privilege, session timeouts (30m).
- **Audit logging:** Log PHI access, mutations, and admin actions with user, timestamp, IP/UA.
- **Encryption:** TLS 1.3 in transit; AES-256 at rest (KMS-managed keys).
- **Input validation:** Zod validation at API edges; reject malformed or unsafe payloads.
- **No PHI in client storage:** Never persist PHI to localStorage/sessionStorage; avoid URLs.
- **Secrets management:** Use Secret Manager; no secrets in code or VCS.
- **Third-party calls:** Vendor due diligence; no PHI to vendors without BAA.

## Incident Readiness
- Security contact: security@ihep.app
- Triage within 24h; notify affected users when applicable.

## Data Subject Rights
- Provide access/export/delete where required by applicable jurisdiction and policy.

## Logging and Monitoring
- Ship audit and security logs to centralized SIEM; alert on auth anomalies and PHI access spikes.

## Next Steps
- Map environment-specific configurations to this policy.
- Attach SOPs for incident response and change management.

