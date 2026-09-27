#!/usr/bin/env bash
# Instalador do PVN Controle TV (controle infravermelho pelo Termux).
#
#   bash instalar.sh                       instala a partir desta pasta
#   curl -fsSL <url>/instalar.sh | bash    instala baixando do GitHub
#
# Opcoes: --atalhos (cria atalhos do Termux:Widget sem perguntar)
#         --sem-atalhos
#         --remover (desinstala)
set -euo pipefail

REPO_RAW="${TV_REPO_RAW:-https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/controle-tv/source}"
APP_DIR="${TV_HOME:-$HOME/.local/share/pvn-controle-tv}"
SHORTCUTS_DIR="$HOME/.shortcuts"

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

is_termux() { [ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux/files ]; }
if is_termux; then BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"; else BIN_DIR="$HOME/.local/bin"; fi

ask() {
  local answer=""
  # /dev/tty pode existir sem abrir (sem terminal de controle): testa abrindo de verdade
  if (exec </dev/tty) 2>/dev/null; then
    printf '    %s%s%s [s/N] ' "$B" "$1" "$N"
    read -r answer </dev/tty || answer=""
  fi
  [[ "$answer" =~ ^[sSyY] ]]
}

SHORTCUTS_MODE="ask"; ACTION="install"
for arg in "$@"; do
  case "$arg" in
    --atalhos) SHORTCUTS_MODE="yes" ;;
    --sem-atalhos) SHORTCUTS_MODE="no" ;;
    --remover|--desinstalar) ACTION="remove" ;;
    -h|--ajuda) sed -n '2,10p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "opcao desconhecida: $arg" ;;
  esac
done

is_ours() { [ -f "$1" ] && grep -q "$APP_DIR/tv.py" "$1"; }

if [ "$ACTION" = "remove" ]; then
  step "Removendo o PVN Controle TV"
  if is_ours "$BIN_DIR/tv"; then rm -f "$BIN_DIR/tv"; ok "comando tv removido"; fi
  for f in "$SHORTCUTS_DIR"/TV\ *; do
    [ -f "$f" ] && grep -q "exec tv " "$f" && rm -f "$f"
  done
  ok "atalhos removidos"
  rm -rf "$APP_DIR" && ok "arquivos removidos"
  printf '    %sA TV escolhida e os perfis importados continuam em ~/.config/pvn-tv%s\n' "$D" "$N"
  printf '\n%sPronto. PVN Controle TV desinstalado.%s\n' "$G" "$N"
  exit 0
fi

printf '\n%s  PVN CONTROLE TV · instalador%s\n' "$B" "$N"
printf '%s  %s%s\n\n' "$D" "$(is_termux && echo "Termux detectado" || echo "Linux detectado (sem emissor IR: use tv --simular)")" "$N"

step "1/5  Python"
if ! command -v python3 >/dev/null 2>&1; then
  is_termux || die "instale o Python 3 e rode de novo"
  warn "Python nao encontrado, instalando (pode levar 1-2 minutos)..."
  pkg install -y python </dev/null >/dev/null 2>&1 || die "falhou 'pkg install python'. Rode 'pkg update' e tente de novo."
fi
python3 -c 'import sys; sys.exit(sys.version_info < (3, 7))' || die "Python 3.7 ou mais novo e necessario"
python3 -c 'import curses' 2>/dev/null || die "modulo curses indisponivel neste Python"
ok "$(python3 --version) com curses"

step "2/5  Termux:API (acesso ao infravermelho)"
if is_termux; then
  if ! command -v termux-infrared-transmit >/dev/null 2>&1; then
    warn "instalando o pacote termux-api..."
    pkg install -y termux-api </dev/null >/dev/null 2>&1 || die "falhou 'pkg install termux-api'. Rode 'pkg update' e tente de novo."
  fi
  ok "pacote termux-api instalado"
else
  ok "nao se aplica fora do Termux"
fi

step "3/5  Arquivos do controle"
SELF="${BASH_SOURCE[0]:-}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
if [ -n "$SELF" ] && [ -f "$SELF" ] && [ -f "$(dirname "$SELF")/tv.py" ]; then
  SRC="$(cd "$(dirname "$SELF")" && pwd)"
  cp "$SRC/tv.py" "$SRC/VERSION" "$SRC/instalar.sh" "$TMP/"
  ok "copiando da pasta ${D}$(short "$SRC")${N}"
else
  fetch() { if command -v curl >/dev/null 2>&1; then curl -fsSL "$1" -o "$2"; else wget -qO "$2" "$1"; fi; }
  for f in tv.py VERSION instalar.sh; do
    fetch "$REPO_RAW/$f" "$TMP/$f" || die "nao consegui baixar $f (sem internet?)"
  done
  ok "baixado do GitHub"
fi
python3 -m py_compile "$TMP/tv.py" 2>/dev/null || die "tv.py corrompido ou incompleto"
rm -rf "$TMP/__pycache__"
mkdir -p "$APP_DIR"
cp "$TMP/tv.py" "$TMP/VERSION" "$TMP/instalar.sh" "$APP_DIR/"
VERSION="$(cat "$APP_DIR/VERSION")"
ok "versao $VERSION em ${D}$(short "$APP_DIR")${N}"

mkdir -p "$BIN_DIR"
if [ -e "$BIN_DIR/tv" ] && ! is_ours "$BIN_DIR/tv"; then
  die "ja existe um comando 'tv' que nao e deste controle ($BIN_DIR/tv)"
fi
printf '#!/usr/bin/env sh\nexec python3 "%s/tv.py" "$@"\n' "$APP_DIR" > "$BIN_DIR/tv"
chmod +x "$BIN_DIR/tv"
ok "comando: ${B}tv${N}"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) warn "$BIN_DIR nao esta no PATH. Adicione ao ~/.bashrc: export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

step "4/5  Emissor infravermelho do celular"
IR_OK=0
if is_termux; then
  printf '    %saguardando o app Termux:API (ate 15 s)...%s\n' "$D" "$N"
  if out="$(timeout 15 python3 "$APP_DIR/tv.py" --diagnostico 2>&1)"; then
    out="${out%%$'\n'*}"; ok "${out#OK   }"; IR_OK=1
  else
    warn "${out#ERRO }"
    case "$out" in
      *"Termux:API"*) warn "Instale o app Termux:API pela mesma loja do Termux (F-Droid), abra-o uma vez e rode: tv --diagnostico" ;;
      *"infravermelho"*) warn "Sem emissor IR, o controle nao consegue falar com a TV. Use tv --simular para ver a tela." ;;
    esac
  fi
else
  ok "nao se aplica fora do Termux"
fi

step "5/5  Atalhos na tela inicial"
if ! is_termux; then
  ok "nao se aplica fora do Termux"
elif [ "$SHORTCUTS_MODE" = "yes" ] || { [ "$SHORTCUTS_MODE" = "ask" ] && ask "Criar atalhos (Ligar, Volume, Canal, Mudo) para o app Termux:Widget?"; }; then
  python3 "$APP_DIR/tv.py" --atalhos >/dev/null
  ok "6 atalhos criados em ~/.shortcuts (adicione o widget do Termux:Widget na tela inicial)"
else
  ok "sem atalhos (crie depois com: tv --atalhos)"
fi

printf '\n%s  ✔ PVN Controle TV %s instalado%s\n\n' "$G$B" "$VERSION" "$N"
printf '  Para abrir o controle, digite:  %stv%s\n' "$B" "$N"
[ "$IR_OK" = 1 ] || printf '  %sAntes, resolva o aviso da etapa 4.%s\n' "$Y" "$N"
printf '  %sAponte o topo do celular para a TV, a ate uns 3 metros.%s\n' "$D" "$N"
printf '  %sDesinstalar: bash %s/instalar.sh --remover%s\n\n' "$D" "$(short "$APP_DIR")" "$N"
