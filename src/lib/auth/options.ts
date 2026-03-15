import type { NextAuthOptions } from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import GoogleProvider from 'next-auth/providers/google'
// import AppleProvider from 'next-auth/providers/apple'
import { mockStore } from '@/lib/mockStore'
import bcrypt from 'bcryptjs'
// import { generateAppleClientSecret } from './apple-secret'

export const authOptions: NextAuthOptions = {
  secret: process.env.SESSION_SECRET,
  providers: (() => {
    const providers: NextAuthOptions['providers'] = []

    const hasGoogle =
      !!process.env.GOOGLE_CLIENT_ID && !!process.env.GOOGLE_CLIENT_SECRET
    if (hasGoogle) {
      providers.push(
        GoogleProvider({
          clientId: process.env.GOOGLE_CLIENT_ID!,
          clientSecret: process.env.GOOGLE_CLIENT_SECRET!
        })
      )
    }

    // Apple Sign-In requires dynamic client secret generation
    // Currently disabled - requires async initialization pattern
    // TODO: Implement Apple OAuth with proper async secret generation
    // const hasApple =
    //   !!process.env.APPLE_CLIENT_ID &&
    //   !!process.env.APPLE_TEAM_ID &&
    //   !!process.env.APPLE_KEY_ID &&
    //   !!process.env.APPLE_PRIVATE_KEY
    // if (hasApple) {
    //   providers.push(
    //     AppleProvider({
    //       clientId: process.env.APPLE_CLIENT_ID!,
    //       clientSecret: generateAppleClientSecret(),
    //       authorization: { params: { scope: 'name email' } }
    //     })
    //   )
    // }

    providers.push(
      CredentialsProvider({
        name: 'credentials',
        credentials: {
          username: { label: 'Username', type: 'text' },
          password: { label: 'Password', type: 'password' }
        },
        async authorize(credentials) {
          if (!credentials?.username || !credentials?.password) return null
          const user = await mockStore.getUserByUsername(credentials.username)
          if (!user) return null
          const ok = await bcrypt.compare(credentials.password, user.password)
          if (!ok) return null
          return {
            id: String(user.id),
            username: user.username,
            email: user.email,
            firstName: user.firstName,
            lastName: user.lastName,
            role: user.role,
            profilePicture: user.profilePicture ?? undefined,
            phone: user.phone ?? undefined,
            preferredContactMethod: user.preferredContactMethod ?? undefined
          }
        }
      })
    )

    return providers
  })(),
  session: { strategy: 'jwt', maxAge: 30 * 60 },
  pages: { signIn: '/login' },
  callbacks: {
    async jwt({ token, user, account }) {
      if (user) {
        const fromOAuth = account?.provider && account.provider !== 'credentials'
        const name = user.name as string | undefined
        const [firstName, ...rest] = (name ?? '').split(' ').filter(Boolean)
        token.role = user.role ?? 'patient'
        token.username = user.username ?? user.email ?? ''
        token.firstName = user.firstName ?? firstName ?? ''
        token.lastName = user.lastName ?? rest.join(' ') ?? ''
        if (fromOAuth && user.email) {
          token.email = user.email
        }
      }
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub!
        session.user.role = token.role
        session.user.username = token.username
        session.user.firstName = token.firstName
        session.user.lastName = token.lastName
        if (token.email) {
          session.user.email = token.email
        }
      }
      return session
    }
  }
}
