"""Quick check: connect to Chrome CDP and screenshot the current state."""
import asyncio
import time
import socket
from pathlib import Path
from playwright.async_api import async_playwright

LOG_DIR = Path(__file__).parent / "logs"

async def main():
    if not socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex(("127.0.0.1", 9222)) == 0:
        print("Chrome not on port 9222")
        return
    
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
    
    # Check all pages/tabs
    for ctx in browser.contexts:
        for i, page in enumerate(ctx.pages):
            url = page.url
            title = await page.title()
            print(f"  Tab {i}: {title[:50]} | {url[:80]}")
            path = str(LOG_DIR / f"status-tab{i}-{int(time.time())}.png")
            try:
                await page.screenshot(path=path, timeout=10000)
                print(f"    Screenshot: {path.split(chr(92))[-1]}")
            except Exception as e:
                print(f"    Screenshot failed: {e}")
            
            # Check for workflow iframe content
            for frame in page.frames:
                if "client-app-automation" in frame.url or "leadconnectorhq" in frame.url:
                    try:
                        txt = await frame.inner_text("body")
                        print(f"    Iframe text ({len(txt)} chars): {txt[:200]}")
                    except Exception:
                        pass
    
    await browser.close()
    await pw.stop()

if __name__ == "__main__":
    asyncio.run(main())
