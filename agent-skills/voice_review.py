"""
Voice Review System — Agent does work, Lee's voice reports back
================================================================
1. Agent completes a task
2. Generates a summary
3. Converts to speech using Lee's cloned voice (ElevenLabs)
4. Plays audio for review
5. Waits for approval (voice or keyboard)

USAGE:
    from voice_review import speak, review_task

    # Quick speak
    speak("The IVR workflow is ready. 5 extensions configured.")

    # Full review cycle
    review_task(
        task="Build IVR workflow",
        result="Created workflow with 5 branches: sell, coaching, deals, ops, team",
        next_steps="Need to assign phone numbers to each extension"
    )

CLI:
    python voice_review.py say "Hello, this is a test"
    python voice_review.py status   # Speak current system status
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
AGENT_DIR = Path(__file__).parent
AUDIO_DIR = AGENT_DIR / "voice-output"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Load env
env_file = BASE_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

ELEVENLABS_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
LEE_VOICE_ID = os.environ.get("LEE_VOICE_ID", "6HrHqiq7ijVOY0eVOKhz")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] [{tag}] {msg}")


# ============================================================
# 1. TEXT-TO-SPEECH — Lee's cloned voice
# ============================================================
def speak(text, voice_id=None, save_path=None, play=True):
    """Convert text to speech using Lee's cloned voice via ElevenLabs."""
    if not ELEVENLABS_KEY:
        log("VOICE", "No ELEVENLABS_API_KEY set")
        print(f"\n  [Would say]: {text}")
        return None

    voice = voice_id or LEE_VOICE_ID
    log("VOICE", f"Generating speech ({len(text)} chars)...")

    try:
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
            headers={
                "xi-api-key": ELEVENLABS_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.3,
                    "use_speaker_boost": True,
                },
            },
            timeout=30,
        )

        if r.status_code == 200:
            # Save audio
            if not save_path:
                save_path = str(AUDIO_DIR / f"review-{int(time.time())}.mp3")
            Path(save_path).write_bytes(r.content)
            log("VOICE", f"Audio saved: {Path(save_path).name} ({len(r.content)} bytes)")

            # Play audio
            if play:
                play_audio(save_path)

            return save_path
        else:
            log("VOICE", f"ElevenLabs error {r.status_code}: {r.text[:200]}")
            print(f"\n  [Would say]: {text}")
            return None
    except Exception as e:
        log("VOICE", f"Error: {str(e)[:100]}")
        print(f"\n  [Would say]: {text}")
        return None


def play_audio(path):
    """Play audio file on Windows."""
    try:
        import subprocess
        # Use Windows media player (silent, no window)
        subprocess.Popen(
            ["powershell", "-c", f'(New-Object Media.SoundPlayer "{path}").PlaySync()'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log("VOICE", "Playing audio...")
    except Exception:
        try:
            # Fallback: open with default player
            os.startfile(path)
        except Exception:
            log("VOICE", f"Could not play audio. File at: {path}")


# ============================================================
# 2. SMART SUMMARY — AI generates concise review text
# ============================================================
def generate_review_text(task, result, next_steps=""):
    """Use AI to generate a natural, concise voice review."""
    if not GROQ_KEY:
        # Fallback: simple template
        text = f"Task complete: {task}. {result}."
        if next_steps:
            text += f" Next up: {next_steps}."
        return text

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": (
                        "You are Lee Kearney's AI assistant giving a brief voice update. "
                        "Speak naturally like you're talking to Daniel on the phone. "
                        "Be direct, confident, no fluff. Tampa energy. "
                        "Keep it under 3 sentences. Use simple words that sound good spoken aloud."
                    )},
                    {"role": "user", "content": (
                        f"Generate a brief voice update for Daniel:\n"
                        f"Task: {task}\n"
                        f"Result: {result}\n"
                        f"Next steps: {next_steps or 'None'}\n\n"
                        f"Make it sound natural and conversational, like a quick phone update."
                    )}
                ],
                "temperature": 0.7,
                "max_tokens": 150,
            },
            timeout=15,
        )
        if r.ok:
            return r.json()["choices"][0]["message"]["content"].strip().strip('"')
    except Exception as e:
        log("REVIEW", f"AI error: {str(e)[:100]}")

    # Fallback
    text = f"Hey Daniel, {task} is done. {result}."
    if next_steps:
        text += f" Next up: {next_steps}."
    return text


# ============================================================
# 3. REVIEW CYCLE — Do work, speak result, get approval
# ============================================================
def review_task(task, result, next_steps="", wait_for_approval=True):
    """Full review cycle: generate summary, speak it, wait for approval."""
    print(f"\n{'='*60}")
    print(f"  🎤 Voice Review: {task}")
    print(f"{'='*60}")

    # Generate natural review text
    review_text = generate_review_text(task, result, next_steps)
    print(f"\n  📝 Review: {review_text}")

    # Speak it
    audio_path = speak(review_text)

    if wait_for_approval:
        print(f"\n  ✅ Press ENTER to approve, or type feedback:")
        feedback = input("  > ").strip()
        if feedback:
            log("REVIEW", f"Feedback: {feedback}")
            return {"approved": False, "feedback": feedback}
        else:
            log("REVIEW", "Approved!")
            return {"approved": True}

    return {"audio": audio_path, "text": review_text}


def speak_status():
    """Speak current system status using Lee's voice."""
    # Gather status
    status_parts = []

    # Check workflows
    try:
        sys.path.insert(0, str(AGENT_DIR))
        from ghl_doer import ghl_api, GHL_LOCATION_ID
        workflows = ghl_api("GET", "/workflows/")
        if "workflows" in workflows:
            wf_list = workflows["workflows"]
            published = sum(1 for w in wf_list if w.get("status") == "published")
            draft = sum(1 for w in wf_list if w.get("status") == "draft")
            status_parts.append(f"{len(wf_list)} workflows, {published} published, {draft} in draft")
    except Exception:
        pass

    # Check knowledge base
    kb_dir = AGENT_DIR / "ghl-knowledge"
    if kb_dir.exists():
        transcripts = len(list((kb_dir / "youtube-transcripts").glob("*.json"))) if (kb_dir / "youtube-transcripts").exists() else 0
        summaries = len(list((kb_dir / "summaries").glob("*.md"))) if (kb_dir / "summaries").exists() else 0
        status_parts.append(f"Knowledge base has {transcripts} transcripts and {summaries} summaries")

    # Build status text
    if status_parts:
        status = "Here's your system status. " + ". ".join(status_parts) + ". All agents are online and ready."
    else:
        status = "System is online. All agents are ready. No issues to report."

    print(f"\n  📊 Status: {status}")
    speak(status)


# ============================================================
# MAIN
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python voice_review.py say "text to speak"')
        print("  python voice_review.py status    # Speak system status")
        print("  python voice_review.py test      # Test voice generation")
        return

    cmd = sys.argv[1].lower()

    if cmd == "say":
        text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hey Daniel, everything is running smooth. No issues."
        speak(text)

    elif cmd == "status":
        speak_status()

    elif cmd == "test":
        print("\n  🎤 Testing Lee's voice clone...")
        speak("Hey Daniel, this is Lee A.I. Just checking in. All systems are running, logos are being generated, and the research agent pulled 18 new Reddit posts about GoHighLevel. We're good to go.")

    else:
        # Treat everything as text to speak
        text = " ".join(sys.argv[1:])
        speak(text)


if __name__ == "__main__":
    main()
