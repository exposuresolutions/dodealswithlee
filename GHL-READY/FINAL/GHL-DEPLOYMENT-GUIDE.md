# DDWL Website — GHL Deployment Guide

## Pages to Deploy (in order)

| # | File | GHL Page Path | Description |
|---|------|---------------|-------------|
| 1 | `home.html` | `/home-662956` | Main homepage (Option A) |
| 2 | `careers.html` | `/careersportal` | Careers portal with job listings |
| 3 | `student-enrollment.html` | `/studentenrollment` | Student enrollment portal |
| 4 | `onboarding.html` | `/onboardingportal` | Team onboarding (internal) |
| 5 | `admin-dashboard.html` | `/adminportal` | Admin dashboard (internal) |

---

## How to Paste into GHL (Per Page)

### Step 1: Open GHL Sites
1. Go to **Sites** → **Funnels & Websites**
2. Find the existing DDWL website
3. Click on the page you want to update (e.g., Home)

### Step 2: Add Custom Code Element
1. In the page editor, **delete all existing elements** (or start fresh)
2. Click **+ Add Element** → scroll to **Custom Code** (under "Other")
3. Drag the Custom Code element onto the page
4. Click on it to edit

### Step 3: Paste the HTML
1. Open the corresponding `.html` file from the `FINAL/` folder
2. **Select ALL** the content (Ctrl+A)
3. **Copy** (Ctrl+C)
4. In GHL's Custom Code editor, **Paste** (Ctrl+V)
5. Click **Save**

### Step 4: Page Settings (CRITICAL for no white borders)
1. Click the **gear icon** (page settings) in the top right
2. Under **Custom CSS**, paste this:
```css
body, .hl_page-creator, .hl-page-preview, #preview-container,
[class*="wrapper"], [class*="container"], [class*="section"],
.inner-section, .section-element, .row-element, .column-element {
    background: #0a0a0a !important;
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100% !important;
    border: none !important;
    box-shadow: none !important;
}
```
3. Under **Custom Header Code**, paste:
```html
<style>
body { margin: 0 !important; padding: 0 !important; background: #0a0a0a !important; }
</style>
```
4. Set **Section Padding** to `0` on all sides
5. Set **Page Width** to `Full Width`
6. Click **Save**

### Step 5: Publish
1. Click **Publish** in the top right
2. Verify the page loads correctly at `dodealswithlee.com/[path]`
3. Check on mobile too

---

## Troubleshooting White Borders

If you still see white borders after pasting:

1. **Check section padding**: Click on the section wrapper in GHL editor → set all padding to 0
2. **Check row/column margins**: Same — set to 0
3. **Page-level CSS**: Make sure the Custom CSS from Step 4 is applied
4. **Browser cache**: Hard refresh with Ctrl+Shift+R
5. **The aggressive GHL reset** in each HTML file should handle most cases automatically

---

## Navigation Links (All Pages Use These)

| Link | Path |
|------|------|
| Home | `/home-662956` |
| Careers | `/careersportal` |
| Students | `/studentenrollment` |
| Onboarding | `/onboardingportal` |
| Admin | `/adminportal` |

All pages have a **Home** button in the nav. All sub-pages link back to the homepage.

---

## GHL API — Pushing Pages Directly

### Option 1: GHL API (Limited)
GHL's API does NOT currently support creating/updating page HTML content directly. The Sites/Funnels API only supports:
- Listing funnels/websites
- Getting funnel steps
- Creating new funnels

**You cannot push custom code to a page via the API.** This is a GHL limitation.

### Option 2: Playwright Browser Automation (Recommended)
Use the Lilly agent with Playwright to automate the paste process:

```python
# Pseudocode for GHL page update automation
from playwright.sync_api import sync_playwright

def update_ghl_page(page_path, html_content):
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="C:/Users/danga/AppData/Local/Google/Chrome/User Data",
            channel="chrome",
            args=["--profile-directory=Profile 2"]  # Lilly's profile
        )
        page = browser.pages[0]
        
        # Navigate to GHL page editor
        page.goto(f"https://app.gohighlevel.com/...")
        
        # Find custom code element, click edit
        # Clear existing content
        # Paste new HTML
        # Save and publish
        
        browser.close()
```

This approach uses Lilly's Chrome profile (already logged into GHL) to automate the paste process.

### Option 3: GHL Webhooks + Custom Hosting
Host the pages on Vercel/Netlify and use GHL's iframe or redirect to point to them. This gives you:
- Version control (Git)
- Instant deploys
- No paste-into-GHL needed
- But: separate domain, potential CORS issues

---

## File Sizes (All Under GHL's 100KB Limit)

| File | Size |
|------|------|
| home.html | ~34 KB |
| careers.html | ~36 KB |
| student-enrollment.html | ~37 KB |
| onboarding.html | ~45 KB |
| admin-dashboard.html | ~65 KB |

All files are self-contained single HTML files with inline CSS/JS. No external dependencies except CDN links (Tailwind, GSAP, Lucide, WebFont).

---

## Brand Consistency Checklist

- [x] All pages use DDWL brand colors (#0a0a0a, #111, #161616, #00e5ff, #ff6b00, #ffd700)
- [x] All pages use Playfair Display + Inter fonts (loaded via WebFont Loader)
- [x] All pages have the DDWL logo SVG
- [x] All pages have the aggressive GHL reset (no white borders)
- [x] All pages have unified navigation with Home button
- [x] All pages have unified footer with contact info
- [x] All pages have mobile-responsive nav with hamburger menu
- [x] All forms submit to GHL webhook
- [x] All pages use HTML entities (not UTF-8 special chars) per GHL requirements
