#!/usr/bin/env bash
set -euo pipefail

APP_NAME="NotionOverlay"
BUNDLE_ID="com.zhouhuaifeng.notion-overlay"
ICON_SOURCE="${1:-}"
SYSTEM_GENERIC_ICON="/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"
BUILD_DIR="$SCRIPT_DIR/.build/release"
APP_DIR="$DIST_DIR/$APP_NAME.app"
INSTALL_DIR="/Applications/$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RES_DIR="$CONTENTS_DIR/Resources"
ICONSET_DIR="$DIST_DIR/$APP_NAME.iconset"
ICON_ICNS="$RES_DIR/$APP_NAME.icns"

if [[ -n "$ICON_SOURCE" && ! -f "$ICON_SOURCE" ]]; then
  echo "Icon source not found: $ICON_SOURCE" >&2
  exit 1
fi

echo "[1/5] Build release binary..."
cd "$SCRIPT_DIR"
CLANG_MODULE_CACHE_PATH=/tmp/clang-module-cache swift build -c release

echo "[2/5] Prepare app bundle..."
rm -rf "$APP_DIR"
mkdir -p "$MACOS_DIR" "$RES_DIR"

cp "$BUILD_DIR/NotionOverlayApp" "$MACOS_DIR/$APP_NAME"
chmod +x "$MACOS_DIR/$APP_NAME"

if [[ -n "$ICON_SOURCE" ]]; then
  echo "[3/5] Generate app icon (.icns)..."
  rm -rf "$ICONSET_DIR"
  mkdir -p "$ICONSET_DIR"

  gen_icon() {
    local size="$1"
    local out="$2"
    sips -s format png -z "$size" "$size" "$ICON_SOURCE" --out "$out" >/dev/null
  }

  gen_icon 16 "$ICONSET_DIR/icon_16x16.png"
  gen_icon 32 "$ICONSET_DIR/icon_16x16@2x.png"
  gen_icon 32 "$ICONSET_DIR/icon_32x32.png"
  gen_icon 64 "$ICONSET_DIR/icon_32x32@2x.png"
  gen_icon 128 "$ICONSET_DIR/icon_128x128.png"
  gen_icon 256 "$ICONSET_DIR/icon_128x128@2x.png"
  gen_icon 256 "$ICONSET_DIR/icon_256x256.png"
  gen_icon 512 "$ICONSET_DIR/icon_256x256@2x.png"
  gen_icon 512 "$ICONSET_DIR/icon_512x512.png"
  gen_icon 1024 "$ICONSET_DIR/icon_512x512@2x.png"

  iconutil -c icns "$ICONSET_DIR" -o "$ICON_ICNS"
  rm -rf "$ICONSET_DIR"
else
  echo "[3/5] Use system generic app icon..."
  cp "$SYSTEM_GENERIC_ICON" "$ICON_ICNS"
fi

echo "[4/5] Write Info.plist..."
BUILD_VERSION="$(date +%s)"
ICON_PLIST='    <key>CFBundleIconFile</key>
    <string>'"$APP_NAME"'</string>'
cat > "$CONTENTS_DIR/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
$ICON_PLIST
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>$BUILD_VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRemindersUsageDescription</key>
    <string>用于读取 macOS 提醒事项并展示到悬浮日报窗口。</string>
</dict>
</plist>
EOF

echo "[5/5] Install app to /Applications..."
rm -rf "$INSTALL_DIR"
cp -R "$APP_DIR" "$INSTALL_DIR"

echo
echo "Done."
echo "App bundle: $APP_DIR"
echo "Installed app: $INSTALL_DIR"
