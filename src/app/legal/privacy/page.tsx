import { LegalDocument } from '@/components/LegalDocument'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy | IHEP',
  description: 'Privacy Policy for the Integrated Health Empowerment Program - HIPAA compliant health data protection',
  robots: { index: true, follow: true },
}

export default function PrivacyPolicyPage() {
  return (
    <LegalDocument title="Privacy Policy">
      <p className="text-gray-600 mb-6">
        <strong>Effective Date:</strong> January 7, 2026<br />
        <strong>Last Updated:</strong> January 7, 2026
      </p>

      <div className="bg-blue-50 border border-blue-200 rounded-md p-4 my-6">
        <h3 className="font-bold text-blue-900 mb-2">Our Commitment to Your Privacy</h3>
        <p className="text-sm">
          The Integrated Health Empowerment Program (IHEP) is committed to protecting your privacy and securing
          your Protected Health Information (PHI). This Privacy Policy explains how we collect, use, disclose,
          store, and protect your personal information and health data in compliance with HIPAA, HITECH, and
          applicable state privacy laws.
        </p>
      </div>

      <h2>1. Information We Collect</h2>

      <h3>1.1 Personal Identifying Information (PII)</h3>
      <p><strong>Account Information:</strong></p>
      <ul>
        <li>Full name, email address, phone number</li>
        <li>Date of birth, mailing address</li>
        <li>Username and password (encrypted)</li>
        <li>Profile photo (optional)</li>
        <li>Emergency contact information</li>
      </ul>

      <h3>1.2 Protected Health Information (PHI)</h3>
      <p>Health-related information protected under HIPAA:</p>

      <p><strong>Clinical Twin Data:</strong></p>
      <ul>
        <li>Medical diagnoses and conditions</li>
        <li>Medications and prescriptions</li>
        <li>Laboratory and test results</li>
        <li>Vital signs (blood pressure, heart rate, weight, BMI)</li>
        <li>Immunization records and allergies</li>
        <li>Treatment plans and clinical notes</li>
      </ul>

      <p><strong>Behavioral Twin Data:</strong></p>
      <ul>
        <li>Mental health assessments and diagnoses</li>
        <li>Substance use history and treatment</li>
        <li>Self-reported mood and mental health tracking</li>
        <li>Crisis intervention records</li>
      </ul>

      <p><strong>Social Twin Data:</strong></p>
      <ul>
        <li>Social determinants of health (housing, food security, transportation)</li>
        <li>Support network information</li>
        <li>Community resource utilization</li>
      </ul>

      <p><strong>Financial Twin Data:</strong></p>
      <ul>
        <li>Financial health assessments</li>
        <li>Income information and employment status</li>
        <li>Benefits enrollment status</li>
        <li>Banking information (encrypted and tokenized)</li>
      </ul>

      <h3>1.3 Usage and Technical Data</h3>
      <ul>
        <li>IP address (masked for privacy)</li>
        <li>Device type, operating system, browser</li>
        <li>Pages visited and features used</li>
        <li>Login frequency and patterns</li>
      </ul>

      <h3>1.4 Cookies and Tracking Technologies</h3>
      <p>We use cookies for:</p>
      <ul>
        <li><strong>Essential Cookies:</strong> Required for platform functionality (cannot be disabled)</li>
        <li><strong>Analytics Cookies:</strong> Understanding usage patterns (can be disabled)</li>
        <li><strong>Preference Cookies:</strong> Remembering your settings (can be disabled)</li>
      </ul>

      <h2>2. How We Use Your Information</h2>

      <h3>2.1 To Provide and Improve Services</h3>
      <ul>
        <li>Create and manage your account</li>
        <li>Provide the Digital Twin Ecosystem and visualizations</li>
        <li>Track health metrics and wellness goals</li>
        <li>Schedule appointments and send reminders</li>
        <li>Enable secure messaging with healthcare providers</li>
        <li>Connect you with community resources and benefits programs</li>
      </ul>

      <h3>2.2 AI and Machine Learning</h3>
      <p>AI systems use your data to:</p>
      <ul>
        <li>Predict health risks and recommend preventive interventions</li>
        <li>Personalize health coaching and education</li>
        <li>Detect medication adherence patterns</li>
        <li>Generate digital twin visualizations</li>
      </ul>
      <p className="mt-2">
        <strong>AI Governance:</strong> All AI use is governed by our{' '}
        <a href="/legal/ai-governance" className="text-primary hover:underline">AI Governance Policy</a>,
        ensuring transparency, fairness, and human oversight.
      </p>

      <h2>3. How We Share Your Information</h2>

      <h3>3.1 With Your Consent</h3>
      <p>We share information only with your explicit authorization:</p>
      <ul>
        <li>Healthcare providers authorized to view your records</li>
        <li>Care team members and caregivers you designate</li>
        <li>Third-party health apps you choose to connect</li>
      </ul>

      <h3>3.2 HIPAA-Permitted Healthcare Operations</h3>
      <p>We may share PHI without consent for:</p>
      <ul>
        <li><strong>Treatment:</strong> Coordinating care with your healthcare team</li>
        <li><strong>Payment:</strong> Processing insurance claims and billing</li>
        <li><strong>Healthcare Operations:</strong> Quality improvement and care coordination</li>
        <li><strong>Business Associates:</strong> Service providers with Business Associate Agreements</li>
      </ul>

      <h3>3.3 Legal Requirements</h3>
      <p>We may disclose information when required by law:</p>
      <ul>
        <li>Court orders and legal process</li>
        <li>Public health reporting (communicable diseases, adverse events)</li>
        <li>Regulatory agency audits and investigations</li>
        <li>To prevent serious threats to health or safety</li>
      </ul>

      <h3>3.4 De-identified and Aggregated Data</h3>
      <p>
        We may share de-identified, aggregated data for research and public health purposes. De-identified
        data cannot be linked back to you and is not subject to HIPAA restrictions.
      </p>

      <h2>4. Data Security and Protection</h2>

      <h3>4.1 Technical Safeguards</h3>
      <p><strong>Encryption:</strong></p>
      <ul>
        <li><strong>In Transit:</strong> TLS 1.3 encryption for all data transmission</li>
        <li><strong>At Rest:</strong> AES-256 encryption for stored data</li>
        <li><strong>Key Management:</strong> Google Cloud KMS with Hardware Security Modules</li>
      </ul>

      <p><strong>Access Controls:</strong></p>
      <ul>
        <li>Role-based access control (RBAC) with least privilege</li>
        <li>Multi-factor authentication for staff accounts</li>
        <li>Session timeouts (30 minutes of inactivity)</li>
        <li>Audit logs of all PHI access</li>
      </ul>

      <p><strong>Network Security:</strong></p>
      <ul>
        <li>Web Application Firewall (WAF) with Google Cloud Armor</li>
        <li>DDoS protection and intrusion detection</li>
        <li>Regular security scanning and penetration testing</li>
      </ul>

      <h3>4.2 Data Retention and Deletion</h3>
      <p><strong>Retention Periods:</strong></p>
      <ul>
        <li><strong>Active Accounts:</strong> Data retained while account is active</li>
        <li><strong>Inactive Accounts:</strong> Data retained for 7 years after last activity (HIPAA requirement)</li>
        <li><strong>Closed Accounts:</strong> PHI retained for 7 years, then securely deleted</li>
        <li><strong>Audit Logs:</strong> Retained for 7 years for compliance</li>
      </ul>

      <h3>4.3 Your Security Responsibilities</h3>
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 my-4">
        <p className="font-bold">Help us protect your data:</p>
        <ul className="text-sm mt-2">
          <li>Use strong, unique passwords (minimum 12 characters)</li>
          <li>Enable two-factor authentication</li>
          <li>Never share your password with anyone</li>
          <li>Log out after using shared devices</li>
          <li>Report suspicious activity to security@ihep.app</li>
        </ul>
      </div>

      <h2>5. Your Privacy Rights</h2>

      <h3>5.1 HIPAA Rights</h3>
      <ul>
        <li><strong>Right to Access:</strong> Request a copy of your PHI (within 30 days, free)</li>
        <li><strong>Right to Amend:</strong> Request corrections to inaccurate PHI</li>
        <li><strong>Right to Accounting:</strong> List of certain disclosures in past 6 years</li>
        <li><strong>Right to Restrict:</strong> Request limits on uses and disclosures</li>
        <li><strong>Right to Complain:</strong> File complaints without retaliation</li>
      </ul>

      <h3>5.2 State Privacy Rights (CCPA/CPRA)</h3>
      <p>California residents and residents of other states with privacy laws may have additional rights:</p>
      <ul>
        <li>Right to know what personal information is collected and used</li>
        <li>Right to delete personal information</li>
        <li>Right to opt-out of sale (we do not sell data)</li>
        <li>Right to non-discrimination</li>
      </ul>

      <h3>5.3 Data Portability</h3>
      <p>
        Request an export of your data in machine-readable format (JSON, CSV, or FHIR). We will provide
        within 30 days at no charge.
      </p>

      <h3>5.4 Account Deletion</h3>
      <p>
        You can delete your account at any time. Upon deletion, your account is immediately deactivated and
        PHI is retained for 7 years to comply with legal requirements, then securely deleted.
      </p>
      <p className="font-bold mt-2">Account deletion is permanent and cannot be undone.</p>

      <h2>6. Children's Privacy</h2>
      <p>
        IHEP is not intended for children under 18 without parental consent. We do not knowingly collect
        information from children except with verifiable parental consent.
      </p>

      <h2>7. International Data Transfers</h2>
      <p>
        IHEP is based in the United States. Your data is stored on servers in the U.S., which may have
        different data protection laws. By using IHEP, you consent to the transfer of your information to
        the U.S. with appropriate safeguards.
      </p>

      <h2>8. Changes to This Privacy Policy</h2>
      <p>
        We may update this Privacy Policy to reflect changes in practices, technology, or legal requirements.
        Material changes will be communicated via email (at least 30 days before effective date), prominent
        notice on the platform, and in-app notification.
      </p>

      <h2>9. Contact Us</h2>
      <div className="bg-gray-100 rounded-md p-4 my-4">
        <p>
          <strong>IHEP Privacy Office</strong><br />
          Email: <a href="mailto:privacy@ihep.app" className="text-primary hover:underline">privacy@ihep.app</a><br />
          Security Issues: <a href="mailto:security@ihep.app" className="text-primary hover:underline">security@ihep.app</a><br />
          Data Rights: <a href="mailto:datarights@ihep.app" className="text-primary hover:underline">datarights@ihep.app</a>
        </p>
        <p className="mt-2 text-sm">
          <strong>Response Time:</strong> We will respond to privacy requests within 30 days.
        </p>
      </div>

      <h2>10. Regulatory Oversight</h2>
      <p>
        <strong>HIPAA Complaints:</strong> If you believe your privacy rights have been violated, file a complaint with:
      </p>
      <div className="bg-gray-100 rounded-md p-4 my-4">
        <p className="text-sm">
          U.S. Department of Health and Human Services<br />
          Office for Civil Rights (OCR)<br />
          200 Independence Avenue, S.W.<br />
          Washington, D.C. 20201<br />
          Phone: 1-877-696-6775<br />
          Online: <a href="https://www.hhs.gov/ocr/complaints" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">https://www.hhs.gov/ocr/complaints</a>
        </p>
      </div>

      <div className="mt-8 pt-8 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          <strong>Version:</strong> 1.0<br />
          <strong>Effective Date:</strong> January 7, 2026<br />
          <strong>Last Reviewed:</strong> January 7, 2026
        </p>
        <p className="text-sm text-gray-600 mt-4">
          <strong>Authors:</strong><br />
          Jason M Jarmacz &lt;jason@ihep.app&gt;<br />
          Claude by Anthropic &lt;noreply@anthropic.com&gt;
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
            <a href="/legal/ai-governance" className="text-primary hover:underline">AI Governance Policy</a>
          </li>
          <li>
            <a href="/legal/trust" className="text-primary hover:underline">Trust Statement</a>
          </li>
        </ul>
      </div>
    </LegalDocument>
  )
}
