"""
Usage Tracker — Track API costs across all providers.
Logs every API call with tokens, cost, task type, and provider.
Generates daily/weekly/monthly reports.
Recommends cheaper alternatives when spending is high.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

TRACKER_FILE = Path(__file__).parent / "usage-log.json"

# Cost per 1K tokens (input/output) — updated Feb 2026
PRICING = {
    "anthropic": {"name": "Claude Sonnet", "input": 0.003, "output": 0.015, "tier": "paid"},
    "groq": {"name": "Groq Llama 70B", "input": 0.0, "output": 0.0, "tier": "free"},
    "cerebras": {"name": "Cerebras Llama 70B", "input": 0.0, "output": 0.0, "tier": "free"},
    "mistral": {"name": "Mistral Small", "input": 0.0, "output": 0.0, "tier": "free"},
    "openrouter": {"name": "OpenRouter Free", "input": 0.0, "output": 0.0, "tier": "free"},
    "github-models": {"name": "GitHub GPT-4o-mini", "input": 0.0, "output": 0.0, "tier": "free"},
    "google": {"name": "Gemini 2.5 Flash", "input": 0.0, "output": 0.0, "tier": "free"},
    "elevenlabs": {"name": "ElevenLabs Voice", "input": 0.0, "output": 0.0, "tier": "paid",
                   "per_char": 0.00003},  # ~$0.30 per 10K chars
    "ghl-voice": {"name": "GHL Voice AI", "input": 0.0, "output": 0.0, "tier": "paid",
                  "per_minute": 0.07},
    "ghl-conversation": {"name": "GHL Conversation AI", "input": 0.0, "output": 0.0, "tier": "paid",
                         "per_message": 0.002},
    "ghl-workflow": {"name": "GHL Workflow AI", "input": 0.0, "output": 0.0, "tier": "paid",
                     "per_execution": 0.01},
    "kimi": {"name": "Kimi K2", "input": 0.0006, "output": 0.0025, "tier": "paid"},
}


class UsageTracker:
    def __init__(self, path=TRACKER_FILE):
        self.path = path
        self.data = self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, "r") as f:
                return json.load(f)
        return {"entries": [], "summary": {}}

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def log(self, provider, task_type, input_tokens=0, output_tokens=0,
            chars=0, minutes=0, messages=0, executions=0, project="general", notes=""):
        """Log a single API usage event."""
        pricing = PRICING.get(provider, {})
        
        # Calculate cost
        cost = 0.0
        if input_tokens or output_tokens:
            cost += (input_tokens / 1000) * pricing.get("input", 0)
            cost += (output_tokens / 1000) * pricing.get("output", 0)
        if chars:
            cost += chars * pricing.get("per_char", 0)
        if minutes:
            cost += minutes * pricing.get("per_minute", 0)
        if messages:
            cost += messages * pricing.get("per_message", 0)
        if executions:
            cost += executions * pricing.get("per_execution", 0)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "provider_name": pricing.get("name", provider),
            "tier": pricing.get("tier", "unknown"),
            "task_type": task_type,
            "project": project,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "chars": chars,
            "minutes": minutes,
            "messages": messages,
            "executions": executions,
            "cost_usd": round(cost, 6),
            "notes": notes,
        }
        self.data["entries"].append(entry)
        self._save()
        return entry

    def report(self, days=7):
        """Generate a usage report for the last N days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self.data["entries"] if e["timestamp"] >= cutoff]

        if not recent:
            return {"period": f"Last {days} days", "total_cost": 0, "entries": 0,
                    "by_provider": {}, "by_task": {}, "by_project": {},
                    "savings_tip": "No usage recorded yet."}

        total_cost = sum(e["cost_usd"] for e in recent)
        total_tokens = sum(e["total_tokens"] for e in recent)

        # By provider
        by_provider = {}
        for e in recent:
            p = e["provider_name"]
            if p not in by_provider:
                by_provider[p] = {"cost": 0, "tokens": 0, "calls": 0, "tier": e["tier"]}
            by_provider[p]["cost"] += e["cost_usd"]
            by_provider[p]["tokens"] += e["total_tokens"]
            by_provider[p]["calls"] += 1

        # By task type
        by_task = {}
        for e in recent:
            t = e["task_type"]
            if t not in by_task:
                by_task[t] = {"cost": 0, "tokens": 0, "calls": 0}
            by_task[t]["cost"] += e["cost_usd"]
            by_task[t]["tokens"] += e["total_tokens"]
            by_task[t]["calls"] += 1

        # By project
        by_project = {}
        for e in recent:
            p = e["project"]
            if p not in by_project:
                by_project[p] = {"cost": 0, "tokens": 0, "calls": 0}
            by_project[p]["cost"] += e["cost_usd"]
            by_project[p]["tokens"] += e["total_tokens"]
            by_project[p]["calls"] += 1

        # Savings tips
        paid_cost = sum(v["cost"] for v in by_provider.values() if v["tier"] == "paid")
        free_calls = sum(v["calls"] for v in by_provider.values() if v["tier"] == "free")
        paid_calls = sum(v["calls"] for v in by_provider.values() if v["tier"] == "paid")

        tips = []
        if paid_calls > free_calls:
            tips.append("You're using paid APIs more than free ones. Route simple tasks to Groq/Cerebras.")
        if by_task.get("coding", {}).get("cost", 0) > 0.50:
            tips.append("Coding tasks costing too much. Draft with Groq/Cerebras, only final test with Claude.")
        if by_task.get("chat", {}).get("cost", 0) > 0.20:
            tips.append("Chat tasks should use free APIs. Switch to Groq for all simple chat.")
        if total_cost > 5.0:
            tips.append(f"Spending ${total_cost:.2f} in {days} days. Review which tasks really need paid APIs.")
        if not tips:
            tips.append("Good cost management! Mostly using free APIs.")

        return {
            "period": f"Last {days} days",
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "entries": len(recent),
            "paid_vs_free": f"{paid_calls} paid / {free_calls} free calls",
            "by_provider": {k: {"cost": f"${v['cost']:.4f}", "tokens": v["tokens"],
                                "calls": v["calls"], "tier": v["tier"]}
                           for k, v in sorted(by_provider.items(), key=lambda x: x[1]["cost"], reverse=True)},
            "by_task": {k: {"cost": f"${v['cost']:.4f}", "calls": v["calls"]}
                       for k, v in sorted(by_task.items(), key=lambda x: x[1]["cost"], reverse=True)},
            "by_project": {k: {"cost": f"${v['cost']:.4f}", "calls": v["calls"]}
                          for k, v in sorted(by_project.items(), key=lambda x: x[1]["cost"], reverse=True)},
            "savings_tips": tips,
        }

    def print_report(self, days=7):
        """Pretty-print the usage report."""
        r = self.report(days)
        print(f"\n{'='*60}")
        print(f"  USAGE REPORT — {r['period']}")
        print(f"{'='*60}")
        print(f"  Total cost:   ${r['total_cost']:.4f}")
        print(f"  Total tokens: {r['total_tokens']:,}")
        print(f"  API calls:    {r['entries']}")
        print(f"  Paid vs Free: {r.get('paid_vs_free', 'N/A')}")

        print(f"\n  BY PROVIDER:")
        for name, data in r["by_provider"].items():
            icon = "$" if data["tier"] == "paid" else "F"
            print(f"    [{icon}] {name:<25} {data['cost']:>10}  ({data['calls']} calls, {data['tokens']:,} tokens)")

        print(f"\n  BY TASK TYPE:")
        for name, data in r["by_task"].items():
            print(f"    {name:<25} {data['cost']:>10}  ({data['calls']} calls)")

        print(f"\n  BY PROJECT:")
        for name, data in r["by_project"].items():
            print(f"    {name:<25} {data['cost']:>10}  ({data['calls']} calls)")

        print(f"\n  SAVINGS TIPS:")
        for tip in r["savings_tips"]:
            print(f"    → {tip}")
        print(f"{'='*60}\n")


# ============================================================
# SMART ROUTER — picks the cheapest provider for each task
# ============================================================
ROUTING_TABLE = {
    # Task type → preferred provider (cheapest first)
    "chat": ["groq", "cerebras", "mistral"],
    "coding": ["cerebras", "groq", "github-models"],
    "coding_review": ["anthropic"],  # Only Claude for final review
    "reasoning": ["google", "mistral", "anthropic"],
    "translation": ["mistral", "google", "groq"],
    "summarization": ["cerebras", "groq", "google"],
    "content_writing": ["google", "mistral", "groq"],
    "voice_generation": ["elevenlabs"],
    "crm_automation": ["ghl-workflow"],
    "email_draft": ["mistral", "groq", "cerebras"],
    "seo_analysis": ["google", "groq", "cerebras"],
    "complex_analysis": ["anthropic", "google"],
    "second_opinion": ["kimi"],
}


def get_best_provider(task_type):
    """Return the cheapest provider for a given task type."""
    providers = ROUTING_TABLE.get(task_type, ["groq"])
    for p in providers:
        pricing = PRICING.get(p, {})
        if pricing.get("tier") == "free":
            return p, pricing.get("name", p), "FREE"
    # If no free option, return first (cheapest paid)
    p = providers[0]
    return p, PRICING.get(p, {}).get("name", p), "PAID"


def print_routing_table():
    """Show the full routing table with costs."""
    print(f"\n{'='*70}")
    print(f"  SMART ROUTING TABLE — Cheapest Provider Per Task")
    print(f"{'='*70}")
    print(f"  {'Task':<25} {'Provider':<25} {'Cost':<10}")
    print(f"  {'-'*60}")
    for task, providers in ROUTING_TABLE.items():
        p, name, cost = get_best_provider(task)
        print(f"  {task:<25} {name:<25} {cost}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    import sys
    tracker = UsageTracker()

    if len(sys.argv) < 2:
        print("Usage: python usage_tracker.py [report|route|log]")
        print("  report [days]    — Show usage report")
        print("  route            — Show smart routing table")
        print("  log <provider> <task> <in_tokens> <out_tokens> [project]")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "report":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        tracker.print_report(days)
    elif cmd == "route":
        print_routing_table()
    elif cmd == "log":
        if len(sys.argv) < 5:
            print("  Usage: log <provider> <task> <in_tokens> <out_tokens> [project]")
        else:
            provider = sys.argv[2]
            task = sys.argv[3]
            in_tok = int(sys.argv[4])
            out_tok = int(sys.argv[5]) if len(sys.argv) > 5 else 0
            project = sys.argv[6] if len(sys.argv) > 6 else "general"
            entry = tracker.log(provider, task, input_tokens=in_tok, output_tokens=out_tok, project=project)
            print(f"  Logged: {entry['provider_name']} | {task} | {in_tok}+{out_tok} tokens | ${entry['cost_usd']:.4f}")
