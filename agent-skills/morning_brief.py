"""
Morning Brief — Proactive Heartbeat for DDWL
==============================================
Generates a Scout morning brief and sends it to Lee via Telegram.
Designed to run as a daily cron job / scheduled task at 7 AM.

USAGE:
    python morning_brief.py           # Generate + send to Telegram
    python morning_brief.py --dry-run # Generate only, don't send

On Ubuntu (Lenovo):
    crontab -e
    0 7 * * * cd /home/daniel/ddwl-os && python3 agent-skills/morning_brief.py >> agent-skills/logs/morning-brief.log 2>&1

On Windows (Task Scheduler):
    daily_brief.bat → runs this script at 7 AM
"""

import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
AGENT_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_DIR))

load_dotenv(BASE_DIR / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
LOG_DIR = AGENT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log(tag, msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"  [{ts}] [{tag}] {msg}"
    print(line)


def send_telegram(text, chat_id=None):
    """Send a message via Telegram Bot API."""
    if not TELEGRAM_TOKEN:
        log("ERROR", "TELEGRAM_BOT_TOKEN not set")
        return False
    cid = chat_id or TELEGRAM_CHAT_ID
    if not cid:
        log("ERROR", "TELEGRAM_ADMIN_CHAT_ID not set")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # Telegram max message length is 4096
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]

    for chunk in chunks:
        try:
            r = requests.post(url, json={
                "chat_id": cid,
                "text": chunk,
                "disable_web_page_preview": True,
            }, timeout=15)
            if r.status_code != 200:
                log("TELEGRAM", f"Send failed: {r.status_code} {r.text[:200]}")
                return False
        except Exception as e:
            log("TELEGRAM", f"Send error: {e}")
            return False
        time.sleep(0.5)

    return True


def main():
    dry_run = "--dry-run" in sys.argv

    log("BRIEF", f"Morning brief starting — {datetime.now().strftime('%A, %B %d, %Y %I:%M %p')}")

    # Generate the brief using Scout
    try:
        from xai_scout import generate_morning_brief
        brief = generate_morning_brief()
    except Exception as e:
        log("ERROR", f"Scout failed: {e}")
        brief = None

    if not brief:
        log("ERROR", "No brief generated")
        return

    log("BRIEF", f"Brief generated ({len(brief)} chars)")

    if dry_run:
        print("\n" + brief)
        log("BRIEF", "Dry run — not sending to Telegram")
        return

    # Send to Telegram
    header = "☀️ DDWL Morning Brief\n━━━━━━━━━━━━━━━━━━━━\n\n"
    success = send_telegram(header + brief)

    if success:
        log("BRIEF", "✓ Sent to Telegram")
    else:
        log("BRIEF", "✗ Failed to send to Telegram")


if __name__ == "__main__":
    main()
