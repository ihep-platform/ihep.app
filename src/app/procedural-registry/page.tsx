'use client';

const summaryItems = [
  'Registry is the sole authority for data lifecycle decisions; deletion is denied or deferred unless multi-approver criteria are met.',
  'Retention defaults: HIPAA 6-year minimum; retain by default; synergy value and correlations block deletion.',
  'Multi-approver sign-off required (security lead, compliance officer, data scientist) even when other checks pass.',
  'Storage-based deletion only considered when usage exceeds critical thresholds.',
  'Legal holds override everything; predictive value and active correlations prevent deletion.',
];

export default function ProceduralRegistryPage() {
  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 px-6 py-16">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="space-y-2">
          <p className="text-xs tracking-[0.2em] uppercase text-gray-500">IHEP Procedural Registry</p>
          <h1 className="text-3xl font-semibold">Policy Overview</h1>
          <p className="text-sm text-gray-700">
            This registry governs fragment retention and deletion. It enforces legal/compliance holds, HIPAA
            retention, synergy and correlation protection, predictive value safeguards, and multi-approver
            sign-off for any destructive action.
          </p>
          <p className="text-sm text-gray-600">
            Full policy and procedures are documented in <code>procedural-registry/PROCEDURAL_REGISTRY.md</code>.
          </p>
        </header>

        <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 space-y-4">
          <h2 className="text-xl font-semibold">Core Rules</h2>
          <ul className="space-y-2 text-sm text-gray-700 list-disc list-inside">
            {summaryItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 space-y-3">
          <h2 className="text-xl font-semibold">Decision Pipeline</h2>
          <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
            <li>Legal/Compliance Hold Check</li>
            <li>Retention Policy Check (HIPAA 6-year minimum, defaults)</li>
            <li>Synergy Value Check (retain if synergy above threshold)</li>
            <li>Active Correlations Check (retain if any correlations exist)</li>
            <li>Predictive Value Check (retain if future value indicated)</li>
            <li>Storage Criticality Check (only proceed if storage is critical)</li>
            <li>Multi-Approver Sign-off Required</li>
          </ol>
        </section>
      </div>
    </main>
  );
}
