"""
DDWL Logo Generator — Gemini 2.5 Flash Image (FREE tier)
==========================================================
Generates logo variations automatically and saves to Branding/generated/
You handle Kimi + DALL-E manually, this handles Gemini.
Uses gemini-2.5-flash-image model via google-genai SDK.
"""
import os
import time
import base64
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).parent.parent / '.env')

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OUTPUT_DIR = Path(__file__).parent / "generated" / "gemini-flash"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = genai.Client(api_key=GOOGLE_API_KEY)

# ============================================================
# LOGO PROMPTS — 4 Variations based on Lee & Krystle feedback
# ============================================================
LOGO_PROMPTS = {
    "V1_Cyan_House_Neon": (
        'A premium neon sign logo for "DO DEALS WITH LEE" real estate brand on a pure black background. '
        'Classic neon tube style with visible tube outlines and realistic glow. Layout: "DO" in bold orange '
        'neon (#FF6B00) top left. A house icon (simple roofline with small window) in bright CYAN neon '
        '(#00E5FF) next to "DO" — the house MUST be a different color than "DO". Below them, "DEALS" in '
        'large bold cyan neon (#00E5FF). Below that, a tag/badge shape containing "WITH LEE" in orange neon '
        '(#FF6B00). Soft neon glow on the black surface. Sharp, clean, readable from distance. '
        'Professional real estate investment brand. Square format, centered composition.'
    ),
    "V2_Gold_House_Neon": (
        'A premium neon sign logo for "DO DEALS WITH LEE" real estate brand on a pure black background. '
        'Classic neon tube style with visible tube outlines and warm glow. Layout: "DO" in bold orange '
        'neon (#FF6B00) top left. A house icon (simple roofline with small window) in rich GOLD neon '
        '(#FFD700) next to "DO" — the house is gold, distinct from the orange "DO". Below them, "DEALS" '
        'in large bold cyan neon (#00E5FF). Below that, a tag/badge shape containing "WITH LEE" in gold '
        'neon (#FFD700) matching the house. Warm gold and cool cyan contrast. Soft neon glow on black. '
        'Sharp, clean, readable from distance. Professional real estate brand. Square format, centered.'
    ),
    "V3_Holographic_Glow": (
        'A premium holographic glow logo for "DO DEALS WITH LEE" real estate brand on a reflective black '
        'surface with mirror floor effect. Layout: "DO" top left with a cyan-to-gold iridescent gradient. '
        'A house icon (roofline with window) in pure bright cyan (#00E5FF) with a subtle orange (#FF6B00) '
        'glow halo around its edges — house is clearly different color from "DO". Below, "DEALS" in large '
        'bold text with the same cyan-to-gold holographic gradient, metallic iridescent sheen. Below that, '
        '"WITH LEE" in a tag/badge with cyan-to-gold gradient. Reflective floor mirrors the logo. '
        'Futuristic, premium, luxury real estate brand. Square format, centered composition.'
    ),
    "V4_Gilded_Zenith": (
        'A $10,000 premium logo for "DO DEALS WITH LEE" real estate brand on deep matte black background. '
        'Architectural luxury style combining neon glow with metallic precision. "DO" top left in clean '
        'cyan (#00E5FF) with a subtle gold inner glow for depth. House icon (roofline with window) in '
        'solid gleaming GOLD (#FFD700) with a precise thin cyan edge glow defining its silhouette — '
        'the gold house is the centerpiece. "DEALS" large and bold in powerful cyan (#00E5FF) with a '
        'refined thin gold outline catching light. "WITH LEE" in a sleek black tag with gold text, '
        'subtly backlit with soft cyan aura. High contrast, sophisticated minimalism, jewel-tone accents. '
        'Volumetric, premium, suitable for billboard, neon sign, and embroidered polo. Square format.'
    ),
}

# ============================================================
# MOCKUP PROMPTS — Real-world applications
# ============================================================
MOCKUP_PROMPTS = {
    "M1_ForSale_Sign": (
        'A professional real estate FOR SALE yard sign on a green lawn in front of a modern Florida home. '
        'The sign is sleek black with the "DO DEALS WITH LEE" neon-style logo (cyan house icon, orange '
        '"DO", cyan "DEALS", orange "WITH LEE" tag) centrally placed. Above the logo: "FOR SALE" in '
        'white text. Below: phone number. Bright sunny day, blue sky, palm trees, upscale neighborhood. '
        'The neon colors pop even in daylight. Professional real estate photography style.'
    ),
    "M2_Billboard": (
        'A massive highway billboard against a clear blue sky. Black background with the "DO DEALS WITH '
        'LEE" neon logo (cyan house, orange "DO", cyan "DEALS") large and centered, glowing with neon '
        'effect. Below the logo: "7,000+ Deals Closed" in crisp white modern text. Highway stretching '
        'into distance below. The neon glow commands attention. Professional billboard photography.'
    ),
    "M3_Black_Tshirt": (
        'A premium heavy cotton black t-shirt laid flat on a light surface. The "DO DEALS WITH LEE" '
        'neon logo on the chest, but the cyan and orange neon colors FLOW through the fabric like '
        'light streaks, trailing downward from the logo. Not just printed on — the colors run through '
        'the shirt like a wave of neon light. Lifestyle brand streetwear feel. High-end product photo.'
    ),
    "M4_Snapback_Hat": (
        'A high-quality black snapback hat, close-up angled shot. The "DO DEALS WITH LEE" logo '
        'embroidered on the front panel — cyan house, orange "DO", cyan "DEALS" in detailed thread '
        'work catching the light. Side panel has small "DDWL" in cyan embroidery. Premium quality, '
        'clean stitching. Streetwear meets professional business. Product photography on clean background.'
    ),
    "M5_Black_Polo": (
        'A sophisticated black polo shirt on a hanger. The "DO DEALS WITH LEE" logo embroidered small '
        'on the left chest — cyan and orange threads creating refined contrast on black fabric. Below '
        'the logo, a small gold "WITH LEE" tag. Clean, executive look. The kind of polo you would wear '
        'to a $500 million real estate closing. Premium product photography.'
    ),
    "M6_Neon_Sign_Studio": (
        'An authentic neon sign of the "DO DEALS WITH LEE" logo mounted on a dark textured brick wall '
        'in a professional podcast studio. Visible glass neon tubes glowing cyan and orange. Industrial '
        'mounting brackets visible. Warm neon glow illuminating the surrounding dark brick, creating '
        'dramatic shadows. Moody, professional, Instagram-worthy. Podcast microphone slightly visible '
        'in foreground. Professional interior photography.'
    ),
}


def generate_gemini_image(prompt, name, attempts=1):
    """Generate image using Gemini 2.5 Flash Image model (free tier)."""
    saved = []
    for i in range(attempts):
        print(f"  Generating: {name} (attempt {i+1}/{attempts})...")
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                )
            )
            img_count = 0
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(f"    📝 {part.text[:100]}...")
                elif part.inline_data is not None:
                    img_count += 1
                    img_bytes = base64.b64decode(part.inline_data.data)
                    filename = f"{name}_{i+1}_{img_count}.png"
                    filepath = OUTPUT_DIR / filename
                    filepath.write_bytes(img_bytes)
                    saved.append(str(filepath))
                    print(f"    ✅ Saved: {filename} ({len(img_bytes)//1024}KB)")
            if img_count == 0:
                print(f"    ⚠️ No image in response, got text only")
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:300]}")
        time.sleep(3)  # rate limit
    return saved


def main():
    print("=" * 70)
    print("  DDWL LOGO GENERATOR — Gemini 2.5 Flash Image (FREE)")
    print("  You: Kimi + DALL-E | Me: Gemini Flash")
    print("=" * 70)

    if not GOOGLE_API_KEY:
        print("  ❌ No GOOGLE_API_KEY found in .env")
        return

    all_files = []

    # Phase 1: Logo Variations (1 image per prompt, 4 prompts)
    print(f"\n  PHASE 1: Logo Variations (4 prompts)")
    print("  " + "-" * 66)
    for name, prompt in LOGO_PROMPTS.items():
        files = generate_gemini_image(prompt, name, attempts=1)
        all_files.extend(files)

    # Phase 2: Mockups
    print(f"\n  PHASE 2: Application Mockups (6 prompts)")
    print("  " + "-" * 66)
    for name, prompt in MOCKUP_PROMPTS.items():
        files = generate_gemini_image(prompt, name, attempts=1)
        all_files.extend(files)

    # Summary
    print(f"\n{'='*70}")
    print(f"  DONE! Generated {len(all_files)} images")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*70}")
    print(f"\n  Division of labor:")
    print(f"  🤖 Gemini Flash: {len(all_files)} images (this script)")
    print(f"  👤 You + Kimi: generating in browser")
    print(f"  👤 You + DALL-E: generating in browser")
    print(f"\n  Next: Review all outputs, pick top 3, build reveal presentation")


if __name__ == '__main__':
    main()
