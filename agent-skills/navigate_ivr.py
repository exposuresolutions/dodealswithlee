"""
Navigate the already-logged-in Comet browser to the IVR workflow.
Connects to the ghl-lilly persistent profile that's already running.
"""
import asyncio
import time
import glob
from pathlib import Path
from playwright.async_api import async_playwright

GHL_LOCATION = "KbiucErIMNPbO1mY4qXL"
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

PROFILE_DIR = Path(__file__).parent / "browser-profiles" / "ghl-lilly"
DASHBOARD_URL = f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/dashboard"


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


async def ss(page, name):
    path = str(LOG_DIR / f"comet-{name}-{int(time.time())}.png")
    try:
        await page.screenshot(path=path, timeout=10000)
        log("SS", name)
    except Exception as e:
        log("SS_FAIL", str(e))
    return path


def get_workflow_frame(page):
    for frame in page.frames:
        if "client-app-automation-workflows" in frame.url:
            return frame
    return None


async def main():
    print("=" * 60)
    print("  Navigate to IVR Workflow (Comet)")
    print("=" * 60)

    pw = await async_playwright().start()
    ctx = await pw.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        viewport={"width": 1280, "height": 900},
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        ignore_default_args=["--enable-automation"],
    )

    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    log("START", "Browser launched with ghl-lilly profile")

    # Step 1: Go to dashboard
    log("NAV", "Going to GHL dashboard...")
    await page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(5000)
    await ss(page, "dashboard")

    # Check if we're logged in
    url = page.url
    log("NAV", f"Current URL: {url[:80]}")

    if "login" in url or "verify" in url:
        log("ERROR", "Not logged in! Please run open_ivr_comet.py first and complete 2FA.")
        await ctx.close()
        await pw.stop()
        return

    # Step 2: Click Automation in sidebar
    log("NAV", "Looking for Automation sidebar link...")
    try:
        # Try multiple selectors for the sidebar
        selectors = [
            'a:has-text("Automation")',
            '[data-testid="sb_automation"]',
            'nav a[href*="automation"]',
            '.sidebar a:has-text("Automation")',
            'text=Automation',
        ]
        clicked = False
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=3000):
                    await el.click(timeout=5000)
                    log("NAV", f"Clicked sidebar: {sel}")
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            # Try JS click on sidebar
            log("NAV", "Trying JS sidebar click...")
            result = await page.evaluate("""
                (() => {
                    const links = document.querySelectorAll('a, [role="menuitem"], [role="link"]');
                    for (const el of links) {
                        if (el.textContent.trim().includes('Automation')) {
                            el.click();
                            return 'clicked: ' + el.tagName + ' ' + el.textContent.trim().substring(0, 30);
                        }
                    }
                    return 'not found';
                })()
            """)
            log("NAV", f"JS result: {result}")
            if "clicked" in result:
                clicked = True

        if not clicked:
            log("NAV", "Could not find Automation link, trying direct URL...")
            await page.goto(
                f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/automation/workflows?listTab=all",
                wait_until="domcontentloaded",
                timeout=30000,
            )

        await page.wait_for_timeout(8000)
        await ss(page, "workflows-page")

    except Exception as e:
        log("ERROR", f"Navigation error: {e}")

    # Step 3: Find workflow iframe and click IVR workflow
    wf = get_workflow_frame(page)
    if not wf:
        log("FRAMES", f"Frames: {[f.url[:60] for f in page.frames]}")
        # Maybe the page rendered without iframe — check for workflow names directly
        body = await page.inner_text("body")
        if "Lee AI - IVR" in body:
            log("NAV", "Found IVR text in main page, clicking...")
            await page.locator('text=Lee AI - IVR').first.click(timeout=5000)
            await page.wait_for_timeout(8000)
            await ss(page, "ivr-open")
        else:
            log("ERROR", f"No workflow iframe found. Body preview: {body[:200]}")
            await ss(page, "no-iframe")
    else:
        log("NAV", f"Found workflow iframe: {wf.url[:80]}")

        # Click on DDWL - Lee AI - IVR
        try:
            ivr_link = wf.locator('a:has-text("DDWL - Lee AI - IVR"), td:has-text("DDWL - Lee AI - IVR")')
            count = await ivr_link.count()
            log("NAV", f"Found {count} IVR elements")

            if count > 0:
                await ivr_link.first.click(timeout=5000)
                log("NAV", "Clicked DDWL - Lee AI - IVR")
                await page.wait_for_timeout(8000)
                await ss(page, "ivr-open")
            else:
                # JS fallback
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
                log("NAV", f"JS click: {result}")
                await page.wait_for_timeout(8000)
                await ss(page, "ivr-open")
        except Exception as e:
            log("ERROR", f"Click error: {e}")
            await ss(page, "click-error")

    print("\n" + "=" * 60)
    print("  IVR Workflow should be open in the browser.")
    print("  Review and edit manually.")
    print("  Press Enter to close the browser.")
    print("=" * 60)
    input("  > ")
    await ctx.close()
    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
