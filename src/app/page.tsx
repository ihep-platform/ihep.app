// src/app/page.tsx - Render the landing page to match index.html
'use client';

import React, { useCallback, useState } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Menu } from 'lucide-react';

type NavLink = { id: string; label: string };
type Metric = { value: string; label: string };
type DocumentCard = { href: string; icon: string; title: string; desc: string; format: string };
type Position = { title: string; reqs: string; comp: string };

const navLinks: NavLink[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'documents', label: 'Documents' },
  { id: 'press', label: 'Press Kit' },
  { id: 'team', label: 'Team' },
  { id: 'partner', label: 'Partner With Us' },
];

const metrics: Metric[] = [
  { value: '$290B', label: 'Annual Cost of Non-Adherence' },
  { value: '40%', label: 'HIV Patients Lost in 6 Months' },
  { value: '66%', label: 'Current Viral Suppression Rate' },
  { value: '1.2M', label: 'Americans Living with HIV' },
];

const documents: DocumentCard[] = [
  {
    href: '/docs/A%20Recursive%20Blueprint%20for%20a%20Global%20Problem.pdf',
    icon: 'Doc',
    title: 'One-Page Overview',
    desc: "Quick introduction to IHEP's problem, solution, market opportunity, and funding ask. Perfect for first impressions.",
    format: 'PDF',
  },
  {
    href: '/docs/ihep-pitch-deck.pdf',
    icon: 'Deck',
    title: 'Investor Deck',
    desc: 'Comprehensive 10-12 slide presentation covering market opportunity, technology differentiation, financial projections, team, and investment terms.',
    format: 'PDF',
  },
  {
    href: '/docs/architecture/HUB_AND_SPOKE_ARCHITECTURE.md',
    icon: 'Arch',
    title: 'Hub-and-Spoke Architecture',
    desc: 'Complete technical architecture showing how IHEP uses a central hub with domain spokes for omnidirectional data flow and HIPAA compliance.',
    format: 'Markdown',
  },
  {
    href: '/docs/IHEP%20System%20Architecture%20Document.pdf',
    icon: 'Build',
    title: 'Technical Architecture',
    desc: 'Detailed whitepaper covering digital twin technology, federated learning, morphogenetic framework, and NIST compliance architecture.',
    format: 'PDF',
  },
  {
    href: '/docs/IHEP%20Comprehensive%20Financial%20Model.pdf',
    icon: 'Finance',
    title: 'Financial Model',
    desc: 'Phase I budget breakdown, 10-year financial projections, unit economics, and path to profitability. Conservative assumptions detailed.',
    format: 'PDF',
  },
  {
    href: '/docs/IHEP%20Phase%20I%20Detailed%20Project%20Plan.pdf',
    icon: 'Plan',
    title: 'Pilot Plan & Timeline',
    desc: 'Detailed Phase I implementation roadmap with milestones, success metrics, outcome measurement methodology, and measurable endpoints.',
    format: 'PDF',
  },
  {
    href: '/docs/IHEP%20Complete%20Due%20Diligence%20Package.pdf',
    icon: 'Checklist',
    title: 'Due Diligence Package',
    desc: 'Complete due diligence documentation for investor review including all key materials and supporting documents.',
    format: 'PDF',
  },
  {
    href: '/investor-dashboard',
    icon: 'Dashboard',
    title: 'Investor Dashboard',
    desc: 'Interactive 10 year Income Streams, Financial Impact, Income Streams, Op Costs, Funding Model & ROI Analysis.',
    format: 'HTML',
  },
];

const positions: Position[] = [
  {
    title: 'Chief Technology Officer',
    reqs: '10+ years software architecture, healthcare tech background, AIML expertise, HIPAA-compliant systems at scale',
    comp: '$200K base + 3% equity + performance bonuses',
  },
  {
    title: 'Chief Security & Compliance Officer',
    reqs: 'CISSP/equivalent, healthcare compliance expertise (HIPAA, NIST), FDA digital health regulations',
    comp: '$180K base + 2% equity',
  },
  {
    title: 'Clinical Director',
    reqs: 'MD/equivalent, HIV/AIDS clinical expertise, clinical informatics background',
    comp: '$220K base + 2% equity',
  },
  {
    title: 'Community Engagement Director',
    reqs: '7+ years community health work, HIV/AIDS service org leadership, lived experience preferred',
    comp: '$140K base + 1.5% equity',
  },
  {
    title: 'AIML Lead Engineer',
    reqs: 'PhD in CS/ML or equivalent, healthcare AI experience, federated learning expertise',
    comp: '$180K base + 2% equity',
  },
];

export default function InvestorLandingPage() {
  const [email, setEmail] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const smoothScroll = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const handleAnchor = useCallback(
    (event: React.MouseEvent<HTMLAnchorElement>, id: string) => {
      event.preventDefault();
      smoothScroll(id);
    },
    [smoothScroll],
  );

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    alert('Thank you for subscribing! Check your email for a welcome message.');
    setEmail('');
  };

  return (
    <>
      <div className="ihep-landing">
        <nav>
          <div className="nav-container">
            <a href="#overview" className="logo" onClick={(e) => handleAnchor(e, 'overview')}>
              IHEP
            </a>
            <ul className="nav-links">
              {navLinks.map((link) => (
                <li key={link.id}>
                  <a href={`#${link.id}`} onClick={(e) => handleAnchor(e, link.id)}>
                    {link.label}
                  </a>
                </li>
              ))}
              <li>
                <a href="/investor-dashboard">Investor Dashboard</a>
              </li>
            </ul>
            <a
              href="#newsletter"
              className="cta-button hidden-mobile"
              onClick={(e) => handleAnchor(e, 'newsletter')}
            >
              Subscribe
            </a>
            {/* Mobile hamburger menu button */}
            <button
              className="mobile-menu-button"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open navigation menu"
              type="button"
            >
              <Menu className="h-6 w-6" />
            </button>
          </div>
        </nav>

        {/* Mobile navigation sheet */}
        <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
          <SheetContent side="right" className="w-[85%] max-w-[350px] bg-white">
            <SheetHeader className="mb-6">
              <SheetTitle className="text-xl font-bold" style={{ color: 'var(--color-teal-600)' }}>
                IHEP
              </SheetTitle>
              <SheetDescription className="sr-only">
                Site navigation links
              </SheetDescription>
            </SheetHeader>
            <div className="flex flex-col space-y-1">
              {navLinks.map((link) => (
                <a
                  key={link.id}
                  href={`#${link.id}`}
                  onClick={(e) => {
                    handleAnchor(e, link.id);
                    setMobileMenuOpen(false);
                  }}
                  className="flex items-center min-h-[48px] px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 font-medium text-base transition-colors"
                >
                  {link.label}
                </a>
              ))}
              <a
                href="/investor-dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center min-h-[48px] px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 font-medium text-base transition-colors"
              >
                Investor Dashboard
              </a>
              <hr className="my-3 border-gray-200" />
              <a
                href="#newsletter"
                onClick={(e) => {
                  handleAnchor(e, 'newsletter');
                  setMobileMenuOpen(false);
                }}
                className="flex items-center justify-center min-h-[48px] px-4 py-3 rounded-lg font-semibold text-base text-white transition-colors"
                style={{ background: 'var(--color-teal-600)' }}
              >
                Subscribe
              </a>
            </div>
          </SheetContent>
        </Sheet>

        <section className="hero">
          <div className="hero-container">
            <h1>Transforming Healthcare Aftercare Through AI-Powered Digital Twins</h1>
            <p>
              The Integrated Health Empowerment Program (IHEP) solves the $290 billion problem of
              treatment non-adherence by combining patient digital twins, organizational ecosystem
              mapping, and federated AI learning—built on Google Cloud with compliance-first
              architecture.
            </p>
            <div>
              <button type="button" className="cta-button" onClick={() => smoothScroll('overview')}>
                Learn More
              </button>
              <a
                href="/docs/ihep-pitch-deck.pdf"
                className="secondary-button"
                target="_blank"
                rel="noopener noreferrer"
              >
                Download Our Deck
              </a>
            <a
              href="/investor-dashboard"
              className="secondary-button"
              rel="noopener noreferrer"
            >
              View Investor Dashboard
            </a>
            </div>
          </div>
        </section>

        <section id="overview" className="light">
          <div className="container">
            <h2 className="text-center">IHEP in 90 Seconds</h2>

            <div className="metrics text-center">
              {metrics.map((metric) => (
                <div className="metric" key={metric.label}>
                  <div className="metric-number">{metric.value}</div>
                  <div className="metric-label">{metric.label}</div>
                </div>
              ))}
            </div>

            <div className="overview-grid">
              <div className="overview-card">
                <h3>The Problem</h3>
                <p>
                  When patients receive life-altering diagnoses like HIV, cancer, or rare blood
                  diseases, the healthcare system provides excellent acute care but abandons them in
                  the critical months that follow. The result: 40% dropout rates, $290 billion in
                  wasted healthcare costs, and preventable deaths.
                </p>
              </div>

              <div className="overview-card">
                <h3>The Solution</h3>
                <p>
                  <span className="highlight">Patient Digital Twins</span> fuse clinical,
                  psychosocial, environmental, and behavioral data to anticipate challenges before
                  they manifest. <span className="highlight">Organizational Twins</span> map entire
                  care ecosystems. <span className="highlight">Federated AI</span> learns across
                  sites without moving private health information.
                </p>
              </div>

              <div className="overview-card">
                <h3>The Impact</h3>
                <p>
                  Phase I pilot targeting 15% improvement in appointment adherence, 25% reduction in
                  emergency department visits, and 85% viral suppression rate (vs. 66% national
                  average). Built on Google Cloud with NIST SP 800-53r5 compliance-first
                  architecture.
                </p>
              </div>
            </div>

            <div
              style={{
                background: 'var(--color-gray-200)',
                padding: 'var(--spacing-24)',
                borderRadius: 'var(--radius-lg)',
                marginTop: 'var(--spacing-32)',
              }}
            >
              <h3 style={{ marginTop: 0 }}>Raising $3.5M Series Seed</h3>
              <p>
                To fund Phase I pilot deployment in Miami/Orlando, executive team assembly,
                compliance validation, and outcome demonstration.
              </p>
              <p>
                <strong>Investment Terms:</strong> Convertible note, 20% Series A discount, $15M
                cap, 6% interest, 24-month maturity. Minimum investment $100K.
              </p>
              <p>
                <strong>Timeline:</strong> Operations commence March 2026. SBIR Phase I application
                April 5, 2026 ($300K non-dilutive if successful).
              </p>
            </div>
          </div>
        </section>

        <section id="documents" className="gray">
          <div className="container">
            <h2 className="text-center">Document Library</h2>
            <p
              className="text-center"
              style={{ marginBottom: 'var(--spacing-32)', color: 'var(--color-slate-500)' }}
            >
              All materials available for download. Password-protected materials upon request.
            </p>

            <div className="doc-grid">
              {documents.map((doc) => (
                <a
                  key={doc.title}
                  className="doc-card"
                  href={doc.href}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <div className="doc-icon" aria-hidden="true">
                    {doc.icon}
                  </div>
                  <div className="doc-title">{doc.title}</div>
                  <div className="doc-desc">{doc.desc}</div>
                  <div className="doc-size">{doc.format}</div>
                </a>
              ))}
            </div>

            <p
              className="text-center"
              style={{
                marginTop: 'var(--spacing-48)',
                color: 'var(--color-slate-500)',
                fontSize: 'var(--font-size-sm)',
              }}
            >
              Additional materials available upon request: Technical specifications • Security &
              Compliance Framework • Clinical Study Protocol • Partnership Agreements • Regulatory
              Strategy
            </p>
          </div>
        </section>

        <section id="press" className="light">
          <div className="container">
            <h2 className="text-center">Press &amp; Media Kit</h2>

            <div
              style={{
                background: varString('--color-gray-200'),
                padding: varString('--spacing-32'),
                borderRadius: varString('--radius-lg'),
                marginTop: varString('--spacing-32'),
              }}
            >
              <h3>Company Boilerplate</h3>
              <p style={{ marginBottom: varString('--spacing-16') }}>
                <strong>50-word version:</strong>
              </p>
              <p
                style={{
                  marginBottom: varString('--spacing-24'),
                  fontStyle: 'italic',
                  color: varString('--color-slate-600'),
                }}
              >
                "The Integrated Health Empowerment Program (IHEP) is an AI-driven digital health
                platform transforming aftercare for life-altering conditions. Using patient digital
                twins, organizational ecosystem mapping, and federated learning, IHEP addresses the
                $290 billion problem of treatment non-adherence while building the data
                infrastructure for breakthrough treatments. Founded by Jason Jarmacz."
              </p>

              <p style={{ marginBottom: varString('--spacing-16') }}>
                <strong>100-word version:</strong>
              </p>
              <p
                style={{
                  marginBottom: varString('--spacing-24'),
                  fontStyle: 'italic',
                  color: varString('--color-slate-600'),
                }}
              >
                "The Integrated Health Empowerment Program (IHEP) is a morphogenetic digital health
                ecosystem solving the $290 billion annual crisis of treatment non-adherence in
                life-altering conditions like HIV, cancer, and rare blood diseases. IHEP combines
                three layers of innovation: patient digital twins that anticipate challenges before
                they manifest, organizational twins that optimize entire care ecosystems, and
                federated AI networks that learn across sites without moving private health
                information. Built on Google Cloud with compliance-first NIST SP 800-53r5
                architecture, IHEP demonstrates measurable outcomes while building the data
                infrastructure for functional cures. Founded by Jason Jarmacz, Chief Evolution
                Strategist, IHEP is raising a $3.5M Series Seed to fund Phase I pilot operations."
              </p>

              <h3 style={{ marginTop: varString('--spacing-32') }}>Media Assets</h3>
              <ul style={{ marginTop: varString('--spacing-16') }}>
                <li style={{ marginBottom: varString('--spacing-8') }}>
                  <strong>Logo Files:</strong> SVG, PNG (white, dark, full color versions) available
                  upon request
                </li>
                <li style={{ marginBottom: varString('--spacing-8') }}>
                  <strong>Founder Photo:</strong> High-resolution headshot (JPG, 4000x5000px)
                  available upon request
                </li>
                <li style={{ marginBottom: varString('--spacing-8') }}>
                  <strong>Key Statistics:</strong> $290B annual cost, 40% dropout rate, 1.2M
                  Americans with HIV, 25.9% digital health CAGR
                </li>
                <li style={{ marginBottom: varString('--spacing-8') }}>
                  <strong>Media Contact:</strong> press@ihep.app
                </li>
              </ul>
            </div>
          </div>
        </section>

        <section id="team" className="gray">
          <div className="container">
            <h2 className="text-center">Founding Team &amp; Advisory</h2>

            <div style={{ maxWidth: 800, margin: `${varString('--spacing-32')} auto` }}>
              <h3>Jason Jarmacz, Founder &amp; Principal Investigator</h3>
              <p style={{ marginBottom: varString('--spacing-16') }}>
                15+ years in business development and research analytics; 5+ years in healthcare
                insights. Jason has persevered through multiple hardships pursuing his life goal of
                developing an application that changes humanity and provides uplift to community.
                His evolution strategy framework informed IHEP's three-layer architecture. Based in
                Newark, New Jersey.
              </p>

              <h3 style={{ marginTop: varString('--spacing-32') }}>Positions Now Hiring (Phase I)</h3>
              <div style={{ marginTop: varString('--spacing-16') }}>
                {positions.map((job) => (
                  <p key={job.title} style={{ marginTop: varString('--spacing-16') }}>
                    <strong>{job.title}</strong>
                    <br />
                    Requirements: {job.reqs}
                    <br />
                    Compensation: {job.comp}
                  </p>
                ))}
              </div>

              <p style={{ marginTop: varString('--spacing-24') }}>
                <strong>Advisory Board Status:</strong> Building advisory board of healthcare
                researchers, health equity experts, AI ethicists, and experienced founders. Advisor
                compensation: 0.25% equity, 2-year vest, quarterly engagement requirements.
              </p>
            </div>
          </div>
        </section>

        <section id="partner" className="light">
          <div className="container">
            <h2 className="text-center">Partner With IHEP</h2>

            <div style={{ maxWidth: 900, margin: `${varString('--spacing-32')} auto` }}>
              <p
                style={{
                  fontSize: varString('--font-size-lg'),
                  textAlign: 'center',
                  marginBottom: varString('--spacing-32'),
                }}
              >
                We're seeking partnerships across three dimensions: investment, clinical
                collaboration, and technology integration.
              </p>

              <div className="overview-grid">
                <div className="overview-card">
                  <h3>Funding Partnership</h3>
                  <p>
                    <strong>Investment Opportunity:</strong> $3.5M Series Seed round at $12M
                    pre-money valuation. Convertible note terms: 20% Series A discount, $15M cap, 6%
                    interest, 24-month maturity.
                  </p>
                  <p style={{ marginTop: varString('--spacing-12') }}>
                    <strong>Investor Types:</strong> VCs, impact investors, angels, strategic
                    investors, foundations.
                  </p>
                </div>

                <div className="overview-card">
                  <h3>Healthcare System Partnership</h3>
                  <p>
                    <strong>Phase I Pilot Sites:</strong> Seeking 2-4 healthcare systems in
                    Miami/Orlando for 150-300 participant pilot. Pilot partners receive early access
                    to platform, co-publication opportunities, revenue sharing on successful
                    outcomes.
                  </p>
                </div>

                <div className="overview-card">
                  <h3>Research Collaboration</h3>
                  <p>
                    <strong>Academic Partners:</strong> Co-PI arrangements, data access agreements,
                    joint publications. Platform offers unprecedented longitudinal dataset for HIV
                    treatment research.
                  </p>
                  <p style={{ marginTop: varString('--spacing-12') }}>
                    <strong>Also Seeking:</strong> Regulatory consultants, clinical advisors, AI
                    ethics experts.
                  </p>
                </div>
              </div>
            </div>

            <div id="newsletter" className="newsletter-form">
              <h3>Stay Connected</h3>
              <p>
                Subscribe to IHEP Progress Brief—weekly updates on digital health innovation,
                clinical outcomes, and fundraising milestones.
              </p>
              <form className="form-group" onSubmit={handleSubmit}>
                <input
                  type="email"
                  placeholder="your.email@example.com"
                  required
                  aria-label="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <button type="submit">Subscribe</button>
              </form>
              <p style={{ fontSize: varString('--font-size-sm'), marginTop: varString('--spacing-16') }}>
                We'll never share your email. Unsubscribe anytime.
              </p>
            </div>
          </div>
        </section>

        <footer>
          <div className="footer-container">
            <div className="footer-section">
              <h4>About IHEP</h4>
              <ul>
                <li>
                  <a href="#overview" onClick={(e) => handleAnchor(e, 'overview')}>
                    Our Mission
                  </a>
                </li>
                <li>
                  <a href="#team" onClick={(e) => handleAnchor(e, 'team')}>
                    Leadership
                  </a>
                </li>
                <li>
                  <a href="#partner" onClick={(e) => handleAnchor(e, 'partner')}>
                    Careers
                  </a>
                </li>
                <li>
                  <a href="mailto:press@ihep.app">Press Inquiries</a>
                </li>
              </ul>
            </div>

            <div className="footer-section">
              <h4>Resources</h4>
              <ul>
                <li>
                  <a href="#documents" onClick={(e) => handleAnchor(e, 'documents')}>
                    Document Library
                  </a>
                </li>
                <li>
                  <a href="#documents" onClick={(e) => handleAnchor(e, 'documents')}>
                    Investor Deck
                  </a>
                </li>
                <li>
                  <a href="/investor-dashboard">Investor Dashboard</a>
                </li>
                <li>
                  <a href="#documents" onClick={(e) => handleAnchor(e, 'documents')}>
                    FAQ
                  </a>
                </li>
              </ul>
            </div>

            <div className="footer-section">
              <h4>Architecture</h4>
              <ul>
                <li>
                  <a href="/docs/architecture/HUB_AND_SPOKE_ARCHITECTURE.md">
                    Hub-and-Spoke Design
                  </a>
                </li>
                <li>
                  <a href="/RESTRUCTURING_REPORT.md">
                    System Structure
                  </a>
                </li>
                <li>
                  <a href="/docs/IHEP%20System%20Architecture%20Document.pdf">
                    Technical Whitepaper
                  </a>
                </li>
                <li>
                  <a href="/docs/Phase_4_Deployment_Architecture_on_Google_Cloud_Platform.md">
                    GCP Deployment
                  </a>
                </li>
              </ul>
            </div>

            <div className="footer-section">
              <h4>Connect</h4>
              <ul>
                <li>
                  <a href="https://linkedin.com/" target="_blank" rel="noopener noreferrer">
                    LinkedIn
                  </a>
                </li>
                <li>
                  <a href="https://substack.com/" target="_blank" rel="noopener noreferrer">
                    Newsletter
                  </a>
                </li>
                <li>
                  <a href="mailto:jason@ihep.app">Contact Us</a>
                </li>
                <li>
                  <a href="https://zenodo.org/" target="_blank" rel="noopener noreferrer">
                    Publications (DOI)
                  </a>
                </li>
              </ul>

              <div className="social-links" style={{ marginTop: varString('--spacing-16') }}>
                <a href="https://linkedin.com/" target="_blank" rel="noopener noreferrer" title="LinkedIn">
                  in
                </a>
                <a href="https://twitter.com/" target="_blank" rel="noopener noreferrer" title="Twitter/X">
                  𝕏
                </a>
                <a href="https://github.com/" target="_blank" rel="noopener noreferrer" title="GitHub">
                  GH
                </a>
              </div>
            </div>

            <div className="footer-section">
              <h4>Compliance</h4>
              <ul>
                <li>
                  <a href="/legal/privacy">Privacy Policy</a>
                </li>
                <li>
                  <a href="/legal/terms">Terms of Service</a>
                </li>
                <li>
                  <a href="/legal/compliance">Security Framework</a>
                </li>
                <li>
                  <a href="/legal/compliance">HIPAA Notice</a>
                </li>
              </ul>
            </div>
          </div>

          <div className="footer-bottom">
            <p>© 2026 Integrated Health Empowerment Program (IHEP). All rights reserved.</p>
            <p style={{ marginTop: varString('--spacing-8') }}>
              Building the future of healthcare aftercare through AI-powered digital twins and
              community partnership.
            </p>
          </div>
        </footer>
      </div>
    </>
  );
}

function varString(name: string) {
  return `var(${name})`;
}
