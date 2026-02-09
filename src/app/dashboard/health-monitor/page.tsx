type MonitorResponse = {
  overall: number
  trend: 'up' | 'stable' | 'down'
  vitals: { name: string; value: string; status: 'ok' | 'warning' | 'critical' }[]
  alerts: string[]
}

async function getMonitor(): Promise<MonitorResponse> {
  const res = await fetch('/api/health/monitor', { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to load health monitor')
  return res.json()
}

export default async function HealthMonitorPage() {
  const monitor = await getMonitor()

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm text-muted-foreground">Personal Health Monitor</p>
        <h1 className="text-3xl font-semibold">Live Vitals & Alerts</h1>
        <p className="text-sm text-muted-foreground">Streaming-ready interface with mock data.</p>
      </header>

      <section className="rounded-xl border bg-card p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Overall stability</p>
            <p className="text-3xl font-semibold">{monitor.overall}%</p>
          </div>
          <p className="text-xs text-muted-foreground uppercase">Trend: {monitor.trend}</p>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {monitor.vitals.map((vital) => (
            <div key={vital.name} className="rounded-lg border bg-background p-3">
              <p className="text-sm font-semibold">{vital.name}</p>
              <p className="text-lg font-bold">{vital.value}</p>
              <p className="text-xs text-muted-foreground uppercase">{vital.status}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-xl border bg-card p-4 shadow-sm">
        <h2 className="text-lg font-semibold">Alerts</h2>
        <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
          {monitor.alerts.map((alert) => (
            <li key={alert} className="rounded bg-muted/40 p-2">
              {alert}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

