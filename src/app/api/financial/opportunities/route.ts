import { NextResponse } from 'next/server';
import type { Opportunity } from '@/types/financial';

const opportunities: Opportunity[] = [
  { id: 'opp-1', title: 'Community Health Advocate', category: 'Part-time', payout: '$22/hr', matchScore: 92, status: 'new' },
  { id: 'opp-2', title: 'Remote Survey Panel', category: 'Remote', payout: '$150/week', matchScore: 81, status: 'in-progress' },
  { id: 'opp-3', title: 'Peer Facilitator', category: 'Peer work', payout: '$300/session', matchScore: 77, status: 'applied' }
];

export async function GET() {
  return NextResponse.json({ opportunities });
}

