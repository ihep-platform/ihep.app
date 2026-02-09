import type { TwinSnapshot } from '@/types/twins';

async function getSnapshot(): Promise<TwinSnapshot> {
  const res = await fetch('/api/twins/behavioral', { cache: 'no-store' });
  if (!res.ok) {
    throw new Error('Failed to load behavioral twin data');
  }
  return res.json();
}

export default async function BehavioralTwinPage() {
  const snapshot = await getSnapshot();

  return (
    <section className="space-y-4">
      <header>
        <p className="text-sm text-muted-foreground">Behavioral twin</p>
        <h1 className="text-2xl font-semibold">Behavioral Twin</h1>
        <p className="text-xs text-muted-foreground">Score {snapshot.score} · Trend {snapshot.trend}</p>
      </header>

      <div className="grid gap-3 md:grid-cols-2">
        {snapshot.metrics.map((metric) => (
          <div key={metric.name} className="rounded-lg border bg-card p-3 shadow-sm">
            <p className="text-sm font-semibold">{metric.name}</p>
            <p className="text-lg font-bold">
              {metric.value}
              {metric.unit ? ` ${metric.unit}` : ''}
            </p>
            <p className="text-xs text-muted-foreground uppercase">{metric.status}</p>
          </div>
        ))}
      </div>

      <div className="space-y-3">
        {snapshot.insights.map((insight) => (
          <div key={insight.title} className="rounded-lg bg-muted/40 p-3">
            <p className="text-sm font-semibold">{insight.title}</p>
            <p className="text-xs text-muted-foreground">{insight.summary}</p>
            <p className="text-xs text-primary">Next: {insight.recommendation}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

