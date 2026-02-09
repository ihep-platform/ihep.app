import { NextResponse } from 'next/server';
import type { TwinPillar, TwinSnapshot, TwinSummary, TwinStatus, TwinTrend } from '@/types/twins';

const baseMetrics: Record<TwinPillar, { metrics: TwinSnapshot['metrics']; insights: TwinSnapshot['insights'] }> = {
  clinical: {
    metrics: [
      { name: 'Adherence', value: 92, unit: '%', status: 'ok' },
      { name: 'Vitals stability', value: 88, unit: '%', status: 'ok' },
      { name: 'Labs up-to-date', value: 75, unit: '%', status: 'warning' }
    ],
    insights: [
      {
        title: 'Medication adherence strong',
        summary: 'Patient maintains >90% adherence over last 30 days.',
        recommendation: 'Continue current adherence support cadence.',
        severity: 'low'
      },
      {
        title: 'Upcoming labs',
        summary: 'CMP due in 10 days.',
        recommendation: 'Schedule lab draw and notify patient.',
        severity: 'medium'
      }
    ]
  },
  behavioral: {
    metrics: [
      { name: 'Sleep quality', value: 7.4, unit: 'hrs', status: 'ok' },
      { name: 'Activity', value: 5400, unit: 'steps', status: 'warning' },
      { name: 'Mood check-ins', value: 4, unit: '/week', status: 'ok' }
    ],
    insights: [
      {
        title: 'Activity trending low',
        summary: 'Weekly steps fell 12% vs prior week.',
        recommendation: 'Nudge with achievable activity goals.',
        severity: 'medium'
      }
    ]
  },
  social: {
    metrics: [
      { name: 'Support touches', value: 3, unit: '/week', status: 'ok' },
      { name: 'Group attendance', value: 1, unit: '/week', status: 'warning' },
      { name: 'Housing stability', value: 95, unit: '%', status: 'ok' }
    ],
    insights: [
      {
        title: 'Peer support gap',
        summary: 'Attendance below target for past 2 weeks.',
        recommendation: 'Offer virtual peer mediator session.',
        severity: 'medium'
      }
    ]
  },
  financial: {
    metrics: [
      { name: 'Benefits utilization', value: 68, unit: '%', status: 'warning' },
      { name: 'Cash flow buffer', value: 1.8, unit: 'months', status: 'ok' },
      { name: 'Opportunities matched', value: 2, unit: 'active', status: 'ok' }
    ],
    insights: [
      {
        title: 'Benefits underutilized',
        summary: 'Eligible programs not yet claimed.',
        recommendation: 'Surface BenefitsOptimizer checklist.',
        severity: 'medium'
      }
    ]
  },
  personal: {
    metrics: [
      { name: 'Goal completion', value: 76, unit: '%', status: 'ok' },
      { name: 'Engagement', value: 82, unit: '%', status: 'ok' },
      { name: 'Sentiment', value: 64, unit: '/100', status: 'warning' }
    ],
    insights: [
      {
        title: 'Sentiment softening',
        summary: 'Recent interactions show lower positive sentiment.',
        recommendation: 'Offer check-in and adjust care plan tone.',
        severity: 'medium'
      }
    ]
  }
};

const trends: Record<TwinPillar, TwinTrend> = {
  clinical: 'stable',
  behavioral: 'down',
  social: 'stable',
  financial: 'up',
  personal: 'stable'
};

const scores: Record<TwinPillar, number> = {
  clinical: 84,
  behavioral: 73,
  social: 78,
  financial: 81,
  personal: 77
};

function buildSnapshot(pillar: TwinPillar): TwinSnapshot {
  const { metrics, insights } = baseMetrics[pillar];
  return {
    pillar,
    score: scores[pillar],
    trend: trends[pillar],
    metrics,
    insights,
    lastUpdated: new Date().toISOString()
  };
}

export function getTwinSnapshot(pillar: TwinPillar): TwinSnapshot {
  return buildSnapshot(pillar);
}

export function getTwinSummary(): TwinSummary {
  return {
    snapshots: (Object.keys(baseMetrics) as TwinPillar[]).map(buildSnapshot)
  };
}

export function jsonOk<T>(body: T): NextResponse<T> {
  return NextResponse.json(body);
}

