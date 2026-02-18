"""
Test all API keys in the Exposure Agent ecosystem.
Tests: Groq, OpenRouter, Google Gemini, Cerebras, Together AI, GitHub Models, Hugging Face, Mistral
"""

import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv('.env')

PROMPT = "Say hello in exactly 5 words."
RESULTS = {}


def test_api(name, func):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    try:
        start = time.time()
        result = func()
        elapsed = time.time() - start
        print(f"  PASS | {elapsed:.2f}s | {result[:120]}")
        RESULTS[name] = {"status": "PASS", "time": f"{elapsed:.2f}s"}
    except Exception as e:
        err = str(e)[:200]
        print(f"  FAIL | {err}")
        RESULTS[name] = {"status": "FAIL", "error": err}


# 1. GROQ
def test_groq():
    r = requests.post('https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}', 'Content-Type': 'application/json'},
        json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': PROMPT}], 'max_tokens': 50},
        timeout=15)
    data = r.json()
    if 'choices' in data:
        return data['choices'][0]['message']['content']
    raise Exception(json.dumps(data)[:200])


# 2. OPENROUTER
def test_openrouter():
    r = requests.post('https://openrouter.ai/api/v1/chat/completions',
        headers={'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}', 'Content-Type': 'application/json'},
        json={'model': 'nvidia/nemotron-nano-9b-v2:free', 'messages': [{'role': 'user', 'content': PROMPT}], 'max_tokens': 50},
        timeout=30)
    data = r.json()
    if 'choices' in data:
        return data['choices'][0]['message']['content']
    raise Exception(json.dumps(data)[:200])


# 3. GOOGLE GEMINI
def test_google():
    key = os.getenv("GOOGLE_API_KEY")
    r = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}',
        headers={'Content-Type': 'application/json'},
        json={'contents': [{'parts': [{'text': PROMPT}]}]},
        timeout=15)
    data = r.json()
    if 'candidates' in data:
        return data['candidates'][0]['content']['parts'][0]['text']
    raise Exception(json.dumps(data)[:200])


# 4. CEREBRAS
def test_cerebras():
    r = requests.post('https://api.cerebras.ai/v1/chat/completions',
        headers={'Authorization': f'Bearer {os.getenv("CEREBRAS_API_KEY")}', 'Content-Type': 'application/json'},
        json={'model': 'llama-3.3-70b', 'messages': [{'role': 'user', 'content': PROMPT}], 'max_tokens': 50},
        timeout=15)
    data = r.json()
    if 'choices' in data:
        return data['choices'][0]['message']['content']
    raise Exception(json.dumps(data)[:200])


# 5. TOGETHER AI
def test_together():
    r = requests.post('https://api.together.xyz/v1/chat/completions',
        headers={'Authorization': f'Bearer {os.getenv("TOGETHER_API_KEY")}', 'Content-Type': 'application/json'},
        json={'model': 'meta-llama/Llama-3.3-70B-Instruct-Turbo', 'messages': [{'role': 'user', 'content': PROMPT}], 'max_tokens': 50},
        timeout=15)
    data = r.json()
    if 'choices' in data:
        return data['choices'][0]['message']['content']
    raise Exception(json.dumps(data)[:200])


# 6. GITHUB MODELS
def test_github():
    r = requests.post('https://models.inference.ai.azure.com/chat/completions',
        headers={'Authorization': f'Bearer {os.getenv("GITHUB_MODELS_TOKEN")}', 'Content-Type': 'application/json'},
        json={'model': 'gpt-4o-mini', 'messages': [{'role': 'user', 'content': PROMPT}], 'max_tokens': 50},
        timeout=15)
    data = r.json()
    if 'choices' in data:
        return data['choices'][0]['message']['content']
    raise Exception(json.dumps(data)[:200])


# 7. HUGGING FACE
def test_huggingface():
    r = requests.post('https://router.huggingface.co/hf-inference/models/microsoft/Phi-3-mini-4k-instruct/v1/chat/completions',
        headers={'Authorization': f'Bearer {os.getenv("HF_API_KEY")}', 'Content-Type': 'application/json'},
        json={'model': 'microsoft/Phi-3-mini-4k-instruct',
              'messages': [{'role': 'user', 'content': PROMPT}],
              'max_tokens': 50},
        timeout=30)
    data = r.json()
    if 'choices' in data:
        return data['choices'][0]['message']['content']
    raise Exception(json.dumps(data)[:200])


# 8. MISTRAL
def test_mistral():
    r = requests.post('https://api.mistral.ai/v1/chat/completions',
        headers={'Authorization': f'Bearer {os.getenv("MISTRAL_API_KEY")}', 'Content-Type': 'application/json'},
        json={'model': 'mistral-small-latest', 'messages': [{'role': 'user', 'content': PROMPT}], 'max_tokens': 50},
        timeout=15)
    data = r.json()
    if 'choices' in data:
        return data['choices'][0]['message']['content']
    raise Exception(json.dumps(data)[:200])


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  EXPOSURE AGENT — FULL API TEST SUITE")
    print("=" * 60)

    test_api("1. Groq (Llama 3.3 70B)", test_groq)
    test_api("2. OpenRouter (Qwen free)", test_openrouter)
    test_api("3. Google Gemini (2.5 Flash)", test_google)
    test_api("4. Cerebras (Llama 3.3 70B)", test_cerebras)
    test_api("5. Together AI (Llama 3.3 70B)", test_together)
    test_api("6. GitHub Models (GPT-4o-mini)", test_github)
    test_api("7. Hugging Face (Mistral 7B)", test_huggingface)
    test_api("8. Mistral (Small)", test_mistral)

    # Summary
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    passed = 0
    for name, result in RESULTS.items():
        icon = "PASS" if result["status"] == "PASS" else "FAIL"
        detail = result.get("time", result.get("error", "")[:60])
        print(f"  {name:<40} {icon}  {detail}")
        if result["status"] == "PASS":
            passed += 1
    print(f"\n  {passed}/{len(RESULTS)} APIs working")
    print("=" * 60)
