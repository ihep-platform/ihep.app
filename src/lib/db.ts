/**
 * Database Connection Module
 *
 * Provides PostgreSQL connection using Drizzle ORM.
 * Designed for HIPAA compliance with connection pooling and security.
 *
 * Author: Jason M Jarmacz | jason@ihep.app
 * Co-Author: Claude by Anthropic
 */

import { drizzle } from 'drizzle-orm/postgres-js'
import postgres from 'postgres'
import * as schema from '@shared/schema'

// Environment variable validation
const DATABASE_URL = process.env.DATABASE_URL

if (!DATABASE_URL && process.env.NODE_ENV === 'production') {
  throw new Error('DATABASE_URL environment variable is required in production')
}

// Development fallback with in-memory mock
const isDevelopmentWithoutDB = !DATABASE_URL && process.env.NODE_ENV !== 'production'

// PostgreSQL connection configuration
// Using connection pooling for production workloads
const connectionConfig = {
  // Maximum connections in pool
  max: parseInt(process.env.DB_POOL_SIZE || '10', 10),
  // Idle timeout in seconds
  idle_timeout: 20,
  // Connect timeout in seconds
  connect_timeout: 10,
  // SSL mode for production
  ssl: process.env.NODE_ENV === 'production' ? 'require' as const : false,
  // Prepare statements for better performance
  prepare: true,
}

// Create PostgreSQL client
// Falls back to a placeholder in development if no DATABASE_URL
const client = DATABASE_URL
  ? postgres(DATABASE_URL, connectionConfig)
  : null

// Create Drizzle instance
// Type assertion to handle null client for development mode
export const db = client
  ? drizzle(client, { schema })
  : null

// Export a function to check database availability
export function isDatabaseAvailable(): boolean {
  return db !== null
}

// Export connection status for health checks
export async function checkDatabaseConnection(): Promise<{
  healthy: boolean
  latency?: number
  error?: string
}> {
  if (!db || !client) {
    return {
      healthy: false,
      error: isDevelopmentWithoutDB
        ? 'Database not configured (using mock store in development)'
        : 'Database connection not initialized'
    }
  }

  const startTime = Date.now()
  try {
    // Simple connectivity test
    await client`SELECT 1`
    return {
      healthy: true,
      latency: Date.now() - startTime
    }
  } catch (error) {
    return {
      healthy: false,
      latency: Date.now() - startTime,
      error: error instanceof Error ? error.message : 'Unknown database error'
    }
  }
}

// Graceful shutdown handler
export async function closeDatabaseConnection(): Promise<void> {
  if (client) {
    await client.end()
  }
}

// Re-export schema for convenience
export { schema }
