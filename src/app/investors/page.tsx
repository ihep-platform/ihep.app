import Link from 'next/link';

type Metric = { value: string; label: string };
type DocumentCard = {
  href: string;
  icon: string;
  title: string;
  desc: string;
  format: string;
};

const investorMetrics: Metric[] = [
  { value: '$290B', label: 'Annual Cost of Non-Adherence' },
  { value: '40%', label: 'HIV Patients Lost in 6 Months' },
  { value: '66%', label: 'Current Viral Suppression Rate' },
  { value: '1.2M', label: 'Americans Living with HIV' },
];

const investorDocuments: DocumentCard[] = [
  {
    href: '/docs/ihep-pitch-deck.pdf',
    icon: 'Deck',
    title: 'Investor Deck',
    desc: 'Market, differentiation, roadmap, and team overview.',
    format: 'PDF',
  },
  {
    href: '/docs/IHEP%20Comprehensive%20Financial%20Model.pdf',
    icon: 'Finance',
    title: 'Financial Model',
    desc: 'Phase I budget, 10-year projections, and unit economics.',
    format: 'PDF',
  },
  {
    href: '/docs/IHEP%20Complete%20Due%20Diligence%20Package.pdf',
    icon: 'Checklist',
    title: 'Due Diligence Package',
    desc: 'Key materials assembled for investor diligence requests.',
    format: 'PDF',
  },
  {
    href: '/investor-dashboard',
    icon: 'Dashboard',
    title: 'Investor Dashboard',
    desc: 'Interactive ROI, funding model, and financial impact views.',
    format: 'HTML',
  },
];

export default function InvestorsPage() {
  return (
    <div className="ihep-landing">
      <nav>
        <div className="nav-container">
          <Link href="/" className="logo">
            IHEP
          </Link>
          <ul className="nav-links">
            <li>
              <Link href="/">Home</Link>
            </li>
            <li>
              <Link href="/investor-dashboard">Investor Dashboard</Link>
            </li>
          </ul>
          <Link href="/investor-dashboard" className="cta-button hidden-mobile">
            Open Dashboard
          </Link>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-container">
          <h1>Investor Materials</h1>
          <p>
            Key diligence documents, financial model, and the interactive dashboard are collected
            here for capital partners.
          </p>
          <div>
            <Link href="/investor-dashboard" className="cta-button">
              View Investor Dashboard
            </Link>
            <Link href="/" className="secondary-button">
              Back to Home
            </Link>
          </div>
        </div>
      </section>

      <section className="light">
        <div className="container">
          <h2 className="text-center">Snapshot Metrics</h2>
          <div className="metrics text-center">
            {investorMetrics.map((metric) => (
              <div className="metric" key={metric.label}>
                <div className="metric-number">{metric.value}</div>
                <div className="metric-label">{metric.label}</div>
              </div>
            ))}
          </div>

          <h2 className="text-center" style={{ marginTop: 'var(--spacing-48)' }}>
            Downloads &amp; Tools
          </h2>
          <div className="doc-grid" style={{ marginTop: 'var(--spacing-24)' }}>
            {investorDocuments.map((doc) => (
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
        </div>
      </section>

      <footer>
        <div className="footer-bottom">
          <p>© 2026 Integrated Health Empowerment Program (IHEP). All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

