export interface Post {
  rank: number
  title: string
  title_zh: string
  subreddit: string
  url: string
  upvotes: number
  comments: number
  category: 'Commuter' | 'Urban' | 'Folding' | 'Cargo' | 'General'
  category_zh: string
  summary: string
  summary_zh: string
  why_trending: string
  why_trending_zh: string
  sentiment: string
  sentiment_zh: string
  score: number
}

export interface DigestSection {
  source: 'r/ebikes' | 'Brand Communities'
  posts: Post[]
}

export interface DailyDigest {
  date: string          // "2026-04-17"
  generated_at: string  // ISO timestamp
  sections: DigestSection[]
}

export interface DigestIndex {
  dates: string[]       // sorted desc, max 7
}
