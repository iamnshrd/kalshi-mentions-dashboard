#!/usr/bin/env bash
set -euo pipefail

SRC="/root/.openclaw/workspace/kalshi_mentions_monitor/output/dashboard"
DST="/root/.openclaw/workspace/.deploy/kalshi-mentions-dashboard"
REPO_URL="https://github.com/iamnshrd/kalshi-mentions-dashboard.git"
TOKEN="${GITHUB_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "Missing GITHUB_TOKEN" >&2
  exit 2
fi

mkdir -p "$(dirname "$DST")"
if [ ! -d "$DST/.git" ]; then
  git clone "$REPO_URL" "$DST"
fi

cd "$DST"
git remote remove origin >/dev/null 2>&1 || true
git remote add origin "https://x-access-token:${TOKEN}@github.com/iamnshrd/kalshi-mentions-dashboard.git"
git fetch origin main || true
git checkout -B main

find "$DST" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R "$SRC"/. "$DST"/

git add .
if git diff --cached --quiet; then
  echo "NO_CHANGES"
  python3 - <<'PY'
from pathlib import Path
p=Path('.git/config')
text=p.read_text()
text=text.replace('https://x-access-token:${TOKEN}@github.com/iamnshrd/kalshi-mentions-dashboard.git','https://github.com/iamnshrd/kalshi-mentions-dashboard.git')
p.write_text(text)
PY
  exit 0
fi

git config user.name "OpenClaw"
git config user.email "openclaw@local"
git commit -m "Deploy dashboard"
git push -u origin main
python3 - <<PY
from pathlib import Path
p=Path('.git/config')
text=p.read_text()
text=text.replace('https://x-access-token:${TOKEN}@github.com/iamnshrd/kalshi-mentions-dashboard.git','https://github.com/iamnshrd/kalshi-mentions-dashboard.git')
p.write_text(text)
print('REMOTE_SANITIZED')
PY
