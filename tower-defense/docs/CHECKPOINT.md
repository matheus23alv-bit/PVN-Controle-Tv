# Checkpoint — Tower Defense

**Marcador:** `TD-CHECKPOINT-2026-09-27b` · Tower Defense **3.2.0** · baterias verdes (lógica 75, tela 99, instalador 29, pack 37). O marcador anterior, `TD-CHECKPOINT-2026-09-27`, era a 3.1.2.

Este é o checkpoint só do jogo, para continuar o Tower Defense em outra sessão sem depender do controle da TV. A versão anterior deste checkpoint entrou pelo PR #9; esta entra pelo PR do Teclado Termux. O do repositório inteiro é o `CHECKPOINT.md` da raiz. O hash exato do commit está no `MARCADOR-DE-CONTINUIDADE.txt` do pack de continuidade, ou em `git log -1 --format=%H -- tower-defense/docs/CHECKPOINT.md`.

## 1. Estado atual

| Item | Valor |
|---|---|
| Repositório | `matheus23alv-bit/PVN-Controle-Tv`, pasta `tower-defense/` |
| Branch principal (a "Main") | `claude/tv-remote-control-app-lu248i`, o branch padrão |
| Branch de trabalho | `claude/tower-defense-termux-yjzaeb` (ou o que a sessão indicar), sempre recriado a partir da Main |
| Versão | 3.2.0: a barra de teclas do jogo entra só com o `td` aberto (Teclado Termux) |
| Instalado no celular | `~/.local/share/tower-defense`, comando `td` (e `tower-defense`) |
| Dados do jogador | `~/.config/td-termux/config.json` (opções e recordes) e `~/.config/td-termux/mapas/*.mapa` |
| Fora do escopo | `controle-tv/` e `teclado-termux/` (exceto o perfil `jogo`), projetos independentes no mesmo repositório. O outro tower defense do usuário, complexo, também é separado |
| Barra de teclas | Do `teclado-termux/` (comando `teclas`). O `td` só chama `teclas --entrar jogo` e `teclas --sair`, se o comando existir |

## 2. O jogo

Tower defense de terminal para o Termux, em tela cheia com o celular em pé (layout 9:16). É um único arquivo Python, `source/td.py`, que usa só a biblioteca padrão e `curses`. Joga-se inteiro pelo toque ou pelo teclado.

- **Visual:** emojis em casas de 2 colunas, com escala automática de 1× a 3× (casa = 2k colunas × k linhas). O modo sem emoji usa letras coloridas.
- **Telas:** menu, tutorial de 9 passos jogando de verdade, Mapas, Criar mapa (editor), Como jogar, Opções e Ajustar tela (régua de emojis, tela cheia e fonte DejaVu).
- **Mapas:** 3 prontos (Serpente, Espiral, Rio), gerador por semente, editor na tela e arquivos `.mapa` em texto (`. # S B T ~`), de 5×5 a 24×40.
- **Efeitos só visuais:** tiros voando, explosão, raio, anel, números de dano, faixas de onda e de chefe, barra do chefe, tremida e vibração (`termux-vibrate`). O dano é instantâneo.

| Torre | Custo | Alcance | Dano | Intervalo | Nível 3 |
|---|---|---|---|---|---|
| 🏹 Arqueiro | 20 | 3,0 | 6 | 0,5 s | 2 alvos por tiro |
| 💣 Canhão | 50 | 2,3 | 20 | 1,4 s | explosão de 1,1 → 1,6 casa |
| 🔮 Mago | 35 | 4,0 | 10 | 0,9 s | raio atravessa 1,2 casa; sempre vê fantasma e ignora casco |
| 🌀 Vórtice | 40 | 2,6 | 4 | 0,8 s | congela 0,5 s (lentidão normal: 50% por 1,6 s, área 1,2) |

Cada nível dá +60% de dano e +0,4 de alcance. O nível 2 custa 0,7× a torre e o nível 3 custa 2,2×. Vender devolve metade do gasto. Cada torre tem mira própria: 1º, forte ou perto.

| Monstro | Vida | Veloc. | Ouro | Onda | Detalhe |
|---|---|---|---|---|---|
| 👾 Invasor | 28 | 1,5 | 4 | 1 | comum |
| 🐀 Rato | 15 | 2,6 | 4 | 2 | rápido |
| 👹 Ogro | 100 | 0,85 | 10 | 3 | tira 2 💗 |
| 🐌 Lesma | 70 | 0,75 | 7 | 4 | se cura depois de 1 s sem apanhar |
| 🐢 Tartaruga | 55 | 0,95 | 8 | 5 | casco −4 por tiro |
| 🦇 Morcego | 24 | 2,1 | 6 | 6 | nunca fica lento |
| 👻 Fantasma | 40 | 1,3 | 8 | 8 | some; sumido, só o Mago vê |
| 🐉 Dragão | 520 | 0,6 | 50 | a cada 5 | chefe, tira 5 💗, chama 3 ratos |

**Economia:** 100 de ouro, 20 vidas, vida dos monstros +16% por onda, 4 + 2n monstros por onda (até 60), com saída a cada 0,7 s.

## 3. Mapa do código

**`source/td.py`** (3.189 linhas). Os números de linha são aproximados e servem para achar o bloco.

| Linhas | Bloco | Conteúdo |
|---|---|---|
| 1–147 | Constantes e configuração | `TOWERS`, `ENEMIES`, economia, cores (`LEVEL_BG`, `FIRE_BG`, `RANGE_BG`), `GLYPHS`, `load_config`, `clean_config`, `save_config` |
| 149–559 | Motor de mapas | `MapError` (com mensagem curta), `Mapa` (`trace`, `check`, `from_text`, `to_text`), `_snake`, `_decorate`, `_zigzag`, `generate_map`, mapas prontos, `user_maps`, `save_user_map`, `resolve_map` |
| 561–982 | Lógica | `Tower`, `Enemy`, `Fx`, `target_key`, `make_wave` e `Game` (`_step`, `_fire` com busca binária na trilha, `_hit`, `_summon`, eventos de vibração) |
| 984–1085 | Editor sem tela | `Editor`: pintar, trilha pelos cantos, desfazer (80 passos), redimensionar e gerar |
| 1087–1129 | Tutorial | `tutorial_spots` e `tutorial_steps` |
| 1131–1334 | Utilidades de tela | `text_width`, `clip`, `wrap`, `fit` (texto longo/curto), `short_num`, `termux_screen_state`, `Palette` (256 ou 8 cores), `Layout`, `compute_layout`, `texture` |
| 1336–3040 | `App` | pares `key_<tela>` e `draw_<tela>`; `do_upgrade`, `do_mode` e `do_sell`; `draw_sprites` e `draw_effects` com mapa de ocupação (nada corta emoji ao meio); `draw_tela`; `run()` |
| 3042–3189 | Linha de comando | `USAGE`, `--mapas`, `--gerar`, `--validar`, `--importar`, `main` (Ctrl+C sai com 130) e `teclas()`, que troca a barra ao abrir e fechar |

**Outros arquivos:**
- `source/instalar.sh`: instala, atualiza e remove. Flags `--tela-cheia`, `--fonte`, `--so-tela` e `--remover`, que restaura byte a byte. As versões `--sem-…` também existem. Desde a 3.2.0, não mexe na barra de teclas; `--teclas` é aceito e só avisa.
- `source/fontes/`: DejaVu Sans Mono e a licença dela.
- **`testes/`:**
  - `test_logica.py`: unidade, inclui o gabarito de força bruta da mira.
  - `test_terminal.sh`: tela real no tmux; o `tela.py` acha botões e casas.
  - `test_instalador.sh`.
  - `simulacao_balanceamento.py`: jogadores automáticos.
  - `benchmark.py`.
- `docs/`: este checkpoint, `RELATORIO-TESTES.md`, `ROADMAP.md` (roteiro de 15 passos no celular) e `capturas/` (8 PNGs).
- `legados/`: v1.0.0, v1.1.0, v2.0.1, v3.0.0 e v3.1.2.

## 4. Regras

- **Entrega:**
  1. testes do jogo e do pack;
  2. PR para a Main e merge;
  3. pack só do jogo, gerado do commit mesclado: `git fetch origin && bash empacotar.sh <pasta> origin/claude/tv-remote-control-app-lu248i td`;
  4. enviar o zip e o `instalar-pack.sh`;
  5. responder com o que mudou, o resultado dos testes, o comando de instalação e o que testar.
- **Escopo:** sessões do jogo não mexem em `controle-tv/`. A barra de teclas do jogo mora no `teclado-termux/source/teclas.py` (perfil `jogo`). Mudar uma tecla do jogo exige mexer lá também e subir a versão do teclado.
- **Versão:** toda mudança de código sobe `source/VERSION` e ganha entrada no `source/CHANGELOG.md`. Versão maior guarda a anterior em `legados/`. `source/` tem só os arquivos de funcionamento, `VERSION`, `CHANGELOG.md` e `LEIA-ME.md`.
- **Tela:** só emojis de largura "W" (2 colunas). Textos de interface com versão longa e curta (`fit`). Nada desenhado pode cortar um emoji ao meio (mapa de ocupação).
- **Idioma e estilo:** tudo em português do Brasil. O usuário quer resposta direta, sem bajulação, com o diff, o relatório e os detalhes, e perguntas A/B/C/D só quando a decisão muda o resultado.

## 5. Testar e revisar

```bash
cd tower-defense
python3 -m unittest testes/test_logica.py        # 75
bash testes/test_terminal.sh                     # 99, precisa de tmux, ~2 min
bash testes/test_instalador.sh                   # 29
python3 testes/simulacao_balanceamento.py source/td.py 3   # ~2 min
python3 -m pyflakes source/td.py
cd .. && bash testes/test_pack.sh                # 37, inclui o pack só do jogo e a troca da barra
```

**Revisão visual:** abra `td` numa sessão do tmux em 46×50 e rode `bash testes/captura.sh <sessão> <nome>` na raiz. O PNG sai com a fonte de emoji do Android.

## 6. Decisões já tomadas (não reabrir sem motivo)

| Decisão | Motivo |
|---|---|
| Jogo próprio e leve, com visual de emojis | Escolha do usuário; o outro tower defense dele é separado |
| Casas de 2 colunas, só emojis "W" | Alinhamento previsível no Termux; o modo sem emoji é a reserva |
| Tela cheia em retrato com escala automática | O mapa preenche a altura; com teclado aberto, volta à escala 1 (mínimo 30×24) |
| Trilha pelos cantos no editor | Arrastar o dedo no Termux vira rolagem, não pintura |
| Efeitos só visuais e dano instantâneo | Mantém o balanceamento e o gabarito da mira |
| Duração dos efeitos em segundos reais | Em 2× os efeitos não somem pela metade |
| Nível 3 custa 2,2× a torre | Com habilidades a 1,4×, a melhor estratégia chegava à onda 30; com 2,2×, volta à média 27 |
| Tela cheia e fonte só com confirmação e backup | Mudam o Termux inteiro; o `--remover` restaura byte a byte |
| Barra do jogo só com o `td` aberto, pelo `teclas` | A barra fixa pelo instalador (até a 3.1) não tinha volta fácil; o usuário quer três barras (dia a dia, jogo, TV) e a dele de antes |

## 7. Última auditoria (2026-09-27), parte do jogo

| # | Gravidade | Problema | Correção |
|---|---|---|---|
| T1 | Alta | O gerador falhava em mapas de 5 casas, e 🎲 Gerar derrubava o editor | Zigue-zague para mapas estreitos; o editor mostra uma mensagem |
| T2 | Alta | Um `config.json` com tipo errado impedia o jogo de abrir | Valores inválidos descartados na leitura (`clean_config`) |
| T4 | Alta | `q` com a tela pequena no editor perdia o mapa sem salvar | `q` não fecha com mudanças pendentes, e aparece um aviso |
| T3 | Média | Ctrl+C despejava `KeyboardInterrupt` | Saída limpa, código 130 |
| T5 | Baixa | Processo de vibração solto se o Termux:API travasse | Encerrado na saída |
| T6 | Baixa | Mensagem do gerador cortada em 46 colunas | Versão curta |

Relatório completo, com o controle: `docs/AUDITORIA-2026-09-27.md` na raiz.

**Depois da auditoria:**
- o pack ganhou a opção só do jogo (`empacotar.sh … td`), e o `setup-teste.sh` passou a instalar só o que vier no pack;
- a 3.2.0 passou a barra de teclas ao Teclado Termux.

## 8. Limites e pendências

- **Nunca testado em aparelho real:**
  - emojis e fonte na tela do Android;
  - tela cheia;
  - barra de teclas trocando no Termux real (`termux-reload-settings`);
  - vibração;
  - toque;
  - dificuldade sentida por um jogador humano.
- **Desempenho no pior caso:** 8,7 ms por quadro com 120 torres, 120 monstros e 594 efeitos, num limite de 50 ms.
- **Falta o retorno do usuário:**
  - modelo do celular;
  - onda alcançada em cada mapa pronto;
  - capturas de qualquer desalinhamento;
  - resultado da régua em Opções → Ajustar tela.

## 9. Próximos passos recomendados

1. **Teste no celular:** receber o resultado do roteiro em `docs/ROADMAP.md` e corrigir o que aparecer.
2. **Dificuldade:** ajustar com as ondas reais (`HP_GROWTH`, `UPGRADE_PRICE` e os pesos das ondas) e refazer a simulação.
3. **30 quadros por segundo:** opção na escala 2, para movimento mais fluido; gasta um pouco mais de bateria.
4. **Compartilhar mapa por texto:** copiar e colar o `.mapa`, que já é texto.
5. **Chamar a onda antes da hora:** com bônus de ouro.
6. **Pintar arrastando no editor:** depende do comportamento do arraste no aparelho.
7. **Duas entradas ou dois caminhos:** custo alto, porque muda o motor de trilha e a validação.
8. **Sons curtos com `termux-media-player`:** opcional.

## 10. Prompt para continuar em outra sessão

Cole numa sessão nova com o repositório `matheus23alv-bit/PVN-Controle-Tv` anexado:

```
Continuação do Tower Defense (PVN Workspace) a partir do marcador TD-CHECKPOINT-2026-09-27b.
Escopo: só a pasta tower-defense/. Não altere o controle-tv; o teclado-termux só se a barra do jogo mudar.
Antes de qualquer coisa:
1. Leia CLAUDE.md na raiz e tower-defense/docs/CHECKPOINT.md.
2. Confira o estado: git fetch origin && git log --oneline -5 origin/claude/tv-remote-control-app-lu248i
   (se houver commits no jogo depois do checkpoint, leia tower-defense/source/CHANGELOG.md).
3. Rode as baterias do jogo e a do pack (seção 5 do checkpoint) e me diga se estão verdes.
4. Trabalhe no branch que a sessão indicar, criado a partir da Main.
Entrega: testes, PR e merge na Main, pack só do jogo
(git fetch origin && bash empacotar.sh <pasta> origin/claude/tv-remote-control-app-lu248i td)
e instalar-pack.sh; respostas em português do Brasil.
Próxima tarefa: [descreva aqui, ou peça para seguir a seção 9 do checkpoint]
```
