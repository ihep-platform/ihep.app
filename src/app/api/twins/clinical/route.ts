import { jsonOk, getTwinSnapshot } from '../mock-data';

export async function GET() {
  return jsonOk(getTwinSnapshot('clinical'));
}

