import { NextResponse } from 'next/server';
import type { PersonalFinanceSnapshot } from '@/types/financial';

const snapshot: PersonalFinanceSnapshot = {
  netCashFlow: 320,
  monthlyIncome: 3400,
  monthlyExpenses: 3080,
  bufferMonths: 1.8,
  alerts: ['Utilities spend 12% above target', 'Subscription audit could free $35/mo']
};

export async function GET() {
  return NextResponse.json(snapshot);
}

