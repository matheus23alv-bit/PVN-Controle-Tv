# Relatório — Tower Defense 3.0.0

Data: 2026-09-26 · Python 3.11 · terminal real via `tmux` em retrato de celular (46×50 e 32×26) com 256 cores. Telas conferidas em imagem, com a fonte de emoji do Android (Noto Color Emoji); as capturas estão em `docs/capturas/`.

## Pedido e entrega

| Pedido | Entregue |
|---|---|
| Tela cheia, celular em pé (9:16) | Mapas em retrato (11×19) e casas em escala 1×, 2× ou 3× até preencherem a altura. O placar fica no topo e os controles embaixo, perto do polegar. |
| Melhorar os monstros e a caminhada | 4 monstros novos com habilidades (🐌 🐢 🦇 👻), Dragão que chama ratos e andar suave entre casas. Cada monstro tem ritmo próprio, com barra de vida, lentidão visível e "+ouro" no abate. |
| Motor e criador de mapas | Editor na tela com trilha pelos cantos, validação ao vivo, desfazer, gerar, testar e salvar. Tela de Mapas com miniatura. Gerador por semente. Arquivos `.mapa` em texto e comandos `--gerar`, `--validar`, `--importar` e `--editor`. |

## Resultado dos testes

| Bateria | Resultado |
|---|---|
| Lógica (`test_logica.py`): mapas, validação, gerador, arquivos, editor, torres, monstros novos, ondas, escala da tela | 54 / 54 |
| Tela (`test_terminal.sh`): menu, tutorial inteiro pelo toque, partida, pausa, Mapas, criador de mapas, fim de jogo, sem emoji, escalas 1 e 2, linha de comando | 76 / 76 |
| Instalador (`test_instalador.sh`): Linux, Termux com barra própria, `curl \| bash`, falhas | 17 / 17 |
| Controle da TV (inalterado): `test_ir.py`, `test_tela.sh`, `test_instalador.sh` | 20 / 20 · 27 / 27 · 9 / 9 |
| Pack (`testes/test_pack.sh`, raiz) | 18 / 18 |

### O que os testes garantem

**Mapas:** os 3 mapas prontos são jogáveis e têm trilha contínua de 63 a 66 casas. Cada erro de desenho tem mensagem e casa próprias: falta entrada ou base, entrada ou base repetida, entrada solta, trilha que se divide, voltas encostadas, sem saída, trilha solta, curta ou sem grama. O gerador foi testado com 360 sementes nos 3 tamanhos: todos os mapas saíram jogáveis, a mesma semente sempre gera o mesmo mapa e os enfeites ficam longe da trilha. Salvar, renomear, nomes reservados, nomes repetidos e arquivos quebrados na pasta também foram testados.

**Editor:** a entrada liga a ferramenta Trilha e os cantos preenchem as retas. Tocar numa trilha existente continua dela. Há uma entrada e uma base só. O teste também cobre desfazer, redimensionar (e desfazer o tamanho), limpar e gerar.

**Monstros:**

- O casco tira 4 de dano, com mínimo de 25%, e o Mago o ignora.
- O Fantasma sumido só é alvo do Mago.
- A Lesma só se cura depois de 1 s sem apanhar e nunca passa da vida máxima.
- O Morcego não fica lento.
- O Dragão chama 3 ratos uma única vez.
- As ondas só trazem monstros já liberados, e a prévia é exatamente a próxima onda.

**Mira:** a mira otimizada foi comparada com um gabarito de força bruta em 400 cenários. Eles cobrem 6 mapas, os 8 monstros, as 4 torres, os níveis 1 a 3, fantasmas sumidos e casco, e o resultado foi idêntico em todos.

**Simulação estável:** passos de 0,25 s dão o mesmo resultado que passos de 0,05 s, inclusive com monstros novos, então celular lento não muda o jogo.

**Tela:** a escala certa foi conferida para 5 tamanhos de tela. Cada toque cai na casa certa, inclusive na segunda coluna do emoji, e a posição entre duas casas fica no meio delas.

## Balanceamento

Jogadores automáticos compram entre as ondas sempre na casa de maior cobertura. Foram 3 partidas por estratégia em cada mapa, e a tabela mostra a onda média alcançada.

| Estratégia | Serpente | Espiral | Rio | Aleatório 1 | Aleatório 2 | 2.0.1 (mapa único) |
|---|---|---|---|---|---|---|
| Só Arqueiro | 23,3 | 24,0 | 22,0 | 23,3 | 21,7 | 25,0 |
| Só Canhão | 25,0 | 23,3 | 23,3 | 25,0 | 23,3 | 25,0 |
| Só Mago | 25,0 | 27,0 | 24,0 | 25,0 | 24,0 | 25,7 |
| Só Vórtice | 6,0 | 6,3 | 6,0 | 6,0 | 6,0 | 8,3 |
| Misto | 25,0 | 25,0 | 25,0 | 25,0 | 25,0 | 25,0 |
| Misto + melhorar | 25,0 | 29,7 | 25,0 | 29,3 | 25,0 | 26,7 |

A dificuldade ficou no mesmo nível da 2.0.1, e nenhum número de balanceamento precisou mudar. Os monstros novos puniram quem usa uma torre só: só Arqueiro caiu cerca de 2 ondas por causa do casco da Tartaruga, enquanto misturar e melhorar continua sendo o melhor caminho. A Espiral é o mapa mais fácil, porque o centro fica coberto por várias voltas. A onda 25 é o muro de 3 dragões.

## Desempenho

Medido em terminal real, na escala 2 (casas de 4×2), com emojis e 256 cores:

| Cenário | Lógica | Desenho | Total |
|---|---|---|---|
| 60 torres, 60 monstros, todas atirando | 0,46 ms | 0,79 ms | 1,25 ms |
| 120 torres, 120 monstros | 1,58 ms | 1,04 ms | 2,62 ms |

O limite a 20 quadros por segundo é de 50 ms por quadro, então sobra margem de 19× para celulares lentos. O desenho do fundo do mapa fica guardado e só é refeito quando o mapa muda. Parado entre ondas, no editor ou na tela de Mapas, o jogo não redesenha a tela.

## Problemas encontrados e corrigidos durante o desenvolvimento

| Problema | Correção |
|---|---|
| Trilhas geradas saíam curtas (média de 43 casas no 11×19, contra 63 a 66 nos prontos), o que deixava os mapas aleatórios mais difíceis | Faixas quase sempre cruzam o mapa, com mínimo de 1/5 da área: a média subiu para 50 casas |
| Textura de grama aparecia sob o cursor e sob as torres | Casa do cursor e de torre desenhadas lisas |
| Menu grudado no topo em telas altas, com metade da tela vazia | Bloco do menu centralizado na altura |
| Tela de Mapas com um vão grande entre a lista e a miniatura | Lista do tamanho dos mapas e miniatura centralizada no espaço livre |
| Dicas do editor cortadas na largura de 46 colunas | Textos encurtados para caber |
| Voltar da ajuda aberta na pausa soltava a partida | Voltar da ajuda reabre a pausa |
| Tocar no título "MAPAS" voltava ao menu sem querer | Só o botão "◀ Voltar" volta |
| O cache do desenho das casas reconhecia o mapa pelo endereço de memória, que pode ser reaproveitado por outro objeto | O cache guarda o próprio mapa |

## O que só o seu celular confirma

- **Tamanho da tela no seu aparelho:** o jogo escolhe a escala sozinho. Confira se o mapa ocupa bem a tela.
- **Alinhamento dos emojis na sua fonte:** o 🐌 e o 🦇 são novos. Se desalinharem, use Opções → Emojis: NÃO.
- **Toques na barra de ferramentas do editor:** são 6 botões lado a lado, 7 colunas cada.
- **Teclado com acento no nome do mapa:** o teclado do Android envia os acentos em bytes, e o jogo os monta. Isso foi testado com "Trilha Ágil" no terminal, mas não em aparelho.
- **Sensação da dificuldade com monstros novos.**

## Como rodar

```bash
cd tower-defense
python3 -m unittest testes/test_logica.py
bash testes/test_terminal.sh        # precisa de tmux; ~1 minuto
bash testes/test_instalador.sh
python3 testes/simulacao_balanceamento.py source/td.py 3    # ~2 minutos
python3 testes/benchmark.py 2> resultado.txt                # num terminal
```

## Capturas (`docs/capturas/`)

| Arquivo | Tela |
|---|---|
| `1-menu.png` | Menu com a faixa animada |
| `2-tutorial.png` | Tutorial, passo 3, com o alcance do Mago |
| `3-partida.png` | Onda 8 com monstros novos, barras de vida, estrelas de nível e alcance |
| `4-editor.png` | Criador de mapas: rio com ponte, árvores e "✔ Pronto para jogar" |
| `5-mapas.png` | Tela Mapas: prontos, seus mapas e miniatura |
| `6-sem-emoji.png` | Modo com letras no mapa Rio |
| `7-escala1.png` | Tela menor (32×30), na escala 1 |
