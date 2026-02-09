import { NextResponse } from 'next/server';

type ResourceResult = {
  id: string;
  name: string;
  category: string;
  distanceMiles: number;
  address: string;
  rating: number;
};

const results: ResourceResult[] = [
  { id: 'res-1', name: 'Harbor Wellness Clinic', category: 'Clinic', distanceMiles: 1.2, address: '120 Bay St', rating: 4.7 },
  { id: 'res-2', name: 'Community Support Group', category: 'Peer Support', distanceMiles: 0.9, address: '45 Mission Ave', rating: 4.8 },
  { id: 'res-3', name: 'Downtown Lab Services', category: 'Diagnostics', distanceMiles: 2.5, address: '300 Market Rd', rating: 4.5 },
  { id: 'res-4', name: 'Wellness Pharmacy', category: 'Pharmacy', distanceMiles: 1.7, address: '88 Health Way', rating: 4.9 }
];

export async function GET() {
  return NextResponse.json({ results });
}

