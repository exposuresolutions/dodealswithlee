"""
Exposure Solutions Signup Agent
================================
Browser automation agent that can:
1. Sign up for free API services
2. Extract API keys from dashboards
3. Store keys in .env and brain.json
4. Maintain persistent browser profiles (stays logged in)
5. Self-upgrade by adding new services

Uses Playwright with persistent browser contexts so logins survive between runs.
All agents share brain.json as the single source of truth.
"""

import json
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv, set_key

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).parent.parent  # DDWL root
AGENT_DIR = Path(__file__).parent        # agent-skills/
BRAIN_FILE = AGENT_DIR / "brain.json"
ENV_FILE = BASE_DIR / ".env"
LOG_DIR = AGENT_DIR / "logs"
PROFILE_DIR = AGENT_DIR / "browser-profiles"

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

# Load env
load_dotenv(ENV_FILE)


# ============================================================
# SHARED BRAIN — read/write the central config
# ============================================================
class Brain:
    """Single source of truth for all agent state."""

    def __init__(self, path=BRAIN_FILE):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, "r") as f:
                return json.load(f)
        return {"services": {}, "browser_profiles": {}, "_meta": {}}

    def save(self):
        self.data["_meta"]["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data["_meta"]["updated_by"] = "exposure_agent"
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_service(self, name):
        return self.data.get("services", {}).get(name, None)

    def set_service_status(self, name, status):
        if name in self.data.get("services", {}):
            self.data["services"][name]["status"] = status
            self.save()

    def add_service(self, name, config):
        self.data.setdefault("services", {})[name] = config
        self.save()

    def get_services_needing_signup(self):
        return {
            k: v for k, v in self.data.get("services", {}).items()
            if v.get("status") == "needs_signup"
        }

    def get_all_services(self):
        return self.data.get("services", {})


# ============================================================
# LOGGER — audit trail for all agent actions
# ============================================================
class AgentLogger:
    def __init__(self):
        self.log_file = LOG_DIR / f"agent-{datetime.now().strftime('%Y%m%d')}.log"

    def log(self, action, details=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{action}] {details}"
        print(entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")


# ============================================================
# ENV MANAGER — read/write .env file
# ============================================================
class EnvManager:
    def __init__(self, env_path=ENV_FILE):
        self.env_path = str(env_path)

    def get(self, key):
        load_dotenv(self.env_path, override=True)
        return os.getenv(key)

    def set(self, key, value):
        # Write directly to avoid python-dotenv wrapping values in quotes
        lines = []
        found = False
        with open(self.env_path, "r") as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
        if not found:
            lines.append(f"{key}={value}\n")
        with open(self.env_path, "w") as f:
            f.writelines(lines)
        os.environ[key] = value

    def has(self, key):
        load_dotenv(self.env_path, override=True)
        val = os.getenv(key)
        return val is not None and val != "" and not val.startswith("paste-your")

    def list_keys(self):
        load_dotenv(self.env_path, override=True)
        keys = {}
        with open(self.env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    keys[k.strip()] = "SET" if v.strip() and not v.strip().startswith("paste-your") else "MISSING"
        return keys


# ============================================================
# BROWSER AGENT — Playwright with persistent profiles
# ============================================================
class BrowserAgent:
    """
    Browser automation with persistent login sessions.
    Uses Playwright persistent contexts so cookies/sessions survive between runs.
    """

    def __init__(self, profile_name="exposure-agent", headless=False):
        self.profile_name = profile_name
        self.profile_path = str(PROFILE_DIR / profile_name)
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.logger = AgentLogger()

    async def start(self):
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().start()
        self.context = await self._pw.chromium.launch_persistent_context(
            user_data_dir=self.profile_path,
            headless=self.headless,
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            ignore_default_args=["--enable-automation"],
        )
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
        self.logger.log("BROWSER_START", f"Profile: {self.profile_name}, Headless: {self.headless}")
        return self

    async def goto(self, url, wait_until="domcontentloaded"):
        self.logger.log("NAVIGATE", url)
        await self.page.goto(url, wait_until=wait_until, timeout=30000)
        await self.page.wait_for_timeout(1000)
        return self.page

    async def screenshot(self, name="screenshot"):
        path = str(LOG_DIR / f"{name}-{int(time.time())}.png")
        await self.page.screenshot(path=path)
        self.logger.log("SCREENSHOT", path)
        return path

    async def get_text(self):
        return await self.page.inner_text("body")

    async def click(self, selector, timeout=5000):
        self.logger.log("CLICK", selector)
        await self.page.click(selector, timeout=timeout)
        await self.page.wait_for_timeout(500)

    async def fill(self, selector, value, timeout=5000):
        self.logger.log("FILL", f"{selector} = [REDACTED]")
        await self.page.fill(selector, value, timeout=timeout)

    async def wait_for(self, selector, timeout=10000):
        await self.page.wait_for_selector(selector, timeout=timeout)

    async def get_url(self):
        return self.page.url

    async def close(self):
        if self.context:
            await self.context.close()
        if hasattr(self, '_pw') and self._pw:
            await self._pw.stop()
        self.logger.log("BROWSER_CLOSE", f"Profile: {self.profile_name}")


# ============================================================
# API KEY EXTRACTORS — per-service logic
# ============================================================
class GroqExtractor:
    """Navigate to Groq console and extract API key."""

    @staticmethod
    async def check_login(agent):
        await agent.goto("https://console.groq.com/keys")
        await agent.page.wait_for_timeout(3000)
        text = await agent.get_text()
        # If we see "Create an account" or "Continue with Google", we're on the login page
        if "Create an account" in text or "Continue with Google" in text:
            return False
        return True

    @staticmethod
    async def extract_key(agent):
        """If already logged in, try to create and extract a key."""
        await agent.goto("https://console.groq.com/keys")
        await agent.page.wait_for_timeout(2000)
        text = await agent.get_text()
        await agent.screenshot("groq-keys-page")
        return text


class OpenRouterExtractor:
    """Navigate to OpenRouter and extract API key."""

    @staticmethod
    async def check_login(agent):
        await agent.goto("https://openrouter.ai/settings/keys")
        await agent.page.wait_for_timeout(2000)
        url = await agent.get_url()
        return "settings" in url and "auth" not in url

    @staticmethod
    async def extract_key(agent):
        await agent.goto("https://openrouter.ai/settings/keys")
        await agent.page.wait_for_timeout(2000)
        text = await agent.get_text()
        await agent.screenshot("openrouter-keys-page")
        return text


class GoogleAIExtractor:
    """Navigate to Google AI Studio and check API key."""

    @staticmethod
    async def check_login(agent):
        await agent.goto("https://aistudio.google.com/apikey")
        await agent.page.wait_for_timeout(3000)
        url = await agent.get_url()
        return "apikey" in url

    @staticmethod
    async def extract_key(agent):
        await agent.goto("https://aistudio.google.com/apikey")
        await agent.page.wait_for_timeout(3000)
        text = await agent.get_text()
        await agent.screenshot("google-ai-keys-page")
        return text


# ============================================================
# MAIN AGENT ORCHESTRATOR
# ============================================================
class ExposureAgent:
    """
    Main orchestrator that:
    1. Reads the shared brain
    2. Checks what services need signup/keys
    3. Launches browser with persistent profile
    4. Navigates to each service
    5. Extracts API keys
    6. Stores them in .env and brain.json
    """

    EXTRACTORS = {
        "groq": GroqExtractor,
        "openrouter": OpenRouterExtractor,
        "google": GoogleAIExtractor,
    }

    def __init__(self):
        self.brain = Brain()
        self.env = EnvManager()
        self.logger = AgentLogger()

    def status(self):
        """Print current status of all services and keys."""
        print("\n" + "=" * 60)
        print("  EXPOSURE AGENT — System Status")
        print("=" * 60)

        env_keys = self.env.list_keys()
        services = self.brain.get_all_services()

        print(f"\n  Brain file: {BRAIN_FILE}")
        print(f"  Env file:   {ENV_FILE}")
        print(f"  Profiles:   {PROFILE_DIR}")
        print(f"  Logs:       {LOG_DIR}")

        print(f"\n  {'Service':<20} {'Status':<15} {'Tier':<8} {'Env Key':<25} {'Key Set?':<10}")
        print("  " + "-" * 78)

        for name, svc in services.items():
            env_key = svc.get("env_key", "")
            key_status = env_keys.get(env_key, "N/A")
            status = svc.get("status", "unknown")
            tier = svc.get("tier", "?")

            status_icon = "✓" if status == "active" else "⚠" if status == "needs_signup" else "?"
            key_icon = "✓" if key_status == "SET" else "✗"

            print(f"  {name:<20} {status_icon} {status:<13} {tier:<8} {env_key:<25} {key_icon} {key_status}")

        # Check for services that need action
        needs_signup = self.brain.get_services_needing_signup()
        if needs_signup:
            print(f"\n  ⚠ Services needing signup: {', '.join(needs_signup.keys())}")
        else:
            print(f"\n  ✓ All services configured")

        print("=" * 60 + "\n")

    async def check_service(self, service_name):
        """Check if we're logged into a service and can access its API keys."""
        extractor = self.EXTRACTORS.get(service_name)
        if not extractor:
            self.logger.log("SKIP", f"No extractor for {service_name}")
            return None

        agent = BrowserAgent(headless=False)
        try:
            await agent.start()
            self.logger.log("CHECK_SERVICE", f"Checking {service_name}...")

            logged_in = await extractor.check_login(agent)
            if logged_in:
                self.logger.log("LOGIN_STATUS", f"{service_name}: LOGGED IN")
                page_text = await extractor.extract_key(agent)
                return {"logged_in": True, "page_text": page_text}
            else:
                self.logger.log("LOGIN_STATUS", f"{service_name}: NOT LOGGED IN — manual login needed")
                current_url = await agent.get_url()
                await agent.screenshot(f"{service_name}-login-needed")

                print(f"\n  ⚠ {service_name}: Not logged in.")
                print(f"  Browser is open at: {current_url}")
                print(f"  Please log in manually, then press Enter to continue...")
                input("  > Press Enter after logging in: ")

                logged_in = await extractor.check_login(agent)
                if logged_in:
                    page_text = await extractor.extract_key(agent)
                    return {"logged_in": True, "page_text": page_text}
                else:
                    return {"logged_in": False, "page_text": None}
        finally:
            await agent.close()

    async def open_dashboard(self, service_name):
        """Open a service dashboard in the persistent browser for manual interaction."""
        svc = self.brain.get_service(service_name)
        if not svc:
            print(f"  Unknown service: {service_name}")
            return

        url = svc.get("dashboard_url") or svc.get("signup_url")
        print(f"\n  Opening {svc['name']} dashboard: {url}")

        agent = BrowserAgent(headless=False)
        await agent.start()
        await agent.goto(url)
        await agent.screenshot(f"{service_name}-dashboard")

        print(f"  Browser is open. Do what you need, then press Enter to close.")
        input("  > Press Enter when done: ")
        await agent.close()

    async def store_key(self, service_name, api_key):
        """Store an API key in .env and update brain status."""
        svc = self.brain.get_service(service_name)
        if not svc:
            print(f"  Unknown service: {service_name}")
            return

        env_key = svc.get("env_key")
        if not env_key:
            print(f"  No env_key defined for {service_name}")
            return

        self.env.set(env_key, api_key)
        self.brain.set_service_status(service_name, "active")
        self.logger.log("KEY_STORED", f"{service_name} -> {env_key} = [REDACTED]")
        print(f"  ✓ Stored {env_key} in .env and updated brain.json")

    async def run_signup_flow(self, service_name):
        """Full flow: open browser, check login, navigate to keys, extract, store."""
        svc = self.brain.get_service(service_name)
        if not svc:
            print(f"  Unknown service: {service_name}")
            return

        print(f"\n{'='*60}")
        print(f"  Signup Flow: {svc['name']}")
        print(f"  URL: {svc.get('signup_url', 'N/A')}")
        print(f"  Tier: {svc.get('tier', '?')}")
        print(f"{'='*60}")

        result = await self.check_service(service_name)

        if result and result.get("logged_in"):
            print(f"\n  ✓ Logged into {svc['name']}")
            print(f"  Screenshot saved to logs/")

            # Check if we already have the key
            env_key = svc.get("env_key")
            if self.env.has(env_key):
                print(f"  ✓ {env_key} already set in .env")
                self.brain.set_service_status(service_name, "active")
            else:
                print(f"\n  ⚠ {env_key} not found in .env")
                print(f"  The API keys page has been screenshotted.")
                print(f"  Please copy your API key from the browser.")
                key = input(f"  > Paste your {svc['name']} API key here: ").strip()
                if key:
                    await self.store_key(service_name, key)
                else:
                    print(f"  Skipped — no key entered")
        else:
            print(f"\n  ✗ Could not access {svc['name']}. Try again or sign up manually at:")
            print(f"    {svc.get('signup_url', 'N/A')}")


# ============================================================
# CLI INTERFACE
# ============================================================
async def main():
    agent = ExposureAgent()

    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command == "status":
        agent.status()

    elif command == "signup":
        if len(sys.argv) < 3:
            # Sign up for all services that need it
            needs = agent.brain.get_services_needing_signup()
            if not needs:
                print("  ✓ All services are configured. Nothing to sign up for.")
                return
            for name in needs:
                await agent.run_signup_flow(name)
        else:
            await agent.run_signup_flow(sys.argv[2])

    elif command == "open":
        if len(sys.argv) < 3:
            print("  Usage: python exposure_agent.py open <service_name>")
            return
        await agent.open_dashboard(sys.argv[2])

    elif command == "check":
        if len(sys.argv) < 3:
            print("  Usage: python exposure_agent.py check <service_name>")
            return
        result = await agent.check_service(sys.argv[2])
        if result:
            print(f"  Logged in: {result['logged_in']}")

    elif command == "store":
        if len(sys.argv) < 4:
            print("  Usage: python exposure_agent.py store <service_name> <api_key>")
            return
        await agent.store_key(sys.argv[2], sys.argv[3])

    elif command == "add":
        if len(sys.argv) < 5:
            print("  Usage: python exposure_agent.py add <name> <signup_url> <env_key> [tier]")
            return
        name = sys.argv[2]
        signup_url = sys.argv[3]
        env_key = sys.argv[4]
        tier = sys.argv[5] if len(sys.argv) > 5 else "free"
        agent.brain.add_service(name, {
            "name": name.title(),
            "status": "needs_signup",
            "env_key": env_key,
            "signup_url": signup_url,
            "dashboard_url": signup_url,
            "tier": tier,
            "models": [],
            "notes": f"Added by agent on {datetime.now().strftime('%Y-%m-%d')}"
        })
        print(f"  ✓ Added {name} to brain.json")

    elif command == "browse":
        # Just open a browser with the persistent profile
        url = sys.argv[2] if len(sys.argv) > 2 else "https://google.com"
        ba = BrowserAgent(headless=False)
        await ba.start()
        await ba.goto(url)
        print(f"  Browser open at {url}. Press Enter to close.")
        input("  > ")
        await ba.close()

    else:
        print_help()


def print_help():
    print("""
╔══════════════════════════════════════════════════════════╗
║          EXPOSURE AGENT — Browser Automation            ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Commands:                                               ║
║                                                          ║
║  status              Show all services & key status      ║
║  signup              Sign up for all pending services    ║
║  signup <service>    Sign up for a specific service      ║
║  open <service>      Open service dashboard in browser   ║
║  check <service>     Check if logged into a service      ║
║  store <svc> <key>   Store an API key for a service      ║
║  add <name> <url> <env_key> [tier]  Add new service      ║
║  browse [url]        Open browser with persistent profile║
║                                                          ║
║  Services: groq, openrouter, google, anthropic,          ║
║            elevenlabs, ghl                               ║
║                                                          ║
║  All logins persist between runs (browser profiles).     ║
║  All keys stored in .env + brain.json (shared brain).    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
