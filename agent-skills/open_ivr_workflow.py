"""Open the existing DDWL - Lee AI - IVR workflow in Chrome for manual review."""
import asyncio
from playwright.async_api import async_playwright

GHL_LOCATION = "KbiucErIMNPbO1mY4qXL"
IVR_WORKFLOW_ID = "43c27781-3e52-40f5-95af-1d612e0654d0"  # DDWL - Lee AI - IVR
WORKFLOW_URL = f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/automation/workflows/{IVR_WORKFLOW_ID}"

async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
    
    ctx = browser.contexts[0]
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    
    print(f"  Navigating to: DDWL - Lee AI - IVR workflow...")
    await page.goto(WORKFLOW_URL, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(5000)
    
    title = await page.title()
    print(f"  Page title: {title}")
    print(f"  URL: {page.url}")
    print(f"\n  Workflow is open in Chrome. Review and edit manually.")
    
    await browser.close()
    await pw.stop()

if __name__ == "__main__":
    asyncio.run(main())
