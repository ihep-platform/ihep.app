import type { MediatorCurriculumResponse } from '@/types/mediators';

async function getCurriculum(): Promise<MediatorCurriculumResponse> {
  const res = await fetch('/api/peer-mediators/curriculum', { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load peer mediator curriculum');
  return res.json();
}

export default async function PeerMediatorsCurriculumPage() {
  const data = await getCurriculum();

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm text-muted-foreground">Peer Mediators Program</p>
        <h1 className="text-3xl font-semibold">Training Curriculum</h1>
        <p className="text-sm text-muted-foreground">
          Evidence-based modules, practice sessions, and competency tracking.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Modules</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {data.modules.map((mod) => (
            <article key={mod.id} className="rounded-lg border bg-card p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground uppercase">{mod.id}</p>
                  <h3 className="text-lg font-semibold">{mod.title}</h3>
                </div>
                <span className="text-xs uppercase text-muted-foreground">{mod.status}</span>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{mod.summary}</p>
              <p className="mt-1 text-xs text-muted-foreground">Duration: {mod.durationMinutes} min</p>
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

