# OpenClaw + Windsurf Research — DDWL-OS

> Compiled Feb 18, 2026. Read this when you're back.

---

## 1. YOUR CURRENT SETUP

| Component | Status |
|---|---|
| OpenClaw v2026.2.17 | Installed on Lenovo |
| Telegram Bot (Lilly) | Running — custom Python bot, NOT OpenClaw's Telegram channel |
| Windsurf | NOT yet installed on Lenovo |
| SSH | `ssh lenovo` from Windows (passwordless) |

**Key distinction:** Right now Lilly (your Telegram bot) and OpenClaw are SEPARATE. OpenClaw has its OWN Telegram channel that could replace or complement Lilly. More on that below.

---

## 2. OPENCLAW — WHAT IT ACTUALLY IS

OpenClaw is an open-source personal AI assistant (like having your own ChatGPT that runs locally). It's the fastest-growing open-source project on GitHub (2026).

**Core architecture:**
```
WhatsApp / Telegram / Slack / Discord / WebChat
    │
    ▼
┌─────────────────────────┐
│  Gateway (control plane) │
│  ws://127.0.0.1:18789   │
└────────────┬────────────┘
    │
    ├─ AI Agent (Claude, GPT, Groq, Gemini, local models)
    ├─ Skills (SKILL.md files — custom instructions)
    ├─ MCP Servers (1200+ tools)
    ├─ Browser control (CDP)
    ├─ File system access
    └─ Shell command execution
```

**What makes it powerful:**
- Runs on YOUR machine (privacy-first)
- Connects to ANY messaging platform (Telegram, WhatsApp, Slack, Discord, etc.)
- Has "skills" — markdown files that teach it how to do specific things
- Has MCP (Model Context Protocol) — connects to databases, APIs, file systems
- Can run shell commands, edit files, browse the web
- Multi-agent routing — different agents for different channels/people

---

## 3. OPENCLAW SKILLS — HOW TO CREATE THEM

Skills are just markdown files (`SKILL.md`) placed in specific directories.

### Skill locations (in order of precedence):
1. `<workspace>/skills/` — workspace-specific (highest priority)
2. `~/.openclaw/skills/` — shared across all agents
3. Bundled skills — shipped with OpenClaw

### Skill format:
```markdown
---
name: ddwl-ghl-manager
description: Manage GoHighLevel CRM for DDWL
---

You are a GHL management assistant for Do Deals With Lee.

## Tools available
- Use `bash` to run API calls to GHL
- GHL API base: https://services.leadconnectorhq.com
- Location ID: KbiucErIMNPbO1mY4qXL

## Tasks you can do
- List contacts: GET /contacts/?locationId={locationId}
- List workflows: GET /workflows/?locationId={locationId}
- Search contacts by name, phone, email
- Create new contacts
- Update pipeline stages

## Rules
- Always confirm before creating or deleting anything
- Keep responses concise
- Use the API key from environment variable GHL_API_KEY
```

### Install skills from ClawHub:
```bash
clawhub install <skill-slug>
clawhub update --all
```

### Our DDWL skills to create:
- `ddwl-ghl/SKILL.md` — GHL CRM management
- `ddwl-voice/SKILL.md` — ElevenLabs voice generation
- `ddwl-research/SKILL.md` — Market research + Scout capabilities
- `ddwl-server/SKILL.md` — Server management instructions

---

## 4. OPENCLAW + TELEGRAM — CONNECTING THEM

OpenClaw has a NATIVE Telegram channel. This means you could have OpenClaw (with Claude/GPT brain) responding to your Telegram messages instead of (or alongside) our custom Lilly bot.

### Setup:
```json
// ~/.openclaw/openclaw.json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "YOUR_BOT_TOKEN",
      "dmPolicy": "pairing",
      "groups": {
        "*": { "requireMention": true }
      }
    }
  }
}
```

### Then:
```bash
openclaw gateway
openclaw pairing list telegram
openclaw pairing approve telegram <CODE>
```

### IMPORTANT DECISION:
You have two options:
1. **Keep Lilly (current)** — Our custom Python bot with hardcoded commands. Fast, predictable, no AI costs per message.
2. **Switch to OpenClaw Telegram** — Full AI brain (Claude/GPT) behind every message. More powerful but costs tokens per message.
3. **BEST: Run both** — Lilly for quick commands (/run, /disk, /service), OpenClaw for complex AI tasks. Use a DIFFERENT Telegram bot for OpenClaw (create a second bot via @BotFather).

---

## 5. WINDSURF ON THE LENOVO — HOW IT WORKS

Windsurf supports **Remote SSH development**. This means:
- Windsurf runs on your Windows PC (the GUI)
- It SSHes into the Lenovo server
- You edit files, run commands, use Cascade — all on the Lenovo's filesystem
- It's like coding directly on the server

### How to connect:
1. Open Windsurf on your Windows PC
2. Click the **"Open a Remote Window"** button (bottom-left corner)
3. Choose **Remote-SSH**
4. Select `lenovo` (it'll use your SSH config)
5. You're now coding on the Lenovo!

### Requirements:
- Windsurf is already on your Windows PC ✅
- SSH key auth is set up ✅ (`ssh lenovo` works)
- The Lenovo just needs to be on and connected to WiFi ✅

**You do NOT need to install Windsurf on the Lenovo itself.** Windsurf automatically installs a lightweight server component when you first connect via SSH.

### Can you install Windsurf directly on the Lenovo?
- Windsurf is a desktop IDE — it needs a GUI (monitor + keyboard)
- The Lenovo is running Ubuntu Server (no GUI)
- **Remote SSH from your Windows Windsurf is the correct approach**
- If you want a GUI on the Lenovo later, you could install Ubuntu Desktop, but that's overkill

---

## 6. OPENCLAW CONFIGURATION — BEST PRACTICES

### Model setup (use free/cheap models):
```json
{
  "agent": {
    "model": "groq/llama-3.3-70b-versatile"
  }
}
```

### Or use Claude (paid but best):
```json
{
  "agent": {
    "model": "anthropic/claude-sonnet-4-20250514"
  }
}
```

### Key config file: `~/.openclaw/openclaw.json`
```json
{
  "agent": {
    "model": "groq/llama-3.3-70b-versatile",
    "workspace": "/home/exposureai/ddwl"
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "SEPARATE_BOT_TOKEN_HERE"
    }
  },
  "gateway": {
    "port": 18789
  }
}
```

### Useful commands:
```bash
openclaw doctor          # Check for config issues
openclaw status          # Gateway status
openclaw dashboard       # Open browser UI
openclaw onboard         # Run setup wizard
openclaw update          # Update to latest version
```

---

## 7. WHAT TO DO NEXT (ACTION ITEMS)

### Immediate (when you're back):
1. **Test Windsurf Remote SSH** — Open Windsurf → Remote-SSH → `lenovo`
2. **Run `openclaw onboard`** on the Lenovo to complete OpenClaw setup
3. **Create DDWL skills** in `~/.openclaw/skills/ddwl-ghl/SKILL.md`
4. **Test Lilly v2** — Send commands from Telegram

### Short-term:
5. **Create a second Telegram bot** for OpenClaw (via @BotFather)
6. **Connect OpenClaw to Telegram** — Full AI assistant alongside Lilly
7. **Set up Tailscale** — Access the Lenovo from anywhere (not just home WiFi)
8. **Install Docker** on Lenovo — For OpenClaw sandboxing

### Medium-term:
9. **Create MCP servers** for GHL API, ElevenLabs, etc.
10. **Set up OpenClaw cron** — Scheduled AI tasks
11. **Connect OpenClaw to WhatsApp** — Same AI on WhatsApp too

---

## 8. VOICE MESSAGES — WHAT WORKS NOW

**Yes, you can send voice messages to Lilly right now.**

Flow:
1. You send a voice message in Telegram
2. Lilly downloads the audio
3. Groq Whisper transcribes it (free)
4. The transcribed text is routed to the right command
5. Lilly responds with text + voice (Lee's voice via ElevenLabs)

So you can literally say "check disk space" or "restart the chat widget" into your phone and it'll happen.

**What you CAN'T do yet via voice/Telegram:**
- Edit code files (need Windsurf for that)
- Complex multi-step builds
- Anything requiring a GUI

**What you CAN do:**
- Run any shell command
- Install packages
- Start/stop/restart services
- Check server health (disk, memory, CPU, temp)
- Pull code updates from GitHub
- Download files
- Reboot the server
- Ask AI questions
- Get morning briefs
- Search news/trends

---

## 9. USEFUL LINKS

- OpenClaw Docs: https://docs.openclaw.ai
- OpenClaw GitHub: https://github.com/openclaw/openclaw
- OpenClaw Skills: https://docs.openclaw.ai/tools/skills
- OpenClaw Telegram: https://docs.openclaw.ai/channels/telegram
- ClawHub (skill marketplace): https://clawhub.com
- Windsurf SSH Docs: https://docs.windsurf.com/windsurf/advanced
