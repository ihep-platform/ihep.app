import type {
  Benefit,
  FocusGroup,
  Opportunity,
  PersonalFinanceSnapshot
} from '@/types/financial';

async function getOpportunities(): Promise<Opportunity[]> {
  const res = await fetch('/api/financial/opportunities', { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load opportunities');
  const data = await res.json();
  return data.opportunities;
}

async function getBenefits(): Promise<Benefit[]> {
  const res = await fetch('/api/financial/benefits', { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load benefits');
  const data = await res.json();
  return data.benefits;
}

async function getPersonalFinance(): Promise<PersonalFinanceSnapshot> {
  const res = await fetch('/api/financial/personal-finance', { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load personal finance snapshot');
  return res.json();
}

async function getFocusGroups(): Promise<FocusGroup[]> {
  const res = await fetch('/api/financial/focus-groups', { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load focus groups');
  const data = await res.json();
  return data.focusGroups;
}

export default async function FinancialTwinPage() {
  const [opportunities, benefits, personalFinance, focusGroups] = await Promise.all([
    getOpportunities(),
    getBenefits(),
    getPersonalFinance(),
    getFocusGroups()
  ]);

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm text-muted-foreground">Financial Twin</p>
        <h1 className="text-3xl font-semibold">Financial Empowerment System</h1>
        <p className="text-sm text-muted-foreground">
          OpportunityMatcher · BenefitsOptimizer · PersonalFinanceManager · FocusGroups & CaseStudies
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">OpportunityMatcher</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {opportunities.map((opp) => (
            <article key={opp.id} className="rounded-lg border bg-card p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{opp.title}</h3>
                <span className="text-xs uppercase text-muted-foreground">{opp.status}</span>
              </div>
              <p className="text-sm text-muted-foreground">{opp.category} · {opp.payout}</p>
              <p className="text-xs text-muted-foreground">Match score: {opp.matchScore}%</p>
            </article>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">BenefitsOptimizer</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {benefits.map((benefit) => (
            <article key={benefit.id} className="rounded-lg border bg-card p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{benefit.name}</h3>
                <span className="text-xs uppercase text-muted-foreground">{benefit.status}</span>
              </div>
              <p className="text-sm text-muted-foreground">{benefit.type} · {benefit.value}</p>
              <p className="text-xs text-muted-foreground">Eligibility: {benefit.eligibility}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">PersonalFinanceManager</h2>
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <div className="flex flex-wrap gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Net cash flow</p>
              <p className="text-lg font-semibold">${personalFinance.netCashFlow}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Monthly income</p>
              <p className="text-lg font-semibold">${personalFinance.monthlyIncome}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Monthly expenses</p>
              <p className="text-lg font-semibold">${personalFinance.monthlyExpenses}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Buffer</p>
              <p className="text-lg font-semibold">{personalFinance.bufferMonths} months</p>
            </div>
          </div>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
            {personalFinance.alerts.map((alert) => (
              <li key={alert}>{alert}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">FocusGroups & CaseStudies</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {focusGroups.map((fg) => (
            <article key={fg.id} className="rounded-lg border bg-card p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{fg.title}</h3>
                <p className="text-xs text-muted-foreground">{fg.theme}</p>
              </div>
              <p className="text-xs text-muted-foreground">
                Scheduled: {new Date(fg.scheduledFor).toLocaleString()}
              </p>
              <p className="text-xs text-muted-foreground">
                {fg.enrolled}/{fg.capacity} enrolled
              </p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

