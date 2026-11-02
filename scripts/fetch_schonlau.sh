#!/usr/bin/env sh
# Fetch the Schonlau et al. (2001) masquerade dataset into data/raw/schonlau/.
# Source mirror: https://github.com/coulls/masquerade (mask.dat, summary.dat)
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/data/raw/schonlau"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$DEST"
git clone --depth 1 --quiet https://github.com/coulls/masquerade "$TMP/masquerade"
cp "$TMP/masquerade/mask.dat" "$TMP/masquerade/summary.dat" "$DEST/"

lines=$(wc -l < "$DEST/mask.dat" | tr -d ' ')
if [ "$lines" != "750000" ]; then
  echo "Unexpected size: mask.dat has $lines lines (expected 750000)" >&2
  exit 1
fi
echo "Schonlau data ready in $DEST"
