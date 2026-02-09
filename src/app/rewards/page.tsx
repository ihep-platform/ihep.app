export default function RewardsPage() {
  return (
    <main className="min-h-screen bg-stone-50">
      <div className="container mx-auto max-w-5xl px-4 py-16 space-y-10">
        <header className="space-y-3 text-center">
          <p className="text-sm uppercase tracking-wide text-teal-600">Health Rewards</p>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900">Earn rewards for healthy actions</h1>
          <p className="text-gray-600 max-w-3xl mx-auto">
            Celebrate adherence, education milestones, and community participation with redeemable rewards.
          </p>
        </header>

        <section className="grid gap-6 md:grid-cols-2">
          {[
            {
              title: 'Adherence Streaks',
              desc: 'Track medication and appointment streaks to earn badges.',
            },
            {
              title: 'Education Milestones',
              desc: 'Complete learning modules and skill workshops to unlock points.',
            },
            {
              title: 'Community Participation',
              desc: 'Join discussions, support peers, and attend live sessions.',
            },
            {
              title: 'Redeem & Share',
              desc: 'Redeem rewards for wellness perks and share achievements with your care team.',
            },
          ].map((item) => (
            <div key={item.title} className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-teal-700 mb-2">{item.title}</h2>
              <p className="text-gray-600 text-sm">{item.desc}</p>
            </div>
          ))}
        </section>

        <section className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-teal-700 mb-2">Activate your rewards</h2>
          <p className="text-gray-600 mb-4">
            Sign in to start collecting points and syncing achievements with your Dynamic Calendar and providers.
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
