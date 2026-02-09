import { NextResponse } from 'next/server';
import type { Provider } from '@/types/provider';

const providers: Provider[] = [
  {
    id: '1',
    userId: 'u1',
    firstName: 'Sarah',
    lastName: 'Johnson',
    title: 'MD',
    specialty: 'Internal Medicine',
    licenseNumber: 'IM-12345',
    email: 'sarah.johnson@example.com',
    phone: '(555) 123-4001',
    bio: 'Specializing in HIV care and chronic disease management with a holistic approach.',
    yearsOfExperience: 15,
    languages: ['English', 'Spanish'],
    acceptingNewPatients: true,
    rating: 4.9,
    reviewCount: 127,
    location: {
      facilityName: 'Main Clinic',
      address: '100 Health Way',
      city: 'San Francisco',
      state: 'CA',
      zipCode: '94107'
    },
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    id: '2',
    userId: 'u2',
    firstName: 'Michael',
    lastName: 'Chen',
    title: 'MD, PhD',
    specialty: 'Infectious Disease',
    licenseNumber: 'ID-98123',
    email: 'michael.chen@example.com',
    phone: '(555) 123-4002',
    bio: 'Expert in HIV treatment and research with focus on latest therapeutic approaches.',
    yearsOfExperience: 12,
    languages: ['English', 'Mandarin'],
    acceptingNewPatients: true,
    rating: 4.8,
    reviewCount: 98,
    location: {
      facilityName: 'University Medical Center',
      address: '200 Research Ave',
      city: 'San Francisco',
      state: 'CA',
      zipCode: '94110'
    },
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    id: '3',
    userId: 'u3',
    firstName: 'Lisa',
    lastName: 'Martinez',
    title: 'LCSW',
    specialty: 'Mental Health',
    licenseNumber: 'MH-44721',
    email: 'lisa.martinez@example.com',
    phone: '(555) 123-4003',
    bio: 'Specialized in therapy for chronic illness, trauma, and wellness support.',
    yearsOfExperience: 8,
    languages: ['English', 'Spanish'],
    acceptingNewPatients: true,
    rating: 5.0,
    reviewCount: 84,
    location: {
      facilityName: 'Wellness Center',
      address: '50 Care St',
      city: 'San Francisco',
      state: 'CA',
      zipCode: '94103'
    },
    createdAt: new Date(),
    updatedAt: new Date()
  }
];

export async function GET() {
  return NextResponse.json({ providers });
}

