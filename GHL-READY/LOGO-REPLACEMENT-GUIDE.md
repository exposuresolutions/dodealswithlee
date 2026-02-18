# DDWL Logo Replacement Guide

> **New Brand Energy Integration** - Replace logo across all pages

---

## Current Logo Locations

Each page has the logo in **2 places**:
1. **Navigation bar** (top of page)
2. **Footer** (bottom of page)

**Current URL**: `https://storage.googleapis.com/msgsndr/KbiucErIMNPbO1mY4qXL/media/67630a6111b3975ed85ffd20.svg`

---

## Pages to Update

1. **home.html** → /home-662956
2. **careers.html** → /careersportal
3. **student-enrollment.html** → /studentenrollment
4. **onboarding.html** → /onboardingportal
5. **admin-dashboard.html** → /adminportal

---

## Quick Replacement Steps

### Step 1: Upload New Logo
1. **Go to GHL**: app.gohighlevel.com
2. **Navigate**: Settings > Media
3. **Upload**: Your new logo (SVG format recommended)
4. **Copy**: The new URL

### Step 2: Replace in Each File
**Find and replace these 2 lines in each file:**

```html
<!-- Navigation logo (around line 55) -->
<img src="OLD_URL" alt="Do Deals With Lee" class="h-8">

<!-- Footer logo (around line 344) -->
<img src="OLD_URL" alt="Do Deals With Lee" class="h-8 mb-4">
```

**Replace with:**
```html
<!-- Navigation logo -->
<img src="NEW_URL_HERE" alt="Do Deals With Lee" class="h-8">

<!-- Footer logo -->
<img src="NEW_URL_HERE" alt="Do Deals With Lee" class="h-8 mb-4">
```

---

## Brand Energy Updates

### New Color Palette (Based on your new branding)
```css
/* Update these in the <style> section of each page */
'lee-cyan': '#00e5ff',     /* Your vibrant cyan */
'lee-gold': '#ffd700',     /* Your premium gold */
'lee-orange': '#ff6b00',   /* Your energy orange */
'lee-black': '#0a0a0a',    /* Keep this */
'lee-dark': '#111111',     /* Keep this */
'lee-card': '#161616',     /* Keep this */
```

### Typography Updates
Consider these modern font combinations:
- **Headings**: Playfair Display (keep - it's elegant)
- **Body**: Inter (keep - it's clean)
- **Accent**: Maybe add a modern sans for CTAs

---

## Enhanced Brand Elements to Add

### 1. Gradient Accents
```css
/* Add to style section */
.energy-gradient {
    background: linear-gradient(135deg, #00e5ff, #ff6b00);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.glow-border {
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
}
```

### 2. Micro-animations
```css
/* Add subtle hover effects */
.hover-energy {
    transition: all 0.3s ease;
}

.hover-energy:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(0, 229, 255, 0.3);
}
```

### 3. New Button Styles
```css
.btn-energy {
    background: linear-gradient(135deg, #00e5ff, #ff6b00);
    color: #0a0a0a;
    font-weight: 600;
    padding: 12px 24px;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.btn-energy:hover {
    transform: scale(1.05);
    box-shadow: 0 0 30px rgba(0, 229, 255, 0.5);
}
```

---

## Homepage Energy Boost Ideas

### Hero Section Updates
- **Add animated gradient background**
- **Increase font sizes** for more impact
- **Add subtle particle effects** (optional)
- **Stronger CTAs** with energy colors

### Stats Section Enhancement
```html
<!-- Consider adding animated counters -->
<div class="text-4xl font-bold energy-gradient">7,000+</div>
<div class="text-xl text-gray-400">Properties Transformed</div>
```

### Testimonial Cards
- **Add hover animations**
- **Use gradient borders**
- **Include headshots** if available

---

## Implementation Order

1. **URGENT**: Upload new logo to GHL Media
2. **Replace logo URLs** in all 5 pages
3. **Update colors** if you want the new energy palette
4. **Add gradient effects** to headings and buttons
5. **Test all pages** in GHL preview
6. **Deploy** one page at a time (start with home)

---

## Files Ready for Update

Once you have the new logo URL, I can instantly update all files. Just provide:
- **New logo URL** from GHL Media
- **Any color changes** you want

I'll update all 5 pages in minutes.

---

## Next Steps

1. **Get logo URL** from GHL Media
2. **Set up Lilly's phone** (urgent - she's live)
3. **Update all pages** with new branding
4. **Test and deploy** homepage first

Ready when you have the logo URL!
