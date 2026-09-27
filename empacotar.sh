#!/usr/bin/env bash
# Gera o pack zip de entrega a partir de um commit (padrão: HEAD).
#
#   bash empacotar.sh [pasta-destino] [commit] [tudo|td]
#
# tudo (padrão): o repositório daquele commit (sem .git), com os dois projetos
#   (source, legados, testes, docs) e o setup-teste.sh.
# td: só a pasta tower-defense/ inteira e o setup-teste.sh, que então instala
#   só o jogo.
# Os dois levam um PACK-INFO.txt com commit, versões e o SHA-256 de cada arquivo.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
DEST="${1:-dist}"
REF="${2:-HEAD}"
QUAL="${3:-tudo}"
case "$QUAL" in
  tudo) PATHS=() ;;
  td)   PATHS=(tower-defense setup-teste.sh) ;;
  *)    echo "pack desconhecido: $QUAL (use tudo ou td)" >&2; exit 1 ;;
esac

git rev-parse --verify --quiet "$REF^{commit}" >/dev/null || { echo "commit desconhecido: $REF" >&2; exit 1; }
TV="$(git show "$REF:controle-tv/source/VERSION" | tr -d '[:space:]')"
TD="$(git show "$REF:tower-defense/source/VERSION" | tr -d '[:space:]')"
SHA="$(git rev-parse --short "$REF")"
DATE="$(git log -1 --format=%cd --date=format:%Y%m%d "$REF")"
if [ "$QUAL" = td ]; then NAME="PVN-pack-${DATE}-td-${TD}-${SHA}"; else NAME="PVN-pack-${DATE}-controle-${TV}-td-${TD}-${SHA}"; fi
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"
ZIP="$DEST/$NAME.zip"

WORK="$(mktemp -d)"; INFO_DIR="$(mktemp -d)"; trap 'rm -rf "$WORK" "$INFO_DIR"' EXIT
INFO="$INFO_DIR/PACK-INFO.txt"  # fora da pasta varrida: o manifesto nao lista a si mesmo
git archive --format=tar "$REF" ${PATHS[@]+"${PATHS[@]}"} | tar -x -C "$WORK"
{
  if [ "$QUAL" = td ]; then echo "PVN pack · só o Tower Defense"; else echo "PVN pack"; fi
  echo "commit:   $(git rev-parse "$REF")"
  echo "data:     $(git log -1 --format=%cd --date=iso "$REF")"
  [ "$QUAL" = td ] || echo "controle: $TV"
  echo "jogo:     $TD"
  echo
  echo "Instalar no Termux (a partir desta pasta):  bash setup-teste.sh"
  echo
  echo "SHA-256 dos arquivos:"
  (cd "$WORK" && find . -type f | sort | sed 's#^\./##' | xargs -d '\n' sha256sum)
} > "$INFO"

rm -f "$ZIP"
git archive --format=zip --prefix="$NAME/" --add-file="$INFO" -o "$ZIP" "$REF" ${PATHS[@]+"${PATHS[@]}"}
echo "$ZIP"
