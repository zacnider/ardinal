#!/usr/bin/env bash
# Ardinals araçlarını bu klasörün içine kurar (ev dizinine yazmaz).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

mkdir -p bin run-home

pick_asset() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"
  case "$os:$arch" in
    Darwin:arm64) echo "ardi-agent-darwin-aarch64" ;;
    Darwin:x86_64) echo "ardi-agent-darwin-x86_64" ;;
    Linux:aarch64|Linux:arm64) echo "ardi-agent-linux-aarch64" ;;
    Linux:x86_64) echo "ardi-agent-linux-x86_64-musl" ;;
    *) echo "unsupported OS/ARCH: $os $arch" >&2; exit 1 ;;
  esac
}

fetch_latest_ardi() {
  local json tag asset url
  json="$(curl -fsSL "https://api.github.com/repos/awp-worknet/ardi-skill/releases/latest")"
  tag="$(printf '%s' "$json" | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])")"
  asset="$(pick_asset)"
  url="https://github.com/awp-worknet/ardi-skill/releases/download/${tag}/${asset}"
  echo "Downloading ${url} ..."
  curl -fL --retry 3 --retry-delay 1 -o bin/ardi-agent.new "$url"
  chmod +x bin/ardi-agent.new
  mv bin/ardi-agent.new bin/ardi-agent
  echo "Installed bin/ardi-agent (${tag})"
}

if [[ ! -x bin/ardi-agent ]]; then
  fetch_latest_ardi
else
  echo "bin/ardi-agent already present — skip download (delete file to re-fetch)"
fi

if [[ ! -d awp-wallet/.git ]]; then
  rm -rf awp-wallet
  echo "Cloning awp-wallet ..."
  git clone --depth 1 https://github.com/awp-core/awp-wallet.git awp-wallet
fi

echo "npm install (awp-wallet) ..."
(cd awp-wallet && npm install --no-audit --no-fund >/dev/null)
chmod +x awp-wallet/scripts/wallet-cli.js

export HOME="$ROOT/run-home"
export AWP_WALLET_BIN="$ROOT/awp-wallet/scripts/wallet-cli.js"
echo "Wallet home: $HOME/.openclaw-wallet (sadece bu proje klasörü altında)"
node "$AWP_WALLET_BIN" setup

echo
echo "Tamam. Örnek:"
echo "  cd \"$ROOT\" && ./ardi preflight"
