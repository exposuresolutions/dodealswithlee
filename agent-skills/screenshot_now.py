"""Take a screenshot of the current Chrome tab."""
import asyncio, time
from pathlib import Path
from playwright.async_api import async_playwright

LOG_DIR = Path(__file__).parent / "logs"

async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = browser.contexts[0]
    for i, page in enumerate(ctx.pages):
        title = await page.title()
        url = page.url
        if "gohighlevel" in url:
            path = str(LOG_DIR / f"current-{int(time.time())}.png")
            await page.screenshot(path=path, timeout=15000)
            print(f"  Tab {i}: {title}")
            print(f"  URL: {url[:100]}")
            print(f"  Screenshot: {path}")
            break
    await browser.close()
    await pw.stop()

if __name__ == "__main__":
    asyncio.run(main())
