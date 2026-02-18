# Exposure OS — Client Bot System

## The Product

Every Exposure Solutions client gets an AI assistant on their website.
Their customers chat with it. It answers questions, books appointments,
captures leads, and pushes everything to GoHighLevel.

Three delivery methods. Same backend. Different front-ends.

---

## Method 1: Floating Telegram Button

**What:** A floating chat icon on the client's website. Customer taps it,
opens the client's Telegram bot. Works on mobile and desktop.

**Effort:** 5 minutes per client
**Cost:** $0
**Requires:** Customer has Telegram (or uses web.telegram.org)

**How to add to any website:**
```html
<!-- Exposure OS Chat Button — paste before </body> -->
<div id="expo-chat-btn" onclick="window.open('https://t.me/CLIENT_BOT_USERNAME','_blank')"
  style="position:fixed;bottom:24px;right:24px;width:60px;height:60px;
  border-radius:50%;background:#0088cc;cursor:pointer;z-index:9999;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 4px 12px rgba(0,0,0,0.3);transition:transform 0.2s">
  <svg width="28" height="28" viewBox="0 0 24 24" fill="white">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
  </svg>
</div>
<style>#expo-chat-btn:hover{transform:scale(1.1)}</style>
```

**Swap per client:** Change `CLIENT_BOT_USERNAME` and optionally the color.

---

## Method 2: Web Chat Widget (No Telegram Required)

**What:** An embeddable chat window that runs on the client's website.
Customer types in the widget, messages go to the bot backend,
responses appear in the widget. No Telegram app needed.

**Effort:** Built once, configure per client
**Cost:** $0 (uses Groq free tier for AI responses)
**Requires:** The widget JS file hosted (CDN or client's server)

**Architecture:**
```
Customer types in widget
    → POST to /api/chat (our server)
    → Groq/Gemini generates response
    → Response sent back to widget
    → Lead captured → GHL contact created
```

**How to add to any website:**
```html
<!-- Exposure OS Web Chat — paste before </body> -->
<script src="https://cdn.exposuresolutions.me/chat-widget.js"
  data-bot="mcgintys"
  data-color="#FF6B00"
  data-greeting="Hey! I'm the McGinty's assistant. How can I help?"
  data-ghl-location="KbiucErIMNPbO1mY4qXL">
</script>
```

**Features:**
- Branded colors and greeting per client
- Lead capture (name, email, phone) before chat starts
- FAQ answers from client's knowledge base
- Appointment booking via GHL calendar API
- Conversation history saved to GHL contact
- Mobile responsive
- No Telegram account needed

---

## Method 3: Client Bot Template (The Replicable System)

**What:** A config-driven Telegram bot that we clone per client.
One codebase, many bots. Swap the config file, new client is live.

**Effort:** 2 minutes per new client (create bot + config file)
**Cost:** $0 per bot (Telegram API is free)

**Config file per client:**
```json
{
  "client": "McGinty's Garage",
  "bot_username": "mcgintys_bot",
  "bot_token": "xxx:yyy",
  "brand_color": "#FF6B00",
  "greeting": "Hey! Welcome to McGinty's. I can help with appointments, estimates, and questions about our services.",
  "ghl": {
    "api_key": "pit-xxx",
    "location_id": "abc123",
    "calendar_id": "cal-xxx",
    "pipeline_id": "pipe-xxx"
  },
  "voice": {
    "enabled": false,
    "voice_id": null
  },
  "faqs": [
    {"q": "What are your hours?", "a": "Mon-Fri 8am-6pm, Sat 9am-2pm"},
    {"q": "Where are you located?", "a": "123 Main St, Cleveland, OH"},
    {"q": "Do you do oil changes?", "a": "Yes! Walk-ins welcome or book online."}
  ],
  "services": [
    "Oil Change - $39.99",
    "Brake Service - from $149",
    "Tire Rotation - $29.99",
    "Full Inspection - $89.99"
  ],
  "lead_capture": {
    "enabled": true,
    "required_fields": ["name", "phone"],
    "optional_fields": ["email", "vehicle"],
    "auto_tag": ["website-lead", "telegram"]
  },
  "notifications": {
    "owner_chat_id": "123456789",
    "notify_on_new_lead": true,
    "notify_on_appointment": true
  }
}
```

**Bot capabilities per client:**
- Welcome message with inline keyboard
- FAQ answers (from config)
- Service menu with prices
- Appointment booking → GHL calendar
- Lead capture → GHL contact with tags
- Owner notifications via Telegram
- AI fallback for questions not in FAQ (Groq free)

---

## Pricing Model (Exposure Solutions Revenue)

| Tier | Setup | Monthly | What They Get |
|------|-------|---------|---------------|
| **Starter** | $299 | $49/mo | Floating button + Telegram bot + FAQ |
| **Pro** | $499 | $99/mo | Web widget + bot + lead capture + booking |
| **Enterprise** | $999 | $199/mo | All above + voice clone + custom AI training |

**Our cost per client: ~$0-5/mo** (all free APIs)
**Margin: 90%+**

---

## Implementation Priority

### Tonight (Built)
- [x] Core bot engine (telegram_bot.py)
- [x] GHL API integration
- [x] Voice generation (ElevenLabs)
- [x] Voice input (Groq Whisper)
- [x] Research agent
- [x] Email watcher

### This Week
- [ ] Floating chat button component (reusable HTML snippet)
- [ ] Client bot template (config-driven)
- [ ] Web chat widget (embeddable JS)
- [ ] First client deployment: McGinty's Garage
- [ ] Second client: Flavors Frozen Daiquiri Bar

### Next Week
- [ ] Chat widget hosted on CDN
- [ ] Admin dashboard for client management
- [ ] Automated onboarding flow
- [ ] First paying client

---

## File Structure

```
agent-skills/
  telegram_bot.py          ← Core bot (DDWL/Lilly)
  client_bot_template.py   ← Config-driven client bot
  lilly_inbox_watcher.py   ← Email monitoring
  web_chat_server.py       ← Web widget backend
  
client-configs/
  ddwl.json                ← Do Deals With Lee
  mcgintys.json            ← McGinty's Garage
  flavors.json             ← Flavors Frozen Daiquiri
  
web-widgets/
  chat-widget.js           ← Embeddable chat widget
  chat-widget.css          ← Widget styles
  floating-button.html     ← Telegram button snippet
```
