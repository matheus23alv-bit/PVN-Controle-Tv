#!/usr/bin/env bash
# Testes de interface em terminal real (tmux). Uso: bash testes/test_terminal.sh [caminho/td.py]
set -u
TD="$(realpath "${1:-$(dirname "$0")/../source/td.py}")"
DIR="$(dirname "$TD")"
pass=0; fail=0

check() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi; }
# encerra so a sessao e espera ela sumir: matar o servidor e abrir outro em seguida gera corrida no tmux
start() {
  tmux kill-session -t td 2>/dev/null
  while tmux has-session -t td 2>/dev/null; do sleep .1; done
  tmux new-session -d -s td -x "$1" -y "$2" "cd '$DIR' && TERM=xterm-256color ${3:-python3 td.py}"
  sleep 1
}
screen() { tmux capture-pane -p -t td; }
row() { screen | sed -n "$1p"; }
alive() { tmux has-session -t td 2>/dev/null; }
tap() { tmux send-keys -t td -l $'\e'"[<0;$1;$2M"; tmux send-keys -t td -l $'\e'"[<0;$1;$2m"; sleep .25; }
# inimigos rapidos e 1 de vida: fim de jogo em poucos segundos
FAST="python3 -c 'import td; td.START_LIFE=1; [v.update(speed=25) for v in td.ENEMY_BASE.values()]; td.main([])'"

echo "== Termux em retrato (40x22)"
start 40 22
check "HUD completo" 'row 1 | grep -q "Vida 20 Ouro 120 Onda 0 Abates 0"'
check "Seletor de torres" 'row 2 | grep -q "1:A \$20  2:C \$50  3:M \$35  Arqueiro"'
check "Grid inteiro com a base B" 'screen | grep -q "################B"'
check "Controles visiveis" 'screen | grep -q "p pausa  h ajuda  q sai"'
check "Dica da proxima onda" 'screen | grep -q "n ou toque aqui"'
tmux send-keys -t td d d s Enter; sleep .3
check "Constroi torre pelo teclado" 'screen | grep -q "Arqueiro construida"'
tmux send-keys -t td n; sleep 1.5
check "Onda 1 com inimigos" 'row 1 | grep -q "Onda 1" && screen | grep -q "[o*]"'
tmux send-keys -t td n; sleep .2
check "n durante a onda avisa" 'screen | grep -q "Aguarde o fim da onda"'
tmux send-keys -t td p; sleep .2
check "Pausa" 'screen | grep -q "PAUSADO"'
tmux send-keys -t td a Enter; sleep .2
check "Pausado nao constroi" 'row 1 | grep -q "Ouro 100"'
tmux send-keys -t td p q; sleep .3
check "q pede confirmacao" 'screen | grep -q "Sair? q = sim" && alive'
tmux send-keys -t td s; sleep .3
check "s (descer) cancela a saida em vez de sair" 'alive && ! screen | grep -q "Sair?"'
tmux send-keys -t td h; sleep .3
check "h abre a ajuda" 'screen | grep -q "AJUDA  Tower Defense v"'
tmux send-keys -t td x; sleep .3
check "Qualquer tecla fecha a ajuda" '! screen | grep -q "AJUDA"'
tmux send-keys -t td Escape; sleep .2; tmux send-keys -t td Escape; sleep .5
check "Esc duas vezes encerra" '! alive'

echo "== Entrada rapida"
start 40 22
tmux send-keys -t td d d d d d d d d d d d d d d d d d d d d d d d d d d d d d d Enter; sleep .3
check "30 teclas + Enter processadas em 300 ms" 'screen | grep -q "Arqueiro construida" && row 10 | grep -q "A$"'

echo "== Toque na tela"
start 40 22
tap 6 8; tap 6 8
check "2 toques na mesma celula constroem" 'row 8 | grep -q "^.....A" && screen | grep -q "Arqueiro construida"'
tap 21 2
check "Toque no seletor escolhe o Mago" 'row 2 | grep -q "Mago$"'
tap 5 17; sleep 1
check "Toque no rodape chama a onda" 'row 1 | grep -q "Onda 1"'

echo "== Tela compacta e tela pequena"
start 32 16
check "32x16 mostra HUD compacto" 'row 1 | grep -q "Vida 20 \$120 Onda 0 Abt 0"'
check "32x16 mostra o grid inteiro e o rodape" 'screen | grep -q "B" && row 16 | grep -q "n ou toque aqui"'
start 31 15
check "Abaixo de 32x16 avisa e orienta" 'screen | grep -q "Tela pequena demais" && screen | grep -q "Esconda o teclado"'
tmux send-keys -t td q; sleep .4
check "q sai da tela pequena" '! alive'

echo "== Fim de jogo"
start 40 22 "$FAST"
tmux send-keys -t td n; sleep 5
check "Base cai e mostra a onda" 'screen | grep -q "Base caiu na onda 1"'
tap 5 17
check "Toque no rodape reinicia" 'screen | grep -q "Nova partida" && row 1 | grep -q "Vida 1 .*Onda 0"'
tmux send-keys -t td n; sleep 5; tmux send-keys -t td r; sleep .3
check "r reinicia" 'screen | grep -q "Nova partida" && ! screen | grep -q "Base caiu"'
tmux send-keys -t td q; sleep .4
check "q antes da 1a onda sai direto" '! alive'

echo "== Linha de comando"
check "--versao le o arquivo VERSION" '[ "$(cd "$DIR" && python3 td.py --versao)" = "$(cat "$DIR/VERSION")" ]'
check "--ajuda lista as opcoes" 'cd "$DIR" && python3 td.py --ajuda | grep -q -- "--sem-toque"'
start 40 22 "python3 td.py --sem-toque"
tap 6 8; tap 6 8
check "--sem-toque ignora toques" '! screen | grep -q "construida"'

tmux kill-session -t td 2>/dev/null
rm -rf "$DIR/__pycache__"
echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
