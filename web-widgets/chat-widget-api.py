"""
Chat Widget API — Lightweight backend for the web chat widget
==============================================================
Proxies chat requests to Groq (free) so the API key stays server-side.
Runs on the Lenovo or any server.

USAGE:
    python chat-widget-api.py                  # Start on port 8090
    python chat-widget-api.py --port 8091      # Custom port

DEPLOY:
    systemd service on Lenovo (see LENOVO-SETUP-GUIDE.md)
    or: nohup python3 chat-widget-api.py &

CORS enabled so any client website can call it.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import requests

# Load env
BASE_DIR = Path(__file__).parent.parent
env_file = BASE_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
PORT = 8090
MODEL = "llama-3.3-70b-versatile"

# Client configs — add new clients here
CLIENTS = {
    "ddwl": {
        "name": "Do Deals With Lee",
        "bot_name": "Lilly",
        "system_prompt": """You are Lilly, the AI assistant for Do Deals With Lee (DDWL), a Tampa Bay real estate investment company run by Lee Kearney.
Lee does wholesaling, coaching, and creative finance deals.
Be helpful, concise, and professional.
If someone wants to sell a property, get their name, phone number, and property address.
If they want coaching info, direct them to dodealswithlee.com.
Keep responses under 100 words.""",
    },
    "mcgintys": {
        "name": "McGinty's Garage Repair",
        "bot_name": "Lilly",
        "system_prompt": """You are Lilly, the AI assistant for McGinty's Garage Repair.
Help customers with booking appointments, getting quotes, and answering questions about car repair services.
Be friendly and professional. If they need a quote, ask for: vehicle make/model/year, the issue, and their phone number.
Keep responses under 100 words.""",
    },
}

logging.basicConfig(format="  [%(asctime)s] %(message)s", datefmt="%H:%M:%S", level=logging.INFO)
logger = logging.getLogger(__name__)


def call_groq(messages):
    """Call Groq API and return the response text."""
    if not GROQ_API_KEY:
        return "Chat is currently offline. Please call us directly."

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": 300,
            },
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            logger.error(f"Groq {r.status_code}: {r.text[:200]}")
            return "I'm having trouble right now. Please try again in a moment."
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "Connection error. Please try again."


class ChatHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        """Handle chat message."""
        path = urlparse(self.path).path

        if path != "/api/chat":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception:
            self.send_error(400, "Invalid JSON")
            return

        client_id = body.get("client", "ddwl")
        user_messages = body.get("messages", [])

        if not user_messages:
            self.send_error(400, "No messages")
            return

        # Get client config
        client = CLIENTS.get(client_id, CLIENTS["ddwl"])

        # Build message history with system prompt
        messages = [{"role": "system", "content": client["system_prompt"]}]
        for msg in user_messages[-10:]:  # Keep last 10 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        logger.info(f"[{client_id}] {user_messages[-1].get('content', '')[:60]}")

        # Get AI response
        reply = call_groq(messages)

        # Send response
        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "reply": reply,
            "bot_name": client["bot_name"],
        }).encode())

    def do_GET(self):
        """Health check."""
        if self.path == "/health":
            self.send_response(200)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "clients": list(CLIENTS.keys()),
                "model": MODEL,
            }).encode())
        else:
            self.send_error(404)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        pass  # Suppress default logging


def main():
    global PORT
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            PORT = int(sys.argv[idx + 1])

    server = HTTPServer(("0.0.0.0", PORT), ChatHandler)
    logger.info(f"Chat Widget API running on http://0.0.0.0:{PORT}")
    logger.info(f"Health: http://localhost:{PORT}/health")
    logger.info(f"Chat:   POST http://localhost:{PORT}/api/chat")
    logger.info(f"Clients: {', '.join(CLIENTS.keys())}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
