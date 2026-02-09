import { getTwinSummary, jsonOk } from '../mock-data';

export async function GET() {
  return jsonOk(getTwinSummary());
}

