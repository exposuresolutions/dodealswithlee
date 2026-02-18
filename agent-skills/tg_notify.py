#!/usr/bin/env python3
"""Send a Telegram message to the admin from anywhere on the server."""
import sys, os, requests
from pathlib import Path

env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = 1399744360


def send(msg):
    if not TOKEN:
        print("No TELEGRAM_BOT_TOKEN")
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"},
        timeout=10,
    )
    return r.ok


if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) or "Ping from Lilly"
    ok = send(msg)
    print("Sent" if ok else "Failed")
