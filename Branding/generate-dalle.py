"""
DDWL Logo Color Variations — DALL-E 3 API
==========================================
Generates color variations of Options 1 & 2 via OpenAI API.
No ChatGPT memory needed — direct API calls.
"""
import os
import time
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OUTPUT_DIR = Path(__file__).parent / "generated" / "dalle"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Reference images for upload with edit requests
REF_DIR = Path(__file__).parent / "New Logo"
OPTION1_REF = REF_DIR / "DDWL - Holographic Gradient.png"
OPTION2_REF = REF_DIR / "DDWL - Neon Redraw.png"

# ============================================================
# Simple color variations — same design, different house colors
# ============================================================
PROMPTS = {
    # Option 2 style (Neon Sign) — change house color
    "Opt2_CyanHouse": (
        'Recreate this exact "DO DEALS WITH LEE" neon sign logo on black background. '
        'Keep everything the same EXCEPT change the house icon color from orange to bright '
        'CYAN (#00E5FF) so it matches "DEALS" instead of "DO". "DO" stays orange, "DEALS" '
        'stays cyan, "WITH LEE" tag stays orange. The house must be clearly different from "DO". '
        'Same neon tube style, same layout, same reflective floor. Square format.'
    ),
    "Opt2_GoldHouse": (
        'Recreate this exact "DO DEALS WITH LEE" neon sign logo on black background. '
        'Keep everything the same EXCEPT change the house icon color to rich GOLD (#FFD700). '
        '"DO" stays orange, "DEALS" stays cyan, "WITH LEE" tag stays orange. The gold house '
        'creates a warm premium accent. Same neon tube style, same layout, same reflective floor. '
        'Square format.'
    ),
    "Opt2_WhiteHouse": (
        'Recreate this exact "DO DEALS WITH LEE" neon sign logo on black background. '
        'Keep everything the same EXCEPT change the house icon color to bright WHITE neon. '
        '"DO" stays orange, "DEALS" stays cyan, "WITH LEE" tag stays orange. The white house '
        'stands out as a neutral anchor. Same neon tube style, same layout, same reflective floor. '
        'Square format.'
    ),
    # Option 1 style (Holographic Gradient) — change house color
    "Opt1_CyanHouse": (
        'Recreate this exact "DO DEALS WITH LEE" holographic gradient logo on black background '
        'with reflective floor. Keep everything the same EXCEPT change the house icon from orange '
        'to bright CYAN (#00E5FF) so it matches the text gradient. Same holographic/iridescent '
        'text effect, same layout. Square format.'
    ),
    "Opt1_GoldHouse": (
        'Recreate this exact "DO DEALS WITH LEE" holographic gradient logo on black background '
        'with reflective floor. Keep everything the same EXCEPT change the house icon from orange '
        'to rich GOLD (#FFD700). Same holographic/iridescent text effect, same layout. Square format.'
    ),
    "Opt1_AllCyan": (
        'Recreate this exact "DO DEALS WITH LEE" holographic gradient logo on black background '
        'with reflective floor. Keep everything the same EXCEPT make the entire logo cyan-to-white '
        'gradient — remove the orange entirely. House, text, tag all in shades of cyan/white '
        'holographic glow. Same layout. Square format.'
    ),
}


def generate_dalle(prompt, name):
    """Generate image using DALL-E 3 API."""
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "hd",
        "response_format": "b64_json"
    }

    print(f"  Generating: {name}...")
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.ok:
            data = r.json()
            img_b64 = data["data"][0]["b64_json"]
            revised_prompt = data["data"][0].get("revised_prompt", "")
            img_bytes = base64.b64decode(img_b64)
            filename = f"{name}.png"
            filepath = OUTPUT_DIR / filename
            filepath.write_bytes(img_bytes)
            print(f"    ✅ Saved: {filename} ({len(img_bytes)//1024}KB)")
            if revised_prompt:
                print(f"    📝 DALL-E revised: {revised_prompt[:120]}...")
            return str(filepath)
        else:
            print(f"    ❌ HTTP {r.status_code}: {r.text[:300]}")
            return None
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:200]}")
        return None


def main():
    print("=" * 60)
    print("  DDWL Logo Color Variations — DALL-E 3")
    print("  6 variations: 3 × Option 2 + 3 × Option 1")
    print("=" * 60)

    if not OPENAI_API_KEY:
        print("\n  ❌ No OPENAI_API_KEY in .env")
        print("  Add: OPENAI_API_KEY=sk-your-key-here")
        return

    results = []
    for name, prompt in PROMPTS.items():
        filepath = generate_dalle(prompt, name)
        if filepath:
            results.append(filepath)
        time.sleep(2)

    print(f"\n{'='*60}")
    print(f"  DONE! Generated {len(results)}/{len(PROMPTS)} images")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}")

    if results:
        print(f"\n  Files:")
        for f in results:
            print(f"    {Path(f).name}")


if __name__ == '__main__':
    main()
