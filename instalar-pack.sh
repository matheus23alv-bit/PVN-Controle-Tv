#!/usr/bin/env bash
# Instala o PVN (controle da TV + Tower Defense) a partir do pack zip salvo
# na pasta Download do celular.
#
#   termux-setup-storage                          (uma vez: toque em Permitir)
#   bash ~/storage/downloads/instalar-pack.sh     (se este arquivo também está no Download)
#   curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/instalar-pack.sh | bash
#   bash instalar-pack.sh /caminho/PVN-pack-....zip    (usa um zip específico)
#
# Usa o PVN-pack-*.zip mais recente da pasta Download, confere o SHA-256 de cada
# arquivo, extrai em ~/pvn-pack e roda o setup-teste.sh do próprio pack.
set -uo pipefail

DEST="${PVN_PACK_DIR:-$HOME/pvn-pack}"
DOWNLOAD_DIRS=("${PVN_DOWNLOADS:-$HOME/storage/downloads}" /storage/emulated/0/Download /sdcard/Download)

if [ -t 1 ]; then
  B=$'\e[1m'; D=$'\e[2m'; G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; C=$'\e[36m'; N=$'\e[0m'
else
  B=""; D=""; G=""; Y=""; R=""; C=""; N=""
fi
title() { printf '\n%s━━ %s%s\n' "$C$B" "$*" "$N"; }
ok()   { printf '  %s✔%s %s\n' "$G" "$N" "$*"; }
warn() { printf '  %s!%s %s\n' "$Y" "$N" "$*"; }
die()  { printf '  %s✘ %s%s\n' "$R" "$*" "$N" >&2; exit 1; }
short() { local t="~"; printf '%s' "${1/#$HOME/$t}"; }

printf '\n%s  ╭──────────────────────────────────╮%s\n' "$Y" "$N"
printf '%s  │%s  %sPVN · instalar pelo pack zip%s    %s│%s\n' "$Y" "$N" "$B" "$N" "$Y" "$N"
printf '%s  ╰──────────────────────────────────╯%s\n' "$Y" "$N"

# a pasta de destino é substituída a cada instalação: só aceita uma que seja de um pack anterior
if [ -e "$DEST" ] && [ ! -f "$DEST/PACK-INFO.txt" ]; then
  die "$(short "$DEST") já existe e não é um pack do PVN. Escolha outra pasta com PVN_PACK_DIR=<pasta>."
fi

title "1/4  Pack na pasta Download"
ZIP="${1:-}"
if [ -n "$ZIP" ]; then
  [ -f "$ZIP" ] || die "arquivo não encontrado: $ZIP"
else
  find_download() {
    for d in "${DOWNLOAD_DIRS[@]}"; do
      [ -d "$d" ] && [ -r "$d" ] && { echo "$d"; return 0; }
    done
    return 1
  }
  DL="$(find_download)"
  if [ -z "$DL" ] && command -v termux-setup-storage >/dev/null 2>&1; then
    warn "o Termux ainda não tem acesso aos arquivos do celular"
    printf '  %s→ toque em PERMITIR na janela do Android%s\n' "$B" "$N"
    termux-setup-storage </dev/null >/dev/null 2>&1 &
    for _ in $(seq 1 60); do
      sleep 1
      DL="$(find_download)" && break
    done
  fi
  [ -n "$DL" ] || die "sem acesso à pasta Download. Rode termux-setup-storage, toque em Permitir e tente de novo."
  # o mais recente pela data do arquivo; aceita nomes como "PVN-pack-... (1).zip".
  # -H: ~/storage/downloads é um link simbólico para a pasta Download do Android
  ZIP="$(find -H "$DL" -maxdepth 1 -type f -name 'PVN-pack-*.zip' -printf '%T@\t%p\n' 2>/dev/null | sort -rn | head -1 | cut -f2-)"
  if [ -z "$ZIP" ]; then
    die "nenhum PVN-pack-*.zip em $(short "$DL"). Baixe o pack para a pasta Download e rode de novo."
  fi
fi
ok "$(basename "$ZIP")  ${D}($(du -h "$ZIP" | cut -f1))${N}"

title "2/4  Extraindo"
TMP="$DEST.novo"
rm -rf "$TMP"
mkdir -p "$TMP"
extract() {
  if command -v unzip >/dev/null 2>&1 && unzip -q -o "$ZIP" -d "$TMP" 2>/dev/null; then return 0; fi
  if command -v python3 >/dev/null 2>&1 && python3 -m zipfile -e "$ZIP" "$TMP" 2>/dev/null; then return 0; fi
  if command -v pkg >/dev/null 2>&1; then
    warn "instalando o unzip..."
    pkg install -y unzip </dev/null >/dev/null 2>&1 && unzip -q -o "$ZIP" -d "$TMP" 2>/dev/null && return 0
  fi
  return 1
}
extract || { rm -rf "$TMP"; die "não consegui abrir o zip. Ele pode estar incompleto: baixe de novo."; }
INFO="$(find "$TMP" -maxdepth 2 -name PACK-INFO.txt | head -1)"
[ -n "$INFO" ] && [ -f "$(dirname "$INFO")/setup-teste.sh" ] || { rm -rf "$TMP"; die "este zip não é um pack do PVN (falta PACK-INFO.txt)"; }
PACK="$(dirname "$INFO")"
ok "extraído"

title "3/4  Conferindo os arquivos"
if command -v sha256sum >/dev/null 2>&1; then
  total="$(sed -n '/^SHA-256/,$p' "$INFO" | tail -n +2 | grep -c .)"
  if (cd "$PACK" && sed -n '/^SHA-256/,$p' PACK-INFO.txt | tail -n +2 | sha256sum -c --quiet >/dev/null 2>&1); then
    ok "$total arquivos conferem com o SHA-256 do pack"
  else
    rm -rf "$TMP"
    die "algum arquivo não confere com o PACK-INFO.txt: o zip está corrompido. Baixe de novo."
  fi
else
  warn "sha256sum indisponível: pulando a conferência"
fi
sed -n 's/^\(commit\|controle\|jogo\): */\1 /p' "$INFO" | sed 's/^commit \(.......\).*/commit \1/' | while read -r k v; do ok "$k $v"; done
rm -rf "$DEST"
mv "$PACK" "$DEST"
rm -rf "$TMP"
ok "pack em $(short "$DEST")"

title "4/4  Instalando a versão do pack"
exec bash "$DEST/setup-teste.sh"
