# Changelog — Tower Defense (Termux)

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento semântico.

## [3.1.2] — 2026-09-27

Correções da auditoria de 2026-09-27.

### Corrigido
- O gerador de mapas falhava em mapas com 5 casas de largura ou altura, que o formato aceita. Com um mapa desses aberto no editor, tocar em 🎲 Gerar fechava o jogo com erro. Agora esses tamanhos recebem uma trilha em zigue-zague, e o editor mostra uma mensagem em vez de cair se algo der errado.
- Um `config.json` com tipos errados (ex.: editado à mão, `"recordes"` como lista) impedia o jogo de abrir. Agora os valores inválidos são descartados na leitura.
- Ctrl+C despejava um erro técnico (KeyboardInterrupt) no terminal. Agora o jogo sai limpo, com código 130, como o controle.
- No editor, com a tela pequena demais (ex.: teclado aberto), tocar `q` fechava o jogo e perdia o mapa sem salvar. Agora `q` não fecha enquanto houver mudanças sem salvar, e o aviso diz "Mapa sem salvar: aumente a tela para salvar".
- Se o Termux:API travasse durante uma vibração, o processo ficava solto depois de sair do jogo. Agora ele é encerrado na saída.
- Mensagem do gerador no editor com versão curta, para caber em telas estreitas.

### Testes
- 4 testes de lógica novos (75 no total) e 5 de tela (95 no total).

## [3.1.1] — 2026-09-26

### Corrigido
- Instalador: ao instalar a fonte do jogo num Termux sem fonte própria, a mensagem dizia "a sua ficou em ~/.termux/font.ttf.antes-do-td", mas não havia backup (não existia fonte antes). Agora diz "antes era a fonte padrão". O `--remover` já apagava a fonte corretamente nesse caso.

## [3.1.0] — 2026-09-26

Legibilidade na tela do Android, efeitos de combate, tela cheia e fonte do Termux, e mais estratégia nas torres. A 3.0.0 está em `legados/v3.0.0/`.

### Corrigido
- Placar estourava em tela estreita: com ouro e abates altos, ele passava de 30 colunas e o botão `||` cobria o fim. Agora ele encolhe em etapas (espaços menores, depois 1,7k/17M, depois sem abates) e os números têm largura fixa para não empurrar o resto.
- Textos cortados em telas estreitas (ex.: "Toque numa casa de grama para c"): painel, linha da onda, editor, botões e mensagens têm versão longa e curta, escolhida pela largura.
- O brilho do monstro atingido durava 0,08 s de jogo (0,04 s em 2×, menos que um quadro) e quase nunca aparecia. Agora dura 0,15 s reais e acontece quando o tiro chega.
- Células pretas no mapa: quando dois emojis se encostavam por uma coluna, o terminal apagava a metade cortada. Agora monstros, efeitos e rótulos só ocupam células livres.
- Monstros empilhados se escondiam: agora aparecem lado a lado (escala 2) e com um contador de quantos há no lugar.

### Efeitos de combate (só visuais: o dano continua instantâneo)
- 🏹 flecha "•" e 💣 bala "●" voam até o alvo; a explosão do Canhão pinta de laranja a área exata do dano; o 🔮 Mago solta um raio magenta; o 🌀 Vórtice pulsa um anel azul.
- A plataforma da torre dá um clarão a cada tiro.
- Morte em dois tempos: o monstro fica até o tiro chegar, depois 💥 e 💨; o "+ouro" sobe em seguida.
- Números de dano (escala 2): somados a cada 0,3 s por monstro, cinza quando o casco da Tartaruga reduz o dano. Dá para desligar em Opções.
- "imune" quando o Vórtice tenta deixar lento um Morcego; monstro congelado fica azul-claro.
- Faixas no meio do mapa: "ONDA N", "CHEFE CHEGOU" e "CHEFE DERROTADO +ouro"; a barra de vida do Dragão aparece no topo enquanto ele está vivo.
- O mapa treme quando um monstro entra na base.
- Vibração pelo Termux:API (`termux-vibrate`) quando um monstro entra na base e quando o chefe chega ou morre. Dá para desligar em Opções.
- Botões piscam ao toque.

### Torres
- Habilidade no nível 3 (★★): Arqueiro atira em 2 monstros; Canhão tem explosão meia casa maior; o raio do Mago atravessa e acerta também quem vem logo atrás; o Vórtice congela o alvo por 0,5 s (chefe e morcego não).
- Mira por torre: o mais adiantado (padrão), o de mais vida ou o mais perto. Botão 🎯 na barra de ações ou tecla `t`.
- O painel da torre mostra o dano por segundo, os abates dela e a mira.
- Barra de ações com 5 botões: Onda, velocidade, 🎯 Mira, ⏫ Melhorar e 💲 Vender.

### Tela e fonte do Termux
- Opções → **Ajustar tela**: mostra colunas × linhas, a escala e o tamanho necessário para a próxima, uma régua para conferir se cada emoji e símbolo cabe nas suas 2 colunas, e botões para ativar a tela cheia e a fonte do jogo.
- Instalador: `--tela-cheia` (esconde as barras do Android, com a correção do teclado, e zera a margem lateral), `--fonte` (DejaVu Sans Mono em `~/.termux/font.ttf`, com ★ e barras sem falhas), `--so-tela` (só essas opções, sem reinstalar) e as versões `--sem-...`. Tudo com backup; `--remover` devolve a configuração e a fonte originais byte a byte.
- A fonte acompanha o jogo em `fontes/`, com a licença (Bitstream Vera/DejaVu, redistribuível).

### Balanceamento
- O nível 3 custa 2,2× o preço da torre (antes 1,4×): com as habilidades, melhorar ficou forte demais (onda 30 em todos os mapas). Com o preço novo, o jogador automático que mistura e melhora chega à onda 27 em média (3.0: 26,8).

### Desempenho
- Pior caso medido: 120 torres atirando em todo quadro com 594 efeitos na tela, 8,7 ms por quadro (orçamento de 50 ms).

## [3.0.0] — 2026-09-26

Tela cheia em retrato (9:16), monstros novos com andar suave e criador de mapas dentro do jogo. A 2.0.1 está em `legados/v2.0.1/`.

### Tela cheia vertical
- O jogo ocupa a tela inteira do celular em pé. Cada casa cresce em escala (1×, 2× ou 3×) até o mapa preencher a altura: num celular comum (≈46×50 caracteres) cada casa vira 4 colunas × 2 linhas.
- Mapas em retrato (11×19). Placar e botão de pausa (`||`) no topo; prévia da próxima onda logo abaixo.
- Controles embaixo, ao alcance do polegar: barra de torres (4 botões com custo e nome) e barra de ações (▶ Onda, ⏩ velocidade, ⏫ Melhorar, 💲 Vender). Melhorar e Vender agem na torre do cursor e mostram o preço.
- Fundo escuro em toda a tela; em telas menores (teclado aberto) o jogo volta à escala 1 sozinho.
- Torres mostram o nível com ★ acima do emoji; a entrada pisca quando nasce um monstro; a base pisca vermelho quando um monstro chega.

### Monstros e caminhada
- Quatro monstros novos, liberados aos poucos: 🐌 Lesma (onda 4, se cura depois de 1 s sem apanhar), 🐢 Tartaruga (onda 5, casco tira 4 de dano de cada tiro), 🦇 Morcego (onda 6, rápido e nunca fica lento) e 👻 Fantasma (onda 8, some por 1,2 s a cada 3,7 s; sumido, só o Mago o vê).
- O 🐉 Dragão, ferido pela metade, chama 3 ratos uma vez por luta.
- O Mago ignora o casco e enxerga fantasmas: cada torre tem um papel.
- Andar suave: o monstro aparece entre duas casas (meia casa na escala 1, um quarto de casa na escala 2) em vez de pular de casa em casa.
- Cada monstro anda até 6% mais rápido ou mais devagar que os outros: a fila se espalha e ninguém fica escondido atrás do outro.
- Barra de vida com oitavos de bloco acima de cada monstro ferido (escala 2 ou maior); fundo azul quando está lento; 💥 e "+ouro" subindo no abate.
- Ondas sorteadas por peso entre os monstros já liberados; a linha de cima mostra quem vem na próxima.

### Criador de mapas
- Menu → **Criar mapa** (ou Mapas → Novo, ou `td --editor`). Ferramentas: Entrada, Trilha, Base, Grama (apaga), Árvore e Água.
- Trilha pelos cantos: toque na casa de canto e a reta desde o último ponto (em laranja) é preenchida. A entrada já liga a ferramenta Trilha; a base alinhada fecha o caminho.
- Validação ao vivo na linha de cima: "✔ Pronto para jogar" ou o que falta (entrada, base, trilha que se divide ou encosta, sem saída, solta, curta), com a casa do problema em vermelho.
- Desfazer (80 passos), 🎲 Gerar (mapa aleatório), ▶ Testar (joga na hora e volta ao editor), 💾 Salvar com nome (aceita acentos), tamanhos 9×15, 11×19 e 13×23, Limpar tudo.
- Água sob a trilha vira ponte.
- Tela **Mapas**: prontos (Serpente, Espiral, Rio) e os seus, com miniatura, tamanho da trilha e recorde. Jogar, Editar (os prontos viram cópia), Novo, Gerar e Apagar (com confirmação).
- Gerador de mapas: a mesma semente gera o mesmo mapa; às vezes as faixas ficam em pé; lagos e árvores longe da trilha.
- Mapas são arquivos de texto em `~/.config/td-termux/mapas/*.mapa` (`.` grama, `#` trilha, `S` entrada, `B` base, `T` árvore, `~` água), editáveis também no `nano`.
- Linha de comando: `td --mapas`, `td --gerar 11x19 42 > meu.mapa`, `td --validar meu.mapa`, `td --importar meu.mapa`, `td --jogar NOME`, `td --editor [NOME]`.
- Recorde separado por mapa; o mapa escolhido fica salvo.

### Alterado
- Tutorial refeito para o layout novo; as casas marcadas são calculadas pelo mapa.
- Ajuda com os monstros novos, o editor e o formato do arquivo, com quebra de linha pela largura da tela.
- Textos do modo sem emoji: monstros com a inicial do nome (i, r, O, l, t, m, f, D).
- O recorde antigo (mapa único da 2.0) não é mais mostrado; "Zerar recordes" limpa tudo.

### Balanceamento
- Simulado nos 3 mapas prontos e em 2 gerados: o jogador automático que mistura torres e melhora chega às ondas 25 a 30 (2.0.1: 26,7). Só Arqueiro caiu de 25 para 22–24 por causa do casco: misturar torres agora compensa.

### Desempenho
- 1,3 ms por quadro com 60 torres e 60 monstros na escala 2; 2,6 ms com 120 e 120 (orçamento de 50 ms).

## [2.0.1] — 2026-09-26

### Corrigido
- O instalador baixava os arquivos pelo branch de desenvolvimento; se ele fosse apagado depois do merge, a instalação quebraria. Agora usa o branch principal do repositório (`HEAD`).
- Sem terminal interativo, a pergunta da barra de teclas mostrava o erro "/dev/tty: No such device or address"; agora o instalador testa se o terminal abre antes de perguntar.

### Adicionado
- `TD_SEM_TUTORIAL=1` faz o instalador não oferecer o tutorial no fim (usado pelo `setup-teste.sh` da raiz, que instala os dois projetos).

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
