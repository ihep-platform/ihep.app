export type TwinPillar = 'clinical' | 'behavioral' | 'social' | 'financial' | 'personal';

export type TwinTrend = 'up' | 'stable' | 'down';

export type TwinStatus = 'ok' | 'warning' | 'critical';

export interface TwinMetric {
  name: string;
  value: number;
  unit?: string;
  status: TwinStatus;
}

export interface TwinInsight {
  title: string;
  summary: string;
  recommendation: string;
  severity: 'low' | 'medium' | 'high';
}

export interface TwinSnapshot {
  pillar: TwinPillar;
  score: number; // 0-100 composite score
  trend: TwinTrend;
  metrics: TwinMetric[];
  insights: TwinInsight[];
  lastUpdated: string;
}

export interface TwinSummary {
  snapshots: TwinSnapshot[];
}

