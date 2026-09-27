#!/usr/bin/env bash
# Instalador do Teclado Termux (comando teclas): barras de teclas do Termux
# para o dia a dia, o jogo e a TV, com volta à sua barra de antes.
#
#   bash instalar.sh                       instala a partir desta pasta
#   curl -fsSL <url>/instalar.sh | bash    instala baixando do GitHub
#
# Opcoes: --melhorado       usa o padrão melhorado no dia a dia, sem perguntar
#         --sem-melhorado   não troca a barra agora
#         --remover         desinstala e devolve a barra que você tinha
set -euo pipefail

REPO_RAW="${TECLAS_REPO_RAW:-https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/teclado-termux/source}"
APP_DIR="${TECLAS_HOME:-$HOME/.local/share/teclado-termux}"

if [ -t 1 ]; then
  B=$'\e[1m'; D=$'\e[2m'; G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; C=$'\e[36m'; N=$'\e[0m'
else
  B=""; D=""; G=""; Y=""; R=""; C=""; N=""
fi
step() { printf '%s==>%s %s%s%s\n' "$C" "$N" "$B" "$*" "$N"; }
ok()   { printf '    %s✔%s %s\n' "$G" "$N" "$*"; }
warn() { printf '    %s!%s %s\n' "$Y" "$N" "$*"; }
short() { local t="~"; printf '%s' "${1/#$HOME/$t}"; }
die()  { printf '    %s✘ %s%s\n' "$R" "$*" "$N" >&2; exit 1; }
fetch() { if command -v curl >/dev/null 2>&1; then curl -fsSL "$1" -o "$2"; else wget -qO "$2" "$1"; fi; }

is_termux() { [ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux/files ]; }
if is_termux; then BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"; else BIN_DIR="$HOME/.local/bin"; fi

ask() {
  # funciona mesmo com "curl | bash": lê do terminal; sem terminal (testes), responde não
  local answer=""
  if (exec </dev/tty) 2>/dev/null; then
    printf '    %s%s%s [s/N] ' "$B" "$1" "$N"
    read -r answer </dev/tty || answer=""
  fi
  [[ "$answer" =~ ^[sSyY] ]]
}

MODE="ask"; ACTION="install"
for arg in "$@"; do
  case "$arg" in
    --melhorado) MODE="yes" ;;
    --sem-melhorado) MODE="no" ;;
    --remover|--desinstalar) ACTION="remove" ;;
    -h|--ajuda) sed -n '2,11p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "opcao desconhecida: $arg" ;;
  esac
done
SELF="${BASH_SOURCE[0]:-}"
SRC=""
[ -n "$SELF" ] && [ -f "$SELF" ] && [ -f "$(dirname "$SELF")/teclas.py" ] && SRC="$(cd "$(dirname "$SELF")" && pwd)"

is_ours() { [ -f "$1" ] && grep -q "$APP_DIR/teclas.py" "$1"; }

if [ "$ACTION" = "remove" ]; then
  step "Removendo o Teclado Termux"
  if [ -f "$APP_DIR/teclas.py" ] && command -v python3 >/dev/null 2>&1; then
    python3 "$APP_DIR/teclas.py" --remover >/dev/null && ok "a sua barra de teclas de antes voltou"
  fi
  if is_ours "$BIN_DIR/teclas"; then rm -f "$BIN_DIR/teclas"; ok "comando teclas removido"; fi
  rm -rf "$APP_DIR" && ok "arquivos removidos"
  printf '\n%sPronto. Teclado Termux desinstalado.%s\n' "$G" "$N"
  exit 0
fi

printf '\n%s  ╭──────────────────────────────────╮%s\n' "$Y" "$N"
printf '%s  │%s  ⌨  %sTECLADO TERMUX%s · instalador  %s│%s\n' "$Y" "$N" "$B" "$N" "$Y" "$N"
printf '%s  ╰──────────────────────────────────╯%s\n' "$Y" "$N"
printf '%s  %s%s\n\n' "$D" "$(is_termux && echo "Termux detectado" || echo "Linux detectado")" "$N"

step "1/3  Python"
if ! command -v python3 >/dev/null 2>&1; then
  if is_termux; then
    warn "Python nao encontrado, instalando (pode levar 1-2 minutos)..."
    pkg install -y python </dev/null >/dev/null 2>&1 || die "falhou 'pkg install python'. Rode 'pkg update' e tente de novo."
  else
    die "instale o Python 3 (ex.: sudo apt install python3) e rode de novo"
  fi
fi
python3 -c 'import sys; sys.exit(sys.version_info < (3, 7))' || die "Python 3.7 ou mais novo e necessario"
ok "$(python3 --version)"

step "2/3  Arquivos e comando teclas"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
if [ -n "$SRC" ]; then
  cp "$SRC/teclas.py" "$SRC/VERSION" "$SRC/instalar.sh" "$TMP/"
  ok "copiando da pasta ${D}$(short "$SRC")${N}"
else
  for f in teclas.py VERSION instalar.sh; do
    fetch "$REPO_RAW/$f" "$TMP/$f" || die "nao consegui baixar $f (sem internet?)"
  done
  ok "baixado do GitHub"
fi
python3 -m py_compile "$TMP/teclas.py" 2>/dev/null || die "teclas.py corrompido ou incompleto"
rm -rf "$TMP/__pycache__"
mkdir -p "$APP_DIR" "$BIN_DIR"
cp "$TMP/teclas.py" "$TMP/VERSION" "$TMP/instalar.sh" "$APP_DIR/"
VERSION="$(cat "$APP_DIR/VERSION")"
ok "versao $VERSION em ${D}$(short "$APP_DIR")${N}"
if [ -e "$BIN_DIR/teclas" ] && ! is_ours "$BIN_DIR/teclas"; then
  die "'teclas' ja existe em $BIN_DIR e nao e deste instalador"
fi
printf '#!/usr/bin/env sh\nexec python3 "%s/teclas.py" "$@"\n' "$APP_DIR" > "$BIN_DIR/teclas"
chmod +x "$BIN_DIR/teclas"
ok "comando: ${B}teclas${N}"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) warn "$BIN_DIR nao esta no PATH. Adicione ao ~/.bashrc: export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

step "3/3  Barra de teclas do Termux"
if ! is_termux; then
  ok "nao se aplica fora do Termux"
else
  now="$(python3 "$APP_DIR/teclas.py" --estado | sed -n 's/^barra: //p')"
  if [ "$now" = "Padrão melhorado" ]; then
    ok "barra: Padrão melhorado"
  else
    [ "$now" = "Jogo (fixada pelo td 3.1)" ] && warn "a barra do jogo estava fixa; agora ela entra só quando o td abre"
    if [ "$MODE" = "yes" ] || { [ "$MODE" = "ask" ] && ask "Usar o padrão melhorado no dia a dia (volta com: teclas original)?"; }; then
      python3 "$APP_DIR/teclas.py" melhorado >/dev/null
      ok "barra: Padrão melhorado; o Termux recarregou"
    else
      ok "barra mantida: ${now:-Padrão do Termux}"
    fi
  fi
  ok "troca automática: o tv e o td põem a barra deles ao abrir"
fi

printf '\n%s  ✔ Teclado Termux %s instalado%s\n\n' "$G$B" "$VERSION" "$N"
printf '  Para escolher a barra, digite:  %steclas%s\n' "$B" "$N"
printf '  %sDireto: teclas melhorado | jogo | tv | padrao | original%s\n' "$D" "$N"
printf '  %sDesinstalar: bash %s/instalar.sh --remover%s\n\n' "$D" "$(short "$APP_DIR")" "$N"
