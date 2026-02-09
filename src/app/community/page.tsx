export default function CommunityPage() {
  return (
    <main className="min-h-screen bg-stone-50">
      <div className="container mx-auto max-w-5xl px-4 py-16 space-y-10">
        <header className="space-y-3 text-center">
          <p className="text-sm uppercase tracking-wide text-teal-600">Community</p>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900">Connect with peers and care allies</h1>
          <p className="text-gray-600 max-w-3xl mx-auto">
            Build supportive connections with moderated groups, peer mentors, and shared journeys.
          </p>
        </header>

        <section className="grid gap-6 md:grid-cols-2">
          {[
            {
              title: 'Peer Mentors',
              desc: 'Match with trained peers for encouragement and accountability.',
            },
            {
              title: 'Topic Channels',
              desc: 'Join channels for medication support, stress, caregiving, and lifestyle change.',
            },
            {
              title: 'Moderated Spaces',
              desc: 'Safe, respectful rooms with guidelines to protect privacy and wellbeing.',
            },
            {
              title: 'Community Challenges',
              desc: 'Participate in wellness streaks, activity goals, and education challenges.',
            },
          ].map((item) => (
            <div key={item.title} className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-teal-700 mb-2">{item.title}</h2>
              <p className="text-gray-600 text-sm">{item.desc}</p>
            </div>
          ))}
        </section>

        <section className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-teal-700 mb-2">Join the community</h2>
          <p className="text-gray-600 mb-4">
            Sign in to start conversations, follow topics, and receive moderated support.
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
