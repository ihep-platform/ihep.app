'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { KnowledgebaseArticle } from '@/types/support'

export default function SupportPage() {
  const [articles, setArticles] = useState<KnowledgebaseArticle[]>([])
  const [query, setQuery] = useState('')
  const [message, setMessage] = useState('')
  const [category, setCategory] = useState('general')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      const res = await fetch('/api/support/kb', { cache: 'no-store' })
      if (res.ok) {
        const data = await res.json()
        setArticles(data.articles)
      }
      setLoading(false)
    }
    load()
  }, [])

  const filtered = useMemo(
    () =>
      articles.filter(
        (a) =>
          a.title.toLowerCase().includes(query.toLowerCase()) ||
          a.summary.toLowerCase().includes(query.toLowerCase()) ||
          a.category.toLowerCase().includes(query.toLowerCase())
      ),
    [articles, query]
  )

  const submitTicket = async () => {
    if (!message.trim()) return
    await fetch('/api/support/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject: 'Member support request', message, category })
    })
    setMessage('')
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm text-muted-foreground">Support & Knowledgebase</p>
        <h1 className="text-3xl font-semibold">Help Center</h1>
      </header>

      <Card className="apple-card">
        <CardContent className="pt-6 space-y-3">
          <Input
            placeholder="Search help articles..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="grid gap-3 md:grid-cols-2">
          {loading && <p className="text-sm text-muted-foreground">Loading articles...</p>}
          {!loading && filtered.map((article) => (
              <div key={article.slug} className="rounded-lg border p-3 shadow-sm">
                <p className="text-xs text-muted-foreground">{article.category}</p>
                <h3 className="text-lg font-semibold">{article.title}</h3>
                <p className="text-sm text-muted-foreground">{article.summary}</p>
                <Link href={`/support/kb/${article.slug}`} className="text-sm text-primary">
                  Read more
                </Link>
              </div>
            ))}
          {!loading && filtered.length === 0 && <p className="text-sm text-muted-foreground">No articles found.</p>}
          </div>
        </CardContent>
      </Card>

      <Card className="apple-card">
        <CardHeader>
          <CardTitle>Contact Support</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            placeholder="Category (billing, technical, account, care)"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
          <Input
            placeholder="Describe your issue"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          <div className="flex justify-end">
            <Button onClick={submitTicket} disabled={!message.trim()}>
              Submit ticket
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

