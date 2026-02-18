"""
Multi-Brain Agent — Ask all free LLMs at once, compare answers, pick the best.
Also: Can analyze your PC, scan files, generate reports, and take actions.

This was IMPOSSIBLE before today. Now we have 6 free brains to query simultaneously.
"""

import os
import json
import time
import subprocess
import platform
import psutil
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')


# ============================================================
# ALL FREE BRAINS
# ============================================================
BRAINS = {
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
        "url": None,  # special handling
        "key_env": "GOOGLE_API_KEY",
        "model": "gemini-2.5-flash",
        "style": "google",
    },
}


def query_brain(name, config, prompt, system_prompt="You are a helpful assistant."):
    """Query a single brain and return the result."""
    key = os.getenv(config["key_env"])
    if not key:
        return {"name": name, "response": None, "error": "No API key", "time": 0}

    start = time.time()
    try:
        if config["style"] == "openai":
            r = requests.post(config["url"],
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": config["model"],
                      "messages": [
                          {"role": "system", "content": system_prompt},
                          {"role": "user", "content": prompt}
                      ],
                      "max_tokens": 500},
                timeout=20)
            data = r.json()
            if "choices" in data:
                elapsed = time.time() - start
                return {"name": name, "response": data["choices"][0]["message"]["content"],
                        "time": elapsed, "error": None}
            else:
                return {"name": name, "response": None, "error": str(data)[:100], "time": time.time() - start}

        elif config["style"] == "google":
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{config['model']}:generateContent?key={key}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}]},
                timeout=20)
            data = r.json()
            if "candidates" in data:
                elapsed = time.time() - start
                return {"name": name, "response": data["candidates"][0]["content"]["parts"][0]["text"],
                        "time": elapsed, "error": None}
            else:
                return {"name": name, "response": None, "error": str(data)[:100], "time": time.time() - start}

    except Exception as e:
        return {"name": name, "response": None, "error": str(e)[:100], "time": time.time() - start}


def ask_all_brains(prompt, system_prompt="You are a helpful assistant."):
    """Send prompt to ALL brains simultaneously, return all results."""
    results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(query_brain, name, config, prompt, system_prompt): name
            for name, config in BRAINS.items()
        }
        for future in as_completed(futures):
            results.append(future.result())

    # Sort by speed
    results.sort(key=lambda x: x["time"])
    return results


def get_pc_info():
    """Gather real PC system info."""
    info = {}
    info["hostname"] = platform.node()
    info["os"] = f"{platform.system()} {platform.release()} ({platform.version()})"
    info["cpu"] = platform.processor()
    info["cpu_cores"] = psutil.cpu_count(logical=False)
    info["cpu_threads"] = psutil.cpu_count(logical=True)
    info["cpu_usage"] = f"{psutil.cpu_percent(interval=1)}%"
    mem = psutil.virtual_memory()
    info["ram_total"] = f"{mem.total / (1024**3):.1f} GB"
    info["ram_used"] = f"{mem.used / (1024**3):.1f} GB"
    info["ram_available"] = f"{mem.available / (1024**3):.1f} GB"
    info["ram_percent"] = f"{mem.percent}%"

    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "drive": part.device,
                "total": f"{usage.total / (1024**3):.1f} GB",
                "free": f"{usage.free / (1024**3):.1f} GB",
                "percent_used": f"{usage.percent}%"
            })
        except:
            pass
    info["disks"] = disks

    # Top processes by memory
    procs = []
    for p in psutil.process_iter(['name', 'memory_info']):
        try:
            mem_mb = p.info['memory_info'].rss / (1024**2)
            if mem_mb > 50:
                procs.append({"name": p.info['name'], "ram_mb": round(mem_mb)})
        except:
            pass
    procs.sort(key=lambda x: x["ram_mb"], reverse=True)
    info["top_processes"] = procs[:15]

    # Network
    net = psutil.net_io_counters()
    info["network"] = {
        "bytes_sent": f"{net.bytes_sent / (1024**2):.0f} MB",
        "bytes_recv": f"{net.bytes_recv / (1024**2):.0f} MB"
    }

    # Battery
    battery = psutil.sensors_battery()
    if battery:
        info["battery"] = f"{battery.percent}% ({'charging' if battery.power_plugged else 'on battery'})"

    # Boot time
    boot = datetime.fromtimestamp(psutil.boot_time())
    info["uptime"] = str(datetime.now() - boot).split('.')[0]

    return info


def demo():
    """Full demo: scan PC, send to all brains, get recommendations."""

    print("\n" + "=" * 70)
    print("  MULTI-BRAIN AGENT — PC Analysis Demo")
    print("  6 Free AI Brains Working Simultaneously")
    print("=" * 70)

    # Step 1: Scan PC
    print("\n  [1/3] Scanning your PC...")
    pc_info = get_pc_info()
    print(f"  ✓ Hostname: {pc_info['hostname']}")
    print(f"  ✓ OS: {pc_info['os']}")
    print(f"  ✓ CPU: {pc_info['cpu_cores']} cores / {pc_info['cpu_threads']} threads @ {pc_info['cpu_usage']}")
    print(f"  ✓ RAM: {pc_info['ram_used']} / {pc_info['ram_total']} ({pc_info['ram_percent']})")
    for d in pc_info['disks']:
        print(f"  ✓ Disk {d['drive']}: {d['free']} free / {d['total']} ({d['percent_used']} used)")
    print(f"  ✓ Uptime: {pc_info['uptime']}")
    top5 = [p["name"] + "(" + str(p["ram_mb"]) + "MB)" for p in pc_info['top_processes'][:5]]
    print(f"  ✓ Top RAM hogs: {', '.join(top5)}")

    # Step 2: Ask all brains to analyze
    print(f"\n  [2/3] Sending PC data to 6 AI brains simultaneously...")
    prompt = f"""Analyze this Windows PC and give me your TOP 3 specific, actionable recommendations to improve performance. Be concrete — name specific processes to kill, settings to change, or tools to install. Keep it brief (3 bullet points max).

PC Data:
{json.dumps(pc_info, indent=2)}"""

    system_prompt = "You are a Windows PC optimization expert. Give brief, specific, actionable advice. No fluff."

    results = ask_all_brains(prompt, system_prompt)

    # Step 3: Display all results
    print(f"\n  [3/3] All 6 brains responded!\n")

    for i, r in enumerate(results, 1):
        status = "✓" if r["response"] else "✗"
        speed = f"{r['time']:.2f}s"
        print(f"  {'─' * 66}")
        print(f"  {status} Brain #{i}: {r['name']} ({speed})")
        print(f"  {'─' * 66}")
        if r["response"]:
            # Indent the response
            for line in r["response"].strip().split("\n"):
                print(f"    {line}")
        else:
            print(f"    ERROR: {r['error']}")
        print()

    # Speed leaderboard
    print(f"  {'=' * 66}")
    print(f"  SPEED LEADERBOARD")
    print(f"  {'=' * 66}")
    for i, r in enumerate(results, 1):
        bar = "█" * int(r["time"] * 10)
        status = "✓" if r["response"] else "✗"
        print(f"  {i}. {status} {r['name']:<25} {r['time']:.2f}s {bar}")

    print(f"\n  Total cost: $0.00 (all free APIs)")
    print(f"  {'=' * 66}\n")


if __name__ == "__main__":
    demo()
