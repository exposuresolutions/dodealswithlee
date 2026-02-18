"""Regenerate just the Lee AI greeting and voicemail audio files."""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

API_KEY = os.getenv("ELEVENLABS_API_KEY")
LEE_VOICE_ID = os.getenv("LEE_VOICE_ID", "6HrHqiq7ijVOY0eVOKhz")
OUTPUT_DIR = Path(__file__).parent.parent / "Media" / "ivr-audio"

SCRIPTS = {
    "18-lee-ai-greeting": "Hey, this is Lee AI, your real estate investing assistant. How can I help you today?",
    "19-lee-ai-voicemail": "You've reached Lee AI at Do Deals with Lee. For immediate help, visit dodealswithlee.com or text this number. Leave a message and we'll get back to you.",
}

for name, text in SCRIPTS.items():
    print(f"Generating: {name}...")
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{LEE_VOICE_ID}",
        headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
        json={"text": text, "model_id": "eleven_monolingual_v1",
              "voice_settings": {"stability": 0.75, "similarity_boost": 0.85, "style": 0.0, "use_speaker_boost": True}},
        timeout=30)
    if r.status_code == 200:
        filepath = OUTPUT_DIR / f"{name}.mp3"
        with open(filepath, "wb") as f:
            f.write(r.content)
        print(f"  OK: {filepath.name} ({len(r.content)/1024:.1f} KB)")
    else:
        print(f"  FAIL: {r.status_code} {r.text[:100]}")

print("Done!")
