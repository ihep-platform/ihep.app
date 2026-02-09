import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/components/auth/AuthProvider'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'IHEP - Integrated Health Empowerment Program',
  description:
    'IHEP - Transforming healthcare aftercare through AI-powered digital twins. Addressing the $290B crisis in treatment adherence.',
  keywords: [
    'digital health',
    'AI',
    'HIV care',
    'digital twins',
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
      'Transforming aftercare management for life-altering conditions through digital twins and federated AI.',
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
      </body>
    </html>
  )
}
