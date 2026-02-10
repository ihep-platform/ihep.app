import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/options';
import type { Benefit } from '@/types/financial';

const benefits: Benefit[] = [
  { id: 'ben-1', name: 'SNAP', type: 'Food', value: '$250/mo', eligibility: 'Gross income <130% FPL', status: 'in-progress' },
  { id: 'ben-2', name: 'LIHEAP', type: 'Utilities', value: '$400 one-time', eligibility: 'Income + energy burden', status: 'not-started' },
  { id: 'ben-3', name: 'Medicaid Redetermination', type: 'Health', value: 'Coverage continuity', eligibility: 'State guidelines', status: 'submitted' }
];

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  return NextResponse.json({ benefits });
}

