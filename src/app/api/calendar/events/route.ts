import { NextResponse } from 'next/server';

interface CalendarEvent {
  id: string;
  title: string;
  provider: string;
  specialty: string;
  datetime: string;
  durationMinutes: number;
  location: string;
  type: 'In-Person' | 'Telehealth';
}

const seedEvents: CalendarEvent[] = [
  {
    id: '1',
    title: 'Follow-up Consultation',
    provider: 'Dr. Sarah Johnson',
    specialty: 'Internal Medicine',
    datetime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    durationMinutes: 30,
    location: 'Main Clinic, Room 203',
    type: 'In-Person'
  },
  {
    id: '2',
    title: 'Lab Work',
    provider: 'Dr. Michael Chen',
    specialty: 'Laboratory',
    datetime: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    durationMinutes: 15,
    location: 'Lab Building, 2nd Floor',
    type: 'In-Person'
  },
  {
    id: '3',
    title: 'Therapy Session',
    provider: 'Lisa Martinez, LCSW',
    specialty: 'Mental Health',
    datetime: new Date(Date.now() + 9 * 24 * 60 * 60 * 1000).toISOString(),
    durationMinutes: 60,
    location: 'Virtual',
    type: 'Telehealth'
  }
];

export async function GET() {
  return NextResponse.json({ events: seedEvents });
}

export async function POST(request: Request) {
  const body = await request.json();
  const newEvent: CalendarEvent = {
    id: `evt-${Date.now()}`,
    title: body.title ?? 'New appointment',
    provider: body.provider ?? 'TBD',
    specialty: body.specialty ?? 'General',
    datetime: body.datetime ?? new Date().toISOString(),
    durationMinutes: Number(body.durationMinutes ?? 30),
    location: body.location ?? 'Virtual',
    type: body.type === 'In-Person' ? 'In-Person' : 'Telehealth'
  };
  return NextResponse.json({ event: newEvent }, { status: 201 });
}

