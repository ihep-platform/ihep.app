import { LegalDocument } from '@/components/LegalDocument'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AI Governance Policy | IHEP',
  description: 'AI Governance Policy for IHEP - Ensuring safe, ethical, and transparent AI systems in healthcare',
  robots: { index: true, follow: true },
}

export default function AIGovernancePolicyPage() {
  return (
    <LegalDocument title="IHEP AI Governance Policy">
      <p className="text-gray-600 mb-6">
        <strong>Version:</strong> 1.0<br />
        <strong>Effective Date:</strong> December 4, 2025<br />
        <strong>Approving Authority:</strong> IHEP Executive Governance Board<br />
        <strong>Compliance Frameworks:</strong> NIST AI RMF 1.0, HIPAA Security Rule, FDA SaMD, WHO Ethics Guidelines
      </p>

      <div className="bg-blue-50 border border-blue-200 rounded-md p-4 my-6">
        <h3 className="font-bold text-blue-900 mb-2">Purpose and Scope</h3>
        <p className="text-sm">
          This policy establishes the governance framework for the design, development, deployment, and monitoring
          of Artificial Intelligence (AI) and Machine Learning (ML) systems within IHEP. It ensures that all AI
          assets—specifically the Digital Twin engine, Morphogenetic AI, and Predictive Analytics modules—are
          safe, effective, ethical, and compliant with applicable regulations.
        </p>
      </div>

      <h2>1. Governance Structure</h2>

      <h3>1.1 Executive Governance Board</h3>
      <p><strong>Role:</strong> Ultimate accountability for AI strategy and risk acceptance.</p>
      <p><strong>Responsibilities:</strong></p>
      <ul>
        <li>Approve high-risk AI system deployments</li>
        <li>Allocate budget for compliance and safety infrastructure</li>
        <li>Review quarterly AI safety and performance reports</li>
      </ul>

      <h3>1.2 AI Ethics & Safety Committee (AIESC)</h3>
      <p><strong>Role:</strong> Independent oversight of ethical implications and patient safety.</p>
      <p><strong>Composition:</strong></p>
      <ul>
        <li>Chief Medical Officer</li>
        <li>Chief Information Security Officer (CISO)</li>
        <li>Lead AI Ethicist</li>
        <li>Patient Advocacy Representative</li>
        <li>Legal Counsel</li>
      </ul>
      <p><strong>Responsibilities:</strong></p>
      <ul>
        <li>Conduct Ethical Impact Assessments (EIA) for all new models</li>
        <li>Review fairness and bias testing results</li>
        <li>Adjudicate "Go/No-Go" decisions for model deployment based on safety criteria</li>
      </ul>

      <h3>1.3 Technical Review Board (TRB)</h3>
      <p><strong>Role:</strong> Technical validation and architectural integrity.</p>
      <p><strong>Responsibilities:</strong></p>
      <ul>
        <li>Validate model performance metrics (accuracy, AUC, etc.)</li>
        <li>Verify implementation of explainability features (SHAP values)</li>
        <li>Audit data lineage and quality</li>
      </ul>

      <h2>2. AI System Lifecycle Management</h2>

      <h3>Phase I: Clinical Necessity & Conception</h3>
      <p>
        <strong>Requirement:</strong> No AI project shall commence without a documented Clinical Necessity
        Statement approved by the Medical Director.
      </p>
      <p>
        <strong>Criteria:</strong> The AI solution must solve a validated clinical or operational problem
        better than existing non-AI alternatives.
      </p>

      <h3>Phase II: Design & Development</h3>
      <p><strong>Data Governance:</strong></p>
      <ul>
        <li>All training data must be fully de-identified per HIPAA Safe Harbor or Expert Determination</li>
        <li>Complete data lineage tracking from raw source to training set is mandatory</li>
        <li>Federated Learning for multi-site training; Differential Privacy (epsilon ≤ 1.0) for shared gradients</li>
      </ul>
      <p><strong>Algorithm Selection:</strong></p>
      <ul>
        <li>"Black box" models prohibited for clinical decision support unless accompanied by robust explainability</li>
      </ul>

      <h3>Phase III: Validation & Verification (V&V)</h3>
      <p><strong>Performance Testing:</strong></p>
      <ul>
        <li>Models must meet pre-defined accuracy thresholds (e.g., &gt;85% AUC)</li>
      </ul>
      <p><strong>Fairness Testing:</strong></p>
      <ul>
        <li>Mandatory testing for Disparate Impact across protected classes</li>
        <li>Disparate Impact Ratio must be between 0.8 and 1.25</li>
      </ul>
      <p><strong>Adversarial Testing:</strong></p>
      <ul>
        <li>Models must undergo stress testing against adversarial attacks and edge cases</li>
      </ul>

      <h3>Phase IV: Deployment & Monitoring</h3>
      <p><strong>Human-in-the-Loop (HITL):</strong></p>
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 my-4">
        <p className="font-bold">
          AI predictions for clinical interventions are decision support only. A licensed human provider
          must review and approve all clinical recommendations.
        </p>
      </div>

      <p><strong>Continuous Monitoring:</strong></p>
      <ul>
        <li>Automated drift detection for input distribution changes and accuracy degradation</li>
        <li>A 5% drop in performance triggers automatic rollback or alert</li>
      </ul>

      <p><strong>Explainability:</strong></p>
      <ul>
        <li>All clinician-facing AI outputs must present top contributing factors (SHAP values)</li>
      </ul>

      <h3>Phase V: Retirement</h3>
      <p>
        Models that no longer meet performance standards must be securely decommissioned. Data used for
        training retired models is archived or destroyed per IHEP Data Retention Policy.
      </p>

      <h2>3. Risk Management Framework</h2>
      <p>IHEP adopts a risk-based approach aligned with NIST AI RMF:</p>

      <div className="overflow-x-auto my-4">
        <table className="min-w-full border border-gray-300">
          <thead className="bg-gray-100">
            <tr>
              <th className="border border-gray-300 px-4 py-2 text-left">Risk Level</th>
              <th className="border border-gray-300 px-4 py-2 text-left">Definition</th>
              <th className="border border-gray-300 px-4 py-2 text-left">Requirements</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="border border-gray-300 px-4 py-2 font-bold text-red-600">Critical</td>
              <td className="border border-gray-300 px-4 py-2">Clinical diagnosis, treatment recommendation, crisis intervention</td>
              <td className="border border-gray-300 px-4 py-2">Full FDA SaMD compliance, HITL mandatory, external audit, real-time monitoring</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-4 py-2 font-bold text-orange-600">High</td>
              <td className="border border-gray-300 px-4 py-2">Triage support, resource allocation, personalized coaching</td>
              <td className="border border-gray-300 px-4 py-2">Internal AIESC approval, fairness audit, monthly performance review</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-4 py-2 font-bold text-green-600">Low</td>
              <td className="border border-gray-300 px-4 py-2">Administrative tasks, scheduling, operational efficiency</td>
              <td className="border border-gray-300 px-4 py-2">Standard IT validation, automated monitoring</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h2>4. Transparency and Patient Rights</h2>

      <h3>4.1 Notification</h3>
      <p>
        Patients must be explicitly informed when interacting with an AI agent or when AI aids their care decisions.
      </p>

      <h3>4.2 Right to Explanation</h3>
      <p>
        Patients have the right to request an explanation of how an AI decision affected their care plan.
      </p>

      <h3>4.3 Opt-Out</h3>
      <p>
        Where clinically feasible, patients should be offered the option to opt-out of AI-driven features
        in favor of standard manual care processes.
      </p>

      <h2>5. Incident Response</h2>

      <div className="bg-red-50 border border-red-200 rounded-md p-4 my-4">
        <p className="font-bold text-red-800">Adverse Events Protocol:</p>
        <p className="text-sm mt-2">
          Any patient harm or "near miss" attributed to an AI system must be reported immediately as a Level 1 Incident.
        </p>
        <p className="text-sm mt-2"><strong>Response Protocol:</strong></p>
        <ol className="text-sm mt-2 ml-4">
          <li>1. Immediate suspension of the affected AI model</li>
          <li>2. Activation of "Standard of Care" fallback protocols</li>
          <li>3. Root Cause Analysis (RCA) by TRB and AIESC</li>
          <li>4. Report to regulatory bodies (FDA, OCR) if required</li>
        </ol>
      </div>

      <h2>6. Audit and Compliance</h2>
      <ul>
        <li><strong>Internal Audit:</strong> Quarterly review of AI inventory, performance logs, and bias assessments</li>
        <li><strong>External Audit:</strong> Annual third-party algorithmic audit for safety, fairness, and security</li>
      </ul>

      <h2>7. Policy Enforcement</h2>
      <p>
        Failure to adhere to this policy may result in disciplinary action, up to and including termination
        of employment and legal action. Unauthorized deployment of AI models is strictly prohibited.
      </p>

      <div className="mt-8 pt-8 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          <strong>Approved By:</strong> Jason Jarmacz, Principal Investigator & Project Sponsor<br />
          <strong>Date:</strong> December 4, 2025
        </p>
      </div>

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <p className="text-sm">
          <strong>Related Documents:</strong>
        </p>
        <ul className="text-sm mt-2">
          <li>
            <a href="/legal/terms" className="text-primary hover:underline">Terms of Service</a>
          </li>
          <li>
            <a href="/legal/privacy" className="text-primary hover:underline">Privacy Policy</a>
          </li>
          <li>
            <a href="/legal/trust" className="text-primary hover:underline">Trust Statement</a>
          </li>
        </ul>
      </div>
    </LegalDocument>
  )
}
