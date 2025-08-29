#!/usr/bin/env bash
set -euo pipefail
payload="$(cat)"
file="$(python3 - <<'PY'\nimport sys,json;d=json.load(sys.stdin);print((d.get('tool_input') or {}).get('file_path',''))\nPY\n <<< "$payload")"
[[ -z "$file" ]] && exit 0
case "$file" in
  *.py) command -v ruff >/dev/null && ruff check --fix "$file" || true
        command -v black >/dev/null && black -q "$file" || true ;;
  *.ts|*.tsx) if command -v pnpm >/dev/null; then pnpm -s format --if-present || true; fi ;;
esac
