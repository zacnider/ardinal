#!/usr/bin/env bash
# Private key / mnemonic — SADECE kendi makinenizde çalıştırın; çıktıyı kimseyle paylaşmayın.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export HOME="$ROOT/run-home"
CLI="$ROOT/awp-wallet/scripts/wallet-cli.js"
if [[ ! -f "$CLI" ]]; then
  echo "awp-wallet yok. Önce: bash \"$ROOT/setup-local.sh\"" >&2
  exit 1
fi
echo "=== export-private-key ===" >&2
node "$CLI" export-private-key
echo "=== export (mnemonic) ===" >&2
node "$CLI" export
