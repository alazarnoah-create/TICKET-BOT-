#!/bin/bash
# Runs ticketbot.py with whichever Python 3 this Mac has. Exits 127 if there isn't one.
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/Current/bin:$PATH"
for py in /Library/Frameworks/Python.framework/Versions/Current/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  [ -x "$py" ] && exec "$py" ticketbot.py "$@"
done
# /usr/bin/python3 is only a placeholder until Apple's Command Line Tools (or Xcode) are installed.
if [ -x /usr/bin/python3 ] && xcode-select -p >/dev/null 2>&1; then
  exec /usr/bin/python3 ticketbot.py "$@"
fi
echo "Python 3 isn't installed. Get it free from https://www.python.org/downloads/macos/" >&2
exit 127
