import { LegalDocument } from '@/components/LegalDocument'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service | IHEP',
  description: 'Terms and Conditions of Membership for the Integrated Health Empowerment Program',
  robots: { index: true, follow: true },
}

export default function TermsOfServicePage() {
  return (
    <LegalDocument title="Terms and Conditions of Membership">
      <p className="text-gray-600 mb-6">
        <strong>Effective Date:</strong> January 7, 2026<br />
        <strong>Last Updated:</strong> January 7, 2026
      </p>

      <h2>1. Agreement to Terms</h2>
      <p>
        By creating an account with the Integrated Health Empowerment Program ("IHEP," "we," "us," or "our"),
        you ("Member," "you," or "your") agree to be bound by these Terms and Conditions of Membership ("Terms").
        If you do not agree to these Terms, you may not access or use the IHEP platform.
      </p>
      <p>
        IHEP is a comprehensive healthcare aftercare resource management application designed to empower patients
        through digital health tools, including our 4-Twin Digital Twin Ecosystem, Financial Empowerment Module,
        wellness tracking, telehealth services, and educational resources.
      </p>

      <h2>2. Eligibility</h2>
      <h3>2.1 Age Requirement</h3>
      <p>
        You must be at least 18 years of age to create a Member account. If you are under 18, a parent or legal
        guardian must create and manage the account on your behalf and agrees to be bound by these Terms.
      </p>

      <h3>2.2 Authorized Use</h3>
      <p>You represent and warrant that:</p>
      <ul>
        <li>All information you provide during registration is accurate, current, and complete</li>
        <li>You will maintain the accuracy of such information</li>
        <li>You have the legal capacity to enter into this binding agreement</li>
        <li>You are not prohibited from using the platform under applicable law</li>
      </ul>

      <h2>3. Account Registration and Security</h2>
      <h3>3.1 Account Creation</h3>
      <p>To access IHEP services, you must:</p>
      <ul>
        <li>Provide accurate personal information including name, email address, and date of birth</li>
        <li>Create a secure password meeting our security requirements</li>
        <li>Complete identity verification as required</li>
        <li>Consent to our Privacy Policy and HIPAA Authorization</li>
      </ul>

      <h3>3.2 Account Security</h3>
      <p>You are responsible for:</p>
      <ul>
        <li>Maintaining the confidentiality of your account credentials</li>
        <li>All activities that occur under your account</li>
        <li>Notifying us immediately of any unauthorized access or security breach</li>
        <li>Using strong, unique passwords and enabling two-factor authentication when available</li>
      </ul>

      <h2>4. Services and Features</h2>
      <h3>4.1 Core Services</h3>
      <p>IHEP provides the following core services:</p>

      <h4>Digital Twin Ecosystem:</h4>
      <ul>
        <li><strong>Clinical Twin:</strong> Health metrics, medication adherence tracking, lab results visualization</li>
        <li><strong>Behavioral Twin:</strong> Mental health tracking, substance use monitoring, behavioral patterns</li>
        <li><strong>Social Twin:</strong> Support network mapping, community engagement, resource connections</li>
        <li><strong>Financial Twin:</strong> Financial health assessment, benefits optimization, income opportunities</li>
      </ul>

      <h4>Health Management:</h4>
      <ul>
        <li>Dynamic calendar for appointments, medications, and health activities</li>
        <li>Telehealth services connection</li>
        <li>Medication reminders and adherence tracking</li>
        <li>Wellness metrics and goal setting</li>
      </ul>

      <h3>4.2 AI-Powered Features</h3>
      <p>
        IHEP uses Artificial Intelligence (AI) and Machine Learning (ML) systems, including predictive analytics,
        personalized health coaching, risk stratification, and morphogenetic AI for anomaly detection.
      </p>
      <p>
        <strong>AI Governance:</strong> All AI systems are governed by our comprehensive{' '}
        <a href="/legal/ai-governance" className="text-primary hover:underline">AI Governance Policy</a>,
        which ensures safety, fairness, transparency, and compliance with healthcare regulations.
      </p>
      <p>
        <strong>Human Oversight:</strong> AI recommendations are decision-support tools only. Licensed healthcare
        professionals review and approve all clinical recommendations.
      </p>

      <h2>5. Member Responsibilities</h2>
      <h3>5.1 Appropriate Use</h3>
      <p>You agree to use IHEP only for lawful purposes and in accordance with these Terms. You agree NOT to:</p>
      <ul>
        <li>Use the platform to transmit any unlawful, harassing, defamatory, or harmful material</li>
        <li>Impersonate any person or entity</li>
        <li>Interfere with or disrupt the platform or servers</li>
        <li>Attempt to gain unauthorized access to any portion of the platform</li>
        <li>Use automated systems (bots, scrapers, etc.) without express written permission</li>
        <li>Upload or transmit viruses, malware, or destructive code</li>
      </ul>

      <h3>5.2 Emergency Situations</h3>
      <div className="bg-red-50 border border-red-200 rounded-md p-4 my-4">
        <p className="font-bold text-red-800">
          IHEP IS NOT FOR EMERGENCIES. If you are experiencing a medical emergency, call 911 immediately.
        </p>
        <p className="mt-2 text-sm">
          <strong>Crisis Resources:</strong><br />
          National Suicide Prevention Lifeline: 988<br />
          Crisis Text Line: Text HOME to 741741<br />
          SAMHSA National Helpline: 1-800-662-4357
        </p>
      </div>

      <h2>6. Privacy and Protected Health Information</h2>
      <p>
        IHEP is committed to protecting your health information in compliance with HIPAA and applicable state
        privacy laws. Our detailed privacy practices are described in our{' '}
        <a href="/legal/privacy" className="text-primary hover:underline">Privacy Policy</a>.
      </p>

      <h2>7. Disclaimers and Limitations of Liability</h2>
      <h3>7.1 Medical Disclaimer</h3>
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 my-4">
        <p className="font-bold">
          IHEP IS NOT A SUBSTITUTE FOR PROFESSIONAL MEDICAL ADVICE, DIAGNOSIS, OR TREATMENT.
        </p>
        <p className="mt-2 text-sm">
          Always seek the advice of qualified health providers with questions about medical conditions.
          Never disregard professional medical advice or delay seeking it because of information obtained through IHEP.
        </p>
      </div>

      <h3>7.2 No Warranty</h3>
      <p>
        THE PLATFORM IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED.
      </p>

      <h2>8. Contact Information</h2>
      <p>For questions about these Terms or to report violations, contact us:</p>
      <div className="bg-gray-100 rounded-md p-4 my-4">
        <p>
          <strong>IHEP Legal Department</strong><br />
          Email: <a href="mailto:legal@ihep.app" className="text-primary hover:underline">legal@ihep.app</a><br />
          Security Issues: <a href="mailto:security@ihep.app" className="text-primary hover:underline">security@ihep.app</a><br />
          Privacy Concerns: <a href="mailto:privacy@ihep.app" className="text-primary hover:underline">privacy@ihep.app</a>
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
            <a href="/legal/privacy" className="text-primary hover:underline">Privacy Policy</a>
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
