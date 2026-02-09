import { LegalDocument } from '@/components/LegalDocument'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Trust Statement | IHEP',
  description: 'IHEP Trust Statement - Our commitment to transparency, privacy, and ethical healthcare technology',
  robots: { index: true, follow: true },
}

export default function TrustStatementPage() {
  return (
    <LegalDocument title="IHEP Trust Statement">
      <p className="text-gray-600 mb-6">
        <strong>Published:</strong> January 7, 2026<br />
        <strong>Last Updated:</strong> January 7, 2026
      </p>

      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-md p-6 my-6">
        <h3 className="font-bold text-blue-900 mb-3 text-xl">Our Commitment to You</h3>
        <p className="text-base">
          The Integrated Health Empowerment Program (IHEP) is built on a foundation of trust, transparency,
          and unwavering commitment to your health, privacy, and empowerment. This Trust Statement articulates
          the principles that guide every decision we make and the values that define our relationship with you.
        </p>
      </div>

      <h2>1. Core Trust Principles</h2>

      <h3>1.1 You Own Your Data</h3>
      <div className="bg-teal-50 border border-teal-200 rounded-md p-4 my-4">
        <p className="font-bold text-teal-900">
          Your health data belongs to you, period.
        </p>
        <p className="text-sm mt-2">
          IHEP is the steward of your information, never the owner. You have complete control over what
          data you share, who can access it, how it's used, and when to export or delete it.
        </p>
        <p className="text-sm mt-2 font-bold">
          We will never sell your personal health information to third parties. Your data is not a commodity—it
          is a sacred trust.
        </p>
      </div>

      <h3>1.2 Transparency in All Things</h3>
      <p>We believe you deserve to know:</p>
      <ul>
        <li>Exactly what data we collect and why</li>
        <li>How AI systems make recommendations that affect your care</li>
        <li>Who has access to your information and under what circumstances</li>
        <li>How we make money and sustain our operations</li>
        <li>When things go wrong and what we're doing to fix them</li>
      </ul>
      <p className="font-semibold mt-2">
        Hidden agendas and obscure practices have no place in healthcare. We commit to plain-language
        explanations and open communication.
      </p>

      <h3>1.3 Privacy as a Human Right</h3>
      <p>Your privacy is not negotiable. We implement:</p>
      <ul>
        <li>Military-grade encryption for all data in transit and at rest</li>
        <li>Strict access controls limited to authorized personnel only</li>
        <li>Regular third-party security audits</li>
        <li>Immediate breach notification if incidents occur</li>
        <li>HIPAA-compliant practices that exceed minimum standards</li>
      </ul>
      <p className="font-semibold mt-2">
        Privacy is embedded in our architecture, not added as an afterthought.
      </p>

      <h3>1.4 Human-Centered AI</h3>
      <div className="bg-purple-50 border border-purple-200 rounded-md p-4 my-4">
        <p className="font-bold text-purple-900">
          Artificial Intelligence enhances care—it does not replace human judgment.
        </p>
        <p className="text-sm mt-2">We guarantee:</p>
        <ul className="text-sm mt-2 space-y-1">
          <li>• AI systems provide decision support only; licensed professionals make final clinical decisions</li>
          <li>• You can always request a human review of AI recommendations</li>
          <li>• AI models are tested rigorously for fairness across all populations</li>
          <li>• You receive explanations of how AI systems reach conclusions</li>
          <li>• You can opt-out of AI-driven features when clinically appropriate</li>
        </ul>
        <p className="text-sm mt-2 font-bold">
          Technology serves humanity, not the other way around.
        </p>
      </div>

      <h2>2. Our Promises to You</h2>

      <h3>Promise 1: Clinical Excellence</h3>
      <p>
        <strong>We will:</strong> Partner with licensed, credentialed healthcare professionals who adhere
        to evidence-based practices and ethical standards.
      </p>
      <p>
        <strong>We will not:</strong> Provide medical advice without appropriate clinical oversight or make
        claims not supported by peer-reviewed research.
      </p>
      <p>
        <strong>Accountability:</strong> All healthcare providers are verified, licensed, and subject to
        ongoing quality reviews.
      </p>

      <h3>Promise 2: Security Without Compromise</h3>
      <p>
        <strong>We will:</strong> Implement industry-leading security measures, conduct regular penetration
        testing, and maintain 24/7 threat monitoring.
      </p>
      <p>
        <strong>We will not:</strong> Cut corners on security to save costs or delay security patches
        for convenience.
      </p>
      <p>
        <strong>Accountability:</strong> We publish annual security audit summaries and maintain SOC 2 Type II
        certification.
      </p>

      <h3>Promise 3: Fairness and Equity</h3>
      <p>
        <strong>We will:</strong> Design systems that reduce health disparities, test AI models for bias,
        and ensure equitable access to platform features.
      </p>
      <p>
        <strong>We will not:</strong> Allow algorithms to perpetuate discrimination or create barriers to
        care based on protected characteristics.
      </p>
      <p>
        <strong>Accountability:</strong> We publish annual fairness audits and disparate impact analyses
        for all AI systems.
      </p>

      <h3>Promise 4: Financial Transparency</h3>
      <p>
        <strong>We will:</strong> Clearly communicate pricing, provide advance notice of fee changes, and
        offer financial assistance programs for those in need.
      </p>
      <p>
        <strong>We will not:</strong> Hide fees, surprise you with unexpected charges, or make it difficult
        to cancel your subscription.
      </p>
      <p>
        <strong>Accountability:</strong> All pricing is published on our website with 30-day notice of
        material changes.
      </p>

      <h3>Promise 5: Continuous Improvement</h3>
      <p>
        <strong>We will:</strong> Listen to your feedback, learn from our mistakes, and evolve our platform
        to better serve your needs.
      </p>
      <p>
        <strong>We will not:</strong> Ignore user concerns, dismiss complaints, or become complacent in
        our service delivery.
      </p>
      <p>
        <strong>Accountability:</strong> We publish quarterly product roadmaps informed by user feedback and
        conduct annual user satisfaction surveys.
      </p>

      <h3>Promise 6: Ethical Research</h3>
      <p>
        <strong>We will:</strong> Seek your explicit consent for research use of data, de-identify data to
        protect privacy, and share findings that advance public health.
      </p>
      <p>
        <strong>We will not:</strong> Use your data for research without consent, re-identify de-identified
        data, or publish findings that compromise individual privacy.
      </p>
      <p>
        <strong>Accountability:</strong> All research undergoes IRB review or equivalent ethical oversight.
      </p>

      <h2>3. Governance and Oversight</h2>
      <p>IHEP operates under rigorous governance structures:</p>

      <ul>
        <li><strong>Executive Governance Board:</strong> Strategic oversight and accountability for AI strategy</li>
        <li><strong>AI Ethics & Safety Committee:</strong> Independent oversight of ethical implications and patient safety</li>
        <li><strong>Technical Review Board:</strong> Validates model performance and technical integrity</li>
        <li><strong>Patient Advisory Council:</strong> User community input on features, policies, and experience</li>
      </ul>

      <h2>4. Compliance and Certification</h2>
      <p>We maintain compliance with:</p>
      <ul>
        <li>HIPAA (Health Insurance Portability and Accountability Act)</li>
        <li>HITECH (Health Information Technology for Economic and Clinical Health Act)</li>
        <li>FDA Software as a Medical Device (SaMD) guidelines where applicable</li>
        <li>NIST AI Risk Management Framework</li>
        <li>SOC 2 Type II security standards</li>
        <li>WCAG 2.1 AA accessibility standards</li>
        <li>State privacy laws (CCPA, CDPA, CPA, CTDPA, and emerging regulations)</li>
      </ul>

      <h2>5. When Trust is Broken: Our Response</h2>
      <p>Despite our best efforts, incidents may occur. When they do, we commit to:</p>

      <h3>5.1 Immediate Transparency</h3>
      <ul>
        <li>Notify affected users within 24 hours of confirming an incident</li>
        <li>Provide clear, honest explanations of what happened</li>
        <li>Avoid technical jargon and corporate-speak</li>
        <li>Take responsibility without deflection or blame-shifting</li>
      </ul>

      <h3>5.2 Swift Remediation</h3>
      <ul>
        <li>Immediately contain and neutralize threats</li>
        <li>Engage external experts if needed</li>
        <li>Implement fixes to prevent recurrence</li>
        <li>Offer remedies to affected users (credit monitoring, fee waivers, etc.)</li>
      </ul>

      <h3>5.3 Root Cause Analysis</h3>
      <ul>
        <li>Conduct thorough investigations to understand how incidents occurred</li>
        <li>Identify systemic issues, not just individual errors</li>
        <li>Publish findings (with appropriate redactions for security)</li>
        <li>Implement organizational and technical changes to prevent repetition</li>
      </ul>

      <div className="bg-blue-50 border border-blue-200 rounded-md p-4 my-4">
        <p className="font-bold text-blue-900">Recent Incidents:</p>
        <p className="text-sm mt-2">
          None as of January 7, 2026. This section will be updated if incidents occur.
        </p>
      </div>

      <h2>6. Our Business Model</h2>
      <div className="bg-gray-50 border border-gray-300 rounded-md p-4 my-4">
        <p className="font-bold mb-2">How We Make Money:</p>
        <ul className="text-sm space-y-1">
          <li>• Subscription fees for premium memberships</li>
          <li>• Institutional partnerships with healthcare organizations</li>
          <li>• Research grants (federal and foundation funding with user consent)</li>
          <li>• Value-based care contracts (shared savings agreements)</li>
        </ul>

        <p className="font-bold mt-4 mb-2">How We Do NOT Make Money:</p>
        <ul className="text-sm space-y-1">
          <li>• We do not sell your personal health information</li>
          <li>• We do not share identifiable data with advertisers</li>
          <li>• We do not accept payments to prioritize treatments or providers</li>
          <li>• We do not profit from undisclosed referral fees</li>
        </ul>

        <p className="text-sm mt-4">
          <strong>Financial Assistance:</strong> We offer sliding-scale pricing and free accounts for those
          experiencing financial hardship. Contact{' '}
          <a href="mailto:billing@ihep.app" className="text-primary hover:underline">billing@ihep.app</a> to apply.
        </p>
      </div>

      <h2>7. Accessibility and Inclusion</h2>
      <p>IHEP is for everyone. We are committed to:</p>
      <ul>
        <li><strong>Digital Accessibility:</strong> WCAG 2.1 AA compliance, screen reader compatibility</li>
        <li><strong>Language Access:</strong> Multilingual platform, translation services</li>
        <li><strong>Financial Accessibility:</strong> Free tier, sliding-scale pricing, assistance programs</li>
        <li><strong>Technology Accessibility:</strong> Mobile-responsive design, low-bandwidth mode</li>
      </ul>
      <p className="mt-2">
        If you encounter accessibility barriers, contact{' '}
        <a href="mailto:accessibility@ihep.app" className="text-primary hover:underline">accessibility@ihep.app</a>.
      </p>

      <h2>8. How to Hold Us Accountable</h2>

      <h3>8.1 Asking Questions</h3>
      <div className="bg-gray-100 rounded-md p-4 my-4">
        <p className="text-sm">
          General Inquiries: <a href="mailto:hello@ihep.app" className="text-primary hover:underline">hello@ihep.app</a><br />
          Privacy Concerns: <a href="mailto:privacy@ihep.app" className="text-primary hover:underline">privacy@ihep.app</a><br />
          Security Issues: <a href="mailto:security@ihep.app" className="text-primary hover:underline">security@ihep.app</a><br />
          Trust & Ethics: <a href="mailto:ethics@ihep.app" className="text-primary hover:underline">ethics@ihep.app</a>
        </p>
      </div>

      <h3>8.2 Filing Complaints</h3>
      <p>If you believe we have violated this Trust Statement:</p>
      <ol className="mt-2">
        <li>1. Contact us at ethics@ihep.app with your concern</li>
        <li>2. We will investigate and respond within 30 days</li>
        <li>3. If unsatisfied, escalate to our Patient Advisory Council</li>
        <li>4. File complaints with regulatory agencies (HHS OCR, FTC, state AG)</li>
      </ol>

      <h3>8.3 Participating in Governance</h3>
      <ul>
        <li>Join our Patient Advisory Council (applications accepted quarterly)</li>
        <li>Participate in user research and feedback sessions</li>
        <li>Attend virtual town halls (quarterly)</li>
        <li>Vote in member surveys on major platform changes</li>
      </ul>

      <h2>9. Final Word</h2>
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-md p-6 my-6">
        <p className="text-base leading-relaxed">
          Trust is earned through consistent action, not eloquent words. This document represents our
          aspirations and commitments, but our true measure is how we behave when tested—when systems
          fail, when difficult decisions arise, when shortcuts tempt.
        </p>
        <p className="text-base leading-relaxed mt-4">
          We promise to choose your trust over our convenience, your safety over our efficiency, your
          dignity over our profits.
        </p>
        <p className="text-base leading-relaxed mt-4 font-semibold">
          Thank you for placing your trust in IHEP. We do not take it lightly.
        </p>
      </div>

      <div className="mt-8 pt-8 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          <strong>Version:</strong> 1.0<br />
          <strong>Effective Date:</strong> January 7, 2026<br />
          <strong>Next Review:</strong> January 2027
        </p>
        <p className="text-sm text-gray-600 mt-4">
          <strong>With gratitude and accountability,</strong><br />
          Jason M Jarmacz<br />
          Founder & Principal Investigator<br />
          IHEP - Integrated Health Empowerment Program
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
            <a href="/legal/privacy" className="text-primary hover:underline">Privacy Policy</a>
          </li>
          <li>
            <a href="/legal/ai-governance" className="text-primary hover:underline">AI Governance Policy</a>
          </li>
        </ul>
      </div>
    </LegalDocument>
  )
}
