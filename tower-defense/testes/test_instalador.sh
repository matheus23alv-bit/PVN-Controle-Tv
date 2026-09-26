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
termux tx "$INST" --teclas >/dev/null 2>&1
P="$WORK/tx/.termux/termux.properties"
check "Comando criado em \$PREFIX/bin" '[ -x "$WORK/tx-prefix/bin/td" ]'
check "Barra antiga removida por inteiro" '! grep -q "HOME" "$P" && ! grep -q "TAB" "$P"'
check "Outras opcoes preservadas" 'grep -q "use-black-ui = true" "$P" && grep -q "# minha config" "$P"'
check "Barra do jogo gravada" 'grep -q "KEYBOARD" "$P"'
termux tx "$INST" --teclas >/dev/null 2>&1
check "Reinstalar nao duplica a barra" '[ "$(grep -c "^extra-keys" "$P")" = 1 ]'
check "Backup e o arquivo original" 'cmp -s "$WORK/original" "$WORK/tx/.termux/termux.properties.antes-do-td"'
termux tx "$WORK/tx/.local/share/tower-defense/instalar.sh" --remover >/dev/null 2>&1
check "Remover restaura o arquivo byte a byte" 'cmp -s "$WORK/original" "$P"'
check "Remover apaga comandos e arquivos" '[ ! -e "$WORK/tx-prefix/bin/td" ] && [ ! -e "$WORK/tx/.local/share/tower-defense" ]'

echo "== Termux sem configuracao, via curl | bash"
PORT=18090
(cd "$SRC" && exec python3 -m http.server "$PORT" >/dev/null 2>&1) & SRV=$!
sleep 1
mkdir -p "$WORK/cu" "$WORK/cu-prefix/bin"
out="$(cat "$INST" | HOME="$WORK/cu" TERMUX_VERSION=0.118 PREFIX="$WORK/cu-prefix" TD_REPO_RAW="http://localhost:$PORT" bash -s -- --teclas 2>&1)"
check "Baixa os arquivos pela rede" 'grep -q "baixado do GitHub" <<<"$out" && [ -f "$WORK/cu/.local/share/tower-defense/td.py" ]'
check "Script completo apesar de vir pela entrada padrao" 'grep -q "instalado" <<<"$out"'
termux cu "$WORK/cu/.local/share/tower-defense/instalar.sh" --remover >/dev/null 2>&1
check "Remover apaga o termux.properties criado pelo jogo" '[ ! -e "$WORK/cu/.termux/termux.properties" ]'

echo "== Falhas"
bad="$(cat "$INST" | HOME="$WORK/bad" TD_REPO_RAW="http://localhost:1" bash -s -- --sem-teclas 2>&1)"; code=$?
check "Sem internet: mensagem clara e codigo de erro" '[ $code -ne 0 ] && grep -q "nao consegui baixar" <<<"$bad"'
check "Opcao invalida e recusada" '! bash "$INST" --xyz >/dev/null 2>&1'

echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
