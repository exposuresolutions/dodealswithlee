"""
ChatGPT Memory Export Agent
============================
Opens ChatGPT in browser, navigates to Settings → Data Controls → Export,
clicks Export, and waits for the email confirmation.

Also parses the export zip once downloaded.

USAGE:
    python chatgpt_export.py export    # Open ChatGPT and trigger export
    python chatgpt_export.py parse     # Parse a downloaded export zip
"""

import asyncio
import sys
import json
import zipfile
from pathlib import Path
from datetime import datetime

AGENT_DIR = Path(__file__).parent
BASE_DIR = AGENT_DIR.parent
LOG_DIR = AGENT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR = BASE_DIR / "chatgpt-export"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


async def trigger_export():
    """Open ChatGPT and trigger data export."""
    sys.path.insert(0, str(AGENT_DIR))
    from browser_resilience import ResilientBrowser

    print("\n" + "=" * 60)
    print("  ChatGPT Memory Export")
    print("=" * 60)

    async with ResilientBrowser(profile="chatgpt-export", headless=False) as browser:
        # Go to ChatGPT settings
        page = await browser.goto("https://chatgpt.com/#settings/DataControls")
        await page.wait_for_timeout(3000)

        # Check if logged in
        if "auth" in page.url or "login" in page.url:
            await browser.wait_for_human(
                "Please log into ChatGPT, then press Enter.\n"
                "After login, I'll navigate to Settings → Data Controls."
            )
            page = await browser.goto("https://chatgpt.com/#settings/DataControls")
            await page.wait_for_timeout(3000)

        # Try to find and click Export button
        print("\n  Looking for Export Data button...")
        found = False

        # Try clicking Settings gear first if we're not in settings
        try:
            settings_btn = page.locator('button[aria-label="Settings"], button:has-text("Settings"), [data-testid="settings"]')
            if await settings_btn.count() > 0:
                await settings_btn.first.click()
                await page.wait_for_timeout(2000)
        except Exception:
            pass

        # Look for Data Controls tab
        try:
            data_tab = page.locator('button:has-text("Data controls"), a:has-text("Data controls"), [data-testid*="data"]')
            if await data_tab.count() > 0:
                await data_tab.first.click()
                await page.wait_for_timeout(2000)
                print("  ✅ Found Data Controls tab")
        except Exception:
            pass

        # Look for Export button
        try:
            export_btn = page.locator('button:has-text("Export"), button:has-text("Export data")')
            if await export_btn.count() > 0:
                await export_btn.first.click()
                print("  ✅ Clicked Export Data!")
                await page.wait_for_timeout(2000)

                # Confirm export
                confirm_btn = page.locator('button:has-text("Confirm"), button:has-text("Yes"), button:has-text("Export")')
                if await confirm_btn.count() > 0:
                    await confirm_btn.first.click()
                    print("  ✅ Confirmed export!")
                found = True
        except Exception:
            pass

        if not found:
            await browser.screenshot("chatgpt-export-page")
            await browser.wait_for_human(
                "I couldn't find the Export button automatically.\n"
                "Please do it manually:\n"
                "  1. Click Settings (gear icon)\n"
                "  2. Click 'Data controls'\n"
                "  3. Click 'Export data'\n"
                "  4. Click 'Confirm export'\n"
                "  5. Check your email for the download link\n\n"
                "Press Enter when done."
            )

        print("\n  📧 ChatGPT will email you a download link.")
        print("  Once downloaded, run: python chatgpt_export.py parse")
        print("=" * 60)


def parse_export(zip_path=None):
    """Parse a ChatGPT export zip file."""
    print("\n" + "=" * 60)
    print("  ChatGPT Export Parser")
    print("=" * 60)

    # Find zip file
    if not zip_path:
        # Look in Downloads and export dir
        search_dirs = [
            Path.home() / "Downloads",
            EXPORT_DIR,
            BASE_DIR,
        ]
        for d in search_dirs:
            zips = list(d.glob("*chatgpt*.zip")) + list(d.glob("*openai*.zip"))
            if zips:
                zip_path = str(max(zips, key=lambda f: f.stat().st_mtime))
                break

    if not zip_path or not Path(zip_path).exists():
        print("  ❌ No ChatGPT export zip found.")
        print("  Download it from the email ChatGPT sent you,")
        print("  then run: python chatgpt_export.py parse path/to/file.zip")
        return

    print(f"  📦 Parsing: {zip_path}")

    with zipfile.ZipFile(zip_path, 'r') as z:
        files = z.namelist()
        print(f"  📁 Files in export: {len(files)}")

        # Extract memories
        memories_extracted = False
        for f in files:
            if "memory" in f.lower() or "model_spec" in f.lower():
                content = z.read(f).decode("utf-8", errors="replace")
                out_path = EXPORT_DIR / Path(f).name
                out_path.write_text(content, encoding="utf-8")
                print(f"  💾 Saved: {out_path.name} ({len(content)} chars)")
                memories_extracted = True

                # Parse if JSON
                if f.endswith(".json"):
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            print(f"     → {len(data)} memory entries")
                            # Save as readable text
                            txt_path = EXPORT_DIR / f"memories-readable.txt"
                            lines = []
                            for i, mem in enumerate(data, 1):
                                if isinstance(mem, dict):
                                    text = mem.get("content", mem.get("text", mem.get("value", str(mem))))
                                    lines.append(f"{i}. {text}")
                                else:
                                    lines.append(f"{i}. {mem}")
                            txt_path.write_text("\n".join(lines), encoding="utf-8")
                            print(f"  📝 Readable memories → {txt_path.name}")
                    except json.JSONDecodeError:
                        pass

        # Extract conversations summary
        for f in files:
            if "conversations" in f.lower() and f.endswith(".json"):
                content = z.read(f).decode("utf-8", errors="replace")
                try:
                    convos = json.loads(content)
                    if isinstance(convos, list):
                        print(f"\n  💬 Conversations: {len(convos)}")
                        # Save titles
                        titles = []
                        for c in convos:
                            title = c.get("title", "Untitled")
                            created = c.get("create_time", "")
                            titles.append(f"{title} ({created})")
                        titles_path = EXPORT_DIR / "conversation-titles.txt"
                        titles_path.write_text("\n".join(titles[:200]), encoding="utf-8")
                        print(f"  📝 Conversation titles → {titles_path.name}")
                except Exception:
                    pass
                break

        if not memories_extracted:
            # Just extract everything
            z.extractall(EXPORT_DIR)
            print(f"  📁 Extracted all files to {EXPORT_DIR}")

    print(f"\n  ✅ Export parsed! Files saved to: {EXPORT_DIR}")
    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python chatgpt_export.py export              # Trigger export in browser")
        print("  python chatgpt_export.py parse [zip_path]    # Parse downloaded export")
        return

    cmd = sys.argv[1].lower()
    if cmd == "export":
        asyncio.run(trigger_export())
    elif cmd == "parse":
        zip_path = sys.argv[2] if len(sys.argv) > 2 else None
        parse_export(zip_path)
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
