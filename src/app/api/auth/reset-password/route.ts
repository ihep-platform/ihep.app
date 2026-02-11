import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import bcrypt from 'bcryptjs'
import { mockStore } from '@/lib/mockStore'

const resetPasswordSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  newPassword: z.string()
    .min(12, 'Password must be at least 12 characters')
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#^_\-.+=\/~])[A-Za-z\d@$!%*?&#^_\-.,()+=\/~[\]{}|\\`]+$/,
      'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
    ),
})

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const validatedData = resetPasswordSchema.parse(body)

    // Verify the user exists before attempting password update
    const existingUser = await mockStore.getUserByUsername(validatedData.username)
    if (!existingUser) {
      // Return generic message to prevent username enumeration
      return NextResponse.json(
        { message: 'If the account exists, the password has been updated.' },
        { status: 200 }
      )
    }

    // Hash the new password with 12 rounds (OWASP 2024 recommendation)
    const saltRounds = 12
    const hashedPassword = await bcrypt.hash(validatedData.newPassword, saltRounds)

    const updated = await mockStore.updateUserPassword(validatedData.username, hashedPassword)

    if (!updated) {
      // Should not reach here given the check above, but handle defensively
      return NextResponse.json(
        { message: 'If the account exists, the password has been updated.' },
        { status: 200 }
      )
    }

    return NextResponse.json(
      { message: 'Password has been reset successfully.' },
      { status: 200 }
    )
  } catch (error) {
    if (error instanceof z.ZodError) {
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
    console.error('Password reset failed', {
      errorType: error instanceof Error ? error.name : 'Unknown',
    })
    return NextResponse.json(
      { message: 'Password reset failed' },
      { status: 500 }
    )
  }
}
