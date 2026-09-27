#!/usr/bin/env bash
# Testa o empacotar.sh e o instalar-pack.sh simulando o celular (Termux, pasta Download).
# Uso (na raiz do repositório): bash testes/test_pack.sh
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MOCK="$ROOT/controle-tv/testes/mock-termux-api"
W="$(mktemp -d)"; trap 'tmux kill-session -t pk 2>/dev/null; rm -rf "$W"' EXIT
pass=0; fail=0
check() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi; }

# celular simulado: HOME próprio, Termux:API falso, pasta Download com arquivos
phone() {  # phone <nome>: cria o aparelho e deixa a pasta Download pronta
  H="$W/$1"; mkdir -p "$H/prefix/bin" "$H/sdcard/Download" "$H/storage"
  ln -s "$H/sdcard/Download" "$H/storage/downloads"
}
run() {  # run <nome> [comando...]: roda como no Termux desse aparelho
  local h="$W/$1"; shift
  HOME="$h" TERMUX_VERSION=0.118 PREFIX="$h/prefix" TV_MOCK_LOG="$h/ir.log" \
    PATH="${EXTRA_PATH:+$EXTRA_PATH:}$h/prefix/bin:$MOCK:$PATH" "$@" 2>&1
}

echo "== empacotar.sh"
ZIP="$(bash "$ROOT/empacotar.sh" "$W/dist" HEAD)"
check "Gera o zip com versões e commit no nome" '[[ "$(basename "$ZIP")" =~ ^PVN-pack-[0-9]{8}-controle-.*-teclado-.*-[0-9a-f]{7}\.zip$ ]]'
check "Zip sem a pasta do jogo, que saiu para o repositório dele" '! unzip -Z1 "$ZIP" | grep -q "/tower-defense/"'
check "Zip sem .git e sem CLAUDE.md" '! unzip -l "$ZIP" | grep -qE "\.git/|CLAUDE\.md"'
check "Zip traz o manifesto e o setup" 'unzip -l "$ZIP" | grep -q PACK-INFO.txt && unzip -l "$ZIP" | grep -q setup-teste.sh'

echo "== Pasta Download sem pack"
phone vazio
out="$(run vazio bash "$ROOT/instalar-pack.sh")"; code=$?
check "Avisa que não há pack e para" '[ $code -ne 0 ] && grep -q "nenhum PVN-pack-\*.zip" <<<"$out"'

echo "== Pack baixado duas vezes, com um pack antigo e outro zip na pasta"
phone a
cp "$ZIP" "$W/a/sdcard/Download/PVN-pack-20200101-controle-0.0.1-td-0.0.1-0000000.zip"
touch -d "2020-01-01" "$W/a/sdcard/Download/PVN-pack-20200101-controle-0.0.1-td-0.0.1-0000000.zip"
cp "$ZIP" "$W/a/sdcard/Download/$(basename "$ZIP" .zip) (1).zip"
echo x > "$W/a/sdcard/Download/fotos.zip"
out="$(run a bash "$ROOT/instalar-pack.sh")"; code=$?
check "Escolhe o pack mais recente, mesmo com nome (1)" 'grep -q "(1).zip" <<<"$out"'
check "Confere o SHA-256 de todos os arquivos" 'grep -q "arquivos conferem com o SHA-256" <<<"$out"'
check "Instala a partir de ~/pvn-pack, sem baixar do GitHub" 'grep -q "usando os arquivos desta pasta (~/pvn-pack)" <<<"$out"'
check "Teclado e controle instalados, emissor detectado" '[ $code -eq 0 ] && grep -q "teclado .* instalado: comando teclas" <<<"$out" && grep -q "controle .* instalado: comando tv" <<<"$out" && grep -q "emissor IR pronto" <<<"$out"'
check "Pack completo: 4 passos e os dois roteiros" 'grep -q "SETUP DE TESTE COMPLETO" <<<"$out" && grep -q "4/4  Conferência" <<<"$out" && grep -q "controle-tv/docs/ROADMAP.md" <<<"$out" && grep -q "teclado-termux/docs/ROADMAP.md" <<<"$out"'
check "Não instala nem cita o jogo" '[ ! -e "$W/a/prefix/bin/td" ] && ! grep -qE "Tower Defense|comando td|🏰" <<<"$out"'
check "Manifesto e instalador mostram a versão do teclado" 'grep -q "✔ teclado $(cat "$ROOT/teclado-termux/source/VERSION")" <<<"$out"'
check "Comando tv funciona depois" 'run a tv --perfil LG ligar | grep -q "✓ Ligar/desligar (LG)"'

echo "== Teclado e controle juntos: a barra troca sozinha ao abrir o tv"
PROPS="$W/a/.termux/termux.properties"
bar() { sed -n 's/^# teclas: //p' "$PROPS" 2>/dev/null; }
app() {  # app <comando>: abre no tmux como no Termux desse aparelho
  tmux kill-session -t pk 2>/dev/null
  tmux new-session -d -s pk -x 46 -y 50 "HOME='$W/a' TERMUX_VERSION=0.118 PREFIX='$W/a/prefix' TV_MOCK_LOG='$W/a/ir.log' PATH='$W/a/prefix/bin:$MOCK:$PATH' TERM=xterm-256color $1"
  sleep 2.5
}
run a teclas melhorado >/dev/null
check "teclas melhorado grava a barra do dia a dia" '[ "$(bar)" = melhorado ]'
run a tv --perfil LG vol- >/dev/null; VOLDN="$(tail -1 "$W/a/ir.log")"; : > "$W/a/ir.log"
app "tv --perfil LG"
check "Abrir o tv põe a barra da TV" '[ "$(bar)" = tv ]'
tmux send-keys -t pk NPage; sleep 1
check "VOL- da barra da TV transmite pelo emissor" '[ "$(tail -1 "$W/a/ir.log")" = "$VOLDN" ]'
tmux send-keys -t pk q; sleep 2.5
check "Fechar o tv devolve o padrão melhorado" '[ "$(bar)" = melhorado ]'
tmux kill-session -t pk 2>/dev/null
run a teclas original >/dev/null
check "teclas original: sem barra própria antes, volta ao padrão do Termux" '[ -z "$(bar)" ] && ! grep -q "^extra-keys" "$PROPS" 2>/dev/null'
out="$(run a bash "$ROOT/instalar-pack.sh")"; code=$?
check "Reinstalar substitui o pack anterior" '[ $code -eq 0 ] && [ -f "$W/a/pvn-pack/PACK-INFO.txt" ] && [ ! -e "$W/a/pvn-pack.novo" ]'

echo "== Termux sem unzip"
phone b; cp "$ZIP" "$W/b/sdcard/Download/"
mkdir -p "$W/semunzip"; printf '#!/bin/sh\nexit 127\n' > "$W/semunzip/unzip"; chmod +x "$W/semunzip/unzip"
out="$(EXTRA_PATH="$W/semunzip" run b bash "$ROOT/instalar-pack.sh")"; code=$?
check "Descompacta pelo Python quando o unzip falha" '[ $code -eq 0 ] && grep -q "arquivos conferem" <<<"$out"'

echo "== Primeiro acesso: permissão de arquivos"
H="$W/c"; mkdir -p "$H/prefix/bin" "$H/sdcard/Download" "$W/permissao"; cp "$ZIP" "$H/sdcard/Download/"
printf '#!/bin/sh\n# imita a janela do Android: o acesso aparece depois que a pessoa toca em Permitir\nsleep 2; mkdir -p "$HOME/storage"; ln -s "$HOME/sdcard/Download" "$HOME/storage/downloads"\n' > "$W/permissao/termux-setup-storage"
chmod +x "$W/permissao/termux-setup-storage"
out="$(EXTRA_PATH="$W/permissao" run c bash "$ROOT/instalar-pack.sh")"; code=$?
check "Pede Permitir, espera o acesso e continua" '[ $code -eq 0 ] && grep -q "toque em PERMITIR" <<<"$out" && grep -q "instalado: comando tv" <<<"$out"'

echo "== Zips com defeito"
phone d
run d bash "$ROOT/instalar-pack.sh" "$ZIP" >/dev/null   # instalação boa anterior
head -c 200000 "$ZIP" > "$W/d/sdcard/Download/PVN-pack-cortado.zip"
out="$(run d bash "$ROOT/instalar-pack.sh" "$W/d/sdcard/Download/PVN-pack-cortado.zip")"; code=$?
check "Zip incompleto é recusado" '[ $code -ne 0 ] && grep -q "baixe de novo" <<<"$out"'
check "Instalação anterior continua intacta" '[ -f "$W/d/pvn-pack/PACK-INFO.txt" ]'
mkdir -p "$W/adult" && (cd "$W/adult" && unzip -q "$ZIP" && f="$(ls -d PVN-pack-*)" && echo "# alterado" >> "$f/controle-tv/source/tv.py" && zip -qr "$W/adulterado.zip" "$f")
out="$(run d bash "$ROOT/instalar-pack.sh" "$W/adulterado.zip")"; code=$?
check "Arquivo alterado dentro do zip é detectado" '[ $code -ne 0 ] && grep -q "não confere com o PACK-INFO" <<<"$out"'
out="$(run d bash "$ROOT/instalar-pack.sh" "$W/d/sdcard/Download/fotos-inexistente.zip")"; code=$?
check "Caminho inexistente é recusado" '[ $code -ne 0 ] && grep -q "arquivo não encontrado" <<<"$out"'

echo "== Segurança da pasta de destino"
phone e; cp "$ZIP" "$W/e/sdcard/Download/"; mkdir -p "$W/e/meus-arquivos"; echo importante > "$W/e/meus-arquivos/nota.txt"
out="$(PVN_PACK_DIR="$W/e/meus-arquivos" run e bash "$ROOT/instalar-pack.sh")"; code=$?
check "Não apaga uma pasta que não é pack" '[ $code -ne 0 ] && [ -f "$W/e/meus-arquivos/nota.txt" ] && grep -q "não é um pack do PVN" <<<"$out"'

echo "== Pelo curl | bash"
phone f; cp "$ZIP" "$W/f/sdcard/Download/"
out="$(cat "$ROOT/instalar-pack.sh" | run f bash)"; code=$?
check "Funciona recebido pela entrada padrão" '[ $code -eq 0 ] && grep -q "instalado: comando tv" <<<"$out"'

echo "== A barra de um app não fica presa (Teclado Termux 1.1)"
phone h; cp "$ZIP" "$W/h/sdcard/Download/"
run h bash "$ROOT/instalar-pack.sh" >/dev/null
run h teclas melhorado >/dev/null
PROPS_H="$W/h/.termux/termux.properties"
barh() { sed -n 's/^# teclas: //p' "$PROPS_H" 2>/dev/null; }
sleep 30 & DONO=$!; kill -KILL "$DONO" 2>/dev/null; wait "$DONO" 2>/dev/null
run h teclas --entrar tv --dono "$DONO" >/dev/null   # app que já morreu pediu a barra
check "A barra do app entrou" '[ "$(barh)" = tv ]'
out="$(run h teclas --estado)"
check "O teclas vê que o app morreu e devolve a barra" '[ "$(barh)" = melhorado ]'
check "O --estado avisa quando o dono já foi encerrado" 'run h teclas --entrar tv --dono "$DONO" >/dev/null; run h teclas --estado | grep -q "já encerrado" || [ "$(barh)" = melhorado ]'
run h teclas original >/dev/null

echo; echo "$pass aprovados, $fail falhas"
[ "$fail" -eq 0 ]
