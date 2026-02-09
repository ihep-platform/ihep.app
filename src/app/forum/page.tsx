export default function ForumPage() {
  return (
    <main className="min-h-screen bg-stone-50">
      <div className="container mx-auto max-w-5xl px-4 py-16 space-y-10">
        <header className="space-y-3 text-center">
          <p className="text-sm uppercase tracking-wide text-teal-600">Forum</p>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900">Ask questions, share insights, stay informed</h1>
          <p className="text-gray-600 max-w-3xl mx-auto">
            A moderated forum for practical tips, lived experience, and expert-backed answers.
          </p>
        </header>

        <section className="grid gap-6 md:grid-cols-2">
          {[
            {
              title: 'Care Navigation',
              desc: 'Coverage questions, referrals, and coordinating with providers.',
            },
            {
              title: 'Medication & Adherence',
              desc: 'Managing side effects, routines, and reminders that work.',
            },
            {
              title: 'Lifestyle & Mind-Body',
              desc: 'Sleep, stress, nutrition, activity, and resilience practices.',
            },
            {
              title: 'Security & Privacy',
              desc: 'HIPAA-aligned guidance on protecting PHI in digital spaces.',
            },
          ].map((item) => (
            <div key={item.title} className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-teal-700 mb-2">{item.title}</h2>
              <p className="text-gray-600 text-sm">{item.desc}</p>
            </div>
          ))}
        </section>

        <section className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-teal-700 mb-2">Participate securely</h2>
          <p className="text-gray-600 mb-4">
            Sign in to post, follow threads, and receive responses while keeping your data protected.
          </p>
          <div className="flex flex-wrap gap-3">
            <a className="px-5 py-2 rounded-full bg-gradient-to-r from-teal-600 to-teal-500 text-white text-sm font-medium" href="/login">
              Log in
            </a>
            <a className="px-5 py-2 rounded-full border border-teal-600 text-teal-700 text-sm font-medium hover:bg-teal-50" href="/register">
              Create account
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
