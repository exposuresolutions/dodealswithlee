"""
Quick GHL page explorer — find which pages render and what's available.
Connects to Chrome via CDP (must be running with --remote-debugging-port=9222).
"""

import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

AGENT_DIR = Path(__file__).parent
LOG_DIR = AGENT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

GHL_LOCATION = "KbiucErIMNPbO1mY4qXL"
BASE = f"https://app.gohighlevel.com/location/{GHL_LOCATION}"

# Pages to explore — focus on phone/voice/AI features
PAGES = [
    ("AI Agents", f"{BASE}/ai-agents"),
    ("Voice AI", f"{BASE}/voice-ai"),
    ("Phone", f"{BASE}/phone"),
    ("Phone System Settings", f"{BASE}/settings/phone-system"),
    ("Phone Number Settings", f"{BASE}/settings/phone-number"),
    ("Phone Numbers", f"{BASE}/settings/phone-numbers"),
    ("Twilio Settings", f"{BASE}/settings/twilio"),
    ("Call Tracking", f"{BASE}/settings/call-tracking"),
    ("Conversations Settings", f"{BASE}/settings/conversations"),
    ("Marketing", f"{BASE}/marketing"),
    ("Automation", f"{BASE}/automation/list"),
    ("Settings Main", f"{BASE}/settings"),
    ("Settings Business", f"{BASE}/settings/business-info"),
]


async def dismiss_modals(page):
    try:
        await page.evaluate("""
            (() => {
                document.querySelectorAll('.modal, .modal-backdrop, .modal-dialog').forEach(el => el.remove());
                document.documentElement.style.overflow = 'auto';
                document.documentElement.classList.remove('overflow-hidden');
                const app = document.getElementById('app');
                if (app) { app.style.overflow = 'auto'; app.style.height = 'auto'; }
                if (app) app.querySelectorAll(':scope > div').forEach(d => { d.style.overflow = 'auto'; d.style.height = 'auto'; });
            })()
        """)
    except Exception:
        pass


async def explore_page(page, name, url):
    print(f"\n  [{name}]")
    print(f"    URL: {url}")
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
    except Exception as e:
        print(f"    TIMEOUT: {e}")
        return
    
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    await page.wait_for_timeout(2000)
    await dismiss_modals(page)
    await page.wait_for_timeout(1000)

    # Check final URL (may have redirected)
    final_url = page.url
    if final_url != url:
        print(f"    REDIRECTED TO: {final_url}")

    # Count elements
    el_count = await page.evaluate("document.querySelectorAll('*').length")
    
    # Get body text
    try:
        body_text = await page.inner_text("body")
        text_len = len(body_text.strip())
    except Exception:
        body_text = ""
        text_len = 0

    renders = el_count > 150 and text_len > 50
    status = "RENDERS" if renders else "BLANK"
    print(f"    Status: {status} (elements={el_count}, text={text_len} chars)")

    if renders:
        # Screenshot
        safe = name.lower().replace(" ", "-").replace("/", "-")
        path = str(LOG_DIR / f"explore-{safe}-{int(time.time())}.png")
        try:
            await page.screenshot(path=path, timeout=10000)
            print(f"    Screenshot: {path}")
        except Exception:
            print(f"    Screenshot failed")

        # Show first 200 chars of text
        preview = body_text.strip()[:200].replace("\n", " | ")
        print(f"    Preview: {preview}")

        # List buttons
        buttons = await page.locator('button').all_text_contents()
        clean_buttons = [b.strip() for b in buttons if b.strip()][:10]
        if clean_buttons:
            print(f"    Buttons: {clean_buttons}")

        # List nav links
        links = await page.locator('a').all_text_contents()
        clean_links = [l.strip() for l in links if l.strip() and len(l.strip()) > 2][:15]
        if clean_links:
            print(f"    Links: {clean_links}")


async def main():
    import socket

    def port_open(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    if not port_open(9222):
        print("Chrome not running with debug port 9222. Start it first.")
        return

    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]
    page = await context.new_page()

    print("=" * 60)
    print("  GHL Page Explorer")
    print("=" * 60)

    for name, url in PAGES:
        await explore_page(page, name, url)

    print("\n" + "=" * 60)
    print("  Done. Browser stays open.")
    print("=" * 60)

    await browser.close()
    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
