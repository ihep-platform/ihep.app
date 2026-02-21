import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/components/auth/AuthProvider'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'IHEP - Integrated Health Empowerment Program',
  description:
    'IHEP helps patients navigate aftercare with 5-pillar digital twins, financial support tools, and a dynamic calendar—built with privacy-first safeguards.',
  keywords: [
    'digital health',
    'AI',
    'digital twins',
    'medication adherence',
    'care coordination',
    'health equity',
    'healthcare technology',
    'aftercare management',
    'federated AI',
  ],
  authors: [{ name: 'Integrated Health Empowerment Program' }],
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'https://ihep.app'),
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: '/',
    title: 'IHEP - AI-Powered Digital Health Aftercare Platform',
    description:
      'Navigate aftercare with 5-pillar digital twins, financial support, and a dynamic calendar—built with privacy-first safeguards.',
    siteName: 'IHEP',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} antialiased`}>
        <AuthProvider>
          {children}
        </AuthProvider>
        <Toaster />
      </body>
    </html>
  )
}
