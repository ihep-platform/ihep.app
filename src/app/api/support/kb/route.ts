import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/options';

type Article = {
  slug: string;
  title: string;
  summary: string;
  category: string;
};

const articles: Article[] = [
  { slug: 'account-security', title: 'Account Security', summary: 'MFA, sessions, and device safety.', category: 'Account' },
  { slug: 'appointments', title: 'Managing Appointments', summary: 'Scheduling, rescheduling, and reminders.', category: 'Calendar' },
  { slug: 'digital-twin', title: 'Digital Twin Overview', summary: 'How twins are used and protected.', category: 'Digital Twin' }
];

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  return NextResponse.json({ articles });
}

