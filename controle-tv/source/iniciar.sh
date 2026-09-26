#!/usr/bin/env bash
# Abre o PVN Controle TV. No Termux sobe um servidor local, porque o navegador
# do Android nao le arquivos da pasta privada do Termux.
#   bash iniciar.sh              abre no navegador
#   bash iniciar.sh --servidor   forca o servidor local (http://localhost)
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VER="$(cat "$DIR/VERSION" 2>/dev/null || echo dev)"
echo "PVN Controle TV $VER"

free_port() {
  for p in $(seq "${PORT:-8080}" 8099); do
    python3 -c "import socket,sys; s=socket.socket(); s.bind(('127.0.0.1',$p))" 2>/dev/null && { echo "$p"; return; }
  done
  return 1
}

serve() {
  command -v python3 >/dev/null 2>&1 || { echo "Python nao encontrado. Termux: pkg install python"; exit 1; }
  local port; port="$(free_port)" || { echo "Nenhuma porta livre entre 8080 e 8099"; exit 1; }
  local url="http://localhost:$port/index.html"
  echo "Servidor em $url  (Ctrl+C encerra)"
  if [ -n "${1:-}" ]; then (sleep 1; "$1" "$url" >/dev/null 2>&1 || true) & fi
  exec python3 -m http.server "$port" --bind 127.0.0.1 --directory "$DIR"
}

opener=""
command -v xdg-open >/dev/null 2>&1 && opener=xdg-open
command -v open >/dev/null 2>&1 && [ -z "$opener" ] && opener=open

if [ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux/files ]; then
  command -v termux-open-url >/dev/null 2>&1 && serve termux-open-url || serve ""
elif [ "${1:-}" = "--servidor" ]; then
  serve "$opener"
elif [ -n "$opener" ]; then
  "$opener" "$DIR/index.html"
else
  echo "Abra no navegador: $DIR/index.html"
fi
