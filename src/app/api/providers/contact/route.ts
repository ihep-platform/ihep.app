import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/options';

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const messageId = `msg-${Date.now()}`;
  return NextResponse.json(
    {
      messageId,
      received: {
        providerId: body.providerId ?? 'unknown',
        subject: body.subject ?? 'No subject',
        message: body.message ?? '',
        from: body.from ?? 'member'
      },
      status: 'queued'
    },
    { status: 201 }
  );
}

