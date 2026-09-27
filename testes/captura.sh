#!/usr/bin/env bash
# Captura a tela de uma sessão do tmux em PNG, para revisar o visual dos dois projetos.
#   bash testes/captura.sh <sessão-tmux> <nome> [colunas] [pasta]
# Ex.: tmux new-session -d -s v -x 46 -y 50 "python3 tower-defense/source/td.py"
#      bash testes/captura.sh v menu 46      ->  capturas/menu.png
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SESSION="${1:?informe a sessão do tmux}"; NAME="${2:?informe o nome da imagem}"
COLS="${3:-46}"; OUT="${4:-capturas}"
mkdir -p "$OUT"
tmux capture-pane -e -N -p -t "$SESSION" > "$OUT/$NAME.ans"
python3 "$HERE/term2png.py" "$OUT/$NAME.ans" "$OUT/$NAME.png" "$COLS" >/dev/null
rm -f "$OUT/$NAME.ans" "$OUT/$NAME.html"
echo "$OUT/$NAME.png"
