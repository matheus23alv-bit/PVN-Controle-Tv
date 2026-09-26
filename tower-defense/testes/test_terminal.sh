#!/usr/bin/env bash
# Testes de tela do Tower Defense 2 num terminal real (tmux). Uso: bash testes/test_terminal.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$(cd "$HERE/../source" && pwd)"
WORK="$(mktemp -d)"; trap 'tmux kill-session -t tdt 2>/dev/null; rm -rf "$WORK" "$SRC/__pycache__"' EXIT
pass=0; fail=0
check() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi; }
start() {  # start <col> <lin> <comando python> ; HOME isolado em $WORK/$HOMEX
  tmux kill-session -t tdt 2>/dev/null
  while tmux has-session -t tdt 2>/dev/null; do sleep .1; done
  tmux new-session -d -s tdt -x "$1" -y "$2" "cd '$SRC' && HOME='$WORK/${HOMEX:-h}' TERM=xterm-256color $3"
  sleep 1.2
}
screen() { tmux capture-pane -p -t tdt; }
row() { screen | sed -n "$1p"; }
alive() { tmux has-session -t tdt 2>/dev/null; }
tap() { tmux send-keys -t tdt -l $'\e'"[<0;$1;$2M"; tmux send-keys -t tdt -l $'\e'"[<0;$1;$2m"; sleep .45; }
key() { tmux send-keys -t tdt "$@"; sleep .4; }
cfg() { cat "$WORK/${HOMEX:-h}/.config/td-termux/config.json" 2>/dev/null; }
# casa (x,y) do mapa -> coluna/linha do terminal (1-based): x=2+2*cx, y=4+cy
cell() { tap $((2 + 2 * $1)) $((4 + $2)); }
FAST="python3 -c 'import td; td.START_LIFE=1; [v.update(speed=30) for v in td.ENEMIES.values()]; td.main([\"--jogar\"])'"

echo "== Menu (primeira vez)"
start 44 24 "python3 td.py"
check "Título e itens do menu" 'screen | grep -q "TOWER DEFENSE" && screen | grep -q "Como jogar" && screen | grep -q "Opções"'
check "Sugere o tutorial na primeira vez" 'screen | grep -q "Tutorial   (comece aqui)"'
check "Sem recorde ainda" 'screen | grep -q "Sem recorde ainda"'
check "Tutorial vem selecionado na primeira vez" 'screen | grep -q "▶  Tutorial"'
key Down Enter
check "Como jogar abre a ajuda" 'screen | grep -q "TORRES" && screen | grep -q "Vórtice"'
key x
check "Tecla volta ao menu" 'screen | grep -q "TOWER DEFENSE"'

echo "== Tutorial inteiro pelo toque"
tap 10 10
check "Passo 1 explica a entrada e a base" 'screen | grep -q "TUTORIAL 1/9"'
tap 10 21
check "Passo 2 pede o Mago" 'screen | grep -q "TUTORIAL 2/9"'
tap 19 2
check "Toque no seletor escolhe o Mago" 'screen | grep -q "TUTORIAL 3/9" && row 2 | grep -q "Mago"'
cell 12 3; cell 12 3
check "Dois toques na casa marcada constroem" 'screen | grep -q "TUTORIAL 4/9" && row 1 | grep -q "💰65"'
tap 20 21; sleep 1.5
check "Botão chama a onda e os monstros andam sozinhos" 'row 1 | grep -q "🌊1" && screen | grep -q "👾"'
for i in $(seq 1 30); do screen | grep -q "TUTORIAL 6/9" && break; sleep 1; done
check "Fim da onda avança o tutorial" 'screen | grep -q "TUTORIAL 6/9"'
tap 3 2; cell 4 5; cell 4 5
check "Arqueiro construído na segunda casa" 'screen | grep -q "TUTORIAL 7/9"'
cell 12 3; cell 12 3
check "Dois toques no Mago melhoram" 'screen | grep -q "TUTORIAL 8/9"'
tap 10 21; tap 10 21
check "Tutorial termina e começa a partida" 'screen | grep -q "Boa sorte" && row 1 | grep -q "🌊0"'
check "Tutorial fica marcado como visto" 'cfg | grep -q "\"tutorial_visto\": true"'

echo "== Partida pelo teclado"
key 2
key Right Right Enter
check "Enter constrói o Canhão escolhido" 'row 1 | grep -q "💰50" && screen | grep -q "💣"'
key u
check "u melhora a torre" 'screen | grep -q "nível 2" && row 1 | grep -q "💰15"'
key x
check "x vende devolvendo metade" 'screen | grep -q "vendido (+42)" && row 1 | grep -q "💰57"'
key n; sleep .3
check "n chama a onda" 'row 1 | grep -q "🌊1"'
key n
check "n durante a onda avisa" 'screen | grep -q "Aguarde o fim da onda"'
key f
check "f acelera (⏩ no topo)" 'row 1 | grep -q "⏩"'

echo "== Pausa pelo toque"
tap 5 1
check "Toque no topo abre a pausa" 'screen | grep -q "PAUSA" && screen | grep -q "Continuar"'
gold_before="$(row 1)"
cell 1 8; cell 1 8
check "Tocar no mapa com a pausa aberta não constrói" 'screen | grep -q "PAUSA" && [ "$(row 1)" = "$gold_before" ]'
key Enter
check "Continuar fecha a pausa" '! screen | grep -q "PAUSA"'
key q; key Down Down Enter
check "Menu principal pela pausa" 'screen | grep -q "TOWER DEFENSE" && ! screen | grep -q "(comece aqui)"'

echo "== Fim de jogo e recorde"
start 44 24 "$FAST"
key n; sleep 3
check "Base cai e mostra o placar" 'screen | grep -q "A BASE CAIU!" && screen | grep -q "Onda 1"'
check "Primeiro recorde é anunciado e salvo" 'screen | grep -q "Novo recorde" && cfg | grep -q "\"onda\": 1"'
key Enter
check "Jogar de novo reinicia" 'row 1 | grep -q "💗1 .*🌊0" && ! screen | grep -q "A BASE CAIU"'

echo "== Opções"
HOMEX=o start 44 24 "python3 td.py"
key Down Down Enter Enter
check "Emojis: NÃO troca por letras" 'screen | grep -q "Emojis: NÃO (letras)" && HOMEX=o cfg | grep -q "\"emoji\": false"'
key Down Down Down Enter
key Up Up Up Enter
check "Partida sem emoji desenha letras" 'screen | grep -q "S " && ! screen | grep -q "🚪"'

echo "== Tela e linha de comando"
start 36 15 "python3 td.py"
check "Tela pequena avisa com o mínimo" 'screen | grep -q "Tela pequena demais" && screen | grep -q "mínimo 38x17"'
key q; sleep .3
check "q sai da tela pequena" '! alive'
start 44 24 "python3 td.py --sem-emoji --jogar"
check "--sem-emoji e --jogar" 'screen | grep -q "B " && row 1 | grep -q "V:20"'
check "--versao lê o VERSION" '[ "$(cd "$SRC" && python3 td.py --versao)" = "$(cat "$SRC/VERSION")" ]'
check "--ajuda lista as opções" 'cd "$SRC" && python3 td.py --ajuda | grep -q -- "--tutorial"'

echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
