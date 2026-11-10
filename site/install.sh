#!/usr/bin/env bash
set -e

echo "⚡ Installing TokenRelay — Universal AI Cost Savings Agent..."

INSTALL_DIR="$HOME/.tokenrelay"
mkdir -p "$INSTALL_DIR"

ZIP_URL="https://github.com/qanvass/tokenrelay/archive/refs/heads/master.zip"
TMP_ZIP="/tmp/tokenrelay.zip"
TMP_DIR="/tmp/tokenrelay_extract"

echo "Downloading latest TokenRelay release from GitHub..."
curl -fsSL "$ZIP_URL" -o "$TMP_ZIP"

echo "Extracting..."
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
unzip -q "$TMP_ZIP" -d "$TMP_DIR"
cp -R "$TMP_DIR/tokenrelay-master/"* "$INSTALL_DIR/"
rm -rf "$TMP_DIR" "$TMP_ZIP"

echo "Configuring Claude Desktop MCP..."
if command -v python3 &>/dev/null; then
    python3 "$INSTALL_DIR/agent.py" mcp || true
fi

echo "✅ TokenRelay installed successfully to $INSTALL_DIR"
echo "To launch your Control Center: python3 $INSTALL_DIR/agent.py dashboard"
