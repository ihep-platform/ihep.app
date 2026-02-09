import { NextResponse } from 'next/server';

export async function POST(request: Request) {
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

