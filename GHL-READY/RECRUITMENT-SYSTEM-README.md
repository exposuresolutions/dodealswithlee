# DDWL Recruitment & Onboarding System

> **White-label recruitment + onboarding portal built for DDWL, reusable for Flavors and any future client.**

## Architecture Decision

After researching open-source ATS systems (OpenCATS, SpotAxis, Huly, Resume-Matcher) and evaluating Zoho Recruit's free tier (limited to 1 active job, no API on free plan), we chose:

**Custom Portal + GHL Backend** — the best fit because:
- Already in the DDWL tech stack (GHL handles CRM, automations, email, SMS)
- White-label ready — swap branding in one config file
- schema.org/JobPosting markup — jobs appear on Google Jobs for FREE
- No additional SaaS costs or vendor lock-in
- Full control over candidate communication (every applicant gets a response)

---

## Files Overview

| File | Purpose |
|------|---------|
| `portal-config.json` | **White-label config** — all branding, colors, fonts, admins, GHL settings for DDWL + Flavors |
| `careers-portal.html` | **Public careers page** — job listings, application form, CV upload, GHL webhook, Google Jobs schema |
| `admin-dashboard.html` | **Admin dashboard** — pipeline board, candidate management, job posting CRUD, onboarding tracking |
| `recruitment-pipeline.json` | **GHL pipeline definition** — 10 stages, 15 custom fields, 14 tags, 10 automations, 5 email templates |
| `onboarding-portal.html` | **New hire onboarding checklist** — 5-phase interactive portal (built in previous session) |
| `ddwl-onboarding-pipeline.json` | **GHL onboarding pipeline** — stages from Application to Active Team Member |
| `DDWL-ONBOARDING-GUIDE.md` | **Comprehensive onboarding guide** — systems, training, compliance, HR |

---

## How It Works

### Candidate Flow
```
1. Candidate visits careers-portal.html
2. Browses open positions (with schema.org markup for Google Jobs)
3. Clicks "Apply Now" → fills form + uploads CV
4. Form submits to:
   a. GHL webhook (creates contact, triggers automations)
   b. localStorage (picked up by admin dashboard)
5. GHL automation sends acknowledgment email to candidate
6. Lilly (admin@dodealswithlee.com) gets notified
```

### Admin Flow
```
1. Admin opens admin-dashboard.html
2. Sees new applications in overview + pipeline board
3. Can advance candidates through stages (click "Advance")
4. Each stage move triggers GHL automation:
   - Under Review → candidate gets "we're reviewing" email
   - Phone Screen → candidate gets calendar link
   - Interview → Krystle gets notified
   - Offer → Lee + Krystle get notified
   - Hired → triggers onboarding pipeline + tech setup notification to Daniel
   - Unsuccessful → 2-hour delay then rejection email (ALWAYS sent)
   - Talent Pool → warm email + 90-day re-engagement task
5. Stale applications (7 days no action) trigger reminder to Lilly
```

### Recruitment Pipeline Stages
```
New Application → Under Review → Phone Screen → Interview Scheduled →
Interview Complete → Reference Check → Offer Extended → Hired
                                                      ↘ Unsuccessful (rejection email auto-sent)
                                                      ↘ Talent Pool (re-engage in 90 days)
```

---

## Admin Roles & Notifications

| Admin | Email | Gets Notified For |
|-------|-------|-------------------|
| **Lee Kearney** | lee.kearney@dodealswithlee.com | Hire decisions, 90-day reviews, critical issues |
| **Krystle Gordon** | krystle.gordon@dodealswithlee.com | New apps, interviews, offers, hires, all reviews |
| **Daniel Gallagher** | daniel@exposuresolutions.me | New apps, tech setup required, system issues |
| **Lilly (AI Agent)** | admin@dodealswithlee.com | **Everything** — handles all heavy lifting admin |

---

## How to Swap Branding (DDWL → Flavors → Anyone)

### 1. Update `portal-config.json`
The config already has both DDWL and Flavors defined. To switch:

### 2. In `careers-portal.html`
Change the `CONFIG` object at the top of the script:
```javascript
var CONFIG = {
  client: "flavors",  // ← change this
  companyName: "Flavors Zante",
  shortName: "Flavors",
  logo: "https://storage.googleapis.com/.../flavors-logo.png",
  // ... update all fields
};
```

### 3. In `admin-dashboard.html`
- Update the sidebar logo `src`
- Update the `ADMINS` array
- Update localStorage key if running multiple clients on same domain

### 4. In `recruitment-pipeline.json`
- Update pipeline name, email templates, and notification recipients

### 5. Job Postings
Edit the `JOBS` array in `careers-portal.html` — this is the **only** place you need to add/remove/update job listings.

---

## Key Features

### Candidate Communication (CRITICAL)
- **Every applicant gets a response** — no one is left in the dark
- Acknowledgment email sent immediately on application
- Status update emails at every pipeline stage
- Rejection emails sent automatically (with 2-hour delay for dignity)
- Talent pool candidates get warm "we'll be in touch" email
- 3-day follow-up if candidate doesn't respond
- 7-day stale application reminder to admin

### Google Jobs Integration (FREE)
The careers portal injects `schema.org/JobPosting` structured data automatically. When hosted on a crawlable URL, jobs will appear in Google Jobs search results at no cost.

### GHL Integration Points
- **Webhook**: Application data → GHL contact creation
- **Pipeline**: 10-stage recruitment pipeline
- **Custom Fields**: 15 fields for tracking recruitment data
- **Tags**: 14 tags for segmentation and automation triggers
- **Automations**: 10 workflows for candidate communication and admin notifications
- **Email Templates**: 5 pre-built templates (acknowledgment, interview, offer, rejection, talent pool)

---

## Deployment Options

### Option A: GHL Pages (Recommended)
1. Copy HTML into GHL page builder (custom code element)
2. Forms submit directly to GHL webhook
3. Admin dashboard accessed via GHL custom menu link

### Option B: Static Hosting (Netlify/Vercel)
1. Deploy careers-portal.html as public page
2. Deploy admin-dashboard.html behind auth (or use GHL user login)
3. Both connect to GHL via webhook

### Option C: GHL Funnel
1. Create funnel with careers page as step 1
2. Application form as GHL form (native)
3. Pipeline and automations handle the rest

---

## What's NOT Included (Needs Lee/Krystle Input)

- [ ] Specific phone scripts for each role
- [ ] "A Day in the Life" documents per role
- [ ] Role-specific 30/60/90 day targets
- [ ] HR portal details (payslip access, pay schedule, benefits)
- [ ] Actual salary ranges for job postings
- [ ] Interview calendar link (GHL calendar)
- [ ] Company policies and compliance documents

---

## Tech Stack

- **Frontend**: Vanilla HTML/CSS/JS (GHL-compatible, no build step)
- **Backend**: GoHighLevel (CRM, automations, email, SMS, pipeline)
- **Data Bridge**: localStorage (local demo) / GHL API (production)
- **Job Discovery**: schema.org/JobPosting → Google Jobs
- **Fonts**: Google Fonts (Playfair Display + Inter)
- **Branding**: Configurable via portal-config.json

---

*Built by Exposure Solutions — Gamified AI Consultancy*
*System designed to be reused across DDWL, Flavors, and future clients.*
