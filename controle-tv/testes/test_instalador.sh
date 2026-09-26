#!/usr/bin/env bash
# Testa o instalador em HOMEs temporarios simulando o Termux. Uso: bash testes/test_instalador.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$(cd "$HERE/../source" && pwd)"
MOCK="$HERE/mock-termux-api"
WORK="$(mktemp -d)"; SRV=""
trap 'rm -rf "$WORK" "$SRC/__pycache__"; [ -n "$SRV" ] && kill "$SRV" 2>/dev/null' EXIT
pass=0; fail=0
check() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi; }
termux() {  # termux <nome> <comando...>: roda como se fosse o Termux, com o Termux:API falso
  local h="$WORK/$1"; shift
  mkdir -p "$h/prefix/bin"
  HOME="$h" TERMUX_VERSION=0.118 PREFIX="$h/prefix" TV_MOCK_LOG="$h/ir.log" PATH="$h/prefix/bin:$MOCK:$PATH" "$@"
}

echo "== Termux com emissor IR"
out="$(termux a bash "$SRC/instalar.sh" --atalhos 2>&1)"
check "Instala sem erro" 'grep -q "PVN Controle TV .* instalado" <<<"$out"'
check "Detecta o emissor" 'grep -q "emissor IR pronto" <<<"$out"'
check "Cria o comando tv" '[ -x "$WORK/a/prefix/bin/tv" ]'
check "Cria os atalhos do widget" '[ -x "$WORK/a/.shortcuts/TV Ligar" ] && [ "$(ls "$WORK/a/.shortcuts" | wc -l)" = 6 ]'
termux a tv --perfil Samsung mudo >/dev/null 2>&1
check "Comando tv transmite pelo Termux:API" 'grep -q "^-f 38000 4500,4500" "$WORK/a/ir.log"'
termux a bash "$WORK/a/.local/share/pvn-controle-tv/instalar.sh" --remover >/dev/null 2>&1
check "Remover apaga comando, atalhos e arquivos" '[ ! -e "$WORK/a/prefix/bin/tv" ] && [ ! -e "$WORK/a/.shortcuts/TV Ligar" ] && [ ! -e "$WORK/a/.local/share/pvn-controle-tv" ]'

echo "== Termux sem emissor IR"
out="$(TV_MOCK_SEM_IR=1 termux b bash "$SRC/instalar.sh" --sem-atalhos 2>&1)"
check "Avisa que o celular nao tem emissor" 'grep -q "não tem emissor infravermelho" <<<"$out" && grep -q "resolva o aviso da etapa 4" <<<"$out"'

echo "== curl | bash"
PORT=18097
(cd "$SRC" && exec python3 -m http.server "$PORT" >/dev/null 2>&1) & SRV=$!
sleep 1
out="$(cat "$SRC/instalar.sh" | TV_REPO_RAW="http://localhost:$PORT" termux c bash -s -- --sem-atalhos 2>&1)"
check "Baixa e instala pela rede" 'grep -q "baixado do GitHub" <<<"$out" && [ -f "$WORK/c/.local/share/pvn-controle-tv/tv.py" ]'

echo "== Conflito"
mkdir -p "$WORK/d/prefix/bin"; printf '#!/bin/sh\necho outro\n' > "$WORK/d/prefix/bin/tv"; chmod +x "$WORK/d/prefix/bin/tv"
out="$(termux d bash "$SRC/instalar.sh" --sem-atalhos 2>&1)"; code=$?
check "Nao sobrescreve um comando tv de outro programa" '[ $code -ne 0 ] && grep -q "outro" "$WORK/d/prefix/bin/tv"'

echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
