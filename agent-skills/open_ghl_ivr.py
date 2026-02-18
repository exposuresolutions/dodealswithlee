"""
Open GHL IVR Workflow Builder — Quick Launch
=============================================
Opens Chrome with the correct profile directly to the GHL workflow page.
Then prints step-by-step instructions for using the IVR Recipe.
"""
import subprocess
import os
import sys
import time

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
GHL_LOCATION = "KbiucErIMNPbO1mY4qXL"
GHL_URL = f"https://app.gohighlevel.com/location/{GHL_LOCATION}/automation/list"

# Use Profile 4 (admin@dodealswithlee.com)
PROFILE = "Profile 4"

print("\n" + "=" * 60)
print("  DDWL IVR Setup — Quick Launch")
print("=" * 60)

# Launch Chrome with the GHL profile
print(f"\n  Opening Chrome ({PROFILE}) → GHL Workflows...")
subprocess.Popen([
    CHROME_EXE,
    f"--profile-directory={PROFILE}",
    GHL_URL,
])

time.sleep(3)

print("""
  ✅ Chrome opened to GHL Workflows page.

  ══════════════════════════════════════════════════════════
  FOLLOW THESE STEPS (5 minutes total):
  ══════════════════════════════════════════════════════════

  STEP 1: CREATE WORKFLOW FROM RECIPE
  ─────────────────────────────────────
  1. Click [+ Create Workflow]
  2. Click [Recipes] tab (not "Start from Scratch")
  3. Search for "IVR" in the recipe search
  4. Select the "IVR" recipe
  5. Click [Select This Recipe] or [Use Recipe]

  STEP 2: SET THE TRIGGER
  ─────────────────────────────────────
  1. Click on the trigger node at the top
  2. Select phone number: (813) 675-0916
  3. Click [Save Trigger]

  STEP 3: EDIT THE GREETING (Say/Play node)
  ─────────────────────────────────────
  1. Click the first Say/Play action
  2. Switch to "Play a Message"
  3. Upload: Media/ivr-audio/01-main-greeting.mp3
     (Or keep "Say a Message" and paste this text):
     "Thank you for calling Do Deals with Lee.
      Tampa Bay's trusted real estate investment partner."
  4. Click Save

  STEP 4: EDIT THE MAIN MENU (Gather Input node)
  ─────────────────────────────────────
  1. Click the Gather Input action
  2. Switch to "Play a Message"
  3. Upload: Media/ivr-audio/02-main-menu.mp3
     (Or paste this text):
     "Press 1 to sell your home to Lee.
      Press 2 for coaching and events.
      Press 3 to do a deal or fund a deal with Lee.
      Press 4 for operations and general inquiries.
      Press 0 to speak with a team member.
      Or stay on the line to leave a message."
  4. Set Loops: 2
  5. Enable Match Conditions
  6. Add branches:
     - Branch "Sell Home" → Key 1
     - Branch "Coaching" → Key 2
     - Branch "Deals" → Key 3
     - Branch "Operations" → Key 4
     - Branch "Team" → Key 0
  7. Click Save

  STEP 5: CONFIGURE EACH BRANCH
  ─────────────────────────────────────

  [1] SELL HOME branch:
      → Add Say/Play: "We buy homes fast. No repairs, no fees, no hassle."
        (or upload 03-sell-home.mp3)
      → Add Connect Call: Select Krystle Gordon + Lee Kearney
        Timeout: 30s, Record: ✅
      → Add Record Voicemail on timeout
      → Add End Call

  [2] COACHING branch:
      → Add Say/Play: "Lee Kearney offers private coaching and live events."
        (or upload 05-coaching-events.mp3)
      → Add Gather Input sub-menu:
        "Press 1 for events. Press 2 for coaching. Press 0 to go back."
        (or upload 06-coaching-submenu.mp3)
      → Events sub-branch: Say/Play events info → Voicemail → End
      → Coaching sub-branch: Connect Call to Krystle → Voicemail → End

  [3] DEALS branch:
      → Add Say/Play: "Partner with Lee on your next deal."
        (or upload 09-deals-intro.mp3)
      → Add Gather Input sub-menu:
        "Press 1 to submit a deal. Press 2 to fund a deal. Press 0 to go back."
        (or upload 10-deals-submenu.mp3)
      → Submit sub-branch: Say/Play → Voicemail → End
      → Fund sub-branch: Connect Call to Lee → Voicemail → End

  [4] OPERATIONS branch:
      → Add Say/Play: "Connecting you with our operations team."
        (or upload 13-operations.mp3)
      → Add Connect Call: Krystle + Becky + Stacy
        Timeout: 30s
      → Add Record Voicemail on timeout
      → Add End Call

  [0] TEAM MEMBER branch:
      → Add Say/Play: "Please hold while we connect you."
        (or upload 15-connect-team.mp3)
      → Add Connect Call: ALL team members
        Timeout: 30s
      → Add Record Voicemail → End Call

  [NO INPUT] branch:
      → Add Say/Play: "We didn't receive your selection."
        (or upload 16-no-input.mp3)
      → Add Record Voicemail → End Call

  STEP 6: SAVE & PUBLISH
  ─────────────────────────────────────
  1. Click [Save] at the top
  2. Toggle workflow to [Published]
  3. Test by calling (813) 675-0916

  ══════════════════════════════════════════════════════════
  AUDIO FILES LOCATION:
  ══════════════════════════════════════════════════════════
""")

# List audio files
audio_dir = os.path.join(os.path.dirname(__file__), "..", "Media", "ivr-audio")
if os.path.exists(audio_dir):
    files = sorted(os.listdir(audio_dir))
    for f in files:
        size = os.path.getsize(os.path.join(audio_dir, f)) / 1024
        print(f"  {f:<35} {size:.0f} KB")
else:
    print(f"  Audio dir not found: {audio_dir}")

print(f"\n  Full path: {os.path.abspath(audio_dir)}")
print(f"\n  TIP: Drag files from File Explorer into GHL upload dialogs")
print(f"  NOTE: GHL recommends .wav format. MP3 usually works too.\n")
