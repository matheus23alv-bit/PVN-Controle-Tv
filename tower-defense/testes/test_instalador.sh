#!/usr/bin/env bash
# Testa o instalador em HOMEs temporarios, simulando Linux e Termux. Uso: bash testes/test_instalador.sh
set -u
SRC="$(realpath "$(dirname "$0")/../source")"
INST="$SRC/instalar.sh"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"; kill "$SRV" 2>/dev/null; rm -rf "$SRC/__pycache__"' EXIT
pass=0; fail=0
check() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi; }
termux() { HOME="$WORK/$1" TERMUX_VERSION=0.118 PREFIX="$WORK/$1-prefix" bash "${@:2}"; }

echo "== Linux, instalacao local"
mkdir -p "$WORK/lin"
HOME="$WORK/lin" bash "$INST" --sem-teclas >/dev/null 2>&1
check "Instala e cria o comando td" '[ -x "$WORK/lin/.local/bin/td" ]'
check "td --versao responde" '[ "$("$WORK/lin/.local/bin/td" --versao)" = "$(cat "$SRC/VERSION")" ]'
check "Guarda copia do instalador" '[ -f "$WORK/lin/.local/share/tower-defense/instalar.sh" ]'
check "Nao cria configuracao do Termux fora do Termux" '[ ! -e "$WORK/lin/.termux" ]'

echo "== Termux com barra de teclas propria (valor em varias linhas)"
mkdir -p "$WORK/tx/.termux" "$WORK/tx-prefix/bin"
cat > "$WORK/tx/.termux/termux.properties" <<'EOF'
# minha config
extra-keys = [ \
 ['ESC','/','-','HOME','UP','END'], \
 ['TAB','CTRL','ALT','LEFT','DOWN','RIGHT'] \
]
use-black-ui = true
EOF
cp "$WORK/tx/.termux/termux.properties" "$WORK/original"
out="$(termux tx "$INST" --teclas 2>&1)"
P="$WORK/tx/.termux/termux.properties"
check "Comando criado em \$PREFIX/bin" '[ -x "$WORK/tx-prefix/bin/td" ]'
check "A barra da pessoa fica intacta: a do jogo e do comando teclas" 'cmp -s "$WORK/original" "$P"'
check "Nada muda no termux.properties, entao nao ha backup" '[ ! -e "$WORK/tx/.termux/termux.properties.antes-do-td" ]'
check "--teclas avisa que a barra nao e mais fixada" 'grep -q "para fixar: teclas jogo" <<<"$out"'
check "Sem o teclas, orienta a instalar o Teclado Termux" 'grep -q "instale o Teclado Termux" <<<"$out"'
printf '#!/bin/sh\n' > "$WORK/tx-prefix/bin/teclas"; chmod +x "$WORK/tx-prefix/bin/teclas"
out="$(PATH="$WORK/tx-prefix/bin:$PATH" termux tx "$INST" 2>&1)"
check "Com o teclas, explica que a barra entra ao abrir o td" 'grep -q "entra ao abrir o td e sai ao fechar" <<<"$out"'
termux tx "$WORK/tx/.local/share/tower-defense/instalar.sh" --remover >/dev/null 2>&1
check "Remover deixa o arquivo como estava" 'cmp -s "$WORK/original" "$P"'
check "Remover apaga comandos e arquivos" '[ ! -e "$WORK/tx-prefix/bin/td" ] && [ ! -e "$WORK/tx/.local/share/tower-defense" ]'

echo "== Termux: tela cheia e fonte"
mkdir -p "$WORK/tf/.termux" "$WORK/tf-prefix/bin"
printf '%s\n' "fullscreen = false" "use-black-ui = true" > "$WORK/tf/.termux/termux.properties"
echo "minha fonte" > "$WORK/tf/.termux/font.ttf"
cp "$WORK/tf/.termux/termux.properties" "$WORK/tf-original"
TP="$WORK/tf/.termux/termux.properties"; TF="$WORK/tf/.termux/font.ttf"
termux tf "$INST" --sem-teclas --tela-cheia --fonte >/dev/null 2>&1
check "Tela cheia gravada no lugar da configuracao antiga" '[ "$(grep -c "^fullscreen" "$TP")" = 1 ] && grep -q "^fullscreen = true" "$TP" && grep -q "^terminal-margin-horizontal = 0" "$TP"'
check "Outras opcoes da pessoa preservadas" 'grep -q "use-black-ui = true" "$TP"'
check "Fonte do jogo instalada e a antiga guardada" 'cmp -s "$SRC/fontes/DejaVuSansMono.ttf" "$TF" && grep -q "minha fonte" "$WORK/tf/.termux/font.ttf.antes-do-td"'
check "Fonte e licenca copiadas junto do jogo" '[ -f "$WORK/tf/.local/share/tower-defense/fontes/DejaVuSansMono.ttf" ] && [ -f "$WORK/tf/.local/share/tower-defense/fontes/LICENCA.txt" ]'
termux tf "$INST" --sem-teclas --tela-cheia --fonte >/dev/null 2>&1
check "Reinstalar nao duplica nem perde o backup da fonte" '[ "$(grep -c "^fullscreen" "$TP")" = 1 ] && grep -q "minha fonte" "$WORK/tf/.termux/font.ttf.antes-do-td"'
out="$(termux tf "$WORK/tf/.local/share/tower-defense/instalar.sh" --so-tela --sem-tela-cheia 2>&1)"
check "--so-tela desliga a tela cheia sem reinstalar" '! grep -q "^fullscreen" "$TP" && grep -q "use-black-ui = true" "$TP" && ! grep -q "Arquivos do jogo" <<<"$out" && grep -q "tela cheia desligada; o Termux recarregou" <<<"$out"'
termux tf "$WORK/tf/.local/share/tower-defense/instalar.sh" --so-tela --tela-cheia >/dev/null 2>&1
termux tf "$WORK/tf/.local/share/tower-defense/instalar.sh" --so-tela --sem-fonte >/dev/null 2>&1
check "--sem-fonte devolve a fonte da pessoa" 'grep -q "minha fonte" "$TF" && [ ! -e "$WORK/tf/.termux/font.ttf.antes-do-td" ]'
termux tf "$WORK/tf/.local/share/tower-defense/instalar.sh" --so-tela --fonte >/dev/null 2>&1
termux tf "$WORK/tf/.local/share/tower-defense/instalar.sh" --remover >/dev/null 2>&1
check "Remover devolve termux.properties e fonte byte a byte" 'cmp -s "$WORK/tf-original" "$TP" && grep -q "minha fonte" "$TF"'
check "--so-tela fora do Termux e recusado" '! HOME="$WORK/lin" bash "$INST" --so-tela --tela-cheia >/dev/null 2>&1'

echo "== Termux sem configuracao, via curl | bash"
PORT=18090
(cd "$SRC" && exec python3 -m http.server "$PORT" >/dev/null 2>&1) & SRV=$!
sleep 1
mkdir -p "$WORK/cu" "$WORK/cu-prefix/bin"
out="$(cat "$INST" | HOME="$WORK/cu" TERMUX_VERSION=0.118 PREFIX="$WORK/cu-prefix" TD_REPO_RAW="http://localhost:$PORT" bash -s -- --tela-cheia 2>&1)"
check "Baixa os arquivos pela rede" 'grep -q "baixado do GitHub" <<<"$out" && [ -f "$WORK/cu/.local/share/tower-defense/td.py" ]'
check "Script completo apesar de vir pela entrada padrao" 'grep -q "instalado" <<<"$out" && grep -q "^fullscreen = true" "$WORK/cu/.termux/termux.properties"'
out="$(cat "$INST" | HOME="$WORK/cu" TERMUX_VERSION=0.118 PREFIX="$WORK/cu-prefix" TD_REPO_RAW="http://localhost:$PORT" bash -s -- --sem-teclas --fonte 2>&1)"
check "Pelo curl, a fonte e baixada so quando pedida" 'cmp -s "$SRC/fontes/DejaVuSansMono.ttf" "$WORK/cu/.termux/font.ttf" && [ -e "$WORK/cu/.termux/.td-sem-fonte-original" ]'
check "Sem fonte propria antes, nao promete backup" 'grep -q "antes era a fonte padrão" <<<"$out" && ! grep -q "a sua ficou" <<<"$out"'
termux cu "$WORK/cu/.local/share/tower-defense/instalar.sh" --remover >/dev/null 2>&1
check "Remover apaga o termux.properties criado pelo jogo" '[ ! -e "$WORK/cu/.termux/termux.properties" ]'
check "Remover apaga a fonte que nao existia antes" '[ ! -e "$WORK/cu/.termux/font.ttf" ] && [ ! -e "$WORK/cu/.termux/.td-sem-fonte-original" ]'

echo "== Falhas"
bad="$(cat "$INST" | HOME="$WORK/bad" TD_REPO_RAW="http://localhost:1" bash -s -- --sem-teclas 2>&1)"; code=$?
check "Sem internet: mensagem clara e codigo de erro" '[ $code -ne 0 ] && grep -q "nao consegui baixar" <<<"$bad"'
check "Opcao invalida e recusada" '! bash "$INST" --xyz >/dev/null 2>&1'

echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
