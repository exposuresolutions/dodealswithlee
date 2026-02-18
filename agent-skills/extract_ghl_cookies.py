"""Extract GHL session cookies from Chrome Profile 4 and save for Playwright."""
import sqlite3
import os
import json
import shutil

chrome_profile = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Profile 4")
cookies_db = os.path.join(chrome_profile, "Cookies")
temp_db = os.path.join(os.environ["TEMP"], "ghl_cookies.db")
output_file = os.path.join(os.path.dirname(__file__), "ghl_cookies.json")

# Copy cookies DB (locked by Chrome)
shutil.copy2(cookies_db, temp_db)

conn = sqlite3.connect(temp_db)
cursor = conn.cursor()

# Get GHL-related cookies
cursor.execute(
    "SELECT name, value, host_key, path, is_secure, is_httponly, expires_utc "
    "FROM cookies "
    "WHERE host_key LIKE '%gohighlevel%' OR host_key LIKE '%leadconnector%' "
    "ORDER BY host_key"
)

rows = cursor.fetchall()
print(f"Found {len(rows)} GHL cookies")

cookies = []
for name, value, host, path, secure, httponly, expires in rows:
    # Chrome stores encrypted cookies on Windows - value may be empty
    if not value:
        continue
    domain = host.lstrip(".")
    cookies.append({
        "name": name,
        "value": value,
        "domain": domain,
        "path": path,
        "secure": bool(secure),
        "httpOnly": bool(httponly),
    })
    print(f"  {host}: {name} = {value[:40]}..." if len(value) > 40 else f"  {host}: {name} = {value}")

conn.close()
os.remove(temp_db)

if cookies:
    with open(output_file, "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"\nSaved {len(cookies)} cookies to {output_file}")
else:
    print("\nNo unencrypted cookies found. Chrome encrypts cookies on Windows.")
    print("Alternative: Will use Playwright persistent context with manual login.")
