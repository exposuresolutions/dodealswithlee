"""
DDWL Logo Brainstorm — Push to ALL AI engines simultaneously.
Each engine generates 4 detailed image prompts for logo variations.
Results saved to Branding/logo-prompts/ for use in DALL-E/Midjourney/Ideogram.
"""
import os
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

OUTPUT_DIR = Path(__file__).parent / "logo-prompts"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# AI ENGINES
# ============================================================
ENGINES = {
    "Groq (Llama 70B)": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
        "model": "llama-3.3-70b-versatile",
        "style": "openai",
    },
    "Mistral (Small)": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "key_env": "MISTRAL_API_KEY",
        "model": "mistral-small-latest",
        "style": "openai",
    },
    "Cerebras (Llama 70B)": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "key_env": "CEREBRAS_API_KEY",
        "model": "llama-3.3-70b",
        "style": "openai",
    },
    "GitHub (GPT-4o-mini)": {
        "url": "https://models.inference.ai.azure.com/chat/completions",
        "key_env": "GITHUB_MODELS_TOKEN",
        "model": "gpt-4o-mini",
        "style": "openai",
    },
    "OpenRouter (Nemotron)": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
        "model": "nvidia/nemotron-nano-9b-v2:free",
        "style": "openai",
    },
    "Google (Gemini 2.5)": {
        "url": None,
        "key_env": "GOOGLE_API_KEY",
        "model": "gemini-2.5-flash",
        "style": "google",
    },
    "Kimi 2.5": {
        "url": "https://api.moonshot.cn/v1/chat/completions",
        "key_env": "KIMI_API_KEY",
        "model": "moonshot-v1-128k",
        "style": "openai",
    },
}

# ============================================================
# MASTER PROMPT
# ============================================================
SYSTEM_PROMPT = """You are a world-class brand designer and creative director specializing in premium real estate branding. You have 20 years of experience creating $10K+ logo packages for high-net-worth real estate investors and national brands.

Your expertise includes:
- Color psychology for real estate (trust, authority, premium positioning)
- Logo scalability (from billboard to business card to embroidered merch)
- Neon sign design (actual fabrication-ready concepts)
- Merch integration (logos that FLOW through products, not just stamped on)
- Modern design trends (2025-2026): sophisticated minimalism, jewel tones, high-contrast accents"""

USER_PROMPT = """# DDWL Logo Redesign — Generate 4 Image Prompts

## Brand: Do Deals With Lee™
Real estate investment education & deal-making. 7,000+ deals, $500M+ volume, Inc. 5000. CEO Lee Kearney — Licensed Broker, MBA, Tampa FL with national reach.

## Current Logo Elements (KEEP these):
- House icon (roofline with window)
- "DO" on top left
- House icon between "DO" and next to it
- "DEALS" large below
- "WITH LEE" in a tag/badge below DEALS
- Layout: stacked, reads top-to-bottom

## Brand Colors:
- Cyan #00E5FF (primary — trust, modern energy)
- Orange #FF6B00 (secondary — action, Florida sun)
- Gold #FFD700 (accent — success, premium)
- Black #0A0A0A (background — luxury, authority)

## Client Feedback:
- They LOVE the neon glow aesthetic (Options 1 & 2 from previous round)
- Option 1 was "Holographic Glow" — cyan-to-gold gradient, iridescent metallic, reflective floor
- Option 2 was "Classic Neon" — true neon tube outlines, orange/blue split
- CRITICAL FIX: The house icon must be a DIFFERENT color than "DO" (Krystle's feedback)
- Lee wants MORE VARIATIONS in the same style/feel

## Design Constraints:
- Must be readable on a FOR SALE sign at 30 feet
- Must work as a 2-inch embroidered logo on a polo
- Must work as an actual neon sign (Lee is getting one fabricated)
- Must look premium on dark AND light backgrounds
- Colors should be able to FLOW through merch (t-shirts, hats) — not just a logo stamp

## YOUR TASK:
Generate exactly 4 detailed image generation prompts (for DALL-E / Midjourney). Each prompt should be a complete, ready-to-paste prompt that will generate a high-quality logo.

For each prompt, also provide:
1. **Name** — A catchy 2-3 word name for this variation
2. **Color Breakdown** — Exactly which color goes where (DO, house, DEALS, WITH LEE tag)
3. **Why It Works** — 1-2 sentences on why this color/style combo is effective
4. **Best Application** — Where this version shines most (signage, merch, digital, neon)

## The 4 Variations:

**VARIATION 1**: Classic Neon style — house in CYAN (#00E5FF), "DO" in orange (#FF6B00), "DEALS" in cyan, "WITH LEE" tag in orange. True neon tube outlines on black.

**VARIATION 2**: Classic Neon style — house in GOLD (#FFD700), "DO" in orange, "DEALS" in cyan, "WITH LEE" tag in gold. Warm/cool contrast.

**VARIATION 3**: Holographic Glow style — house in pure cyan with orange glow edge, text has cyan-to-gold gradient shift, reflective floor effect. Premium iridescent feel.

**VARIATION 4**: YOUR BEST IDEA — Based on your expertise in real estate branding and color psychology, what combination would make this logo a $10K showstopper? Surprise us. Consider what would look incredible on a billboard, a neon sign, AND embroidered on a black polo.

Format each as:
---
### [Variation Name]
**Image Prompt:** [complete DALL-E/Midjourney prompt, 100-200 words]
**Color Breakdown:** DO=[color], House=[color], DEALS=[color], WITH LEE=[color], Background=[color]
**Why It Works:** [explanation]
**Best Application:** [where it shines]
---
"""

MOCKUP_PROMPT = """# DDWL Logo Mockup Descriptions

Now generate 6 detailed image prompts showing the WINNING logo (Variation 1 — cyan house, orange DO, cyan DEALS) applied to real-world contexts:

1. **FOR SALE Sign** — Professional real estate yard sign on a green lawn in front of a modern Florida home. The DDWL neon-style logo is on a black sign with "FOR SALE" above and phone number below. Daytime, sunny, palm trees visible.

2. **Billboard** — Highway billboard mockup, the DDWL logo large and centered on black background. "7,000+ Deals Closed" tagline below. Blue sky, highway visible. The neon glow effect makes it pop even in daylight.

3. **Merch: Black T-Shirt** — Premium black t-shirt laid flat. The logo isn't just printed on — the cyan and orange neon colors FLOW through the fabric like light streaks, starting from the logo and trailing down the shirt. Lifestyle brand feel.

4. **Merch: Snapback Hat** — Black snapback hat with the logo embroidered on the front. The cyan and orange threads catch the light. Side panel has "DDWL" in small cyan text. Premium quality, streetwear meets business.

5. **Merch: Black Polo** — Professional black polo shirt with the logo embroidered small on the left chest. Gold "WITH LEE" tag visible. Clean, executive look. The kind of polo you'd wear to a $500M closing.

6. **Neon Sign** — The logo as an actual neon sign mounted on a dark brick wall in Lee's podcast studio. Visible neon tubes, mounting brackets, warm glow on the brick. Moody, professional, Instagram-worthy.

For each, provide a complete DALL-E/Midjourney image prompt (100-150 words) ready to paste.
"""


def query_engine(name, config, prompt, system_prompt):
    """Query a single AI engine."""
    key = os.getenv(config["key_env"])
    if not key:
        return {"name": name, "response": None, "error": "No API key", "time": 0}

    start = time.time()
    try:
        if config["style"] == "google":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{config['model']}:generateContent?key={key}"
            r = requests.post(url, json={
                "contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}],
                "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.8}
            }, timeout=60)
            if r.ok:
                data = r.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return {"name": name, "response": text, "error": None, "time": time.time() - start}
            return {"name": name, "response": None, "error": f"HTTP {r.status_code}", "time": time.time() - start}
        else:
            r = requests.post(config["url"],
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": config["model"],
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.8,
                },
                timeout=60)
            if r.ok:
                data = r.json()
                text = data["choices"][0]["message"]["content"]
                return {"name": name, "response": text, "error": None, "time": time.time() - start}
            return {"name": name, "response": None, "error": f"HTTP {r.status_code}: {r.text[:200]}", "time": time.time() - start}
    except Exception as e:
        return {"name": name, "response": None, "error": str(e)[:200], "time": time.time() - start}


def main():
    print("=" * 70)
    print("  DDWL LOGO BRAINSTORM — All AI Engines")
    print("  Pushing to all brains simultaneously...")
    print("=" * 70)

    # Phase 1: Logo Variations
    print("\n  PHASE 1: Logo Variation Prompts")
    print("  " + "-" * 66)

    results = {}
    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = {
            pool.submit(query_engine, name, cfg, USER_PROMPT, SYSTEM_PROMPT): name
            for name, cfg in ENGINES.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            result = future.result()
            results[name] = result
            if result["error"]:
                print(f"  ❌ {name}: {result['error']}")
            else:
                print(f"  ✅ {name}: {len(result['response'])} chars in {result['time']:.1f}s")
                # Save individual result
                safe_name = name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "-")
                out_file = OUTPUT_DIR / f"variations_{safe_name}.md"
                out_file.write_text(f"# Logo Variations from {name}\n\n{result['response']}", encoding="utf-8")

    # Phase 2: Mockup Prompts (use the fastest successful engine)
    print(f"\n  PHASE 2: Application Mockup Prompts")
    print("  " + "-" * 66)

    mockup_results = {}
    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = {
            pool.submit(query_engine, name, cfg, MOCKUP_PROMPT, SYSTEM_PROMPT): name
            for name, cfg in ENGINES.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            result = future.result()
            mockup_results[name] = result
            if result["error"]:
                print(f"  ❌ {name}: {result['error']}")
            else:
                print(f"  ✅ {name}: {len(result['response'])} chars in {result['time']:.1f}s")
                safe_name = name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "-")
                out_file = OUTPUT_DIR / f"mockups_{safe_name}.md"
                out_file.write_text(f"# Mockup Prompts from {name}\n\n{result['response']}", encoding="utf-8")

    # Save combined results
    combined = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "variations": {}, "mockups": {}}
    for name, r in results.items():
        if r["response"]:
            combined["variations"][name] = r["response"]
    for name, r in mockup_results.items():
        if r["response"]:
            combined["mockups"][name] = r["response"]

    combined_file = OUTPUT_DIR / "all-results.json"
    combined_file.write_text(json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")

    # Summary
    success_v = sum(1 for r in results.values() if r["response"])
    success_m = sum(1 for r in mockup_results.values() if r["response"])

    print(f"\n{'='*70}")
    print(f"  RESULTS SUMMARY")
    print(f"  Logo Variations: {success_v}/{len(ENGINES)} engines responded")
    print(f"  Mockup Prompts:  {success_m}/{len(ENGINES)} engines responded")
    print(f"  Output folder:   {OUTPUT_DIR}")
    print(f"{'='*70}")
    print(f"\n  Next steps:")
    print(f"  1. Review the prompts in {OUTPUT_DIR}")
    print(f"  2. Pick the best prompts from each engine")
    print(f"  3. Paste into ChatGPT/DALL-E, Midjourney, or Ideogram to generate images")
    print(f"  4. Create mockups with the top picks")
    print(f"  5. Build the reveal presentation for Lee")


if __name__ == '__main__':
    main()
