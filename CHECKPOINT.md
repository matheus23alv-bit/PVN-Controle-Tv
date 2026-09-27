# Checkpoint — PVN Workspace

**Marcador:** `PVN-CHECKPOINT-2026-09-27b` · controle **2.1.0** · Tower Defense **3.2.0** · Teclado Termux **1.0.0** · todas as baterias verdes.

Este arquivo existe para continuar o projeto em outra sessão sem perder contexto.
- **Marcador anterior:** `PVN-CHECKPOINT-2026-09-27`, o da auditoria (PR #8), com o controle 2.0.2 e o jogo 3.1.2.
- **Este:** entra pelo PR do Teclado Termux.
- **Hash exato do commit:** está no resultado de `git log -1 --format=%H -- CHECKPOINT.md`.

Para continuar só o jogo, use `tower-defense/docs/CHECKPOINT.md` (marcador `TD-CHECKPOINT-2026-09-27b`).

## 1. Estado atual

| Item | Valor |
|---|---|
| Repositório | `matheus23alv-bit/PVN-Controle-Tv` |
| Branch principal (a "Main" do usuário) | `claude/tv-remote-control-app-lu248i`, que é o branch padrão |
| Branch de trabalho das sessões | `claude/tower-defense-termux-yjzaeb`, recriado a partir da Main depois de cada merge |
| Histórico de merges | #1 a #7; #8, a auditoria; #9, o pack e o checkpoint só do Tower Defense; e o PR do Teclado Termux |
| Controle TV | 2.1.0: controle IR real pelo emissor do celular, com a LG conferida inteira e o VOL que repete ao segurar |
| Tower Defense | 3.2.0: jogo de terminal em tela cheia retrato, com editor de mapas e barra de teclas automática |
| Teclado Termux | 1.0.0: comando `teclas`, com as barras de teclas do Termux |
| TV do usuário | **LG** (informada em 2026-09-27) |
| Testes | controle 31/39/9 · jogo 75/99/29 · teclado 29/21/19 · pack 37 |

## 2. Os três projetos

**`controle-tv/`**: controle remoto de TV pelo **emissor infravermelho do próprio celular**, usando o Termux:API (`termux-infrared-transmit`).
- **Código:** `source/tv.py`, um arquivo só, com biblioteca padrão e `curses`.
- **Protocolos:** NEC, NECext, Samsung32, Sony SIRC 12/15/20, RC5/RC5X e RC6 (com bit de alternância) e raw.
- **Marcas embutidas:**
  - Samsung, LG e Sony, com os códigos conferidos contra os publicados;
  - na LG, os 27 botões: NEC, endereço 04, LIGAR = `20DF10EF`.
- **Outras marcas:** importa arquivos `.ir` do Flipper-IRDB.
- **Telas:** controle, escolha da TV (com rolagem), descobrir TV e ajuda.
- **Volume:** PgUp e PgDn são VOL+ e VOL−. Segurar repete, sem fila acumulada.
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

**`teclado-termux/`**: comando `teclas`, que troca a barra de teclas extras do Termux. Só mexe na linha `extra-keys` do `~/.termux/termux.properties`.
- **Código:** `source/teclas.py`, um arquivo só, com biblioteca padrão e `curses`.
- **Perfis:**
  - **padrão melhorado:** 📺 abre a TV, 🏰 o jogo e TECLAS o menu; ao deslizar para cima, dá ^C, ~, |, PGUP, PGDN, limpar e colar;
  - **jogo;**
  - **TV:** VOL no PGUP e no PGDN, que o Termux repete ao segurar;
  - **padrão do Termux;**
  - **a barra de antes da pessoa.**
- **Troca automática:** `teclas --entrar <perfil>` e `--sair`, chamados pelo `tv` e pelo `td`.
  - A barra anterior volta idêntica.
  - Uma trava de arquivo põe as trocas em ordem.
  - A barra fixada pelo instalador do td 3.1 é reconhecida.
- **Gravação:** emojis e acentos vão como `\uXXXX`. Depois de cada troca, o Termux recarrega com `termux-reload-settings`.
- **Configuração:** `~/.config/teclas/estado.json` e o backup `termux.properties.antes-do-teclas`. Instala em `~/.local/share/teclado-termux`, com o comando `teclas`.

**Raiz:**
- `setup-teste.sh`: instala os três projetos, o teclado primeiro, ou só o que vier no pack.
- `empacotar.sh`: gera o pack zip com o `PACK-INFO.txt` (versões, inclusive a do teclado) e o SHA-256 de cada arquivo. Com `td` no fim, o pack leva só o jogo.
- `instalar-pack.sh`: instala do zip na pasta Download do celular.
- `testes/test_pack.sh`: testa essas três ferramentas e os três projetos juntos (a barra trocando de verdade).
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
8. **Linha de comando:** `--jogar`, `--editor`, `--mapas`, `--gerar`, `--validar`, `--importar`, `--tutorial`, `--sem-emoji`, `--sem-toque`, `--versao` e `--ajuda`. O `teclas()` troca a barra ao abrir e fechar.

**`controle-tv/source/tv.py`** (cerca de 1.000 linhas):

1. Codificadores IR e `encode(signal, toggle)`.
2. Nomes, apelidos (`canon`) e marcas embutidas.
3. `parse_ir_file` e `import_profile`.
4. `Transmitter`, com tempo limite e `TV_IR_TIMEOUT`.
5. `Worker`: envio fora do laço da tela, que descarta a fila se o Termux:API travar.
   - `submit` com `REPEATABLE`, `HELD=0.15` e `MAX_QUEUED=3`: tecla segurada não acumula.
6. `App`, `cli` e `teclas()`.

**`teclado-termux/source/teclas.py`** (cerca de 700 linhas):

1. **Perfis** (`PROFILES`, `TERMUX_DEFAULT`) e `render()`, que gera a linha `extra-keys` com `\uXXXX`.
2. **Arquivo:** `find_blocks` (valores em várias linhas e marcas), `current_block`, `block_value`, `detect` e `replace_block`.
3. **Estado e trocas:**
   - `apply`, `enter` e `leave`, com trava (`fcntl.flock`);
   - `remember_original`, que cobre a migração do td 3.1;
   - `remove`.
4. **`Menu`:** a tela com toque e prévia.
5. **`main`:** a linha de comando.

## 4. Regras que valem sempre

Resumo do `CLAUDE.md`, que é carregado automaticamente em toda sessão.

- **Entrega:**
  1. testes;
  2. PR para a Main e merge;
  3. pack zip gerado do commit mesclado: `git fetch origin && bash empacotar.sh <pasta> origin/claude/tv-remote-control-app-lu248i` (acrescente `td` numa sessão só do jogo);
  4. o zip e o `instalar-pack.sh` enviados como arquivos;
  5. resposta dizendo o que mudou, o resultado dos testes, o comando de instalação e o que testar.
- **Onde roda:** os três projetos rodam no terminal do Termux, nunca no navegador. O simulador web é legado.
- **Independência:** o `tv` e o `td` só chamam o comando `teclas` se ele existir. Sem o teclado, os dois funcionam igual.
- **Estrutura:** cada projeto tem `source/` (só arquivos de funcionamento + `VERSION` + `CHANGELOG.md` + `LEIA-ME.md`), `legados/`, `testes/` e `docs/`.
- **Versão:** um `VERSION` por projeto. Toda mudança de código sobe a versão e ganha entrada no CHANGELOG. Versões maiores e menores guardam a anterior em `legados/`.
- **Idioma e instaladores:** tudo em português do Brasil. Os instaladores baixam pelo `HEAD` do repositório.
- **Estilo de resposta do usuário:** títulos curtos, parágrafos curtos, tabelas para comparar e perguntas de múltipla escolha (A, B, C, D) só quando a decisão muda o resultado. Ele gosta de receber o diff, o relatório e os detalhes. Não bajular e não enrolar.

## 5. Testar e revisar

```bash
cd controle-tv && python3 -m unittest testes/test_ir.py && bash testes/test_tela.sh && bash testes/test_instalador.sh
cd tower-defense && python3 -m unittest testes/test_logica.py && bash testes/test_terminal.sh && bash testes/test_instalador.sh
cd teclado-termux && python3 -m unittest testes/test_teclas.py && bash testes/test_tela.sh && bash testes/test_instalador.sh
bash testes/test_pack.sh                                        # na raiz
python3 tower-defense/testes/simulacao_balanceamento.py tower-defense/source/td.py 3   # ~2 min
python3 -m pyflakes controle-tv/source/tv.py tower-defense/source/td.py teclado-termux/source/teclas.py
```

- **Pré-requisitos:** os testes de tela precisam de `tmux`. O controle usa o Termux:API falso de `controle-tv/testes/mock-termux-api/`, e `TV_MOCK_ATRASO` imita a demora do envio.
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
| Barra de teclas num projeto próprio (`teclado-termux`), trocada ao abrir e fechar os apps | O usuário quer três barras (dia a dia, jogo, TV) e a volta à dele; a barra fixa pelo instalador do jogo não tinha volta fácil |
| VOL da barra da TV no PGUP e no PGDN | São teclas que o Termux repete sozinho ao segurar; o controle descarta as repetições enquanto o sinal anterior não saiu |
| O teclas mexe só na linha `extra-keys` e grava `\uXXXX` | Não estraga o resto do `termux.properties` e funciona em qualquer versão do Termux |

## 7. Limites e pendências conhecidos

- **Nunca testados em aparelho real:**
  - emissor IR com a TV LG do usuário;
  - emojis e fonte no Android;
  - vibração;
  - dificuldade para um jogador humano;
  - a barra de teclas trocando no Termux real;
  - o intervalo de repetição do Termux, que o controle presume em cerca de 0,08 s.
- **Pior caso de desempenho:** 8,7 ms por quadro com 594 efeitos na tela, dentro de um limite de 50 ms.
- **Retorno do usuário ainda não recebido:**
  - modelo da TV LG (etiqueta de trás) e se ligou;
  - modelo do celular;
  - ondas alcançadas por mapa;
  - capturas.

## 8. Próximos passos recomendados

1. **Teste real do usuário:** receber o resultado dos roteiros e corrigir o que aparecer. Os roteiros estão em:
   - `controle-tv/docs/ROADMAP.md`;
   - `tower-defense/docs/ROADMAP.md`;
   - `teclado-termux/docs/ROADMAP.md`.
2. **Dificuldade:** ajustar com as ondas reais (`HP_GROWTH`, `UPGRADE_PRICE` e os pesos das ondas), refazendo a simulação.
3. **Controle:** uma segunda página de botões LG (Guia, Q.Menu, cores, play e pausa, ligar e desligar separados).
4. **Perfis embutidos de outras marcas do usuário:** só com o modelo confirmado.
5. **Jogo:** opção de 30 quadros por segundo; compartilhar mapas por texto.

Relatório completo da última auditoria: `docs/AUDITORIA-2026-09-27.md`.

## 9. Prompt para continuar em outra sessão

Cole este prompt numa sessão nova, com o repositório `matheus23alv-bit/PVN-Controle-Tv` anexado:

```
Continuação do PVN Workspace a partir do marcador PVN-CHECKPOINT-2026-09-27b.
Antes de qualquer coisa:
1. Leia CLAUDE.md e CHECKPOINT.md na raiz do repositório.
2. Confira o estado: git fetch origin && git log --oneline -5 origin/claude/tv-remote-control-app-lu248i
   (se houver commits depois do checkpoint, leia os CHANGELOGs).
3. Rode as baterias de teste da seção 5 do CHECKPOINT.md e me diga se estão verdes.
4. Trabalhe no branch que a sessão indicar, criado a partir da Main.
Depois, siga as regras de entrega do CLAUDE.md (testes, PR e merge na Main, pack zip
e instalar-pack.sh) e responda em português do Brasil.
Próxima tarefa: [descreva aqui, ou peça para seguir a seção 8 do CHECKPOINT.md]
```
