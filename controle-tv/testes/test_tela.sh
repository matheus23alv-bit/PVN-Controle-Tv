#!/usr/bin/env bash
# Testa a tela do controle num terminal real (tmux), com emissor IR falso.
# Uso (na pasta controle-tv): bash testes/test_tela.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$(cd "$HERE/../source" && pwd)"
MOCK="$HERE/mock-termux-api"
WORK="$(mktemp -d)"; trap 'tmux kill-session -t tvt 2>/dev/null; rm -rf "$WORK" "$SRC/__pycache__"' EXIT
LOG="$WORK/ir.log"
pass=0; fail=0
check() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi; }
start() {  # start <colunas> <linhas> [variaveis extras] [argumentos]
  tmux kill-session -t tvt 2>/dev/null
  while tmux has-session -t tvt 2>/dev/null; do sleep .1; done
  tmux new-session -d -s tvt -x "$1" -y "$2" \
    "cd '$SRC' && HOME='$WORK/home' TV_MOCK_LOG='$LOG' PATH='${PATHX:-$MOCK:$PATH}' TERM=xterm-256color $3 python3 tv.py $4"
  sleep 1.2
}
screen() { tmux capture-pane -p -t tvt; }
line() { screen | sed -n "$1p"; }
last() { screen | tail -1; }
tap() { tmux send-keys -t tvt -l $'\e'"[<0;$1;$2M"; tmux send-keys -t tvt -l $'\e'"[<0;$1;$2m"; sleep .5; }
key() { tmux send-keys -t tvt "$@"; sleep .5; }
sent() { tail -1 "$LOG" 2>/dev/null; }
alive() { tmux has-session -t tvt 2>/dev/null; }
mkdir -p "$WORK/home"

echo "== Primeira abertura (celular retrato 44x40)"
start 44 40 "" ""
check "Pede a marca da TV" 'screen | grep -q "Qual é a marca da sua TV?"'
check "Mostra emissor pronto" 'line 2 | grep -q "emissor IR pronto (30-60 kHz)"'
check "Explica como usar outras marcas" 'screen | grep -q "tv --importar arquivo.ir"'
tap 5 6
check "Toque escolhe Samsung e abre o controle" 'line 1 | grep -q "TV: Samsung" && screen | grep -q "LIGAR"'
check "Escolha fica salva" 'grep -q Samsung "$WORK/home/.config/pvn-tv/config.json"'

echo "== Envio pelo toque e pelo teclado"
tap 5 5
check "Toque em LIGAR transmite o código Samsung" '[[ "$(sent)" == "-f 38000 4500,4500,560,1690,560,1690,560,1690,560,560"* ]]'
check "Rodapé confirma o envio logo após o toque" 'last | grep -q "✓ Ligar/desligar enviado (38 kHz)"'
key +
check "Tecla + envia VOL +" 'last | grep -q "✓ Volume + enviado" && [ "$(wc -l < "$LOG")" -eq 2 ]'
key 7
check "Tecla 7 envia o dígito 7" 'last | grep -q "Dígito 7 enviado"'
tap 20 11
check "Toque no OK envia OK" 'last | grep -q "✓ OK enviado"'

echo "== Trocar de TV"
key t
check "t abre a escolha de TV" 'screen | grep -q "Qual é a marca"'
key Down Enter
check "Setas e Enter escolhem outra TV" 'line 1 | grep -q "TV: LG"'
key l
check "LG usa o protocolo NEC" '[[ "$(sent)" == "-f 38000 9000,4500,"* ]]'

echo "== Botão sem código"
key t; key Down Enter
n0=$(wc -l < "$LOG")
tap 5 17
check "Sony sem VOLTAR avisa e não transmite" 'last | grep -q "não tem esse código" && [ "$(wc -l < "$LOG")" -eq "$n0" ]'
key l
check "Sony transmite a 40 kHz" '[[ "$(sent)" == "-f 40000 2400,600,"* ]]'

echo "== Descobrir TV"
key d
check "Descobrir envia o LIGAR da primeira marca" 'screen | grep -q "Descobrir TV  1 de 3" && [[ "$(sent)" == "-f 38000 4500,4500"* ]]'
key n
check "n passa para a próxima marca" 'screen | grep -q "2 de 3" && [[ "$(sent)" == "-f 38000 9000,4500"* ]]'
tap 5 12
check "Toque em SIM escolhe a marca" 'line 1 | grep -q "TV: LG"'

echo "== Ajuda e saída"
key ?
check "? mostra a ajuda" 'screen | grep -q "Aponte o topo do celular para a TV"'
key x
check "Qualquer tecla volta ao controle" 'screen | grep -q "LIGAR"'
key q; sleep .3
check "q sai" '! alive'

echo "== Situações de erro"
start 44 40 "TV_MOCK_SEM_IR=1" ""
check "Celular sem emissor é avisado" 'line 2 | grep -q "não tem emissor infravermelho"'
PATHX="/usr/bin:/bin" start 44 40 "" ""
check "Sem termux-api orienta a instalar" 'line 2 | grep -q "pkg install termux-api"'
key l; sleep .5
check "Botão sem termux-api mostra o erro" 'last | grep -q "✗ Ligar/desligar: Instale o pacote"'
start 44 40 "" "--simular"
check "Modo simulado identificado" 'line 2 | grep -q "modo simulado"'
start 28 14 "" ""
check "Tela pequena avisa" 'screen | grep -q "Tela pequena demais"'
start 44 20 "" ""
check "Tela baixa usa botões de 1 linha" 'screen | grep -q "\[   LIGAR    \]"'

echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
