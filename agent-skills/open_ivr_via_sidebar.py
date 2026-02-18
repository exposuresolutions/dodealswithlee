"""
Open the DDWL - Lee AI - IVR workflow via sidebar navigation (the only way GHL renders pages).
"""
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

GHL_LOCATION = "KbiucErIMNPbO1mY4qXL"
IVR_WORKFLOW_ID = "43c27781-3e52-40f5-95af-1d612e0654d0"
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# The workflows page URL that works
WORKFLOWS_URL = f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/automation/workflows?listTab=all"


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


async def ss(page, name):
    path = str(LOG_DIR / f"ivr-{name}-{int(time.time())}.png")
    try:
        await page.screenshot(path=path, timeout=10000)
        log("SS", f"{name}")
    except Exception as e:
        log("SS", f"Failed: {e}")


def get_workflow_frame(page):
    for frame in page.frames:
        if "client-app-automation-workflows" in frame.url:
            return frame
    return None


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = browser.contexts[0]
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()

    log("NAV", "Navigating to Workflows via sidebar...")

    # Step 1: Go to dashboard first (renders the sidebar)
    await page.goto(
        f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/dashboard",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await page.wait_for_timeout(5000)

    # Step 2: Click Automation in sidebar
    try:
        auto_link = page.locator('a:has-text("Automation"), [data-testid="sb_automation"]').first
        await auto_link.click(timeout=10000)
        log("NAV", "Clicked Automation sidebar link")
        await page.wait_for_timeout(8000)
    except Exception as e:
        log("NAV", f"Sidebar click failed ({e}), trying direct URL...")
        await page.goto(WORKFLOWS_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(8000)

    await ss(page, "workflows-page")

    # Step 3: Find the workflow iframe and click on "DDWL - Lee AI - IVR"
    wf = get_workflow_frame(page)
    if not wf:
        log("ERROR", "Could not find workflow iframe")
        log("FRAMES", str([f.url[:80] for f in page.frames]))
        await browser.close()
        await pw.stop()
        return

    log("NAV", f"Found workflow iframe: {wf.url[:80]}")

    # Look for the IVR workflow link in the iframe
    try:
        # Find the workflow by name
        ivr_link = wf.locator('a:has-text("DDWL - Lee AI - IVR"), td:has-text("DDWL - Lee AI - IVR")')
        count = await ivr_link.count()
        log("NAV", f"Found {count} 'DDWL - Lee AI - IVR' elements")

        if count > 0:
            await ivr_link.first.click(timeout=5000)
            log("NAV", "Clicked on DDWL - Lee AI - IVR workflow")
            await page.wait_for_timeout(8000)
            await ss(page, "ivr-workflow-open")
        else:
            # Try finding it by partial text or scrolling
            log("NAV", "Trying to find IVR workflow by searching all text...")
            all_text = await wf.locator("body").inner_text()
            if "Lee AI - IVR" in all_text:
                log("NAV", "Text found in iframe, looking for clickable element...")
                # Try clicking via JS
                result = await wf.evaluate("""
                    (() => {
                        const links = document.querySelectorAll('a, [role="link"], tr, td');
                        for (const el of links) {
                            if (el.textContent.includes('Lee AI - IVR')) {
                                el.click();
                                return 'clicked: ' + el.tagName + ' ' + el.textContent.trim().substring(0, 50);
                            }
                        }
                        return 'not found';
                    })()
                """)
                log("NAV", f"JS click result: {result}")
                await page.wait_for_timeout(8000)
                await ss(page, "ivr-workflow-open")
            else:
                log("NAV", "IVR workflow not visible on current page, may need to scroll or paginate")
                # List visible workflows
                wf_names = await wf.evaluate("""
                    (() => {
                        const names = [];
                        document.querySelectorAll('[class*="workflow-name"], td a, .name').forEach(el => {
                            const t = el.textContent.trim();
                            if (t && t.length > 3) names.push(t.substring(0, 60));
                        });
                        return names;
                    })()
                """)
                log("NAV", f"Visible workflows: {wf_names[:10]}")
                await ss(page, "workflows-list")
    except Exception as e:
        log("ERROR", f"Error finding IVR workflow: {e}")
        await ss(page, "error")

    log("DONE", "Browser stays open. Review the workflow manually.")
    await browser.close()
    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
