import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/options';
import type { PersonalFinanceSnapshot } from '@/types/financial';

const snapshot: PersonalFinanceSnapshot = {
  netCashFlow: 320,
  monthlyIncome: 3400,
  monthlyExpenses: 3080,
  bufferMonths: 1.8,
  alerts: ['Utilities spend 12% above target', 'Subscription audit could free $35/mo']
};

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  return NextResponse.json(snapshot);
}

