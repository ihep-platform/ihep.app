export default function AboutPage() {
  return (
    <main className="min-h-screen bg-stone-50">
      <div className="container mx-auto max-w-5xl px-4 py-16 space-y-10">
        <header className="space-y-3 text-center">
          <p className="text-sm uppercase tracking-wide text-teal-600">About IHEP</p>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900">Integrated Health Empowerment Program</h1>
          <p className="text-gray-600 max-w-3xl mx-auto">
            We combine digital twin modeling, coordinated care tools, and human support to simplify aftercare and improve outcomes.
          </p>
        </header>

        <section className="grid gap-6 md:grid-cols-2">
          {[
            {
              title: 'Digital Twin Ecosystem',
              desc: 'Health, financial, social, and care twins give a 360 degree view to personalize plans.',
            },
            {
              title: 'Dynamic Calendar',
              desc: 'One place for appointments, meds, programs, and reminders with sync to telehealth.',
            },
            {
              title: 'Security & Compliance',
              desc: 'HIPAA-aligned controls, encryption, and privacy by design to safeguard PHI.',
            },
            {
              title: 'Human + AI Support',
              desc: 'Clinicians, peer mentors, and AI-assisted insights working together for you.',
            },
          ].map((item) => (
            <div key={item.title} className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-teal-700 mb-2">{item.title}</h2>
              <p className="text-gray-600 text-sm">{item.desc}</p>
            </div>
          ))}
        </section>

        <section className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-teal-700 mb-2">Talk with us</h2>
          <p className="text-gray-600 mb-4">
            Have questions about care pathways, security, or partnerships? Reach out and we will respond quickly.
          </p>
          <div className="flex flex-wrap gap-3">
            <a className="px-5 py-2 rounded-full bg-gradient-to-r from-teal-600 to-teal-500 text-white text-sm font-medium" href="mailto:support@ihep.app">
              support@ihep.app
            </a>
            <a className="px-5 py-2 rounded-full border border-teal-600 text-teal-700 text-sm font-medium hover:bg-teal-50" href="/#contact">
              Contact form
            </a>
            <a className="px-5 py-2 rounded-full border border-teal-200 text-teal-600 text-sm font-medium hover:bg-teal-50" href="/">
              Back to home
            </a>
          </div>
        </section>
      </div>
    </main>
  );
}
