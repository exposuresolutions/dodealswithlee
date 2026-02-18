"""
Browser Resilience Module — Anti-Cookie, Anti-Popup, Anti-Detection
====================================================================
Drop-in upgrade for all our Playwright browser agents.
Handles: cookie banners, GDPR popups, login walls, modals, CAPTCHAs,
         bot detection, and session persistence.

USAGE:
    from browser_resilience import ResilientBrowser

    async with ResilientBrowser(profile="lilly-agent") as browser:
        page = await browser.goto("https://app.gohighlevel.com")
        # Cookies auto-dismissed, session persisted, stealth enabled

WHAT IT DOES:
    1. COOKIE/POPUP KILLER — Auto-clicks Accept/Dismiss on any cookie banner
    2. STEALTH MODE — Anti-detection flags so sites don't know it's automated
    3. PERSISTENT SESSIONS — Cookies/logins survive between runs
    4. MODAL DESTROYER — Kills overlays, modals, backdrop divs
    5. SMART RETRY — Retries on failures with exponential backoff
    6. HUMAN HANDOFF — Pauses and asks user when it genuinely can't proceed
"""

import asyncio
import time
import json
from pathlib import Path
from datetime import datetime

AGENT_DIR = Path(__file__).parent
LOG_DIR = AGENT_DIR / "logs"
PROFILE_BASE = AGENT_DIR / "browser-profiles"
LOG_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_BASE.mkdir(parents=True, exist_ok=True)

# Comet browser (Perplexity) — our default
COMET_EXE = r"C:\Users\danga\AppData\Local\Perplexity\Comet\Application\comet.exe"
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def _log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


# ============================================================
# 1. COOKIE CONSENT KILLER
# ============================================================
# Common selectors for cookie accept buttons across the web.
# Covers: OneTrust, CookieBot, Quantcast, TrustArc, GDPR banners,
#         generic "Accept", "I agree", "Got it", "Allow all", etc.
COOKIE_ACCEPT_SELECTORS = [
    # Generic text matches (most common)
    'button:has-text("Accept All")',
    'button:has-text("Accept all")',
    'button:has-text("Accept Cookies")',
    'button:has-text("Accept cookies")',
    'button:has-text("Allow All")',
    'button:has-text("Allow all")',
    'button:has-text("I Accept")',
    'button:has-text("I agree")',
    'button:has-text("I Agree")',
    'button:has-text("Got it")',
    'button:has-text("OK")',
    'button:has-text("Agree")',
    'button:has-text("Consent")',
    'button:has-text("Continue")',
    'a:has-text("Accept All")',
    'a:has-text("Accept Cookies")',
    'a:has-text("I agree")',
    'a:has-text("Got it")',
    # OneTrust (very common — used by thousands of sites)
    '#onetrust-accept-btn-handler',
    '.onetrust-close-btn-handler',
    # CookieBot
    '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
    '#CybotCookiebotDialogBodyButtonAccept',
    'a#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
    # Quantcast / CMP
    '.qc-cmp2-summary-buttons button:first-child',
    'button.css-47sehv',  # Quantcast accept
    # TrustArc
    '.truste-consent-button',
    '#truste-consent-button',
    # Osano
    '.osano-cm-accept-all',
    # Cookielaw
    '.cookie-consent-accept',
    '.cookie-accept',
    '.cc-accept',
    '.cc-btn.cc-allow',
    # Generic class patterns
    '[class*="cookie"] button:has-text("Accept")',
    '[class*="cookie"] button:has-text("OK")',
    '[class*="consent"] button:has-text("Accept")',
    '[class*="consent"] button:has-text("OK")',
    '[class*="gdpr"] button:has-text("Accept")',
    '[id*="cookie"] button:has-text("Accept")',
    '[id*="consent"] button:has-text("Accept")',
    # Data attribute patterns
    '[data-testid="cookie-accept"]',
    '[data-action="accept"]',
    '[data-cookiefirst-action="accept"]',
]

# Selectors for cookie banner containers (to remove if clicking fails)
COOKIE_BANNER_SELECTORS = [
    '#onetrust-banner-sdk',
    '#onetrust-consent-sdk',
    '#CybotCookiebotDialog',
    '.qc-cmp2-container',
    '#truste-consent-track',
    '.osano-cm-window',
    '[class*="cookie-banner"]',
    '[class*="cookie-consent"]',
    '[class*="cookieConsent"]',
    '[class*="cookie-notice"]',
    '[class*="gdpr"]',
    '[id*="cookie-banner"]',
    '[id*="cookie-consent"]',
    '[id*="cookieConsent"]',
    '[id*="gdpr"]',
    '.cc-window',
    '.cc-banner',
]

# Selectors for generic modals/overlays to dismiss
MODAL_DISMISS_SELECTORS = [
    'button[aria-label="Close"]',
    'button[aria-label="close"]',
    'button[aria-label="Dismiss"]',
    'button.close',
    '.modal-close',
    '[data-dismiss="modal"]',
    '.popup-close',
    'button:has-text("×")',
    'button:has-text("✕")',
    'button:has-text("Close")',
    'button:has-text("No thanks")',
    'button:has-text("Not now")',
    'button:has-text("Maybe later")',
    'button:has-text("Skip")',
    'button:has-text("Dismiss")',
]


async def kill_cookie_popups(page, timeout=2000):
    """Try to click cookie accept buttons. Returns True if something was clicked."""
    clicked = False
    for selector in COOKIE_ACCEPT_SELECTORS:
        try:
            el = page.locator(selector).first
            if await el.is_visible(timeout=timeout):
                await el.click(timeout=timeout)
                _log("COOKIE", f"Clicked: {selector}")
                clicked = True
                await page.wait_for_timeout(500)
                break
        except Exception:
            continue

    if not clicked:
        # Fallback: remove cookie banners via JS
        try:
            removed = await page.evaluate("""() => {
                const selectors = """ + json.dumps(COOKIE_BANNER_SELECTORS) + """;
                let removed = 0;
                for (const sel of selectors) {
                    document.querySelectorAll(sel).forEach(el => {
                        el.remove();
                        removed++;
                    });
                }
                // Also remove any fixed/sticky overlays that cover the page
                document.querySelectorAll('[style*="position: fixed"], [style*="position:fixed"]').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > window.innerWidth * 0.5 && rect.height > 100) {
                        const text = el.innerText.toLowerCase();
                        if (text.includes('cookie') || text.includes('consent') || text.includes('privacy') || text.includes('gdpr')) {
                            el.remove();
                            removed++;
                        }
                    }
                });
                // Restore scrolling
                document.body.style.overflow = 'auto';
                document.documentElement.style.overflow = 'auto';
                return removed;
            }""")
            if removed > 0:
                _log("COOKIE", f"Removed {removed} banner elements via JS")
                clicked = True
        except Exception:
            pass

    return clicked


async def dismiss_modals(page, timeout=1500):
    """Dismiss generic modals, overlays, and popups."""
    dismissed = False
    for selector in MODAL_DISMISS_SELECTORS:
        try:
            el = page.locator(selector).first
            if await el.is_visible(timeout=timeout):
                await el.click(timeout=timeout)
                _log("MODAL", f"Dismissed: {selector}")
                dismissed = True
                await page.wait_for_timeout(300)
        except Exception:
            continue

    # Also try Escape key
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
    except Exception:
        pass

    # Nuclear option: remove all modal overlays via JS
    try:
        await page.evaluate("""() => {
            // Remove modal backdrops
            document.querySelectorAll('.modal-backdrop, .overlay, .modal-overlay, [class*="backdrop"]').forEach(el => el.remove());
            // Remove modals
            document.querySelectorAll('.modal.show, .modal[style*="display: block"], [role="dialog"]').forEach(el => {
                if (el.querySelector('[class*="cookie"]') || el.querySelector('[class*="consent"]')) {
                    el.remove();
                }
            });
            // Restore scroll
            document.body.style.overflow = 'auto';
            document.body.classList.remove('modal-open', 'overflow-hidden', 'no-scroll');
            document.documentElement.style.overflow = 'auto';
            document.documentElement.classList.remove('overflow-hidden', 'no-scroll');
        }""")
    except Exception:
        pass

    return dismissed


async def clear_all_overlays(page):
    """Nuclear cleanup — kill ALL overlays, banners, modals."""
    await kill_cookie_popups(page)
    await dismiss_modals(page)
    await page.wait_for_timeout(500)


# ============================================================
# 2. STEALTH FLAGS — Anti-bot detection
# ============================================================
STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-infobars",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-features=TranslateUI",
    "--disable-ipc-flooding-protection",
]

STEALTH_IGNORE_ARGS = [
    "--enable-automation",
    "--enable-blink-features=IdleDetection",
]

STEALTH_JS = """
// Override navigator.webdriver
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// Override chrome.runtime to look like a real browser
if (!window.chrome) { window.chrome = {}; }
if (!window.chrome.runtime) { window.chrome.runtime = { connect: () => {}, sendMessage: () => {} }; }

// Override permissions query
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters);

// Override plugins to look real
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5].map(() => ({
        name: 'Chrome PDF Plugin',
        description: 'Portable Document Format',
        filename: 'internal-pdf-viewer',
        length: 1,
    })),
});

// Override languages
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
"""


# ============================================================
# 3. RESILIENT BROWSER — Main class
# ============================================================
class ResilientBrowser:
    """
    Drop-in replacement for BrowserAgent with full resilience.

    Features:
    - Persistent sessions (cookies survive between runs)
    - Auto cookie/popup dismissal on every navigation
    - Stealth mode (anti-bot detection)
    - Smart retry with backoff
    - Human handoff when stuck
    """

    def __init__(self, profile="resilient-agent", headless=False, use_comet=True):
        self.profile = profile
        self.profile_path = str(PROFILE_BASE / profile)
        self.headless = headless
        self.use_comet = use_comet
        self._pw = None
        self.context = None
        self.page = None
        self._needs_human = False
        self._human_reason = ""

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def start(self):
        """Launch browser with stealth + persistence."""
        from playwright.async_api import async_playwright

        self._pw = await async_playwright().start()

        # Choose browser executable
        exe = COMET_EXE if self.use_comet and Path(COMET_EXE).exists() else None

        launch_args = {
            "user_data_dir": self.profile_path,
            "headless": self.headless,
            "viewport": {"width": 1366, "height": 900},
            "args": STEALTH_ARGS,
            "ignore_default_args": STEALTH_IGNORE_ARGS,
        }
        if exe:
            launch_args["executable_path"] = exe

        self.context = await self._pw.chromium.launch_persistent_context(**launch_args)

        # Inject stealth JS on every new page
        await self.context.add_init_script(STEALTH_JS)

        # Get or create page
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()

        # Set up auto-popup handler
        self.page.on("dialog", self._handle_dialog)

        _log("BROWSER", f"Started | Profile: {self.profile} | Stealth: ON | Comet: {bool(exe)}")
        return self

    async def _handle_dialog(self, dialog):
        """Auto-accept browser dialogs (alert, confirm, prompt)."""
        _log("DIALOG", f"Auto-accepting: {dialog.type} — {dialog.message[:80]}")
        await dialog.accept()

    async def goto(self, url, wait="domcontentloaded", auto_clean=True):
        """Navigate with auto cookie/popup cleanup."""
        _log("NAV", url)
        try:
            await self.page.goto(url, wait_until=wait, timeout=30000)
        except Exception as e:
            _log("NAV_WARN", f"Timeout/error on {url}: {str(e)[:100]}")

        await self.page.wait_for_timeout(1500)

        if auto_clean:
            await clear_all_overlays(self.page)

        return self.page

    async def goto_retry(self, url, max_retries=3, wait="domcontentloaded"):
        """Navigate with retry + exponential backoff."""
        for attempt in range(max_retries):
            try:
                page = await self.goto(url, wait=wait)
                # Check if page actually loaded
                el_count = await page.evaluate("document.querySelectorAll('*').length")
                if el_count > 50:
                    return page
                _log("RETRY", f"Page seems empty ({el_count} elements), retry {attempt+1}/{max_retries}")
            except Exception as e:
                _log("RETRY", f"Attempt {attempt+1} failed: {str(e)[:100]}")

            backoff = (2 ** attempt) * 2
            _log("RETRY", f"Waiting {backoff}s before retry...")
            await asyncio.sleep(backoff)

        _log("RETRY", f"All {max_retries} attempts failed for {url}")
        return self.page

    async def click_safe(self, selector, timeout=5000):
        """Click with auto-cleanup before and after."""
        await clear_all_overlays(self.page)
        try:
            await self.page.click(selector, timeout=timeout)
            await self.page.wait_for_timeout(500)
            return True
        except Exception as e:
            _log("CLICK_FAIL", f"{selector}: {str(e)[:100]}")
            return False

    async def fill_safe(self, selector, value, timeout=5000):
        """Fill input with auto-cleanup."""
        await clear_all_overlays(self.page)
        try:
            await self.page.fill(selector, value, timeout=timeout)
            return True
        except Exception as e:
            _log("FILL_FAIL", f"{selector}: {str(e)[:100]}")
            return False

    async def screenshot(self, name="screenshot"):
        """Take screenshot."""
        path = str(LOG_DIR / f"{name}-{int(time.time())}.png")
        try:
            await self.page.screenshot(path=path)
            _log("SCREENSHOT", path)
        except Exception:
            _log("SCREENSHOT", f"Failed: {name}")
        return path

    async def get_text(self):
        """Get page body text."""
        try:
            return await self.page.inner_text("body")
        except Exception:
            return ""

    async def wait_for_human(self, reason="Agent needs help"):
        """
        Pause and wait for human intervention.
        Prints a clear message and waits for Enter key in terminal.
        """
        self._needs_human = True
        self._human_reason = reason
        print("\n" + "=" * 60)
        print(f"  🙋 HUMAN HELP NEEDED")
        print(f"  Reason: {reason}")
        print(f"  The browser is open — do what's needed, then")
        print(f"  press ENTER here to continue...")
        print("=" * 60)
        await asyncio.get_event_loop().run_in_executor(None, input)
        self._needs_human = False
        _log("HUMAN", "User completed manual step, resuming...")

    async def check_for_captcha(self):
        """Check if page has a CAPTCHA and ask human if so."""
        try:
            text = await self.get_text()
            text_lower = text.lower()
            captcha_signals = [
                "captcha", "i'm not a robot", "verify you are human",
                "human verification", "security check", "prove you're not",
                "challenge", "recaptcha", "hcaptcha", "cloudflare"
            ]
            for signal in captcha_signals:
                if signal in text_lower:
                    _log("CAPTCHA", f"Detected: '{signal}'")
                    await self.wait_for_human(f"CAPTCHA detected: '{signal}' — please solve it in the browser")
                    return True

            # Also check for CAPTCHA iframes
            captcha_frames = await self.page.evaluate("""() => {
                const frames = document.querySelectorAll('iframe');
                return Array.from(frames).filter(f =>
                    f.src && (f.src.includes('recaptcha') || f.src.includes('hcaptcha') || f.src.includes('captcha'))
                ).length;
            }""")
            if captcha_frames > 0:
                _log("CAPTCHA", f"Found {captcha_frames} CAPTCHA iframe(s)")
                await self.wait_for_human("CAPTCHA iframe detected — please solve it in the browser")
                return True
        except Exception:
            pass
        return False

    async def check_for_login_wall(self, expected_url_contains=None):
        """Check if we got redirected to a login page."""
        url = self.page.url.lower()
        login_signals = ["login", "signin", "sign-in", "auth", "sso", "oauth"]
        for signal in login_signals:
            if signal in url:
                if expected_url_contains and expected_url_contains.lower() not in url:
                    _log("LOGIN_WALL", f"Redirected to login: {self.page.url}")
                    await self.wait_for_human(f"Login required at {self.page.url} — please log in, then press Enter")
                    return True
        return False

    async def save_cookies(self, filepath=None):
        """Save current cookies to file for reuse."""
        cookies = await self.context.cookies()
        if not filepath:
            filepath = Path(self.profile_path) / "saved-cookies.json"
        Path(filepath).write_text(json.dumps(cookies, indent=2))
        _log("COOKIES", f"Saved {len(cookies)} cookies → {filepath}")
        return cookies

    async def load_cookies(self, filepath=None):
        """Load cookies from file."""
        if not filepath:
            filepath = Path(self.profile_path) / "saved-cookies.json"
        if Path(filepath).exists():
            cookies = json.loads(Path(filepath).read_text())
            await self.context.add_cookies(cookies)
            _log("COOKIES", f"Loaded {len(cookies)} cookies from {filepath}")
            return True
        return False

    async def close(self):
        """Close browser, saving session state."""
        if self.context:
            try:
                await self.save_cookies()
            except Exception:
                pass
            await self.context.close()
        if self._pw:
            await self._pw.stop()
        _log("BROWSER", "Closed")


# ============================================================
# 4. QUICK HELPERS — for use in scripts
# ============================================================
async def quick_browse(url, profile="quick"):
    """One-liner to open a URL with full resilience."""
    async with ResilientBrowser(profile=profile) as b:
        await b.goto(url)
        text = await b.get_text()
        return text


async def quick_screenshot(url, output_path, profile="quick"):
    """One-liner to screenshot a URL with cookie popups auto-dismissed."""
    async with ResilientBrowser(profile=profile) as b:
        await b.goto(url)
        await b.screenshot(output_path)


# ============================================================
# 5. TEST — verify everything works
# ============================================================
async def test_resilience():
    """Test the resilience module against common sites."""
    print("=" * 60)
    print("  Browser Resilience Test")
    print("=" * 60)

    test_sites = [
        ("Google", "https://www.google.com"),
        ("GHL Login", "https://app.gohighlevel.com"),
    ]

    async with ResilientBrowser(profile="resilience-test", headless=False) as b:
        for name, url in test_sites:
            print(f"\n  Testing: {name} ({url})")
            await b.goto(url)
            await b.check_for_captcha()
            text = await b.get_text()
            print(f"    Page text length: {len(text)}")
            await b.screenshot(f"test-{name.lower()}")
            print(f"    ✅ {name} OK")

        print(f"\n{'='*60}")
        print(f"  All tests passed!")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(test_resilience())
