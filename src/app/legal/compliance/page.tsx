import Link from 'next/link'

const policyPath = '/docs/legal/compliance.md'

export default function CompliancePage() {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Legal & Compliance</p>
      <h1 className="text-3xl font-semibold">Compliance Overview</h1>
      <p className="text-sm text-muted-foreground">
        HIPAA-aligned safeguards, auditing, encryption, and consent expectations for the IHEP platform.
      </p>
      <ul className="list-disc pl-5 space-y-1 text-sm text-muted-foreground">
        <li>Access control: role-based, least privilege, 30-minute session timeouts.</li>
        <li>Audit logging: capture PHI access and admin actions with user, IP/UA, and timestamps.</li>
        <li>Encryption: TLS 1.3 in transit; AES-256 at rest with KMS-managed keys.</li>
        <li>Input validation: Zod validation at API edges; reject unsafe payloads.</li>
        <li>No PHI in client storage; avoid embedding PHI in URLs.</li>
        <li>Secrets in Secret Manager only; no secrets in source control.</li>
        <li>Vendor calls require due diligence/BAA before sending PHI.</li>
      </ul>
      <p className="text-sm text-muted-foreground">
        Full policy text: <Link href={policyPath} className="text-primary underline">compliance.md</Link>
      </p>
    </div>
  )
}

