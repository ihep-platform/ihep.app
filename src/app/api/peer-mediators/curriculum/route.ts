import { NextResponse } from 'next/server';
import type { MediatorCurriculumResponse } from '@/types/mediators';

const response: MediatorCurriculumResponse = {
  modules: [
    {
      id: 'pm-101',
      title: 'Foundations of Peer Mediation',
      summary: 'Core principles, confidentiality, and trauma-informed communication.',
      durationMinutes: 45,
      status: 'in-progress'
    },
    {
      id: 'pm-201',
      title: 'De-escalation Techniques',
      summary: 'Safety, grounding, and stepwise de-escalation approaches.',
      durationMinutes: 40,
      status: 'not-started'
    },
    {
      id: 'pm-301',
      title: 'Care Navigation',
      summary: 'Connecting members to resources, follow-up practices, and documentation.',
      durationMinutes: 50,
      status: 'completed'
    }
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
      id: 'sess-0',
      topic: 'Orientation recording',
      facilitator: 'Program Ops',
      scheduledFor: new Date(Date.now() - 604800000).toISOString(),
      attendees: 34,
      status: 'completed'
    }
  ]
};

export async function GET() {
  return NextResponse.json(response);
}

