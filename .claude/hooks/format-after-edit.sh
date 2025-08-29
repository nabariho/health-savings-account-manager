#!/usr/bin/env bash
set -euo pipefail

# Read hook input (JSON) from stdin; extract file path if present
payload="$(cat)"
file="$(printf '%s' "$payload" | /usr/bin/python3 -c 'import sys, json; d=json.load(sys.stdin); print((d.get("tool_input") or {}).get("file_path",""))')"

# Run formatters conditionally
if [[ -n "$file" && "$file" == *.py ]]; then
  command -v ruff >/dev/null 2>&1 && ruff check --fix "$file" || true
  command -v black >/dev/null 2>&1 && black -q "$file" || true
elif [[ -n "$file" && "$file" =~ \.tsx?$ ]]; then
  if command -v npm >/dev/null 2>&1; then
    npm run -s lint --if-present || true
    npm run -s format --if-present || true
  fi
fi
