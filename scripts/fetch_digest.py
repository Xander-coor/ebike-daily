#!/usr/bin/env python3
"""
Daily E-Bike Digest Fetcher
Fetches top posts from Reddit, scores them, generates bilingual digest via Claude API,
and writes JSON cache to public/data/.
"""

import os, json, time, sys, requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
import anthropic

# ── Config ───────────────────────────────────────────────────────────────────
REDDIT_CLIENT_ID     = os.environ["REDDIT_CLIENT_ID"]
REDDIT_CLIENT_SECRET = os.environ["REDDIT_CLIENT_SECRET"]
REDDIT_USER_AGENT    = "ebike-daily-digest/1.0"
ANTHROPIC_API_KEY    = os.environ["ANTHROPIC_API_KEY"]

SUBREDDITS_EBIKES  = ["ebikes"]
SUBREDDITS_BRANDS  = ["Aventon", "RadPowerBikes", "lectric_ebikes", "cowboyebike", "super73"]
TOP_N              = 10
DATA_DIR           = Path(__file__).parent.parent / "public" / "data"
MAX_DAYS           = 7

# ── Reddit OAuth ─────────────────────────────────────────────────────────────
def get_reddit_token() -> str:
    r = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": REDDIT_USER_AGENT},
    )
    r.raise_for_status()
    return r.json()["access_token"]

def fetch_top_posts(subreddit: str, token: str, limit: int = 50) -> list[dict]:
    url = f"https://oauth.reddit.com/r/{subreddit}/top"
    r = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "User-Agent": REDDIT_USER_AGENT},
        params={"t": "day", "limit": limit},
    )
    r.raise_for_status()
    time.sleep(0.5)  # rate limit courtesy
    children = r.json()["data"]["children"]
    posts = []
    for c in children:
        d = c["data"]
        posts.append({
            "id":       d["id"],
            "title":    d["title"],
            "subreddit": d["subreddit"],
            "url":      "https://reddit.com" + d["permalink"],
            "upvotes":  d["ups"],
            "comments": d["num_comments"],
            "awards":   d.get("total_awards_received", 0),
            "created":  d["created_utc"],
        })
    return posts

# ── Scoring ───────────────────────────────────────────────────────────────────
def score(post: dict, now_utc: float) -> float:
    age_hours = (now_utc - post["created"]) / 3600
    if age_hours < 6:
        recency = 30
    elif age_hours < 12:
        recency = 20
    elif age_hours < 18:
        recency = 10
    else:
        recency = 0
    return post["upvotes"] * 0.5 + post["comments"] * 0.3 + post["awards"] * 0.2 + recency

def top_n(posts: list[dict], n: int, now_utc: float) -> list[dict]:
    scored = sorted(posts, key=lambda p: score(p, now_utc), reverse=True)
    # If fewer than n, return all
    return scored[:n]

# ── Claude Generation ─────────────────────────────────────────────────────────
CATEGORY_MAPPING = {
    "Commuter": "通勤型",
    "Urban":    "城市休閒型",
    "Folding":  "折疊車",
    "Cargo":    "貨運車",
    "General":  "綜合",
}

def generate_post_analysis(posts: list[dict], client: anthropic.Anthropic) -> list[dict]:
    """Send posts to Claude for bilingual analysis."""
    posts_text = "\n".join(
        f"{i+1}. [{p['subreddit']}] {p['title']} (↑{p['upvotes']} 💬{p['comments']})"
        for i, p in enumerate(posts)
    )

    prompt = f"""You are analyzing Reddit posts about lifestyle e-bikes (commuter, urban, folding, cargo).

For each post below, provide a JSON array where each item has:
- rank (int, 1-based)
- title_zh (Chinese translation of title)
- category (one of: Commuter, Urban, Folding, Cargo, General)
- category_zh (Chinese: 通勤型/城市休閒型/折疊車/貨運車/綜合)
- summary (English, 2 sentences max)
- summary_zh (Chinese translation)
- why_trending (English, 1-2 sentences explaining why this is popular today)
- why_trending_zh (Chinese translation)
- sentiment (English, 1 sentence on community reaction)
- sentiment_zh (Chinese translation)

Posts:
{posts_text}

Return ONLY a valid JSON array, no markdown, no explanation."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    analyses = json.loads(raw)
    return analyses

# ── Cache management ──────────────────────────────────────────────────────────
def update_index(new_date: str) -> None:
    index_path = DATA_DIR / "index.json"
    if index_path.exists():
        idx = json.loads(index_path.read_text())
        dates = idx.get("dates", [])
    else:
        dates = []

    if new_date not in dates:
        dates.insert(0, new_date)

    # Keep max MAX_DAYS, delete old files
    dates.sort(reverse=True)
    if len(dates) > MAX_DAYS:
        for old in dates[MAX_DAYS:]:
            old_file = DATA_DIR / f"{old}.json"
            if old_file.exists():
                old_file.unlink()
                print(f"Deleted old cache: {old_file.name}")
        dates = dates[:MAX_DAYS]

    index_path.write_text(json.dumps({"dates": dates}, indent=2))
    print(f"Index updated: {dates}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")
    out_path = DATA_DIR / f"{date_str}.json"

    if out_path.exists():
        print(f"Cache already exists for {date_str}, skipping.")
        sys.exit(0)

    print(f"Fetching digest for {date_str}...")
    token = get_reddit_token()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # ── r/ebikes section ──
    print("Fetching r/ebikes...")
    ebike_posts_raw = []
    for sub in SUBREDDITS_EBIKES:
        ebike_posts_raw.extend(fetch_top_posts(sub, token))
    ebike_top = top_n(ebike_posts_raw, TOP_N, now_utc.timestamp())

    # Pad if under TOP_N
    if len(ebike_top) < TOP_N:
        print(f"  Only {len(ebike_top)} posts, padding accepted.")

    # ── Brand subreddits section ──
    print("Fetching brand subreddits...")
    brand_posts_raw = []
    for sub in SUBREDDITS_BRANDS:
        try:
            brand_posts_raw.extend(fetch_top_posts(sub, token))
        except Exception as e:
            print(f"  Warning: failed to fetch r/{sub}: {e}")
    brand_top = top_n(brand_posts_raw, TOP_N, now_utc.timestamp())

    # ── Claude analysis ──
    print("Generating analysis with Claude...")
    ebike_analyses = generate_post_analysis(ebike_top, client)
    brand_analyses = generate_post_analysis(brand_top, client)

    def merge(raw_posts: list[dict], analyses: list[dict]) -> list[dict]:
        result = []
        for i, (raw, analysis) in enumerate(zip(raw_posts, analyses)):
            result.append({
                "rank":          i + 1,
                "title":         raw["title"],
                "title_zh":      analysis.get("title_zh", ""),
                "subreddit":     raw["subreddit"],
                "url":           raw["url"],
                "upvotes":       raw["upvotes"],
                "comments":      raw["comments"],
                "category":      analysis.get("category", "General"),
                "category_zh":   analysis.get("category_zh", "綜合"),
                "summary":       analysis.get("summary", ""),
                "summary_zh":    analysis.get("summary_zh", ""),
                "why_trending":  analysis.get("why_trending", ""),
                "why_trending_zh": analysis.get("why_trending_zh", ""),
                "sentiment":     analysis.get("sentiment", ""),
                "sentiment_zh":  analysis.get("sentiment_zh", ""),
                "score":         round(score(raw, now_utc.timestamp()), 2),
            })
        return result

    digest = {
        "date":         date_str,
        "generated_at": now_utc.isoformat(),
        "sections": [
            {
                "source": "r/ebikes",
                "posts":  merge(ebike_top, ebike_analyses),
            },
            {
                "source": "Brand Communities",
                "posts":  merge(brand_top, brand_analyses),
            },
        ],
    }

    out_path.write_text(json.dumps(digest, ensure_ascii=False, indent=2))
    print(f"Written: {out_path}")
    update_index(date_str)
    print("Done.")

if __name__ == "__main__":
    main()
