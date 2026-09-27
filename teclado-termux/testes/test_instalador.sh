#!/usr/bin/env bash
# Testa o instalador do Teclado Termux em HOMEs temporários, simulando Linux e Termux.
# Uso (na pasta teclado-termux): bash testes/test_instalador.sh
set -u
SRC="$(realpath "$(dirname "$0")/../source")"
INST="$SRC/instalar.sh"
WORK="$(mktemp -d)"; SRV=""
trap 'rm -rf "$WORK" "$SRC/__pycache__"; [ -n "$SRV" ] && kill "$SRV" 2>/dev/null' EXIT
pass=0; fail=0
check() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi; }
termux() {  # termux <nome> <comando...>: roda como no Termux, com um termux-reload-settings falso
  local h="$WORK/$1"; shift
  mkdir -p "$h/prefix/bin"
  [ -e "$h/prefix/bin/termux-reload-settings" ] || { printf '#!/bin/sh\necho r >> "%s/recargas"\n' "$h" > "$h/prefix/bin/termux-reload-settings"; chmod +x "$h/prefix/bin/termux-reload-settings"; }
  HOME="$h" TERMUX_VERSION=0.118 PREFIX="$h/prefix" PATH="$h/prefix/bin:$PATH" "$@"
}
MINHA='# minha config
extra-keys = [ \
 ['"'"'ESC'"'"','"'"'/'"'"','"'"'-'"'"','"'"'HOME'"'"','"'"'UP'"'"','"'"'END'"'"'], \
 ['"'"'TAB'"'"','"'"'CTRL'"'"','"'"'ALT'"'"','"'"'LEFT'"'"','"'"'DOWN'"'"','"'"'RIGHT'"'"'] \
]
use-black-ui = true'

echo "== Linux"
mkdir -p "$WORK/lin"
out="$(HOME="$WORK/lin" bash "$INST" 2>&1)"
check "Instala e cria o comando teclas" '[ -x "$WORK/lin/.local/bin/teclas" ] && grep -q "Teclado Termux .* instalado" <<<"$out"'
check "teclas --versao responde" '[ "$(HOME="$WORK/lin" "$WORK/lin/.local/bin/teclas" --versao)" = "$(cat "$SRC/VERSION")" ]'
check "Não cria configuração do Termux fora dele" '[ ! -e "$WORK/lin/.termux" ]'

echo "== Termux com barra própria"
mkdir -p "$WORK/tx/.termux"
P="$WORK/tx/.termux/termux.properties"
printf '%s\n' "$MINHA" > "$P"; cp "$P" "$WORK/original"
out="$(termux tx bash "$INST" --melhorado 2>&1)"
check "Comando em \$PREFIX/bin" '[ -x "$WORK/tx/prefix/bin/teclas" ]'
check "Padrão melhorado aplicado e Termux recarregado" 'grep -q "^# teclas: melhorado" "$P" && [ "$(grep -c "^extra-keys" "$P")" = 1 ] && [ -s "$WORK/tx/recargas" ]'
check "Outras opções preservadas" 'grep -q "use-black-ui = true" "$P" && grep -q "# minha config" "$P"'
check "Avisa da troca automática" 'grep -q "troca automática: o tv e o td" <<<"$out"'
out="$(termux tx bash "$INST" 2>&1)"
check "Reinstalar não pergunta nem duplica" 'grep -q "barra: Padrão melhorado" <<<"$out" && [ "$(grep -c "^extra-keys" "$P")" = 1 ]'
termux tx teclas tv >/dev/null
termux tx teclas original >/dev/null
check "teclas original devolve a barra da pessoa byte a byte" 'cmp -s "$WORK/original" "$P"'
termux tx teclas jogo >/dev/null
termux tx bash "$WORK/tx/.local/share/teclado-termux/instalar.sh" --remover >/dev/null 2>&1
check "Remover devolve a barra byte a byte" 'cmp -s "$WORK/original" "$P"'
check "Remover apaga comando, arquivos, estado e backup" '[ ! -e "$WORK/tx/prefix/bin/teclas" ] && [ ! -e "$WORK/tx/.local/share/teclado-termux" ] && [ ! -e "$WORK/tx/.config/teclas" ] && [ ! -e "$P.antes-do-teclas" ]'

echo "== Termux com a barra do jogo fixada pelo Tower Defense 3.1"
mkdir -p "$WORK/td/.termux"
P="$WORK/td/.termux/termux.properties"
printf '%s\n' "$MINHA" > "$P.antes-do-td"
printf '%s\n' "# instalado pelo tower-defense" "extra-keys = [['ESC','1','2','3','4','u','x','UP','ENTER'],['p','n','f','h','q','KEYBOARD','LEFT','DOWN','RIGHT']]" "use-black-ui = true" > "$P"
out="$(termux td bash "$INST" --sem-melhorado 2>&1)"
check "Avisa que a barra do jogo deixa de ser fixa" 'grep -q "a barra do jogo estava fixa" <<<"$out" && grep -q "barra mantida: Jogo (fixada pelo td 3.1)" <<<"$out"'
termux td teclas melhorado >/dev/null
termux td teclas original >/dev/null
check "A de antes é a barra de antes do jogo" 'grep -q "TAB" "$P" && ! grep -q "KEYBOARD" "$P" && ! grep -q "tower-defense" "$P"'

echo "== Termux sem configuração, via curl | bash"
PORT=18097
(cd "$SRC" && exec python3 -m http.server "$PORT" >/dev/null 2>&1) & SRV=$!
sleep 1
mkdir -p "$WORK/cu"
out="$(cat "$INST" | termux cu env TECLAS_REPO_RAW="http://localhost:$PORT" bash -s -- --melhorado 2>&1)"
check "Baixa os arquivos pela rede" 'grep -q "baixado do GitHub" <<<"$out" && [ -f "$WORK/cu/.local/share/teclado-termux/teclas.py" ]'
check "Cria o termux.properties só com a barra" '[ "$(grep -vc "^#" "$WORK/cu/.termux/termux.properties")" = 1 ]'
termux cu bash "$WORK/cu/.local/share/teclado-termux/instalar.sh" --remover >/dev/null 2>&1
check "Remover apaga o arquivo que não existia" '[ ! -e "$WORK/cu/.termux/termux.properties" ]'

echo "== Falhas"
bad="$(cat "$INST" | HOME="$WORK/bad" TECLAS_REPO_RAW="http://localhost:1" bash -s 2>&1)"; code=$?
check "Sem internet: mensagem clara e código de erro" '[ $code -ne 0 ] && grep -q "nao consegui baixar" <<<"$bad"'
check "Opção inválida é recusada" '! bash "$INST" --xyz >/dev/null 2>&1'
mkdir -p "$WORK/outro/.local/bin"; printf '#!/bin/sh\necho outro\n' > "$WORK/outro/.local/bin/teclas"; chmod +x "$WORK/outro/.local/bin/teclas"
check "Não sobrescreve um teclas de outro programa" '! HOME="$WORK/outro" bash "$INST" >/dev/null 2>&1 && grep -q outro "$WORK/outro/.local/bin/teclas"'

echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
