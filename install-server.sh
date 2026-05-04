#!/usr/bin/env bash
# Ubuntu (veya Debian) sunucuda: apt bağımlılıkları + Node 20 + certifi + setup-local.sh
# Kullanım: proje kökünde  bash install-server.sh
# root veya sudo yetkili normal kullanıcı ile çalıştır.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ${1:-} == "--help" ]] || [[ ${1:-} == "-h" ]]; then
  echo "Usage: cd /path/to/ardinal && bash install-server.sh"
  echo "Installs: git curl ca-certificates python3 pip, Node.js 20+, certifi, then setup-local.sh"
  echo "Env: INSTALL_SERVER_APT_IPV4=0 — apt için IPv4 zorlamasını yazma (varsayılan: 1, kırık IPv6 VPS için)"
  exit 0
fi

SUDO=""
if [[ "$(id -u)" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    echo "Root veya sudo gerekli (apt kurulumu için)." >&2
    exit 1
  fi
fi

# Birçok VPS'te IPv6 dışarı çıkmaz; apt archive.ubuntu.com'a IPv6 ile gidince "Network is unreachable" olur.
APT_FORCE_IPV4="/etc/apt/apt.conf.d/99ardinal-apt-ipv4"
if [[ "${INSTALL_SERVER_APT_IPV4:-1}" != "0" ]]; then
  echo "==> apt: IPv4 zorlama (kırık IPv6 için; kapatmak: INSTALL_SERVER_APT_IPV4=0)"
  echo 'Acquire::ForceIPv4 "true";' | $SUDO tee "$APT_FORCE_IPV4" >/dev/null
fi

echo "==> apt: temel paketler"
$SUDO apt-get update -qq
$SUDO apt-get install -y \
  git \
  curl \
  ca-certificates \
  python3 \
  python3-pip \
  python3-venv \
  >/dev/null

echo "==> Node.js (awp-wallet için 20.x)"
need_nodesource=1
if command -v node >/dev/null 2>&1; then
  maj=$(node -p 'parseInt(process.versions.node.split(".")[0],10)' 2>/dev/null || echo 0)
  if [[ "$maj" -ge 18 ]]; then
    need_nodesource=0
  fi
fi
if [[ "$need_nodesource" -eq 1 ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | $SUDO -E bash -
  $SUDO apt-get install -y nodejs >/dev/null
fi
command -v node >/dev/null
command -v npm >/dev/null
echo "    $(node -v) / $(npm -v)"

echo "==> Python: certifi (OpenRouter TLS; isteğe bağlı ama önerilir)"
if python3 -m pip install --user certifi >/dev/null 2>&1; then
  :
elif python3 -m pip install --user --break-system-packages certifi >/dev/null 2>&1; then
  :
else
  echo "    Uyarı: certifi kurulamadı; gerekirse: python3 -m venv .venv && . .venv/bin/activate && pip install certifi" >&2
fi

echo "==> Proje scriptleri çalıştırılabilir"
chmod +x "$ROOT/ardi" "$ROOT/setup-local.sh" 2>/dev/null || true
chmod +x "$ROOT/install-server.sh" 2>/dev/null || true

if [[ ! -f "$ROOT/setup-local.sh" ]]; then
  echo "Eksik: $ROOT/setup-local.sh — repoyu tam kopyala veya git clone yap." >&2
  exit 1
fi

echo "==> setup-local.sh (ardi-agent + awp-wallet)"
bash "$ROOT/setup-local.sh"

echo
echo "Kurulum bitti."
echo "  cd \"$ROOT\" && ./ardi preflight"
echo "  .env oluştur; sonra: python3 openrouter_mine.py --auto-chain"
