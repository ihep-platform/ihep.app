import { NextResponse } from 'next/server';

export async function POST(request: Request) {
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

