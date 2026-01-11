#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env.dev}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to update $ENV_FILE"
  exit 1
fi

python3 - "$ENV_FILE" <<'PY'
import json
import sys
import urllib.request

env_file = sys.argv[1]

try:
    with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=2) as resp:
        data = json.load(resp)
except Exception as exc:
    print(f"Failed to query ngrok API at http://127.0.0.1:4040/api/tunnels: {exc}")
    sys.exit(1)

public_url = None
for t in data.get("tunnels", []):
    url = t.get("public_url", "")
    if url.startswith("https://"):
        public_url = url
        break
if not public_url and data.get("tunnels"):
    public_url = data["tunnels"][0].get("public_url")

if not public_url:
    print("No ngrok tunnels found. Start ngrok first: ngrok http 8443")
    sys.exit(1)

with open(env_file, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

updated = False
for i, line in enumerate(lines):
    if line.startswith("WEBHOOK_URL="):
        lines[i] = f"WEBHOOK_URL={public_url}"
        updated = True
        break

if not updated:
    lines.append(f"WEBHOOK_URL={public_url}")

with open(env_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Updated WEBHOOK_URL in {env_file} -> {public_url}")
PY
