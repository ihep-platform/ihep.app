import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/options';
import { getTwinSummary, jsonOk } from '../mock-data';

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  return jsonOk(getTwinSummary());
}

