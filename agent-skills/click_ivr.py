"""Click on the DDWL - Lee AI - IVR workflow in the already-open Comet browser."""
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

GHL_LOCATION = "KbiucErIMNPbO1mY4qXL"
LOG_DIR = Path(__file__).parent / "logs"
PROFILE_DIR = Path(__file__).parent / "browser-profiles" / "ghl-lilly"


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


async def main():
    print("=" * 60)
    print("  Click IVR Workflow (Comet)")
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
    log("START", "Browser launched")

    # Navigate to workflows page via sidebar click
    log("NAV", "Going to dashboard first...")
    await page.goto(
        f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/dashboard",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await page.wait_for_timeout(5000)

    # Click Automation in sidebar
    log("NAV", "Clicking Automation sidebar...")
    try:
        await page.locator('text=Automation').first.click(timeout=10000)
        log("NAV", "Clicked Automation")
    except Exception:
        log("NAV", "Sidebar click failed, trying direct URL")
        await page.goto(
            f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/automation/workflows?listTab=all",
            wait_until="domcontentloaded",
            timeout=30000,
        )
    # Wait for the workflow list to actually load (not just the spinner)
    for attempt in range(6):
        await page.wait_for_timeout(5000)
        # Check if workflow list has loaded in any frame
        found_list = False
        for frame in [page] + page.frames:
            try:
                text = await frame.inner_text("body", timeout=3000)
                if "Lee AI - IVR" in text or "Workflow List" in text or "Create Workflow" in text:
                    found_list = True
                    break
            except Exception:
                continue
        if found_list:
            log("NAV", f"Workflow list loaded (attempt {attempt+1})")
            break
        log("NAV", f"Waiting for list to load... (attempt {attempt+1})")
    
    await page.wait_for_timeout(3000)
    await ss(page, "workflows-list")

    # Now find and click "DDWL - Lee AI - IVR" — search all frames
    log("NAV", "Looking for DDWL - Lee AI - IVR...")
    clicked = False

    # Search all frames (main page + iframes)
    targets = [page] + page.frames
    for i, target in enumerate(targets):
        try:
            ivr = target.locator('text=DDWL - Lee AI - IVR').first
            if await ivr.is_visible(timeout=3000):
                log("NAV", f"Found in frame {i}, clicking...")
                await ivr.click(timeout=5000)
                clicked = True
                log("NAV", "Clicked!")
                break
        except Exception:
            continue

    if not clicked:
        # Try JS across all frames
        for i, target in enumerate(targets):
            try:
                result = await target.evaluate("""
                    (() => {
                        // Find the row/link containing "Lee AI - IVR"
                        const all = document.querySelectorAll('a, td, tr, span, div');
                        for (const el of all) {
                            if (el.textContent.includes('DDWL - Lee AI - IVR') && el.tagName !== 'BODY') {
                                // Find the nearest link or clickable parent
                                const link = el.closest('a') || el.querySelector('a') || el;
                                link.click();
                                return 'clicked: ' + link.tagName + ' in ' + link.textContent.trim().substring(0, 40);
                            }
                        }
                        return 'not found';
                    })()
                """)
                if "clicked" in result:
                    log("NAV", f"JS click in frame {i}: {result}")
                    clicked = True
                    break
            except Exception:
                continue

    if clicked:
        await page.wait_for_timeout(8000)
        await ss(page, "ivr-workflow-builder")
        log("DONE", "IVR workflow should be open!")
    else:
        log("ERROR", "Could not find DDWL - Lee AI - IVR")
        await ss(page, "not-found")

    print("\n" + "=" * 60)
    print("  Browser is open. Review the IVR workflow.")
    print("  Press Enter to close.")
    print("=" * 60)
    input("  > ")
    await ctx.close()
    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
