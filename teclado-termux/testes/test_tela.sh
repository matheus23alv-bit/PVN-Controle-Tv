#!/usr/bin/env bash
# Testa o menu do teclas num terminal real (tmux), como no Termux, com um termux-reload-settings falso.
# Uso (na pasta teclado-termux): bash testes/test_tela.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$(cd "$HERE/../source" && pwd)"
WORK="$(mktemp -d)"; trap 'tmux kill-session -t tkt 2>/dev/null; rm -rf "$WORK" "$SRC/__pycache__"' EXIT
pass=0; fail=0
check() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi; }
mkdir -p "$WORK/bin" "$WORK/home"
printf '#!/bin/sh\necho r >> "%s/recargas"\n' "$WORK" > "$WORK/bin/termux-reload-settings"; chmod +x "$WORK/bin/termux-reload-settings"
P="$WORK/home/.termux/termux.properties"
start() {  # start <colunas> <linhas>
  tmux kill-session -t tkt 2>/dev/null
  while tmux has-session -t tkt 2>/dev/null; do sleep .1; done
  tmux new-session -d -s tkt -x "$1" -y "$2" \
    "cd '$SRC' && HOME='$WORK/home' TERMUX_VERSION=0.118 PATH='$WORK/bin:$PATH' TERM=xterm-256color python3 teclas.py"
  sleep 1.2
}
screen() { tmux capture-pane -p -t tkt; }
last() { screen | tail -1; }
row() { screen | grep -n -F "$1" | head -1 | cut -d: -f1; }   # linha (1 = topo) onde o texto aparece
tap() { tmux send-keys -t tkt -l $'\e'"[<0;$1;$2M"; tmux send-keys -t tkt -l $'\e'"[<0;$1;$2m"; sleep .7; }
key() { tmux send-keys -t tkt "$@"; sleep .6; }
alive() { tmux has-session -t tkt 2>/dev/null; }

echo "== Primeira abertura (celular em pé, 46x50)"
start 46 50
check "Mostra a barra atual" 'screen | grep -q "Agora: Padrão do Termux"'
check "Quatro escolhas; sem barra própria, não mostra A sua de antes" 'screen | grep -q "4  Padrão do Termux" && ! screen | grep -q "A sua de antes"'
check "Marca a barra atual" 'screen | grep "Padrão do Termux" | grep -q "✔"'
check "Prévia da barra selecionada" 'screen | grep -q "Prévia:" && screen | grep -q "PGUP"'
check "Troca automática ligada de início" 'screen | grep -q "Troca automática: SIM"'

echo "== Escolher pelo toque e pelo teclado"
tap 5 "$(row "Controle da TV")"
check "Toque aplica a barra da TV" 'grep -q "^# teclas: tv" "$P" && [ -s "$WORK/recargas" ]'
check "Confirma e atualiza a tela" 'last | grep -q "✔ Controle da TV; o Termux recarregou" && screen | grep -q "Agora: Controle da TV"'
check "Prévia mostra VOL+ e VOL-" 'screen | grep -q "VOL+" && screen | grep -q "VOL-"'
key 1
check "Tecla 1 aplica o padrão melhorado" 'grep -q "^# teclas: melhorado" "$P" && screen | grep -q "Agora: Padrão melhorado"'
check "Prévia do melhorado com os atalhos" 'screen | grep -q "📺" && screen | grep -q "🏰"'
key Down
key Enter
check "Setas e Enter aplicam o jogo" 'grep -q "^# teclas: jogo" "$P" && screen | grep -q "🏹"'

echo "== Troca automática"
key a
check "Tecla a desliga" 'screen | grep -q "Troca automática: NÃO" && grep -q "\"auto\": false" "$WORK/home/.config/teclas/estado.json"'
check "Explica que o tv e o td não mexem" 'screen | grep -q "tv e td não mexem na barra"'
tap 5 "$(row "Troca automática")"
check "Toque liga de novo" 'screen | grep -q "Troca automática: SIM" && grep -q "\"auto\": true" "$WORK/home/.config/teclas/estado.json"'

echo "== Tela pequena (teclado aberto) e sair"
tmux resize-window -t tkt -x 46 -y 20; sleep .6
check "Com 20 linhas mostra escolhas e estado" 'screen | grep -q "4  Padrão do Termux" && screen | grep -q "Troca automática"'
tmux resize-window -t tkt -x 28 -y 10; sleep .6
check "Menor que 30x12 pede mais espaço" 'screen | grep -q "Tela pequena demais"'
tmux resize-window -t tkt -x 46 -y 50; sleep .6
check "Volta ao menu ao crescer" 'screen | grep -q "Agora: Jogo"'
key q
check "q sai" '! alive'

echo "== Com barra própria"
rm -rf "$WORK/home/.termux" "$WORK/home/.config"
mkdir -p "$WORK/home/.termux"
printf '%s\n' "extra-keys = [['ESC','TAB','CTRL','ALT']]" "use-black-ui = true" > "$P"
cp "$P" "$WORK/original"
start 46 50
check "Mostra A sua de antes, marcada como atual" 'screen | grep -q "Agora: A sua de antes" && screen | grep "5  A sua de antes" | grep -q "✔"'
key 3
key 5
check "Voltar à sua devolve o arquivo byte a byte" 'cmp -s "$WORK/original" "$P" && screen | grep -q "Agora: A sua de antes"'
key Escape
check "Esc sai" '! alive'

echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
