'use client'

import { useState } from 'react'
import { signIn, getSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import Link from 'next/link'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [socialLoading, setSocialLoading] = useState<string | null>(null)
  const [error, setError] = useState('')
  const router = useRouter()
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      const result = await signIn('credentials', {
        username,
        password,
        redirect: false
      })

      if (result?.error) {
        setError('Invalid username or password')
        toast({
          title: "Login Failed",
          description: "Invalid username or password. Please try again.",
          variant: "destructive",
        })
      } else {
        // Refresh session and redirect to dashboard
        await getSession()
        router.push('/dashboard')
      }
    } catch (error) {
      setError('An error occurred during login')
      toast({
        title: "Error",
        description: "An error occurred during login. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSocial = async (provider: 'google' | 'apple') => {
    if (socialLoading) return
    setSocialLoading(provider)
    try {
      await signIn(provider, { callbackUrl: '/dashboard' })
    } finally {
      setSocialLoading(null)
    }
  }

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center px-4">
      <Card className="apple-card w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold gradient-text">Welcome Back</CardTitle>
          <p className="text-gray-600">Sign in to your IHEP account</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Button
              type="button"
              variant="outline"
              className="w-full"
              disabled={isLoading || !!socialLoading}
              onClick={() => handleSocial('google')}
            >
              {socialLoading === 'google' ? 'Connecting to Google...' : 'Continue with Google'}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full"
              disabled={isLoading || !!socialLoading}
              onClick={() => handleSocial('apple')}
            >
              {socialLoading === 'apple' ? 'Connecting to Apple...' : 'Continue with Apple'}
            </Button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 mt-6">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full"
              />
            </div>
            {error && (
              <div className="text-red-600 text-sm">{error}</div>
            )}
            <Button
              type="submit"
              className="gradient-primary w-full"
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <Link href="/auth/reset-password" className="text-sm text-primary hover:underline">
              Forgot Password?
            </Link>
          </div>
          <div className="mt-3 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link href="/auth/signup" className="text-primary hover:underline">
                Sign up here
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
