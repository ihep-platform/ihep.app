import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/options';

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const ticketId = `ticket-${Date.now()}`;
  return NextResponse.json(
    {
      ticketId,
      status: 'queued',
      received: {
        subject: body.subject ?? 'Support request',
        message: body.message ?? '',
        category: body.category ?? 'general'
      }
    },
    { status: 201 }
  );
}

