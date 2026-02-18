"""
GHL Research Agent — Learns GoHighLevel Inside-Out
====================================================
A full-time research agent that:
1. Watches YouTube tutorials (extracts transcripts, no browser needed)
2. Reads GHL docs & support articles
3. Summarizes everything via free LLMs
4. Builds a searchable knowledge base
5. Maps out marketplace app opportunities

This agent runs continuously, building knowledge that makes us
know GHL better than their own support team.

USAGE:
    python ghl_research_agent.py learn          # Run full learning cycle
    python ghl_research_agent.py youtube         # Just YouTube transcripts
    python ghl_research_agent.py docs            # Just GHL docs
    python ghl_research_agent.py search "IVR"    # Search knowledge base
    python ghl_research_agent.py apps            # List app marketplace ideas
    python ghl_research_agent.py status          # Show what we've learned
"""

import os
import sys
import json
import time
import re
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
AGENT_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')

# Knowledge base paths
KB_DIR = AGENT_DIR / "ghl-knowledge"
KB_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPTS_DIR = KB_DIR / "youtube-transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR = KB_DIR / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
SUMMARIES_DIR = KB_DIR / "summaries"
SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
APPS_DIR = KB_DIR / "app-ideas"
APPS_DIR.mkdir(parents=True, exist_ok=True)

KB_INDEX = KB_DIR / "knowledge-index.json"
LEARNING_LOG = KB_DIR / "learning-log.json"

# API keys
GROQ_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")

# ============================================================
# YouTube Tutorial Sources — GHL channels & key videos
# ============================================================
GHL_YOUTUBE_SOURCES = {
    "playlists": [
        # Official & top GHL tutorial playlists
        "PL1hE_JByQxEpTseI_5oPTST2OnmnUDlh3",  # GoHighLevel Tutorials and Training
        "PL1Kb5YmNDjeyItGIyLFJ8bx5OW-HMmObX",  # GoHighLevel Tutorial For Beginners 2026
        "PLL31x9TXl_mIqWrLumeR1ueyFM6LYrD_W",  # GoHighLevel Automation Tutorials 2025
    ],
    "videos": [
        # Beginner tutorials
        "YMHJ9jvoKjY",  # GoHighLevel Tutorial for Beginners 2026 - Step by Step
        "DAxQA46e024",  # Ultimate GoHighLevel Guide 2026
        # IVR & Phone System
        "ZWfLg0ic3nM",  # GoHighLevel IVR System Setup
        # Voice AI
        "VvYCVfoYuMk",  # How to Use GoHighLevel AI Voice Agents: Ultimate 2025 Tutorial
        "TuAc-z5Dw5k",  # How to Use GoHighLevel AI Voice Agent (Full 2025 Tutorial)
        "bMi5JZBz5E4",  # NEW GoHighLevel Voice AI Widget (Sept 2025)
        "oIm1rx3RsXI",  # GoHighLevel Outbound Voice AI Beta
        "nPL0cZPHFxI",  # 2025's Best Voice AI for GoHighLevel: Assistable Ai
        # Marketplace App Development
        "wmoshlenptM",  # Build A GoHighLevel Marketplace App in 20 Minutes
        "2wDjPGsJGNk",  # Build A GoHighLevel App in 30 minutes
        "huevGw_mgYA",  # Watch this before you build a GHL marketplace app
        "PKUH0DMam6g",  # GoHighLevel App Marketplace - How to Install Apps
    ],
    "search_queries": [
        "GoHighLevel IVR setup tutorial",
        "GoHighLevel Voice AI agent setup",
        "GoHighLevel workflow automation tutorial",
        "GoHighLevel marketplace app development",
        "GoHighLevel API integration tutorial",
        "GoHighLevel phone system setup",
        "GoHighLevel conversation AI setup",
        "GoHighLevel WhatsApp integration",
        "GoHighLevel calendar booking setup",
        "GoHighLevel pipeline automation",
        "GoHighLevel custom values and fields",
        "GoHighLevel webhook automation",
        "GoHighLevel SMS marketing automation",
        "GoHighLevel email campaign setup",
        "GoHighLevel membership site setup",
        "GoHighLevel affiliate manager",
        "GoHighLevel social planner",
        "GoHighLevel reputation management",
        "GoHighLevel invoicing payments",
        "GoHighLevel communities setup",
    ],
}

# GHL Documentation URLs to scrape
GHL_DOC_URLS = [
    "https://help.gohighlevel.com/support/solutions/155000000049",  # App marketplace
    "https://marketplace.gohighlevel.com/docs/",  # API docs
    "https://help.gohighlevel.com/support/solutions/48000449585",  # Phone system
    "https://help.gohighlevel.com/support/solutions/48000449583",  # Conversations
    "https://help.gohighlevel.com/support/solutions/48000449587",  # Automation
    "https://help.gohighlevel.com/support/solutions/48000449589",  # Calendar
    "https://help.gohighlevel.com/support/solutions/48000449591",  # Payments
    "https://help.gohighlevel.com/support/solutions/48000449593",  # Membership
]


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


# ============================================================
# 1. YOUTUBE TRANSCRIPT EXTRACTOR
# ============================================================
def get_transcript(video_id):
    """Extract transcript from a YouTube video (free, no API key needed)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id)
        # Combine all text segments
        full_text = " ".join([entry.text for entry in transcript.snippets])
        return full_text
    except Exception as e:
        log("YT_ERROR", f"Video {video_id}: {str(e)[:100]}")
        return None


def get_video_info(video_id):
    """Get video title and metadata via YouTube oEmbed (free, no key)."""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            return {
                "title": data.get("title", "Unknown"),
                "author": data.get("author_name", "Unknown"),
            }
    except Exception:
        pass
    return {"title": "Unknown", "author": "Unknown"}


def search_youtube_videos(query, max_results=5):
    """Search YouTube for GHL tutorial videos (uses Google API key)."""
    if not GOOGLE_KEY:
        log("YT_SEARCH", "No GOOGLE_API_KEY, skipping search")
        return []

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "key": GOOGLE_KEY,
            "videoDuration": "medium",  # 4-20 min videos
            "order": "relevance",
        }
        r = requests.get(url, params=params, timeout=15)
        if r.ok:
            items = r.json().get("items", [])
            return [item["id"]["videoId"] for item in items]
        else:
            log("YT_SEARCH", f"API error: {r.status_code}")
    except Exception as e:
        log("YT_SEARCH", f"Error: {str(e)[:100]}")
    return []


def get_playlist_videos(playlist_id, max_results=20):
    """Get video IDs from a YouTube playlist."""
    if not GOOGLE_KEY:
        log("YT_PLAYLIST", "No GOOGLE_API_KEY, skipping playlist")
        return []

    try:
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            "part": "contentDetails",
            "playlistId": playlist_id,
            "maxResults": max_results,
            "key": GOOGLE_KEY,
        }
        r = requests.get(url, params=params, timeout=15)
        if r.ok:
            items = r.json().get("items", [])
            return [item["contentDetails"]["videoId"] for item in items]
    except Exception as e:
        log("YT_PLAYLIST", f"Error: {str(e)[:100]}")
    return []


def process_youtube_sources():
    """Process all YouTube sources — extract transcripts."""
    log("YOUTUBE", "Starting YouTube transcript extraction...")
    all_video_ids = set()

    # Direct videos
    all_video_ids.update(GHL_YOUTUBE_SOURCES["videos"])

    # Playlist videos
    for playlist_id in GHL_YOUTUBE_SOURCES["playlists"]:
        log("YOUTUBE", f"Fetching playlist: {playlist_id}")
        vids = get_playlist_videos(playlist_id)
        all_video_ids.update(vids)
        log("YOUTUBE", f"  Found {len(vids)} videos")
        time.sleep(1)

    # Search-based videos (first 3 queries to save quota)
    for query in GHL_YOUTUBE_SOURCES["search_queries"][:3]:
        log("YOUTUBE", f"Searching: {query}")
        vids = search_youtube_videos(query, max_results=3)
        all_video_ids.update(vids)
        time.sleep(1)

    log("YOUTUBE", f"Total unique videos to process: {len(all_video_ids)}")

    results = []
    for vid_id in all_video_ids:
        # Skip if already processed
        transcript_file = TRANSCRIPTS_DIR / f"{vid_id}.json"
        if transcript_file.exists():
            log("YOUTUBE", f"  Already have: {vid_id}")
            results.append(json.loads(transcript_file.read_text()))
            continue

        info = get_video_info(vid_id)
        log("YOUTUBE", f"  Processing: {info['title'][:60]}...")

        transcript = get_transcript(vid_id)
        if transcript:
            entry = {
                "video_id": vid_id,
                "title": info["title"],
                "author": info["author"],
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "transcript_length": len(transcript),
                "transcript": transcript,
                "extracted_at": datetime.now().isoformat(),
            }
            transcript_file.write_text(json.dumps(entry, indent=2))
            results.append(entry)
            log("YOUTUBE", f"    ✅ {len(transcript)} chars")
        else:
            log("YOUTUBE", f"    ⚠️ No transcript available")

        time.sleep(0.5)  # rate limit

    log("YOUTUBE", f"Done! {len(results)} transcripts extracted")
    return results


# ============================================================
# 2. LLM SUMMARIZER — Uses free Groq to summarize content
# ============================================================
def summarize_with_llm(text, prompt_prefix, max_input=6000):
    """Summarize text using Groq (free, fast)."""
    if not GROQ_KEY:
        log("LLM", "No GROQ_API_KEY, skipping summarization")
        return None

    # Truncate if too long
    if len(text) > max_input:
        text = text[:max_input] + "... [truncated]"

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": (
                        "You are a GoHighLevel expert analyst. Extract actionable knowledge "
                        "from content. Focus on: features, setup steps, API capabilities, "
                        "automation possibilities, and things that could be built as marketplace apps. "
                        "Be specific and practical. Use bullet points."
                    )},
                    {"role": "user", "content": f"{prompt_prefix}\n\n{text}"}
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
            },
            timeout=30,
        )
        if r.ok:
            return r.json()["choices"][0]["message"]["content"]
        else:
            log("LLM", f"Error: {r.status_code} {r.text[:100]}")
    except Exception as e:
        log("LLM", f"Error: {str(e)[:100]}")
    return None


def summarize_transcripts():
    """Summarize all YouTube transcripts into actionable knowledge."""
    log("SUMMARIZE", "Summarizing transcripts...")
    transcript_files = list(TRANSCRIPTS_DIR.glob("*.json"))

    for tf in transcript_files:
        summary_file = SUMMARIES_DIR / f"yt-{tf.stem}.md"
        if summary_file.exists():
            continue

        data = json.loads(tf.read_text())
        title = data.get("title", "Unknown")
        transcript = data.get("transcript", "")

        if not transcript or len(transcript) < 100:
            continue

        log("SUMMARIZE", f"  Summarizing: {title[:50]}...")
        summary = summarize_with_llm(
            transcript,
            f"Summarize this GoHighLevel tutorial video titled '{title}'. "
            f"Extract: key features shown, step-by-step setup instructions, "
            f"API/automation capabilities mentioned, and potential marketplace app ideas."
        )

        if summary:
            content = f"# {title}\n\n**Source:** {data.get('url', '')}\n**Author:** {data.get('author', '')}\n\n{summary}\n"
            summary_file.write_text(content, encoding="utf-8")
            log("SUMMARIZE", f"    ✅ Saved summary")
        else:
            log("SUMMARIZE", f"    ⚠️ Failed to summarize")

        time.sleep(2)  # rate limit


# ============================================================
# 3. KNOWLEDGE BASE — Search & retrieve
# ============================================================
def build_index():
    """Build searchable index of all knowledge."""
    index = {
        "built_at": datetime.now().isoformat(),
        "transcripts": [],
        "summaries": [],
        "topics": {},
    }

    # Index transcripts
    for tf in TRANSCRIPTS_DIR.glob("*.json"):
        data = json.loads(tf.read_text())
        index["transcripts"].append({
            "file": tf.name,
            "title": data.get("title", ""),
            "video_id": data.get("video_id", ""),
            "length": data.get("transcript_length", 0),
        })

    # Index summaries
    for sf in SUMMARIES_DIR.glob("*.md"):
        content = sf.read_text(encoding="utf-8")
        index["summaries"].append({
            "file": sf.name,
            "title": content.split("\n")[0].replace("# ", ""),
            "length": len(content),
        })

        # Extract topics
        for keyword in ["IVR", "Voice AI", "Workflow", "Pipeline", "Calendar",
                        "SMS", "Email", "WhatsApp", "Phone", "Conversation AI",
                        "Membership", "Payment", "Invoice", "Webhook", "API",
                        "Marketplace", "Custom Field", "Custom Value", "Trigger",
                        "Automation", "Funnel", "Website", "Blog", "Social",
                        "Reputation", "Review", "Affiliate", "Community"]:
            if keyword.lower() in content.lower():
                index["topics"].setdefault(keyword, []).append(sf.name)

    KB_INDEX.write_text(json.dumps(index, indent=2))
    log("INDEX", f"Built index: {len(index['transcripts'])} transcripts, {len(index['summaries'])} summaries, {len(index['topics'])} topics")
    return index


def search_knowledge(query):
    """Search the knowledge base for a topic."""
    query_lower = query.lower()
    results = []

    for sf in SUMMARIES_DIR.glob("*.md"):
        content = sf.read_text(encoding="utf-8")
        if query_lower in content.lower():
            # Find matching lines
            matches = [line.strip() for line in content.split("\n")
                       if query_lower in line.lower() and line.strip()]
            results.append({
                "file": sf.name,
                "title": content.split("\n")[0].replace("# ", ""),
                "matches": matches[:5],
            })

    return results


# ============================================================
# 4. APP MARKETPLACE IDEAS GENERATOR
# ============================================================
def generate_app_ideas():
    """Analyze knowledge base and generate marketplace app ideas."""
    log("APPS", "Generating marketplace app ideas from knowledge...")

    # Gather all summaries
    all_knowledge = []
    for sf in SUMMARIES_DIR.glob("*.md"):
        all_knowledge.append(sf.read_text(encoding="utf-8"))

    if not all_knowledge:
        log("APPS", "No summaries yet — run 'learn' first")
        return

    combined = "\n\n---\n\n".join(all_knowledge[:10])  # First 10 summaries

    ideas = summarize_with_llm(
        combined,
        "Based on this GoHighLevel knowledge, suggest 10 specific marketplace apps "
        "that Exposure Solutions could build and sell. For each app:\n"
        "1. App name\n"
        "2. What it does (one sentence)\n"
        "3. Target user (agency, sub-account, or both)\n"
        "4. Pricing model (free, subscription $X/mo, usage-based)\n"
        "5. Technical complexity (easy/medium/hard)\n"
        "6. Revenue potential (low/medium/high)\n"
        "7. What GHL APIs it would use\n\n"
        "Focus on apps that solve real pain points for GHL agencies. "
        "Consider: AI-powered features, automation templates, reporting, "
        "integrations with external services, and tools that save time."
    )

    if ideas:
        ideas_file = APPS_DIR / f"app-ideas-{datetime.now().strftime('%Y%m%d')}.md"
        content = f"# GHL Marketplace App Ideas\n\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{ideas}\n"
        ideas_file.write_text(content, encoding="utf-8")
        log("APPS", f"✅ Saved app ideas → {ideas_file.name}")
        print(f"\n{ideas}")
    else:
        log("APPS", "Failed to generate ideas")


# ============================================================
# 5. LEARNING LOG — Track what we've learned
# ============================================================
def update_learning_log(action, details):
    """Track learning progress."""
    log_data = []
    if LEARNING_LOG.exists():
        log_data = json.loads(LEARNING_LOG.read_text())

    log_data.append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details,
    })

    LEARNING_LOG.write_text(json.dumps(log_data, indent=2))


def show_status():
    """Show current knowledge base status."""
    print("\n" + "=" * 60)
    print("  GHL Research Agent — Knowledge Status")
    print("=" * 60)

    transcripts = list(TRANSCRIPTS_DIR.glob("*.json"))
    summaries = list(SUMMARIES_DIR.glob("*.md"))
    app_ideas = list(APPS_DIR.glob("*.md"))

    print(f"\n  📹 YouTube Transcripts: {len(transcripts)}")
    print(f"  📝 Summaries: {len(summaries)}")
    print(f"  💡 App Idea Files: {len(app_ideas)}")

    if KB_INDEX.exists():
        index = json.loads(KB_INDEX.read_text())
        topics = index.get("topics", {})
        print(f"  🏷️  Topics indexed: {len(topics)}")
        if topics:
            print(f"\n  Top topics:")
            sorted_topics = sorted(topics.items(), key=lambda x: len(x[1]), reverse=True)
            for topic, files in sorted_topics[:10]:
                print(f"    {topic}: {len(files)} sources")

    total_chars = sum(
        json.loads(f.read_text()).get("transcript_length", 0)
        for f in transcripts
    )
    print(f"\n  📊 Total transcript content: {total_chars:,} characters")
    print(f"     (~{total_chars // 4000} pages of knowledge)")

    if LEARNING_LOG.exists():
        log_data = json.loads(LEARNING_LOG.read_text())
        if log_data:
            last = log_data[-1]
            print(f"\n  🕐 Last learning session: {last['timestamp'][:16]}")
            print(f"     Action: {last['action']}")

    print(f"\n{'='*60}")


# ============================================================
# MAIN
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ghl_research_agent.py learn      # Full learning cycle")
        print("  python ghl_research_agent.py youtube     # YouTube transcripts only")
        print("  python ghl_research_agent.py summarize   # Summarize transcripts")
        print("  python ghl_research_agent.py search X    # Search knowledge base")
        print("  python ghl_research_agent.py apps        # Generate app ideas")
        print("  python ghl_research_agent.py status      # Show status")
        return

    cmd = sys.argv[1].lower()

    if cmd == "learn":
        print("\n" + "=" * 60)
        print("  GHL Research Agent — Full Learning Cycle")
        print("=" * 60)

        # Phase 1: YouTube
        transcripts = process_youtube_sources()
        update_learning_log("youtube", f"Extracted {len(transcripts)} transcripts")

        # Phase 2: Summarize
        summarize_transcripts()
        update_learning_log("summarize", "Summarized all transcripts")

        # Phase 3: Build index
        build_index()
        update_learning_log("index", "Built knowledge index")

        # Phase 4: Generate app ideas
        generate_app_ideas()
        update_learning_log("apps", "Generated marketplace app ideas")

        show_status()

    elif cmd == "youtube":
        transcripts = process_youtube_sources()
        update_learning_log("youtube", f"Extracted {len(transcripts)} transcripts")

    elif cmd == "summarize":
        summarize_transcripts()
        build_index()
        update_learning_log("summarize", "Summarized and indexed")

    elif cmd == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not query:
            print("Usage: python ghl_research_agent.py search <query>")
            return
        results = search_knowledge(query)
        if results:
            print(f"\n  Found {len(results)} results for '{query}':\n")
            for r in results:
                print(f"  📄 {r['title']}")
                for m in r['matches'][:3]:
                    print(f"     → {m[:100]}")
                print()
        else:
            print(f"  No results for '{query}'. Run 'learn' first to build knowledge.")

    elif cmd == "apps":
        generate_app_ideas()

    elif cmd == "status":
        show_status()

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
