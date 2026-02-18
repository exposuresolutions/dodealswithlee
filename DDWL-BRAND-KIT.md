# DDWL Brand Kit — Official Reference

**For:** All agents, developers, and designers working on DDWL properties
**Last Updated:** February 12, 2026

---

## LOGO ASSETS

| Asset | File | Use Case |
|-------|------|----------|
| **Transparent PNG** | `ddwl-logo-transparent.png` | Light backgrounds, overlays |
| **Black Background PNG** | `ddwl-real-logo.png` | Dark backgrounds, social media |
| **Small Dark PNG** | `ddwl-logo.png` | Thumbnails, favicons |
| **SVG (GHL hosted)** | `https://storage.googleapis.com/msgsndr/KbiucErIMNPbO1mY4qXL/media/67630a6111b3975ed85ffd20.svg` | Web pages, scalable |
| **Nav Base64** | `ddwl-real-logo-nav-b64.txt` | GHL custom code (50px height) |
| **Header Base64** | `ddwl-real-logo-header-b64.txt` | GHL custom code (70px height) |
| **Transparent Nav B64** | `ddwl-logo-transparent-nav-b64.txt` | GHL custom code, light bg |
| **Transparent Header B64** | `ddwl-logo-transparent-header-b64.txt` | GHL custom code, light bg |

### Logo Rules
- Always use on dark backgrounds (#0a0a0a) unless transparent version
- Minimum height: 40px (nav), 60px (headers)
- Never stretch or distort
- Always link to `https://dodealswithlee.com`

---

## COLORS

### Primary Palette

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| **DDWL Black** | `#0a0a0a` | 10, 10, 10 | Page backgrounds |
| **DDWL Dark** | `#111111` | 17, 17, 17 | Card backgrounds, sections |
| **DDWL Card** | `#161616` | 22, 22, 22 | Cards, inputs, elevated surfaces |
| **DDWL Cyan** | `#00e5ff` | 0, 229, 255 | Primary accent, links, highlights |
| **Cyan Light** | `#40efff` | 64, 239, 255 | Hover states, glow effects |
| **Cyan Dark** | `#00b8d4` | 0, 184, 212 | Active states |
| **DDWL Orange** | `#ff6b00` | 255, 107, 0 | CTAs, buttons, urgency, "DO" in logo |
| **Orange Light** | `#ff8533` | 255, 133, 51 | Hover states |
| **Orange Dark** | `#e05500` | 224, 85, 0 | Active/pressed states |

### Secondary / Utility

| Name | Hex | Use |
|------|-----|-----|
| **White 90%** | `rgba(255,255,255,0.9)` | Body text |
| **White 70%** | `rgba(255,255,255,0.7)` | Secondary text |
| **White 50%** | `rgba(255,255,255,0.5)` | Muted text, labels |
| **White 20%** | `rgba(255,255,255,0.2)` | Borders, dividers |
| **White 10%** | `rgba(255,255,255,0.1)` | Subtle borders |
| **White 5%** | `rgba(255,255,255,0.05)` | Background tints |
| **Glass** | `rgba(255,255,255,0.08)` | Glass-morphism cards |
| **Success Green** | `#28c840` | Success states, confirmations |
| **Error Red** | `#ff5f57` | Errors, warnings |
| **Gold** | `#ffd700` | Premium accents (use sparingly) |

### Gradients

| Name | CSS | Use |
|------|-----|-----|
| **CTA Gradient** | `linear-gradient(135deg, #ff6b00, #ff8533)` | Primary buttons |
| **Hero Gradient** | `linear-gradient(180deg, #0a0a0a, #0d0d0d)` | Hero backgrounds |
| **Cyan Glow** | `0 0 30px rgba(0,229,255,0.15)` | Card hover shadows |
| **Orange Glow** | `0 0 30px rgba(255,107,0,0.2)` | CTA hover shadows |
| **Text Gradient** | `linear-gradient(135deg, #00e5ff, #40efff)` | Headline accents |

---

## TYPOGRAPHY

### Font Families

| Role | Font | Weight | Fallback |
|------|------|--------|----------|
| **Headlines** | Playfair Display | 700, 800, 900 | Georgia, serif |
| **Body** | Inter | 400, 500, 600, 700 | -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |

### Loading (GHL Compatible)
```html
<script src="https://ajax.googleapis.com/ajax/libs/webfont/1.6.26/webfont.js"></script>
<script>
WebFont.load({
  google: { families: ['Inter:400,500,600,700', 'Playfair Display:700,800,900'] },
  active: function() {
    document.body.style.fontFamily = "'Inter', -apple-system, sans-serif";
    document.querySelectorAll('h1,h2,h3').forEach(function(el){
      el.style.fontFamily = "'Playfair Display', Georgia, serif";
    });
  }
});
</script>
```

### Type Scale

| Element | Size | Weight | Font |
|---------|------|--------|------|
| H1 (Hero) | clamp(2.5rem, 7vw, 4.5rem) | 900 | Playfair Display |
| H2 (Section) | clamp(1.8rem, 4vw, 2.8rem) | 800 | Playfair Display |
| H3 (Card) | 1.3rem | 700 | Playfair Display |
| Body | 1rem | 400 | Inter |
| Small/Label | 0.85rem | 500-600 | Inter |
| Badge | 0.82rem | 600 | Inter, uppercase, tracking 1.5px |

---

## BRAND VOICE

### Tone
- **Bold** — No hedging, no "maybe"
- **Direct** — Say it straight
- **No-BS** — Cut the fluff
- **Premium** — High-end, exclusive feel
- **Street-smart** — Real experience, not theory

### Key Phrases
- "Real deals, real money, real mentorship"
- "Student &rarr; Player &rarr; Empire"
- "Not a course. Not theory."
- "7,000+ deals. $500M+ volume."
- "Earn while you learn"
- "Close 3 deals and graduate"

### What NOT to Say
- "Pay to play" (reframe as "Investment Tiers")
- "Cleveland Academy" (dropped — focus on main DDWL brand)
- "Guaranteed income" (compliance risk)
- Any unverified claims

---

## KEY PEOPLE

| Person | Role | Email | Phone |
|--------|------|-------|-------|
| **Lee Kearney** | CEO & Founder | lee.kearney@dodealswithlee.com | 813-675-0916 |
| **Krystle Gordon** | Operations Manager | krystle.gordon@dodealswithlee.com | — |
| **Lilly** | AI Agent | lilly@dodealswithlee.com | — |
| **Daniel Gallagher** | Tech Lead (Exposure Solutions) | daniel@exposuresolutions.me | — |

---

## KEY ASSETS

| Asset | URL |
|-------|-----|
| **Logo SVG** | `https://storage.googleapis.com/msgsndr/KbiucErIMNPbO1mY4qXL/media/67630a6111b3975ed85ffd20.svg` |
| **Lee's Photo** | `https://storage.googleapis.com/msgsndr/KbiucErIMNPbO1mY4qXL/media/6740d661a865994979d38612.webp` |
| **GHL Webhook** | `https://services.leadconnectorhq.com/hooks/KbiucErIMNPbO1mY4qXL/webhook-trigger/mCdlXsgchQ4v9BQeIa9E` |
| **Sitereview Proxy** | `https://ghl-proxy-blush.vercel.app/sitereview` |
| **Website** | `https://dodealswithlee.com` |

---

## GHL CONSTRAINTS

- GHL strips `<head>` — no `<link>` or `@import` in `<style>`
- Load fonts via WebFont Loader script in `<body>`
- Use HTML entities (`&mdash;` not `—`, `&rsquo;` not `'`)
- Keep total file under 100KB
- Base64 images OK if small, but avoid 400KB+ files
- `ajax.googleapis.com` is whitelisted for scripts

---

## SOCIAL PROOF DATA

| Stat | Value | Source |
|------|-------|--------|
| Deals closed | 7,000+ | Lee's track record |
| Volume | $500M+ | Lee's track record |
| Students | 500+ | DDWL Academy |
| Student deals (2024) | 847 | DDWL records |
| Inc. 5000 | Recognized | Public record |
| Lee's MBA | USF | Public record |
| Featured in | Inc., BiggerPockets, Yahoo Finance | Public record |

---

*This brand kit is the single source of truth for all DDWL design and development work.*
