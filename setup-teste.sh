#!/usr/bin/env bash
# Setup de teste completo: instala o PVN Controle TV e o Tower Defense no Termux,
# confere o emissor infravermelho e mostra o roteiro de teste.
#
#   curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/setup-teste.sh | bash
set -uo pipefail

BASE="${PVN_RAW:-https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD}"
export TV_REPO_RAW="${TV_REPO_RAW:-$BASE/controle-tv/source}"
export TD_REPO_RAW="${TD_REPO_RAW:-$BASE/tower-defense/source}"
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

printf '\n%s  ╭──────────────────────────────────╮%s\n' "$Y" "$N"
printf '%s  │%s   %sPVN · SETUP DE TESTE COMPLETO%s  %s│%s\n' "$Y" "$N" "$B" "$N" "$Y" "$N"
printf '%s  ╰──────────────────────────────────╯%s\n' "$Y" "$N"
printf '  %s📺 Controle TV  +  🏰 Tower Defense%s\n' "$D" "$N"

title "1/4  Preparação"
if is_termux; then
  ok "Termux detectado"
  if ! command -v python3 >/dev/null 2>&1 || ! command -v termux-infrared-transmit >/dev/null 2>&1; then
    warn "atualizando a lista de pacotes (1 a 3 minutos na primeira vez)..."
    if pkg update -y </dev/null >/dev/null 2>&1; then ok "pacotes atualizados"; else warn "pkg update falhou; se a instalação falhar, rode: termux-change-repo"; fi
  else
    ok "Python e termux-api já presentes"
  fi
else
  warn "fora do Termux: o controle roda só em modo simulado (sem emissor IR)"
fi
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fetch "$TV_REPO_RAW/instalar.sh" "$TMP/tv.sh" && fetch "$TD_REPO_RAW/instalar.sh" "$TMP/td.sh" \
  || { bad "não consegui baixar os instaladores (sem internet?)"; exit 1; }
ok "instaladores baixados"

title "2/4  PVN Controle TV"
if bash "$TMP/tv.sh" </dev/null; then TV_OK=1; else TV_OK=0; fi

title "3/4  Tower Defense"
if TD_SEM_TUTORIAL=1 bash "$TMP/td.sh" </dev/null; then TD_OK=1; else TD_OK=0; fi

title "4/4  Conferência"
find_cmd() { command -v "$1" 2>/dev/null || { [ -x "$HOME/.local/bin/$1" ] && echo "$HOME/.local/bin/$1"; }; }
TV_BIN="$(find_cmd tv)"; TD_BIN="$(find_cmd td)"
if [ "$TV_OK" = 1 ] && [ -n "$TV_BIN" ]; then ok "controle $("$TV_BIN" --versao) instalado: comando tv"; else bad "controle não instalou (veja as mensagens acima)"; fi
if [ "$TD_OK" = 1 ] && [ -n "$TD_BIN" ]; then ok "jogo $("$TD_BIN" --versao) instalado: comando td"; else bad "jogo não instalou (veja as mensagens acima)"; fi
IR_OK=0
if [ -n "$TV_BIN" ] && is_termux; then
  if diag="$(timeout 15 "$TV_BIN" --diagnostico 2>&1)"; then diag="${diag%%$'\n'*}"; ok "${diag#OK   }"; IR_OK=1; else bad "${diag#ERRO }"; fi
fi

printf '\n%s  ROTEIRO DE TESTE%s\n' "$B" "$N"
printf '  %s📺 Controle%s\n' "$B" "$N"
if [ "$IR_OK" = 1 ]; then
  printf '   1. digite %stv%s e toque na marca da sua TV\n' "$B" "$N"
else
  printf '   1. resolva o aviso do emissor acima; enquanto isso: %stv --simular%s\n' "$B" "$N"
fi
printf '   2. aponte o topo do celular para a TV e toque em LIGAR\n'
printf '   3. teste VOL, MUDO, CH, números, setas e OK\n'
printf '   4. se a marca não reagir: tecla %sd%s (descobrir)\n' "$B" "$N"
printf '  %s🏰 Tower Defense%s\n' "$B" "$N"
printf '   1. digite %std%s e abra o Tutorial\n' "$B" "$N"
printf '   2. jogue só com toques; anote a onda em que perdeu\n'
printf '   3. se os emojis desalinharem: Opções → Emojis: NÃO\n'
printf '\n  %sRoteiros completos:%s\n' "$D" "$N"
printf '  %s%s/controle-tv/docs/ROADMAP.md%s\n' "$D" "$REPO_WEB" "$N"
printf '  %s%s/tower-defense/docs/ROADMAP.md%s\n\n' "$D" "$REPO_WEB" "$N"
[ "$TV_OK" = 1 ] && [ "$TD_OK" = 1 ]
