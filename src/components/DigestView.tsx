import type { DailyDigest, Post } from '../types/digest'

interface Props {
  digest: DailyDigest
}

const CATEGORY_COLORS: Record<string, string> = {
  Commuter: 'text-sky-400 bg-sky-400/10 border-sky-400/30',
  Urban:    'text-violet-400 bg-violet-400/10 border-violet-400/30',
  Folding:  'text-amber-400 bg-amber-400/10 border-amber-400/30',
  Cargo:    'text-orange-400 bg-orange-400/10 border-orange-400/30',
  General:  'text-zinc-400 bg-zinc-400/10 border-zinc-400/30',
}

function PostCard({ post }: { post: Post }) {
  return (
    <article className="border border-zinc-800 rounded-lg p-5 hover:border-zinc-700 transition-colors">
      {/* Rank + Category */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <span className="text-3xl font-mono font-bold text-zinc-700 leading-none">
          {String(post.rank).padStart(2, '0')}
        </span>
        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${CATEGORY_COLORS[post.category]}`}>
          {post.category} · {post.category_zh}
        </span>
      </div>

      {/* Title */}
      <a
        href={post.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block group"
      >
        <h3 className="font-semibold text-zinc-100 group-hover:text-brand-400 transition-colors leading-snug">
          {post.title}
        </h3>
        <p className="text-sm text-zinc-500 mt-0.5">{post.title_zh}</p>
      </a>

      {/* Stats */}
      <div className="flex items-center gap-4 mt-3 text-xs font-mono text-zinc-600">
        <span>r/{post.subreddit}</span>
        <span>↑ {post.upvotes.toLocaleString()}</span>
        <span>💬 {post.comments.toLocaleString()}</span>
      </div>

      {/* Divider */}
      <div className="border-t border-zinc-800/80 my-4" />

      {/* Content fields */}
      <div className="space-y-3 text-sm">
        <div>
          <p className="text-[10px] font-mono text-zinc-600 uppercase tracking-widest mb-1">Summary · 摘要</p>
          <p className="text-zinc-300">{post.summary}</p>
          <p className="text-zinc-500 mt-1">{post.summary_zh}</p>
        </div>
        <div>
          <p className="text-[10px] font-mono text-zinc-600 uppercase tracking-widest mb-1">Why Trending · 為何熱門</p>
          <p className="text-zinc-300">{post.why_trending}</p>
          <p className="text-zinc-500 mt-1">{post.why_trending_zh}</p>
        </div>
        <div>
          <p className="text-[10px] font-mono text-zinc-600 uppercase tracking-widest mb-1">Community Sentiment · 社群反應</p>
          <p className="text-zinc-300">{post.sentiment}</p>
          <p className="text-zinc-500 mt-1">{post.sentiment_zh}</p>
        </div>
      </div>
    </article>
  )
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className="h-px flex-1 bg-zinc-800" />
      <span className="text-xs font-mono text-zinc-500 tracking-widest uppercase px-2">
        {title}
      </span>
      <div className="h-px flex-1 bg-zinc-800" />
    </div>
  )
}

export default function DigestView({ digest }: Props) {
  const generated = new Date(digest.generated_at).toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Taipei',
  })

  return (
    <div>
      <p className="text-xs font-mono text-zinc-600 mb-8">
        Generated at {generated} CST · {digest.sections.reduce((a, s) => a + s.posts.length, 0)} posts
      </p>

      {digest.sections.map(section => (
        <section key={section.source} className="mb-12">
          <SectionHeader title={section.source} />
          <div className="space-y-4">
            {section.posts.map(post => (
              <PostCard key={post.rank + section.source} post={post} />
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
