"""
GHL Live Research Agent — Real-Time Multi-Source Intelligence
==============================================================
Scrapes the REAL sources where GHL knowledge lives:
1. GHL Changelog (ideas.gohighlevel.com/changelog) — latest features
2. Reddit (r/gohighlevel, r/HighLevel) — real user problems & solutions
3. GHL Help Center — official docs
4. GHL Developer Docs — API changes
5. Multi-AI Query — asks Perplexity/Gemini/Groq the same question, compares answers
6. GHL Ideas Board — what's coming next

Run daily or on-demand to stay ahead of GHL's own support team.

USAGE:
    python ghl_live_research.py changelog     # Latest GHL changes
    python ghl_live_research.py reddit "IVR"  # Search Reddit for IVR tips
    python ghl_live_research.py ask "how to set up Voice AI outbound calling"
    python ghl_live_research.py full          # Full research cycle
    python ghl_live_research.py status        # What we know
"""

import os
import sys
import json
import time
import re
import requests
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
AGENT_DIR = Path(__file__).parent
KB_DIR = AGENT_DIR / "ghl-knowledge"
KB_DIR.mkdir(parents=True, exist_ok=True)
LIVE_DIR = KB_DIR / "live-intel"
LIVE_DIR.mkdir(parents=True, exist_ok=True)
REDDIT_DIR = KB_DIR / "reddit"
REDDIT_DIR.mkdir(parents=True, exist_ok=True)
CHANGELOG_DIR = KB_DIR / "changelog"
CHANGELOG_DIR.mkdir(parents=True, exist_ok=True)
AI_ANSWERS_DIR = KB_DIR / "ai-answers"
AI_ANSWERS_DIR.mkdir(parents=True, exist_ok=True)

# Load env
env_file = BASE_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
GOOGLE_KEY = os.environ.get("GOOGLE_API_KEY", "")


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


# ============================================================
# 1. GHL CHANGELOG SCRAPER — Latest features & changes
# ============================================================
GHL_CHANGELOG_RSS = "https://ideas.gohighlevel.com/api/changelog/feed.rss"
GHL_CHANGELOG_URL = "https://ideas.gohighlevel.com/changelog"


def fetch_changelog():
    """Fetch latest GHL changelog entries via RSS."""
    log("CHANGELOG", "Fetching GHL changelog RSS...")
    try:
        r = requests.get(GHL_CHANGELOG_RSS, timeout=15)
        if not r.ok:
            log("CHANGELOG", f"RSS failed ({r.status_code}), trying web scrape...")
            return fetch_changelog_web()

        # Parse RSS XML
        content = r.text
        entries = []
        items = content.split("<item>")[1:]  # Skip header
        for item in items[:20]:  # Last 20 entries
            title = re.search(r"<title>(.*?)</title>", item)
            link = re.search(r"<link>(.*?)</link>", item)
            desc = re.search(r"<description>(.*?)</description>", item, re.DOTALL)
            pub_date = re.search(r"<pubDate>(.*?)</pubDate>", item)

            entry = {
                "title": title.group(1) if title else "Unknown",
                "link": link.group(1) if link else "",
                "description": desc.group(1)[:500] if desc else "",
                "date": pub_date.group(1) if pub_date else "",
            }
            # Clean HTML from description
            entry["description"] = re.sub(r"<[^>]+>", "", entry["description"]).strip()
            entries.append(entry)

        log("CHANGELOG", f"Got {len(entries)} changelog entries")
        return entries
    except Exception as e:
        log("CHANGELOG", f"Error: {str(e)[:100]}")
        return []


def fetch_changelog_web():
    """Fallback: fetch changelog via web search."""
    try:
        r = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": GOOGLE_KEY,
                "cx": "search",  # Would need a custom search engine ID
                "q": "site:ideas.gohighlevel.com/changelog",
                "num": 10,
            },
            timeout=10,
        )
        if r.ok:
            return r.json().get("items", [])
    except Exception:
        pass
    return []


def save_changelog(entries):
    """Save changelog entries."""
    if not entries:
        return

    today = datetime.now().strftime("%Y%m%d")
    filepath = CHANGELOG_DIR / f"changelog-{today}.json"
    filepath.write_text(json.dumps(entries, indent=2))

    # Also save as readable markdown
    md_path = CHANGELOG_DIR / f"changelog-{today}.md"
    lines = [f"# GHL Changelog — {datetime.now().strftime('%Y-%m-%d')}\n"]
    for e in entries:
        lines.append(f"## {e['title']}")
        if e.get("date"):
            lines.append(f"*{e['date']}*\n")
        if e.get("description"):
            lines.append(f"{e['description']}\n")
        if e.get("link"):
            lines.append(f"[Read more]({e['link']})\n")
        lines.append("---\n")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    log("CHANGELOG", f"Saved → {md_path.name}")


# ============================================================
# 2. REDDIT SCRAPER — Real user problems & solutions
# ============================================================
REDDIT_SUBREDDITS = ["gohighlevel", "HighLevel"]


def search_reddit(query, subreddit="gohighlevel", limit=10):
    """Search Reddit for GHL discussions (no API key needed)."""
    log("REDDIT", f"Searching r/{subreddit}: {query}")
    results = []

    try:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "on",
            "sort": "relevance",
            "t": "year",
            "limit": limit,
        }
        headers = {"User-Agent": "ExposureSolutions-GHL-Research/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=15)

        if r.ok:
            data = r.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts:
                p = post.get("data", {})
                results.append({
                    "title": p.get("title", ""),
                    "selftext": p.get("selftext", "")[:500],
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "url": f"https://reddit.com{p.get('permalink', '')}",
                    "created": datetime.fromtimestamp(p.get("created_utc", 0)).strftime("%Y-%m-%d"),
                    "subreddit": subreddit,
                })
            log("REDDIT", f"  Found {len(results)} posts")
        else:
            log("REDDIT", f"  HTTP {r.status_code}")
    except Exception as e:
        log("REDDIT", f"  Error: {str(e)[:100]}")

    return results


def search_reddit_all(query, limit=10):
    """Search all GHL subreddits."""
    all_results = []
    for sub in REDDIT_SUBREDDITS:
        results = search_reddit(query, sub, limit)
        all_results.extend(results)
        time.sleep(1)  # Rate limit
    # Sort by score
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results


def get_reddit_hot(subreddit="gohighlevel", limit=15):
    """Get hot/trending posts from GHL subreddit."""
    log("REDDIT", f"Fetching hot posts from r/{subreddit}...")
    try:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        headers = {"User-Agent": "ExposureSolutions-GHL-Research/1.0"}
        r = requests.get(url, params={"limit": limit}, headers=headers, timeout=15)

        if r.ok:
            posts = r.json().get("data", {}).get("children", [])
            results = []
            for post in posts:
                p = post.get("data", {})
                if p.get("stickied"):
                    continue
                results.append({
                    "title": p.get("title", ""),
                    "selftext": p.get("selftext", "")[:500],
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "url": f"https://reddit.com{p.get('permalink', '')}",
                    "created": datetime.fromtimestamp(p.get("created_utc", 0)).strftime("%Y-%m-%d"),
                })
            log("REDDIT", f"  Got {len(results)} hot posts")
            return results
        else:
            log("REDDIT", f"  HTTP {r.status_code}")
    except Exception as e:
        log("REDDIT", f"  Error: {str(e)[:100]}")
    return []


# ============================================================
# 3. MULTI-AI QUERY — Ask multiple AIs the same question
# ============================================================
def ask_groq(question, context=""):
    """Ask Groq (Llama 70B, free)."""
    if not GROQ_KEY:
        return None
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": (
                        "You are a GoHighLevel expert. Answer with specific, actionable steps. "
                        "Include exact menu paths, button names, and settings. "
                        "If something changed recently, mention the old vs new way. "
                        "Be concise but thorough."
                    )},
                    {"role": "user", "content": f"{context}\n\nQuestion: {question}" if context else question}
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
            },
            timeout=30,
        )
        if r.ok:
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        log("GROQ", f"Error: {str(e)[:100]}")
    return None


def ask_gemini(question, context=""):
    """Ask Google Gemini (free tier)."""
    if not GOOGLE_KEY:
        return None
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_KEY}",
            json={
                "contents": [{"parts": [{"text": (
                    f"You are a GoHighLevel CRM expert. Answer with specific, actionable steps. "
                    f"Include exact menu paths, button names, and settings. "
                    f"If something changed recently, mention the old vs new way.\n\n"
                    f"{context}\n\nQuestion: {question}" if context else
                    f"You are a GoHighLevel CRM expert. Answer with specific, actionable steps.\n\n{question}"
                )}]}],
            },
            timeout=30,
        )
        if r.ok:
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        log("GEMINI", f"Error: {str(e)[:100]}")
    return None


def multi_ai_ask(question):
    """Ask multiple AIs and compare answers."""
    log("MULTI_AI", f"Asking: {question[:80]}...")

    # Gather context from our knowledge base
    context = ""
    summaries_dir = KB_DIR / "summaries"
    if summaries_dir.exists():
        for sf in list(summaries_dir.glob("*.md"))[:3]:
            content = sf.read_text(encoding="utf-8")
            if any(word in content.lower() for word in question.lower().split()):
                context += content[:1000] + "\n\n"

    answers = {}

    # Groq (Llama 70B)
    log("MULTI_AI", "  Asking Groq (Llama 70B)...")
    groq_answer = ask_groq(question, context)
    if groq_answer:
        answers["Groq (Llama 70B)"] = groq_answer
        log("MULTI_AI", f"  ✅ Groq: {len(groq_answer)} chars")

    time.sleep(1)

    # Gemini
    log("MULTI_AI", "  Asking Gemini 2.0 Flash...")
    gemini_answer = ask_gemini(question, context)
    if gemini_answer:
        answers["Gemini 2.0 Flash"] = gemini_answer
        log("MULTI_AI", f"  ✅ Gemini: {len(gemini_answer)} chars")

    if not answers:
        log("MULTI_AI", "  ❌ No AI responses")
        return None

    # Now synthesize — ask Groq to combine the best of both
    if len(answers) > 1:
        log("MULTI_AI", "  Synthesizing best answer...")
        combined = "\n\n---\n\n".join(f"**{name}:**\n{ans}" for name, ans in answers.items())
        synthesis = ask_groq(
            f"Two AI experts answered this GoHighLevel question: '{question}'\n\n"
            f"Their answers:\n{combined}\n\n"
            f"Synthesize the BEST answer combining both. Where they disagree, note both approaches. "
            f"Focus on what's most current and actionable. Be specific with menu paths and steps."
        )
        if synthesis:
            answers["Synthesized Best Answer"] = synthesis

    return answers


# ============================================================
# 4. RESEARCH TOPICS — What to research automatically
# ============================================================
AUTO_RESEARCH_TOPICS = [
    "GoHighLevel Voice AI setup outbound calling 2026",
    "GoHighLevel IVR workflow best practices",
    "GoHighLevel Conversation AI WhatsApp setup",
    "GoHighLevel workflow automation tips tricks",
    "GoHighLevel marketplace app development",
    "GoHighLevel API webhook integration",
    "GoHighLevel phone system call routing",
    "GoHighLevel AI builder workflow creation",
    "GoHighLevel membership site course setup",
    "GoHighLevel reputation management reviews",
]


# ============================================================
# 5. FULL RESEARCH CYCLE
# ============================================================
def run_full_research():
    """Run complete research cycle across all sources."""
    print("\n" + "=" * 60)
    print("  GHL Live Research — Full Cycle")
    print("=" * 60)

    all_intel = {
        "timestamp": datetime.now().isoformat(),
        "changelog": [],
        "reddit_hot": [],
        "reddit_search": [],
        "ai_answers": {},
    }

    # 1. Changelog
    print("\n  📋 Phase 1: GHL Changelog")
    print("  " + "-" * 50)
    entries = fetch_changelog()
    save_changelog(entries)
    all_intel["changelog"] = entries

    # 2. Reddit hot posts
    print("\n  🔥 Phase 2: Reddit Hot Posts")
    print("  " + "-" * 50)
    for sub in REDDIT_SUBREDDITS:
        hot = get_reddit_hot(sub, limit=10)
        all_intel["reddit_hot"].extend(hot)
        time.sleep(2)

    # Save Reddit intel
    today = datetime.now().strftime("%Y%m%d")
    reddit_file = REDDIT_DIR / f"reddit-hot-{today}.json"
    reddit_file.write_text(json.dumps(all_intel["reddit_hot"], indent=2))

    # 3. Multi-AI research on top 3 topics
    print("\n  🧠 Phase 3: Multi-AI Research")
    print("  " + "-" * 50)
    for topic in AUTO_RESEARCH_TOPICS[:3]:
        answers = multi_ai_ask(topic)
        if answers:
            all_intel["ai_answers"][topic] = answers
            # Save individual answer
            safe_name = re.sub(r'[^\w\s-]', '', topic)[:50].strip().replace(' ', '-')
            answer_file = AI_ANSWERS_DIR / f"{safe_name}-{today}.md"
            lines = [f"# {topic}\n\n*Researched: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"]
            for ai_name, answer in answers.items():
                lines.append(f"\n## {ai_name}\n\n{answer}\n")
            answer_file.write_text("\n".join(lines), encoding="utf-8")
        time.sleep(2)

    # Save full intel report
    intel_file = LIVE_DIR / f"intel-{today}.json"
    intel_file.write_text(json.dumps(all_intel, indent=2, default=str))

    # Print summary
    print(f"\n{'='*60}")
    print(f"  ✅ Research Complete!")
    print(f"  📋 Changelog entries: {len(all_intel['changelog'])}")
    print(f"  🔥 Reddit hot posts: {len(all_intel['reddit_hot'])}")
    print(f"  🧠 AI research topics: {len(all_intel['ai_answers'])}")
    print(f"  📁 Saved to: {LIVE_DIR}")
    print(f"{'='*60}")

    # Print latest changelog
    if entries:
        print(f"\n  📋 Latest GHL Changes:")
        for e in entries[:5]:
            print(f"    • {e['title']}")

    # Print top Reddit posts
    if all_intel["reddit_hot"]:
        print(f"\n  🔥 Top Reddit Discussions:")
        for p in all_intel["reddit_hot"][:5]:
            print(f"    • [{p.get('score', 0)}↑] {p['title'][:70]}")


# ============================================================
# MAIN
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ghl_live_research.py changelog          # Latest GHL changes")
        print("  python ghl_live_research.py reddit \"query\"      # Search Reddit")
        print("  python ghl_live_research.py hot                 # Reddit hot posts")
        print("  python ghl_live_research.py ask \"question\"      # Multi-AI answer")
        print("  python ghl_live_research.py full                # Full research cycle")
        return

    cmd = sys.argv[1].lower()

    if cmd == "changelog":
        entries = fetch_changelog()
        save_changelog(entries)
        if entries:
            print(f"\n  📋 Latest {len(entries)} GHL Changes:\n")
            for e in entries:
                print(f"  [{e.get('date', '')}] {e['title']}")
                if e.get("description"):
                    print(f"    {e['description'][:120]}")
                print()

    elif cmd == "reddit":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "workflow automation"
        results = search_reddit_all(query)
        if results:
            print(f"\n  🔍 Reddit results for '{query}':\n")
            for p in results[:10]:
                print(f"  [{p['score']}↑ | {p['num_comments']} comments] {p['title'][:70]}")
                if p.get("selftext"):
                    print(f"    {p['selftext'][:100]}...")
                print(f"    {p['url']}")
                print()
        else:
            print(f"  No Reddit results for '{query}'")

    elif cmd == "hot":
        for sub in REDDIT_SUBREDDITS:
            posts = get_reddit_hot(sub)
            if posts:
                print(f"\n  🔥 Hot on r/{sub}:\n")
                for p in posts[:10]:
                    print(f"  [{p['score']}↑] {p['title'][:70]}")
            time.sleep(1)

    elif cmd == "ask":
        question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "How to set up Voice AI in GoHighLevel?"
        answers = multi_ai_ask(question)
        if answers:
            print(f"\n  🧠 Multi-AI Answer: {question}\n")
            for ai_name, answer in answers.items():
                print(f"  {'='*50}")
                print(f"  {ai_name}:")
                print(f"  {'='*50}")
                print(f"  {answer[:1000]}")
                print()

    elif cmd == "full":
        run_full_research()

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
