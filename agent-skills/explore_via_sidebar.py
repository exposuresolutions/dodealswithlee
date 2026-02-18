"""
Explore GHL pages via sidebar navigation (the only method that works).
Direct URL navigation renders blank pages, but clicking sidebar links works.

This script:
1. Goes to Settings (renders) → clicks Phone System → explores Voice tab
2. Goes to Dashboard → clicks Automation sidebar link → checks Workflows
3. Goes to Dashboard → clicks AI Agents sidebar link → checks Voice AI
"""

import asyncio
import time
import socket
from pathlib import Path
from playwright.async_api import async_playwright

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

GHL_LOCATION = "KbiucErIMNPbO1mY4qXL"
BASE = f"https://app.gohighlevel.com/location/{GHL_LOCATION}"
DEBUG_PORT = 9222


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


async def ss(page, name):
    path = str(LOG_DIR / f"{name}-{int(time.time())}.png")
    try:
        await page.screenshot(path=path, timeout=10000)
    except Exception:
        pass
    return path


async def dismiss_modals(page):
    try:
        await page.evaluate("""(() => {
            document.querySelectorAll('.modal, .modal-backdrop, .modal-dialog').forEach(el => el.remove());
            document.documentElement.style.overflow = 'auto';
            document.documentElement.classList.remove('overflow-hidden');
            const app = document.getElementById('app');
            if (app) { app.style.overflow = 'auto'; app.style.height = 'auto'; }
            if (app) app.querySelectorAll(':scope > div').forEach(d => {
                d.style.overflow = 'auto'; d.style.height = 'auto';
            });
        })()""")
    except Exception:
        pass


async def wait_load(page, timeout=15000):
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    await page.wait_for_timeout(2000)
    await dismiss_modals(page)
    await page.wait_for_timeout(1000)


async def page_status(page):
    el = await page.evaluate("document.querySelectorAll('*').length")
    try:
        txt = await page.inner_text("body")
        tl = len(txt.strip())
    except Exception:
        txt = ""
        tl = 0
    return el, tl, txt


async def click_and_check(page, selector, label):
    """Click a link/button and check if the resulting page renders."""
    try:
        el = page.locator(selector).first
        await el.wait_for(state="visible", timeout=5000)
        await el.click()
        log("CLICK", f"Clicked: {label}")
        await wait_load(page)
        ec, tl, txt = await page_status(page)
        renders = ec > 150 and tl > 50
        log("RESULT", f"{label}: {'RENDERS' if renders else 'BLANK'} ({ec} el, {tl} chars)")
        await ss(page, label.lower().replace(" ", "-").replace("/", "-"))
        if renders:
            log("URL", page.url)
            # Show buttons and key text
            buttons = await page.locator('button').all_text_contents()
            clean = [b.strip() for b in buttons if b.strip() and len(b.strip()) > 1][:10]
            if clean:
                log("BUTTONS", str(clean))
            log("PREVIEW", txt[:300].replace("\n", " | "))
        return renders, txt
    except Exception as e:
        log("ERROR", f"Could not click {label}: {e}")
        return False, ""


async def main():
    def port_open(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    if not port_open(DEBUG_PORT):
        print("  Chrome not running on port 9222. Start it first.")
        return

    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")
    context = browser.contexts[0]
    page = await context.new_page()

    print("=" * 60)
    print("  GHL Sidebar Navigation Explorer")
    print("=" * 60)

    # ── PART 1: Settings → Phone System → Voice tab ──
    print("\n--- PART 1: Phone System & Voice ---")
    await page.goto(f"{BASE}/settings", wait_until="domcontentloaded", timeout=20000)
    await wait_load(page)

    # Click Phone System
    renders, txt = await click_and_check(page, 'a:has-text("Phone System")', "Phone System")
    if renders:
        # Click Voice tab
        renders2, txt2 = await click_and_check(page, 'a:has-text("Voice"), button:has-text("Voice")', "Voice Tab")
        if not renders2:
            # Try tab-style click
            await click_and_check(page, 'text="Voice"', "Voice Tab v2")

        # Also check the phone number config — click the 3-dot menu on DDWL Main Line
        log("INFO", "Checking DDWL Main Line phone number config...")
        try:
            # Find the row with 813-675-0916
            row = page.locator('text="813-675-0916"').first
            if await row.is_visible(timeout=3000):
                # Click the 3-dot menu (kebab) in that row
                parent = row.locator("xpath=ancestor::tr | ancestor::div[contains(@class,'row')]").first
                kebab = parent.locator('button, [class*="menu"], [class*="dots"], [class*="kebab"]').last
                try:
                    await kebab.click(timeout=3000)
                    await page.wait_for_timeout(1000)
                    await ss(page, "phone-number-menu")
                    # Check what options appear
                    ec, tl, txt = await page_status(page)
                    log("MENU", txt[:200])
                except Exception:
                    # Try clicking the ⋮ directly
                    dots = page.locator('text="⋮", text="..."').first
                    await dots.click(timeout=2000)
                    await page.wait_for_timeout(1000)
                    await ss(page, "phone-number-dots")
        except Exception as e:
            log("INFO", f"Could not find phone number row: {e}")

    # ── PART 2: Dashboard → Automation sidebar ──
    print("\n--- PART 2: Automation/Workflows via sidebar ---")
    await page.goto(f"{BASE}/dashboard", wait_until="domcontentloaded", timeout=20000)
    await wait_load(page)

    renders, txt = await click_and_check(page, 'a:has-text("Automation")', "Automation Sidebar")

    # ── PART 3: Dashboard → AI Agents sidebar ──
    print("\n--- PART 3: AI Agents via sidebar ---")
    await page.goto(f"{BASE}/dashboard", wait_until="domcontentloaded", timeout=20000)
    await wait_load(page)

    renders, txt = await click_and_check(page, 'a:has-text("AI Agents")', "AI Agents Sidebar")

    # ── PART 4: Check other sidebar items ──
    print("\n--- PART 4: Other sidebar items ---")
    for item in ["Conversations", "Contacts", "Opportunities", "Sites", "Reputation", "Reporting"]:
        await page.goto(f"{BASE}/dashboard", wait_until="domcontentloaded", timeout=20000)
        await wait_load(page)
        renders, txt = await click_and_check(page, f'a:has-text("{item}")', item)
        if not renders:
            continue

    print("\n" + "=" * 60)
    print("  Exploration complete.")
    print("=" * 60)

    await browser.close()
    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
