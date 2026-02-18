"""
GHL Page Access Fixer — Three approaches to unlock blank pages
================================================================
1. Navigate to Settings (which renders) and click Phone System link
2. Try logging in with lilly@ credentials (different permissions)
3. Check agency-level settings for feature access

Connects to Chrome via CDP (port 9222).
"""

import asyncio
import os
import time
import socket
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv(Path(__file__).parent.parent / ".env")

AGENT_DIR = Path(__file__).parent
LOG_DIR = AGENT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

GHL_LOCATION = os.getenv("GHL_LOCATION_ID", "KbiucErIMNPbO1mY4qXL")
BASE = f"https://app.gohighlevel.com/location/{GHL_LOCATION}"
GHL_LOGIN_URL = "https://app.gohighlevel.com/"

LILLY_EMAIL = os.getenv("GHL_EMAIL", "")
LILLY_PASS = os.getenv("GHL_PASSWORD", "")

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT = 9222


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


async def screenshot(page, name):
    path = str(LOG_DIR / f"{name}-{int(time.time())}.png")
    try:
        await page.screenshot(path=path, timeout=10000)
        log("SCREENSHOT", path)
    except Exception:
        log("SCREENSHOT", f"FAILED: {name}")
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
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
    except Exception:
        pass


async def wait_and_check(page, timeout=15000):
    """Wait for page load and return (element_count, text_length, body_text)."""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    await page.wait_for_timeout(2000)
    await dismiss_modals(page)
    await page.wait_for_timeout(1000)

    el_count = await page.evaluate("document.querySelectorAll('*').length")
    try:
        body_text = await page.inner_text("body")
        text_len = len(body_text.strip())
    except Exception:
        body_text = ""
        text_len = 0

    return el_count, text_len, body_text


async def is_logged_in(page):
    url = page.url
    return "/location/" in url and "login" not in url


async def auto_login(page, email, password):
    """Auto-login to GHL with given credentials."""
    log("LOGIN", f"Logging in as {email}...")
    await page.goto(GHL_LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    # Check if already logged in
    if await is_logged_in(page):
        log("LOGIN", "Already logged in")
        return True

    try:
        # Fill email
        email_input = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first
        await email_input.fill(email, timeout=5000)
        await page.wait_for_timeout(500)

        # Fill password
        pass_input = page.locator('input[type="password"], input[name="password"]').first
        await pass_input.fill(password, timeout=5000)
        await page.wait_for_timeout(500)

        # Click sign in
        login_btn = page.locator('button[type="submit"], button:has-text("Sign"), button:has-text("Log")').first
        await login_btn.click(timeout=5000)
        log("LOGIN", "Submitted login form")

        # Wait for redirect
        await page.wait_for_timeout(8000)

        if await is_logged_in(page):
            log("LOGIN", f"Logged in as {email}")
            return True
        else:
            log("LOGIN", f"Login may have failed. URL: {page.url}")
            await screenshot(page, "login-result")
            return await is_logged_in(page)
    except Exception as e:
        log("LOGIN_ERROR", str(e))
        await screenshot(page, "login-error")
        return False


async def check_page_renders(page, name, url):
    """Navigate to a URL and check if it renders."""
    log("CHECK", f"{name}: {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    el_count, text_len, body_text = await wait_and_check(page)
    renders = el_count > 150 and text_len > 50
    status = "RENDERS" if renders else "BLANK"
    log("STATUS", f"{name}: {status} (elements={el_count}, text={text_len})")
    return renders, body_text


# ============================================================
# APPROACH 1: Click Phone System from Settings sidebar
# ============================================================
async def approach_1_click_from_settings(page):
    """Navigate to Settings (which renders) and click Phone System link."""
    log("APPROACH_1", "Clicking Phone System from Settings sidebar...")

    renders, body_text = await check_page_renders(page, "Settings", f"{BASE}/settings")
    if not renders:
        log("APPROACH_1", "Settings page didn't render either!")
        return False

    await screenshot(page, "a1-settings-page")

    # Click "Phone System" link in the sidebar
    try:
        phone_link = page.locator('a:has-text("Phone System")').first
        await phone_link.wait_for(state="visible", timeout=5000)
        await phone_link.click()
        log("APPROACH_1", "Clicked 'Phone System' link")
        await page.wait_for_timeout(3000)
    except Exception as e:
        log("APPROACH_1", f"Could not click Phone System link: {e}")
        return False

    # Check if the phone system page rendered
    el_count, text_len, body_text = await wait_and_check(page)
    renders = el_count > 150 and text_len > 50
    await screenshot(page, "a1-phone-system")

    if renders:
        log("APPROACH_1", f"Phone System page RENDERS! ({el_count} elements, {text_len} chars)")
        log("CONTENT", body_text[:300])
        return True
    else:
        log("APPROACH_1", f"Phone System still blank ({el_count} elements)")

        # Try other links from settings
        for link_text in ["Calendars", "Email Services", "WhatsApp", "Billing"]:
            try:
                link = page.locator(f'a:has-text("{link_text}")').first
                if await link.is_visible(timeout=2000):
                    await link.click()
                    await page.wait_for_timeout(3000)
                    el2, txt2, body2 = await wait_and_check(page)
                    r2 = el2 > 150 and txt2 > 50
                    log("APPROACH_1", f"  {link_text}: {'RENDERS' if r2 else 'BLANK'} ({el2} el, {txt2} txt)")
                    if r2:
                        await screenshot(page, f"a1-{link_text.lower().replace(' ', '-')}")
                    # Go back to settings
                    await page.goto(f"{BASE}/settings", wait_until="domcontentloaded", timeout=15000)
                    await wait_and_check(page)
            except Exception:
                continue

        return False


# ============================================================
# APPROACH 2: Login with lilly@ credentials
# ============================================================
async def approach_2_lilly_login(page):
    """Sign out and log in with lilly@ credentials to check different permissions."""
    log("APPROACH_2", "Trying lilly@ login for different permissions...")

    # First sign out
    try:
        # Navigate to a page that renders
        await page.goto(f"{BASE}/dashboard", wait_until="domcontentloaded", timeout=15000)
        await wait_and_check(page)

        # Try to find sign out
        signout = page.locator('a:has-text("Signout"), a:has-text("Sign Out"), button:has-text("Sign Out")')
        if await signout.count() > 0:
            await signout.first.click()
            await page.wait_for_timeout(3000)
            log("APPROACH_2", "Signed out")
        else:
            # Try via URL
            await page.goto("https://app.gohighlevel.com/logout", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)
            log("APPROACH_2", "Navigated to logout URL")
    except Exception as e:
        log("APPROACH_2", f"Sign out issue: {e}")

    # Login with lilly@
    success = await auto_login(page, LILLY_EMAIL, LILLY_PASS)
    if not success:
        log("APPROACH_2", "Could not log in with lilly@ credentials")
        return False

    await screenshot(page, "a2-lilly-logged-in")

    # Check key pages
    test_pages = [
        ("Workflows", f"{BASE}/automation/list"),
        ("Phone System", f"{BASE}/settings/phone-system"),
        ("AI Agents", f"{BASE}/ai-agents"),
    ]

    for name, url in test_pages:
        renders, body_text = await check_page_renders(page, name, url)
        await screenshot(page, f"a2-lilly-{name.lower().replace(' ', '-')}")
        if renders:
            log("APPROACH_2", f"{name} RENDERS with lilly@ login!")
            return True

    log("APPROACH_2", "Same blank pages with lilly@ login")
    return False


# ============================================================
# APPROACH 3: Check agency-level settings
# ============================================================
async def approach_3_agency_settings(page):
    """Check agency-level settings and billing to understand feature access."""
    log("APPROACH_3", "Checking agency settings and billing...")

    # Check billing page
    renders, body_text = await check_page_renders(page, "Billing", f"{BASE}/settings/billing")
    if renders:
        await screenshot(page, "a3-billing")
        log("BILLING", body_text[:400])

        # Look for plan info
        for keyword in ["plan", "subscription", "upgrade", "pro", "premium", "starter", "unlimited"]:
            if keyword in body_text.lower():
                log("PLAN_INFO", f"Found '{keyword}' in billing page")

    # Check the v2 settings URL (Settings redirected to v2 earlier)
    v2_pages = [
        ("V2 Profile", f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/settings/profile"),
        ("V2 Phone", f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/settings/phone-number"),
        ("V2 Phone System", f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/settings/phone-system"),
        ("V2 Workflows", f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/automation/list"),
        ("V2 AI Agents", f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/ai-agents"),
    ]

    for name, url in v2_pages:
        renders, body_text = await check_page_renders(page, name, url)
        if renders:
            await screenshot(page, f"a3-{name.lower().replace(' ', '-')}")
            log("APPROACH_3", f"{name} RENDERS!")
            if "phone" in name.lower() or "workflow" in name.lower() or "ai" in name.lower():
                log("APPROACH_3", f"Found working page: {name}")
                log("CONTENT", body_text[:400])
                return True

    log("APPROACH_3", "No v2 pages rendered either")
    return False


# ============================================================
# MAIN
# ============================================================
async def main():
    print("\n" + "=" * 60)
    print("  GHL Page Access Fixer — 3 Approaches")
    print("=" * 60)

    def port_open(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    if not port_open(DEBUG_PORT):
        log("CHROME", "Launching Chrome with debug port...")
        subprocess.Popen([
            CHROME_EXE,
            f"--remote-debugging-port={DEBUG_PORT}",
            "--profile-directory=Profile 4",
            "--no-first-run", "--no-default-browser-check",
        ])
        for _ in range(30):
            if port_open(DEBUG_PORT):
                break
            await asyncio.sleep(1)
        else:
            print("  Chrome did not start. Exiting.")
            return

    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")
    context = browser.contexts[0]
    page = await context.new_page()
    log("START", "Connected to Chrome via CDP")

    try:
        # Make sure we're logged in first
        await page.goto(f"{BASE}/dashboard", wait_until="domcontentloaded", timeout=20000)
        el_count, text_len, body_text = await wait_and_check(page)

        if not await is_logged_in(page):
            log("LOGIN", "Not logged in, auto-logging in...")
            success = await auto_login(page, LILLY_EMAIL, LILLY_PASS)
            if not success:
                print("\n  Could not log in. Exiting.")
                return

        # ── APPROACH 1: Click from Settings ──
        print("\n" + "-" * 50)
        print("  APPROACH 1: Click Phone System from Settings")
        print("-" * 50)
        if await approach_1_click_from_settings(page):
            print("\n  APPROACH 1 SUCCEEDED!")
            print("  Phone System page is accessible via Settings sidebar.")
            await keep_open()
            return

        # ── APPROACH 2: Lilly login ──
        print("\n" + "-" * 50)
        print("  APPROACH 2: Login with lilly@ credentials")
        print("-" * 50)
        if await approach_2_lilly_login(page):
            print("\n  APPROACH 2 SUCCEEDED!")
            print("  Different login unlocked the pages.")
            await keep_open()
            return

        # ── APPROACH 3: Agency/V2 settings ──
        print("\n" + "-" * 50)
        print("  APPROACH 3: Check agency settings & V2 URLs")
        print("-" * 50)
        if await approach_3_agency_settings(page):
            print("\n  APPROACH 3 SUCCEEDED!")
            print("  V2 URLs work for this feature.")
            await keep_open()
            return

        # All approaches failed
        print("\n" + "=" * 60)
        print("  ALL 3 APPROACHES FAILED")
        print("=" * 60)
        print("  The phone system, workflows, and AI agents pages")
        print("  are all blank. This is likely because:")
        print("  1. The GHL plan doesn't include these features")
        print("  2. Features need to be enabled at the agency level")
        print("  3. The sub-account needs specific permissions")
        print("")
        print("  NEXT STEPS:")
        print("  - Check GHL agency settings (agency-level login)")
        print("  - Verify the plan includes Phone System & Workflows")
        print("  - Contact GHL support if features should be available")
        print("  - Use GHL API as alternative (some endpoints work)")
        print("=" * 60)

        await screenshot(page, "all-approaches-failed")

    except Exception as e:
        log("ERROR", str(e))
        import traceback
        traceback.print_exc()
        await screenshot(page, "error")
    finally:
        await browser.close()
        await pw.stop()


async def keep_open():
    print("\n  Browser stays open. Press Ctrl+C to disconnect.")
    try:
        while True:
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("  Disconnecting...")


if __name__ == "__main__":
    asyncio.run(main())
