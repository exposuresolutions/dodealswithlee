# DDWL Phone Extension & IVR Setup Guide

**Main Number:** (813) 675-0916  
**Location:** Do Deals with Lee — GHL Sub-Account `KbiucErIMNPbO1mY4qXL`  
**Date:** February 15, 2026

---

## PART 1: Team Member Extensions

Each team member gets a direct extension on the main number. Callers who know the extension can dial it directly.

### Extension Directory

| Ext. | Person           | Role                      | Email                          | Forward To         |
|------|------------------|---------------------------|--------------------------------|--------------------|
| 200  | Admin / General  | General Line              | admin@dodealswithlee.com       | (main IVR)         |
| 201  | Krystle Gordon   | Operations Manager        | krystle@dodealswithlee.com     | Krystle's cell     |
| 202  | Becky            | Team Member               | becky@dodealswithlee.com       | Becky's cell       |
| 203  | Stacy            | Team Member               | stacy@dodealswithlee.com       | Stacy's cell       |
| 204  | Lee AI           | AI Assistant              | admin@dodealswithlee.com       | (Voice AI/AI)      |
| 209  | Lee Kearney      | Lic. Real Estate Broker   | lee@dodealswithlee.com         | (813) 434-6741     |

### Setup Steps — Team Management

1. Go to **Settings → Team Management** in GHL
2. For each user listed above, click **Edit**
3. In the **Phone** field, enter their cell/forwarding number
4. In the **Extension** field next to the phone number, enter the extension number (200, 201, etc.)
5. Click **Save**
6. Repeat for all 6 team members

> **Note:** The extension field only appears when a phone number is assigned to the user. Extensions allow direct-dial routing when the main number is called.

---

## PART 2: Phone Number Configuration

Configure the main number (813) 675-0916 for optimal call handling.

### Setup Steps — Phone Number Config

1. Go to **Settings → Phone Numbers**
2. Find **(813) 675-0916** and click **Edit Configuration**
3. Configure these settings:

| Setting                          | Value                                                    |
|----------------------------------|----------------------------------------------------------|
| **Name Your Number**             | DDWL Main Line                                           |
| **Forward Calls To**             | *(leave blank — IVR workflow will handle routing)*       |
| **Call Connect**                 | ✅ Enabled (prevents voicemail false-connects)            |
| **Whisper Message**              | "Incoming call from Do Deals with Lee — press any key to connect" |
| **Call Recording**               | ✅ Enabled                                                |
| **Play Recording Message**       | ✅ "This call may be recorded for quality purposes"       |
| **Incoming Call Timeout**        | 30 seconds                                               |
| **Outgoing Call Timeout**        | 45 seconds                                               |
| **Ring Incoming Calls to Users** | *(do NOT set — IVR workflow handles this)*               |

4. Click **Save**

> **Important:** Do NOT set "Ring Incoming Calls to Selected Users" here — the IVR workflow will handle all routing. Setting both will cause conflicts.

---

## PART 3: IVR Workflow — Full Phone Menu

This creates a professional phone menu system. When someone calls (813) 675-0916, they hear a greeting and menu options.

### IVR Menu Tree

```
CALLER DIALS (813) 675-0916
│
├─ GREETING (Say/Play)
│  "Thank you for calling Do Deals with Lee. 
│   Tampa Bay's trusted real estate investment partner."
│
├─ MAIN MENU (Gather Input)
│  "Press 1 to sell your home to Lee.
│   Press 2 for coaching and events.
│   Press 3 to do a deal or fund a deal with Lee.
│   Press 4 for operations and general inquiries.
│   Press 0 to speak with a team member.
│   Or stay on the line to leave a message."
│
├─ [1] SELL YOUR HOME
│  ├─ Say/Play: "We buy homes fast — no repairs, no fees, no hassle. 
│  │   Let us connect you with our acquisitions team."
│  └─ Connect Call → Krystle Gordon (ext 201) + Lee (ext 209)
│     └─ Timeout (30s) → Record Voicemail
│        "Please leave your name, number, and property address. 
│         We'll get back to you within 24 hours."
│
├─ [2] COACHING & EVENTS
│  ├─ Say/Play: "Lee Kearney offers private one-on-one coaching 
│  │   and live real estate investing events."
│  └─ SUB-MENU (Gather Input)
│     │  "Press 1 for upcoming events.
│     │   Press 2 for private coaching.
│     │   Press 0 to go back."
│     ├─ [1] EVENTS
│     │  ├─ Say/Play: "Visit dodealswithlee.com/events for our next 
│     │  │   live event. Or leave a message and we'll send you details."
│     │  └─ Record Voicemail → End Call
│     ├─ [2] COACHING
│     │  ├─ Say/Play: "Our coaching program includes personalized 
│     │  │   portfolio analysis and action plans."
│     │  └─ Connect Call → Krystle (ext 201)
│     │     └─ Timeout → Record Voicemail → End Call
│     └─ [0] → BACK TO MAIN MENU
│
├─ [3] DO A DEAL / FUND A DEAL
│  ├─ Say/Play: "Partner with Lee Kearney on your next real estate deal."
│  └─ SUB-MENU (Gather Input)
│     │  "Press 1 to submit a deal.
│     │   Press 2 to fund a deal with Lee.
│     │   Press 0 to go back."
│     ├─ [1] SUBMIT A DEAL
│     │  ├─ Say/Play: "Visit dodealswithlee.com to submit your deal online, 
│     │  │   or leave your details after the tone."
│     │  └─ Record Voicemail → End Call
│     ├─ [2] FUND A DEAL
│     │  ├─ Say/Play: "Lee's lending program offers high-velocity wholesale 
│     │  │   and cosmetic rehab opportunities across Florida."
│     │  └─ Connect Call → Lee (ext 209)
│     │     └─ Timeout → Record Voicemail → End Call
│     └─ [0] → BACK TO MAIN MENU
│
├─ [4] OPERATIONS / GENERAL
│  ├─ Say/Play: "Connecting you with our operations team."
│  └─ Connect Call → Krystle (201) + Becky (202) + Stacy (203)
│     └─ Timeout (30s) → Record Voicemail
│        "You've reached Do Deals with Lee operations. 
│         Please leave a message and we'll return your call."
│
├─ [0] SPEAK WITH A TEAM MEMBER
│  ├─ Say/Play: "Please hold while we connect you."
│  └─ Connect Call → ALL USERS (Krystle, Becky, Stacy, Lee)
│     └─ Timeout (30s) → Record Voicemail → End Call
│
└─ [NO INPUT / TIMEOUT]
   ├─ Say/Play: "We didn't receive your selection."
   └─ REPEAT MAIN MENU (loop 2x) → Record Voicemail → End Call
```

### IVR Workflow Build Steps

#### Step 1: Create the Workflow

1. Go to **Automation → Workflows**
2. Click **+ Create Workflow**
3. Click **Start from Scratch**

#### Step 2: Add the IVR Trigger

1. Click **+ Add New Trigger**
2. Search for **"Start IVR"**
3. Name it: `DDWL Main Line IVR`
4. Select phone number: **(813) 675-0916**
5. Click **Save Trigger**

> **Note:** A phone number can only be assigned to ONE IVR workflow. If 675-0916 is already mapped elsewhere, remove it first.

#### Step 3: Add Greeting (Say/Play)

1. Add action: **IVR Say/Play**
2. Choose: **Say a Message**
3. Text: `Thank you for calling Do Deals with Lee. Tampa Bay's trusted real estate investment partner.`
4. Voice: **Woman** (professional tone)
5. Language: **English (US)**
6. Loops: **1**

#### Step 4: Add Main Menu (Gather Input)

1. Add action: **IVR Gather Input On Call**
2. Name: `Main Menu`
3. Choose: **Say a Message**
4. Text: `Press 1 to sell your home to Lee. Press 2 for coaching and events. Press 3 to do a deal or fund a deal with Lee. Press 4 for operations and general inquiries. Press 0 to speak with a team member. Or stay on the line to leave a message.`
5. Voice: **Woman**
6. Loops: **2** (repeats once if no input)
7. Advanced Settings:
   - Stop Gathering After: **10 seconds**
   - Stop Gathering on Key Press: **✅ Enabled**
   - Stop Gathering After Digits: **1**
8. **Match Conditions:** ✅ Enabled
   - Branch 1: `Sell Home` → On Key Press: **1**
   - Branch 2: `Coaching & Events` → On Key Press: **2**
   - Branch 3: `Deals` → On Key Press: **3**
   - Branch 4: `Operations` → On Key Press: **4**
   - Branch 5: `Team Member` → On Key Press: **0**
   - None Branch: `No Input` (fallback)

#### Step 5: Build Each Branch

For **each branch**, add the appropriate actions as shown in the menu tree above:

**Branch 1 (Sell Home):**
1. Add **IVR Say/Play**: "We buy homes fast — no repairs, no fees, no hassle. Let us connect you with our acquisitions team."
2. Add **IVR Connect Call**: Select Krystle Gordon + Lee Kearney. Timeout: 30 seconds. Record Call: ✅
3. Add **Record Voicemail** (on timeout): "Please leave your name, number, and property address. We'll get back to you within 24 hours."
4. Add **IVR End Call**

**Branch 2 (Coaching & Events):**
1. Add **IVR Say/Play**: "Lee Kearney offers private one-on-one coaching and live real estate investing events."
2. Add **IVR Gather Input**: Sub-menu with Press 1 (Events), Press 2 (Coaching), Press 0 (Back)
3. Build sub-branches:
   - Events → Say/Play info + Record Voicemail + End Call
   - Coaching → Connect Call to Krystle → Timeout → Voicemail → End Call
   - Back → Loop back to Main Menu Gather Input

**Branch 3 (Deals):**
1. Add **IVR Say/Play**: "Partner with Lee Kearney on your next real estate deal."
2. Add **IVR Gather Input**: Sub-menu with Press 1 (Submit Deal), Press 2 (Fund Deal), Press 0 (Back)
3. Build sub-branches:
   - Submit Deal → Say/Play + Record Voicemail + End Call
   - Fund Deal → Connect Call to Lee → Timeout → Voicemail → End Call
   - Back → Loop back to Main Menu

**Branch 4 (Operations):**
1. Add **IVR Say/Play**: "Connecting you with our operations team."
2. Add **IVR Connect Call**: Select Krystle + Becky + Stacy. Timeout: 30 seconds.
3. Add **Record Voicemail** (on timeout): "You've reached Do Deals with Lee operations. Please leave a message and we'll return your call."
4. Add **IVR End Call**

**Branch 5 (Team Member — Press 0):**
1. Add **IVR Say/Play**: "Please hold while we connect you."
2. Add **IVR Connect Call**: Select ALL users. Timeout: 30 seconds.
3. Add **Record Voicemail** (on timeout)
4. Add **IVR End Call**

**None Branch (No Input):**
1. Add **IVR Say/Play**: "We didn't receive your selection."
2. Add **Record Voicemail**: "Please leave a message after the tone."
3. Add **IVR End Call**

#### Step 6: Save & Publish

1. Review all branches and connections
2. Click **Save**
3. Toggle the workflow to **Published**
4. Test by calling (813) 675-0916 from a different phone

---

## PART 4: After-Hours Setup (Optional Enhancement)

Add time-based routing so callers get a different greeting outside business hours.

### Business Hours

| Day       | Hours          |
|-----------|----------------|
| Mon–Fri   | 9:00 AM – 6:00 PM EST |
| Saturday  | 10:00 AM – 2:00 PM EST |
| Sunday    | Closed         |

### After-Hours Flow

Add an **IF/ELSE** condition right after the IVR trigger:
- **IF** current time is within business hours → proceed to normal IVR menu
- **ELSE** → Play after-hours message:
  - "Thank you for calling Do Deals with Lee. Our office is currently closed. Our hours are Monday through Friday, 9 AM to 6 PM Eastern, and Saturday 10 AM to 2 PM. Please leave a message after the tone, or visit dodealswithlee.com anytime."
  - → Record Voicemail → End Call

---

## PART 5: Lee AI Extension (ext 204)

Extension 204 is the AI assistant powered by Lee's cloned voice. Options:
- Route ext 204 calls to **GHL Voice AI** with Lee AI persona
- Use GHL's **Conversation AI** to handle the call
- Forward to a **Bland.ai** or **Vapi** voice agent endpoint

Voicemail message:
> "You've reached Lee AI at Do Deals with Lee. For immediate help, visit dodealswithlee.com or text this number. Leave a message and we'll get back to you."

---

## PART 6: Testing Checklist

- [ ] Call (813) 675-0916 from external phone
- [ ] Verify greeting plays correctly
- [ ] Press 1 — verify connects to Krystle/Lee
- [ ] Press 2 → 1 — verify events info plays
- [ ] Press 2 → 2 — verify connects to Krystle for coaching
- [ ] Press 3 → 1 — verify deal submission voicemail
- [ ] Press 3 → 2 — verify connects to Lee for funding
- [ ] Press 4 — verify connects to operations team
- [ ] Press 0 — verify rings all team members
- [ ] No input — verify timeout → voicemail
- [ ] Verify voicemails appear in GHL conversations
- [ ] Verify call recordings are saved
- [ ] Test after-hours routing (if configured)
- [ ] Verify each team member's extension direct-dial works

---

## Cost Notes

| Item                    | Cost                          |
|-------------------------|-------------------------------|
| IVR Workflow            | **Free** (included in GHL)    |
| Text-to-Speech (TTS)   | $0.00084 per 100 characters   |
| Call Recording          | $0.0025/min                   |
| Recording Storage       | $0.0005/min/month             |
| Extensions              | **Free** (included in GHL)    |

Estimated monthly cost for moderate call volume (~200 calls/month): **$2–5/month**

---

## Quick Reference

- **IVR Workflow Location:** Automation → Workflows → "DDWL Main Line IVR"
- **Phone Config:** Settings → Phone Numbers → (813) 675-0916
- **Team Extensions:** Settings → Team Management → Edit User → Phone + Extension
- **Company Phone (fallback):** Settings → Company → Company Phone field
- **Voicemails:** Conversations → filter by voicemail
- **Call Recordings:** Contact → Activity tab → call entries
