"""
Open the DDWL - Lee AI - IVR workflow using the Exposure Agent (Comet) browser.
Uses persistent profile + Lilly credentials to log in and navigate via sidebar.
"""
import asyncio
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from exposure_agent import BrowserAgent, AgentLogger, LOG_DIR

load_dotenv(Path(__file__).parent.parent / ".env")

GHL_LOCATION = os.getenv("GHL_LOCATION_ID", "KbiucErIMNPbO1mY4qXL")
IVR_WORKFLOW_ID = "43c27781-3e52-40f5-95af-1d612e0654d0"
LILLY_EMAIL = os.getenv("GHL_EMAIL", "")
LILLY_PASS = os.getenv("GHL_PASSWORD", "")

DASHBOARD_URL = f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/dashboard"
WORKFLOWS_URL = f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/automation/workflows?listTab=all"

logger = AgentLogger()


async def ss(agent, name):
    path = str(LOG_DIR / f"comet-{name}-{int(time.time())}.png")
    try:
        await agent.page.screenshot(path=path, timeout=10000)
        logger.log("SS", name)
    except Exception as e:
        logger.log("SS_FAIL", str(e))
    return path


def get_workflow_frame(page):
    for frame in page.frames:
        if "client-app-automation-workflows" in frame.url:
            return frame
    return None


async def login_if_needed(agent):
    """Check if logged in, login with Lilly credentials if not."""
    page = agent.page
    url = page.url

    # Check if we're already on a GHL page
    body_text = await page.inner_text("body")
    if "Dashboard" in body_text or "Automation" in body_text or "Contacts" in body_text:
        logger.log("LOGIN", "Already logged in to GHL")
        return True

    # Check if we see a login form
    login_selectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[placeholder*="email" i]',
    ]

    for sel in login_selectors:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=3000):
                logger.log("LOGIN", "Login form found, entering credentials...")
                await el.fill(LILLY_EMAIL)

                # Find password field
                pw_field = page.locator('input[type="password"]').first
                await pw_field.fill(LILLY_PASS)

                # Click sign in button
                sign_in = page.locator('button[type="submit"], button:has-text("Sign In"), button:has-text("Log In")').first
                await sign_in.click(timeout=5000)

                logger.log("LOGIN", "Submitted login form, waiting...")
                await page.wait_for_timeout(8000)
                await ss(agent, "after-login")

                # Check if login succeeded
                new_url = page.url
                if "dashboard" in new_url or "location" in new_url:
                    logger.log("LOGIN", "Login successful!")
                    return True
                else:
                    logger.log("LOGIN", f"Login may have failed, URL: {new_url[:80]}")
                    return False
        except Exception:
            continue

    logger.log("LOGIN", "No login form found, may already be logged in or page not loaded")
    return True


async def main():
    print("=" * 60)
    print("  COMET — Open DDWL IVR Workflow")
    print("=" * 60)

    # Use the Exposure Agent's persistent browser profile
    agent = BrowserAgent(profile_name="ghl-lilly", headless=False)
    await agent.start()
    logger.log("START", "Browser launched with ghl-lilly profile")

    # Step 1: Navigate to GHL dashboard
    logger.log("NAV", "Going to GHL dashboard...")
    await agent.goto(DASHBOARD_URL)
    await agent.page.wait_for_timeout(5000)
    await ss(agent, "dashboard")

    # Step 2: Login if needed
    logged_in = await login_if_needed(agent)
    if not logged_in:
        logger.log("ERROR", "Could not log in. Browser stays open for manual login.")
        print("\n  Login failed. Please log in manually in the browser.")
        print("  Press Enter when done...")
        input("  > ")

    # Step 3: Navigate to Automation via sidebar
    logger.log("NAV", "Clicking Automation in sidebar...")
    page = agent.page
    try:
        auto_link = page.locator('a:has-text("Automation"), [data-testid="sb_automation"]').first
        await auto_link.click(timeout=10000)
        logger.log("NAV", "Clicked Automation sidebar link")
        await page.wait_for_timeout(8000)
    except Exception as e:
        logger.log("NAV", f"Sidebar click failed ({e}), trying direct URL...")
        await agent.goto(WORKFLOWS_URL)
        await page.wait_for_timeout(8000)

    await ss(agent, "workflows-page")

    # Step 4: Find the workflow iframe and click on the IVR workflow
    wf = get_workflow_frame(page)
    if not wf:
        logger.log("ERROR", "Could not find workflow iframe")
        logger.log("FRAMES", str([f.url[:80] for f in page.frames]))
        print("\n  Could not find workflow iframe. Browser stays open.")
        print("  Press Enter when done...")
        input("  > ")
        await agent.close()
        return

    logger.log("NAV", f"Found workflow iframe: {wf.url[:80]}")

    # Click on "DDWL - Lee AI - IVR"
    try:
        ivr_link = wf.locator('a:has-text("DDWL - Lee AI - IVR"), td:has-text("DDWL - Lee AI - IVR")')
        count = await ivr_link.count()
        logger.log("NAV", f"Found {count} 'DDWL - Lee AI - IVR' elements")

        if count > 0:
            await ivr_link.first.click(timeout=5000)
            logger.log("NAV", "Clicked on DDWL - Lee AI - IVR workflow")
            await page.wait_for_timeout(8000)
            await ss(agent, "ivr-workflow-open")
        else:
            # Try JS click
            result = await wf.evaluate("""
                (() => {
                    const els = document.querySelectorAll('a, td, span, div');
                    for (const el of els) {
                        if (el.textContent.includes('Lee AI - IVR')) {
                            el.click();
                            return 'clicked: ' + el.tagName;
                        }
                    }
                    return 'not found';
                })()
            """)
            logger.log("NAV", f"JS click: {result}")
            await page.wait_for_timeout(8000)
            await ss(agent, "ivr-workflow-open")
    except Exception as e:
        logger.log("ERROR", f"Error finding IVR workflow: {e}")
        await ss(agent, "error")

    print("\n" + "=" * 60)
    print("  IVR Workflow is open in the browser.")
    print("  Review and edit manually.")
    print("  Press Enter to close the browser.")
    print("=" * 60)
    input("  > ")
    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
