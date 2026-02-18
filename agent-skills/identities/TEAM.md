# DDWL Agent Team

## Overview

Four specialized AI agents working together for Do Deals With Lee. Each agent has a distinct role, personality, and set of tools. Lilly coordinates the team.

## The Team

```
                    ┌─────────────┐
                    │    LEE      │
                    │  (Human)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   LILLY     │
                    │ Chief of    │
                    │   Staff     │
                    └──┬───┬───┬──┘
                       │   │   │
            ┌──────────┘   │   └──────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
     │   SCOUT     │ │ BUILDER  │ │   VOICE     │
     │ Research &  │ │ Dev &    │ │ Content &   │
     │ Intelligence│ │ Automation│ │ Comms       │
     └─────────────┘ └──────────┘ └─────────────┘
```

## Agent Summary

| Agent | Role | Primary Tool | Cost |
| --- | --- | --- | --- |
| Lilly | Chief of Staff — coordinates everything | Telegram Bot | $0 |
| Scout | Research & trend monitoring | Groq + Google News + Reddit | $0 |
| Builder | Code, automation, GHL workflows | Playwright + Python | $0 |
| Voice | Lee's voice, content, communications | ElevenLabs | ~$5/mo |

## Communication Flow

1. **Lee/Daniel → Lilly** (via Telegram or email)
2. **Lilly → Scout** ("What's trending?" / "Morning brief")
3. **Lilly → Builder** ("Build this workflow" / "Fix the IVR")
4. **Lilly → Voice** ("Record this greeting" / "Draft a post")
5. **All agents → Lilly** (results flow back through Lilly to the user)

## Shared Resources

- **brain.json** — single source of truth for API keys, services, state
- **.env** — all secrets (never committed to git)
- **ghl-knowledge/** — shared knowledge base (research, briefs, SOPs)
- **logs/** — all agents log here
- **identities/** — this directory, personality/role docs

## Where They Run

| Environment | Agents | Status |
| --- | --- | --- |
| Daniel's PC (Windows) | All four (development) | Active |
| Lenovo Mini PC (Ubuntu) | All four (production, 24/7) | Pending setup |
| Client devices | Lilly only (via Telegram) | Active |

## Adding a New Agent

1. Create `identities/[name].md` with role, personality, tools, rules
2. Create `agent-skills/[name]_agent.py` with the agent's logic
3. Wire into Lilly's Telegram bot (command handler + natural language routing)
4. Add to brain.json if it needs new API keys
5. Add systemd service on Lenovo for 24/7 operation
6. Update this file
