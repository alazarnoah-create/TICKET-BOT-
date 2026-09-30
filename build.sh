#!/bin/bash
# Builds "Ticket Bot.app" and TicketBot.dmg on a Mac, using only tools every Mac has.
# An app built on your own Mac opens straight away, with no "Not Opened" warning.
#   bash build.sh            -> build/Ticket Bot.app and build/TicketBot.dmg
#   bash build.sh --no-dmg   -> just the app
set -e
cd "$(dirname "$0")"

APP="build/Ticket Bot.app"
RES="$APP/Contents/Resources"
PLIST="$APP/Contents/Info.plist"

echo "==> Building $APP"
rm -rf build
mkdir -p build
osacompile -o "$APP" mac/TicketBot.applescript

mkdir -p "$RES/bot"
cp ticketbot.py safari_step.js config.example.json mac/run.sh "$RES/bot/"
chmod +x "$RES/bot/run.sh"

echo "==> Adding the icon"
ICONSET="build/AppIcon.iconset"
mkdir -p "$ICONSET"
for size in 16 32 128 256 512; do
  sips -z $size $size mac/icon.png --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  sips -z $((size * 2)) $((size * 2)) mac/icon.png --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$RES/applet.icns"
rm -rf "$ICONSET"
rm -f "$RES/Assets.car"  # newer macOS applets carry the default icon here too
plutil -remove CFBundleIconName "$PLIST" 2>/dev/null || true
plutil -replace CFBundleIconFile -string applet "$PLIST"

plutil -replace CFBundleIdentifier -string com.alazarnoah.ticketbot "$PLIST"
plutil -replace CFBundleName -string "Ticket Bot" "$PLIST"
plutil -replace CFBundleShortVersionString -string "1.0" "$PLIST"

echo "==> Signing (ad-hoc)"
xattr -cr "$APP" 2>/dev/null || true
codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict "$APP"

if [ "$1" != "--no-dmg" ]; then
  echo "==> Building build/TicketBot.dmg"
  STAGING="build/dmg"
  mkdir -p "$STAGING"
  cp -R "$APP" "$STAGING/"
  ln -s /Applications "$STAGING/Applications"
  cp mac/README.txt "$STAGING/READ ME FIRST.txt"
  hdiutil create -volname "Ticket Bot" -srcfolder "$STAGING" -ov -format UDZO build/TicketBot.dmg >/dev/null
  rm -rf "$STAGING"
fi

echo "Done: $APP"
