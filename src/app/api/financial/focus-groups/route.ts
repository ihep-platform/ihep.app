import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/options';
import type { FocusGroup } from '@/types/financial';

const focusGroups: FocusGroup[] = [
  {
    id: 'fg-1',
    title: 'Income Uplift Case Studies',
    theme: 'Earning pathways',
    scheduledFor: new Date(Date.now() + 3 * 86400000).toISOString(),
    capacity: 20,
    enrolled: 12
  },
  {
    id: 'fg-2',
    title: 'Benefits Navigation Lab',
    theme: 'Benefits optimization',
    scheduledFor: new Date(Date.now() + 5 * 86400000).toISOString(),
    capacity: 18,
    enrolled: 9
  }
];

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  return NextResponse.json({ focusGroups });
}

