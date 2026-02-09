import { NextResponse } from 'next/server';
import type { MediatorAdminResponse } from '@/types/mediators';

const response: MediatorAdminResponse = {
  roster: [
    { id: 'user-1', name: 'Amira Blake', role: 'peer-mediator', cohort: 'Spring 2026', progress: 76 },
    { id: 'user-2', name: 'Drew Patel', role: 'peer-mediator', cohort: 'Spring 2026', progress: 42 },
    { id: 'user-3', name: 'Jordan Kim', role: 'admin', cohort: 'Program Ops', progress: 100 }
  ],
  sessions: [
    {
      id: 'sess-1',
      topic: 'Role-play: Conflict triage',
      facilitator: 'Dr. Lena Ortiz',
      scheduledFor: new Date(Date.now() + 86400000).toISOString(),
      attendees: 12,
      status: 'scheduled'
    },
    {
      id: 'sess-2',
      topic: 'Documentation & audit',
      facilitator: 'Quality Team',
      scheduledFor: new Date(Date.now() + 172800000).toISOString(),
      attendees: 9,
      status: 'scheduled'
    }
  ]
};

export async function GET() {
  return NextResponse.json(response);
}

