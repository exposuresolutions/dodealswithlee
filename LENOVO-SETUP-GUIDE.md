# DDWL-OS — Lenovo Mini PC Setup Guide

## Hardware: Lenovo Mini PC (old, to be wiped)
## OS: Ubuntu Server 24.04 LTS
## Purpose: Always-on DDWL-OS server running OpenClaw + Lilly agents 24/7

---

## PHASE 1: Create Bootable USB Key

### What You Need
- USB drive (8GB minimum, 16GB recommended)
- Your current Windows PC to create the USB
- Internet connection

### Step 1: Download Ubuntu Server 24.04 LTS
- Go to: https://ubuntu.com/download/server
- Download: **Ubuntu Server 24.04.x LTS** (about 2.5 GB ISO)
- LTS = Long Term Support = 5 years of updates

### Step 2: Download Rufus (USB Creator)
- Go to: https://rufus.ie
- Download Rufus portable (no install needed)

### Step 3: Create Bootable USB
1. Insert USB drive
2. Open Rufus
3. Device: Select your USB drive
4. Boot selection: Click SELECT → choose the Ubuntu ISO you downloaded
5. Partition scheme: GPT (for UEFI) or MBR (for older BIOS — check Lenovo)
6. File system: FAT32
7. Click START
8. Wait ~5 minutes

### Step 4: Boot Lenovo from USB
1. Plug USB into Lenovo
2. Power on → press F12 (or F2 or Del) to enter boot menu
3. Select USB drive
4. Choose "Install Ubuntu Server"

---

## PHASE 2: Install Ubuntu Server

### During Installation
1. **Language**: English
2. **Keyboard**: US (or your preference)
3. **Network**: Connect to WiFi or Ethernet (Ethernet preferred for server)
4. **Storage**: Use entire disk (wipe everything)
5. **Profile**:
   - Name: `daniel`
   - Server name: `ddwl-os`
   - Username: `daniel`
   - Password: (choose a strong one)
6. **SSH**: ✅ Install OpenSSH server (IMPORTANT — this is how you'll access it remotely)
7. **Snaps**: Skip for now

### After Installation
- Remove USB, reboot
- Login with your username/password
- You should see a terminal prompt: `daniel@ddwl-os:~$`

---

## PHASE 3: Initial Server Setup

Run these commands after first login:

```bash
# Update everything
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y git curl wget build-essential python3 python3-pip python3-venv nodejs npm ffmpeg

# Install Node.js 20 (LTS) — needed for OpenClaw
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify versions
python3 --version    # Should be 3.12+
node --version       # Should be 20+
npm --version        # Should be 10+
git --version        # Should be 2.40+
ffmpeg -version      # Needed for audio processing

# Set timezone
sudo timedatectl set-timezone America/New_York
```

---

## PHASE 4: Install OpenClaw

```bash
# Install OpenClaw (official installer)
curl -fsSL https://openclaw.ai/install.sh | bash

# Follow the setup wizard:
# - Choose AI model (Claude Opus 4.6 or GPT-5 Codex)
# - Connect messaging platform (Telegram first)
# - Set up API keys
```

### Configure OpenClaw for DDWL
```bash
# OpenClaw stores config in ~/.openclaw/
# We'll add our custom skills and integrations

# Create DDWL skills directory
mkdir -p ~/.openclaw/skills/ddwl-ghl
mkdir -p ~/.openclaw/skills/ddwl-voice
mkdir -p ~/.openclaw/skills/ddwl-research
```

---

## PHASE 5: Install DDWL-OS (Lilly Agent Stack)

```bash
# Clone the DDWL repo
cd ~
git clone https://github.com/exposuresolutions/dodealswithlee.git ddwl
# OR copy from OneDrive/USB

# Create Python virtual environment
cd ~/ddwl
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install python-telegram-bot requests python-dotenv pytz

# Install Playwright for browser automation
pip install playwright
playwright install chromium
playwright install-deps

# Copy .env file (contains all API keys)
# Transfer from your Windows PC via SCP:
# From Windows: scp .env daniel@ddwl-os:~/ddwl/.env
```

---

## PHASE 6: Set Up Services (Auto-Start on Boot)

### Telegram Bot Service
```bash
sudo tee /etc/systemd/system/lilly-telegram.service << 'EOF'
[Unit]
Description=Lilly DDWL Telegram Bot
After=network.target

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

sudo systemctl enable lilly-telegram
sudo systemctl start lilly-telegram
```

### Inbox Watcher Service
```bash
sudo tee /etc/systemd/system/lilly-inbox.service << 'EOF'
[Unit]
Description=Lilly Inbox Watcher
After=network.target

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

sudo systemctl enable lilly-inbox
sudo systemctl start lilly-inbox
```

### Daily Research Cron Job
```bash
# Run research at 7 AM daily
(crontab -l 2>/dev/null; echo "0 7 * * * cd /home/daniel/ddwl/agent-skills && /home/daniel/ddwl/venv/bin/python ghl_live_research.py full >> /home/daniel/ddwl/logs/research.log 2>&1") | crontab -
```

### Check Service Status
```bash
sudo systemctl status lilly-telegram    # Should show "active (running)"
sudo systemctl status lilly-inbox       # Should show "active (running)"
journalctl -u lilly-telegram -f         # Live logs
```

---

## PHASE 7: Remote Access Setup

### From Your Windows PC
```bash
# SSH into the Lenovo from anywhere on your network
ssh daniel@ddwl-os

# Or by IP address
ssh daniel@192.168.1.XXX

# Transfer files
scp file.txt daniel@ddwl-os:~/ddwl/
```

### Optional: Tailscale (Access from Anywhere)
```bash
# Install Tailscale for secure remote access outside your network
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
# Now accessible from anywhere as daniel@ddwl-os via Tailscale
```

---

## PHASE 8: Multi-User Rollout

Each DDWL team member gets their own bot, same machine:

```bash
# Lee's bot
sudo systemctl enable lilly-lee
# Config: ~/ddwl/client-configs/lee.json
# Bot: @ddwl_lee_bot

# Krystle's bot
sudo systemctl enable lilly-krystle
# Config: ~/ddwl/client-configs/krystle.json
# Bot: @ddwl_krystle_bot

# Stacy's bot
sudo systemctl enable lilly-stacy
# Config: ~/ddwl/client-configs/stacy.json

# Becky's bot
sudo systemctl enable lilly-becky
# Config: ~/ddwl/client-configs/becky.json
```

All running simultaneously on the same Lenovo box.
Each person opens their own Telegram bot.
Same codebase, different configs.

---

## Cost Summary

| Item | Cost |
|------|------|
| Lenovo Mini PC | $0 (already owned) |
| Ubuntu Server | $0 (free) |
| OpenClaw | $0 (open source) |
| Telegram bots | $0 (free API) |
| Groq Whisper (voice) | $0 (free tier) |
| ElevenLabs (Lee's voice) | ~$5/mo |
| GHL API | $0 (included in GHL plan) |
| Electricity | ~$5/mo |
| **Total** | **~$10/mo for the entire system** |

---

## Quick Reference

| Command | What It Does |
|---------|-------------|
| `ssh daniel@ddwl-os` | Connect to the server |
| `sudo systemctl status lilly-telegram` | Check bot status |
| `sudo systemctl restart lilly-telegram` | Restart bot |
| `journalctl -u lilly-telegram -f` | Live bot logs |
| `htop` | Check CPU/RAM usage |
| `df -h` | Check disk space |
| `tail -f ~/ddwl/logs/research.log` | Research agent logs |
