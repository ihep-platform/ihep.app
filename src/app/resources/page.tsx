export default function ResourcesPage() {
  return (
    <main className="min-h-screen bg-stone-50">
      <div className="container mx-auto max-w-5xl px-4 py-16 space-y-10">
        <header className="space-y-3 text-center">
          <p className="text-sm uppercase tracking-wide text-teal-600">Resource Hub</p>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900">Curated support, guides, and programs</h1>
          <p className="text-gray-600 max-w-3xl mx-auto">
            Explore education, support groups, community programs, and research updates in one place.
          </p>
        </header>

        <section className="grid gap-6 md:grid-cols-2">
          {[
            {
              title: 'Guides & Playbooks',
              desc: 'Condition-specific checklists, self-care plans, and PDF handouts you can share with your care team.',
            },
            {
              title: 'Support Groups',
              desc: 'Find moderated groups, peer mentors, and local/community meetings that match your needs.',
            },
            {
              title: 'Programs & Benefits',
              desc: 'Discover financial assistance, housing, transportation, and nutrition support programs.',
            },
            {
              title: 'Research & Updates',
              desc: 'Stay current with evidence-based articles, safety advisories, and clinical best practices.',
            },
          ].map((item) => (
            <div key={item.title} className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-teal-700 mb-2">{item.title}</h2>
              <p className="text-gray-600 text-sm">{item.desc}</p>
            </div>
          ))}
        </section>

        <section className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-teal-700 mb-2">Ready to personalize?</h2>
          <p className="text-gray-600 mb-4">
            Sign in to save favorites, receive recommendations, and sync with your care plan.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              className="px-5 py-2 rounded-full bg-gradient-to-r from-teal-600 to-teal-500 text-white text-sm font-medium"
              href="/login"
            >
              Log in
            </a>
            <a
              className="px-5 py-2 rounded-full border border-teal-600 text-teal-700 text-sm font-medium hover:bg-teal-50"
              href="/register"
            >
              Create account
            </a>
            <a
              className="px-5 py-2 rounded-full border border-teal-200 text-teal-600 text-sm font-medium hover:bg-teal-50"
              href="/"
            >
              Back to home
            </a>
          </div>
        </section>
      </div>
    </main>
  );
}
