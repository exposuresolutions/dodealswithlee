"""
Lilly Inbox Watcher — Auto-reply + Telegram notification
==========================================================
Polls Lilly's Gmail inbox every 60 seconds.
When Daniel emails Lilly:
  1. Auto-replies: "On it! I'll get back to you shortly."
  2. Sends Telegram notification with email subject + preview
  3. Marks email as read

Can run standalone or be imported by the Telegram bot.

USAGE:
    python lilly_inbox_watcher.py           # Run watcher loop
    python lilly_inbox_watcher.py once      # Check once and exit
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
AGENT_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
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
TELEGRAM_ADMIN_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")
POLL_INTERVAL = 60  # seconds

# Track which emails we've already processed
PROCESSED_FILE = AGENT_DIR / "processed-emails.json"

# Daniel's email addresses (auto-reply only to these)
DANIEL_EMAILS = [
    "daniel@exposuresolutions.me",
    "daniel@dodealswithlee.com",
    "dangallagher2000@gmail.com",
    "d.gallagher67@nuigalway.ie",
]


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


def load_processed():
    if PROCESSED_FILE.exists():
        try:
            return set(json.loads(PROCESSED_FILE.read_text()))
        except Exception:
            pass
    return set()


def save_processed(ids):
    PROCESSED_FILE.write_text(json.dumps(list(ids)[-500:]))  # Keep last 500


def send_telegram(text, chat_id=None):
    """Send a Telegram notification."""
    if not TELEGRAM_TOKEN:
        log("TG", "No TELEGRAM_BOT_TOKEN — skipping notification")
        return False
    target = chat_id or TELEGRAM_ADMIN_CHAT_ID
    if not target:
        log("TG", "No TELEGRAM_ADMIN_CHAT_ID — skipping notification")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": target,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        if r.ok:
            log("TG", "Notification sent")
            return True
        else:
            log("TG", f"Failed: {r.text[:100]}")
    except Exception as e:
        log("TG", f"Error: {str(e)[:100]}")
    return False


def is_from_daniel(from_header):
    """Check if email is from Daniel."""
    from_lower = from_header.lower()
    return any(email in from_lower for email in DANIEL_EMAILS)


def extract_sender_name(from_header):
    """Extract name from 'Name <email>' format."""
    if "<" in from_header:
        return from_header.split("<")[0].strip().strip('"')
    return from_header.split("@")[0]


def check_inbox():
    """Check Lilly's inbox for new emails from Daniel."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("lilly_email_agent", BASE_DIR / "lilly-email-agent.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    LillyEmailAgent = mod.LillyEmailAgent

    log("INBOX", "Checking Lilly's inbox...")
    agent = LillyEmailAgent()

    if not agent.authenticated:
        log("INBOX", "Authentication failed")
        return

    processed = load_processed()
    new_count = 0

    # Get unread emails
    unread = agent.get_unread(max_results=10)
    log("INBOX", f"Found {len(unread)} unread emails")

    for email in unread:
        msg_id = email["id"]

        # Skip already processed
        if msg_id in processed:
            continue

        sender = email.get("from", "")
        subject = email.get("subject", "(no subject)")
        snippet = email.get("snippet", "")[:150]

        # Only auto-reply to Daniel
        if is_from_daniel(sender):
            sender_name = extract_sender_name(sender)
            log("INBOX", f"New from {sender_name}: {subject[:60]}")

            # 1. Auto-reply
            reply_body = (
                f"Hey {sender_name},\n\n"
                f"Got your email — I'm on it! I'll get back to you shortly.\n\n"
                f"If it's urgent, you can also reach me on Telegram.\n\n"
                f"— Lilly\n"
                f"DDWL AI Assistant"
            )
            success = agent.reply_to(msg_id, reply_body)
            if success:
                log("REPLY", f"Auto-replied to {sender_name}")
            else:
                log("REPLY", f"Failed to reply to {sender_name}")

            # 2. Telegram notification
            tg_text = (
                f"📧 <b>New email from {sender_name}</b>\n\n"
                f"<b>Subject:</b> {subject}\n"
                f"<b>Preview:</b> <i>{snippet}</i>\n\n"
                f"✅ Auto-replied: \"Got your email — I'm on it!\""
            )
            send_telegram(tg_text)

            # 3. Mark as read
            agent.mark_read(msg_id)
            new_count += 1

        else:
            # Not from Daniel — just notify on Telegram (no auto-reply)
            sender_name = extract_sender_name(sender)
            tg_text = (
                f"📨 <b>New email</b>\n\n"
                f"<b>From:</b> {sender_name}\n"
                f"<b>Subject:</b> {subject}\n"
                f"<b>Preview:</b> <i>{snippet}</i>"
            )
            send_telegram(tg_text)

        # Mark as processed
        processed.add(msg_id)

    save_processed(processed)

    if new_count:
        log("INBOX", f"Processed {new_count} new emails from Daniel")
    else:
        log("INBOX", "No new emails from Daniel")


def run_watcher():
    """Run continuous inbox watcher."""
    print("\n" + "=" * 60)
    print("  📧 Lilly Inbox Watcher — Online")
    print(f"  Checking every {POLL_INTERVAL}s")
    print(f"  Auto-reply to: {', '.join(DANIEL_EMAILS[:2])}")
    if TELEGRAM_TOKEN and TELEGRAM_ADMIN_CHAT_ID:
        print(f"  Telegram notifications: ON")
    else:
        print(f"  Telegram notifications: OFF (set TELEGRAM_BOT_TOKEN + TELEGRAM_ADMIN_CHAT_ID)")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    while True:
        try:
            check_inbox()
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\n  👋 Watcher stopped.")
            break
        except Exception as e:
            log("ERROR", str(e)[:200])
            time.sleep(POLL_INTERVAL)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        check_inbox()
    else:
        run_watcher()


if __name__ == "__main__":
    main()
