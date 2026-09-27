#!/usr/bin/env bash
# Setup de teste: instala o Teclado Termux e o PVN Controle TV no Termux,
# confere o emissor infravermelho e mostra o roteiro de teste.
#
# O Tower Defense saiu deste repositório: ele tem o setup dele em
# matheus23alv-bit/TOWER-DEFENSE---TERMUX-. Com o teclas instalado, a barra do
# jogo continua entrando e saindo sozinha quando você abre o td.
#
#   curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/setup-teste.sh | bash
#   bash setup-teste.sh          (de dentro do pack zip: instala a versão do pack)
#
# De dentro de um pack, instala só os projetos que vierem nele.
set -uo pipefail

BASE="${PVN_RAW:-https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD}"
export TV_REPO_RAW="${TV_REPO_RAW:-$BASE/controle-tv/source}"
export TECLAS_REPO_RAW="${TECLAS_REPO_RAW:-$BASE/teclado-termux/source}"
REPO_WEB="https://github.com/matheus23alv-bit/PVN-Controle-Tv/blob/HEAD"

if [ -t 1 ]; then
  B=$'\e[1m'; D=$'\e[2m'; G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; C=$'\e[36m'; N=$'\e[0m'
else
  B=""; D=""; G=""; Y=""; R=""; C=""; N=""
fi
title() { printf '\n%s━━ %s%s\n' "$C$B" "$*" "$N"; }
ok()   { printf '  %s✔%s %s\n' "$G" "$N" "$*"; }
warn() { printf '  %s!%s %s\n' "$Y" "$N" "$*"; }
bad()  { printf '  %s✘%s %s\n' "$R" "$N" "$*"; }
is_termux() { [ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux/files ]; }
fetch() { if command -v curl >/dev/null 2>&1; then curl -fsSL "$1" -o "$2"; else wget -qO "$2" "$1"; fi; }

SELF="${BASH_SOURCE[0]:-}"
HERE=""
[ -n "$SELF" ] && [ -f "$SELF" ] && HERE="$(cd "$(dirname "$SELF")" && pwd)"
TV_INST=""; TK_INST=""
if [ -n "$HERE" ]; then
  [ -f "$HERE/controle-tv/source/instalar.sh" ] && TV_INST="$HERE/controle-tv/source/instalar.sh"
  [ -f "$HERE/teclado-termux/source/instalar.sh" ] && TK_INST="$HERE/teclado-termux/source/instalar.sh"
fi
# rodando de dentro de um pack zip ou do repositório: instala exatamente esta versão, e só
# os projetos que vieram nele; pelo curl, baixa e instala os dois
if [ -n "$TV_INST$TK_INST" ]; then LOCAL=1; else LOCAL=0; fi
DO_TV=1; DO_TK=1
[ "$LOCAL" = 1 ] && [ -z "$TV_INST" ] && DO_TV=0
[ "$LOCAL" = 1 ] && [ -z "$TK_INST" ] && DO_TK=0
TOTAL=$((2 + DO_TV + DO_TK)); STEP=1
step() { title "$STEP/$TOTAL  $*"; STEP=$((STEP + 1)); }

printf '\n%s  ╭──────────────────────────────────╮%s\n' "$Y" "$N"
if [ "$DO_TV" = 1 ] && [ "$DO_TK" = 1 ]; then
  printf '%s  │%s   %sPVN · SETUP DE TESTE COMPLETO%s  %s│%s\n' "$Y" "$N" "$B" "$N" "$Y" "$N"
  printf '%s  ╰──────────────────────────────────╯%s\n' "$Y" "$N"
  printf '  %s⌨ Teclado Termux  +  📺 Controle TV%s\n' "$D" "$N"
elif [ "$DO_TV" = 1 ]; then
  printf '%s  │%s    %sPVN · SETUP DO CONTROLE TV%s    %s│%s\n' "$Y" "$N" "$B" "$N" "$Y" "$N"
  printf '%s  ╰──────────────────────────────────╯%s\n' "$Y" "$N"
  printf '  %s📺 Controle TV%s\n' "$D" "$N"
else
  printf '%s  │%s     %sPVN · SETUP DO TECLADO%s       %s│%s\n' "$Y" "$N" "$B" "$N" "$Y" "$N"
  printf '%s  ╰──────────────────────────────────╯%s\n' "$Y" "$N"
  printf '  %s⌨ Teclado Termux%s\n' "$D" "$N"
fi

step "Preparação"
if is_termux; then
  ok "Termux detectado"
  if ! command -v python3 >/dev/null 2>&1 || { [ "$DO_TV" = 1 ] && ! command -v termux-infrared-transmit >/dev/null 2>&1; }; then
    warn "atualizando a lista de pacotes (1 a 3 minutos na primeira vez)..."
    if pkg update -y </dev/null >/dev/null 2>&1; then ok "pacotes atualizados"; else warn "pkg update falhou; se a instalação falhar, rode: termux-change-repo"; fi
  elif [ "$DO_TV" = 1 ]; then
    ok "Python e termux-api já presentes"
  else
    ok "Python já presente"
  fi
elif [ "$DO_TV" = 1 ]; then
  warn "fora do Termux: o controle roda só em modo simulado (sem emissor IR)"
else
  warn "fora do Termux: as opções de tela do Termux ficam de fora"
fi
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
if [ "$LOCAL" = 1 ]; then
  t="~"; ok "usando os arquivos desta pasta (${HERE/#$HOME/$t})"
else
  TV_INST="$TMP/tv.sh"; TK_INST="$TMP/teclas.sh"
  fetch "$TV_REPO_RAW/instalar.sh" "$TV_INST" && fetch "$TECLAS_REPO_RAW/instalar.sh" "$TK_INST" \
    || { bad "não consegui baixar os instaladores (sem internet?)"; exit 1; }
  ok "instaladores baixados do GitHub"
fi

TV_OK=0; TK_OK=0
# o teclado vai primeiro: o tv (e o td, se estiver instalado) trocam a barra por ele
if [ "$DO_TK" = 1 ]; then
  step "Teclado Termux"
  if bash "$TK_INST" </dev/null; then TK_OK=1; fi
fi
if [ "$DO_TV" = 1 ]; then
  step "PVN Controle TV"
  if bash "$TV_INST" </dev/null; then TV_OK=1; fi
fi
step "Conferência"
find_cmd() { command -v "$1" 2>/dev/null || { [ -x "$HOME/.local/bin/$1" ] && echo "$HOME/.local/bin/$1"; }; }
TV_BIN=""
if [ "$DO_TK" = 1 ]; then
  TK_BIN="$(find_cmd teclas)"
  if [ "$TK_OK" = 1 ] && [ -n "$TK_BIN" ]; then ok "teclado $("$TK_BIN" --versao) instalado: comando teclas"; else bad "teclado não instalou (veja as mensagens acima)"; fi
fi
if [ "$DO_TV" = 1 ]; then
  TV_BIN="$(find_cmd tv)"
  if [ "$TV_OK" = 1 ] && [ -n "$TV_BIN" ]; then ok "controle $("$TV_BIN" --versao) instalado: comando tv"; else bad "controle não instalou (veja as mensagens acima)"; fi
fi
IR_OK=0
if [ -n "$TV_BIN" ] && is_termux; then
  if diag="$(timeout 15 "$TV_BIN" --diagnostico 2>&1)"; then diag="${diag%%$'\n'*}"; ok "${diag#OK   }"; IR_OK=1; else bad "${diag#ERRO }"; fi
fi

printf '\n%s  ROTEIRO DE TESTE%s\n' "$B" "$N"
if [ "$DO_TV" = 1 ]; then
  printf '  %s📺 Controle%s\n' "$B" "$N"
  if [ "$IR_OK" = 1 ]; then
    printf '   1. digite %stv%s e toque na marca da sua TV\n' "$B" "$N"
  else
    printf '   1. resolva o aviso do emissor acima; enquanto isso: %stv --simular%s\n' "$B" "$N"
  fi
  printf '   2. aponte o topo do celular para a TV e toque em LIGAR\n'
  printf '   3. teste VOL, MUDO, CH, números, setas e OK\n'
  printf '   4. se a marca não reagir: tecla %sd%s (descobrir)\n' "$B" "$N"
fi
if [ "$DO_TK" = 1 ]; then
  printf '  %s⌨ Teclado%s\n' "$B" "$N"
  printf '   1. digite %steclas%s e toque na barra que quer no dia a dia\n' "$B" "$N"
  printf '   2. abra o tv: a barra troca sozinha e volta ao sair\n'
  printf '   3. na barra da TV, segure VOL+ para o volume subir sem parar\n'
  printf '   4. para ter a sua barra de antes: %steclas original%s\n' "$B" "$N"
  if command -v td >/dev/null 2>&1; then
    printf '   5. o jogo também troca: abra o %std%s e veja a barra dele entrar e sair\n' "$B" "$N"
  fi
fi
if [ $((DO_TV + DO_TK)) -gt 1 ]; then printf '\n  %sRoteiros completos:%s\n' "$D" "$N"; else printf '\n  %sRoteiro completo:%s\n' "$D" "$N"; fi
[ "$DO_TV" = 1 ] && printf '  %s%s/controle-tv/docs/ROADMAP.md%s\n' "$D" "$REPO_WEB" "$N"
[ "$DO_TK" = 1 ] && printf '  %s%s/teclado-termux/docs/ROADMAP.md%s\n' "$D" "$REPO_WEB" "$N"
echo
{ [ "$DO_TV" = 0 ] || [ "$TV_OK" = 1 ]; } && { [ "$DO_TK" = 0 ] || [ "$TK_OK" = 1 ]; }
