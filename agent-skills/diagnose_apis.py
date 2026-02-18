"""Diagnose failing APIs — OpenRouter, Together, GitHub, HuggingFace, Mistral"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv('.env')


def diagnose():
    # 1. OpenRouter - try nvidia free model
    print("=== OPENROUTER (nvidia model) ===")
    key = os.getenv("OPENROUTER_API_KEY")
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "nvidia/nemotron-nano-9b-v2:free",
              "messages": [{"role": "user", "content": "Say hi in 5 words"}],
              "max_tokens": 50},
        timeout=30)
    print(f"  Status: {r.status_code}")
    print(f"  {r.text[:200]}")

    # 2. Together AI - check key
    print("\n=== TOGETHER AI ===")
    key = os.getenv("TOGETHER_API_KEY")
    print(f"  Key length: {len(key)}, starts: {key[:8]}")
    r = requests.get("https://api.together.xyz/v1/models",
        headers={"Authorization": f"Bearer {key}"},
        timeout=10)
    print(f"  Status: {r.status_code}")
    print(f"  {r.text[:150]}")

    # 3. GitHub Models - check scopes
    print("\n=== GITHUB MODELS ===")
    key = os.getenv("GITHUB_MODELS_TOKEN")
    r = requests.get("https://api.github.com/user",
        headers={"Authorization": f"Bearer {key}"},
        timeout=10)
    print(f"  Status: {r.status_code}")
    scopes = r.headers.get("X-OAuth-Scopes", "none")
    print(f"  Scopes: {scopes}")
    user = r.json().get("login", "unknown")
    print(f"  User: {user}")

    # 4. Hugging Face - try chat completions endpoint
    print("\n=== HUGGING FACE ===")
    key = os.getenv("HF_API_KEY")
    r = requests.post(
        "https://router.huggingface.co/hf-inference/models/microsoft/Phi-3-mini-4k-instruct/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "microsoft/Phi-3-mini-4k-instruct",
              "messages": [{"role": "user", "content": "Say hi in 5 words"}],
              "max_tokens": 50},
        timeout=30)
    print(f"  Status: {r.status_code}")
    print(f"  {r.text[:200]}")

    # 5. Mistral - check models endpoint
    print("\n=== MISTRAL ===")
    key = os.getenv("MISTRAL_API_KEY")
    print(f"  Key: {key[:8]}...")
    r = requests.get("https://api.mistral.ai/v1/models",
        headers={"Authorization": f"Bearer {key}"},
        timeout=10)
    print(f"  Status: {r.status_code}")
    print(f"  {r.text[:200]}")


if __name__ == "__main__":
    diagnose()
