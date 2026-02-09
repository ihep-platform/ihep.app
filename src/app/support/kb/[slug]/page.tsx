type Article = { slug: string; title: string; summary: string; category: string }

async function getArticles(): Promise<Article[]> {
  const res = await fetch('/api/support/kb', { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to load knowledgebase')
  const data = await res.json()
  return data.articles
}

export default async function KnowledgeArticlePage({ params }: { params: { slug: string } }) {
  const articles = await getArticles()
  const article = articles.find((a) => a.slug === params.slug)

  if (!article) {
    return <div className="text-sm text-muted-foreground">Article not found.</div>
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Knowledgebase · {article.category}</p>
      <h1 className="text-3xl font-semibold">{article.title}</h1>
      <p className="text-sm text-muted-foreground">{article.summary}</p>
      <p className="text-sm text-muted-foreground">
        Detailed content will be authored here. For now, this stub ensures routing and data flow are in place.
      </p>
    </div>
  )
}

