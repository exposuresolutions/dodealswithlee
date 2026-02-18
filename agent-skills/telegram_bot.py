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
import asyncio
import subprocess
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

# Admin Telegram user IDs — only these users can run server commands
ADMIN_IDS = {1399744360}  # Daniel Gallagher
DDWL_DIR = Path.home() / "ddwl"


def is_admin(update: Update) -> bool:
    return update.effective_user.id in ADMIN_IDS


async def deny_access(update: Update):
    await safe_reply(update, "🔒 <b>Access denied.</b>\n<i>Server commands are admin-only.</i>")


def notify_admin(msg):
    """Send a proactive Telegram message to admin (callable from anywhere, sync)."""
    if not TELEGRAM_TOKEN:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": list(ADMIN_IDS)[0], "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
        return r.ok
    except Exception:
        return False


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
            InlineKeyboardButton("📊 GHL Status", callback_data="status"),
            InlineKeyboardButton("🖥️ Server", callback_data="server_top"),
        ],
        [
            InlineKeyboardButton("⚡ Workflows", callback_data="workflows"),
            InlineKeyboardButton("📋 Contacts", callback_data="contacts"),
        ],
        [
            InlineKeyboardButton("💾 Disk", callback_data="server_disk"),
            InlineKeyboardButton("🧠 Memory", callback_data="server_mem"),
        ],
        [
            InlineKeyboardButton("⚙️ Services", callback_data="server_services"),
            InlineKeyboardButton("📋 Logs", callback_data="server_logs"),
        ],
        [
            InlineKeyboardButton("🔥 Reddit", callback_data="reddit"),
            InlineKeyboardButton("🎤 Voice Test", callback_data="voice_test"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome = (
        f"👋 <b>Hey {user.first_name}!</b>\n\n"
        f"I'm <b>Lilly</b> — your DDWL-OS command center.\n"
        f"Running 24/7 on the Lenovo server.\n\n"
        f"<b>🏢 GHL</b>\n"
        f"/status · /workflows · /contacts · /research\n\n"
        f"<b>🧠 AI</b>\n"
        f"/ask · /trends · /news · /brief · /say\n\n"
        f"<b>🖥️ Server Control</b>\n"
        f"/run · /install · /service · /git\n"
        f"/disk · /mem · /top · /logs\n"
        f"/download · /update · /reboot\n\n"
        f"<b>Or just type in plain English</b> — I'll figure it out."
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
    elif action == "server_top":
        await cmd_top(update, context)
    elif action == "server_disk":
        await cmd_disk(update, context)
    elif action == "server_mem":
        await cmd_mem(update, context)
    elif action == "server_services":
        context.args = ["list"]
        await cmd_service(update, context)
    elif action == "server_logs":
        context.args = ["lilly-telegram"]
        await cmd_logs(update, context)
    elif action == "reboot_confirm":
        if is_admin(update):
            context.args = ["confirm"]
            await cmd_reboot(update, context)
        else:
            await deny_access(update)
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
# SERVER CONTROL — Run commands, install, manage services
# ============================================================
async def run_shell(cmd, timeout=60):
    """Execute a shell command and return stdout+stderr."""
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(DDWL_DIR),
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace").strip()
        return output[:3800] if output else "(no output)"
    except asyncio.TimeoutError:
        proc.kill()
        return "⏰ Command timed out (60s limit)"
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"


async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute any shell command on the server."""
    if not is_admin(update):
        await deny_access(update)
        return
    cmd = " ".join(context.args) if context.args else ""
    if not cmd:
        await safe_reply(update, (
            "🖥️ <b>Run a command on the server</b>\n\n"
            "<code>/run ls -la</code>\n"
            "<code>/run df -h</code>\n"
            "<code>/run docker ps</code>\n"
            "<code>/run pip list</code>\n"
            "<code>/run cat /etc/os-release</code>"
        ))
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    logger.info(f"🖥️ EXEC [{update.effective_user.first_name}]: {cmd}")
    output = await run_shell(cmd)
    await safe_reply(update, f"<b>$ {cmd}</b>\n\n<code>{output}</code>")


async def cmd_install(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Install packages via apt or pip."""
    if not is_admin(update):
        await deny_access(update)
        return
    args = context.args if context.args else []
    if not args:
        await safe_reply(update, (
            "📦 <b>Install packages</b>\n\n"
            "<code>/install docker.io</code> — apt package\n"
            "<code>/install pip requests flask</code> — pip packages\n"
            "<code>/install apt nginx</code> — explicit apt"
        ))
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    if args[0] == "pip":
        packages = " ".join(args[1:])
        cmd = f"source {DDWL_DIR}/venv/bin/activate && pip install {packages}"
    elif args[0] == "apt":
        packages = " ".join(args[1:])
        cmd = f"sudo DEBIAN_FRONTEND=noninteractive apt-get install -y {packages}"
    else:
        packages = " ".join(args)
        cmd = f"sudo DEBIAN_FRONTEND=noninteractive apt-get install -y {packages}"
    await safe_reply(update, f"📦 <b>Installing:</b> <i>{packages}</i>...")
    output = await run_shell(cmd, timeout=120)
    await safe_reply(update, f"<b>📦 Install result:</b>\n\n<code>{output[-2000:]}</code>")


async def cmd_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage systemd services."""
    if not is_admin(update):
        await deny_access(update)
        return
    args = context.args if context.args else []
    if len(args) < 1:
        await safe_reply(update, (
            "⚙️ <b>Manage services</b>\n\n"
            "<code>/service list</code> — show DDWL services\n"
            "<code>/service status lilly-telegram</code>\n"
            "<code>/service restart lilly-telegram</code>\n"
            "<code>/service stop chat-widget-api</code>\n"
            "<code>/service start chat-widget-api</code>\n"
            "<code>/service logs lilly-telegram</code>"
        ))
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    action = args[0].lower()
    if action == "list":
        output = await run_shell("systemctl list-units --type=service --state=running --no-pager | grep -E 'lilly|chat-widget|openclaw|ddwl' || echo 'No DDWL services found'; echo '---'; systemctl list-units --type=service --state=failed --no-pager | head -5")
        await safe_reply(update, f"<b>⚙️ DDWL Services</b>\n\n<code>{output}</code>")
    elif action == "logs" and len(args) > 1:
        svc = args[1]
        output = await run_shell(f"sudo journalctl -u {svc} --no-pager -n 25 --since '10 min ago'")
        await safe_reply(update, f"<b>📋 Logs: {svc}</b>\n\n<code>{output[-3000:]}</code>")
    elif action in ("start", "stop", "restart", "status") and len(args) > 1:
        svc = args[1]
        if action == "status":
            output = await run_shell(f"sudo systemctl status {svc} --no-pager -l")
        else:
            output = await run_shell(f"sudo systemctl {action} {svc} && sudo systemctl status {svc} --no-pager -l")
        icon = {"start": "▶️", "stop": "⏹️", "restart": "🔄", "status": "ℹ️"}.get(action, "⚙️")
        await safe_reply(update, f"{icon} <b>{action.title()} {svc}</b>\n\n<code>{output}</code>")
    else:
        await safe_reply(update, "❓ Usage: <code>/service [list|start|stop|restart|status|logs] [name]</code>")


async def cmd_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download a file from a URL to the server."""
    if not is_admin(update):
        await deny_access(update)
        return
    url = context.args[0] if context.args else ""
    if not url:
        await safe_reply(update, (
            "⬇️ <b>Download a file</b>\n\n"
            "<code>/download https://example.com/file.zip</code>\n"
            "Files saved to ~/ddwl/downloads/"
        ))
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    await safe_reply(update, f"⬇️ <b>Downloading:</b>\n<i>{url[:100]}</i>")
    output = await run_shell(f"mkdir -p {DDWL_DIR}/downloads && cd {DDWL_DIR}/downloads && wget -q --show-progress '{url}' 2>&1 | tail -3", timeout=120)
    await safe_reply(update, f"<b>⬇️ Download complete:</b>\n\n<code>{output}</code>")


async def cmd_git(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Git operations on the DDWL repo."""
    if not is_admin(update):
        await deny_access(update)
        return
    action = context.args[0].lower() if context.args else ""
    if not action:
        await safe_reply(update, (
            "🔀 <b>Git operations</b>\n\n"
            "<code>/git pull</code> — pull latest changes\n"
            "<code>/git status</code> — show repo status\n"
            "<code>/git log</code> — recent commits"
        ))
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    if action == "pull":
        output = await run_shell(f"cd {DDWL_DIR} && git pull")
        await safe_reply(update, f"<b>🔀 Git Pull</b>\n\n<code>{output}</code>")
    elif action == "status":
        output = await run_shell(f"cd {DDWL_DIR} && git status --short")
        await safe_reply(update, f"<b>🔀 Git Status</b>\n\n<code>{output}</code>")
    elif action == "log":
        output = await run_shell(f"cd {DDWL_DIR} && git log --oneline -10")
        await safe_reply(update, f"<b>🔀 Git Log</b>\n\n<code>{output}</code>")
    else:
        output = await run_shell(f"cd {DDWL_DIR} && git {' '.join(context.args)}")
        await safe_reply(update, f"<b>🔀 git {action}</b>\n\n<code>{output}</code>")


async def cmd_disk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show disk usage."""
    if not is_admin(update):
        await deny_access(update)
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    output = await run_shell("df -h / && echo '' && du -sh ~/ddwl/* 2>/dev/null | sort -rh | head -10")
    await safe_reply(update, f"<b>💾 Disk Usage</b>\n\n<code>{output}</code>")


async def cmd_mem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show memory usage."""
    if not is_admin(update):
        await deny_access(update)
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    output = await run_shell("free -h && echo '' && echo 'Top memory:' && ps aux --sort=-%mem | head -6")
    await safe_reply(update, f"<b>🧠 Memory</b>\n\n<code>{output}</code>")


async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system overview."""
    if not is_admin(update):
        await deny_access(update)
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    output = await run_shell(
        "echo '=== SYSTEM ===' && uname -a && echo '' && "
        "echo '=== UPTIME ===' && uptime && echo '' && "
        "echo '=== MEMORY ===' && free -h | head -2 && echo '' && "
        "echo '=== DISK ===' && df -h / | tail -1 && echo '' && "
        "echo '=== TEMP ===' && cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | awk '{printf \"%.1f°C\\n\", $1/1000}' && echo '' && "
        "echo '=== SERVICES ===' && systemctl is-active lilly-telegram chat-widget-api ssh 2>/dev/null | paste - - - && echo '' && "
        "echo '=== TOP CPU ===' && ps aux --sort=-%cpu | head -4"
    )
    await safe_reply(update, f"<b>📊 Server Overview</b>\n\n<code>{output}</code>")


async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View service logs."""
    if not is_admin(update):
        await deny_access(update)
        return
    svc = context.args[0] if context.args else "lilly-telegram"
    lines = context.args[1] if len(context.args) > 1 else "20"
    await update.effective_chat.send_action(ChatAction.TYPING)
    output = await run_shell(f"sudo journalctl -u {svc} --no-pager -n {lines} --since '30 min ago'")
    await safe_reply(update, f"<b>📋 Logs: {svc}</b>\n\n<code>{output[-3000:]}</code>")


async def cmd_reboot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reboot the server."""
    if not is_admin(update):
        await deny_access(update)
        return
    confirm = context.args[0].lower() if context.args else ""
    if confirm != "confirm":
        keyboard = [[InlineKeyboardButton("⚠️ Yes, reboot now", callback_data="reboot_confirm")]]
        await safe_reply(update, (
            "⚠️ <b>Reboot server?</b>\n\n"
            "This will restart the Lenovo. All services will come back up automatically.\n\n"
            "Type <code>/reboot confirm</code> or tap the button below."
        ), reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await safe_reply(update, "🔄 <b>Rebooting server...</b>\n<i>I'll be back in ~60 seconds.</i>")
    await run_shell("sudo reboot")


async def cmd_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pull latest code and restart services."""
    if not is_admin(update):
        await deny_access(update)
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    await safe_reply(update, "🔄 <b>Updating DDWL-OS...</b>\n<i>Pulling code + restarting services</i>")
    output = await run_shell(
        f"cd {DDWL_DIR} && git pull && "
        f"source {DDWL_DIR}/venv/bin/activate && pip install -q -r requirements.txt 2>/dev/null; "
        "sudo systemctl restart lilly-telegram chat-widget-api 2>/dev/null && "
        "echo '✅ Update complete' && "
        "systemctl is-active lilly-telegram chat-widget-api",
        timeout=120,
    )
    await safe_reply(update, f"<b>🔄 Update Result</b>\n\n<code>{output}</code>")


# ============================================================
# /selfupdate — Full system self-update with rollback
# ============================================================
async def cmd_selfupdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Full system update: git pull, pip install, openclaw update, restart everything."""
    if not is_admin(update):
        await deny_access(update)
        return
    await update.effective_chat.send_action(ChatAction.TYPING)

    # Save current commit hash for rollback
    current = await run_shell(f"cd {DDWL_DIR} && git rev-parse --short HEAD")
    await safe_reply(update, f"🔄 <b>Self-updating DDWL-OS...</b>\n<i>Current: {current}</i>\n<i>Saving rollback point...</i>")

    steps = []

    # Step 1: Git pull
    out = await run_shell(f"cd {DDWL_DIR} && git pull 2>&1")
    steps.append(f"<b>Git pull:</b> {'✅' if 'Already up to date' in out or 'Fast-forward' in out else '⚠️'}\n<code>{out[:300]}</code>")

    # Step 2: Pip install requirements
    out = await run_shell(f"source {DDWL_DIR}/venv/bin/activate && pip install -q -r {DDWL_DIR}/requirements.txt 2>&1 | tail -5", timeout=120)
    steps.append(f"<b>Pip install:</b> ✅\n<code>{out[:200]}</code>")

    # Step 3: Update OpenClaw
    out = await run_shell("openclaw update 2>&1 | tail -5", timeout=120)
    steps.append(f"<b>OpenClaw update:</b>\n<code>{out[:200]}</code>")

    # Step 4: Restart services
    out = await run_shell("sudo systemctl restart lilly-telegram 2>&1; systemctl --user restart openclaw-gateway 2>&1; sleep 2; echo 'Services restarted'")
    steps.append(f"<b>Services:</b> ✅ restarted")

    new_commit = await run_shell(f"cd {DDWL_DIR} && git rev-parse --short HEAD")
    steps.append(f"\n<b>Now running:</b> {new_commit}")
    steps.append(f"<b>Rollback to:</b> <code>/rollback {current}</code>")

    await safe_reply(update, "\n\n".join(steps))


async def cmd_rollback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rollback to a previous git commit."""
    if not is_admin(update):
        await deny_access(update)
        return
    commit = context.args[0] if context.args else ""
    if not commit:
        # Show recent commits to pick from
        output = await run_shell(f"cd {DDWL_DIR} && git log --oneline -10")
        await safe_reply(update, (
            "⏪ <b>Rollback to a previous version</b>\n\n"
            f"<code>{output}</code>\n\n"
            "Usage: <code>/rollback abc1234</code>"
        ))
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    await safe_reply(update, f"⏪ <b>Rolling back to {commit}...</b>")
    out = await run_shell(f"cd {DDWL_DIR} && git stash 2>/dev/null; git checkout {commit} 2>&1")
    restart = await run_shell("sudo systemctl restart lilly-telegram 2>&1; echo DONE")
    await safe_reply(update, f"<b>⏪ Rollback result:</b>\n\n<code>{out}</code>\n\n<i>Services restarting...</i>")


# ============================================================
# /skill — Manage OpenClaw skills
# ============================================================
async def cmd_skill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download, list, or update OpenClaw skills."""
    if not is_admin(update):
        await deny_access(update)
        return
    args = context.args if context.args else []
    action = args[0].lower() if args else ""

    if not action:
        await safe_reply(update, (
            "🧩 <b>Manage OpenClaw Skills</b>\n\n"
            "<code>/skill list</code> — show installed skills\n"
            "<code>/skill install slug</code> — install from ClawHub\n"
            "<code>/skill update</code> — update all skills\n"
            "<code>/skill search query</code> — search ClawHub\n"
            "<code>/skill info slug</code> — skill details"
        ))
        return

    await update.effective_chat.send_action(ChatAction.TYPING)

    if action == "list":
        output = await run_shell(f"ls -1 {DDWL_DIR}/skills/*/SKILL.md 2>/dev/null | sed 's|.*/skills/||;s|/SKILL.md||' && echo '---' && ls -1 ~/.openclaw/skills/*/SKILL.md 2>/dev/null | sed 's|.*/skills/||;s|/SKILL.md||' || echo 'No managed skills'")
        await safe_reply(update, f"<b>🧩 Installed Skills</b>\n\n<b>Workspace:</b>\n<code>{output}</code>")
    elif action == "install" and len(args) > 1:
        slug = args[1]
        await safe_reply(update, f"📦 <b>Installing skill:</b> <i>{slug}</i>...")
        output = await run_shell(f"cd {DDWL_DIR} && clawhub install {slug} 2>&1", timeout=60)
        await safe_reply(update, f"<b>📦 Install result:</b>\n\n<code>{output[:2000]}</code>")
    elif action == "update":
        await safe_reply(update, "🔄 <b>Updating all skills...</b>")
        output = await run_shell(f"cd {DDWL_DIR} && clawhub update --all 2>&1", timeout=60)
        await safe_reply(update, f"<b>🔄 Update result:</b>\n\n<code>{output[:2000]}</code>")
    elif action == "search" and len(args) > 1:
        query = " ".join(args[1:])
        output = await run_shell(f"clawhub search {query} 2>&1 | head -30", timeout=30)
        await safe_reply(update, f"<b>🔍 ClawHub: {query}</b>\n\n<code>{output[:2000]}</code>")
    elif action == "info" and len(args) > 1:
        slug = args[1]
        # Try to read the local SKILL.md
        output = await run_shell(f"cat {DDWL_DIR}/skills/{slug}/SKILL.md 2>/dev/null || cat ~/.openclaw/skills/{slug}/SKILL.md 2>/dev/null || echo 'Skill not found locally. Try /skill install {slug}'")
        await safe_reply(update, f"<b>🧩 Skill: {slug}</b>\n\n<code>{output[:3000]}</code>")
    else:
        await safe_reply(update, "❓ Usage: <code>/skill [list|install|update|search|info] [name]</code>")


# ============================================================
# /health — System health check with auto-diagnosis
# ============================================================
async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run a comprehensive health check and report issues."""
    if not is_admin(update):
        await deny_access(update)
        return
    await update.effective_chat.send_action(ChatAction.TYPING)

    checks = ["<b>🏥 System Health Check</b>\n"]

    # Services
    lilly = await run_shell("systemctl is-active lilly-telegram")
    openclaw = await run_shell("systemctl --user is-active openclaw-gateway")
    checks.append(f"<b>Services:</b>")
    checks.append(f"  Lilly: {'✅' if lilly == 'active' else '❌'} {lilly}")
    checks.append(f"  OpenClaw: {'✅' if openclaw == 'active' else '❌'} {openclaw}")

    # Disk
    disk = await run_shell("df -h / | tail -1 | awk '{print $5}'")
    disk_pct = int(disk.replace('%', '')) if disk.replace('%', '').isdigit() else 0
    checks.append(f"\n<b>Disk:</b> {'✅' if disk_pct < 80 else '⚠️' if disk_pct < 90 else '❌'} {disk} used")

    # Memory
    mem = await run_shell("free | grep Mem | awk '{printf \"%.0f\", $3/$2 * 100}'")
    mem_pct = int(mem) if mem.isdigit() else 0
    checks.append(f"<b>Memory:</b> {'✅' if mem_pct < 80 else '⚠️' if mem_pct < 90 else '❌'} {mem}% used")

    # Load
    load = await run_shell("cat /proc/loadavg | awk '{print $1}'")
    checks.append(f"<b>Load:</b> {load}")

    # Uptime
    uptime = await run_shell("uptime -p")
    checks.append(f"<b>Uptime:</b> {uptime}")

    # Git status
    git_status = await run_shell(f"cd {DDWL_DIR} && git log --oneline -1")
    checks.append(f"\n<b>Code:</b> {git_status}")

    # Recent errors
    errors = await run_shell("sudo journalctl -p err --no-pager -n 5 --since '1 hour ago' 2>/dev/null | tail -5")
    if errors and "No entries" not in errors:
        checks.append(f"\n<b>⚠️ Recent errors:</b>\n<code>{errors[:500]}</code>")
    else:
        checks.append(f"\n<b>Errors:</b> ✅ None in last hour")

    await safe_reply(update, "\n".join(checks))


# ============================================================
# NATURAL LANGUAGE — Plain text messages
# ============================================================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    text_lower = text.lower()
    logger.info(f"Text from {update.effective_user.first_name}: {text[:80]}")

    # Pattern match common intents
    if any(w in text_lower for w in ["help", "commands", "menu", "what can you do"]):
        await cmd_start(update, context)
    elif any(w in text_lower for w in ["status", "how are", "what's up", "overview", "dashboard"]):
        await cmd_status(update, context)
    elif any(w in text_lower for w in ["workflow", "automation"]):
        await cmd_workflows(update, context)
    elif any(w in text_lower for w in ["contact", "lead", "people"]):
        await cmd_contacts(update, context)
    elif any(w in text_lower for w in ["reddit", "community", "forum"]):
        context.args = text_lower.replace("reddit", "").strip().split() or []
        await cmd_reddit(update, context)
    elif any(w in text_lower for w in ["research", "what's new", "changelog"]):
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
    # Server control — natural language
    elif any(w in text_lower for w in ["disk", "storage", "space", "how much space"]):
        await cmd_disk(update, context)
    elif any(w in text_lower for w in ["memory", "ram", "how much ram"]):
        await cmd_mem(update, context)
    elif any(w in text_lower for w in ["server", "system", "top", "cpu", "temperature", "temp"]):
        await cmd_top(update, context)
    elif any(w in text_lower for w in ["service", "services", "what's running"]):
        context.args = ["list"]
        await cmd_service(update, context)
    elif any(p in text_lower for p in ["install ", "apt install", "pip install"]):
        pkg = text_lower.replace("install", "").replace("apt", "").replace("pip", "").strip()
        context.args = pkg.split() if pkg else []
        await cmd_install(update, context)
    elif any(p in text_lower for p in ["restart ", "stop ", "start "]):
        for action in ["restart", "stop", "start"]:
            if action in text_lower:
                svc = text_lower.split(action, 1)[1].strip().split()[0] if text_lower.split(action, 1)[1].strip() else ""
                if svc:
                    context.args = [action, svc]
                    await cmd_service(update, context)
                    return
        context.args = text.split()
        await cmd_do(update, context)
    elif any(w in text_lower for w in ["pull", "git pull", "update code", "update the code"]):
        await cmd_update(update, context)
    elif any(w in text_lower for w in ["reboot", "restart server", "restart the server"]):
        context.args = []
        await cmd_reboot(update, context)
    elif any(w in text_lower for w in ["download "]):
        url = text.split()[-1] if "http" in text else ""
        context.args = [url] if url else []
        await cmd_download(update, context)
    elif any(w in text_lower for w in ["log", "logs", "show logs", "check logs"]):
        context.args = ["lilly-telegram"]
        await cmd_logs(update, context)
    else:
        # Route to AI — ask Groq to figure out what they want
        if GROQ_KEY and is_admin(update):
            await smart_route(update, context, text)
        else:
            context.args = text.split()
            await cmd_do(update, context)


async def smart_route(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Use Groq AI to interpret what the user wants and either run a command or answer."""
    await update.effective_chat.send_action(ChatAction.TYPING)
    try:
        prompt = f"""You are Lilly, an AI assistant that controls a Linux server. The user said: "{text}"

Decide what to do. Respond with EXACTLY one of these formats:

SHELL: <command> — if the user wants to run something on the server
ANSWER: <response> — if the user is asking a question you can answer
UNKNOWN: <message> — if you're not sure what they want

Examples:
- "check if nginx is running" → SHELL: systemctl is-active nginx
- "how much space is left" → SHELL: df -h /
- "install htop" → SHELL: sudo apt-get install -y htop
- "what time is it" → SHELL: date
- "what is wholesaling" → ANSWER: Wholesaling is a real estate strategy where...
- "create a folder called projects" → SHELL: mkdir -p ~/projects
- "show me the last 10 lines of the bot log" → SHELL: sudo journalctl -u lilly-telegram --no-pager -n 10
- "what python packages are installed" → SHELL: /home/exposureai/ddwl/venv/bin/pip list
- "restart the telegram bot" → SHELL: sudo systemctl restart lilly-telegram

The server is Ubuntu 24.04. DDWL repo is at /home/exposureai/ddwl. Python venv at /home/exposureai/ddwl/venv.
Services: lilly-telegram, chat-widget-api. User: exposureai. Always use full paths."""

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.1,
            },
            timeout=15,
        )
        if not r.ok:
            await safe_reply(update, f"❌ AI routing failed: {r.status_code}")
            return

        reply = r.json()["choices"][0]["message"]["content"].strip()
        logger.info(f"🧠 Smart route: {reply[:100]}")

        if reply.startswith("SHELL:"):
            cmd = reply[6:].strip()
            await safe_reply(update, f"🖥️ <b>Running:</b> <code>{cmd}</code>")
            output = await run_shell(cmd)
            await safe_reply(update, f"<code>{output}</code>")
        elif reply.startswith("ANSWER:"):
            answer = reply[7:].strip()
            await safe_reply(update, f"💡 {answer}")
        else:
            msg = reply.replace("UNKNOWN:", "").strip()
            await safe_reply(update, f"🤔 {msg}\n\n<i>Try /help to see what I can do.</i>")
    except Exception as e:
        logger.error(f"Smart route error: {e}")
        await safe_reply(update, f"🤔 I'm not sure what you mean.\n\n<i>Try /help or /run [command]</i>")


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
        BotCommand("ask", "Ask AI anything"),
        BotCommand("run", "Run shell command"),
        BotCommand("install", "Install packages"),
        BotCommand("service", "Manage services"),
        BotCommand("git", "Git operations"),
        BotCommand("top", "Server overview"),
        BotCommand("disk", "Disk usage"),
        BotCommand("mem", "Memory usage"),
        BotCommand("logs", "View service logs"),
        BotCommand("download", "Download a file"),
        BotCommand("update", "Pull code + restart"),
        BotCommand("selfupdate", "Full system update"),
        BotCommand("rollback", "Revert to previous version"),
        BotCommand("skill", "Manage OpenClaw skills"),
        BotCommand("health", "System health check"),
        BotCommand("reboot", "Reboot server"),
        BotCommand("trends", "Trending news"),
        BotCommand("brief", "Morning brief"),
        BotCommand("say", "Lee's voice"),
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

    # Server control handlers
    app.add_handler(CommandHandler("run", cmd_run))
    app.add_handler(CommandHandler("install", cmd_install))
    app.add_handler(CommandHandler("service", cmd_service))
    app.add_handler(CommandHandler("download", cmd_download))
    app.add_handler(CommandHandler("git", cmd_git))
    app.add_handler(CommandHandler("disk", cmd_disk))
    app.add_handler(CommandHandler("mem", cmd_mem))
    app.add_handler(CommandHandler("top", cmd_top))
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(CommandHandler("reboot", cmd_reboot))
    app.add_handler(CommandHandler("update", cmd_update))
    app.add_handler(CommandHandler("selfupdate", cmd_selfupdate))
    app.add_handler(CommandHandler("rollback", cmd_rollback))
    app.add_handler(CommandHandler("skill", cmd_skill))
    app.add_handler(CommandHandler("health", cmd_health))

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
