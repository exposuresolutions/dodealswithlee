"""
DDWL IVR Workflow Builder — Automated via Playwright
=====================================================
Uses the BrowserAgent from exposure_agent.py with a persistent GHL profile.
Step 1: Login check (manual login if needed, session persists)
Step 2: Navigate to existing IVR template workflow
Step 3: Click each node and configure it programmatically

This automates the entire IVR setup without manual clicking.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))
from exposure_agent import AgentLogger

# Paths
AGENT_DIR = Path(__file__).parent
PROFILE_DIR = AGENT_DIR / "browser-profiles" / "ghl-ivr-auto"
LOG_DIR = AGENT_DIR / "logs"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# CONFIG
# ============================================================
GHL_LOCATION = os.getenv("GHL_LOCATION_ID", "KbiucErIMNPbO1mY4qXL")
GHL_WORKFLOWS_URL = f"https://app.gohighlevel.com/location/{GHL_LOCATION}/automation/list"
GHL_PHONE_SETTINGS_URL = f"https://app.gohighlevel.com/location/{GHL_LOCATION}/settings/phone-number"
GHL_LOGIN_URL = "https://app.gohighlevel.com/"
GHL_EMAIL = os.getenv("GHL_EMAIL", "")
GHL_PASSWORD = os.getenv("GHL_PASSWORD", "")
PHONE_NUMBER = "(813) 675-0916"

# IVR Content
GREETING_TEXT = "Thank you for calling Do Deals with Lee. Tampa Bay's trusted real estate investment partner."
MENU_TEXT = (
    "Press 1 to sell your home to Lee. "
    "Press 2 for coaching and events. "
    "Press 3 to do a deal or fund a deal with Lee. "
    "Press 4 for operations and general inquiries. "
    "Press 0 to speak with a team member. "
    "Or stay on the line to leave a message."
)

# Branch configs: key -> (branch_name, say_text, connect_to_users, voicemail_msg)
BRANCHES = {
    "1": {
        "name": "Sell Home",
        "say": "We buy homes fast. No repairs, no fees, no hassle. Let us connect you with our acquisitions team.",
        "connect_users": ["Krystle Gordon", "Lee Kearney"],
        "voicemail": "Please leave your name, number, and property address. We'll get back to you within 24 hours.",
    },
    "2": {
        "name": "Coaching & Events",
        "say": "Lee Kearney offers private one-on-one coaching and live real estate investing events.",
        "sub_menu": {
            "text": "Press 1 for upcoming events. Press 2 for private coaching. Press 0 to go back to the main menu.",
            "1": {"name": "Events", "say": "Visit dodealswithlee.com slash events for our next live event.", "voicemail": True},
            "2": {"name": "Coaching", "connect_users": ["Krystle Gordon"], "voicemail": True},
        },
    },
    "3": {
        "name": "Deals",
        "say": "Partner with Lee Kearney on your next real estate deal.",
        "sub_menu": {
            "text": "Press 1 to submit a deal. Press 2 to fund a deal with Lee. Press 0 to go back.",
            "1": {"name": "Submit Deal", "say": "Visit dodealswithlee.com to submit your deal online, or leave your details after the tone.", "voicemail": True},
            "2": {"name": "Fund Deal", "connect_users": ["Lee Kearney"], "voicemail": True},
        },
    },
    "4": {
        "name": "Operations",
        "say": "Connecting you with our operations team.",
        "connect_users": ["Krystle Gordon", "Becky Williams", "Stacy Platt"],
        "voicemail": "Please leave a message and our team will get back to you shortly.",
    },
    "0": {
        "name": "Team Member",
        "say": "Please hold while we connect you.",
        "connect_all": True,
        "voicemail": "All team members are currently unavailable. Please leave a message.",
    },
}

logger = AgentLogger()


# ============================================================
# HELPER: Wait for GHL page to fully load
# ============================================================
async def wait_for_ghl_load(page, timeout=20000):
    """Wait for GHL's React app to finish loading."""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    await page.wait_for_timeout(3000)
    
    # GHL often shows a modal overlay on load — close it
    await dismiss_ghl_modals(page)
    
    # Wait for actual content to render after modal is gone
    await page.wait_for_timeout(3000)


async def dismiss_ghl_modals(page):
    """Close any GHL modal overlays that block the page content."""
    # Nuclear option: use JavaScript to remove modals and fix overflow
    try:
        removed = await page.evaluate("""
            (() => {
                let removed = 0;
                // Remove all modal elements
                document.querySelectorAll('.modal, .modal-backdrop, .modal-dialog').forEach(el => {
                    el.remove();
                    removed++;
                });
                // Fix overflow:hidden on html and body and #app
                document.documentElement.style.overflow = 'auto';
                document.documentElement.classList.remove('overflow-hidden');
                if (document.body) document.body.style.overflow = 'auto';
                const app = document.getElementById('app');
                if (app) {
                    app.style.overflow = 'auto';
                    app.style.height = 'auto';
                }
                // Also fix any direct child divs with overflow:hidden
                if (app) {
                    app.querySelectorAll(':scope > div').forEach(d => {
                        d.style.overflow = 'auto';
                        d.style.height = 'auto';
                    });
                }
                return removed;
            })()
        """)
        if removed > 0:
            logger.log("MODAL", f"Removed {removed} modal element(s) via JS")
    except Exception as e:
        logger.log("MODAL_JS_ERROR", str(e))
    
    # Also try pressing Escape
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)
    except Exception:
        pass


async def take_screenshot(page, name):
    """Take a screenshot and save to logs."""
    path = str(LOG_DIR / f"{name}-{int(time.time())}.png")
    await page.screenshot(path=path, timeout=10000)
    logger.log("SCREENSHOT", path)
    return path


async def dump_page_info(page):
    """Dump page URL, title, visible text, iframes, and HTML structure for debugging."""
    url = page.url
    title = await page.title()
    # Get first 500 chars of body text
    try:
        body_text = await page.inner_text("body")
        body_text = body_text[:500].strip()
    except Exception:
        body_text = "(could not read body)"
    logger.log("PAGE_INFO", f"URL: {url} | Title: {title}")
    logger.log("PAGE_TEXT", body_text[:200] if body_text else "(empty)")
    
    # Check for iframes
    try:
        iframes = page.frames
        logger.log("FRAMES", f"Total frames: {len(iframes)}")
        for i, frame in enumerate(iframes):
            frame_url = frame.url
            logger.log("FRAME", f"  [{i}] {frame_url[:100]}")
            if i > 0:  # Skip main frame
                try:
                    frame_text = await frame.inner_text("body")
                    logger.log("FRAME_TEXT", f"  [{i}] {frame_text[:150]}")
                except Exception:
                    logger.log("FRAME_TEXT", f"  [{i}] (could not read)")
    except Exception as e:
        logger.log("FRAMES_ERROR", str(e))
    
    # Dump outer HTML structure
    try:
        html = await page.evaluate("document.documentElement.outerHTML.substring(0, 2000)")
        logger.log("HTML_SNIPPET", html[:500])
    except Exception:
        pass
    
    # Dump body innerHTML (first 2000 chars) to see actual DOM
    try:
        body_html = await page.evaluate("document.body.innerHTML.substring(0, 3000)")
        logger.log("BODY_HTML", body_html[:800])
        # Check for common blockers
        if "loading" in body_html.lower() or "spinner" in body_html.lower():
            logger.log("BLOCKER", "Loading spinner detected")
        if "modal" in body_html.lower() or "overlay" in body_html.lower():
            logger.log("BLOCKER", "Modal/overlay detected")
    except Exception:
        pass
    
    # Count all elements to see if DOM is populated
    try:
        el_count = await page.evaluate("document.querySelectorAll('*').length")
        logger.log("DOM_SIZE", f"Total elements: {el_count}")
    except Exception:
        pass
    
    return url, title, body_text


# ============================================================
# HELPER: Check if logged into GHL
# ============================================================
async def check_ghl_login(page):
    """Check if we're logged into GHL by looking at the URL.
    GHL redirects to /location/... when logged in.
    Stays on login page or root when not."""
    url = page.url
    logger.log("URL_CHECK", f"Current URL: {url}")
    # If URL contains /location/ or /dashboard, we're logged in
    if "/location/" in url or "/dashboard" in url or "/automation" in url:
        return True
    # If URL is the login page or root, we're not logged in
    if "login" in url or url.rstrip("/").endswith("gohighlevel.com"):
        return False
    # For any other URL, assume logged in if not on login page
    return True


# ============================================================
# STEP 1: Ensure logged in
# ============================================================
async def ensure_login(page, target_url=None):
    """Navigate to GHL and ensure we're logged in. Auto-login with credentials."""
    if target_url is None:
        target_url = GHL_PHONE_SETTINGS_URL
    
    logger.log("LOGIN_CHECK", "Checking GHL login status...")
    await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
    await wait_for_ghl_load(page)
    await take_screenshot(page, "login-check")

    if await check_ghl_login(page):
        logger.log("LOGIN_OK", "Already logged into GHL")
        return True

    # Not logged in — auto-login
    logger.log("LOGIN_NEEDED", "Not logged in. Auto-logging in...")
    await page.goto(GHL_LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)
    
    try:
        # Fill email
        email_input = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first
        await email_input.fill(GHL_EMAIL)
        await page.wait_for_timeout(500)
        
        # Fill password
        pass_input = page.locator('input[type="password"], input[name="password"]').first
        await pass_input.fill(GHL_PASSWORD)
        await page.wait_for_timeout(500)
        
        # Click sign in button
        login_btn = page.locator('button[type="submit"], button:has-text("Sign"), button:has-text("Log")').first
        await login_btn.click()
        logger.log("LOGIN", "Submitted login form")
        
        # Wait for redirect
        await page.wait_for_timeout(5000)
        await wait_for_ghl_load(page)
        await take_screenshot(page, "after-auto-login")
        await dump_page_info(page)
    except Exception as e:
        logger.log("LOGIN_ERROR", f"Auto-login failed: {e}")
        await take_screenshot(page, "login-error")
        print(f"\n  Auto-login failed: {e}")
        print("  Please log in manually in the browser, then press Enter.")
        input("  > ")

    # Navigate to target
    if await check_ghl_login(page):
        await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        await wait_for_ghl_load(page)
        logger.log("LOGIN_OK", "Successfully logged into GHL")
        return True
    
    # One more try
    await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
    await wait_for_ghl_load(page)
    
    if await check_ghl_login(page):
        logger.log("LOGIN_OK", "Successfully logged into GHL (after redirect)")
        return True
    else:
        logger.log("LOGIN_FAIL", f"Still not logged in. URL: {page.url}")
        return False


# ============================================================
# STEP 2: Find or create the IVR workflow
# ============================================================
async def find_or_create_workflow(page):
    """Find existing DDWL IVR workflow or create one from the IVR template."""
    await wait_for_ghl_load(page)
    await take_screenshot(page, "workflows-list")
    url, title, body_text = await dump_page_info(page)
    
    existing_names = ["DDWL Main Line IVR", "DDWL - Lee AI - IVR", "Lee AI - IVR"]
    for name in existing_names:
        if name in body_text:
            logger.log("WORKFLOW_FOUND", f"Found existing workflow: {name}")
            # Click on it to open
            try:
                link = page.locator(f"text={name}").first
                await link.click()
                await page.wait_for_timeout(3000)
                await wait_for_ghl_load(page)
                logger.log("WORKFLOW_OPENED", f"Opened workflow: {name}")
                return True
            except Exception as e:
                logger.log("CLICK_FAIL", f"Could not click workflow: {e}")

    # No existing workflow — create from IVR template
    logger.log("WORKFLOW_CREATE", "No existing IVR workflow found. Creating from template...")
    
    # Click "+ Create Workflow" — try multiple selectors
    create_clicked = False
    for selector in [
        'button:has-text("Create Workflow")',
        'text="Create Workflow"',
        'a:has-text("Create Workflow")',
        '[class*="create"]',
        'button.hl-btn',
        'button >> text=Create',
    ]:
        try:
            el = page.locator(selector).first
            if await el.is_visible(timeout=2000):
                await el.click()
                create_clicked = True
                logger.log("CLICK", f"Clicked create button via: {selector}")
                await page.wait_for_timeout(2000)
                break
        except Exception:
            continue

    if not create_clicked:
        # Dump all buttons on page AND in frames for debugging
        buttons = await page.locator('button').all_text_contents()
        links = await page.locator('a').all_text_contents()
        logger.log("DEBUG_BUTTONS", f"Buttons on main: {buttons[:10]}")
        logger.log("DEBUG_LINKS", f"Links on main: {links[:10]}")
        
        # Check inside frames
        for i, frame in enumerate(page.frames):
            if i == 0:
                continue
            try:
                frame_buttons = await frame.locator('button').all_text_contents()
                frame_links = await frame.locator('a').all_text_contents()
                if frame_buttons or frame_links:
                    logger.log("FRAME_BUTTONS", f"Frame[{i}] buttons: {frame_buttons[:10]}")
                    logger.log("FRAME_LINKS", f"Frame[{i}] links: {frame_links[:10]}")
            except Exception:
                pass
        
        await take_screenshot(page, "no-create-btn")
        logger.log("ERROR", "Could not find Create Workflow button")
        return False

    await take_screenshot(page, "after-create-click")
    await dump_page_info(page)

    # Look for template/recipe options
    template_clicked = False
    for selector in [
        'text="Select from Template"',
        'text="Select a Recipe"',
        'text="Start from Scratch"',
        'text="Continue"',
        ':text-is("Template")',
    ]:
        try:
            el = page.locator(selector).first
            if await el.is_visible(timeout=2000):
                await el.click()
                template_clicked = True
                logger.log("CLICK", f"Clicked template option via: {selector}")
                await page.wait_for_timeout(2000)
                break
        except Exception:
            continue

    if not template_clicked:
        # Maybe it went straight to the builder — that's fine
        logger.log("INFO", "No template dialog found, may have gone to builder directly")

    await take_screenshot(page, "template-selection")
    
    # Search for IVR template
    try:
        search_box = page.locator('input[placeholder*="Search"], input[type="search"], input[placeholder*="search"]').first
        if await search_box.is_visible(timeout=3000):
            await search_box.fill("IVR")
            await page.wait_for_timeout(2000)
            await take_screenshot(page, "ivr-search")
    except Exception:
        logger.log("INFO", "No search box found")

    # Select the IVR template
    try:
        ivr_template = page.locator('text=IVR').first
        await ivr_template.click()
        await page.wait_for_timeout(1000)
        
        # Click Use/Select button
        for btn_text in ["Use", "Select", "Apply", "Continue"]:
            try:
                use_btn = page.locator(f'button:has-text("{btn_text}")').first
                if await use_btn.is_visible(timeout=2000):
                    await use_btn.click()
                    break
            except Exception:
                continue
        
        await page.wait_for_timeout(3000)
        await wait_for_ghl_load(page)
        await take_screenshot(page, "workflow-created")
        logger.log("WORKFLOW_CREATED", "IVR template loaded")
        return True
    except Exception as e:
        logger.log("ERROR", f"Could not select IVR template: {e}")
        await take_screenshot(page, "ivr-template-error")
        return False


# ============================================================
# STEP 3: Configure the workflow nodes
# ============================================================
async def configure_trigger(page):
    """Click the trigger node and set the phone number."""
    logger.log("CONFIG_TRIGGER", f"Setting trigger phone number to {PHONE_NUMBER}")
    
    # Find and click the trigger node (usually first node, or has "Start IVR" text)
    try:
        trigger = page.locator('[class*="trigger"], [data-testid*="trigger"]').first
        if not await trigger.is_visible():
            trigger = page.locator('text=Start IVR, text=Inbound Call').first
        await trigger.click()
        await page.wait_for_timeout(1500)
    except Exception:
        # Try clicking the first node in the workflow
        try:
            first_node = page.locator('[class*="node"], [class*="step"]').first
            await first_node.click()
            await page.wait_for_timeout(1500)
        except Exception as e:
            logger.log("ERROR", f"Could not find trigger node: {e}")
            return False

    # Look for phone number dropdown/select
    try:
        # Try to find a dropdown or select element for phone number
        phone_select = page.locator('select, [class*="select"], [class*="dropdown"]').first
        await phone_select.click()
        await page.wait_for_timeout(500)
        
        # Select the phone number
        phone_option = page.locator(f'text={PHONE_NUMBER}, [title*="675-0916"], option:has-text("675-0916")').first
        await phone_option.click()
        await page.wait_for_timeout(500)
    except Exception:
        logger.log("WARN", "Could not auto-select phone number. Will try alternative approach.")
        # Try typing in a search field
        try:
            search = page.locator('input[placeholder*="phone"], input[placeholder*="number"], input[placeholder*="Search"]').first
            await search.fill("675-0916")
            await page.wait_for_timeout(1000)
            option = page.locator(f'text=675-0916').first
            await option.click()
        except Exception as e:
            logger.log("ERROR", f"Could not set phone number: {e}")
            return False

    # Save
    try:
        save_btn = page.locator('button:has-text("Save")').first
        await save_btn.click()
        await page.wait_for_timeout(1000)
        logger.log("CONFIG_TRIGGER", "Trigger saved with phone number")
        return True
    except Exception:
        logger.log("WARN", "No save button found for trigger")
        return True


async def configure_say_play(page, node_text, new_message):
    """Click a Say/Play node and update its message."""
    logger.log("CONFIG_SAY", f"Configuring Say/Play node: {node_text[:40]}...")
    
    try:
        node = page.locator(f'text="{node_text}"').first
        if not await node.is_visible():
            node = page.locator(f':text("{node_text}")').first
        await node.click()
        await page.wait_for_timeout(1500)
    except Exception:
        logger.log("WARN", f"Could not find node with text: {node_text}")
        return False

    # Find the text area/input and update it
    try:
        textarea = page.locator('textarea, input[type="text"]').first
        await textarea.fill("")
        await textarea.fill(new_message)
        await page.wait_for_timeout(500)
    except Exception as e:
        logger.log("ERROR", f"Could not fill message: {e}")
        return False

    # Save
    try:
        save_btn = page.locator('button:has-text("Save")').first
        await save_btn.click()
        await page.wait_for_timeout(1000)
        logger.log("CONFIG_SAY", "Say/Play node saved")
        return True
    except Exception:
        return True


async def configure_gather_input(page, node_text, menu_message, num_loops=2):
    """Click a Gather Input node and update its message and settings."""
    logger.log("CONFIG_GATHER", f"Configuring Gather Input: {node_text[:40]}...")
    
    try:
        node = page.locator(f'text="{node_text}"').first
        if not await node.is_visible():
            node = page.locator(f':text("{node_text}")').first
        await node.click()
        await page.wait_for_timeout(1500)
    except Exception:
        logger.log("WARN", f"Could not find gather input node: {node_text}")
        return False

    # Fill the message
    try:
        textarea = page.locator('textarea, input[type="text"]').first
        await textarea.fill("")
        await textarea.fill(menu_message)
        await page.wait_for_timeout(500)
    except Exception as e:
        logger.log("ERROR", f"Could not fill gather input message: {e}")
        return False

    # Set number of loops
    try:
        loops_input = page.locator('input[type="number"]').first
        await loops_input.fill(str(num_loops))
    except Exception:
        logger.log("WARN", "Could not set number of loops")

    # Save
    try:
        save_btn = page.locator('button:has-text("Save")').first
        await save_btn.click()
        await page.wait_for_timeout(1000)
        logger.log("CONFIG_GATHER", "Gather Input node saved")
        return True
    except Exception:
        return True


# ============================================================
# MAIN — Explore GHL pages and configure phone system
# ============================================================
async def main():
    print("\n" + "=" * 60)
    print("  DDWL GHL Phone System Explorer")
    print("=" * 60)
    print(f"  Phone: {PHONE_NUMBER}")
    print(f"  Location: {GHL_LOCATION}")
    print("=" * 60 + "\n")

    import subprocess, socket

    CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    DEBUG_PORT = 9222
    CHROME_PROFILE = "Profile 4"

    def port_open(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    if not port_open(DEBUG_PORT):
        print(f"  Launching Chrome with debug port {DEBUG_PORT}...")
        subprocess.Popen([
            CHROME_EXE,
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--profile-directory={CHROME_PROFILE}",
            "--no-first-run", "--no-default-browser-check",
        ])
        for _ in range(30):
            if port_open(DEBUG_PORT):
                break
            await asyncio.sleep(1)
        else:
            print("  Chrome did not start. Exiting.")
            return
        logger.log("CHROME", f"Chrome launched on port {DEBUG_PORT}")
    else:
        logger.log("CHROME", f"Chrome already on port {DEBUG_PORT}")

    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")
    context = browser.contexts[0]
    page = await context.new_page()
    logger.log("START", "Connected to Chrome via CDP (new tab)")

    try:
        # Step 1: Ensure logged in — target the phone settings page
        logged_in = await ensure_login(page, GHL_PHONE_SETTINGS_URL)
        if not logged_in:
            print("\n  Could not log into GHL. Exiting.")
            return

        # Step 2: Explore which pages actually render
        pages_to_check = [
            ("Phone Settings", f"https://app.gohighlevel.com/location/{GHL_LOCATION}/settings/phone-number"),
            ("Phone System", f"https://app.gohighlevel.com/location/{GHL_LOCATION}/settings/phone-system"),
            ("Dashboard", f"https://app.gohighlevel.com/location/{GHL_LOCATION}/dashboard"),
            ("Settings", f"https://app.gohighlevel.com/location/{GHL_LOCATION}/settings"),
            ("Workflows", f"https://app.gohighlevel.com/location/{GHL_LOCATION}/automation/list"),
        ]

        for name, url in pages_to_check:
            logger.log("EXPLORE", f"Checking: {name}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await wait_for_ghl_load(page)
            
            el_count = await page.evaluate("document.querySelectorAll('*').length")
            try:
                body_text = await page.inner_text("body")
                text_len = len(body_text.strip())
            except Exception:
                text_len = 0
            
            status = "RENDERS" if el_count > 150 and text_len > 50 else "BLANK"
            logger.log("PAGE_STATUS", f"{name}: {status} (elements={el_count}, text_len={text_len})")
            
            safe_name = name.lower().replace(" ", "-")
            await take_screenshot(page, f"explore-{safe_name}")
            
            if status == "RENDERS":
                # Dump what we found
                logger.log("PAGE_CONTENT", body_text[:300] if text_len > 0 else "(empty)")
                
                # List all buttons and links
                buttons = await page.locator('button').all_text_contents()
                links_text = await page.locator('a').all_text_contents()
                if buttons:
                    logger.log("BUTTONS", str([b.strip() for b in buttons if b.strip()][:15]))
                if links_text:
                    logger.log("LINKS", str([l.strip() for l in links_text if l.strip()][:15]))

        print("\n" + "=" * 60)
        print("  Exploration complete. Check logs for results.")
        print("  Browser stays open for manual inspection.")
        print("  Press Ctrl+C to disconnect.")
        print("=" * 60 + "\n")

        while True:
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        print("\n  Disconnecting (Chrome stays open)...")
    except Exception as e:
        logger.log("ERROR", str(e))
        import traceback
        traceback.print_exc()
        try:
            await take_screenshot(page, "error-state")
        except Exception:
            pass
        print(f"\n  Error: {e}")
    finally:
        await browser.close()
        await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
