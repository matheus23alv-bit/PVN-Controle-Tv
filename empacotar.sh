#!/usr/bin/env bash
# Gera o pack zip de entrega a partir de um commit (padrão: HEAD).
#
#   bash empacotar.sh [pasta-destino] [commit]
#
# Sai um PVN-pack-<data>-controle-<versão>-teclado-<versão>-<commit>.zip com o
# repositório daquele commit (sem .git): os projetos (source, legados, testes,
# docs) e o setup-teste.sh, mais um PACK-INFO.txt com commit, versões e o
# SHA-256 de cada arquivo.
#
# O Tower Defense saiu deste repositório: ele agora tem o dele,
# matheus23alv-bit/TOWER-DEFENSE---TERMUX-, com empacotar.sh próprio.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
DEST="${1:-dist}"
REF="${2:-HEAD}"

git rev-parse --verify --quiet "$REF^{commit}" >/dev/null || { echo "commit desconhecido: $REF" >&2; exit 1; }
TV="$(git show "$REF:controle-tv/source/VERSION" | tr -d '[:space:]')"
TK="$(git show "$REF:teclado-termux/source/VERSION" | tr -d '[:space:]')"
SHA="$(git rev-parse --short "$REF")"
DATE="$(git log -1 --format=%cd --date=format:%Y%m%d "$REF")"
NAME="PVN-pack-${DATE}-controle-${TV}-teclado-${TK}-${SHA}"
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"
ZIP="$DEST/$NAME.zip"

WORK="$(mktemp -d)"; INFO_DIR="$(mktemp -d)"; trap 'rm -rf "$WORK" "$INFO_DIR"' EXIT
INFO="$INFO_DIR/PACK-INFO.txt"  # fora da pasta varrida: o manifesto nao lista a si mesmo
git archive --format=tar "$REF" | tar -x -C "$WORK"
{
  echo "PVN pack · controle da TV e Teclado Termux"
  echo "commit:   $(git rev-parse "$REF")"
  echo "data:     $(git log -1 --format=%cd --date=iso "$REF")"
  echo "controle: $TV"
  echo "teclado:  $TK"
  echo
  echo "Instalar no Termux (a partir desta pasta):  bash setup-teste.sh"
  echo
  echo "SHA-256 dos arquivos:"
  (cd "$WORK" && find . -type f | sort | sed 's#^\./##' | xargs -d '\n' sha256sum)
} > "$INFO"

rm -f "$ZIP"
git archive --format=zip --prefix="$NAME/" --add-file="$INFO" -o "$ZIP" "$REF"
echo "$ZIP"
