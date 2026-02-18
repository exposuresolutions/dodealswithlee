"""
Logo Reveal — Generate all audio clips with Lee's voice
=========================================================
Uses ElevenLabs API to generate each clip of the narration.
Output: individual MP3 files for CapCut timeline.
"""

import os
import sys
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
env_file = BASE_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
VOICE_ID = os.environ.get("LEE_VOICE_ID", "6HrHqiq7ijVOY0eVOKhz")
OUTPUT_DIR = Path(__file__).parent / "audio-clips"
OUTPUT_DIR.mkdir(exist_ok=True)

CLIPS = [
    ("01-intro", "What's up everybody, it's Lee Kearney — Do Deals With Lee."),
    ("02-setup", "We've been working on something big behind the scenes. A brand refresh that matches where we're headed in twenty twenty-six."),
    ("03-context", "We took the feedback from the team — Krystle wanted the house icon to pop in its own color, separate from the DO. And I wanted that neon energy we love."),
    ("04-reveal-cyan", "First up — the Cyan House Neon. That electric blue house pops right off the screen. Gold DO, cyan everything else. Clean."),
    ("05-reveal-gold", "Number two — the Gold House Classic. This one's premium. Gold house, gold DO, that cyan glow on DEALS. This is the luxury play."),
    ("06-reveal-holo", "And number three — the Holographic. This one moves. Cyan to gold gradient across the text, orange house. It's got that future energy."),
    ("07-mockups", "But check this out — we didn't just make logos. We mocked up the neon sign for the podcast studio, the snapback hat, the black tee, even a for-sale sign on a property in Florida."),
    ("08-recommendation", "My pick? The Cyan House. That blue house with the gold DO — it reads from a hundred feet away, it works small on a business card, and it's going to look incredible as a neon sign."),
    ("09-outro", "Seven thousand deals and counting. New look, same hustle. Do Deals With Lee — let's go."),
]


def generate_clip(name, text):
    """Generate a single audio clip."""
    print(f"  Generating: {name}...")
    print(f"    Text: {text[:60]}...")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    body = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.80,
            "style": 0.35,
            "use_speaker_boost": True,
        },
    }

    r = requests.post(url, headers=headers, json=body, timeout=30)
    if r.status_code == 200:
        out_path = OUTPUT_DIR / f"{name}.mp3"
        out_path.write_bytes(r.content)
        size_kb = len(r.content) / 1024
        print(f"    Saved: {out_path.name} ({size_kb:.0f} KB)")
        return True
    else:
        print(f"    ERROR {r.status_code}: {r.text[:200]}")
        return False


def main():
    if not API_KEY:
        print("ERROR: ELEVENLABS_API_KEY not set")
        return

    print("\n" + "=" * 60)
    print("  Logo Reveal — Generating Lee's Voice Narration")
    print(f"  Voice ID: {VOICE_ID}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Clips: {len(CLIPS)}")
    print("=" * 60 + "\n")

    success = 0
    for name, text in CLIPS:
        if generate_clip(name, text):
            success += 1

    print(f"\n  Done! {success}/{len(CLIPS)} clips generated.")
    print(f"  Files in: {OUTPUT_DIR}")
    print(f"\n  Next: Import into CapCut with the logo images.")


if __name__ == "__main__":
    main()
