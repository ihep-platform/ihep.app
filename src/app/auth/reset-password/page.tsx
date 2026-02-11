'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'

type Step = 'identify' | 'verify' | 'new-password' | 'success'

export default function ResetPasswordPage() {
  const [step, setStep] = useState<Step>('identify')
  const [username, setUsername] = useState('')
  const [resetCode, setResetCode] = useState('')
  const [generatedCode, setGeneratedCode] = useState('')
  const [codeInput, setCodeInput] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [passwordChecks, setPasswordChecks] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false,
  })

  const validatePassword = (password: string) => {
    setPasswordChecks({
      length: password.length >= 12,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[@$!%*?&#^_\-.+=\/~]/.test(password),
    })
  }

  const allPasswordChecksMet =
    passwordChecks.length &&
    passwordChecks.uppercase &&
    passwordChecks.lowercase &&
    passwordChecks.number &&
    passwordChecks.special

  /** Step 1: User enters username/email to identify their account */
  const handleIdentify = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!username.trim()) {
      setError('Please enter your username.')
      return
    }

    // Generate a 6-digit code for simulated verification
    const code = String(Math.floor(100000 + Math.random() * 900000))
    setGeneratedCode(code)
    setResetCode(code)
    setStep('verify')
  }

  /** Step 2: User enters the verification code */
  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (codeInput.trim() !== generatedCode) {
      setError('Invalid verification code. Please check and try again.')
      return
    }

    setStep('new-password')
  }

  /** Step 3: User sets a new password */
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!allPasswordChecksMet) {
      setError('Password does not meet all complexity requirements.')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username.trim(),
          newPassword,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setStep('success')
      } else {
        if (data.errors && Array.isArray(data.errors)) {
          setError(data.errors.map((e: { message: string }) => e.message).join(', '))
        } else {
          setError(data.message || 'Password reset failed.')
        }
      }
    } catch {
      setError('An error occurred. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center px-4 py-8">
      <Card className="apple-card w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold gradient-text">Reset Password</CardTitle>
          <p className="text-gray-600">
            {step === 'identify' && 'Enter your username to begin the reset process.'}
            {step === 'verify' && 'Enter the verification code to continue.'}
            {step === 'new-password' && 'Choose a new password for your account.'}
            {step === 'success' && 'Your password has been updated.'}
          </p>
        </CardHeader>
        <CardContent>

          {/* --- Step 1: Identify Account --- */}
          {step === 'identify' && (
            <form onSubmit={handleIdentify} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="w-full"
                  autoFocus
                />
              </div>
              {error && (
                <div className="text-red-600 text-sm">{error}</div>
              )}
              <Button type="submit" className="gradient-primary w-full">
                Continue
              </Button>
            </form>
          )}

          {/* --- Step 2: Verify Code --- */}
          {step === 'verify' && (
            <>
              <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                <p className="font-semibold mb-1">Development Mode -- Simulated Email</p>
                <p>
                  In production, a verification code would be sent to the email address
                  on file. For development purposes, the code is displayed below:
                </p>
                <p className="mt-2 font-mono text-lg tracking-widest text-center font-bold">
                  {resetCode}
                </p>
              </div>
              <form onSubmit={handleVerify} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="code">Verification Code</Label>
                  <Input
                    id="code"
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    value={codeInput}
                    onChange={(e) => setCodeInput(e.target.value.replace(/\D/g, ''))}
                    required
                    className="w-full font-mono tracking-widest text-center text-lg"
                    autoFocus
                  />
                </div>
                {error && (
                  <div className="text-red-600 text-sm">{error}</div>
                )}
                <Button type="submit" className="gradient-primary w-full">
                  Verify Code
                </Button>
              </form>
            </>
          )}

          {/* --- Step 3: New Password --- */}
          {step === 'new-password' && (
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="newPassword">New Password</Label>
                <Input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => {
                    setNewPassword(e.target.value)
                    validatePassword(e.target.value)
                  }}
                  required
                  minLength={12}
                  className="w-full"
                  autoFocus
                />
                {newPassword.length > 0 && (
                  <ul className="text-xs space-y-1 mt-1">
                    <li className={passwordChecks.length ? 'text-green-600' : 'text-gray-500'}>
                      {passwordChecks.length ? '[met]' : '[--]'} 12+ characters
                    </li>
                    <li className={passwordChecks.uppercase ? 'text-green-600' : 'text-gray-500'}>
                      {passwordChecks.uppercase ? '[met]' : '[--]'} Uppercase letter
                    </li>
                    <li className={passwordChecks.lowercase ? 'text-green-600' : 'text-gray-500'}>
                      {passwordChecks.lowercase ? '[met]' : '[--]'} Lowercase letter
                    </li>
                    <li className={passwordChecks.number ? 'text-green-600' : 'text-gray-500'}>
                      {passwordChecks.number ? '[met]' : '[--]'} Number
                    </li>
                    <li className={passwordChecks.special ? 'text-green-600' : 'text-gray-500'}>
                      {passwordChecks.special ? '[met]' : '[--]'} Special character (@$!%*?&#^_-.+=~/`)
                    </li>
                  </ul>
                )}
                {newPassword.length === 0 && (
                  <p className="text-xs text-gray-500">
                    Min 12 characters. Must include uppercase, lowercase, number, and special character.
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={12}
                  className="w-full"
                />
                {confirmPassword.length > 0 && confirmPassword !== newPassword && (
                  <p className="text-xs text-red-600">Passwords do not match.</p>
                )}
              </div>
              {error && (
                <div className="text-red-600 text-sm">{error}</div>
              )}
              <Button
                type="submit"
                className="gradient-primary w-full"
                disabled={isLoading}
              >
                {isLoading ? 'Resetting Password...' : 'Reset Password'}
              </Button>
            </form>
          )}

          {/* --- Step 4: Success --- */}
          {step === 'success' && (
            <div className="text-center space-y-4">
              <p className="text-gray-700">
                Your password has been reset successfully. You can now sign in with
                your new password.
              </p>
              <Link href="/auth/login">
                <Button className="gradient-primary w-full">
                  Go to Sign In
                </Button>
              </Link>
            </div>
          )}

          {/* Back to login link (shown on all steps except success) */}
          {step !== 'success' && (
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Remember your password?{' '}
                <Link href="/auth/login" className="text-primary hover:underline">
                  Sign in here
                </Link>
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
