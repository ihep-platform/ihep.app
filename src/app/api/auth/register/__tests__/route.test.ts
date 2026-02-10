/**
 * Unit tests for the registration API endpoint (POST /api/auth/register)
 *
 * Tests verify:
 *   - Zod validation rejects passwords shorter than 12 characters
 *   - Zod validation rejects passwords missing complexity requirements
 *   - Admin role is explicitly blocked with 403
 *   - Valid registration succeeds with 201
 *   - Duplicate username/email returns 400
 *   - Response never includes the password field
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

// Mock the mockStore module before importing the route
vi.mock('@/lib/mockStore', () => {
  const users: Array<{
    id: number
    username: string
    password: string
    email: string
    firstName: string
    lastName: string
    role: string
    createdAt: Date
  }> = []
  let nextId = 1

  return {
    mockStore: {
      getUserByUsername: vi.fn(async (username: string) => {
        return users.find((u) => u.username === username) ?? null
      }),
      getUserByEmail: vi.fn(async (email: string) => {
        return users.find((u) => u.email === email) ?? null
      }),
      createUser: vi.fn(async (data: Record<string, unknown>) => {
        const user = {
          ...data,
          id: nextId++,
          createdAt: new Date(),
        }
        users.push(user as typeof users[number])
        return user
      }),
      _reset: () => {
        users.length = 0
        nextId = 1
      },
    },
  }
})

// Import after mock setup
import { POST } from '../route'
import { mockStore } from '@/lib/mockStore'

/**
 * Helper to build a NextRequest with JSON body
 */
function makeRequest(body: Record<string, unknown>): NextRequest {
  return new NextRequest('http://localhost:3000/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

/** A valid registration payload that satisfies all Zod constraints */
const validPayload = {
  username: 'testuser',
  password: 'SecurePass1!xyz',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  role: 'patient',
}

describe('POST /api/auth/register', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset the in-memory store between tests
    ;(mockStore as unknown as { _reset: () => void })._reset()
  })

  describe('Password validation', () => {
    it('should reject a password shorter than 12 characters', async () => {
      const request = makeRequest({
        ...validPayload,
        password: 'Short1!a', // 8 chars - too short
      })

      const response = await POST(request)
      const body = await response.json()

      expect(response.status).toBe(400)
      expect(body.message).toContain('12')
    })

    it('should reject a password missing uppercase letter', async () => {
      const request = makeRequest({
        ...validPayload,
        password: 'alllowercase1!x', // No uppercase
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
    })

    it('should reject a password missing special character', async () => {
      const request = makeRequest({
        ...validPayload,
        password: 'NoSpecialChar1abc', // No special char
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
    })

    it('should reject a password missing digit', async () => {
      const request = makeRequest({
        ...validPayload,
        password: 'NoDigitHere!abcde', // No digit
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
    })
  })

  describe('Role restriction', () => {
    it('should reject admin role with 403 status', async () => {
      const request = makeRequest({
        ...validPayload,
        role: 'admin',
      })

      const response = await POST(request)
      const body = await response.json()

      expect(response.status).toBe(403)
      expect(body.message).toContain('institutional approval')
    })

    it('should allow patient role', async () => {
      const request = makeRequest({
        ...validPayload,
        role: 'patient',
      })

      const response = await POST(request)

      expect(response.status).toBe(201)
    })

    it('should default to patient role when not specified', async () => {
      const { role, ...payloadWithoutRole } = validPayload
      const request = makeRequest(payloadWithoutRole)

      const response = await POST(request)

      expect(response.status).toBe(201)
    })
  })

  describe('Valid registration', () => {
    it('should return 201 with user data on successful registration', async () => {
      const request = makeRequest(validPayload)

      const response = await POST(request)
      const body = await response.json()

      expect(response.status).toBe(201)
      expect(body.user).toBeDefined()
      expect(body.user.username).toBe('testuser')
      expect(body.user.email).toBe('test@example.com')
      expect(body.user.firstName).toBe('Test')
      expect(body.user.lastName).toBe('User')
    })

    it('should never include password in the response', async () => {
      const request = makeRequest(validPayload)

      const response = await POST(request)
      const body = await response.json()

      expect(response.status).toBe(201)
      expect(body.user.password).toBeUndefined()
    })

    it('should hash the password before storing', async () => {
      const request = makeRequest(validPayload)

      await POST(request)

      // createUser should have been called with a hashed password (not the plaintext)
      expect(mockStore.createUser).toHaveBeenCalledTimes(1)
      const storedData = (mockStore.createUser as ReturnType<typeof vi.fn>).mock.calls[0][0]
      expect(storedData.password).not.toBe(validPayload.password)
      // bcrypt hashes start with $2a$ or $2b$
      expect(storedData.password).toMatch(/^\$2[ab]\$/)
    })
  })

  describe('Duplicate checks', () => {
    it('should reject duplicate username with 400', async () => {
      // First registration succeeds
      const request1 = makeRequest(validPayload)
      const response1 = await POST(request1)
      expect(response1.status).toBe(201)

      // Second registration with same username
      const request2 = makeRequest({
        ...validPayload,
        email: 'different@example.com', // Different email, same username
      })
      const response2 = await POST(request2)
      const body2 = await response2.json()

      expect(response2.status).toBe(400)
      expect(body2.message).toContain('Username already exists')
    })

    it('should reject duplicate email with 400', async () => {
      // First registration
      const request1 = makeRequest(validPayload)
      const response1 = await POST(request1)
      expect(response1.status).toBe(201)

      // Second registration with same email, different username
      const request2 = makeRequest({
        ...validPayload,
        username: 'differentuser',
      })
      const response2 = await POST(request2)
      const body2 = await response2.json()

      expect(response2.status).toBe(400)
      expect(body2.message).toContain('already registered')
    })
  })

  describe('Input validation', () => {
    it('should reject missing username', async () => {
      const { username, ...payload } = validPayload
      const request = makeRequest(payload)

      const response = await POST(request)

      expect(response.status).toBe(400)
    })

    it('should reject invalid email format', async () => {
      const request = makeRequest({
        ...validPayload,
        email: 'not-an-email',
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
    })

    it('should reject missing firstName', async () => {
      const { firstName, ...payload } = validPayload
      const request = makeRequest(payload)

      const response = await POST(request)

      expect(response.status).toBe(400)
    })

    it('should reject username shorter than 3 characters', async () => {
      const request = makeRequest({
        ...validPayload,
        username: 'ab', // Too short
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
    })
  })
})
