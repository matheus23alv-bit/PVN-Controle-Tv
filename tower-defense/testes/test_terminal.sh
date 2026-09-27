#!/usr/bin/env bash
# Testes de tela do Tower Defense 3 num terminal real (tmux), em retrato de celular.
# Uso: bash testes/test_terminal.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$(cd "$HERE/../source" && pwd)"
WORK="$(mktemp -d)"; trap 'tmux kill-session -t tdt 2>/dev/null; rm -rf "$WORK" "$SRC/__pycache__" "$HERE/__pycache__"' EXIT
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
click() { tmux send-keys -t tdt -l $'\e'"[<0;$1;$2M"; tmux send-keys -t tdt -l $'\e'"[<0;$1;$2m"; sleep .45; }
tap() {  # tap "TEXTO" [n]: toca no meio do texto na tela
  local pos; pos="$(python3 "$HERE/tela.py" achar "$@")" || { echo "      (não achei '$1' na tela)"; return 1; }
  click $pos
}
cell() { click $(python3 "$HERE/tela.py" casa "$@"); }   # cell X Y [LxA]: toca na casa do mapa
key() { tmux send-keys -t tdt "$@"; sleep .4; }
cfg() { cat "$WORK/${HOMEX:-h}/.config/td-termux/config.json" 2>/dev/null; }
wait_for() { for _ in $(seq 1 "$2"); do screen | grep -q "$1" && return 0; sleep 1; done; return 1; }
FAST="python3 -c 'import td; td.START_LIFE=1; [v.update(speed=30) for v in td.ENEMIES.values()]; td.main([\"--jogar\"])'"
MAGE="6 3"; ARCHER="3 3"   # casas do tutorial no mapa Serpente (td.tutorial_spots)

echo "== Menu (primeira vez), retrato 46x50"
start 46 50 "python3 td.py"
check "Título e itens do menu" 'screen | grep -q "TOWER DEFENSE" && screen | grep -q "Criar mapa" && screen | grep -q "Mapas"'
check "Tutorial selecionado e sugerido na primeira vez" 'screen | grep -q "▶ 🎓 Tutorial" && screen | grep -q "comece aqui"'
check "Mapa atual aparece no Jogar" 'screen | grep -q "mapa Serpente"'
tap "Como jogar"
check "Como jogar mostra torres e monstros novos" 'screen | grep -q "TORRES" && screen | grep -q "Fantasma" && screen | grep -q "Tartaruga"'
key NPage NPage NPage
check "Ajuda explica o editor e o arquivo .mapa" 'screen | grep -q "ARQUIVO .mapa" || screen | grep -q "CRIAR MAPAS"'
key x
check "Tecla volta ao menu" 'screen | grep -q "TOWER DEFENSE"'

echo "== Tutorial inteiro pelo toque"
tap "Tutorial"
check "Passo 1 explica a entrada e a base" 'screen | grep -q "TUTORIAL 1/9"'
check "Tela cheia: placar no topo, barras de torres e ações embaixo" 'row 1 | grep -q "💗20" && row 49 | grep -q "▶ Onda 1" && screen | grep -q "Vórtice"'
tap "Toque aqui"
check "Passo 2 pede o Mago" 'screen | grep -q "TUTORIAL 2/9"'
tap "Mago" 2
check "Toque na barra de torres escolhe o Mago" 'screen | grep -q "TUTORIAL 3/9"'
cell $MAGE; cell $MAGE
check "Dois toques na casa marcada constroem" 'screen | grep -q "TUTORIAL 4/9" && row 1 | grep -q "💰65" && screen | grep -q "🔮"'
tap "▶ Onda 1"; sleep 1.5
check "Botão chama a onda e os monstros andam sozinhos" 'row 1 | grep -q "🌊1" && screen | grep -q "👾"'
tap "1x"
check "⏩ acelera para 2x" 'row 1 | grep -q "⏩" && screen | grep -q "2x"'
check "Fim da onda avança o tutorial" 'wait_for "TUTORIAL 6/9" 60'
tap "Arqueiro" 2; cell $ARCHER; cell $ARCHER
check "Arqueiro construído na segunda casa" 'screen | grep -q "TUTORIAL 7/9" && screen | grep -q "🏹"'
cell $MAGE; cell $MAGE
check "Dois toques no Mago melhoram (estrela de nível)" 'screen | grep -q "TUTORIAL 8/9" && screen | grep -q "★"'
tap "Toque aqui"; tap "Toque aqui"
check "Tutorial termina e começa a partida" 'screen | grep -q "Boa sorte" && row 1 | grep -q "🌊0"'
check "Tutorial fica marcado como visto" 'cfg | grep -q "\"tutorial_visto\": true"'

echo "== Partida pelo teclado"
key 2
key Right Right Enter
check "Enter constrói o Canhão escolhido" 'row 1 | grep -q "💰50" && screen | grep -q "💣"'
check "Barra mostra melhorar e vender da torre do cursor" 'screen | grep -q "⏫35" && screen | grep -q "💲+25"'
key u
check "u melhora a torre" 'screen | grep -q "nível 2" && row 1 | grep -q "💰15"'
key x
check "x vende devolvendo metade" 'screen | grep -q "vendido (+42)" && row 1 | grep -q "💰57"'
check "Prévia da próxima onda" 'row 2 | grep -q "Próxima onda 1: 👾"'
key n; sleep .3
check "n chama a onda" 'row 1 | grep -q "🌊1" && row 2 | grep -q "Onda 1: faltam"'
key n
check "n durante a onda avisa" 'screen | grep -q "Aguarde o fim da onda"'

echo "== Pausa pelo toque"
tap "||"
check "|| abre a pausa com o nome do mapa" 'screen | grep -q "PAUSA" && screen | grep -q "Mapa: Serpente"'
gold_before="$(row 1)"
cell 0 9; cell 0 9
check "Tocar no mapa com a pausa aberta não constrói" 'screen | grep -q "PAUSA" && [ "$(row 1)" = "$gold_before" ]'
key Enter
check "Continuar fecha a pausa" '! screen | grep -q "PAUSA"'
key h
check "h abre a ajuda no meio da partida" 'screen | grep -q "COMO JOGAR"'
key x
check "Sair da ajuda volta para a pausa, com o jogo parado" 'screen | grep -q "PAUSA"'
key Enter
key q; key q
check "Menu principal pela pausa" 'screen | grep -q "TOWER DEFENSE" && ! screen | grep -q "comece aqui"'

echo "== Mapas"
tap "Mapas"
check "Lista os prontos e a seção dos seus" 'screen | grep -q "PRONTOS" && screen | grep -q "Espiral" && screen | grep -q "Rio" && screen | grep -q "nenhum ainda"'
check "Prévia e tamanho da trilha" 'screen | grep -q "▀\|  " && screen | grep -q "Trilha com 66 casas"'
tap "Espiral"
check "Toque escolhe o mapa" 'screen | grep -q "▶ Espiral" && screen | grep -q "Trilha com 65 casas"'
tap "Espiral"
check "Segundo toque joga nele" 'row 1 | grep -q "💗20" && ! screen | grep -q "PRONTOS"'
check "Mapa escolhido fica salvo" 'cfg | grep -q "\"mapa\": \"pronto:espiral\""'
key q; key q
check "Menu mostra o mapa escolhido" 'screen | grep -q "mapa Espiral"'

echo "== Criador de mapas"
tap "Criar mapa"
check "Editor abre vazio pedindo a entrada" 'screen | grep -q "EDITOR · Meu mapa 1" && screen | grep -q "Falta a entrada"'
cell 1 0
check "Entrada posta liga a ferramenta Trilha" 'screen | grep -q "🚪" && screen | grep -q "Falta a base"'
cell 1 5; cell 8 5; cell 8 12; sleep 1.5
check "Cantos da trilha: a reta é preenchida" 'screen | grep -q "Falta a base" && screen | grep -q "a partir do laranja"'
tap "Base"; cell 8 16
check "Base alinhada fecha a trilha" 'screen | grep -q "✔ Pronto para jogar: trilha com 24 casas" && screen | grep -q "🏰"'
tap "Desfazer"
check "Desfazer volta um passo" 'screen | grep -q "Falta a base"'
cell 8 16
check "Refazer a base" 'screen | grep -q "trilha com 24 casas"'
tap "Grama"; cell 8 8
check "Grama no meio da trilha mostra o erro com a posição" 'screen | grep -q "Trilha sem saída em col 9, lin 8"'
tap "Trilha" 2; cell 8 8
check "Trilha conserta" 'screen | grep -q "trilha com 24 casas"'
tap "Testar"
check "Testar joga o mapa na hora" 'row 1 | grep -q "💗20" && screen | grep -q "Voltar ao editor\|volta ao editor"'
tap "||"
check "Pausa do teste volta ao editor" 'screen | grep -q "Voltar ao editor"'
tap "Voltar ao editor"
check "Editor preservado depois do teste" 'screen | grep -q "EDITOR · Meu mapa 1 \*" && screen | grep -q "trilha com 24 casas"'
tap "Salvar"
check "Salvar pede o nome" 'screen | grep -q "Nome do mapa" && screen | grep -q "Meu mapa 1"'
key BSpace BSpace BSpace BSpace BSpace BSpace BSpace BSpace BSpace BSpace
tmux send-keys -t tdt -l "Trilha Ágil"; sleep .4
key Enter
check "Nome com acento é salvo em arquivo .mapa" 'screen | grep -q "Salvo: Trilha Ágil" && grep -q "nome: Trilha Ágil" "$WORK/h/.config/td-termux/mapas/trilha-agil.mapa"'
tap "Gerar"
check "Gerar cria um mapa aleatório pronto para jogar" 'screen | grep -q "Mapa gerado (semente\|Gerado (semente" && screen | grep -q "✔ Pronto para jogar"'
key q
check "q abre o menu do editor" 'screen | grep -q "Sair do editor" && screen | grep -q "Tamanho 11×19"'
tap "Sair do editor"
check "Sair com mudanças pergunta antes" 'screen | grep -q "Sair sem salvar?"'
tap "Sair sem salvar" 2
check "Volta ao menu" 'screen | grep -q "TOWER DEFENSE"'
tap "Mapas"
check "Mapa salvo aparece em Meus mapas" 'screen | grep -q "MEUS MAPAS" && screen | grep -q "Trilha Ágil"'
tap "Trilha Ágil"; tap "Apagar"
check "Apagar pede confirmação" 'screen | grep -q "Apagar Trilha Ágil?"'
tap "Apagar" 2
check "Apagar remove o arquivo" '[ ! -e "$WORK/h/.config/td-termux/mapas/trilha-agil.mapa" ] && screen | grep -q "nenhum ainda"'

echo "== Combate 3.1: mira, painel, nível 3, faixas, vibração"
mkdir -p "$WORK/vib"; printf '#!/bin/sh\necho "$@" >> "%s/vib/log"\n' "$WORK" > "$WORK/vib/termux-vibrate"; chmod +x "$WORK/vib/termux-vibrate"
BOSS="python3 -c 'import td; td.START_GOLD=500; td.START_LIFE=2; td.make_wave=lambda n, rng: [\"chefe\"]; td.ENEMIES[\"chefe\"].update(speed=6); td.main([\"--jogar\"])'"
HOMEX=c start 46 50 "PATH='$WORK/vib':\$PATH $BOSS"
key 2 Right Right Enter; sleep 2.1
check "Painel da torre mostra dano por segundo, abates e mira" 'screen | grep -q "Canhão nv1 · 14/s · 💀0 · mira 1º"'
tap "Mira"
check "🎯 troca a mira da torre" 'screen | grep -q "Canhão mira: o de mais vida" && screen | grep -q "🎯 forte"'
key t
check "t também troca a mira" 'screen | grep -q "mira: o mais perto"'
key u u
check "Nível 3 anuncia a habilidade" 'screen | grep -q "Canhão nível 3: explosão maior" && screen | grep -q "★★"'
key n; sleep .4
check "Faixa da onda e do chefe no meio do mapa" 'screen | grep -q "ONDA 1\|CHEFE CHEGOU"'
sleep 1
check "Barra de vida do chefe no topo" 'row 2 | grep -q "🐉" && row 2 | grep -q "%"'
for i in $(seq 1 12); do [ -s "$WORK/vib/log" ] && grep -q "70" "$WORK/vib/log" && break; sleep 1; done
check "Vibra quando o chefe chega e quando um monstro entra na base" 'grep -q "^-d 250" "$WORK/vib/log" && grep -q "^-d 70" "$WORK/vib/log"'
start 30 26 "python3 -c 'import td; td.START_GOLD=17264000; td.main([\"--jogar\"])'"
check "Placar compacto numa tela de 30 colunas" 'row 1 | grep -q "💰17M" && row 1 | grep -q "||"'

echo "== Fim de jogo e recorde"
HOMEX=f start 46 50 "$FAST"
key n; sleep 3
check "Base cai e mostra o placar" 'screen | grep -q "A BASE CAIU!" && screen | grep -q "Onda 1"'
check "Recorde por mapa é anunciado e salvo" 'screen | grep -q "Novo recorde em Serpente" && HOMEX=f cfg | grep -q "\"onda\": 1"'
key Enter
check "Jogar de novo reinicia" 'row 1 | grep -q "💗1 .*🌊0" && ! screen | grep -q "A BASE CAIU"'

echo "== Opções e modo sem emoji"
HOMEX=o start 46 50 "python3 td.py"
tap "Opções"; key Enter
check "Emojis: NÃO troca por letras" 'screen | grep -q "Emojis: NÃO (letras)" && HOMEX=o cfg | grep -q "\"emoji\": false"'
key q; tap "Jogar"
check "Partida sem emoji desenha letras" 'screen | grep -q "S " && ! screen | grep -q "🚪" && row 1 | grep -q "V:20"'

echo "== Opções 3.1 e Ajustar tela"
HOMEX=t start 46 50 "TERMUX_VERSION=0.118 python3 td.py"
tap "Opções"; tap "Números de dano"
check "Números de dano desliga e fica salvo" 'screen | grep -q "Números de dano: NÃO" && HOMEX=t cfg | grep -q "\"numeros\": false"'
tap "Vibrar"
check "Vibrar desliga e fica salvo" 'screen | grep -q "Vibrar: NÃO" && HOMEX=t cfg | grep -q "\"vibrar\": false"'
tap "Ajustar tela"
check "Ajustar tela mostra tamanho, escala e régua" 'screen | grep -q "Sua tela: 46 colunas × 50 linhas" && screen | grep -q "escala 2" && screen | grep -q "RÉGUA" && screen | grep -q "|🏹|💣|"'
tap "Ativar tela cheia"; sleep 1
check "Botão ativa a tela cheia do Termux" 'screen | grep -q "tela cheia ativada" && grep -q "^fullscreen = true" "$WORK/t/.termux/termux.properties"'
tap "Instalar a fonte"; sleep 1
check "Botão instala a fonte do jogo" 'screen | grep -q "Fonte: SIM\|Fonte do jogo: SIM" && cmp -s "$SRC/fontes/DejaVuSansMono.ttf" "$WORK/t/.termux/font.ttf"'
tap "Tirar a fonte"; sleep 1
check "E tira a fonte de novo" '[ ! -e "$WORK/t/.termux/font.ttf" ]'

echo "== Tamanhos de tela"
start 32 26 "python3 td.py --jogar"
check "Tela menor usa escala 1 e ainda cabe tudo" 'row 1 | grep -q "💗20" && screen | grep -q "▶ Onda 1\|▶ 1" && screen | grep -q "🚪" && screen | grep -q "🎯"'
cell 5 9; cell 5 9
check "Toque em escala 1 constrói" 'row 1 | grep -q "💰80"'
start 28 15 "python3 td.py"
check "Tela pequena avisa com o mínimo" 'screen | grep -q "Tela pequena demais" && screen | grep -q "mínimo 30x12"'
key q; sleep .3
check "q sai da tela pequena" '! alive'

echo "== Auditoria: Ctrl+C, tela pequena no editor, gerador em mapa estreito"
tmux kill-session -t tdt 2>/dev/null; while tmux has-session -t tdt 2>/dev/null; do sleep .1; done
tmux new-session -d -s tdt -x 46 -y 50 "cd '$SRC' && HOME='$WORK/cc' TERM=xterm-256color python3 td.py --jogar 2> '$WORK/cc.err'; echo \$? > '$WORK/cc.code'; sleep 3"
sleep 1.2; tmux send-keys -t tdt C-c; sleep 1
check "Ctrl+C sai limpo, sem erro na tela" '[ "$(cat "$WORK/cc.code" 2>/dev/null)" = 130 ] && ! grep -q Traceback "$WORK/cc.err"'
start 46 50 "python3 td.py --editor"
cell 1 0
tmux resize-window -t tdt -x 46 -y 18 2>/dev/null; sleep .6
check "Tela pequena no editor avisa do mapa sem salvar" 'screen | grep -q "Mapa sem salvar"'
key q; sleep .3
check "q não fecha o editor com mudanças sem salvar" 'alive && screen | grep -q "Mapa sem salvar"'
tmux resize-window -t tdt -x 46 -y 50 2>/dev/null; sleep .6
check "Ao crescer, o editor volta com o desenho" 'screen | grep -q "EDITOR" && screen | grep -q "🚪"'
check "--gerar funciona em mapa de 5 casas" '(cd "$SRC" && python3 td.py --gerar 5x5 1) | grep -q "^####B$"'

echo "== Linha de comando"
check "--versao lê o VERSION" '[ "$(cd "$SRC" && python3 td.py --versao)" = "$(cat "$SRC/VERSION")" ]'
check "--ajuda lista as opções" 'cd "$SRC" && python3 td.py --ajuda | grep -q -- "--editor"'
(cd "$SRC" && python3 td.py --gerar 11x19 7 > "$WORK/g.mapa")
check "--gerar escreve um mapa com semente" 'grep -q "semente: 7" "$WORK/g.mapa" && [ "$(grep -c "^[.#STB~]*$" "$WORK/g.mapa")" = 19 ]'
check "--validar aprova o gerado" '(cd "$SRC" && python3 td.py --validar "$WORK/g.mapa") | grep -q "^OK"'
printf 'nome: Quebrado\nS###.\n.....\n..B..\n.....\n.....\n' > "$WORK/q.mapa"
check "--validar aponta o erro" '! (cd "$SRC" && python3 td.py --validar "$WORK/q.mapa" >/dev/null) && (cd "$SRC" && python3 td.py --validar "$WORK/q.mapa") | grep -q "Trilha sem saída em col 4, lin 1"'
check "--importar copia para os seus mapas" 'HOME="$WORK/cli" python3 "$SRC/td.py" --importar "$WORK/g.mapa" | grep -q "^OK" && [ -f "$WORK/cli/.config/td-termux/mapas/aleatorio-7.mapa" ]'
check "--mapas lista prontos e importados" 'HOME="$WORK/cli" python3 "$SRC/td.py" --mapas | grep -q "Aleatório 7"'
HOMEX=cli start 46 50 "python3 td.py --jogar 'Aleatório 7'"
check "--jogar NOME abre a partida no mapa" 'row 1 | grep -q "💗20" && screen | grep -q "Próxima onda 1"'
key q
check "Pausa mostra o mapa pedido" 'screen | grep -q "Mapa: Aleatório 7"'
HOMEX=cli start 46 50 "python3 td.py --editor Rio"
check "--editor MAPA_PRONTO edita uma cópia" 'screen | grep -q "EDITOR · Rio (cópia)" && screen | grep -q "✔ Pronto para jogar"'

echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
