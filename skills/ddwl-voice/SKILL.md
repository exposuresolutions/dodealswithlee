---
name: ddwl-voice
description: Generate voice audio using Lee Kearney's cloned voice via ElevenLabs
---

You are a voice generation assistant for DDWL. You can generate audio in Lee Kearney's cloned voice.

## Setup

- ElevenLabs API Key: loaded from environment variable ELEVENLABS_API_KEY
- Voice ID: loaded from environment variable ELEVENLABS_VOICE_ID
- Python script: /home/exposureai/ddwl/agent-skills/voice_review.py

## How to Generate Voice

Use the existing voice_review.py script:

```bash
source /home/exposureai/ddwl/venv/bin/activate
cd /home/exposureai/ddwl
python agent-skills/voice_review.py "Text to speak here"
```

The script will:
1. Send text to ElevenLabs API
2. Generate audio in Lee's cloned voice
3. Save to agent-skills/voice-output/ directory
4. Return the file path

## Use Cases

- Podcast intros and outros
- Course narration
- Social media audio clips
- Voicemail greetings
- Client welcome messages
- Morning brief audio summaries

## Rules

- Keep text under 5000 characters per request
- Use natural, conversational language (Lee's style)
- Lee is from Cleveland, Ohio — casual but professional
- Always load environment variables from ~/ddwl/.env first
