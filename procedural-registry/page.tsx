import { getProcedures, getProcedureStats } from '@/lib/data';
import Link from 'next/link';
import { Scale, Plus, ArrowRight, Shield, AlertTriangle, Info } from 'lucide-react';
import type { EnforcementLevel, ProcedureCategory } from '@/lib/types';

export const dynamic = 'force-dynamic';

function EnforcementBadge({ level }: { level: EnforcementLevel }) {
  const styles: Record<EnforcementLevel, string> = {
    advisory: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    soft: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    hard: 'bg-red-500/20 text-red-400 border-red-500/30',
  };
  const icons: Record<EnforcementLevel, React.ReactNode> = {
    advisory: <Info className="w-3 h-3" />,
    soft: <AlertTriangle className="w-3 h-3" />,
    hard: <Shield className="w-3 h-3" />,
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${styles[level]}`}>
      {icons[level]}
      {level.toUpperCase()}
    </span>
  );
}

function CategoryBadge({ category }: { category: ProcedureCategory }) {
  const colors: Record<ProcedureCategory, string> = {
    agent: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    service: 'bg-green-500/20 text-green-400 border-green-500/30',
    workflow: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    deployment: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    api: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${colors[category]}`}>
      {category.toUpperCase()}
    </span>
  );
}

export default async function ProceduresPage() {
  const [procedures, stats] = await Promise.all([
    getProcedures(),
    getProcedureStats(),
  ]);

  // Group by category
  const grouped = procedures.reduce((acc, proc) => {
    if (!acc[proc.category]) acc[proc.category] = [];
    acc[proc.category].push(proc);
    return acc;
  }, {} as Record<ProcedureCategory, typeof procedures>);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Scale className="w-8 h-8 text-blue-500" />
          <div>
            <h1 className="text-2xl font-bold">Procedural Registry</h1>
            <p className="text-gray-400">Operating guidelines with tiered enforcement</p>
          </div>
        </div>
        <Link
          href="/procedures/new"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Procedure
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400">Active Procedures</p>
          <p className="text-2xl font-bold">{stats.active_procedures}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400">Violations (24h)</p>
          <p className="text-2xl font-bold text-yellow-400">{stats.violations_24h}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400">Blocked (24h)</p>
          <p className="text-2xl font-bold text-red-400">{stats.blocked_24h}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400">Executions (24h)</p>
          <p className="text-2xl font-bold text-green-400">{stats.executions_24h}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400">Total</p>
          <p className="text-2xl font-bold text-gray-400">{stats.total_procedures}</p>
        </div>
      </div>

      {/* Enforcement Level Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {stats.by_enforcement.map((e) => (
          <div key={e.enforcement_level} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <EnforcementBadge level={e.enforcement_level} />
              <span className="text-xl font-bold">{e.count}</span>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {e.enforcement_level === 'advisory' && 'Logged only, no action taken'}
              {e.enforcement_level === 'soft' && 'Warning issued, action proceeds'}
              {e.enforcement_level === 'hard' && 'Action blocked if violated'}
            </p>
          </div>
        ))}
      </div>

      {/* Quick Links */}
      <div className="flex gap-4 mb-8">
        <Link
          href="/procedures/violations"
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
        >
          <AlertTriangle className="w-4 h-4 text-yellow-500" />
          View Violations Log
        </Link>
      </div>

      {/* Procedures by Category */}
      {Object.entries(grouped).map(([category, procs]) => (
        <div key={category} className="bg-gray-900 border border-gray-800 rounded-lg mb-6">
          <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CategoryBadge category={category as ProcedureCategory} />
              <h2 className="text-lg font-semibold capitalize">{category} Procedures</h2>
            </div>
            <span className="text-sm text-gray-500">{procs.length} procedure{procs.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-800">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Enforcement</th>
                  <th className="px-4 py-3">Rules</th>
                  <th className="px-4 py-3">Assignments</th>
                  <th className="px-4 py-3">Updated</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {procs.map((proc) => (
                  <tr key={proc.id} className="border-b border-gray-800/50 hover:bg-gray-800/50">
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-white">{proc.name}</p>
                        {proc.description && (
                          <p className="text-gray-500 text-xs mt-0.5 truncate max-w-md">{proc.description}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <EnforcementBadge level={proc.enforcement_level} />
                    </td>
                    <td className="px-4 py-3 text-gray-400">{proc.rule_count || 0}</td>
                    <td className="px-4 py-3 text-gray-400">{proc.assignment_count || 0}</td>
                    <td className="px-4 py-3 text-gray-400 whitespace-nowrap">
                      {new Date(proc.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/procedures/${proc.id}`} className="text-blue-400 hover:text-blue-300">
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {procedures.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center text-gray-500">
          <Scale className="w-12 h-12 mx-auto mb-3 text-blue-500/50" />
          <p>No procedures defined yet. Create your first procedure to get started.</p>
        </div>
      )}
    </div>
  );
}
