"""
Verify IVR workflow: screenshot current state, check voice settings, check agent naming.
"""
import asyncio
import time
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv(Path(__file__).parent.parent / ".env")

GHL_LOCATION = os.getenv("GHL_LOCATION_ID")
API_KEY = os.getenv("GHL_API_KEY")
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
PROFILE_DIR = Path(__file__).parent / "browser-profiles" / "ghl-lilly"

BASE = "https://services.leadconnectorhq.com"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Version": "2021-07-28",
    "Content-Type": "application/json",
}


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


def api_check():
    """Check workflows, phone numbers, and users via API."""
    print("\n" + "=" * 60)
    print("  API VERIFICATION")
    print("=" * 60)

    # 1. List workflows — find the IVR one
    r = requests.get(f"{BASE}/workflows/", headers=HEADERS, params={"locationId": GHL_LOCATION})
    if r.ok:
        wfs = r.json().get("workflows", [])
        for w in wfs:
            if "ivr" in w["name"].lower() or "lee ai" in w["name"].lower():
                log("WORKFLOW", f"  {w['name']} | Status: {w['status']} | ID: {w['id']}")
    else:
        log("ERROR", f"Workflows API: {r.status_code}")

    # 2. List users — check for "Lee" vs "Lilly" naming
    r = requests.get(f"{BASE}/users/", headers=HEADERS, params={"locationId": GHL_LOCATION})
    if r.ok:
        users = r.json().get("users", [])
        print()
        log("USERS", "Team members in GHL:")
        for u in users:
            name = u.get("name", u.get("firstName", "") + " " + u.get("lastName", ""))
            email = u.get("email", "")
            ext = u.get("extension", "N/A")
            phone = u.get("phone", "N/A")
            log("USER", f"  {name:30} ext={ext:5} email={email}")
            # Flag if "Lilly" is still used anywhere
            if "lilly" in name.lower():
                log("WARNING", f"  ⚠️  User '{name}' still has 'Lilly' in name — should be 'Lee AI'?")
    else:
        log("ERROR", f"Users API: {r.status_code}")

    # 3. Check phone numbers
    r = requests.get(f"{BASE}/phone-number/", headers=HEADERS, params={"locationId": GHL_LOCATION})
    if r.ok:
        data = r.json()
        numbers = data.get("data", data.get("phoneNumbers", []))
        print()
        log("PHONES", "Phone numbers in GHL:")
        if isinstance(numbers, list):
            for n in numbers:
                num = n.get("phone", n.get("phoneNumber", "?"))
                name = n.get("name", n.get("friendlyName", "?"))
                log("PHONE", f"  {num} — {name}")
        else:
            log("PHONE", f"  Raw: {str(data)[:300]}")
    else:
        log("ERROR", f"Phone API: {r.status_code} — {r.text[:200]}")


async def browser_check():
    """Open the workflow in Comet and take screenshots of each node."""
    print("\n" + "=" * 60)
    print("  BROWSER VERIFICATION")
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

    # Go to dashboard then Automation
    log("NAV", "Going to dashboard...")
    await page.goto(
        f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/dashboard",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await page.wait_for_timeout(5000)

    # Click Automation
    try:
        await page.locator('text=Automation').first.click(timeout=10000)
        log("NAV", "Clicked Automation")
    except Exception:
        await page.goto(
            f"https://app.gohighlevel.com/v2/location/{GHL_LOCATION}/automation/workflows?listTab=all",
            wait_until="domcontentloaded",
            timeout=30000,
        )

    # Wait for list to load
    for attempt in range(6):
        await page.wait_for_timeout(5000)
        for frame in [page] + page.frames:
            try:
                text = await frame.inner_text("body", timeout=3000)
                if "Lee AI - IVR" in text:
                    log("NAV", f"List loaded (attempt {attempt+1})")
                    break
            except Exception:
                continue
        else:
            continue
        break

    await page.wait_for_timeout(2000)

    # Click on the IVR workflow
    for target in [page] + page.frames:
        try:
            ivr = target.locator('text=DDWL - Lee AI - IVR').first
            if await ivr.is_visible(timeout=3000):
                await ivr.click(timeout=5000)
                log("NAV", "Clicked IVR workflow")
                break
        except Exception:
            continue

    await page.wait_for_timeout(8000)

    # Take full screenshot of the workflow builder
    path = str(LOG_DIR / f"verify-workflow-{int(time.time())}.png")
    await page.screenshot(path=path, full_page=True, timeout=15000)
    log("SS", f"Full workflow: {path.split(chr(92))[-1]}")

    # Also take a zoomed-out screenshot to see more of the workflow
    # Try scrolling down to see all branches
    for frame in page.frames:
        if "client-app-automation" in frame.url:
            try:
                # Scroll the workflow canvas down
                await frame.evaluate("window.scrollBy(0, 500)")
                await page.wait_for_timeout(2000)
                path2 = str(LOG_DIR / f"verify-workflow-scrolled-{int(time.time())}.png")
                await page.screenshot(path=path2, timeout=15000)
                log("SS", f"Scrolled view: {path2.split(chr(92))[-1]}")
            except Exception:
                pass
            break

    # Check the trigger node — click on it to see settings
    for frame in page.frames:
        if "client-app-automation" in frame.url:
            try:
                trigger = frame.locator('text=Start IVR Trigger').first
                if await trigger.is_visible(timeout=3000):
                    await trigger.click(timeout=5000)
                    await page.wait_for_timeout(3000)
                    path3 = str(LOG_DIR / f"verify-trigger-{int(time.time())}.png")
                    await page.screenshot(path=path3, timeout=15000)
                    log("SS", f"Trigger settings: {path3.split(chr(92))[-1]}")
            except Exception as e:
                log("ERROR", f"Trigger click: {e}")
            break

    print("\n" + "=" * 60)
    print("  Browser is open. Press Enter to close.")
    print("=" * 60)
    input("  > ")
    await ctx.close()
    await pw.stop()


async def main():
    api_check()
    await browser_check()


if __name__ == "__main__":
    asyncio.run(main())
