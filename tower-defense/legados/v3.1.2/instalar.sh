#!/usr/bin/env bash
# Instalador do Tower Defense para Termux e Linux.
#
#   bash instalar.sh               instala a partir desta pasta
#   curl -fsSL <url>/instalar.sh | bash      instala baixando do GitHub
#
# Opcoes: --teclas / --sem-teclas            barra de teclas do jogo no Termux, sem perguntar
#         --tela-cheia / --sem-tela-cheia    esconde as barras do Android e tira a margem lateral
#         --fonte / --sem-fonte              fonte DejaVu Sans Mono no Termux (★ e barras sem falhas)
#         --so-tela                          aplica so as opcoes do Termux, sem reinstalar o jogo
#         --remover                          desinstala e devolve a configuracao original do Termux
set -euo pipefail

REPO_RAW="${TD_REPO_RAW:-https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/tower-defense/source}"
APP_DIR="${TD_HOME:-$HOME/.local/share/tower-defense}"
PROPS="$HOME/.termux/termux.properties"
PROPS_BACKUP="$HOME/.termux/termux.properties.antes-do-td"
MARKER="# instalado pelo tower-defense"
EXTRA_KEYS="[['ESC','1','2','3','4','u','x','UP','ENTER'],['p','n','f','h','q','KEYBOARD','LEFT','DOWN','RIGHT']]"
FULL_PROPS=("fullscreen=true" "use-fullscreen-workaround=true" "terminal-margin-horizontal=0")
FONT_NAME="DejaVuSansMono.ttf"
FONT="$HOME/.termux/font.ttf"
FONT_BACKUP="$HOME/.termux/font.ttf.antes-do-td"
FONT_NONE="$HOME/.termux/.td-sem-fonte-original"

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
fetch() { if command -v curl >/dev/null 2>&1; then curl -fsSL "$1" -o "$2"; else wget -qO "$2" "$1"; fi; }

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

KEYS_MODE="ask"; FULL_MODE="ask"; FONT_MODE="ask"; ACTION="install"
for arg in "$@"; do
  case "$arg" in
    --teclas) KEYS_MODE="yes" ;;
    --sem-teclas) KEYS_MODE="no" ;;
    --tela-cheia) FULL_MODE="yes" ;;
    --sem-tela-cheia) FULL_MODE="no" ;;
    --fonte) FONT_MODE="yes" ;;
    --sem-fonte) FONT_MODE="no" ;;
    --so-tela) ACTION="screen" ;;
    --remover|--desinstalar) ACTION="remove" ;;
    -h|--ajuda) sed -n '2,13p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "opcao desconhecida: $arg" ;;
  esac
done
SELF="${BASH_SOURCE[0]:-}"
SRC=""
[ -n "$SELF" ] && [ -f "$SELF" ] && [ -f "$(dirname "$SELF")/td.py" ] && SRC="$(cd "$(dirname "$SELF")" && pwd)"

CHANGED=0; SUMMARY=()

backup_props() {
  mkdir -p "$(dirname "$PROPS")"
  if [ ! -e "$PROPS_BACKUP" ]; then
    if [ -e "$PROPS" ]; then cp "$PROPS" "$PROPS_BACKUP"; else printf '%s\n' "# td: arquivo nao existia" > "$PROPS_BACKUP"; fi
    ok "backup da configuracao atual: ${D}$(short "$PROPS_BACKUP")${N}"
  fi
}

# set_props chave=valor ... (grava, marcadas pelo jogo) e -chave (tira, so se foi o jogo que gravou)
set_props() {
  backup_props
  # respeita valores quebrados em varias linhas com "\" e as configuracoes da pessoa
  python3 - "$PROPS" "$MARKER" "$@" <<'PY'
import os, sys
path, marker, args = sys.argv[1], sys.argv[2], sys.argv[3:]
sets, unsets = {}, set()
for a in args:
    if a.startswith("-"):
        unsets.add(a[1:])
    else:
        k, v = a.split("=", 1)
        sets[k] = v
lines = open(path, encoding="utf-8").read().splitlines() if os.path.exists(path) else []
out, skipping, ours = [], False, False
for line in lines:
    if skipping:
        skipping = line.rstrip().endswith("\\")
        continue
    s = line.strip()
    if s == marker:
        ours = True
        continue
    key = s.split("=", 1)[0].strip() if "=" in s and not s.startswith(("#", "!")) else None
    mine, ours = ours, False
    if key in sets or (key in unsets and mine):
        skipping = line.rstrip().endswith("\\")
        continue
    if mine:
        out.append(marker)
    out.append(line)
for k, v in sets.items():
    out += [marker, f"{k} = {v}"]
open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
PY
  CHANGED=1
}

ours_prop() { [ -f "$PROPS" ] && grep -A1 -x -F "$MARKER" "$PROPS" | grep -q "^$1 ="; }

restore_props() {
  [ -e "$PROPS_BACKUP" ] || return 0
  if [ "$(head -n1 "$PROPS_BACKUP")" = "# td: arquivo nao existia" ]; then
    rm -f "$PROPS" "$PROPS_BACKUP"
  else
    mv -f "$PROPS_BACKUP" "$PROPS"
  fi
  CHANGED=1
  ok "configuracao original do Termux restaurada"
}

font_ours() { [ -e "$FONT_BACKUP" ] || [ -e "$FONT_NONE" ]; }

font_source() {  # a fonte que acompanha o jogo; baixa do GitHub se nao estiver aqui
  for d in "$SRC" "$APP_DIR"; do
    [ -n "$d" ] && [ -f "$d/fontes/$FONT_NAME" ] && { printf '%s' "$d/fontes/$FONT_NAME"; return 0; }
  done
  mkdir -p "$APP_DIR/fontes"
  fetch "$REPO_RAW/fontes/$FONT_NAME" "$APP_DIR/fontes/$FONT_NAME.tmp" || return 1
  fetch "$REPO_RAW/fontes/LICENCA.txt" "$APP_DIR/fontes/LICENCA.txt" || true
  mv -f "$APP_DIR/fontes/$FONT_NAME.tmp" "$APP_DIR/fontes/$FONT_NAME"
  printf '%s' "$APP_DIR/fontes/$FONT_NAME"
}

install_font() {
  local src
  src="$(font_source)" || { warn "nao consegui obter a fonte (sem internet?)"; return 1; }
  mkdir -p "$(dirname "$FONT")"
  if ! font_ours; then
    if [ -e "$FONT" ]; then cp "$FONT" "$FONT_BACKUP"; else : > "$FONT_NONE"; fi
  fi
  cp "$src" "$FONT"
  CHANGED=1; SUMMARY+=("fonte do jogo instalada")
  if [ -e "$FONT_BACKUP" ]; then
    ok "fonte DejaVu Sans Mono no Termux ${D}(a sua ficou em $(short "$FONT_BACKUP"))${N}"
  else
    ok "fonte DejaVu Sans Mono no Termux ${D}(antes era a fonte padrão)${N}"
  fi
}

restore_font() {
  if [ -e "$FONT_BACKUP" ]; then mv -f "$FONT_BACKUP" "$FONT"
  elif [ -e "$FONT_NONE" ]; then rm -f "$FONT" "$FONT_NONE"
  else return 0
  fi
  CHANGED=1; SUMMARY+=("fonte original de volta")
  ok "fonte original do Termux de volta"
}

reload_termux() {
  [ "$CHANGED" = 1 ] || return 0
  if command -v termux-reload-settings >/dev/null 2>&1; then termux-reload-settings || true; fi
}

termux_setup() {  # passo das opcoes do Termux: teclas, tela cheia e fonte ("keep": nao mexe)
  if [ "$KEYS_MODE" = "keep" ]; then
    :
  elif [ "$KEYS_MODE" = "yes" ] || { [ "$KEYS_MODE" = "ask" ] && ask "Trocar a barra de teclas extras por uma feita para o jogo?"; }; then
    set_props "extra-keys=$EXTRA_KEYS"; SUMMARY+=("barra de teclas do jogo")
    ok "barra de teclas do jogo ativada"
  else
    ok "barra de teclas mantida como esta"
  fi
  if [ "$FULL_MODE" = "keep" ]; then
    :
  elif [ "$FULL_MODE" = "no" ]; then
    if ours_prop fullscreen; then
      set_props -fullscreen -use-fullscreen-workaround -terminal-margin-horizontal; SUMMARY+=("tela cheia desligada")
      ok "tela cheia desligada"
    fi
  elif [ "$FULL_MODE" = "ask" ] && ours_prop fullscreen; then
    ok "tela cheia ja ativada"
  elif [ "$FULL_MODE" = "yes" ] || ask "Deixar o Termux em tela cheia (esconde as barras do Android)?"; then
    set_props "${FULL_PROPS[@]}"; SUMMARY+=("tela cheia ativada")
    ok "tela cheia ativada e margem lateral zerada"
  else
    ok "tela do Termux mantida como esta"
  fi
  if [ "$FONT_MODE" = "keep" ]; then
    :
  elif [ "$FONT_MODE" = "no" ]; then
    restore_font
  elif [ "$FONT_MODE" = "ask" ] && font_ours; then
    ok "fonte do jogo ja instalada"
  elif [ "$FONT_MODE" = "yes" ] || ask "Instalar a fonte DejaVu Sans Mono no Termux (★ e barras sem falhas)?"; then
    install_font || true
  else
    ok "fonte do Termux mantida"
  fi
  reload_termux
}

is_ours() { [ -f "$1" ] && grep -q "$APP_DIR/td.py" "$1"; }

if [ "$ACTION" = "remove" ]; then
  step "Removendo o Tower Defense"
  for name in td tower-defense; do
    if is_ours "$BIN_DIR/$name"; then rm -f "$BIN_DIR/$name"; ok "comando $name removido"; fi
  done
  rm -rf "$APP_DIR" && ok "arquivos do jogo removidos"
  if is_termux; then restore_props; restore_font; reload_termux; fi
  printf '\n%sPronto. Tower Defense desinstalado.%s\n' "$G" "$N"
  exit 0
fi

if [ "$ACTION" = "screen" ]; then
  is_termux || die "as opcoes de tela so valem no Termux"
  # aqui ninguem responde perguntas (o jogo chama este modo): so mexe no que foi pedido
  [ "$KEYS_MODE" = "ask" ] && KEYS_MODE="keep"
  [ "$FULL_MODE" = "ask" ] && FULL_MODE="keep"
  [ "$FONT_MODE" = "ask" ] && FONT_MODE="keep"
  termux_setup
  if [ "${#SUMMARY[@]}" -gt 0 ]; then
    msg="$(IFS=','; echo "${SUMMARY[*]}" | sed 's/,/, /g')"
    ok "${msg}; o Termux recarregou"
  else
    ok "nada mudou"
  fi
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
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
if [ -n "$SRC" ]; then
  cp "$SRC/td.py" "$SRC/VERSION" "$SRC/instalar.sh" "$TMP/"
  [ -d "$SRC/fontes" ] && cp -r "$SRC/fontes" "$TMP/"
  ok "copiando da pasta ${D}$(short "$SRC")${N}"
else
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
[ -d "$TMP/fontes" ] && cp -r "$TMP/fontes" "$APP_DIR/"
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

step "4/4  Termux: teclas, tela cheia e fonte"
if ! is_termux; then
  ok "nao se aplica fora do Termux"
else
  termux_setup
fi

printf '\n%s  ✔ Tower Defense %s instalado%s\n\n' "$G$B" "$VERSION" "$N"
printf '  Para jogar, digite:  %s%s%s\n' "$B" "${COMMANDS[-1]}" "$N"
printf '  %sDica: esconda o teclado e jogue tocando na tela.%s\n' "$D" "$N"
printf '  %sCrie seus mapas: menu → Criar mapa (ou td --editor).%s\n' "$D" "$N"
printf '  %sTela cheia e fonte depois: Opções → Ajustar tela.%s\n' "$D" "$N"
printf '  %sDesinstalar: bash %s/instalar.sh --remover%s\n\n' "$D" "$(short "$APP_DIR")" "$N"

# le a resposta do terminal mesmo com "curl | bash"; sem terminal (testes), nao pergunta
# TD_SEM_TUTORIAL=1: usado pelo setup de teste, que instala os dois projetos em sequência
if [ -z "${TD_SEM_TUTORIAL:-}" ] && ask "Abrir o tutorial agora?"; then
  exec python3 "$APP_DIR/td.py" --tutorial </dev/tty >/dev/tty 2>&1
fi
