'use client';

import React, { useMemo, useState } from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Filler,
} from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Filler,
);

type FinancialData = typeof financialData;

const financialData = {
  peer_navigator_income: [360000, 1320000, 2820000, 5080000, 7220000, 8900000, 10660000, 12830000, 15300000, 18070000],
  training_stipends: [95000, 162000, 241000, 333000, 432000, 520000, 610000, 708000, 815000, 668000],
  research_participation: [382150, 843000, 1320000, 1890000, 2560000, 3240000, 4080000, 5120000, 6400000, 6250000],
  gig_marketplace: [481000, 1060000, 2030000, 3220000, 4390000, 5900000, 7520000, 9600000, 12100000, 14120000],
  career_employment: [2107000, 3800000, 5600000, 7500000, 9800000, 12100000, 14800000, 17500000, 20200000, 22500000],
  career_training: [250000, 431000, 589000, 768000, 1030000, 1250000, 1520000, 1820000, 2180000, 2440000],
  direct_income_totals: [3675000, 7616000, 12599000, 18783000, 25503000, 31990000, 39170000, 47250000, 57010000, 64060000],
  indirect_benefits_totals: [3396000, 6072000, 15975000, 26430000, 44000000, 58930000, 73860000, 88790000, 103720000, 158650000],
  total_participant_impact: [7071000, 13688000, 28574000, 45213000, 69503000, 90920000, 113030000, 136040000, 160730000, 222710000],
  active_participants: [2500, 4500, 8500, 13000, 25000, 35000, 45000, 55000, 65000, 75000],
  impact_per_participant: [2829, 3042, 3361, 3478, 2780, 2598, 2512, 2473, 2472, 2970],
  operating_budget: [3054500, 5200000, 7850000, 11200000, 15500000, 19200000, 22800000, 26500000, 30200000, 34500000],
  cost_per_participant: [1222, 1156, 923, 862, 620, 549, 507, 482, 465, 460],
  funding_core: [1225000, 1900000, 3150000, 4800000, 6300000, 7920000, 9360000, 11000000, 12500000, 14000000],
  funding_workforce: [500000, 800000, 1500000, 2400000, 2500000, 3200000, 4000000, 4800000, 5500000, 4000000],
  funding_research: [300000, 550000, 800000, 1200000, 1500000, 1850000, 2300000, 2800000, 3200000, 3000000],
  funding_csr: [625000, 1000000, 1750000, 2600000, 3000000, 3600000, 4300000, 5000000, 5500000, 5000000],
  funding_foundation: [400000, 700000, 1000000, 1500000, 1500000, 1900000, 2300000, 2700000, 3000000, 3500000],
  funding_commercial: [0, 50000, 0, 500000, 1000000, 730000, 1640000, 1200000, 1500000, 6000000],
  funding_totals: [3050000, 5000000, 8200000, 12100000, 15800000, 19800000, 23900000, 27500000, 31200000, 36500000],
  roi_percent_trend: [131.6, 163.2, 264.1, 303.1, 348.4, 373.0, 395.9, 412.9, 431.8, 545.7],
  per_dollar_invested: [2.32, 2.63, 3.64, 4.03, 4.48, 4.73, 4.96, 5.13, 5.32, 6.46],
  sensitivity_conservative_benefit: [4949700, 9581600, 20001800, 31649100, 48651900, 63644000, 79121000, 95228000, 112511000, 155897000],
  sensitivity_conservative_roi: [62.1, 84.4, 155.3, 182.2, 214.0, 231.1, 247.1, 259.8, 272.6, 352.5],
  sensitivity_aggressive_benefit: [8131650, 15741200, 32860100, 52045000, 79978450, 104558000, 130034500, 156446000, 184840500, 256317000],
  sensitivity_aggressive_roi: [166.2, 203.2, 318.5, 364.3, 415.7, 444.5, 470.2, 489.6, 511.4, 643.2],
} as const;

const incomeStreams = [
  { name: 'Peer Navigator', data: financialData.peer_navigator_income, participants: [120, 220, 470, 800, 1200, 1400, 1700, 2000, 2400, 2800] },
  { name: 'Training Stipends', data: financialData.training_stipends, participants: [190, 270, 362, 480, 600, 720, 850, 1000, 1150, 920] },
  { name: 'Research Participation', data: financialData.research_participation, participants: [250, 450, 600, 800, 1000, 1200, 1500, 1800, 2200, 2000] },
  { name: 'Gig Tasks/Marketplace', data: financialData.gig_marketplace, participants: [370, 530, 870, 1300, 1700, 2200, 2600, 3200, 3900, 4400] },
  { name: 'Career Employment', data: financialData.career_employment, participants: [290, 450, 650, 850, 1100, 1350, 1600, 1900, 2200, 2400] },
  { name: 'Career Training', data: financialData.career_training, participants: [500, 862, 1178, 1536, 1800, 2000, 2400, 2800, 3200, 3500] },
];

const sections = [
  { id: 'overview', label: 'Overview' },
  { id: 'income', label: 'Income Streams' },
  { id: 'impact', label: 'Impact' },
  { id: 'costs', label: 'Operating Costs' },
  { id: 'funding', label: 'Funding Model' },
  { id: 'roi', label: 'ROI' },
  { id: 'sensitivity', label: 'Sensitivity' },
] as const;

function formatCurrency(value: number, compact?: boolean) {
  if (compact && value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (compact && value >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString('en-US')}`;
}

function formatNumber(value: number) {
  return value.toLocaleString('en-US');
}

export default function InvestorDashboardPage() {
  const [yearIndex, setYearIndex] = useState(0);
  const [activeSection, setActiveSection] = useState<(typeof sections)[number]['id']>('overview');

  const overviewMetrics = useMemo(
    () => [
      { label: 'Direct Income', value: formatCurrency(financialData.direct_income_totals[yearIndex], true) },
      { label: 'Indirect Benefits', value: formatCurrency(financialData.indirect_benefits_totals[yearIndex], true) },
      { label: 'Total Impact', value: formatCurrency(financialData.total_participant_impact[yearIndex], true) },
      { label: 'Active Participants', value: formatNumber(financialData.active_participants[yearIndex]) },
      { label: 'Cost per Participant', value: formatCurrency(financialData.cost_per_participant[yearIndex]) },
    ],
    [yearIndex],
  );

  const incomeTable = useMemo(() => {
    let totalParticipants = 0;
    const rows = incomeStreams.map((stream) => {
      const participants = stream.participants[yearIndex];
      totalParticipants += participants;
      return {
        name: stream.name,
        participants,
        amount: stream.data[yearIndex],
      };
    });
    const totalAmount = financialData.direct_income_totals[yearIndex];
    return { rows, totalParticipants, totalAmount };
  }, [yearIndex]);

  const roiCards = useMemo(
    () => [
      { label: 'Cost per Participant', value: formatCurrency(financialData.cost_per_participant[yearIndex]) },
      { label: 'Benefit per Participant', value: formatCurrency(financialData.impact_per_participant[yearIndex]) },
      { label: 'ROI Percentage', value: `${financialData.roi_percent_trend[yearIndex].toFixed(1)}%` },
      { label: 'Return per $1 Invested', value: `$${financialData.per_dollar_invested[yearIndex].toFixed(2)}` },
    ],
    [yearIndex],
  );

  const roiChartData = useMemo(
    () => ({
      labels: Array.from({ length: 10 }, (_, i) => `Year ${i + 1}`),
      datasets: [
        {
          label: 'ROI %',
          data: [...financialData.roi_percent_trend] as number[],
          borderColor: '#1FB8CD',
          backgroundColor: 'rgba(31,184,205,0.1)',
          fill: true,
          tension: 0.35,
        },
      ],
    }),
    [],
  );

  const fundingChartData = useMemo(
    () => ({
      labels: Array.from({ length: 10 }, (_, i) => `Year ${i + 1}`),
      datasets: [
        { label: 'IHEP Core', data: [...financialData.funding_core] as number[], backgroundColor: '#1FB8CD' },
        { label: 'Workforce Grants', data: [...financialData.funding_workforce] as number[], backgroundColor: '#FFC185' },
        { label: 'Research Grants', data: [...financialData.funding_research] as number[], backgroundColor: '#B4413C' },
        { label: 'CSR Partnerships', data: [...financialData.funding_csr] as number[], backgroundColor: '#ECEBD5' },
        { label: 'Foundation', data: [...financialData.funding_foundation] as number[], backgroundColor: '#5D878F' },
        { label: 'Commercial', data: [...financialData.funding_commercial] as number[], backgroundColor: '#DB4545' },
      ],
    }),
    [],
  );

  const costPieData = useMemo(
    () => ({
      labels: ['Personnel (48%)', 'Technology (16%)', 'Support Services (25%)', 'Partnerships (6%)', 'Administration (5%)'],
      datasets: [
        {
          data: [48, 16, 25, 6, 5],
          backgroundColor: ['#1FB8CD', '#FFC185', '#B4413C', '#ECEBD5', '#5D878F'],
        },
      ],
    }),
    [],
  );

  return (
    <div className="min-h-screen bg-[var(--color-background,white)] text-[var(--color-text,#111)]" style={{ background: 'var(--color-background)' }}>
      <div className="max-w-6xl mx-auto px-4 py-8">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900">IHEP Financial Dashboard - Investor Report</h1>
          <p className="text-slate-600 mt-2">
            Interactive 10-year financial outlook: income streams, impact, costs, funding, ROI, and sensitivity scenarios.
          </p>
          <div className="flex flex-col md:flex-row md:items-center gap-3 mt-4">
            <div className="flex items-center gap-2">
              <label htmlFor="yearSelect" className="font-medium text-slate-800">
                Select Year
              </label>
              <select
                id="yearSelect"
                value={yearIndex}
                onChange={(e) => setYearIndex(Number(e.target.value))}
                className="border rounded-md px-3 py-2 text-sm"
              >
                {Array.from({ length: 10 }, (_, i) => (
                  <option key={i} value={i}>
                    Year {i + 1}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-wrap gap-2">
              {sections.map((section) => (
                <button
                  key={section.id}
                  type="button"
                  onClick={() => setActiveSection(section.id)}
                  className={`px-3 py-2 text-sm rounded-md border ${
                    activeSection === section.id
                      ? 'border-teal-600 text-teal-700 bg-teal-50'
                      : 'border-slate-200 text-slate-600 bg-white'
                  }`}
                >
                  {section.label}
                </button>
              ))}
            </div>
          </div>
        </header>

        {/* Overview */}
        <section className={activeSection === 'overview' ? 'block' : 'hidden'}>
          <h2 className="text-2xl font-semibold mb-4">Overview Dashboard</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {overviewMetrics.map((metric) => (
              <div key={metric.label} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="text-xs uppercase text-slate-500 tracking-wide mb-2">{metric.label}</div>
                <div className="text-2xl font-bold text-slate-900">{metric.value}</div>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="text-lg font-semibold mb-2">Program Snapshot</h3>
            <ul className="text-sm text-slate-700 space-y-1">
              <li>Income streams across six categories with participant counts</li>
              <li>10-year view of direct/indirect impact and participant growth</li>
              <li>Cost efficiency and ROI trend lines</li>
            </ul>
          </div>
        </section>

        {/* Income Streams */}
        <section className={activeSection === 'income' ? 'block' : 'hidden'}>
          <h2 className="text-2xl font-semibold mb-4">Income Streams Breakdown</h2>
          <div className="overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-slate-700">Income Stream</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-700">Participants</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-700">Total</th>
                </tr>
              </thead>
              <tbody>
                {incomeTable.rows.map((row) => (
                  <tr key={row.name} className="border-t border-slate-100">
                    <td className="px-4 py-3 text-slate-800">{row.name}</td>
                    <td className="px-4 py-3 text-right text-slate-700">{formatNumber(row.participants)}</td>
                    <td className="px-4 py-3 text-right font-medium text-slate-800">{formatCurrency(row.amount)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-slate-50 border-t border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Total</th>
                  <th className="px-4 py-3 text-right font-semibold">{formatNumber(incomeTable.totalParticipants)}</th>
                  <th className="px-4 py-3 text-right font-semibold">{formatCurrency(incomeTable.totalAmount)}</th>
                </tr>
              </tfoot>
            </table>
          </div>
        </section>

        {/* Impact */}
        <section className={activeSection === 'impact' ? 'block' : 'hidden'}>
          <h2 className="text-2xl font-semibold mb-4">Consolidated Financial Impact Analysis</h2>
          <div className="overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold">Year</th>
                  <th className="text-right px-4 py-3 font-semibold">Direct Income</th>
                  <th className="text-right px-4 py-3 font-semibold">Indirect Benefits</th>
                  <th className="text-right px-4 py-3 font-semibold">Total Impact</th>
                  <th className="text-right px-4 py-3 font-semibold">Active Participants</th>
                  <th className="text-right px-4 py-3 font-semibold">Impact / Participant</th>
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: 10 }, (_, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-4 py-3">Year {i + 1}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(financialData.direct_income_totals[i])}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(financialData.indirect_benefits_totals[i])}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(financialData.total_participant_impact[i])}</td>
                    <td className="px-4 py-3 text-right">{formatNumber(financialData.active_participants[i])}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(financialData.impact_per_participant[i])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Costs */}
        <section className={activeSection === 'costs' ? 'block' : 'hidden'}>
          <h2 className="text-2xl font-semibold mb-4">Operating Costs Analysis</h2>
          <div className="overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold">Year</th>
                  <th className="text-right px-4 py-3 font-semibold">Operating Budget</th>
                  <th className="text-right px-4 py-3 font-semibold">Active Participants</th>
                  <th className="text-right px-4 py-3 font-semibold">Cost / Participant</th>
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: 10 }, (_, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-4 py-3">Year {i + 1}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(financialData.operating_budget[i])}</td>
                    <td className="px-4 py-3 text-right">{formatNumber(financialData.active_participants[i])}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(financialData.cost_per_participant[i])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 grid lg:grid-cols-2 gap-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-lg font-semibold mb-2">Cost Allocation</h3>
              <div className="h-72">
                <Pie
                  data={costPieData}
                  options={{
                    plugins: { legend: { position: 'bottom' } },
                    maintainAspectRatio: false,
                  }}
                />
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-lg font-semibold mb-2">Key Notes</h3>
              <ul className="text-sm text-slate-700 space-y-1">
                <li>Personnel + Support account for the largest cost share.</li>
                <li>Cost per participant declines steadily as scale increases.</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Funding */}
        <section className={activeSection === 'funding' ? 'block' : 'hidden'}>
          <h2 className="text-2xl font-semibold mb-4">Funding Model &amp; Revenue Sources</h2>

          <div className="overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold">Year</th>
                  <th className="text-right px-4 py-3 font-semibold">IHEP Core</th>
                  <th className="text-right px-4 py-3 font-semibold">Workforce Grants</th>
                  <th className="text-right px-4 py-3 font-semibold">Research Grants</th>
                  <th className="text-right px-4 py-3 font-semibold">CSR Partnerships</th>
                  <th className="text-right px-4 py-3 font-semibold">Foundation</th>
                  <th className="text-right px-4 py-3 font-semibold">Commercial</th>
                  <th className="text-right px-4 py-3 font-semibold">Total Funding</th>
                  <th className="text-right px-4 py-3 font-semibold">Surplus / (Gap)</th>
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: 10 }, (_, i) => {
                  const surplus = financialData.funding_totals[i] - financialData.operating_budget[i];
                  return (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="px-4 py-3">Year {i + 1}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(financialData.funding_core[i])}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(financialData.funding_workforce[i])}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(financialData.funding_research[i])}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(financialData.funding_csr[i])}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(financialData.funding_foundation[i])}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(financialData.funding_commercial[i])}</td>
                      <td className="px-4 py-3 text-right font-medium">{formatCurrency(financialData.funding_totals[i])}</td>
                      <td className={`px-4 py-3 text-right font-medium ${surplus >= 0 ? 'text-teal-700' : 'text-red-600'}`}>
                        {formatCurrency(surplus)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="text-lg font-semibold mb-2">Funding Composition (10-year)</h3>
            <div className="h-80">
              <Bar
                data={fundingChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    x: { stacked: true },
                    y: {
                      stacked: true,
                      ticks: {
                        callback: (value) => `$${Number(value) / 1_000_000}M`,
                      },
                    },
                  },
                  plugins: {
                    legend: { position: 'bottom' },
                  },
                }}
              />
            </div>
          </div>
        </section>

        {/* ROI */}
        <section className={activeSection === 'roi' ? 'block' : 'hidden'}>
          <h2 className="text-2xl font-semibold mb-4">Return on Investment Analysis</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {roiCards.map((card) => (
              <div key={card.label} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="text-xs uppercase text-slate-500 tracking-wide mb-2">{card.label}</div>
                <div className="text-xl font-semibold text-slate-900">{card.value}</div>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="text-lg font-semibold mb-2">ROI Trend Over 10 Years</h3>
            <div className="h-80">
              <Line
                data={roiChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: {
                    y: {
                      ticks: {
                        callback: (value) => `${value}%`,
                      },
                    },
                  },
                }}
              />
            </div>
          </div>
        </section>

        {/* Sensitivity */}
        <section className={activeSection === 'sensitivity' ? 'block' : 'hidden'}>
          <h2 className="text-2xl font-semibold mb-4">Sensitivity Analysis</h2>
          <p className="text-slate-600 mb-4 text-sm">Impact projections under different scenarios for the selected year.</p>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-lg font-semibold mb-3">Conservative Scenario (70%)</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600">Total Benefit</span>
                  <span className="font-semibold">{formatCurrency(financialData.sensitivity_conservative_benefit[yearIndex])}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">ROI Percentage</span>
                  <span className="font-semibold text-teal-700">{financialData.sensitivity_conservative_roi[yearIndex].toFixed(1)}%</span>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-lg font-semibold mb-3">Base Case (100%)</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600">Total Benefit</span>
                  <span className="font-semibold">{formatCurrency(financialData.total_participant_impact[yearIndex])}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">ROI Percentage</span>
                  <span className="font-semibold text-teal-700">{financialData.roi_percent_trend[yearIndex].toFixed(1)}%</span>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-lg font-semibold mb-3">Aggressive Scenario (115%)</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600">Total Benefit</span>
                  <span className="font-semibold">{formatCurrency(financialData.sensitivity_aggressive_benefit[yearIndex])}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">ROI Percentage</span>
                  <span className="font-semibold text-teal-700">{financialData.sensitivity_aggressive_roi[yearIndex].toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
