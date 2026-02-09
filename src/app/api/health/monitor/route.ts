import { NextResponse } from 'next/server';

type VitalMetric = {
  name: string;
  value: string;
  status: 'ok' | 'warning' | 'critical';
};

type MonitorResponse = {
  overall: number;
  trend: 'up' | 'stable' | 'down';
  vitals: VitalMetric[];
  alerts: string[];
};

const payload: MonitorResponse = {
  overall: 82,
  trend: 'stable',
  vitals: [
    { name: 'Heart rate', value: '72 bpm', status: 'ok' },
    { name: 'BP', value: '122/78', status: 'ok' },
    { name: 'SpO₂', value: '98%', status: 'ok' },
    { name: 'Temp', value: '98.4°F', status: 'ok' },
    { name: 'HRV', value: '56 ms', status: 'warning' }
  ],
  alerts: [
    'HRV slightly low vs baseline; consider recovery protocol.',
    'Next vitals check scheduled in 3 days.'
  ]
};

export async function GET() {
  return NextResponse.json(payload);
}

