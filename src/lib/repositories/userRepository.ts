/**
 * User Repository
 *
 * Data access layer for user operations. Uses PostgreSQL via Drizzle ORM
 * when available, falls back to mockStore in development.
 *
 * Author: Jason M Jarmacz | jason@ihep.app
 * Co-Author: Claude by Anthropic
 */

import { eq } from 'drizzle-orm'
import bcrypt from 'bcryptjs'
import { db, isDatabaseAvailable, schema } from '@/lib/db'
import { mockStore, type MockUser } from '@/lib/mockStore'
import type { User, InsertUser } from '@shared/schema'

// Unified user type for both database and mock store
export type UserRecord = User | MockUser

export interface UserRepository {
  findById(id: number): Promise<UserRecord | null>
  findByUsername(username: string): Promise<UserRecord | null>
  findByEmail(email: string): Promise<UserRecord | null>
  create(data: Omit<InsertUser, 'id' | 'createdAt'>): Promise<UserRecord>
  update(id: number, data: Partial<InsertUser>): Promise<UserRecord | null>
  validatePassword(user: UserRecord, password: string): Promise<boolean>
}

/**
 * Database-backed user repository using Drizzle ORM
 */
class DatabaseUserRepository implements UserRepository {
  async findById(id: number): Promise<User | null> {
    if (!db) return null
    const result = await db.select().from(schema.users).where(eq(schema.users.id, id)).limit(1)
    return result[0] ?? null
  }

  async findByUsername(username: string): Promise<User | null> {
    if (!db) return null
    const result = await db
      .select()
      .from(schema.users)
      .where(eq(schema.users.username, username))
      .limit(1)
    return result[0] ?? null
  }

  async findByEmail(email: string): Promise<User | null> {
    if (!db) return null
    const result = await db
      .select()
      .from(schema.users)
      .where(eq(schema.users.email, email))
      .limit(1)
    return result[0] ?? null
  }

  async create(data: Omit<InsertUser, 'id' | 'createdAt'>): Promise<User> {
    if (!db) throw new Error('Database not available')
    // Hash password before storing (12 rounds per OWASP 2024)
    const hashedPassword = await bcrypt.hash(data.password, 12)
    const result = await db
      .insert(schema.users)
      .values({
        ...data,
        password: hashedPassword,
      })
      .returning()
    return result[0]
  }

  async update(id: number, data: Partial<InsertUser>): Promise<User | null> {
    if (!db) return null
    // If password is being updated, hash it
    if (data.password) {
      data.password = await bcrypt.hash(data.password, 12)
    }
    const result = await db
      .update(schema.users)
      .set(data)
      .where(eq(schema.users.id, id))
      .returning()
    return result[0] ?? null
  }

  async validatePassword(user: UserRecord, password: string): Promise<boolean> {
    return bcrypt.compare(password, user.password)
  }
}

/**
 * Mock store-backed user repository for development without database
 */
class MockUserRepository implements UserRepository {
  async findById(id: number): Promise<MockUser | null> {
    // MockStore doesn't have findById, search through users
    const byUsername = await mockStore.getUserByUsername('demo')
    if (byUsername && byUsername.id === id) return byUsername
    return null
  }

  async findByUsername(username: string): Promise<MockUser | null> {
    return mockStore.getUserByUsername(username)
  }

  async findByEmail(email: string): Promise<MockUser | null> {
    return mockStore.getUserByEmail(email)
  }

  async create(data: Omit<InsertUser, 'id' | 'createdAt'>): Promise<MockUser> {
    // Hash password before storing
    const hashedPassword = await bcrypt.hash(data.password, 12)
    return mockStore.createUser({
      username: data.username,
      email: data.email,
      firstName: data.firstName,
      lastName: data.lastName,
      password: hashedPassword,
      role: data.role ?? 'patient',
      profilePicture: data.profilePicture ?? undefined,
      phone: data.phone ?? undefined,
      preferredContactMethod: data.preferredContactMethod ?? undefined,
    })
  }

  async update(_id: number, _data: Partial<InsertUser>): Promise<MockUser | null> {
    // MockStore doesn't support updates
    console.warn('[MockUserRepository] Update operations not supported in mock mode')
    return null
  }

  async validatePassword(user: UserRecord, password: string): Promise<boolean> {
    return bcrypt.compare(password, user.password)
  }
}

/**
 * Get the appropriate user repository based on database availability
 */
export function getUserRepository(): UserRepository {
  if (isDatabaseAvailable()) {
    return new DatabaseUserRepository()
  }
  console.warn('[UserRepository] Database not available, using mock store')
  return new MockUserRepository()
}

// Export singleton instance
export const userRepository = getUserRepository()
