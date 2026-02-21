// src/app/page.tsx - Render the landing page to match index.html
'use client';

import React, { useCallback, useState } from 'react';
import { getSession, signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Menu } from 'lucide-react';

type NavLink = { id: string; label: string };
type DocumentCard = { href: string; icon: string; title: string; desc: string; format: string };

const navLinks: NavLink[] = [
  { id: 'digital-twins', label: '5-Pillar Twins' },
  { id: 'financial', label: 'Financial Support' },
  { id: 'research', label: 'Research (Optional)' },
  { id: 'program', label: 'What You Get' },
  { id: 'documents', label: 'Resources' },
  { id: 'get-started', label: 'Get Started' },
];

const patientResources: DocumentCard[] = [
  {
    href: '/resources',
    icon: 'Hub',
    title: 'Resource Hub',
    desc: 'Programs, groups, and articles curated to your needs and condition.',
    format: 'Page',
  },
  {
    href: '/dashboard/digital-twin',
    icon: 'Twin',
    title: 'Digital Twin Dashboard',
    desc: 'Your 5-pillar snapshots, insights, and next-step recommendations (members-only).',
    format: 'Members',
  },
  {
    href: '/dashboard/calendar',
    icon: 'Calendar',
    title: 'Dynamic Calendar',
    desc: 'Appointments, medications, and support tasks consolidated in one schedule (members-only).',
    format: 'Members',
  },
  {
    href: '/dashboard/financials',
    icon: 'Finance',
    title: 'Financial Empowerment',
    desc: 'Benefits optimization and opportunity matching to reduce treatment drop-off (members-only).',
    format: 'Members',
  },
  {
    href: '/legal/trust',
    icon: 'Shield',
    title: 'Privacy & Trust',
    desc: 'How we protect your data with security-first controls and HIPAA-aligned safeguards.',
    format: 'Page',
  },
];

export default function LandingPage() {
  const [email, setEmail] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [signInOpen, setSignInOpen] = useState(false);
  const [signInUsername, setSignInUsername] = useState('');
  const [signInPassword, setSignInPassword] = useState('');
  const [signInLoading, setSignInLoading] = useState(false);
  const [signInError, setSignInError] = useState<string | null>(null);
  const router = useRouter();

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

  const openSignIn = useCallback(() => {
    setSignInError(null);
    setSignInOpen(true);
  }, []);

  const handleSignIn = useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();
      if (signInLoading) return;

      setSignInLoading(true);
      setSignInError(null);

      try {
        const result = await signIn('credentials', {
          username: signInUsername,
          password: signInPassword,
          redirect: false,
        });

        if (result?.error) {
          setSignInError('Invalid username or password');
          return;
        }

        await getSession();
        setSignInOpen(false);
        setSignInPassword('');
        router.push('/dashboard');
      } catch {
        setSignInError('An error occurred during sign in');
      } finally {
        setSignInLoading(false);
      }
    },
    [router, signInLoading, signInPassword, signInUsername],
  );

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    alert('Thank you for subscribing! Check your email for a welcome message.');
    setEmail('');
  };

  return (
    <>
      <div className="ihep-landing">
        <Dialog
          open={signInOpen}
          onOpenChange={(open) => {
            setSignInOpen(open);
            if (!open) {
              setSignInError(null);
              setSignInPassword('');
            }
          }}
        >
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Sign in</DialogTitle>
              <DialogDescription>
                Access your dashboard, calendar, and personalized next steps.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleSignIn} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="ihep-signin-username">Email or username</Label>
                <Input
                  id="ihep-signin-username"
                  type="text"
                  value={signInUsername}
                  onChange={(e) => setSignInUsername(e.target.value)}
                  autoComplete="username"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ihep-signin-password">Password</Label>
                <Input
                  id="ihep-signin-password"
                  type="password"
                  value={signInPassword}
                  onChange={(e) => setSignInPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>

              {signInError ? <div className="text-sm text-red-600">{signInError}</div> : null}

              <Button type="submit" className="w-full" disabled={signInLoading}>
                {signInLoading ? 'Signing in…' : 'Sign in'}
              </Button>
            </form>

            <div className="text-center text-sm text-muted-foreground">
              Don&apos;t have an account?{' '}
              <a href="/register" className="text-primary hover:underline">
                Create one
              </a>
              <span className="mx-2">·</span>
              <a href="/login" className="hover:underline">
                Use full sign-in page
              </a>
            </div>
          </DialogContent>
        </Dialog>

        <nav>
          <div className="nav-container">
            <a href="#digital-twins" className="logo" onClick={(e) => handleAnchor(e, 'digital-twins')}>
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
              <li className="hidden-mobile">
                <a
                  href="/login"
                  onClick={(e) => {
                    e.preventDefault();
                    openSignIn();
                  }}
                >
                  Sign in
                </a>
              </li>
            </ul>
            <a
              href="#get-started"
              className="cta-button hidden-mobile"
              onClick={(e) => handleAnchor(e, 'get-started')}
            >
              Get Started
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
                href="/login"
                onClick={(e) => {
                  e.preventDefault();
                  setMobileMenuOpen(false);
                  openSignIn();
                }}
                className="flex items-center min-h-[48px] px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 font-medium text-base transition-colors"
              >
                Sign in
              </a>
              <hr className="my-3 border-gray-200" />
              <a
                href="#get-started"
                onClick={(e) => {
                  handleAnchor(e, 'get-started');
                  setMobileMenuOpen(false);
                }}
                className="flex items-center justify-center min-h-[48px] px-4 py-3 rounded-lg font-semibold text-base text-white transition-colors"
                style={{ background: 'var(--color-teal-600)' }}
              >
                Get Started
              </a>
            </div>
          </SheetContent>
        </Sheet>

        <section className="hero">
          <div className="hero-container">
            <h1>Adherence support that adapts to you</h1>
            <p>
              IHEP helps you keep appointments, take medications on time, and navigate aftercare by
              turning your clinical and daily-life signals into clear next steps—across 5-pillar
              digital twins, financial support, and a dynamic calendar—built with privacy-first
              safeguards.
            </p>
            <div>
              <button type="button" className="cta-button" onClick={() => smoothScroll('get-started')}>
                Get Started
              </button>
              <a href="#program" className="secondary-button" onClick={(e) => handleAnchor(e, 'program')}>
                What you get
              </a>
              <a
                href="#digital-twins"
                className="secondary-button"
                onClick={(e) => handleAnchor(e, 'digital-twins')}
              >
                How it works
              </a>
            </div>
          </div>
        </section>

        <section id="digital-twins" className="light">
          <div className="container">
            <h2 className="text-center">5-Pillar Twin System</h2>
            <p
              className="text-center"
              style={{ marginBottom: 'var(--spacing-32)', color: 'var(--color-slate-500)' }}
            >
              Clinical · Behavioral · Social · Financial · Personal
            </p>

            <div className="overview-grid">
              <div className="overview-card">
                <h3>Clinical Twin</h3>
                <p>
                  Represents diagnoses, medications, vitals, labs, and care plan milestones. It
                  synthesizes EHR signals and time-series telemetry to surface risks and next-step
                  actions for the patient and care team.
                </p>
              </div>

              <div className="overview-card">
                <h3>Behavioral Twin</h3>
                <p>
                  Represents daily habits and engagement (sleep, activity, nutrition, routines). It
                  converts self-reports and wearable patterns into achievable micro-goals and
                  adherence-support nudges tailored to readiness.
                </p>
              </div>

              <div className="overview-card">
                <h3>Social Twin</h3>
                <p>
                  Represents social determinants and support systems (housing, transportation, food,
                  community support). It flags barriers early and orchestrates referrals to the
                  right programs, groups, and services.
                </p>
              </div>

              <div className="overview-card">
                <h3>Financial Twin</h3>
                <p>
                  Represents affordability, benefits utilization, and income stability. It powers
                  benefit optimization, opportunity matching, and financial health scoring to
                  reduce financial friction that drives treatment drop-off.
                </p>
              </div>

              <div className="overview-card">
                <h3>Personal Twin</h3>
                <p>
                  Represents goals, preferences, values, and sentiment over time. It aligns
                  recommendations to what matters most to the person and adapts communication to
                  improve engagement and follow-through.
                </p>
              </div>
            </div>

            <div
              style={{
                background: varString('--color-gray-200'),
                padding: varString('--spacing-24'),
                borderRadius: varString('--radius-lg'),
                marginTop: varString('--spacing-32'),
              }}
            >
              <h3 style={{ marginTop: 0 }}>How it works</h3>
              <p style={{ marginBottom: varString('--spacing-16') }}>
                Each pillar produces a time-updated snapshot (scores, trends, and insights). IHEP
                then synthesizes the pillars into a single prioritized action plan across patient,
                care team, and community resources.
              </p>
              <ul style={{ marginTop: 0 }}>
                <li>Ingest signals (EHR, labs, wearables, check-ins, SDOH screens, benefits data)</li>
                <li>Compute pillar scores, trends, and risk indicators</li>
                <li>Generate recommendations and next-best actions</li>
                <li>Coordinate tasks and follow-ups across stakeholders</li>
                <li>Improve continuously via privacy-preserving learning (federated AI)</li>
              </ul>
            </div>

            <div
              style={{
                background: varString('--color-gray-200'),
                padding: varString('--spacing-24'),
                borderRadius: varString('--radius-lg'),
                marginTop: varString('--spacing-24'),
              }}
            >
              <h3 style={{ marginTop: 0 }}>How this supports adherence</h3>
              <ul style={{ marginTop: 0 }}>
                <li>Helps you build medication routines and keep track of next steps</li>
                <li>Surfaces early warning signs (missed tasks, barriers, stress) before you fall behind</li>
                <li>Connects you to the right resources when cost, transportation, or support is the blocker</li>
                <li>Creates a clear, prioritized plan you can follow day to day</li>
              </ul>
            </div>
          </div>
        </section>

        <section id="financial" className="gray">
          <div className="container">
            <h2 className="text-center">Financial Support</h2>
            <div className="overview-grid">
              <div className="overview-card">
                <h3>Benefits &amp; Coverage</h3>
                <p>
                  Helps you identify programs you may qualify for and organize what to do next—so
                  cost and paperwork do not become the reason you miss care.
                </p>
              </div>
              <div className="overview-card">
                <h3>Opportunities &amp; Stability</h3>
                <p>
                  Matches you with opportunities aligned to your health constraints and readiness,
                  helping stabilize income during treatment and recovery.
                </p>
              </div>
              <div className="overview-card">
                <h3>Affordability Check-ins</h3>
                <p>
                  Flags affordability stress early and recommends support options before it turns
                  into missed doses, missed appointments, or delayed labs.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section id="research" className="light">
          <div className="container">
            <h2 className="text-center">Clinical Research (Optional)</h2>
            <p
              className="text-center"
              style={{ marginBottom: 'var(--spacing-32)', color: 'var(--color-slate-500)' }}
            >
              Participation is always opt-in. Choosing not to participate does not impact your
              program access.
            </p>
            <div className="overview-grid">
              <div className="overview-card">
                <h3>Opt-in Participation</h3>
                <p>
                  If you choose, you can contribute to research studies designed to improve
                  aftercare and treatment support.
                </p>
              </div>
              <div className="overview-card">
                <h3>Consent &amp; De-identification</h3>
                <p>
                  Research workflows are built around consent, audit trails, and privacy-first
                  controls to protect sensitive health information.
                </p>
              </div>
              <div className="overview-card">
                <h3>Better Support Over Time</h3>
                <p>
                  Helps improve the quality of support for future patients by learning what works
                  best—without exposing private data.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section id="program" className="gray">
          <div className="container">
            <h2 className="text-center">What You Get</h2>
            <p
              className="text-center"
              style={{ marginBottom: 'var(--spacing-32)', color: 'var(--color-slate-500)' }}
            >
              IHEP is designed to reduce aftercare overload by consolidating guidance, resources,
              and follow-through into one place.
            </p>

            <div className="overview-grid">
              <div className="overview-card">
                <h3>Adherence Support Plan</h3>
                <p>
                  Clear next steps to help you stay on therapy—medication routines, appointment
                  follow-through, and barrier resolution aligned to your situation.
                </p>
              </div>

              <div className="overview-card">
                <h3>Care Coordination</h3>
                <p>
                  A dynamic calendar to organize appointments, labs, medications, and support tasks
                  with reminders and easy-to-follow routines.
                </p>
              </div>

              <div className="overview-card">
                <h3>Benefits &amp; Cost Support</h3>
                <p>
                  Tools that reduce financial barriers to care so you can keep appointments, labs,
                  and medications on track.
                </p>
              </div>

              <div className="overview-card">
                <h3>Resource Matching</h3>
                <p>
                  Curated programs, groups, and evidence-based education—matched to your situation
                  and updated as your needs change.
                </p>
              </div>

              <div className="overview-card">
                <h3>Community Support</h3>
                <p>
                  Access community pathways and support touchpoints that reduce isolation and
                  improve follow-through over time.
                </p>
              </div>

              <div className="overview-card">
                <h3>Privacy-First Design</h3>
                <p>
                  Built with security-first controls and HIPAA-aligned safeguards to protect
                  sensitive health information.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section id="documents" className="light">
          <div className="container">
            <h2 className="text-center">Patient Resources</h2>
            <p
              className="text-center"
              style={{ marginBottom: 'var(--spacing-32)', color: 'var(--color-slate-500)' }}
            >
              Explore program tools and support resources. Some features require an account.
            </p>

            <div className="doc-grid">
              {patientResources.map((doc) => (
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
              Need help navigating aftercare resources? Contact{' '}
              <a href="mailto:support@ihep.app">support@ihep.app</a>.
            </p>
          </div>
        </section>

        <section id="get-started" className="gray">
          <div className="container">
            <h2 className="text-center">Get Started</h2>
            <p
              className="text-center"
              style={{ marginBottom: 'var(--spacing-32)', color: 'var(--color-slate-500)' }}
            >
              Create an account to access your dashboard, calendar, and personalized recommendations.
              If you are not ready yet, subscribe for updates and program announcements.
            </p>

            <div className="overview-grid">
              <div className="overview-card">
                <h3>Create Your Account</h3>
                <p>
                  Join IHEP to unlock your 5-pillar twins, resource matching, and financial support
                  tools.
                </p>
                <p style={{ marginTop: varString('--spacing-12') }}>
                  <a className="cta-button" href="/register">
                    Create account
                  </a>
                </p>
              </div>

              <div className="overview-card">
                <h3>Sign In</h3>
                <p>
                  Already enrolled? Sign in to review your next steps, schedule, and progress.
                </p>
                <p style={{ marginTop: varString('--spacing-12') }}>
                  <a
                    className="secondary-button"
                    href="/login"
                    onClick={(e) => {
                      e.preventDefault();
                      openSignIn();
                    }}
                  >
                    Sign in
                  </a>
                </p>
              </div>

              <div className="overview-card">
                <h3>Need Help?</h3>
                <p>
                  If you are stuck, need support, or want to learn how the program works, email our
                  support team.
                </p>
                <p style={{ marginTop: varString('--spacing-12') }}>
                  <a className="secondary-button" href="mailto:support@ihep.app">
                    support@ihep.app
                  </a>
                </p>
              </div>
            </div>

            <div className="newsletter-form" style={{ marginTop: varString('--spacing-48') }}>
              <h3>Stay Connected</h3>
              <p>
                Subscribe to IHEP Progress Brief—weekly updates on aftercare support, new features,
                and program access.
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
              <h4>Program</h4>
              <ul>
                <li>
                  <a href="#digital-twins" onClick={(e) => handleAnchor(e, 'digital-twins')}>
                    5-Pillar Twins
                  </a>
                </li>
                <li>
                  <a href="#program" onClick={(e) => handleAnchor(e, 'program')}>
                    What You Get
                  </a>
                </li>
                <li>
                  <a href="#financial" onClick={(e) => handleAnchor(e, 'financial')}>
                    Financial Support
                  </a>
                </li>
                <li>
                  <a href="#get-started" onClick={(e) => handleAnchor(e, 'get-started')}>
                    Get Started
                  </a>
                </li>
              </ul>
            </div>

            <div className="footer-section">
              <h4>Resources</h4>
              <ul>
                <li>
                  <a href="#documents" onClick={(e) => handleAnchor(e, 'documents')}>
                    Patient Resources
                  </a>
                </li>
                <li>
                  <a href="/resources">Resource Hub</a>
                </li>
                <li>
                  <a href="/about">About IHEP</a>
                </li>
                <li>
                  <a href="/legal/trust">Privacy &amp; Trust</a>
                </li>
                <li>
                  <a href="/investors">Investors</a>
                </li>
              </ul>
            </div>

            <div className="footer-section">
              <h4>Support</h4>
              <ul>
                <li>
                  <a href="mailto:support@ihep.app">support@ihep.app</a>
                </li>
                <li>
                  <a href="/register">Create account</a>
                </li>
                <li>
                  <a href="mailto:press@ihep.app">Press inquiries</a>
                </li>
              </ul>
            </div>

            <div className="footer-section">
              <h4>Legal</h4>
              <ul>
                <li>
                  <a href="/legal/privacy">Privacy Policy</a>
                </li>
                <li>
                  <a href="/legal/terms">Terms of Service</a>
                </li>
                <li>
                  <a href="/legal/trust">Trust Center</a>
                </li>
                <li>
                  <a href="/legal/compliance">Security Framework</a>
                </li>
              </ul>
            </div>
          </div>

          <div className="footer-bottom">
            <p>© 2026 Integrated Health Empowerment Program (IHEP). All rights reserved.</p>
            <p style={{ marginTop: varString('--spacing-8') }}>
              Built to help patients navigate aftercare with clarity, support, and privacy-first
              design.
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
