#!/usr/bin/env bash
# Builds WebTransportAddIn with macOS support
# Clones alkoleft/web-transport-addin, compiles dylib for x86_64-apple-darwin,
# and adds it to the existing Template.addin archive.
#
# Prerequisites:
#   - Rust toolchain (cargo, rustc)
#   - x86_64-apple-darwin target: rustup target add x86_64-apple-darwin
#
# Usage:
#   ./scripts/build-macos-addin.sh

set -euo pipefail

REPO="alkoleft/web-transport-addin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${SCRIPT_DIR}/../exts/client-mcp/src/CommonTemplates/$(ls "${SCRIPT_DIR}/../exts/client-mcp/src/CommonTemplates/" | grep -i webTransport)/Template.addin"

echo "=== Building macOS dylib for WebTransportAddIn ==="

# Check prerequisites
if ! command -v cargo &> /dev/null; then
  echo "ERROR: cargo not found. Install Rust: https://rustup.rs/" >&2
  exit 1
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Clone and build
echo "Cloning ${REPO}..."
git clone --depth 1 "https://github.com/${REPO}.git" "${TMP}/src" 2>&1 | tail -1

echo "Building for x86_64-apple-darwin..."
cd "${TMP}/src"
cargo build --release --target x86_64-apple-darwin 2>&1 | tail -3

DYLIB="${TMP}/src/target/x86_64-apple-darwin/release/libwebtransport.dylib"
if [ ! -f "$DYLIB" ]; then
  echo "ERROR: dylib not found at ${DYLIB}" >&2
  exit 1
fi

echo "Built: $(file "$DYLIB")"

# Extract existing addin, add dylib, update manifest
echo "Updating Template.addin..."
mkdir -p "${TMP}/addin"
unzip -o "$TARGET" -d "${TMP}/addin" > /dev/null

cp "$DYLIB" "${TMP}/addin/WebTransportAddIn_x64.dylib"

# Update Manifest.xml to include macOS
if ! grep -q "MacOS" "${TMP}/addin/Manifest.xml"; then
  sed -i '' '/<\/bundle>/i\
    <component os="MacOS" path="WebTransportAddIn_x64.dylib" type="native" arch="x86_64" />' "${TMP}/addin/Manifest.xml"
fi

# Repack
cd "${TMP}/addin"
zip -9 "${TMP}/new-addin.zip" * > /dev/null
cp "${TMP}/new-addin.zip" "$TARGET"

echo "=== Done ==="
echo "Updated: $TARGET"
unzip -l "$TARGET" | grep -E "dylib|Manifest"
