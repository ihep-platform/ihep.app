import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import bcrypt from 'bcryptjs'
import { mockStore } from '@/lib/mockStore'

const insertUserSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string()
    .min(12, 'Password must be at least 12 characters')
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#^_\-.+=\/~])[A-Za-z\d@$!%*?&#^_\-.,()+=\/~[\]{}|\\`]+$/,
      'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
    ),
  email: z.string().email('Please enter a valid email address'),
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  role: z.string().default('patient'),
  profilePicture: z.string().optional(),
  phone: z.string().optional(),
  preferredContactMethod: z.string().optional(),
})

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const validatedData = insertUserSchema.parse(body)

    // Restrict admin role to institutional approval process
    if (validatedData.role === 'admin') {
      return NextResponse.json(
        { message: 'Administrator accounts require institutional approval. Please contact your organization administrator.' },
        { status: 403 }
      )
    }

    // Check for existing username
    const existingUserByUsername = await mockStore.getUserByUsername(validatedData.username)
    if (existingUserByUsername) {
      return NextResponse.json(
        { message: "Username already exists" },
        { status: 400 }
      )
    }

    // Check for existing email
    const existingUserByEmail = await mockStore.getUserByEmail(validatedData.email)
    if (existingUserByEmail) {
      return NextResponse.json(
        { message: "Email address is already registered. Please use a different email or try logging in." },
        { status: 400 }
      )
    }

    // Hash the password before storing it
    // Use 12 rounds for stronger protection (OWASP 2024 recommendation)
    const saltRounds = 12
    const hashedPassword = await bcrypt.hash(validatedData.password, saltRounds)

    // Replace plain password with hashed password
    const userDataWithHashedPassword = {
      ...validatedData,
      password: hashedPassword
    }

    const newUser = await mockStore.createUser(userDataWithHashedPassword)
    const { password, ...userWithoutPassword } = newUser

    return NextResponse.json(
      { user: userWithoutPassword },
      { status: 201 }
    )
  } catch (error) {
    if (error instanceof z.ZodError) {
      // Format Zod errors into user-friendly messages
      const formattedErrors = error.issues.map((issue) => {
        const field = issue.path.join('.')
        return `${field}: ${issue.message}`
      })
      return NextResponse.json(
        {
          message: formattedErrors.join('; '),
          errors: error.issues
        },
        { status: 400 }
      )
    }

    // Log error without exposing sensitive user data
    console.error('Registration failed', {
      errorType: error instanceof Error ? error.name : 'Unknown',
      // Do not log user input data (email, username, etc.)
    })
    return NextResponse.json(
      { message: "Registration failed" },
      { status: 500 }
    )
  }
}
