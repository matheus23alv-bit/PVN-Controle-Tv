# Changelog — Tower Defense (Termux)

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento semântico.

## [2.0.0] — 2026-09-26

Jogo refeito para ter visual de jogo dentro do terminal do Termux, com menu, tutorial e mais estratégia. A 1.1.0 está em `legados/v1.1.0/`.

### Visual
- Mapa com emojis em casas de 2 colunas (quadradas na tela): grama com textura, trilha de terra, 🚪 entrada e 🏰 base.
- Torres 🏹 Arqueiro, 💣 Canhão, 🔮 Mago e 🌀 Vórtice; monstros 👾 Invasor, 🐀 Rato, 👹 Ogro e 🐉 Dragão (chefe a cada 5 ondas).
- Monstro ferido muda o fundo (laranja, depois vermelho), pisca branco ao levar tiro, e 💥 marca cada abate.
- Alcance da torre em verde claro ao mover o cursor; fundo da torre mostra o nível (esverdeado no 2, dourado no 3).
- Painéis com moldura, HUD 💗 💰 🌊 💀, seletor de torres destacado e botões de toque.
- Modo sem emoji (Opções ou `--sem-emoji`) com letras coloridas, para celulares que desalinham emojis.

### Adicionado
- Tela inicial com menu (Jogar, Tutorial, Como jogar, Opções, Sair), animação e recorde.
- Tutorial interativo de 9 passos dentro do jogo: destaca a casa, espera a ação do jogador e explica o resultado.
- Menu de pausa (toque no topo ou `p`) e tela de fim de jogo com placar, "Novo recorde" e "Jogar de novo".
- Recorde salvo em `~/.config/td-termux/config.json`.
- Quarta torre, Vórtice: deixa lentos os monstros perto do alvo (o chefe resiste mais).
- Melhoria de torres até o nível 3 (`u` ou dois toques na torre): +60% de dano e +0,4 de alcance por nível.
- Canhão com dano em área (50% nos vizinhos do alvo).
- Velocidade 2× (`f`) e bônus de ouro no fim de cada onda.
- Instalador com moldura, barra de teclas nova (1–4, u, x, p, n, f, h) e opção de abrir o tutorial ao terminar.
- Opções `--tutorial` e `--jogar`.

### Corrigido
- Depois de um toque, o jogo congelava até a próxima tecla: o evento de soltar o dedo era descartado pelo ncurses e bloqueava a leitura, ignorando o tempo limite.

### Balanceamento
- Dificuldade calibrada por simulação: vida dos monstros cresce 16% por onda; ouro por abate cresce devagar. Melhorar torres passou a render mais que espalhar torres: o jogador automático que melhora chega à onda ~27 com ~54 torres; o que só constrói Arqueiros para na ~25 com o mapa lotado.

### Desempenho
- 3,2 ms por quadro no pior caso medido (151 torres, 120 monstros, todas atirando), para um orçamento de 50 ms.
- Parado entre ondas o jogo não redesenha a tela: 0,05% de CPU.

## [1.1.0] — 2026-09-25

### Adicionado
- `instalar.sh`: instala com um comando (local ou `curl | bash`), verifica Python e curses, cria os comandos `td` e `tower-defense`, e opcionalmente troca a barra de teclas extras do Termux por uma feita para o jogo, com backup. `--remover` desinstala e restaura a barra original byte a byte.
- Toque na tela: tocar numa célula move o cursor, tocar de novo constrói; tocar no seletor escolhe a torre; tocar no rodapé chama a onda ou reinicia. `--sem-toque` desativa.
- Ajuda dentro do jogo (`h`), com a versão lida do arquivo `VERSION`.
- Opções de linha de comando `--versao`, `--ajuda` e `--sem-toque`.
- Aviso "Aguarde o fim da onda" ao apertar `n` durante uma onda.

### Corrigido
- Com o teclado do celular aberto a tela do Termux encolhe e o jogo ficava bloqueado em "Tela pequena demais" (mínimo era 36×21). O layout agora se adapta: mínimo 32×16, controles aparecem quando há espaço e a ajuda fica no `h`.
- Na confirmação de saída, apertar `s` para descer o cursor encerrava o jogo. Agora só `q`/Esc de novo confirma; qualquer outra tecla cancela.
- Segurar uma tecla (ou digitar rápido) criava fila: o jogo lia uma tecla por quadro e o cursor andava atrasado. Agora todas as teclas pendentes são lidas a cada quadro.
- O tempo de recarga das torres corria durante a pausa; agora usa o relógio do jogo.

### Desempenho
- Mira das torres de 11× a 15× mais rápida (0,81 → 0,07 ms por quadro com 150 torres; 2,59 → 0,17 ms com 300), com resultado idêntico ao algoritmo anterior comprovado em 500 cenários aleatórios.
- Jogo parado (entre ondas, pausa, ajuda) usa 10× menos CPU (1,17% → 0,12%): deixa de redesenhar 30 vezes por segundo e espera a próxima tecla.
- Desenho do mapa agrupa células vizinhas de mesma cor em uma única escrita.

## [1.0.1] — 2026-09-25

### Corrigido
- Jogo impossível de perder: a vida dos inimigos crescia de forma linear e a economia sempre vencia (em simulação, qualquer estratégia passava de 40 ondas). Agora cresce 18% por onda de forma composta; um jogador automático perfeito chega à onda ~28.
- Em telas de 40 colunas (Termux em retrato) o painel de torres e a linha de controles ficavam cortados. HUD e controles foram reescritos para caber em 36 colunas.
- A última coluna da tela nunca era desenhada.
- Em tela menor que o grid, o mapa e a base ficavam cortados sem aviso. Agora aparece "Tela pequena demais" com o tamanho atual e o mínimo, e o jogo fica pausado até a tela caber.
- `q` ou Esc (que fica ao lado das setas na barra do Termux) encerrava a partida na hora. Agora pede confirmação durante a partida.
- Esc demorava cerca de 1 s para responder (`ESCDELAY` padrão do curses).

### Adicionado
- `r` inicia nova partida depois de perder. Antes era preciso sair e abrir o jogo de novo.
- Linha de status com dica "Pressione n para a próxima onda" entre ondas.

### Interno
- Estado da partida agrupado em `new_game()`; removida a variável global `PATH`.

## [1.0.0] — 2026-09-25

Versão inicial: grid 32×13, 3 torres, 3 inimigos, ondas infinitas, venda de torres e pausa. Preservada em `legados/v1.0.0/`.
