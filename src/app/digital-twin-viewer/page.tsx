import type { TwinSummary } from '@/types/twins';

async function getSummary(): Promise<TwinSummary> {
  const res = await fetch('/api/twins/summary', { cache: 'no-store' });
  if (!res.ok) {
    throw new Error('Failed to load twin summary');
  }
  return res.json();
}

export default async function DigitalTwinViewerPage() {
  const summary = await getSummary();

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm text-muted-foreground">Digital Twin Ecosystem</p>
        <h1 className="text-3xl font-semibold">5-Pillar Twin System</h1>
        <p className="text-sm text-muted-foreground">
          Clinical · Behavioral · Social · Financial · Personal
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {summary.snapshots.map((snapshot) => (
          <article
            key={snapshot.pillar}
            className="rounded-xl border bg-card p-4 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold capitalize">{snapshot.pillar} twin</h2>
                <p className="text-xs text-muted-foreground">
                  Score {snapshot.score} · Trend {snapshot.trend}
                </p>
              </div>
              <div className="text-2xl font-semibold">{snapshot.score}</div>
            </div>

            <div className="mt-3 space-y-2">
              {snapshot.metrics.map((metric) => (
                <div
                  key={metric.name}
                  className="flex items-center justify-between rounded-lg bg-muted/60 px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-medium">{metric.name}</p>
                    {metric.unit ? (
                      <p className="text-xs text-muted-foreground">
                        {metric.value} {metric.unit}
                      </p>
                    ) : (
                      <p className="text-xs text-muted-foreground">{metric.value}</p>
                    )}
                  </div>
                  <span className="text-xs uppercase text-muted-foreground">{metric.status}</span>
                </div>
              ))}
            </div>

            <div className="mt-3 space-y-2">
              {snapshot.insights.map((insight) => (
                <div key={insight.title} className="rounded-lg bg-background p-3 ring-1 ring-border">
                  <p className="text-sm font-semibold">{insight.title}</p>
                  <p className="text-xs text-muted-foreground">{insight.summary}</p>
                  <p className="text-xs text-primary">Next: {insight.recommendation}</p>
                </div>
              ))}
            </div>

            <p className="mt-2 text-xs text-muted-foreground">
              Updated {new Date(snapshot.lastUpdated).toLocaleString()}
            </p>
          </article>
        ))}
      </div>
    </div>
  );
}

