import type { MediatorAdminResponse } from '@/types/mediators';

async function getAdminData(): Promise<MediatorAdminResponse> {
  const res = await fetch('/api/peer-mediators/admin', { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load peer mediator admin data');
  return res.json();
}

export default async function PeerMediatorsAdminPage() {
  const data = await getAdminData();

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm text-muted-foreground">Peer Mediators Program</p>
        <h1 className="text-3xl font-semibold">Admin Console</h1>
        <p className="text-sm text-muted-foreground">
          Manage roster, cohorts, and training sessions.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Roster</h2>
        <div className="space-y-2">
          {data.roster.map((member) => (
            <article key={member.id} className="rounded-lg border bg-card p-3 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold">{member.name}</h3>
                  <p className="text-xs text-muted-foreground">
                    {member.role} · Cohort {member.cohort}
                  </p>
                </div>
                <p className="text-xs text-muted-foreground">{member.progress}% complete</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Sessions</h2>
        <div className="space-y-2">
          {data.sessions.map((sess) => (
            <article key={sess.id} className="rounded-lg bg-muted/40 p-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold">{sess.topic}</h3>
                <span className="text-xs uppercase text-muted-foreground">{sess.status}</span>
              </div>
              <p className="text-xs text-muted-foreground">Facilitator: {sess.facilitator}</p>
              <p className="text-xs text-muted-foreground">
                Scheduled: {new Date(sess.scheduledFor).toLocaleString()} · Attendees: {sess.attendees}
              </p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

