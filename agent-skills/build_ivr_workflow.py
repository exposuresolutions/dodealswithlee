"""
DDWL IVR Workflow Builder — GHL AI Builder Automation
======================================================
Uses GHL's built-in AI Builder to generate the IVR workflow from a prompt.
Connects to Chrome via CDP (port 9222) and navigates using /v2/ URLs.

Key discovery: GHL pages only render via sidebar clicks or /v2/ URL prefix.
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
GHL_WORKFLOWS_V2 = f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/automation/workflows?listTab=all"
GHL_DASHBOARD_V2 = f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/dashboard"
GHL_SETTINGS_V2 = f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/settings/profile"
GHL_LOGIN_URL = "https://app.gohighlevel.com/"

LILLY_EMAIL = os.getenv("GHL_EMAIL", "")
LILLY_PASS = os.getenv("GHL_PASSWORD", "")
PHONE_NUMBER = "(813) 675-0916"

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT = 9222

# Simplified IVR prompt — GHL AI can't handle complex nested menus
IVR_PROMPT = """Create an inbound call IVR workflow:

1. Trigger: Inbound phone call
2. Say/Play greeting: "Thank you for calling Do Deals with Lee."
3. Gather Input menu: "Press 1 to sell your home. Press 2 for coaching. Press 3 for deals. Press 4 for operations. Press 0 for a team member."
4. Branch on key press:
   - Key 1: Say "Connecting you with acquisitions" then connect call to user
   - Key 2: Say "Connecting you with coaching" then connect call to user
   - Key 3: Say "Connecting you with deals" then connect call to user
   - Key 4: Say "Connecting you with operations" then connect call to user
   - Key 0: Say "Please hold" then connect call to user
   - No input: Say "Please leave a message" then record voicemail
5. End call

Name: DDWL Main Line IVR"""


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


async def ss(page, name):
    path = str(LOG_DIR / f"ivr-{name}-{int(time.time())}.png")
    try:
        await page.screenshot(path=path, timeout=10000)
        log("SS", path.split("\\")[-1])
    except Exception:
        log("SS", f"FAILED: {name}")
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


async def wait_load(page, timeout=15000):
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    await page.wait_for_timeout(2000)
    await dismiss_modals(page)
    await page.wait_for_timeout(1000)


async def page_renders(page):
    el = await page.evaluate("document.querySelectorAll('*').length")
    try:
        txt = await page.inner_text("body")
        tl = len(txt.strip())
    except Exception:
        txt = ""
        tl = 0
    return el > 150 and tl > 50, el, tl, txt


async def auto_login(page):
    """Auto-login to GHL."""
    log("LOGIN", f"Logging in as {LILLY_EMAIL}...")
    await page.goto(GHL_LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    if "/location/" in page.url and "login" not in page.url:
        log("LOGIN", "Already logged in")
        return True

    try:
        email_input = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first
        await email_input.fill(LILLY_EMAIL, timeout=5000)
        await page.wait_for_timeout(500)

        pass_input = page.locator('input[type="password"], input[name="password"]').first
        await pass_input.fill(LILLY_PASS, timeout=5000)
        await page.wait_for_timeout(500)

        login_btn = page.locator('button[type="submit"], button:has-text("Sign"), button:has-text("Log")').first
        await login_btn.click(timeout=5000)
        log("LOGIN", "Submitted login form")

        await page.wait_for_timeout(8000)
        if "/location/" in page.url:
            log("LOGIN", "Logged in successfully")
            return True
        else:
            log("LOGIN", f"Login may have failed. URL: {page.url}")
            await ss(page, "login-result")
            return "/location/" in page.url
    except Exception as e:
        log("LOGIN_ERROR", str(e))
        return False


async def navigate_to_workflows(page):
    """Navigate to workflows page using sidebar (the method that works)."""
    log("NAV", "Navigating to Workflows via sidebar...")

    # First go to dashboard (always renders)
    await page.goto(GHL_DASHBOARD_V2, wait_until="domcontentloaded", timeout=20000)
    await wait_load(page)

    renders, el, tl, txt = await page_renders(page)
    if not renders:
        log("NAV", "Dashboard didn't render, trying login...")
        if not await auto_login(page):
            return False
        await page.goto(GHL_DASHBOARD_V2, wait_until="domcontentloaded", timeout=20000)
        await wait_load(page)

    # Click Automation in sidebar
    try:
        auto_link = page.locator('a:has-text("Automation")').first
        await auto_link.wait_for(state="visible", timeout=5000)
        await auto_link.click()
        log("NAV", "Clicked Automation sidebar link")
        await wait_load(page)
    except Exception as e:
        log("NAV", f"Could not click Automation: {e}")
        # Fallback: try v2 URL directly
        await page.goto(GHL_WORKFLOWS_V2, wait_until="domcontentloaded", timeout=20000)
        await wait_load(page)

    renders, el, tl, txt = await page_renders(page)
    if renders:
        log("NAV", f"Workflows page loaded ({el} elements)")
        await ss(page, "workflows-page")
        return True
    else:
        log("NAV", f"Workflows page blank ({el} elements)")
        return False


async def dismiss_all_popups(page):
    """Dismiss all GHL popups, dialogs, and overlays."""
    # Debug: list all frames
    frames = page.frames
    log("FRAMES", f"Total frames: {len(frames)}")
    
    # Search ALL frames for the popup buttons
    for i, frame in enumerate(frames):
        try:
            # Try clicking "Got it" in each frame
            got_it = frame.locator('button:has-text("Got it"), button:has-text("Got It")')
            count = await got_it.count()
            if count > 0:
                log("POPUP", f"Found 'Got it' in frame {i} ({frame.url[:60]})")
                await got_it.first.click(timeout=3000)
                log("POPUP", "Clicked 'Got it'!")
                await page.wait_for_timeout(1000)
                return
        except Exception:
            pass
        
        try:
            # Also try the X close button
            x_btn = frame.get_by_role("button", name="Close")
            if await x_btn.count() > 0:
                log("POPUP", f"Found Close in frame {i}")
        except Exception:
            pass
    
    # If frame search didn't work, try coordinate click on "Got it" button
    # From screenshot: "Got it" button is at approximately (763, 328) in viewport
    log("POPUP", "Trying coordinate click on 'Got it' button area...")
    await page.mouse.click(763, 328)
    await page.wait_for_timeout(1000)
    
    # Check if popup is gone by looking for "Build using AI" button
    try:
        ai_btn = page.locator('button:has-text("Build using AI")')
        if await ai_btn.count() > 0 and await ai_btn.first.is_visible(timeout=2000):
            log("POPUP", "Popup dismissed! 'Build using AI' is now visible.")
            return
    except Exception:
        pass
    
    # Try clicking the X button at (779, 216)
    log("POPUP", "Trying X button coordinate click...")
    await page.mouse.click(779, 216)
    await page.wait_for_timeout(1000)
    
    await dismiss_modals(page)


def get_workflow_frame(page):
    """Get the iframe that contains the workflow UI."""
    for frame in page.frames:
        if "client-app-automation" in frame.url or "leadconnectorhq" in frame.url:
            return frame
    return None


async def use_ai_builder(page):
    """Click 'Build using AI' and submit the IVR prompt."""
    log("AI_BUILD", "Dismissing popups first...")
    await dismiss_all_popups(page)
    await page.wait_for_timeout(1000)
    await ss(page, "before-ai-build")

    # The workflow UI is inside an iframe — find it
    wf = get_workflow_frame(page)
    if not wf:
        log("AI_BUILD", "Could not find workflow iframe!")
        log("FRAMES", str([f.url[:80] for f in page.frames]))
        return False
    log("AI_BUILD", f"Found workflow iframe: {wf.url[:80]}")

    # List buttons in the iframe for debugging
    buttons = await wf.locator('button').all_text_contents()
    clean = [b.strip() for b in buttons if b.strip()][:20]
    log("IFRAME_BUTTONS", str(clean))

    # Click "Build using AI" button in the iframe
    try:
        ai_btn = wf.locator('button:has-text("Build using AI")')
        count = await ai_btn.count()
        log("AI_BUILD", f"Found {count} 'Build using AI' button(s) in iframe")
        if count > 0:
            await ai_btn.first.click(timeout=5000)
            log("AI_BUILD", "Clicked 'Build using AI'")
            await page.wait_for_timeout(3000)
            await ss(page, "ai-builder-opened")
        else:
            log("AI_BUILD", "No 'Build using AI' button found in iframe")
            return False
    except Exception as e:
        log("AI_BUILD", f"Error clicking 'Build using AI': {e}")
        return False

    # Find the AI prompt textarea/input (could be in iframe or a new frame/modal)
    log("AI_BUILD", "Looking for prompt input...")
    
    # Re-check frames — AI builder might open in a new frame
    await page.wait_for_timeout(2000)
    prompt_input = None
    search_targets = [wf, page]  # Search iframe first, then main page
    
    # Also check for any new frames
    for frame in page.frames:
        if frame not in search_targets:
            search_targets.append(frame)

    selectors = [
        'textarea',
        'div[contenteditable="true"]',
        'input[type="text"][placeholder*="escribe"]',
        'input[type="text"][placeholder*="prompt"]',
        'input[type="text"][placeholder*="workflow"]',
        'input[type="text"][placeholder*="type"]',
        'input[type="text"]',
    ]

    for target in search_targets:
        for sel in selectors:
            try:
                el = target.locator(sel).first
                if await el.is_visible(timeout=2000):
                    prompt_input = el
                    frame_name = "iframe" if target == wf else "main" if target == page else "other"
                    log("AI_BUILD", f"Found prompt input: {sel} in {frame_name}")
                    break
            except Exception:
                continue
        if prompt_input:
            break

    if not prompt_input:
        log("AI_BUILD", "Could not find prompt input")
        await ss(page, "no-prompt-input")
        # Dump iframe content
        try:
            txt = await wf.inner_text("body")
            log("DEBUG", f"Iframe text: {txt[:300]}")
        except Exception:
            pass
        return False

    # Type the IVR prompt
    log("AI_BUILD", "Typing IVR prompt...")
    await prompt_input.click()
    await prompt_input.fill(IVR_PROMPT)
    await page.wait_for_timeout(1000)
    await ss(page, "prompt-filled")

    # Find and click the submit arrow button inside the iframe
    log("AI_BUILD", "Finding submit button in iframe...")
    try:
        build_clicked = False
        
        # Debug: dump all buttons in iframe with their attributes
        btn_info = await wf.evaluate("""
            (() => {
                const info = [];
                document.querySelectorAll('button').forEach((btn, i) => {
                    const rect = btn.getBoundingClientRect();
                    info.push({
                        i: i,
                        text: btn.textContent.trim().substring(0, 30),
                        cls: btn.className.substring(0, 50),
                        hasSvg: !!btn.querySelector('svg'),
                        type: btn.type,
                        ariaLabel: btn.getAttribute('aria-label') || '',
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height),
                        visible: rect.width > 0 && rect.height > 0
                    });
                });
                return info;
            })()
        """)
        # Log only visible buttons
        visible_btns = [b for b in btn_info if b['visible']]
        for b in visible_btns:
            log("BTN", f"[{b['i']}] text='{b['text']}' svg={b['hasSvg']} type={b['type']} aria='{b['ariaLabel']}' pos=({b['x']},{b['y']}) size={b['w']}x{b['h']}")
        
        # Find the submit button: look for aria-label='Submit' first (the purple arrow)
        submit_idx = None
        # Priority 1: aria-label='Submit'
        for b in visible_btns:
            if b['ariaLabel'].lower() == 'submit':
                submit_idx = b['i']
                log("AI_BUILD", f"Found Submit button (aria) at index {submit_idx}")
                break
        # Priority 2: type='submit' with SVG
        if submit_idx is None:
            for b in visible_btns:
                if b['type'] == 'submit' and b['hasSvg']:
                    submit_idx = b['i']
                    log("AI_BUILD", f"Found submit button (type) at index {submit_idx}")
                    break
        
        if submit_idx is not None:
            # Click via JS in the iframe
            result = await wf.evaluate(f"""
                (() => {{
                    const btn = document.querySelectorAll('button')[{submit_idx}];
                    if (btn) {{
                        btn.click();
                        return 'clicked button ' + {submit_idx};
                    }}
                    return 'button not found';
                }})()
            """)
            log("AI_BUILD", f"JS click result: {result}")
            build_clicked = True
            await page.wait_for_timeout(3000)
            await ss(page, "after-submit-click")
        else:
            # Fallback: try clicking all small SVG buttons via JS
            log("AI_BUILD", "No obvious submit button, trying all small SVG buttons...")
            result = await wf.evaluate("""
                (() => {
                    const btns = document.querySelectorAll('button');
                    const clicked = [];
                    for (const btn of btns) {
                        if (btn.querySelector('svg')) {
                            const rect = btn.getBoundingClientRect();
                            if (rect.width > 0 && rect.width < 60 && rect.y > 150) {
                                btn.click();
                                clicked.push(btn.className.substring(0, 20));
                            }
                        }
                    }
                    return clicked;
                })()
            """)
            log("AI_BUILD", f"Clicked buttons: {result}")
            if result:
                build_clicked = True
            await page.wait_for_timeout(3000)
            await ss(page, "after-fallback-click")

        if not build_clicked:
            log("AI_BUILD", "Could not find submit button")
            return False

        # Wait for AI to generate the workflow
        log("AI_BUILD", "Waiting for AI to generate workflow (up to 60s)...")
        for i in range(12):
            await page.wait_for_timeout(5000)
            await ss(page, f"ai-generating-{i}")
            log("AI_BUILD", f"  Generating... ({(i+1)*5}s)")

        await ss(page, "ai-build-result")
        log("AI_BUILD", "AI Builder finished")
        return True

    except Exception as e:
        log("AI_BUILD", f"Error during build: {e}")
        await ss(page, "ai-build-error")
        return False


async def main():
    print("\n" + "=" * 60)
    print("  DDWL IVR Workflow Builder — AI Builder")
    print("=" * 60)
    print(f"  Phone: {PHONE_NUMBER}")
    print(f"  Method: GHL AI Builder via CDP")
    print("=" * 60 + "\n")

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
        log("CHROME", "Chrome launched")
    else:
        log("CHROME", f"Chrome already on port {DEBUG_PORT}")

    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")
    context = browser.contexts[0]
    page = await context.new_page()
    log("START", "Connected to Chrome via CDP")

    try:
        # Step 1: Navigate to Workflows
        if not await navigate_to_workflows(page):
            print("\n  Could not access Workflows page. Exiting.")
            return

        # Step 2: Use AI Builder to create IVR workflow
        success = await use_ai_builder(page)

        if success:
            print("\n" + "=" * 60)
            print("  IVR WORKFLOW BUILT VIA AI BUILDER")
            print("=" * 60)
            print("  The AI has generated the workflow structure.")
            print("  Review it in the browser and:")
            print("  1. Verify all branches are correct")
            print("  2. Check phone number assignment")
            print("  3. Save and Publish when ready")
            print("=" * 60)
        else:
            print("\n  AI Builder did not complete successfully.")
            print("  Check the screenshots in logs/ for details.")

        print("\n  Browser stays open. Press Ctrl+C to disconnect.\n")
        while True:
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        print("\n  Disconnecting (Chrome stays open)...")
    except Exception as e:
        log("ERROR", str(e))
        import traceback
        traceback.print_exc()
        await ss(page, "error")
    finally:
        await browser.close()
        await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
