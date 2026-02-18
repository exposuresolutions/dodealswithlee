"""
Build DDWL IVR workflow via GHL API.
GHL AI Builder can't handle IVR workflows, so we use the API directly.
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("GHL_API_KEY")
LOC = os.getenv("GHL_LOCATION_ID")
BASE = "https://services.leadconnectorhq.com"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Version": "2021-07-28",
    "Content-Type": "application/json",
}


def api_get(path, params=None):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params or {})
    return r.status_code, r.json() if r.ok else r.text


def api_post(path, data=None):
    r = requests.post(f"{BASE}{path}", headers=HEADERS, json=data or {})
    return r.status_code, r.json() if r.ok else r.text


# ── Step 1: List existing workflows ──
print("=" * 60)
print("  GHL API — Workflow Explorer")
print("=" * 60)

code, data = api_get("/workflows/", {"locationId": LOC})
print(f"\n  API Status: {code}")

if code == 200:
    wfs = data.get("workflows", [])
    print(f"  Found {len(wfs)} workflows:\n")
    for w in wfs:
        print(f"    [{w['status']:10}] {w['name'][:50]}")
        print(f"              ID: {w['id']}")
else:
    print(f"  Error: {data}")

# ── Step 2: Check existing IVR workflow ──
print("\n" + "-" * 60)
print("  Checking existing IVR workflows...")

ivr_wf = None
for w in wfs:
    if "ivr" in w["name"].lower() or "phone" in w["name"].lower():
        print(f"\n  Found: {w['name']} ({w['status']})")
        print(f"  ID: {w['id']}")
        ivr_wf = w
        break

# ── Step 3: Try to get workflow details ──
if ivr_wf:
    print(f"\n  Getting workflow details for: {ivr_wf['name']}...")
    code2, detail = api_get(f"/workflows/{ivr_wf['id']}", {"locationId": LOC})
    print(f"  Detail API Status: {code2}")
    if code2 == 200:
        print(f"  Detail: {json.dumps(detail, indent=2)[:2000]}")
    else:
        print(f"  Detail Error: {detail}")

# ── Step 4: Check what API endpoints exist ──
print("\n" + "-" * 60)
print("  Testing API endpoints...")

endpoints = [
    ("/workflows/", "GET", {"locationId": LOC}),
    ("/phone-number/", "GET", {"locationId": LOC}),
    ("/phone-number/lookup", "GET", {"locationId": LOC, "phone": "+18136750916"}),
    ("/users/", "GET", {"locationId": LOC}),
    ("/locations/" + LOC, "GET", {}),
]

for path, method, params in endpoints:
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params)
        print(f"  {method} {path:40} → {r.status_code} ({len(r.text)} bytes)")
        if r.ok and len(r.text) < 500:
            print(f"    {r.text[:200]}")
    except Exception as e:
        print(f"  {method} {path:40} → ERROR: {e}")

# ── Step 5: List users (for call routing) ──
print("\n" + "-" * 60)
print("  Listing users (for call routing)...")

code, users_data = api_get("/users/", {"locationId": LOC})
if code == 200:
    users = users_data.get("users", [])
    print(f"  Found {len(users)} users:")
    for u in users:
        name = u.get("name", u.get("firstName", "") + " " + u.get("lastName", ""))
        email = u.get("email", "")
        uid = u.get("id", "")
        ext = u.get("extension", "")
        print(f"    {name:30} ext={ext:5} email={email:40} id={uid}")
else:
    print(f"  Users Error: {users_data}")

print("\n" + "=" * 60)
print("  Done.")
print("=" * 60)
