"""
Generate IVR greeting audio using Lee's ElevenLabs voice clone.
Creates all the audio files needed for the DDWL phone system.
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

API_KEY = os.getenv("ELEVENLABS_API_KEY")
LEE_VOICE_ID = os.getenv("LEE_VOICE_ID", "6HrHqiq7ijVOY0eVOKhz")
OUTPUT_DIR = Path(__file__).parent.parent / "Media" / "ivr-audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# All IVR scripts
SCRIPTS = {
    "01-main-greeting": (
        "Thank you for calling Do Deals with Lee. "
        "Tampa Bay's trusted real estate investment partner."
    ),
    "02-main-menu": (
        "Press 1 to sell your home to Lee. "
        "Press 2 for coaching and events. "
        "Press 3 to do a deal or fund a deal with Lee. "
        "Press 4 for operations and general inquiries. "
        "Press 0 to speak with a team member. "
        "Or stay on the line to leave a message."
    ),
    "03-sell-home": (
        "We buy homes fast. No repairs, no fees, no hassle. "
        "Let us connect you with our acquisitions team."
    ),
    "04-sell-voicemail": (
        "Please leave your name, number, and property address. "
        "We'll get back to you within 24 hours."
    ),
    "05-coaching-events": (
        "Lee Kearney offers private one-on-one coaching "
        "and live real estate investing events."
    ),
    "06-coaching-submenu": (
        "Press 1 for upcoming events. "
        "Press 2 for private coaching. "
        "Press 0 to go back."
    ),
    "07-events-info": (
        "Visit dodealswithlee.com slash events for our next live event. "
        "Or leave a message and we'll send you the details."
    ),
    "08-coaching-info": (
        "Our coaching program includes personalized portfolio analysis "
        "and action plans. Let me connect you with our team."
    ),
    "09-deals-intro": (
        "Partner with Lee Kearney on your next real estate deal."
    ),
    "10-deals-submenu": (
        "Press 1 to submit a deal. "
        "Press 2 to fund a deal with Lee. "
        "Press 0 to go back."
    ),
    "11-submit-deal": (
        "Visit dodealswithlee.com to submit your deal online, "
        "or leave your details after the tone."
    ),
    "12-fund-deal": (
        "Lee's lending program offers high-velocity wholesale "
        "and cosmetic rehab opportunities across Florida. "
        "Let me connect you with Lee."
    ),
    "13-operations": (
        "Connecting you with our operations team."
    ),
    "14-operations-voicemail": (
        "You've reached Do Deals with Lee operations. "
        "Please leave a message and we'll return your call."
    ),
    "15-connect-team": (
        "Please hold while we connect you."
    ),
    "16-no-input": (
        "We didn't receive your selection. "
        "Please leave a message after the tone."
    ),
    "17-after-hours": (
        "Thank you for calling Do Deals with Lee. "
        "Our office is currently closed. "
        "Our hours are Monday through Friday, 9 AM to 6 PM Eastern, "
        "and Saturday 10 AM to 2 PM. "
        "Please leave a message after the tone, "
        "or visit dodealswithlee.com anytime."
    ),
    "18-lee-ai-greeting": (
        "Hey, this is Lee AI, your real estate investing assistant. How can I help you today?"
    ),
    "19-lee-ai-voicemail": (
        "You've reached Lee AI at Do Deals with Lee. "
        "For immediate help, visit dodealswithlee.com or text this number. "
        "Leave a message and we'll get back to you."
    ),
    "20-recording-notice": (
        "This call may be recorded for quality purposes."
    ),
    "21-whisper": (
        "Incoming call from Do Deals with Lee. Press any key to connect."
    ),
}


def generate_audio(name, text):
    """Generate audio using ElevenLabs API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{LEE_VOICE_ID}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.85,
            "style": 0.0,
            "use_speaker_boost": True,
        }
    }

    print(f"  Generating: {name}...")
    print(f"    Text: {text[:80]}...")
    r = requests.post(url, headers=headers, json=data, timeout=30)

    if r.status_code == 200:
        filepath = OUTPUT_DIR / f"{name}.mp3"
        with open(filepath, "wb") as f:
            f.write(r.content)
        size_kb = len(r.content) / 1024
        print(f"    ✓ Saved: {filepath.name} ({size_kb:.1f} KB)")
        return True
    else:
        print(f"    ✗ Error {r.status_code}: {r.text[:200]}")
        return False


def main():
    print("\n" + "=" * 60)
    print("  DDWL IVR Audio Generator — Lee's Voice")
    print("=" * 60)
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Voice: Lee Kearney ({LEE_VOICE_ID})")
    print(f"  Scripts: {len(SCRIPTS)} audio files")
    print()

    # Calculate total characters (ElevenLabs charges per character)
    total_chars = sum(len(t) for t in SCRIPTS.values())
    est_cost = total_chars * 0.00003  # ~$0.30 per 10K chars
    print(f"  Total characters: {total_chars:,}")
    print(f"  Estimated cost: ${est_cost:.2f}")
    print()

    confirm = input("  Generate all audio files? (y/n): ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return

    success = 0
    failed = 0
    for name, text in SCRIPTS.items():
        if generate_audio(name, text):
            success += 1
        else:
            failed += 1

    print(f"\n  {'=' * 56}")
    print(f"  Done! {success} generated, {failed} failed")
    print(f"  Files saved to: {OUTPUT_DIR}")
    print(f"  {'=' * 56}\n")


if __name__ == "__main__":
    main()
