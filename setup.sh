#!/bin/bash
# One-time setup on your Mac.
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python -m playwright install chromium
[ -f config.json ] || cp config.example.json config.json
echo "Done. Next: edit config.json, then run ./bot login"
