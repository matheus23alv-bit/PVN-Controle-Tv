# Checkpoint — PVN Workspace

**Marcador:** `PVN-CHECKPOINT-2026-09-27` · controle **2.0.2** · Tower Defense **3.1.2** · auditoria completa, todas as baterias verdes.

Este arquivo existe para continuar o projeto em outra sessão sem perder contexto. Ele entra na Main pelo PR da auditoria (#8). O hash exato do commit está no `MARCADOR-DE-CONTINUIDADE.txt` do pack de continuidade, ou no resultado de `git log -1 --format=%H -- CHECKPOINT.md`.

Para continuar só o jogo, use `tower-defense/docs/CHECKPOINT.md` (marcador `TD-CHECKPOINT-2026-09-27`).

## 1. Estado atual

| Item | Valor |
|---|---|
| Repositório | `matheus23alv-bit/PVN-Controle-Tv` |
| Branch principal (a "Main" do usuário) | `claude/tv-remote-control-app-lu248i`, que é o branch padrão |
| Branch de trabalho das sessões | `claude/tower-defense-termux-yjzaeb`, recriado a partir da Main depois de cada merge |
| Histórico de merges | PR #1 a #7 e #8 (esta auditoria) |
| Controle TV | 2.0.2: controle IR real pelo emissor do celular, no terminal |
| Tower Defense | 3.1.2: jogo de terminal em tela cheia retrato, com editor de mapas |
| Testes | controle 25/30/9 · jogo 75/95/29 · pack 28 |

## 2. Os dois projetos

**`controle-tv/`**: controle remoto de TV pelo **emissor infravermelho do próprio celular**, usando o Termux:API (`termux-infrared-transmit`).
- **Código:** `source/tv.py`, um arquivo só, com biblioteca padrão e `curses`.
- **Protocolos:** NEC, NECext, Samsung32, Sony SIRC 12/15/20, RC5/RC5X e RC6 (com bit de alternância) e raw.
- **Marcas embutidas:** Samsung, LG e Sony, com os códigos conferidos contra os publicados.
- **Outras marcas:** importa arquivos `.ir` do Flipper-IRDB.
- **Telas:** controle, escolha da TV (com rolagem), descobrir TV e ajuda.
- **Linha de comando:** `tv ligar`, `--perfil`, `--listar`, `--importar`, `--diagnostico`, `--atalhos` e `--simular`.
- **Configuração:** `~/.config/pvn-tv/` (`config.json` e `perfis/*.ir`). Instala em `~/.local/share/pvn-controle-tv`, com o comando `tv`.

**`tower-defense/`**: tower defense de terminal, independente e leve. O usuário tem outro projeto de tower defense, complexo e separado; este não é porte dele.
- **Código:** `source/td.py`, um arquivo só, com biblioteca padrão e `curses`.
- **Visual:** emojis em casas de 2 colunas e escala automática de 1× a 3× (layout 9:16).
- **Torres:** 4 (🏹 💣 🔮 🌀), com habilidade no nível 3 e mira por torre (1º, forte, perto).
- **Monstros:** 8 (👾 🐀 👹 🐌 🐢 🦇 👻 🐉), com casco, cura, imunidade, invisibilidade e invocação.
- **Efeitos:** só visuais (tiros, explosão, números de dano, faixas, tremida e vibração pelo `termux-vibrate`).
- **Mapas:** 3 prontos (Serpente, Espiral, Rio), gerador por semente, editor na tela e arquivos `.mapa` em texto.
- **Telas:** menu, tutorial de 9 passos, Mapas, Criar mapa, Como jogar, Opções e Ajustar tela (régua de emojis, tela cheia e fonte DejaVu).
- **Configuração:** `~/.config/td-termux/` (`config.json` e `mapas/*.mapa`). Instala em `~/.local/share/tower-defense`, com o comando `td`.

**Raiz:**
- `setup-teste.sh`: instala os dois projetos, ou só o que vier no pack.
- `empacotar.sh`: gera o pack zip com o `PACK-INFO.txt` e o SHA-256 de cada arquivo. Com `td` no fim, o pack leva só o jogo.
- `instalar-pack.sh`: instala do zip na pasta Download do celular.
- `testes/test_pack.sh`: testa essas três ferramentas.
- `testes/captura.sh` e `testes/term2png.py`: capturam a tela do tmux em PNG para revisão visual.

## 3. Mapa do código

**`tower-defense/source/td.py`** (cerca de 3.200 linhas), na ordem:

1. **Constantes:** `TOWERS`, `ENEMIES`, `START_GOLD=100`, `HP_GROWTH=1.16`, `UPGRADE_PRICE={1: 0.7, 2: 2.2}`, `FPS=20`.
2. **Motor de mapas:** `Mapa`, `MapError` (com mensagem curta), `trace()`, `generate_map` (`_snake`, `_zigzag`, `_decorate`), mapas prontos e arquivos.
3. **Lógica:** `Tower`, `Enemy`, `Fx` e `Game` (`_step`, `_fire` com busca binária na trilha, `_hit`). Os efeitos têm duração em segundos reais.
4. **Editor sem tela:** `Editor` (pintar, trilha pelos cantos, desfazer, redimensionar, gerar).
5. **Tutorial:** `tutorial_spots` e `tutorial_steps`.
6. **Utilidades de tela:** `fit`, `wrap`, `short_num`, `Palette` (256 ou 8 cores), `Layout` e `compute_layout` (escala), `texture`.
7. **`App`:** telas `draw_<tela>` e `key_<tela>`, janelas sobrepostas e mapa de ocupação (nada corta emoji ao meio).
8. **Linha de comando:** `--jogar`, `--editor`, `--mapas`, `--gerar`, `--validar`, `--importar`, `--tutorial`, `--sem-emoji`, `--sem-toque`, `--versao` e `--ajuda`.

**`controle-tv/source/tv.py`** (cerca de 950 linhas):

1. Codificadores IR e `encode(signal, toggle)`.
2. Nomes, apelidos (`canon`) e marcas embutidas.
3. `parse_ir_file` e `import_profile`.
4. `Transmitter`, com tempo limite e `TV_IR_TIMEOUT`.
5. `Worker`: envio fora do laço da tela, descartando a fila se o Termux:API travar.
6. `App` e `cli`.

## 4. Regras que valem sempre

Resumo do `CLAUDE.md`, que é carregado automaticamente em toda sessão.

- **Entrega:**
  1. testes;
  2. PR para a Main e merge;
  3. pack zip gerado do commit mesclado: `git fetch origin && bash empacotar.sh <pasta> origin/claude/tv-remote-control-app-lu248i` (acrescente `td` numa sessão só do jogo);
  4. o zip e o `instalar-pack.sh` enviados como arquivos;
  5. resposta dizendo o que mudou, o resultado dos testes, o comando de instalação e o que testar.
- **Onde roda:** os dois projetos rodam no terminal do Termux, nunca no navegador. O simulador web é legado.
- **Estrutura:** cada projeto tem `source/` (só arquivos de funcionamento + `VERSION` + `CHANGELOG.md` + `LEIA-ME.md`), `legados/`, `testes/` e `docs/`.
- **Versão:** um `VERSION` por projeto. Toda mudança de código sobe a versão e ganha entrada no CHANGELOG. Versões maiores guardam a anterior em `legados/`.
- **Idioma e instaladores:** tudo em português do Brasil. Os instaladores baixam pelo `HEAD` do repositório.
- **Estilo de resposta do usuário:** títulos curtos, parágrafos curtos, tabelas para comparar e perguntas de múltipla escolha (A, B, C, D) só quando a decisão muda o resultado. Ele gosta de receber o diff, o relatório e os detalhes. Não bajular e não enrolar.

## 5. Testar e revisar

```bash
cd controle-tv && python3 -m unittest testes/test_ir.py && bash testes/test_tela.sh && bash testes/test_instalador.sh
cd tower-defense && python3 -m unittest testes/test_logica.py && bash testes/test_terminal.sh && bash testes/test_instalador.sh
bash testes/test_pack.sh                                        # na raiz
python3 tower-defense/testes/simulacao_balanceamento.py tower-defense/source/td.py 3   # ~2 min
python3 -m pyflakes controle-tv/source/tv.py tower-defense/source/td.py              # análise estática
```

- **Pré-requisitos:** os testes de tela precisam de `tmux`. O controle usa o Termux:API falso de `controle-tv/testes/mock-termux-api/`.
- **Onde tocar nos testes do jogo:** `tower-defense/testes/tela.py` acha botões e casas na tela capturada.
- **Revisão visual:** abra o programa numa sessão do tmux em 46×50 e rode `bash testes/captura.sh <sessão> <nome>`.

## 6. Decisões já tomadas (não reabrir sem motivo)

| Decisão | Motivo |
|---|---|
| Controle pelo IR nativo do celular, não Wi-Fi nem web | Pedido explícito do usuário; o simulador web virou legado |
| Jogo próprio e leve (opção 1A), com visual de emojis (2C) | Escolha do usuário; o outro tower defense dele é separado |
| Casas de 2 colunas, só emojis de largura "W" | Alinhamento previsível no Termux; modo sem emoji como reserva |
| Tela cheia em retrato com escala automática | Pedido da 3.0; o mapa preenche a altura |
| Trilha pelos cantos no editor | Arrastar o dedo no Termux vira rolagem, não pintura |
| Efeitos só visuais, dano instantâneo | Mantém o balanceamento e os testes de mira |
| Nível 3 custa 2,2× a torre | Com habilidades a 1,4×, a melhor estratégia chegava à onda 30; com 2,2×, volta à média 27 |
| Fonte DejaVu e tela cheia do Termux só com confirmação e backup | Mudam o Termux inteiro; o `--remover` restaura byte a byte |

## 7. Limites e pendências conhecidos

- **Nunca testados em aparelho real:** emissor IR com a TV do usuário (inclusive o bit de alternância numa Philips); emojis e fonte no Android; vibração; dificuldade para um jogador humano.
- **Pior caso de desempenho:** 8,7 ms por quadro com 594 efeitos na tela, dentro de um limite de 50 ms.
- **Retorno do usuário ainda não recebido:** marca e modelo da TV, modelo do celular, ondas alcançadas por mapa e capturas.

## 8. Próximos passos recomendados

1. Receber o teste real do usuário (roteiros em `controle-tv/docs/ROADMAP.md` e `tower-defense/docs/ROADMAP.md`) e corrigir o que aparecer.
2. Ajustar a dificuldade com as ondas reais (`HP_GROWTH`, `UPGRADE_PRICE` e os pesos das ondas), refazendo a simulação.
3. Perfis embutidos das marcas do usuário (Philco, TCL, AOC, Semp), só com o modelo confirmado.
4. Controle: segurar VOL/CH repete o envio.
5. Jogo: opção de 30 quadros por segundo; compartilhar mapas por texto.

Relatório completo da última auditoria: `docs/AUDITORIA-2026-09-27.md`.

## 9. Prompt para continuar em outra sessão

Cole este prompt numa sessão nova, com o repositório `matheus23alv-bit/PVN-Controle-Tv` anexado:

```
Continuação do PVN Workspace a partir do marcador PVN-CHECKPOINT-2026-09-27.
Antes de qualquer coisa:
1. Leia CLAUDE.md e CHECKPOINT.md na raiz do repositório.
2. Confira o estado: git fetch origin && git log --oneline -5 origin/claude/tv-remote-control-app-lu248i
   (o checkpoint é o merge do PR #8; se houver commits depois dele, leia os CHANGELOGs).
3. Rode as baterias de teste da seção 5 do CHECKPOINT.md e me diga se estão verdes.
4. Recrie o branch de trabalho claude/tower-defense-termux-yjzaeb a partir da Main.
Depois, siga as regras de entrega do CLAUDE.md (testes, PR e merge na Main, pack zip
e instalar-pack.sh) e responda em português do Brasil.
Próxima tarefa: [descreva aqui, ou peça para seguir a seção 8 do CHECKPOINT.md]
```
