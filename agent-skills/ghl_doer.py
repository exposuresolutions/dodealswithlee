"""
GHL Doer Agent — Tell it what to do, it does it
=================================================
The unified agent that takes plain English and executes in GHL.

USAGE:
    python ghl_doer.py "build an IVR workflow for the main line"
    python ghl_doer.py "show all contacts tagged as investor"
    python ghl_doer.py "create a workflow that sends SMS when form submitted"
    python ghl_doer.py   # Interactive mode

HOW IT WORKS:
    1. You give it a task in plain English
    2. AI brain classifies: API task or Browser task?
    3. API tasks → GHL REST API (contacts, pipelines, messages, etc.)
    4. Browser tasks → Playwright opens GHL, uses AI Builder or clicks through UI
    5. If stuck → asks you for help (CAPTCHA, login, ambiguous choice)

CAPABILITIES:
    API (instant):  contacts, pipelines, conversations, calendars, tags, forms, workflows list
    Browser (slow): build workflows, configure IVR, set up Voice AI, edit pages, phone settings
"""

import os
import sys
import json
import asyncio
import time
import requests
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
AGENT_DIR = Path(__file__).parent
LOG_DIR = AGENT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
KB_DIR = AGENT_DIR / "ghl-knowledge"

# Load env
env_file = BASE_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

GHL_API_KEY = os.environ.get("GHL_API_KEY", "")
GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID", "KbiucErIMNPbO1mY4qXL")
GHL_API_BASE = "https://services.leadconnectorhq.com"
GHL_API_HEADERS = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Version": "2021-07-28",
}
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

# GHL URLs (v2 — the only ones that render)
GHL_V2 = f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION_ID}"
GHL_URLS = {
    "dashboard": f"{GHL_V2}/dashboard",
    "workflows": f"{GHL_V2}/automation/workflows?listTab=all",
    "phone_system": f"{GHL_V2}/settings/phone_system?tab=manage",
    "voice": f"{GHL_V2}/settings/phone_system?tab=voice",
    "ai_agents": f"{GHL_V2}/ai-agents",
    "contacts": f"{GHL_V2}/contacts",
    "conversations": f"{GHL_V2}/conversations",
    "settings": f"{GHL_V2}/settings/profile",
}

LILLY_EMAIL = os.environ.get("GHL_EMAIL", "")
LILLY_PASS = os.environ.get("GHL_PASSWORD", "")


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


def audit(action, details=""):
    """Append to audit log."""
    log_file = BASE_DIR / "agent-audit-log.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": "ghl_doer",
        "action": action,
        "details": str(details)[:500],
    }
    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except Exception:
            logs = []
    logs.append(entry)
    log_file.write_text(json.dumps(logs[-1000:], indent=2))


# ============================================================
# 1. TASK CLASSIFIER — AI decides API vs Browser
# ============================================================
CLASSIFIER_PROMPT = """You are a GoHighLevel task classifier. Given a user's request, classify it.

RESPOND WITH EXACTLY ONE JSON OBJECT (no markdown, no explanation):
{
    "type": "api" or "browser",
    "action": "specific action name",
    "params": {key: value pairs extracted from the request},
    "ghl_ai_prompt": "if browser type and it's a workflow, write the prompt for GHL's AI Builder",
    "explanation": "one sentence explaining what you'll do"
}

API ACTIONS (fast, no browser needed):
- get_contacts: list/search contacts. params: {query, limit}
- get_contact: get one contact. params: {contact_id}
- create_contact: create contact. params: {name, email, phone, tags}
- send_sms: send SMS. params: {contact_id, message}
- send_email: send email. params: {contact_id, subject, body}
- get_pipelines: list pipelines
- get_opportunities: list deals. params: {pipeline_id}
- get_workflows: list workflows
- get_calendars: list calendars
- get_tags: list all tags
- get_forms: list forms
- get_custom_fields: list custom fields
- system_status: full system overview

BROWSER ACTIONS (slow, opens GHL in browser):
- build_workflow: create a new workflow. params: {name, description}
- setup_ivr: configure IVR/phone tree. params: {description}
- setup_voice_ai: configure Voice AI agent. params: {description}
- setup_conversation_ai: configure Conversation AI. params: {description}
- edit_page: edit a GHL page/funnel. params: {page_name}
- configure_phone: phone system settings. params: {description}
- navigate: just open a GHL page. params: {page: dashboard/workflows/contacts/etc}

For workflow/IVR/Voice AI tasks, write a detailed ghl_ai_prompt that GHL's built-in AI Builder can use.
"""


def classify_task(user_input):
    """Use Groq (free) to classify the task."""
    if not GROQ_KEY:
        log("CLASSIFY", "No GROQ_API_KEY, defaulting to browser")
        return {"type": "browser", "action": "navigate", "params": {"page": "dashboard"}, "explanation": "No AI key"}

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": CLASSIFIER_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.1,
                "max_tokens": 1000,
            },
            timeout=15,
        )
        if r.ok:
            text = r.json()["choices"][0]["message"]["content"]
            # Extract JSON from response
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        else:
            log("CLASSIFY", f"Groq error: {r.status_code}")
    except Exception as e:
        log("CLASSIFY", f"Error: {str(e)[:100]}")

    return {"type": "browser", "action": "navigate", "params": {"page": "dashboard"}, "explanation": "Classification failed"}


# ============================================================
# 2. API EXECUTOR — Fast GHL API calls
# ============================================================
def ghl_api(method, endpoint, params=None, json_data=None):
    """Make a GHL API call."""
    url = f"{GHL_API_BASE}{endpoint}"
    if params is None:
        params = {}
    params.setdefault("locationId", GHL_LOCATION_ID)

    try:
        if method == "GET":
            r = requests.get(url, headers=GHL_API_HEADERS, params=params, timeout=15)
        elif method == "POST":
            r = requests.post(url, headers=GHL_API_HEADERS, json=json_data or {}, timeout=15)
        elif method == "PUT":
            r = requests.put(url, headers=GHL_API_HEADERS, json=json_data or {}, timeout=15)
        else:
            return {"error": f"Unknown method: {method}"}

        if r.status_code in (200, 201):
            return r.json()
        else:
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


def execute_api_task(task):
    """Execute an API-based task."""
    action = task.get("action", "")
    params = task.get("params", {})
    log("API", f"Executing: {action}")
    audit("api_task", f"{action}: {json.dumps(params)[:200]}")

    if action == "get_contacts":
        query = params.get("query", "")
        limit = params.get("limit", 20)
        p = {"locationId": GHL_LOCATION_ID, "limit": limit}
        if query:
            p["query"] = query
        return ghl_api("GET", "/contacts/", params=p)

    elif action == "create_contact":
        data = {"locationId": GHL_LOCATION_ID}
        if "name" in params:
            parts = params["name"].split(" ", 1)
            data["firstName"] = parts[0]
            if len(parts) > 1:
                data["lastName"] = parts[1]
        if "email" in params:
            data["email"] = params["email"]
        if "phone" in params:
            data["phone"] = params["phone"]
        if "tags" in params:
            data["tags"] = params["tags"] if isinstance(params["tags"], list) else [params["tags"]]
        return ghl_api("POST", "/contacts/", json_data=data)

    elif action == "send_sms":
        data = {
            "type": "SMS",
            "contactId": params.get("contact_id", ""),
            "message": params.get("message", ""),
        }
        return ghl_api("POST", "/conversations/messages", json_data=data)

    elif action == "send_email":
        data = {
            "type": "Email",
            "contactId": params.get("contact_id", ""),
            "subject": params.get("subject", ""),
            "message": params.get("body", ""),
            "html": params.get("body", ""),
        }
        return ghl_api("POST", "/conversations/messages", json_data=data)

    elif action == "get_pipelines":
        return ghl_api("GET", "/opportunities/pipelines")

    elif action == "get_opportunities":
        p = {"locationId": GHL_LOCATION_ID, "limit": 50}
        if "pipeline_id" in params:
            p["pipelineId"] = params["pipeline_id"]
        return ghl_api("GET", "/opportunities/search", params=p)

    elif action == "get_workflows":
        return ghl_api("GET", "/workflows/")

    elif action == "get_calendars":
        return ghl_api("GET", "/calendars/")

    elif action == "get_tags":
        return ghl_api("GET", f"/locations/{GHL_LOCATION_ID}/tags")

    elif action == "get_forms":
        return ghl_api("GET", "/forms/")

    elif action == "get_custom_fields":
        return ghl_api("GET", f"/locations/{GHL_LOCATION_ID}/customFields")

    elif action == "system_status":
        status = {}
        for name, endpoint in [
            ("contacts", "/contacts/"),
            ("pipelines", "/opportunities/pipelines"),
            ("workflows", "/workflows/"),
            ("calendars", "/calendars/"),
            ("tags", f"/locations/{GHL_LOCATION_ID}/tags"),
            ("forms", "/forms/"),
        ]:
            status[name] = ghl_api("GET", endpoint)
        return status

    else:
        return {"error": f"Unknown API action: {action}"}


# ============================================================
# 3. BROWSER EXECUTOR — Playwright for UI tasks
# ============================================================
async def execute_browser_task(task):
    """Execute a browser-based task in GHL."""
    action = task.get("action", "")
    params = task.get("params", {})
    ai_prompt = task.get("ghl_ai_prompt", "")
    log("BROWSER", f"Executing: {action}")
    audit("browser_task", f"{action}: {json.dumps(params)[:200]}")

    # Import browser resilience
    sys.path.insert(0, str(AGENT_DIR))
    from browser_resilience import ResilientBrowser

    async with ResilientBrowser(profile="ghl-doer", headless=False) as browser:
        # Navigate to GHL
        target_page = params.get("page", "dashboard")
        url = GHL_URLS.get(target_page, GHL_URLS["dashboard"])

        if action == "navigate":
            url = GHL_URLS.get(params.get("page", "dashboard"), GHL_URLS["dashboard"])

        elif action in ("build_workflow", "setup_ivr"):
            url = GHL_URLS["workflows"]

        elif action in ("setup_voice_ai", "setup_conversation_ai"):
            url = GHL_URLS["ai_agents"]

        elif action == "configure_phone":
            url = GHL_URLS["phone_system"]

        page = await browser.goto(url)
        await page.wait_for_timeout(3000)

        # Check if logged in
        if "login" in page.url.lower() or "/location/" not in page.url:
            log("BROWSER", "Not logged in, logging in...")
            await browser.goto("https://app.gohighlevel.com/")
            await page.wait_for_timeout(2000)

            try:
                email_input = page.locator('input[type="email"], input[name="email"]').first
                await email_input.fill(LILLY_EMAIL, timeout=5000)
                await page.wait_for_timeout(500)

                pass_input = page.locator('input[type="password"]').first
                await pass_input.fill(LILLY_PASS, timeout=5000)
                await page.wait_for_timeout(500)

                login_btn = page.locator('button[type="submit"]').first
                await login_btn.click(timeout=5000)
                await page.wait_for_timeout(8000)

                if "/location/" not in page.url:
                    await browser.wait_for_human("Login failed or needs 2FA — please log in manually")
            except Exception as e:
                log("BROWSER", f"Login error: {str(e)[:100]}")
                await browser.wait_for_human("Could not auto-login — please log in manually")

            # Navigate to target after login
            page = await browser.goto(url)
            await page.wait_for_timeout(3000)

        # Check for CAPTCHA
        await browser.check_for_captcha()

        # Take screenshot of current state
        await browser.screenshot(f"ghl-{action}-start")

        # ── WORKFLOW BUILDER ──
        if action in ("build_workflow", "setup_ivr") and ai_prompt:
            log("BROWSER", "Looking for AI Builder button...")
            await page.wait_for_timeout(2000)

            # Dismiss any popups first
            from browser_resilience import clear_all_overlays
            await clear_all_overlays(page)

            # Look for "Build using AI" or "Create Workflow" button
            found_ai = False

            # Check main page and all frames
            all_targets = [page] + page.frames
            for target in all_targets:
                try:
                    ai_btn = target.locator('button:has-text("Build using AI")')
                    if await ai_btn.count() > 0 and await ai_btn.first.is_visible(timeout=3000):
                        await ai_btn.first.click()
                        log("BROWSER", "Clicked 'Build using AI'!")
                        found_ai = True
                        await page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue

            if not found_ai:
                # Try "Create Workflow" first, then look for AI option
                for target in all_targets:
                    try:
                        create_btn = target.locator('button:has-text("Create Workflow")')
                        if await create_btn.count() > 0:
                            await create_btn.first.click()
                            log("BROWSER", "Clicked 'Create Workflow'")
                            await page.wait_for_timeout(2000)

                            # Now look for AI builder option
                            ai_opt = target.locator('button:has-text("AI"), [data-testid*="ai"]')
                            if await ai_opt.count() > 0:
                                await ai_opt.first.click()
                                found_ai = True
                                await page.wait_for_timeout(2000)
                            break
                    except Exception:
                        continue

            if found_ai:
                # Find the text input and paste the AI prompt
                for target in all_targets:
                    try:
                        textarea = target.locator('textarea, [contenteditable="true"], input[type="text"]').first
                        if await textarea.is_visible(timeout=3000):
                            await textarea.fill(ai_prompt)
                            log("BROWSER", f"Pasted AI prompt ({len(ai_prompt)} chars)")
                            await page.wait_for_timeout(1000)

                            # Click generate/submit
                            gen_btn = target.locator('button:has-text("Generate"), button:has-text("Build"), button:has-text("Create"), button[type="submit"]').first
                            if await gen_btn.is_visible(timeout=3000):
                                await gen_btn.click()
                                log("BROWSER", "Clicked Generate! Waiting for AI to build...")
                                await page.wait_for_timeout(15000)  # AI takes time
                                await browser.screenshot(f"ghl-{action}-result")
                                log("BROWSER", "✅ Workflow generation submitted!")
                            break
                    except Exception:
                        continue
            else:
                log("BROWSER", "Could not find AI Builder button")
                await browser.screenshot(f"ghl-{action}-no-ai-btn")
                await browser.wait_for_human(
                    f"I couldn't find the AI Builder button. The browser is open at the workflows page.\n"
                    f"Please click 'Build using AI' manually, paste this prompt, and press Enter:\n\n"
                    f"{ai_prompt[:200]}..."
                )

        # ── VOICE AI / CONVERSATION AI ──
        elif action in ("setup_voice_ai", "setup_conversation_ai"):
            log("BROWSER", f"Navigated to AI Agents page for {action}")
            await browser.screenshot(f"ghl-{action}-page")
            await browser.wait_for_human(
                f"I've opened the AI Agents page. Here's what to configure:\n\n"
                f"{task.get('explanation', params.get('description', 'Set up AI agent'))}\n\n"
                f"Please make the changes in the browser, then press Enter to continue."
            )

        # ── JUST NAVIGATE ──
        elif action == "navigate":
            log("BROWSER", f"Opened: {url}")
            await browser.screenshot(f"ghl-navigate-{target_page}")

        # ── GENERIC BROWSER TASK ──
        else:
            log("BROWSER", f"Opened GHL for: {action}")
            await browser.screenshot(f"ghl-{action}")
            await browser.wait_for_human(
                f"I've opened GHL. Task: {task.get('explanation', action)}\n"
                f"Please complete the task in the browser, then press Enter."
            )

        # Final screenshot
        await browser.screenshot(f"ghl-{action}-done")
        return {"status": "done", "action": action, "url": page.url}


# ============================================================
# 4. RESULT FORMATTER — Make API results readable
# ============================================================
def format_result(result, action):
    """Format API results for human reading."""
    if isinstance(result, dict) and "error" in result:
        return f"❌ Error: {result['error']}"

    if action == "get_contacts":
        contacts = result.get("contacts", [])
        if not contacts:
            return "No contacts found."
        lines = [f"📋 Found {len(contacts)} contacts:\n"]
        for c in contacts[:10]:
            name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() or "Unknown"
            email = c.get("email", "—")
            phone = c.get("phone", "—")
            tags = ", ".join(c.get("tags", [])) or "—"
            lines.append(f"  • {name} | {email} | {phone} | Tags: {tags}")
        return "\n".join(lines)

    elif action == "get_pipelines":
        pipelines = result.get("pipelines", [])
        if not pipelines:
            return "No pipelines found."
        lines = [f"🎯 {len(pipelines)} pipelines:\n"]
        for p in pipelines:
            stages = [s["name"] for s in p.get("stages", [])]
            lines.append(f"  • {p['name']} — Stages: {', '.join(stages)}")
        return "\n".join(lines)

    elif action == "get_workflows":
        workflows = result.get("workflows", [])
        if not workflows:
            return "No workflows found."
        lines = [f"⚡ {len(workflows)} workflows:\n"]
        for w in workflows:
            status = w.get("status", "unknown")
            lines.append(f"  • {w['name']} [{status}]")
        return "\n".join(lines)

    elif action == "get_tags":
        tags = result.get("tags", [])
        if not tags:
            return "No tags found."
        tag_names = [t["name"] for t in tags]
        return f"🏷️ {len(tags)} tags: {', '.join(tag_names)}"

    elif action == "system_status":
        lines = ["# 📊 GHL System Status\n"]
        for section, data in result.items():
            if isinstance(data, dict) and "error" in data:
                lines.append(f"  {section}: ❌ {data['error'][:50]}")
            elif isinstance(data, dict):
                # Count items
                for key in data:
                    if isinstance(data[key], list):
                        lines.append(f"  {section}: {len(data[key])} items")
                        break
                else:
                    lines.append(f"  {section}: ✅ loaded")
            else:
                lines.append(f"  {section}: ✅")
        return "\n".join(lines)

    else:
        return json.dumps(result, indent=2)[:2000]


# ============================================================
# 5. MAIN — Interactive loop
# ============================================================
async def run_task(user_input):
    """Process a single task."""
    print(f"\n{'='*60}")
    print(f"  📝 Task: {user_input}")
    print(f"{'='*60}")

    # Step 1: Classify
    log("THINK", "Classifying task...")
    task = classify_task(user_input)
    log("THINK", f"Type: {task.get('type')} | Action: {task.get('action')} | {task.get('explanation', '')}")

    # Step 2: Execute
    if task.get("type") == "api":
        result = execute_api_task(task)
        output = format_result(result, task.get("action", ""))
        print(f"\n{output}")
        return result
    else:
        result = await execute_browser_task(task)
        print(f"\n  ✅ Browser task complete: {task.get('action')}")
        return result


async def interactive():
    """Interactive mode — keep asking for tasks."""
    print("\n" + "=" * 60)
    print("  🤖 GHL Doer Agent — Tell me what to do")
    print("  Type a task in plain English, or 'quit' to exit")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n  You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("  👋 Done.")
                break
            await run_task(user_input)
        except KeyboardInterrupt:
            print("\n  👋 Done.")
            break
        except Exception as e:
            log("ERROR", str(e))
            import traceback
            traceback.print_exc()


def main():
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        asyncio.run(run_task(task))
    else:
        asyncio.run(interactive())


if __name__ == "__main__":
    main()
