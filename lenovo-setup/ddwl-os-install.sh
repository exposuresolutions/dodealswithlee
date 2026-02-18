#!/bin/bash
# ============================================================
# DDWL-OS — One-Shot Install Script for Lenovo Mini PC
# ============================================================
# Run this AFTER Ubuntu Server 24.04 is installed.
# Usage: bash ddwl-os-install.sh
# ============================================================

set -e
echo ""
echo "============================================================"
echo "  DDWL-OS — Installing on $(hostname)"
echo "  $(date)"
echo "============================================================"
echo ""

# ── 1. System Updates ──
echo "[1/8] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# ── 2. Core Dependencies ──
echo "[2/8] Installing core dependencies..."
sudo apt install -y \
    git curl wget build-essential \
    python3 python3-pip python3-venv \
    ffmpeg \
    unzip htop tmux

# ── 3. Node.js 20 LTS ──
echo "[3/8] Installing Node.js 20 LTS..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# ── 4. OpenClaw ──
echo "[4/8] Installing OpenClaw..."
curl -fsSL https://openclaw.ai/install.sh | bash

# ── 5. DDWL Agent Stack ──
echo "[5/8] Setting up DDWL agent stack..."
cd ~
mkdir -p ddwl
# If the repo files are on USB, copy them:
# cp -r /media/daniel/USB_DRIVE/ddwl/* ~/ddwl/
# Or clone from git if available

cd ~/ddwl
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install Python dependencies
if [ -f "lenovo-setup/requirements.txt" ]; then
    pip install -r lenovo-setup/requirements.txt
else
    pip install python-telegram-bot==21.5 requests python-dotenv pytz apscheduler
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
    pip install playwright beautifulsoup4
fi

# Install Playwright browsers
playwright install chromium
playwright install-deps

# ── 6. Create systemd Services ──
echo "[6/8] Creating systemd services..."

# Telegram Bot
sudo tee /etc/systemd/system/lilly-telegram.service > /dev/null << 'EOF'
[Unit]
Description=Lilly DDWL Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=daniel
WorkingDirectory=/home/daniel/ddwl/agent-skills
ExecStart=/home/daniel/ddwl/venv/bin/python telegram_bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Inbox Watcher
sudo tee /etc/systemd/system/lilly-inbox.service > /dev/null << 'EOF'
[Unit]
Description=Lilly Inbox Watcher
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=daniel
WorkingDirectory=/home/daniel/ddwl/agent-skills
ExecStart=/home/daniel/ddwl/venv/bin/python lilly_inbox_watcher.py
Restart=always
RestartSec=30
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Enable services (don't start yet — need .env first)
sudo systemctl daemon-reload
sudo systemctl enable lilly-telegram
sudo systemctl enable lilly-inbox

# ── 7. Daily Research Cron ──
echo "[7/8] Setting up daily research cron job (7 AM)..."
(crontab -l 2>/dev/null; echo "0 7 * * * cd /home/daniel/ddwl/agent-skills && /home/daniel/ddwl/venv/bin/python ghl_live_research.py full >> /home/daniel/ddwl/logs/research.log 2>&1") | crontab -
mkdir -p ~/ddwl/logs

# ── 8. Tailscale (Remote Access) ──
echo "[8/8] Installing Tailscale for remote access..."
curl -fsSL https://tailscale.com/install.sh | sh

echo ""
echo "============================================================"
echo "  DDWL-OS Installation Complete!"
echo "============================================================"
echo ""
echo "  Next steps:"
echo "  1. Copy your .env file:  scp .env daniel@ddwl-os:~/ddwl/.env"
echo "  2. Copy agent-skills/:   scp -r agent-skills/ daniel@ddwl-os:~/ddwl/"
echo "  3. Copy client-configs/:  scp -r client-configs/ daniel@ddwl-os:~/ddwl/"
echo "  4. Start Tailscale:      sudo tailscale up"
echo "  5. Start services:"
echo "     sudo systemctl start lilly-telegram"
echo "     sudo systemctl start lilly-inbox"
echo "  6. Check status:"
echo "     sudo systemctl status lilly-telegram"
echo "     journalctl -u lilly-telegram -f"
echo ""
echo "  Versions installed:"
echo "  Python: $(python3 --version)"
echo "  Node:   $(node --version)"
echo "  npm:    $(npm --version)"
echo "  ffmpeg: $(ffmpeg -version 2>&1 | head -1)"
echo ""
