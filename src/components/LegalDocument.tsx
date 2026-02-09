import Link from 'next/link'
import { Button } from '@/components/ui/button'

interface LegalDocumentProps {
  title: string
  children: React.ReactNode
}

export function LegalDocument({ title, children }: LegalDocumentProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link href="/">
            <Button variant="ghost" className="mb-4">
              ← Back to Home
            </Button>
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 sm:p-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{title}</h1>

          <div className="prose prose-slate max-w-none">
            {children}
          </div>
        </div>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p>
            Questions about this document?{' '}
            <a href="mailto:legal@ihep.app" className="text-primary hover:underline">
              Contact us at legal@ihep.app
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
