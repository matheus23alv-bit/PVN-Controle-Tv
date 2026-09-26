#!/usr/bin/env bash
# Instalador do Tower Defense para Termux e Linux.
#
#   bash instalar.sh               instala a partir desta pasta
#   curl -fsSL <url>/instalar.sh | bash      instala baixando do GitHub
#
# Opcoes: --teclas (configura a barra de teclas do Termux sem perguntar)
#         --sem-teclas (nao mexe na barra de teclas)
#         --remover (desinstala e restaura a barra de teclas original)
set -euo pipefail

REPO_RAW="${TD_REPO_RAW:-https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/tower-defense/source}"
APP_DIR="${TD_HOME:-$HOME/.local/share/tower-defense}"
PROPS="$HOME/.termux/termux.properties"
PROPS_BACKUP="$HOME/.termux/termux.properties.antes-do-td"
MARKER="# instalado pelo tower-defense"
EXTRA_KEYS="extra-keys = [['ESC','1','2','3','4','u','x','UP','ENTER'],['p','n','f','h','q','KEYBOARD','LEFT','DOWN','RIGHT']]"

if [ -t 1 ]; then
  B=$'\e[1m'; D=$'\e[2m'; G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; C=$'\e[36m'; N=$'\e[0m'
else
  B=""; D=""; G=""; Y=""; R=""; C=""; N=""
fi
step() { printf '%s==>%s %s%s%s\n' "$C" "$N" "$B" "$*" "$N"; }
ok()   { printf '    %s✔%s %s\n' "$G" "$N" "$*"; }
warn() { printf '    %s!%s %s\n' "$Y" "$N" "$*"; }
# mostra caminhos com ~ (variavel evita a expansao do ~ que o bash faz na substituicao)
short() { local t="~"; printf '%s' "${1/#$HOME/$t}"; }
die()  { printf '    %s✘ %s%s\n' "$R" "$*" "$N" >&2; exit 1; }

is_termux() { [ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux/files ]; }
if is_termux; then BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"; else BIN_DIR="$HOME/.local/bin"; fi

ask() {
  # funciona mesmo com "curl | bash", em que a entrada padrao e o proprio script
  local answer=""
  # /dev/tty pode existir sem abrir (sem terminal de controle): testa abrindo de verdade
  if (exec </dev/tty) 2>/dev/null; then
    printf '    %s%s%s [s/N] ' "$B" "$1" "$N"
    read -r answer </dev/tty || answer=""
  fi
  [[ "$answer" =~ ^[sSyY] ]]
}

KEYS_MODE="ask"; ACTION="install"
for arg in "$@"; do
  case "$arg" in
    --teclas) KEYS_MODE="yes" ;;
    --sem-teclas) KEYS_MODE="no" ;;
    --remover|--desinstalar) ACTION="remove" ;;
    -h|--ajuda) sed -n '2,10p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "opcao desconhecida: $arg" ;;
  esac
done

write_extra_keys() {
  mkdir -p "$(dirname "$PROPS")"
  if [ ! -e "$PROPS_BACKUP" ]; then
    if [ -e "$PROPS" ]; then cp "$PROPS" "$PROPS_BACKUP"; else printf '%s\n' "# td: arquivo nao existia" > "$PROPS_BACKUP"; fi
    ok "backup da configuracao atual: ${D}$(short "$PROPS_BACKUP")${N}"
  fi
  # troca a chave extra-keys respeitando valores quebrados em varias linhas com "\"
  python3 - "$PROPS" "$EXTRA_KEYS" "$MARKER" <<'PY'
import os, sys
path, new_line, marker = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(path, encoding="utf-8").read().splitlines() if os.path.exists(path) else []
out, skipping = [], False
for line in lines:
    if skipping:
        skipping = line.rstrip().endswith("\\")
        continue
    s = line.strip()
    if s == marker:
        continue
    if not s.startswith(("#", "!")) and s.replace(" ", "").startswith("extra-keys="):
        skipping = line.rstrip().endswith("\\")
        continue
    out.append(line)
out += [marker, new_line]
open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
PY
  command -v termux-reload-settings >/dev/null 2>&1 && termux-reload-settings || true
  ok "barra de teclas do jogo ativada"
}

restore_extra_keys() {
  [ -e "$PROPS_BACKUP" ] || return 0
  if [ "$(head -n1 "$PROPS_BACKUP")" = "# td: arquivo nao existia" ]; then
    rm -f "$PROPS" "$PROPS_BACKUP"
  else
    mv -f "$PROPS_BACKUP" "$PROPS"
  fi
  command -v termux-reload-settings >/dev/null 2>&1 && termux-reload-settings || true
  ok "barra de teclas original restaurada"
}

is_ours() { [ -f "$1" ] && grep -q "$APP_DIR/td.py" "$1"; }

if [ "$ACTION" = "remove" ]; then
  step "Removendo o Tower Defense"
  for name in td tower-defense; do
    if is_ours "$BIN_DIR/$name"; then rm -f "$BIN_DIR/$name"; ok "comando $name removido"; fi
  done
  rm -rf "$APP_DIR" && ok "arquivos do jogo removidos"
  is_termux && restore_extra_keys
  printf '\n%sPronto. Tower Defense desinstalado.%s\n' "$G" "$N"
  exit 0
fi

printf '\n%s  ╭──────────────────────────────────╮%s\n' "$Y" "$N"
printf '%s  │%s  🏰  %sTOWER DEFENSE%s · instalador  %s│%s\n' "$Y" "$N" "$B" "$N" "$Y" "$N"
printf '%s  ╰──────────────────────────────────╯%s\n' "$Y" "$N"
printf '%s  %s%s\n\n' "$D" "$(is_termux && echo "Termux detectado" || echo "Linux detectado")" "$N"

step "1/4  Python"
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
if ! python3 -c 'import curses' 2>/dev/null; then
  if is_termux; then
    pkg install -y ncurses python </dev/null >/dev/null 2>&1 || true
  fi
  python3 -c 'import curses' 2>/dev/null || die "modulo curses indisponivel neste Python"
fi
ok "modulo curses disponivel"

step "2/4  Arquivos do jogo"
SELF="${BASH_SOURCE[0]:-}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
if [ -n "$SELF" ] && [ -f "$SELF" ] && [ -f "$(dirname "$SELF")/td.py" ]; then
  SRC="$(cd "$(dirname "$SELF")" && pwd)"
  cp "$SRC/td.py" "$SRC/VERSION" "$SRC/instalar.sh" "$TMP/"
  ok "copiando da pasta ${D}$(short "$SRC")${N}"
else
  fetch() { if command -v curl >/dev/null 2>&1; then curl -fsSL "$1" -o "$2"; else wget -qO "$2" "$1"; fi; }
  fetch "$REPO_RAW/td.py" "$TMP/td.py" || die "nao consegui baixar td.py (sem internet?)"
  fetch "$REPO_RAW/VERSION" "$TMP/VERSION" || die "nao consegui baixar VERSION"
  fetch "$REPO_RAW/instalar.sh" "$TMP/instalar.sh" || die "nao consegui baixar instalar.sh"
  ok "baixado do GitHub"
fi
python3 -m py_compile "$TMP/td.py" 2>/dev/null || die "td.py corrompido ou incompleto"
rm -rf "$TMP/__pycache__"
mkdir -p "$APP_DIR"
# guarda o instalador junto do jogo para atualizar ou desinstalar depois, mesmo apos "curl | bash"
cp "$TMP/td.py" "$TMP/VERSION" "$TMP/instalar.sh" "$APP_DIR/"
VERSION="$(cat "$APP_DIR/VERSION")"
ok "versao $VERSION em ${D}$(short "$APP_DIR")${N}"

step "3/4  Comando para abrir o jogo"
mkdir -p "$BIN_DIR"
COMMANDS=()
for name in tower-defense td; do
  target="$BIN_DIR/$name"
  if [ -e "$target" ] && ! is_ours "$target"; then
    warn "'$name' ja existe no sistema e nao sera substituido"
    continue
  fi
  printf '#!/usr/bin/env sh\nexec python3 "%s/td.py" "$@"\n' "$APP_DIR" > "$target"
  chmod +x "$target"
  COMMANDS+=("$name")
done
[ "${#COMMANDS[@]}" -gt 0 ] || die "nenhum comando pode ser criado em $BIN_DIR"
ok "comando: ${B}${COMMANDS[-1]}${N}"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) warn "$BIN_DIR nao esta no PATH. Adicione ao ~/.bashrc: export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

step "4/4  Barra de teclas do Termux"
if ! is_termux; then
  ok "nao se aplica fora do Termux"
elif [ "$KEYS_MODE" = "yes" ] || { [ "$KEYS_MODE" = "ask" ] && ask "Trocar a barra de teclas extras por uma feita para o jogo?"; }; then
  write_extra_keys
else
  ok "barra de teclas mantida como esta"
fi

printf '\n%s  ✔ Tower Defense %s instalado%s\n\n' "$G$B" "$VERSION" "$N"
printf '  Para jogar, digite:  %s%s%s\n' "$B" "${COMMANDS[-1]}" "$N"
printf '  %sDica: esconda o teclado e jogue tocando na tela.%s\n' "$D" "$N"
printf '  %sDesinstalar: bash %s/instalar.sh --remover%s\n\n' "$D" "$(short "$APP_DIR")" "$N"

# le a resposta do terminal mesmo com "curl | bash"; sem terminal (testes), nao pergunta
# TD_SEM_TUTORIAL=1: usado pelo setup de teste, que instala os dois projetos em sequência
if [ -z "${TD_SEM_TUTORIAL:-}" ] && ask "Abrir o tutorial agora?"; then
  exec python3 "$APP_DIR/td.py" --tutorial </dev/tty >/dev/tty 2>&1
fi
