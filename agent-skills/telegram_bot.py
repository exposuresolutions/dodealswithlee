"""
Lilly Telegram Bot — Mobile Command Center
=============================================
Professional Telegram bot using python-telegram-bot library.
Inline keyboards, rich formatting, voice messages, GHL integration.

SETUP (one-time, 2 minutes):
1. Open Telegram, search @BotFather
2. Send: /newbot
3. Name: Lilly DDWL
4. Username: lilly_ddwl_bot (or similar)
5. Copy the token, paste into .env as TELEGRAM_BOT_TOKEN
6. Run: python telegram_bot.py
7. Open your bot in Telegram, send /start
"""

import os
import sys
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)
from telegram.constants import ParseMode, ChatAction

BASE_DIR = Path(__file__).parent.parent
AGENT_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_DIR))

# Load env
env_file = BASE_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
GHL_API_KEY = os.environ.get("GHL_API_KEY", "")
GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID", "KbiucErIMNPbO1mY4qXL")
GHL_API_BASE = "https://services.leadconnectorhq.com"
GHL_API_HEADERS = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Version": "2021-07-28",
}

logging.basicConfig(format="  [%(asctime)s] %(message)s", datefmt="%H:%M:%S", level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# GHL API
# ============================================================
def ghl_get(endpoint, params=None):
    if params is None:
        params = {}
    params.setdefault("locationId", GHL_LOCATION_ID)
    try:
        r = requests.get(f"{GHL_API_BASE}{endpoint}", headers=GHL_API_HEADERS, params=params, timeout=15)
        return r.json() if r.status_code == 200 else {"error": r.text[:200]}
    except Exception as e:
        return {"error": str(e)[:200]}


# ============================================================
# HELPERS
# ============================================================
def escape_md(text):
    """Escape MarkdownV2 special characters."""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in chars:
        text = text.replace(c, f'\\{c}')
    return text


async def safe_reply(update, text, reply_markup=None, parse_mode=ParseMode.HTML):
    """Send message with auto-chunking and error fallback."""
    try:
        if len(text) > 4000:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for chunk in chunks:
                await update.effective_message.reply_text(
                    chunk, parse_mode=parse_mode, reply_markup=reply_markup,
                    disable_web_page_preview=True,
                )
        else:
            await update.effective_message.reply_text(
                text, parse_mode=parse_mode, reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
    except Exception:
        # Fallback: send without formatting
        await update.effective_message.reply_text(
            text.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<code>', '').replace('</code>', ''),
            reply_markup=reply_markup,
        )


# ============================================================
# /start — Welcome with main menu
# ============================================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("⚡ Workflows", callback_data="workflows"),
        ],
        [
            InlineKeyboardButton("📋 Contacts", callback_data="contacts"),
            InlineKeyboardButton("🎯 Pipelines", callback_data="pipelines"),
        ],
        [
            InlineKeyboardButton("🔥 Reddit", callback_data="reddit"),
            InlineKeyboardButton("📋 Changelog", callback_data="changelog"),
        ],
        [
            InlineKeyboardButton("🧠 Research", callback_data="research"),
            InlineKeyboardButton("🎤 Voice Test", callback_data="voice_test"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome = (
        f"👋 <b>Hey {user.first_name}!</b>\n\n"
        f"I'm <b>Lilly</b> — your DDWL command center.\n"
        f"I manage GoHighLevel, research GHL updates,\n"
        f"and can speak in Lee's voice.\n\n"
        f"<b>Tap a button or type anything:</b>"
    )
    await safe_reply(update, welcome, reply_markup=reply_markup)
    logger.info(f"START from {user.first_name} ({user.id})")


# ============================================================
# /status — System dashboard
# ============================================================
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_action(ChatAction.TYPING)

    lines = ["<b>📊 DDWL System Dashboard</b>\n"]
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Workflows
    data = ghl_get("/workflows/")
    if "workflows" in data:
        wf = data["workflows"]
        pub = sum(1 for w in wf if w.get("status") == "published")
        draft = len(wf) - pub
        lines.append(f"\n⚡ <b>Workflows:</b> {len(wf)} total")
        lines.append(f"   ✅ {pub} published  •  📝 {draft} draft")

    # Contacts
    data = ghl_get("/contacts/", {"limit": 1})
    if "meta" in data:
        lines.append(f"\n📋 <b>Contacts:</b> {data['meta'].get('total', '?')}")
    elif "contacts" in data:
        lines.append(f"\n📋 <b>Contacts:</b> loaded")

    # Pipelines
    data = ghl_get("/opportunities/pipelines")
    if "pipelines" in data:
        pipes = data["pipelines"]
        lines.append(f"\n🎯 <b>Pipelines:</b> {len(pipes)}")
        for p in pipes[:3]:
            stages = len(p.get("stages", []))
            lines.append(f"   • {p['name']} ({stages} stages)")

    # Calendars
    data = ghl_get("/calendars/")
    if "calendars" in data:
        lines.append(f"\n📅 <b>Calendars:</b> {len(data['calendars'])}")

    # Knowledge base
    kb_dir = AGENT_DIR / "ghl-knowledge"
    if kb_dir.exists():
        transcripts = len(list((kb_dir / "youtube-transcripts").glob("*.json"))) if (kb_dir / "youtube-transcripts").exists() else 0
        summaries = len(list((kb_dir / "summaries").glob("*.md"))) if (kb_dir / "summaries").exists() else 0
        reddit_files = len(list((kb_dir / "reddit").glob("*.json"))) if (kb_dir / "reddit").exists() else 0
        lines.append(f"\n🧠 <b>Knowledge Base:</b>")
        lines.append(f"   📹 {transcripts} transcripts  •  📝 {summaries} summaries")
        if reddit_files:
            lines.append(f"   🔥 {reddit_files} Reddit snapshots")

    lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🕐 <i>{datetime.now().strftime('%H:%M  •  %d %b %Y')}</i>")

    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="status"),
            InlineKeyboardButton("⚡ Workflows", callback_data="workflows"),
        ],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="start")],
    ]
    await safe_reply(update, "\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))


# ============================================================
# /workflows — List with status icons
# ============================================================
async def cmd_workflows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_action(ChatAction.TYPING)
    data = ghl_get("/workflows/")
    if "workflows" not in data:
        await safe_reply(update, f"❌ Error: {data.get('error', 'Unknown')}")
        return

    wf = data["workflows"]
    pub = [w for w in wf if w.get("status") == "published"]
    draft = [w for w in wf if w.get("status") != "published"]

    lines = [f"<b>⚡ {len(wf)} Workflows</b>\n"]

    if pub:
        lines.append("<b>✅ Published:</b>")
        for w in pub:
            lines.append(f"  • {w['name']}")

    if draft:
        lines.append(f"\n<b>📝 Draft:</b>")
        for w in draft:
            lines.append(f"  • {w['name']}")

    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("🏠 Menu", callback_data="start"),
        ],
    ]
    await safe_reply(update, "\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))


# ============================================================
# /contacts — Recent contacts
# ============================================================
async def cmd_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_action(ChatAction.TYPING)
    data = ghl_get("/contacts/", {"limit": 10})
    if "contacts" not in data:
        await safe_reply(update, f"❌ Error: {data.get('error', 'Unknown')}")
        return

    contacts = data["contacts"]
    lines = [f"<b>📋 Latest {len(contacts)} Contacts</b>\n"]
    for c in contacts[:10]:
        name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() or "Unknown"
        phone = c.get("phone", "—")
        tags = ", ".join(c.get("tags", [])[:2]) or "—"
        lines.append(f"  <b>{name}</b>")
        lines.append(f"  📱 {phone}  •  🏷 <i>{tags}</i>\n")

    keyboard = [[InlineKeyboardButton("📊 Status", callback_data="status"), InlineKeyboardButton("🏠 Menu", callback_data="start")]]
    await safe_reply(update, "\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))


# ============================================================
# /research — Reddit + Changelog
# ============================================================
async def cmd_research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_action(ChatAction.TYPING)
    await safe_reply(update, "🔍 <b>Running research...</b>\n<i>Reddit + GHL Changelog</i>")

    try:
        from ghl_live_research import get_reddit_hot, fetch_changelog, save_changelog

        parts = []

        # Reddit
        posts = get_reddit_hot("gohighlevel", limit=5)
        if posts:
            lines = ["<b>🔥 Hot on r/gohighlevel</b>\n"]
            for p in posts[:5]:
                score = p.get('score', 0)
                lines.append(f"  <b>{score}↑</b>  {p['title'][:55]}")
            parts.append("\n".join(lines))

        # Changelog
        entries = fetch_changelog()
        if entries:
            save_changelog(entries)
            lines = ["\n<b>📋 Latest GHL Changes</b>\n"]
            for e in entries[:5]:
                lines.append(f"  • {e['title'][:55]}")
            parts.append("\n".join(lines))

        if parts:
            await safe_reply(update, "\n\n".join(parts))
        else:
            await safe_reply(update, "No new data found.")
    except Exception as e:
        await safe_reply(update, f"❌ Research error: {str(e)[:200]}")


# ============================================================
# /ask — Multi-AI answer
# ============================================================
async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = " ".join(context.args) if context.args else ""
    if not question:
        await safe_reply(update, "💡 <b>Usage:</b> <code>/ask your question here</code>\n\n<i>Example: /ask how to set up Voice AI outbound calling</i>")
        return

    await update.effective_chat.send_action(ChatAction.TYPING)
    await safe_reply(update, f"🧠 <b>Researching:</b> <i>{question}</i>\n\n<i>Asking Groq + Gemini...</i>")

    try:
        from ghl_live_research import multi_ai_ask
        answers = multi_ai_ask(question)
        if answers:
            if "Synthesized Best Answer" in answers:
                text = f"<b>🧠 Best Answer</b>\n\n{answers['Synthesized Best Answer'][:3500]}"
            else:
                name, answer = next(iter(answers.items()))
                text = f"<b>🧠 {name}</b>\n\n{answer[:3500]}"
            await safe_reply(update, text)
        else:
            await safe_reply(update, "❌ No AI responses received.")
    except Exception as e:
        await safe_reply(update, f"❌ Error: {str(e)[:200]}")


# ============================================================
# /say — Lee's voice
# ============================================================
async def cmd_say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await safe_reply(update, "🎤 <b>Usage:</b> <code>/say your text here</code>\n\n<i>I'll say it in Lee's voice!</i>")
        return

    await update.effective_chat.send_action(ChatAction.RECORD_VOICE)

    try:
        from voice_review import speak
        audio_path = speak(text, play=False)
        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f:
                await update.effective_message.reply_voice(
                    voice=f,
                    caption=f"🎤 <i>{text[:100]}</i>",
                    parse_mode=ParseMode.HTML,
                )
            logger.info(f"Voice sent: {text[:50]}")
        else:
            await safe_reply(update, f"🔇 Voice generation failed.\n<i>{text}</i>")
    except Exception as e:
        await safe_reply(update, f"❌ Voice error: {str(e)[:200]}")


# ============================================================
# /do — Execute GHL task
# ============================================================
async def cmd_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = " ".join(context.args) if context.args else ""
    if not task:
        await safe_reply(update, "⚙️ <b>Usage:</b> <code>/do your task here</code>\n\n<i>Example: /do show all pipelines</i>")
        return

    await update.effective_chat.send_action(ChatAction.TYPING)

    try:
        from ghl_doer import classify_task, execute_api_task, format_result

        classification = classify_task(task)
        action = classification.get("action", "")
        task_type = classification.get("type", "")

        if task_type == "api":
            result = execute_api_task(classification)
            output = format_result(result, action)
            await safe_reply(update, f"<b>✅ {action}</b>\n\n{output[:3500]}")
        else:
            explanation = classification.get('explanation', '')
            text = (
                f"🖥️ <b>Browser task: {action}</b>\n\n"
                f"<i>{explanation}</i>\n\n"
                f"Run on PC:\n<code>python ghl_doer.py \"{task}\"</code>"
            )
            await safe_reply(update, text)
    except Exception as e:
        await safe_reply(update, f"❌ Error: {str(e)[:200]}")


# ============================================================
# /reddit — Search Reddit
# ============================================================
async def cmd_reddit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else ""
    await update.effective_chat.send_action(ChatAction.TYPING)

    try:
        from ghl_live_research import search_reddit_all, get_reddit_hot

        if query:
            posts = search_reddit_all(query, limit=8)
            title = f"Reddit: '{query}'"
        else:
            posts = get_reddit_hot("gohighlevel", limit=8)
            title = "Hot on r/gohighlevel"

        if posts:
            lines = [f"<b>🔥 {title}</b>\n"]
            for p in posts[:8]:
                score = p.get('score', 0)
                comments = p.get('num_comments', 0)
                lines.append(f"  <b>{score}↑</b> • {comments}💬  {p['title'][:50]}")
            await safe_reply(update, "\n".join(lines))
        else:
            await safe_reply(update, f"No Reddit results for '{query}'")
    except Exception as e:
        await safe_reply(update, f"❌ Error: {str(e)[:200]}")


# ============================================================
# CALLBACK HANDLER — Inline keyboard buttons
# ============================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    action = query.data
    logger.info(f"Button: {action}")

    if action == "start":
        await cmd_start(update, context)
    elif action == "status":
        await cmd_status(update, context)
    elif action == "workflows":
        await cmd_workflows(update, context)
    elif action == "contacts":
        await cmd_contacts(update, context)
    elif action == "pipelines":
        # Quick pipelines view
        await update.effective_chat.send_action(ChatAction.TYPING)
        data = ghl_get("/opportunities/pipelines")
        if "pipelines" in data:
            lines = ["<b>🎯 Pipelines</b>\n"]
            for p in data["pipelines"]:
                stages = [s["name"] for s in p.get("stages", [])]
                lines.append(f"<b>{p['name']}</b>")
                lines.append(f"  Stages: {' → '.join(stages)}\n")
            keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="start")]]
            await safe_reply(update, "\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await safe_reply(update, "❌ Could not load pipelines")
    elif action == "reddit":
        await cmd_reddit(update, context)
    elif action == "changelog":
        await update.effective_chat.send_action(ChatAction.TYPING)
        try:
            from ghl_live_research import fetch_changelog
            entries = fetch_changelog()
            if entries:
                lines = ["<b>📋 GHL Changelog</b>\n"]
                for e in entries[:8]:
                    date = e.get('date', '')[:16] if e.get('date') else ''
                    lines.append(f"  <b>•</b> {e['title'][:55]}")
                    if date:
                        lines.append(f"    <i>{date}</i>")
                keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="start")]]
                await safe_reply(update, "\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await safe_reply(update, "No changelog entries found.")
        except Exception as e:
            await safe_reply(update, f"❌ Error: {str(e)[:200]}")
    elif action == "research":
        await cmd_research(update, context)
    elif action == "voice_test":
        await update.effective_chat.send_action(ChatAction.RECORD_VOICE)
        try:
            from voice_review import speak
            audio_path = speak("Hey, this is Lee A.I. checking in. All systems running smooth. Hit me up if you need anything.", play=False)
            if audio_path and Path(audio_path).exists():
                with open(audio_path, "rb") as f:
                    await update.effective_message.reply_voice(
                        voice=f,
                        caption="🎤 <i>Lee AI voice test</i>",
                        parse_mode=ParseMode.HTML,
                    )
        except Exception as e:
            await safe_reply(update, f"❌ Voice error: {str(e)[:200]}")


# ============================================================
# VOICE MESSAGE — Speech-to-text → process → talk back
# ============================================================
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive voice message, transcribe with Groq Whisper, process, respond in Lee's voice."""
    user = update.effective_user
    logger.info(f"Voice message from {user.first_name}")

    await update.effective_chat.send_action(ChatAction.TYPING)

    # 1. Download the voice file
    voice = update.message.voice or update.message.audio
    if not voice:
        await safe_reply(update, "Could not read voice message.")
        return

    voice_file = await context.bot.get_file(voice.file_id)
    voice_path = AGENT_DIR / "voice-input" / f"voice-{int(time.time())}.ogg"
    voice_path.parent.mkdir(parents=True, exist_ok=True)
    await voice_file.download_to_drive(str(voice_path))
    logger.info(f"Voice downloaded: {voice_path.name} ({voice.file_size} bytes)")

    # 2. Transcribe with Groq Whisper (FREE)
    transcript = await transcribe_voice(voice_path)
    if not transcript:
        await safe_reply(update, "🎤 Couldn't transcribe your voice message. Try again?")
        return

    await safe_reply(update, f"🎤 <i>I heard:</i> <b>{transcript}</b>")
    logger.info(f"Transcribed: {transcript}")

    # 3. Process as text command
    context.args = transcript.split()
    text_lower = transcript.lower().strip()

    # Route the transcribed text
    if any(w in text_lower for w in ["status", "how are", "what's up", "overview", "dashboard"]):
        await cmd_status(update, context)
    elif any(w in text_lower for w in ["workflow", "automation"]):
        await cmd_workflows(update, context)
    elif any(w in text_lower for w in ["contact", "lead", "people"]):
        await cmd_contacts(update, context)
    elif any(w in text_lower for w in ["research", "what's new", "changelog", "update"]):
        await cmd_research(update, context)
    elif text_lower.startswith("say "):
        context.args = transcript[4:].strip().split()
        await cmd_say(update, context)
    elif text_lower.startswith("ask "):
        context.args = transcript[4:].strip().split()
        await cmd_ask(update, context)
    else:
        # For voice commands, generate a voice response too
        await cmd_do(update, context)

    # 4. Generate voice response summary
    try:
        from voice_review import speak
        response_text = f"Got it. I processed your request: {transcript[:80]}."
        audio_path = speak(response_text, play=False)
        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f:
                await update.effective_message.reply_voice(
                    voice=f,
                    caption="🎤 <i>Lee AI response</i>",
                    parse_mode=ParseMode.HTML,
                )
    except Exception as e:
        logger.warning(f"Voice response failed: {e}")


async def transcribe_voice(audio_path):
    """Transcribe audio using Groq Whisper API (free)."""
    if not GROQ_KEY:
        logger.warning("No GROQ_API_KEY for transcription")
        return None

    try:
        with open(audio_path, "rb") as f:
            r = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_KEY}"},
                files={"file": (audio_path.name, f, "audio/ogg")},
                data={"model": "whisper-large-v3-turbo", "language": "en"},
                timeout=30,
            )
        if r.ok:
            return r.json().get("text", "").strip()
        else:
            logger.error(f"Whisper error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logger.error(f"Transcription error: {e}")
    return None


# ============================================================
# SCOUT AGENT — Trends, News, Morning Brief
# ============================================================
async def cmd_trends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch trending news across all DDWL topics."""
    await update.effective_chat.send_action(ChatAction.TYPING)
    await safe_reply(update, "🔍 <b>Scout is scanning trends...</b>\n<i>Google News + Groq analysis</i>")
    try:
        from xai_scout import get_trending
        result = get_trending()
        if result:
            await safe_reply(update, result, parse_mode=None)
        else:
            await safe_reply(update, "❌ No trends found.")
    except Exception as e:
        await safe_reply(update, f"❌ Scout error: {str(e)[:200]}")


async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search Google News for a topic."""
    query = " ".join(context.args) if context.args else "real estate wholesaling"
    await update.effective_chat.send_action(ChatAction.TYPING)
    await safe_reply(update, f"📰 <b>Scout searching news:</b> <i>{query}</i>")
    try:
        from xai_scout import search_news
        result = search_news(query)
        if result:
            await safe_reply(update, result, parse_mode=None)
        else:
            await safe_reply(update, "❌ No news found.")
    except Exception as e:
        await safe_reply(update, f"❌ Scout error: {str(e)[:200]}")


async def cmd_brief(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a full morning brief."""
    await update.effective_chat.send_action(ChatAction.TYPING)
    await safe_reply(update, "☀️ <b>Scout generating morning brief...</b>\n<i>This takes 15-30 seconds</i>")
    try:
        from xai_scout import generate_morning_brief
        result = generate_morning_brief()
        if result:
            await safe_reply(update, result, parse_mode=None)
        else:
            await safe_reply(update, "❌ Brief generation failed.")
    except Exception as e:
        await safe_reply(update, f"❌ Scout error: {str(e)[:200]}")


# ============================================================
# NATURAL LANGUAGE — Plain text messages
# ============================================================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    text_lower = text.lower()
    logger.info(f"Text from {update.effective_user.first_name}: {text[:80]}")

    # Pattern match common intents
    if any(w in text_lower for w in ["status", "how are", "what's up", "overview", "dashboard"]):
        await cmd_status(update, context)
    elif any(w in text_lower for w in ["workflow", "automation"]):
        await cmd_workflows(update, context)
    elif any(w in text_lower for w in ["contact", "lead", "people"]):
        await cmd_contacts(update, context)
    elif any(w in text_lower for w in ["reddit", "community", "forum"]):
        context.args = text_lower.replace("reddit", "").strip().split() or []
        await cmd_reddit(update, context)
    elif any(w in text_lower for w in ["research", "what's new", "changelog", "update"]):
        await cmd_research(update, context)
    elif any(w in text_lower for w in ["trends", "trending", "what's hot", "what's happening"]):
        await cmd_trends(update, context)
    elif any(w in text_lower for w in ["brief", "morning brief", "daily brief", "briefing"]):
        await cmd_brief(update, context)
    elif text_lower.startswith("news "):
        context.args = text[5:].strip().split()
        await cmd_news(update, context)
    elif text_lower.startswith("say "):
        context.args = text[4:].strip().split()
        await cmd_say(update, context)
    elif text_lower.startswith("ask "):
        context.args = text[4:].strip().split()
        await cmd_ask(update, context)
    else:
        # Route to doer agent
        context.args = text.split()
        await cmd_do(update, context)


# ============================================================
# MAIN
# ============================================================
async def post_init(application):
    """Set bot commands for the menu button."""
    commands = [
        BotCommand("start", "Main menu"),
        BotCommand("status", "GHL system dashboard"),
        BotCommand("workflows", "List all workflows"),
        BotCommand("contacts", "Recent contacts"),
        BotCommand("research", "Reddit + Changelog scan"),
        BotCommand("reddit", "Search GHL Reddit"),
        BotCommand("ask", "Multi-AI GHL answer"),
        BotCommand("say", "Lee's voice says it"),
        BotCommand("do", "Execute GHL task"),
        BotCommand("trends", "Trending news (Scout)"),
        BotCommand("news", "Search news (Scout)"),
        BotCommand("brief", "Morning brief (Scout)"),
    ]
    await application.bot.set_my_commands(commands)
    me = await application.bot.get_me()
    logger.info(f"✅ Bot online: @{me.username}")


def main():
    if not TELEGRAM_TOKEN:
        print("\n  ❌ TELEGRAM_BOT_TOKEN not set in .env")
        print("\n  Setup (60 seconds):")
        print("  1. Open Telegram → search @BotFather")
        print("  2. Send /newbot")
        print("  3. Name: Lilly DDWL")
        print("  4. Username: lilly_ddwl_bot")
        print("  5. Copy token → add to .env:")
        print("     TELEGRAM_BOT_TOKEN=your_token_here")
        print("  6. Run this script again")
        return

    print("\n" + "=" * 60)
    print("  🤖 Lilly Telegram Bot — Starting...")
    print("=" * 60)

    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).job_queue(None).build()

    # Command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("workflows", cmd_workflows))
    app.add_handler(CommandHandler("wf", cmd_workflows))
    app.add_handler(CommandHandler("contacts", cmd_contacts))
    app.add_handler(CommandHandler("c", cmd_contacts))
    app.add_handler(CommandHandler("research", cmd_research))
    app.add_handler(CommandHandler("r", cmd_research))
    app.add_handler(CommandHandler("reddit", cmd_reddit))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CommandHandler("say", cmd_say))
    app.add_handler(CommandHandler("do", cmd_do))
    app.add_handler(CommandHandler("trends", cmd_trends))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("brief", cmd_brief))

    # Inline keyboard callback
    app.add_handler(CallbackQueryHandler(button_handler))

    # Plain text — natural language
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Voice messages — speech-to-text → process → talk back
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    # Start polling
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
