/**
 * Drizzle Kit Configuration
 *
 * Configuration for Drizzle ORM migrations and schema management.
 *
 * Author: Jason M Jarmacz | jason@ihep.app
 * Co-Author: Claude by Anthropic
 */

import { defineConfig } from 'drizzle-kit'

// Allow development without DATABASE_URL (uses mock store)
const DATABASE_URL = process.env.DATABASE_URL
if (!DATABASE_URL && process.env.NODE_ENV === 'production') {
  throw new Error('DATABASE_URL is required in production')
}

export default defineConfig({
  // Output directory for migrations
  out: './drizzle',
  // Schema location (corrected path)
  schema: './src/shared/schema.ts',
  // Database dialect
  dialect: 'postgresql',
  // Database credentials from environment
  dbCredentials: {
    url: DATABASE_URL || '',
  },
  // Verbose logging in development
  verbose: process.env.NODE_ENV !== 'production',
  // Strict mode for safer migrations
  strict: true,
})
