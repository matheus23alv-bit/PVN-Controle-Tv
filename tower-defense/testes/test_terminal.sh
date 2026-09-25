#!/usr/bin/env bash
# Testes de interface em terminal real (tmux). Uso: bash testes/test_terminal.sh [caminho/td.py]
set -u
TD="$(realpath "${1:-$(dirname "$0")/../source/td.py}")"
DIR="$(dirname "$TD")"
pass=0; fail=0

check() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi; }
start() { tmux kill-server 2>/dev/null; tmux new-session -d -s td -x "$1" -y "$2" "cd '$DIR' && TERM=xterm-256color ESCDELAY=25 ${3:-python3 td.py}"; sleep 1; }
screen() { tmux capture-pane -p -t td; }
alive() { tmux has-session -t td 2>/dev/null; }

# Termux em retrato (~40 colunas)
start 40 22
check "HUD completo em 40 colunas" 'screen | grep -q "Abates 0"'
check "Seletor de torres visivel" 'screen | grep -q "3:M \$35"'
check "Base B visivel no grid" 'screen | grep -q "B"'
check "Controles visiveis" 'screen | grep -q "p pausa  q sai"'
tmux send-keys -t td d d s Enter; sleep .3
check "Constroi torre" 'screen | grep -q "Arqueiro construida"'
tmux send-keys -t td n; sleep 2
check "Onda 1 inicia e inimigos aparecem" 'screen | head -1 | grep -q "Onda 1" && screen | grep -q "[o*]"'
tmux send-keys -t td p; sleep .3
check "Pausa" 'screen | grep -q "PAUSADO"'
tmux send-keys -t td p q; sleep .4
check "q pede confirmacao durante a partida" 'screen | grep -q "Sair do jogo" && alive'
tmux send-keys -t td n; sleep .3
check "n cancela a saida" 'alive && ! screen | grep -q "Sair do jogo"'
tmux send-keys -t td Escape; sleep .3; tmux send-keys -t td s; sleep .6
check "Esc + s encerra" '! alive'

# Tela menor que o minimo
start 32 14
check "Aviso de tela pequena" 'screen | grep -q "Tela pequena demais"'
tmux send-keys -t td q; sleep .5
check "q sai direto na tela pequena" '! alive'

# Fim de jogo e reinicio (vida reduzida so para o teste)
start 40 22 "python3 -c 'import td,curses; td.START_LIFE=1; curses.wrapper(td.main)'"
tmux send-keys -t td n; sleep 36
check "Game over quando a base cai" 'screen | grep -q "BASE DESTRUIDA"'
tmux send-keys -t td r; sleep .5
check "r reinicia com partida limpa" 'screen | grep -q "Nova partida" && ! screen | grep -q "BASE DESTRUIDA"'
tmux send-keys -t td q; sleep .5
check "q antes da primeira onda sai sem confirmar" '! alive'

tmux kill-server 2>/dev/null
rm -rf "$DIR/__pycache__"
echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
