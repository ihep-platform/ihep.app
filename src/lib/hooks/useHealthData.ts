// lib/hooks/useHealthData.ts
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';

interface WellnessMetrics {
  heartRate: number;
  bloodPressureSystolic: number;
  bloodPressureDiastolic: number;
  oxygenSaturation: number;
  temperature: number;
  viralLoad?: number;
  cd4Count?: number;
  lastUpdated: string;
}

export function useHealthData() {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<WellnessMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshMetrics = useCallback(async () => {
    if (!user) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/health/metrics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch health metrics');
      }

      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      refreshMetrics();
    }
  }, [user, refreshMetrics]);

  return { metrics, loading, error, refreshMetrics };
}
