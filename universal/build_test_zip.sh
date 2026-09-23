#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ZIP_NAME="Alt_Shift_Universal.zip"
PACK_DIR="/tmp/decky-pack-universal"

echo "==> 1. Building Universal Frontend Bundle..."
cd "$SCRIPT_DIR"
pnpm run build

echo "==> 2. Preparing Plugin Package Structure..."
rm -rf "$PACK_DIR"
mkdir -p "$PACK_DIR/Alt_Shift/dist"

cp -v "$SCRIPT_DIR/dist/index.js" "$PACK_DIR/Alt_Shift/dist/"
cp -v "$SCRIPT_DIR/main.py" "$PACK_DIR/Alt_Shift/"
cp -v "$SCRIPT_DIR/plugin.json" "$PACK_DIR/Alt_Shift/"
cp -v "$SCRIPT_DIR/package.json" "$PACK_DIR/Alt_Shift/"
cp -v "$SCRIPT_DIR/LICENSE" "$PACK_DIR/Alt_Shift/"
if [ -f "$SCRIPT_DIR/README.md" ]; then
    cp -v "$SCRIPT_DIR/README.md" "$PACK_DIR/Alt_Shift/"
else
    cp -v "$ROOT_DIR/README.md" "$PACK_DIR/Alt_Shift/"
fi

echo "==> 3. Creating Test ZIP Archive..."
cd "$PACK_DIR"
zip -r "$SCRIPT_DIR/$ZIP_NAME" Alt_Shift

# Copy to root / versions directory for convenience
mkdir -p "$ROOT_DIR/versions/universal"
cp -v "$SCRIPT_DIR/$ZIP_NAME" "$ROOT_DIR/versions/universal/$ZIP_NAME"

echo ""
echo "============================================================"
echo " [SUCCESS] Universal Plugin ZIP built successfully:"
echo " 📦 Location: $SCRIPT_DIR/$ZIP_NAME"
echo " 📦 Backup:   $ROOT_DIR/versions/universal/$ZIP_NAME"
echo "============================================================"
