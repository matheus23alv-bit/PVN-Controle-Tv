# Relatório — Tower Defense 3.1.0

Data: 2026-09-26 · Python 3.11 · terminal real via `tmux` em retrato de celular (46×50, 32×30, 32×26 e 30×26) com 256 cores. Telas conferidas em imagem com a fonte de emoji do Android (Noto Color Emoji). As capturas estão em `docs/capturas/`.

## Pedido e entrega

Os quatro pacotes propostos foram implementados.

| Pacote | Entregue |
|---|---|
| A — correções de legibilidade | Placar compacto; textos em versão longa e curta; brilho de acerto em tempo real; monstros lado a lado com contador; botão pisca ao toque; fim das células pretas |
| B — efeitos de combate | Flecha e bala voando, explosão na área exata, raio do Mago, anel do Vórtice, clarão da torre, morte com 💥 e 💨, números de dano, "imune", faixas de onda e chefe, barra do chefe, tremida e vibração |
| C — tela e fonte do Termux | Opções → Ajustar tela (escala, régua de emojis, botões); instalador com `--tela-cheia`, `--fonte` e `--so-tela`, com backup e restauração byte a byte |
| D — profundidade do combate | Habilidade no nível 3 para cada torre, mira por torre (1º, forte, perto), dano por segundo e abates no painel, preço do nível 3 recalibrado |

## Resultado dos testes

| Bateria | Resultado |
|---|---|
| Lógica (`test_logica.py`) | 71 / 71 |
| Tela (`test_terminal.sh`) | 90 / 90 |
| Instalador (`test_instalador.sh`) | 28 / 28 |
| Controle da TV (inalterado): IR, tela, instalador | 20 / 20 · 27 / 27 · 9 / 9 |
| Pack (`testes/test_pack.sh`, raiz) | 18 / 18 |

### O que os testes novos garantem

- **Nível 3:** o Arqueiro acerta 2 monstros e só ele; o Canhão alcança 1,4 casa só no nível 3; o raio do Mago acerta com dano cheio quem vem atrás, sem casco, e não quem vai à frente; o Vórtice congela, mas não o chefe nem o morcego.
- **Mira:** os três modos escolhem o monstro certo e o botão percorre os três.
- **Gabarito da mira:** o gabarito de força bruta foi reescrito à parte, com os modos de mira e o nível 3. Em 400 cenários, com 6 mapas, 8 monstros, as 4 torres, níveis 1 a 3 e modos sorteados, bateram vida, mortes, lentidão, congelamento, ouro, abates e dano de cada torre.
- **Efeitos:** a duração vale em tempo real (em 2× o relógio do jogo corre 2×). Os números de dano somam 0,3 s por monstro e ficam cinza com casco. Leitura de faixa e eventos de vibração conferidas. A simulação sem efeitos não cria nenhum.
- **Tela:** mira pelo botão e pela tecla; painel com "14/s · 💀0 · mira 1º"; anúncio do nível 3; faixa e barra do chefe; vibração com um `termux-vibrate` falso; placar com "💰17M" em 30 colunas.
- **Opções:** números de dano e vibração ficam salvos. Ajustar tela ativa a tela cheia e instala e tira a fonte, conferido no `termux.properties` e na `font.ttf`.
- **Instalador:** a tela cheia troca a configuração antiga da pessoa sem duplicar; a fonte da pessoa fica guardada; `--so-tela` não reinstala o jogo; `--remover` devolve tudo byte a byte. Pelo `curl`, a fonte só é baixada quando pedida.

## Balanceamento

Jogadores automáticos, com 3 partidas por estratégia e mapa. A tabela mostra a onda média.

| Estratégia | Serpente | Espiral | Rio | Aleatório 1 | Aleatório 2 |
|---|---|---|---|---|---|
| Só Arqueiro | 23,3 | 24,0 | 22,0 | 23,3 | 21,7 |
| Só Canhão | 25,0 | 23,3 | 23,3 | 25,0 | 23,3 |
| Só Mago | 25,0 | 27,0 | 24,0 | 25,0 | 24,0 |
| Misto | 25,0 | 25,0 | 25,0 | 25,0 | 25,0 |
| Misto + melhorar | 26,7 | 30,0 | 25,0 | 28,3 | 25,0 |

Com as habilidades e o preço antigo do nível 3 (1,4× a torre), quem melhorava chegava à onda 30 em todos os mapas. Isso baixaria a dificuldade. A varredura de preço deu:

| Preço do nível 3 | Onda média de "misto + melhorar" |
|---|---|
| 1,4× (antigo) | 30,0 |
| 1,8× | 29,3 |
| **2,2× (escolhido)** | **27,0** |
| 2,6× | 26,0 |

Com 2,2× a média volta ao nível da 3.0 (26,8), e a habilidade vira uma decisão de investimento. As estratégias sem melhoria não mudaram, porque o nível 3 não as afeta.

## Desempenho

Medido em terminal real, na escala 2, com todas as torres atirando em todo quadro, que é o pior caso:

| Cenário | Lógica | Efeitos + desenho | Total |
|---|---|---|---|
| 60 torres, 60 monstros, 250 efeitos na tela | 0,56 ms | 3,46 ms | 4,03 ms |
| 120 torres, 120 monstros, 594 efeitos na tela | 1,83 ms | 6,83 ms | 8,67 ms |

O limite a 20 quadros por segundo é de 50 ms. Os efeitos custam mais que a lógica, mas mesmo o caso extremo usa 17% do limite. Numa partida normal há dezenas de efeitos, não centenas. Parado, o jogo continua sem redesenhar a tela.

## Problemas encontrados e corrigidos durante o desenvolvimento

| Problema | Como apareceu | Correção |
|---|---|---|
| O Arqueiro nível 3 explodia como o Canhão | Teste do nível 3: o terceiro monstro levou dano | O bônus de raio vale só para quem já explode |
| Chamado pelo jogo, o instalador perguntava sobre a fonte e ficava esperando resposta | Captura da tela Ajustar tela parada | `--so-tela` só mexe no que foi pedido, e o jogo roda o instalador sem terminal |
| Células pretas perto dos monstros (já existia na 3.0) | Revisão das imagens | Mapa de ocupação: nada corta emoji pela metade |
| Números de dano colados ("-22-44-35") | Revisão das imagens | Números em linha livre, com um espaço entre eles |
| Rótulos colados na barra de ações em 30 colunas ("chamarnormal") | Captura em 30×26 | Versões curtas pedem 1 coluna de folga |
| Mensagem "Arqueiro nível 3: 2 alvos por" cortada | Captura em 30×26 | Mensagens de ação com versão curta |
| Resultado do botão de tela cheia cortado ("recarrego") | Captura em 46 colunas | Versão curta da mensagem |

## O que só o seu celular confirma

- **Vibração:** depende do app Termux:API instalado. Sem ele, o jogo segue sem vibrar e Opções mostra "(sem Termux:API)".
- **Tela cheia e fonte:** o Termux precisa recarregar. O jogo chama `termux-reload-settings`; se nada mudar, feche e abra o Termux.
- **Margem lateral:** `terminal-margin-horizontal` existe no Termux 0.118 ou mais novo. Em versões antigas ela é ignorada, sem erro.
- **Régua de emojis:** mostra se a fonte do seu aparelho alinha os 25 emojis e os 10 símbolos do jogo.
- **Legibilidade dos efeitos na tela física:** números de dano e a barra do chefe.

## Como rodar

```bash
cd tower-defense
python3 -m unittest testes/test_logica.py
bash testes/test_terminal.sh        # precisa de tmux; ~2 minutos
bash testes/test_instalador.sh
python3 testes/simulacao_balanceamento.py source/td.py 3    # ~2 minutos
python3 testes/benchmark.py 2> resultado.txt                # num terminal
```

## Capturas (`docs/capturas/`)

| Arquivo | Tela |
|---|---|
| `1-menu.png` | Menu com a faixa animada |
| `2-tutorial.png` | Tutorial, passo 3, com o alcance do Mago |
| `3-partida.png` | Onda 10 com chefe: barra do Dragão no topo, torres nível 3 (★★), números de dano, "+ouro", monstros lado a lado |
| `4-editor.png` | Criador de mapas: rio com ponte e "✔ Pronto para jogar" |
| `5-mapas.png` | Tela Mapas com miniatura |
| `6-sem-emoji.png` | Modo com letras no mapa Rio |
| `7-escala1.png` | Combate em tela menor (32×30), escala 1, com contadores e botões curtos |
| `8-ajustar-tela.png` | Ajustar tela: escala, régua de emojis e símbolos, botões de tela cheia e fonte |
