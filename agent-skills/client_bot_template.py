"""
Exposure OS — Client Bot Template
====================================
Config-driven Telegram bot. One codebase, many clients.
Load a JSON config → bot is live with that client's branding,
FAQs, services, lead capture, and GHL integration.

USAGE:
    python client_bot_template.py ddwl          # Run DDWL bot
    python client_bot_template.py mcgintys      # Run McGinty's bot
    python client_bot_template.py flavors       # Run Flavors bot
"""

import os
import sys
import json
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
CONFIG_DIR = BASE_DIR / "client-configs"

# Load .env
env_file = BASE_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

logging.basicConfig(format="  [%(asctime)s] %(message)s", datefmt="%H:%M:%S", level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# CONFIG LOADER
# ============================================================
class ClientConfig:
    def __init__(self, config_name):
        config_path = CONFIG_DIR / f"{config_name}.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        self.data = json.loads(config_path.read_text())
        self.name = self.data["client"]
        self.bot_username = self.data["bot_username"]
        self.greeting = self.data["greeting"]
        self.brand_color = self.data.get("brand_color", "#0088cc")

        # Token from env
        token_env = self.data.get("bot_token_env", "TELEGRAM_BOT_TOKEN")
        self.token = os.environ.get(token_env, "")

        # GHL
        ghl = self.data.get("ghl", {})
        ghl_key_env = ghl.get("api_key_env", "GHL_API_KEY")
        self.ghl_api_key = os.environ.get(ghl_key_env, "")
        self.ghl_location_id = ghl.get("location_id", "")

        # FAQs
        self.faqs = self.data.get("faqs", [])
        self.services = self.data.get("services", [])

        # Lead capture
        self.lead_capture = self.data.get("lead_capture", {})

        # Notifications
        self.notifications = self.data.get("notifications", {})

        # AI fallback
        self.ai_fallback = self.data.get("ai_fallback", {})

        # Voice
        self.voice = self.data.get("voice", {})

        logger.info(f"Loaded config: {self.name} (@{self.bot_username})")


# ============================================================
# GHL API
# ============================================================
def ghl_create_contact(config, name, phone, email=None, tags=None):
    """Create a contact in GHL."""
    if not config.ghl_api_key:
        return None

    headers = {
        "Authorization": f"Bearer {config.ghl_api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Version": "2021-07-28",
    }
    body = {
        "locationId": config.ghl_location_id,
        "firstName": name.split()[0] if name else "",
        "lastName": " ".join(name.split()[1:]) if name and len(name.split()) > 1 else "",
        "phone": phone,
        "source": "Telegram Bot",
        "tags": tags or config.lead_capture.get("auto_tag", ["telegram"]),
    }
    if email:
        body["email"] = email

    try:
        r = requests.post(
            "https://services.leadconnectorhq.com/contacts/",
            headers=headers, json=body, timeout=15,
        )
        if r.ok:
            contact = r.json().get("contact", {})
            logger.info(f"GHL contact created: {name} ({phone})")
            return contact
        else:
            logger.error(f"GHL error: {r.text[:200]}")
    except Exception as e:
        logger.error(f"GHL error: {e}")
    return None


def notify_owner(config, text):
    """Send notification to client owner(s)."""
    chat_ids = config.notifications.get("owner_chat_ids", [])
    for chat_id in chat_ids:
        try:
            requests.post(
                f"https://api.telegram.org/bot{config.token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
        except Exception:
            pass


# ============================================================
# AI RESPONSE (Groq free tier)
# ============================================================
def ai_answer(config, question):
    """Get AI response using Groq (free)."""
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key or not config.ai_fallback.get("enabled"):
        return None

    system = config.ai_fallback.get("system_prompt", f"You are a helpful assistant for {config.name}.")

    # Include FAQs as context
    faq_context = ""
    if config.faqs:
        faq_context = "\n\nKnown FAQs:\n" + "\n".join(
            f"Q: {f['q']}\nA: {f['a']}" for f in config.faqs
        )

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-70b-versatile",
                "messages": [
                    {"role": "system", "content": system + faq_context},
                    {"role": "user", "content": question},
                ],
                "max_tokens": 500,
                "temperature": 0.7,
            },
            timeout=15,
        )
        if r.ok:
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"AI error: {e}")
    return None


# ============================================================
# SAFE REPLY
# ============================================================
async def safe_reply(update, text, reply_markup=None):
    try:
        if len(text) > 4000:
            for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
                await update.effective_message.reply_text(
                    chunk, parse_mode=ParseMode.HTML, reply_markup=reply_markup,
                    disable_web_page_preview=True,
                )
        else:
            await update.effective_message.reply_text(
                text, parse_mode=ParseMode.HTML, reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
    except Exception:
        plain = text.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<code>', '').replace('</code>', '')
        await update.effective_message.reply_text(plain, reply_markup=reply_markup)


# ============================================================
# BOT FACTORY — Creates handlers for a given config
# ============================================================
def create_bot(config: ClientConfig):

    # ── /start ──
    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        keyboard = []

        if config.services:
            keyboard.append([InlineKeyboardButton("📋 Services", callback_data="services")])
        if config.faqs:
            keyboard.append([InlineKeyboardButton("❓ FAQ", callback_data="faq")])
        keyboard.append([InlineKeyboardButton("📞 Contact Us", callback_data="contact")])
        if config.lead_capture.get("enabled"):
            keyboard.append([InlineKeyboardButton("✋ I'm Interested", callback_data="lead")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        welcome = f"👋 <b>Hey {user.first_name}!</b>\n\n{config.greeting}\n\n<b>Tap a button or ask me anything:</b>"
        await safe_reply(update, welcome, reply_markup=reply_markup)
        logger.info(f"START from {user.first_name} ({user.id}) on {config.name}")

    # ── Services ──
    async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not config.services:
            await safe_reply(update, "No services listed yet.")
            return

        lines = [f"<b>📋 {config.name} — Services</b>\n"]
        for i, svc in enumerate(config.services, 1):
            lines.append(f"  {i}. {svc}")

        keyboard = [
            [InlineKeyboardButton("✋ I'm Interested", callback_data="lead")],
            [InlineKeyboardButton("🏠 Menu", callback_data="start")],
        ]
        await safe_reply(update, "\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))

    # ── FAQ ──
    async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not config.faqs:
            await safe_reply(update, "No FAQs yet. Just ask me anything!")
            return

        lines = [f"<b>❓ Frequently Asked Questions</b>\n"]
        for faq in config.faqs:
            lines.append(f"<b>Q: {faq['q']}</b>")
            lines.append(f"A: {faq['a']}\n")

        keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="start")]]
        await safe_reply(update, "\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))

    # ── Contact ──
    async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            f"<b>📞 Contact {config.name}</b>\n\n"
            f"Just type your question here and I'll help!\n\n"
            f"Or tap below to share your info and we'll reach out:"
        )
        keyboard = [
            [InlineKeyboardButton("✋ Share My Info", callback_data="lead")],
            [InlineKeyboardButton("🏠 Menu", callback_data="start")],
        ]
        await safe_reply(update, text, reply_markup=InlineKeyboardMarkup(keyboard))

    # ── Lead Capture ──
    async def start_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            f"<b>✋ Great! Let's get you connected.</b>\n\n"
            f"Please send your info in this format:\n\n"
            f"<code>Name: Your Name\n"
            f"Phone: 555-123-4567\n"
            f"Email: you@email.com</code>\n\n"
            f"<i>(Email is optional)</i>"
        )
        context.user_data["awaiting_lead"] = True
        await safe_reply(update, text)

    # ── Button Handler ──
    async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        action = query.data

        if action == "start":
            await cmd_start(update, context)
        elif action == "services":
            await show_services(update, context)
        elif action == "faq":
            await show_faq(update, context)
        elif action == "contact":
            await show_contact(update, context)
        elif action == "lead":
            await start_lead(update, context)

    # ── Text Handler ──
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        user = update.effective_user
        logger.info(f"Text from {user.first_name}: {text[:80]}")

        # Check if awaiting lead info
        if context.user_data.get("awaiting_lead"):
            context.user_data["awaiting_lead"] = False
            return await process_lead(update, context, text)

        # Check FAQ matches
        text_lower = text.lower()
        for faq in config.faqs:
            # Simple keyword matching
            q_words = set(faq["q"].lower().split())
            input_words = set(text_lower.split())
            overlap = q_words & input_words
            if len(overlap) >= 2 or any(w in text_lower for w in q_words if len(w) > 4):
                await safe_reply(update, f"<b>Q: {faq['q']}</b>\n\n{faq['a']}")
                return

        # AI fallback
        await update.effective_chat.send_action(ChatAction.TYPING)
        answer = ai_answer(config, text)
        if answer:
            keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="start")]]
            await safe_reply(update, answer, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await safe_reply(
                update,
                f"Thanks for your message! Someone from {config.name} will get back to you soon.\n\n"
                f"In the meantime, check out our /start menu.",
            )

        # Notify owner
        if config.notifications.get("notify_on_new_lead"):
            notify_owner(config, f"💬 <b>New message on {config.name} bot</b>\n\nFrom: {user.first_name}\nMessage: {text[:200]}")

    # ── Process Lead ──
    async def process_lead(update, context, text):
        # Parse name/phone/email from text
        lines = text.strip().split("\n")
        info = {}
        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
                info[key.strip().lower()] = val.strip()

        name = info.get("name", "")
        phone = info.get("phone", "")
        email = info.get("email", "")

        if not name and not phone:
            # Try raw format: just a phone number or name
            if text.replace("-", "").replace(" ", "").replace("+", "").isdigit():
                phone = text
            else:
                name = text

        if name or phone:
            # Create GHL contact
            contact = ghl_create_contact(config, name, phone, email)

            await safe_reply(
                update,
                f"✅ <b>Got it!</b>\n\n"
                f"<b>Name:</b> {name or '—'}\n"
                f"<b>Phone:</b> {phone or '—'}\n"
                f"<b>Email:</b> {email or '—'}\n\n"
                f"Someone from <b>{config.name}</b> will reach out soon!",
            )

            # Notify owner
            notify_owner(
                config,
                f"🔥 <b>New lead from {config.name} bot!</b>\n\n"
                f"<b>Name:</b> {name}\n"
                f"<b>Phone:</b> {phone}\n"
                f"<b>Email:</b> {email or '—'}\n"
                f"<b>Source:</b> Telegram",
            )
        else:
            await safe_reply(update, "I couldn't parse your info. Please try:\n\n<code>Name: Your Name\nPhone: 555-123-4567</code>")

    # ── Post Init ──
    async def post_init(application):
        commands = [
            BotCommand("start", "Main menu"),
            BotCommand("services", "Our services"),
            BotCommand("faq", "Frequently asked questions"),
            BotCommand("contact", "Contact us"),
        ]
        await application.bot.set_my_commands(commands)
        me = await application.bot.get_me()
        logger.info(f"✅ {config.name} bot online: @{me.username}")

    # ── Build App ──
    app = Application.builder().token(config.token).post_init(post_init).job_queue(None).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("services", show_services))
    app.add_handler(CommandHandler("faq", show_faq))
    app.add_handler(CommandHandler("contact", show_contact))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app


# ============================================================
# MAIN
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("\n  Exposure OS — Client Bot Template")
        print("  ===================================")
        print(f"\n  Available configs:")
        for f in sorted(CONFIG_DIR.glob("*.json")):
            data = json.loads(f.read_text())
            print(f"    {f.stem:20s} → {data['client']}")
        print(f"\n  Usage: python {Path(__file__).name} <config_name>")
        print(f"  Example: python {Path(__file__).name} ddwl")
        return

    config_name = sys.argv[1]

    try:
        config = ClientConfig(config_name)
    except FileNotFoundError as e:
        print(f"\n  ❌ {e}")
        return

    if not config.token:
        print(f"\n  ❌ No bot token for {config.name}")
        print(f"  Set {config.data.get('bot_token_env', 'TELEGRAM_BOT_TOKEN')} in .env")
        return

    print(f"\n{'=' * 60}")
    print(f"  🤖 {config.name} Bot — Starting...")
    print(f"  Config: {config_name}.json")
    print(f"  Bot: @{config.bot_username}")
    print(f"{'=' * 60}")

    app = create_bot(config)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
