"""
Scout Agent — Real-time trend & news monitoring for DDWL
=========================================================
Uses Groq (FREE) + Google News RSS + Reddit scraping to:
  1. Monitor real-time news on topics Lee cares about
  2. Scrape Google News RSS for breaking stories
  3. Check Reddit for trending discussions
  4. Generate concise briefings via Groq AI analysis

USAGE:
    python xai_scout.py trends                     # Latest news across all topics
    python xai_scout.py news "wholesaling"         # Google News search
    python xai_scout.py reddit "real estate"       # Reddit search
    python xai_scout.py ask "What's hot in AI?"    # Ask Groq directly
    python xai_scout.py brief                      # Full morning brief
    python xai_scout.py test                       # Test API connection
    python xai_scout.py                            # Interactive mode

COST: $0.00 (Groq free tier — 1K req/day)
"""

import os
import sys
import json
import time
import re
import xml.etree.ElementTree as ET
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

# Topics Lee cares about
DDWL_TOPICS = {
    "real_estate": [
        "real estate wholesaling",
        "Tampa Bay real estate market",
        "creative finance real estate",
        "subject-to deals",
    ],
    "ai_business": [
        "AI agents for business",
        "AI automation small business",
        "GoHighLevel AI",
        "AI real estate tools",
    ],
    "coaching": [
        "real estate coaching",
        "real estate mentorship",
    ],
}

BRAIN_DIR = Path(__file__).parent / "ghl-knowledge"
BRAIN_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


# ============================================================
# DATA SOURCES (Free)
# ============================================================

def fetch_google_news(query, max_results=8):
    """Fetch headlines from Google News RSS feed."""
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            log("NEWS", f"Google News returned {r.status_code}")
            return []

        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item")[:max_results]:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            source = item.find("source")
            items.append({
                "title": title.text if title is not None else "",
                "link": link.text if link is not None else "",
                "date": pub_date.text if pub_date is not None else "",
                "source": source.text if source is not None else "",
            })
        return items
    except Exception as e:
        log("NEWS", f"Error: {e}")
        return []


def fetch_reddit(query, subreddit="all", max_results=8):
    """Fetch posts from Reddit search JSON API."""
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={quote_plus(query)}&sort=new&limit={max_results}&t=week"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            log("REDDIT", f"Reddit returned {r.status_code}")
            return []

        data = r.json()
        posts = []
        for child in data.get("data", {}).get("children", [])[:max_results]:
            d = child.get("data", {})
            posts.append({
                "title": d.get("title", ""),
                "subreddit": d.get("subreddit", ""),
                "score": d.get("score", 0),
                "comments": d.get("num_comments", 0),
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "created": datetime.fromtimestamp(d.get("created_utc", 0)).strftime("%Y-%m-%d"),
            })
        return posts
    except Exception as e:
        log("REDDIT", f"Error: {e}")
        return []


# ============================================================
# GROQ AI BRAIN (Free)
# ============================================================

def call_groq(messages, temperature=0.3, max_tokens=2000):
    """Call Groq API — FREE, fast, reliable."""
    if not GROQ_API_KEY:
        log("ERROR", "GROQ_API_KEY not set in .env")
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        r = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        if r.status_code != 200:
            log("ERROR", f"Groq API {r.status_code}: {r.text[:200]}")
            return None
        return r.json()
    except Exception as e:
        log("ERROR", f"Groq request failed: {e}")
        return None


def groq_response(messages, **kwargs):
    """Get just the text response from Groq."""
    result = call_groq(messages, **kwargs)
    if not result:
        return None
    return result.get("choices", [{}])[0].get("message", {}).get("content", "")


# ============================================================
# SCOUT COMMANDS
# ============================================================

def search_news(query, context=""):
    """Search Google News and analyze with Groq."""
    log("NEWS", f"Searching news for: {query}")
    articles = fetch_google_news(query)

    if not articles:
        return "No news articles found."

    # Format articles for Groq analysis
    article_text = "\n".join(
        f"- [{a['source']}] {a['title']} ({a['date'][:16]})"
        for a in articles
    )

    system = """You are Scout, a research agent for Do Deals With Lee (DDWL), a Tampa Bay real estate investment company run by Lee Kearney.
Analyze these news headlines and provide:
1. Key takeaways (bullet points)
2. Anything Lee should act on immediately
3. Market sentiment (bullish/bearish/neutral)
Be concise and actionable."""

    if context:
        system += f"\n\nAdditional context: {context}"

    response = groq_response([
        {"role": "system", "content": system},
        {"role": "user", "content": f"Analyze these recent news headlines about '{query}':\n\n{article_text}"},
    ])

    # Combine raw headlines + analysis
    output = f"### Google News: {query}\n\n"
    for a in articles:
        output += f"- **{a['title']}** — {a['source']} ({a['date'][:16]})\n"
    output += f"\n### Scout Analysis\n\n{response or 'Analysis unavailable.'}"
    return output


def search_reddit_topics(query, context=""):
    """Search Reddit and analyze with Groq."""
    log("REDDIT", f"Searching Reddit for: {query}")
    posts = fetch_reddit(query)

    if not posts:
        return "No Reddit posts found."

    post_text = "\n".join(
        f"- [r/{p['subreddit']}] {p['title']} (score: {p['score']}, comments: {p['comments']}, {p['created']})"
        for p in posts
    )

    system = """You are Scout, a research agent for Do Deals With Lee (DDWL), a Tampa Bay real estate investment company.
Analyze these Reddit discussions and provide:
1. Key themes and sentiment
2. Common questions or pain points
3. Opportunities for Lee (content ideas, engagement, deals)
Be concise."""

    if context:
        system += f"\n\nAdditional context: {context}"

    response = groq_response([
        {"role": "system", "content": system},
        {"role": "user", "content": f"Analyze these Reddit posts about '{query}':\n\n{post_text}"},
    ])

    output = f"### Reddit: {query}\n\n"
    for p in posts:
        output += f"- **{p['title']}** — r/{p['subreddit']} ({p['score']}↑, {p['comments']} comments)\n"
    output += f"\n### Scout Analysis\n\n{response or 'Analysis unavailable.'}"
    return output


def ask_scout(question):
    """Ask Scout anything — uses Groq directly."""
    log("ASK", f"Question: {question}")

    response = groq_response([
        {"role": "system", "content": """You are Scout, a research agent for Do Deals With Lee (DDWL), a Tampa Bay real estate investment company run by Lee Kearney.
Lee is a real estate investor, wholesaler, and coach. He runs deals, coaching programs, and uses AI/automation (GoHighLevel, Telegram bots, voice AI).
Answer questions with actionable insights. Be concise. Use bullet points."""},
        {"role": "user", "content": question},
    ])

    return response or "No response from Groq."


def get_trending():
    """Get trending news across all DDWL topics."""
    log("TRENDS", "Fetching trends across all topics...")
    all_headlines = []

    # Fetch news for key topics
    key_queries = [
        "real estate wholesaling",
        "Tampa Bay real estate",
        "AI agents business automation",
        "GoHighLevel updates",
    ]

    for query in key_queries:
        log("TRENDS", f"  → {query}")
        articles = fetch_google_news(query, max_results=5)
        for a in articles:
            all_headlines.append(f"[{query}] {a['title']} — {a['source']}")
        time.sleep(0.5)  # Be polite to Google

    if not all_headlines:
        return "No trending news found."

    headlines_text = "\n".join(f"- {h}" for h in all_headlines)

    response = groq_response([
        {"role": "system", "content": """You are Scout, a research agent for Do Deals With Lee (DDWL).
Lee Kearney runs a Tampa Bay real estate investment company. He does wholesaling, coaching, and uses AI/automation.

Analyze these headlines and create a TRENDS REPORT with:
1. **Hot Right Now** — Top 3 stories Lee needs to know
2. **Market Pulse** — Real estate market direction
3. **AI & Tech** — Relevant AI/automation news
4. **Action Items** — What Lee should do today based on these trends

Be concise. Bullet points. Flag urgent items with ⚡."""},
        {"role": "user", "content": f"Here are today's headlines across Lee's key topics:\n\n{headlines_text}"},
    ], max_tokens=2500)

    return f"# Trends Report — {datetime.now().strftime('%B %d, %Y')}\n\n{response or 'No analysis available.'}"


def generate_morning_brief():
    """Generate a full morning briefing for Lee."""
    log("BRIEF", "Generating morning brief...")
    now = datetime.now().strftime("%A, %B %d, %Y")
    sections = []

    # 1. Trends
    log("BRIEF", "Section 1/4: Trends")
    trends = get_trending()
    if trends:
        sections.append(trends)

    # 2. Reddit Pulse
    log("BRIEF", "Section 2/4: Reddit")
    reddit = search_reddit_topics("real estate wholesaling")
    if reddit:
        sections.append(reddit)

    # 3. AI News
    log("BRIEF", "Section 3/4: AI News")
    ai_news = search_news("AI agents business automation 2026")
    if ai_news:
        sections.append(ai_news)

    # 4. Tampa Bay Local
    log("BRIEF", "Section 4/4: Tampa Bay")
    local = search_news("Tampa Bay real estate market")
    if local:
        sections.append(local)

    # Compile brief
    divider = "\n\n---\n\n"
    brief = f"""# DDWL Morning Brief — {now}

Generated by Scout (Groq llama-3.3-70b) at {time.strftime("%I:%M %p")}
Cost: $0.00

---

{divider.join(sections) if sections else "No data available. Check internet connection."}

---

*Scout — Do Deals With Lee Research Agent*
*Powered by Groq (free) + Google News + Reddit*
"""

    # Save to brain
    brief_file = BRAIN_DIR / f"morning-brief-{datetime.now().strftime('%Y-%m-%d')}.md"
    brief_file.write_text(brief, encoding="utf-8")
    log("BRIEF", f"Saved to {brief_file.name}")

    return brief


# ============================================================
# CLI
# ============================================================

def interactive_mode():
    """Interactive chat with Scout."""
    print("\n  Scout — DDWL Research Agent (Groq + Google News + Reddit)")
    print("  Commands: trends, news <query>, reddit <query>, ask <question>, brief, quit\n")

    while True:
        try:
            user_input = input("  Scout> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            break

        if user_input.lower() == "trends":
            result = get_trending()
        elif user_input.lower().startswith("news "):
            result = search_news(user_input[5:])
        elif user_input.lower().startswith("reddit "):
            result = search_reddit_topics(user_input[7:])
        elif user_input.lower().startswith("ask "):
            result = ask_scout(user_input[4:])
        elif user_input.lower() == "brief":
            result = generate_morning_brief()
        else:
            result = ask_scout(user_input)

        if result:
            print(f"\n{result}\n")
        else:
            print("\n  No results.\n")


def main():
    if len(sys.argv) < 2:
        interactive_mode()
        return

    cmd = sys.argv[1].lower()

    if cmd == "trends":
        result = get_trending()
    elif cmd == "news" and len(sys.argv) > 2:
        result = search_news(" ".join(sys.argv[2:]))
    elif cmd == "reddit" and len(sys.argv) > 2:
        result = search_reddit_topics(" ".join(sys.argv[2:]))
    elif cmd == "ask" and len(sys.argv) > 2:
        result = ask_scout(" ".join(sys.argv[2:]))
    elif cmd == "brief":
        result = generate_morning_brief()
    elif cmd == "test":
        log("TEST", "Testing Groq API connection...")
        result = call_groq([{"role": "user", "content": "Say 'Scout online' in one sentence."}])
        if result:
            msg = result["choices"][0]["message"]["content"]
            log("TEST", f"✓ Groq: {msg}")
        else:
            log("TEST", "✗ Groq FAILED")
            return

        log("TEST", "Testing Google News RSS...")
        articles = fetch_google_news("real estate", max_results=3)
        if articles:
            log("TEST", f"✓ Google News: {len(articles)} articles")
            for a in articles[:2]:
                log("TEST", f"  → {a['title'][:60]}...")
        else:
            log("TEST", "✗ Google News FAILED")

        log("TEST", "Testing Reddit API...")
        posts = fetch_reddit("real estate", max_results=3)
        if posts:
            log("TEST", f"✓ Reddit: {len(posts)} posts")
            for p in posts[:2]:
                log("TEST", f"  → {p['title'][:60]}...")
        else:
            log("TEST", "✗ Reddit FAILED")

        log("TEST", "All systems checked.")
        return
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python xai_scout.py [trends|news <q>|reddit <q>|ask <q>|brief|test]")
        return

    if result:
        print(f"\n{result}")
    else:
        print("No results.")


if __name__ == "__main__":
    main()
