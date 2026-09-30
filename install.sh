#!/bin/bash
# Installs Ticket Bot on this Mac. Paste into Terminal:
#   curl -fsSL https://raw.githubusercontent.com/alazarnoah-create/TICKET-BOT-/HEAD/install.sh | bash
# Downloading with curl and building here means macOS doesn't show the "Not Opened" warning.
set -e
REF="${TICKETBOT_REF:-HEAD}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading Ticket Bot..."
curl -fsSL "https://codeload.github.com/alazarnoah-create/TICKET-BOT-/tar.gz/$REF" | tar -xz -C "$TMP" --strip-components 1
bash "$TMP/build.sh" --no-dmg

DEST=/Applications
[ -w "$DEST" ] || DEST="$HOME/Applications"
mkdir -p "$DEST"
rm -rf "$DEST/Ticket Bot.app"
ditto "$TMP/build/Ticket Bot.app" "$DEST/Ticket Bot.app"
echo "Installed: $DEST/Ticket Bot.app - opening it now."
open "$DEST/Ticket Bot.app"
