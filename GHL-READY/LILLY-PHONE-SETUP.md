# Lilly AI Phone Setup - DDWL

> **URGENT**: Lilly is answering phones now - needs immediate GHL integration

---

## Current Phone Extensions (Need GHL Setup)

| Extension | Person/Role | Email | Status |
|-----------|-------------|-------|---------|
| 200 | Admin / General | admin@dodealswithlee.com | ⚠️ Need GHL setup |
| 201 | Krystle Gordon | krystle.gordon@dodealswithlee.com | ⚠️ Need GHL setup |
| 202 | Becky | becky@dodealswithlee.com | ⚠️ Need GHL setup |
| 203 | Stacy | stacy@dodealswithlee.com | ⚠️ Need GHL setup |
| 204 | Lilly (AI) | lilly@dodealswithlee.com | 🔴 URGENT - Live now |
| 209 | Lee Kearney | lee.kearney@dodealswithlee.com | ⚠️ Need GHL setup |

---

## GHL Phone System Setup Steps

### 1. Main Number Configuration
**Number**: (813) 675-0916

**In GHL**: Settings > Phone Numbers > (813) 675-0916 > IVR / Call Routing

### 2. IVR Menu Setup
```
"Thank you for calling Do Deals With Lee. Please select:
Press 1 for Homeowners wanting to sell
Press 2 for Investors wanting to partner
Press 3 for Students and Coaching
Press 4 for Admin and General Inquiries
Press 5 for Lilly, our AI Assistant
Press 9 for Lee Kearney (Broker)
Press 0 for Operator"
```

### 3. Extension Routing
- **Press 1** → Route to Lilly (AI) → She qualifies and schedules
- **Press 2** → Route to Lilly (AI) → She qualifies and books strategy call
- **Press 3** → Route to Krystle (ext. 201)
- **Press 4** → Route to Admin (ext. 200)
- **Press 5** → Route to Lilly (ext. 204) - Direct AI access
- **Press 9** → Route to Lee (ext. 209) → If no answer, Krystle
- **Press 0** → Route to Admin (ext. 200)

---

## Lilly AI Configuration

### Voice Settings
- **Voice**: ElevenLabs Lee Clone (ID: 6HrHqiq7ijVOY0eVOKhz)
- **Greeting**: "Hi, I'm Lilly, Lee's AI assistant. How can I help you today?"
- **Capability**: Handle homeowner and investor calls, book appointments, answer questions

### Call Flow for Lilly
1. **Answer**: "Hi, I'm Lilly, Lee's AI assistant..."
2. **Qualify**: Ask series of questions (property type, location, timeline)
3. **Route**: If qualified, schedule with Lee/Krystle
4. **Follow-up**: Send SMS confirmation and info
5. **Log**: All calls logged in GHL with transcript

### Lilly's Scripts
**Homeowner Script**:
- "Are you looking to sell a property?"
- "What's the property address?"
- "What's your timeline?"
- "Any repairs needed?"
- "Best contact number?"

**Investor Script**:
- "Are you looking to invest or fund deals?"
- "What's your investment range?"
- "What type of properties interest you?"
- "Have you invested before?"
- "Schedule strategy call with Lee?"

---

## Implementation Steps

### Step 1: GHL Phone Setup (15 minutes)
1. **Log into GHL**: app.gohighlevel.com
2. **Go to**: Settings > Phone Numbers
3. **Select**: (813) 675-0916
4. **Configure**: IVR / Call Routing
5. **Set extensions**: 200-204, 209 as listed above

### Step 2: Lilly Integration (10 minutes)
1. **Go to**: Settings > AI Assistant
2. **Configure**: Lilly with ElevenLabs voice
3. **Set scripts**: Homeowner and investor qualification
4. **Test**: Call ext. 204 to verify

### Step 3: Test All Extensions (10 minutes)
1. **Call main number**: (813) 675-0916
2. **Test each option**: 1, 2, 3, 4, 5, 9, 0
3. **Verify routing**: Each goes to correct person/AI
4. **Check GHL**: All calls logged properly

---

## Emergency Contacts if Issues

| Issue | Contact | Method |
|-------|---------|--------|
| GHL phone not working | Krystle | ext. 201 |
| Lilly not answering | Daniel | daniel@exposuresolutions.me |
| Extensions not routing | Admin | ext. 200 |
| Urgent - system down | Lee | ext. 209 |

---

## Testing Checklist

- [ ] Main number answers with IVR menu
- [ ] Option 1 routes to Lilly (homeowners)
- [ ] Option 2 routes to Lilly (investors)
- [ ] Option 3 routes to Krystle (students)
- [ ] Option 4 routes to Admin (general)
- [ ] Option 5 routes to Lilly (direct AI)
- [ ] Option 9 routes to Lee (broker)
- [ ] Option 0 routes to Admin (operator)
- [ ] Lilly can qualify leads
- [ ] Lilly can book appointments
- [ ] All calls logged in GHL
- [ ] SMS confirmations sent

---

## Next Steps After Phone Setup

1. **Monitor calls** for first week
2. **Optimize Lilly's responses** based on real calls
3. **Add more languages** if needed
4. **Set up after-hours** routing to Lilly
5. **Create call analytics** dashboard

---

**Priority**: Get Lilly connected to GHL phones TODAY - she's already taking calls!
