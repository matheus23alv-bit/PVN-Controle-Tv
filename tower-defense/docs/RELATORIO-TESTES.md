# Relatório de testes — Tower Defense 2.0.0

Data: 2026-09-26 · Python 3.11 · terminal real via `tmux` em 44×24 (retrato de celular) com 256 cores · telas conferidas em imagem, com a fonte de emoji do Android (Noto Color Emoji).

## Resultado

| Bateria | Resultado |
|---|---|
| Lógica (`test_logica.py`) | 18 / 18 |
| Tela: menu, tutorial inteiro pelo toque, partida, pausa, fim de jogo, opções (`test_terminal.sh`) | 35 / 35 |
| Instalador: Linux, Termux com barra de teclas própria, `curl \| bash`, falhas (`test_instalador.sh`) | 17 / 17 |

## Destaques da cobertura

**Mira das torres:** a mira otimizada (só a faixa da trilha ao alcance da torre) foi comparada com um gabarito de força bruta em 400 cenários aleatórios, com as quatro torres, níveis 1 a 3, dano em área e lentidão. O resultado foi idêntico em todos.

**Simulação:** um passo de 0,25 s dá o mesmo resultado que cinco passos de 0,05 s, então celular lento não muda o jogo.

**Tutorial:** os 9 passos são percorridos só com toques, do menu até o início da partida de verdade.

**Regressão do toque:** depois de um toque, os monstros continuam andando sem nenhuma outra tecla.

## Bug encontrado e corrigido

Na 1.1.0, depois de cada toque o jogo congelava até a próxima tecla. O programa não pedia o evento de "soltar o dedo" ao ncurses, que o descartava e deixava a leitura de teclas bloqueada, ignorando o tempo limite. O mesmo bug foi achado e corrigido no controle da TV.

## Balanceamento

Jogadores automáticos compram entre as ondas sempre na casa de maior cobertura, com 3 partidas por estratégia.

| Ajuste | Só Arqueiro | Mago+Arqueiro+Canhão, melhorando | Com Vórtice, melhorando |
|---|---|---|---|
| Primeira versão das regras (vida +14%/onda) | 30 (mapa lotado) | 30 (mapa lotado) | 30 |
| Final: vida +16%/onda, melhoria mais forte e barata, ouro mais contido | 25,0 (151 torres) | 27,0 (54 torres) | 26,7 (51 torres) |

Na primeira versão, todas as estratégias lotavam o mapa e morriam juntas no muro dos 4 dragões da onda 30. Na final, melhorar torres rende mais que espalhar, e o Vórtice empata com a mistura sem ele. Um jogador humano deve ficar entre as ondas 12 e 22; é estimativa, e o seu teste vai confirmar.

## Desempenho

Medido em terminal real, com emojis e 256 cores:

| Cenário | Lógica | Desenho | Total |
|---|---|---|---|
| 60 torres, 60 monstros, todas atirando | 0,64 ms | 0,94 ms | 1,58 ms |
| 151 torres (mapa lotado), 120 monstros | 2,30 ms | 0,92 ms | 3,23 ms |

O orçamento a 20 quadros por segundo é 50 ms: sobra margem de 15× para celulares mais lentos. Com o jogo parado entre ondas, o uso de CPU é de 0,05%, porque a tela não é redesenhada sem mudança.

## O que só o seu celular confirma

O alinhamento dos emojis na fonte do seu aparelho, o toque do Termux e a sensação da dificuldade. Se os emojis desalinharem, use Opções → Emojis: NÃO.

## Como rodar

```bash
cd tower-defense
python3 -m unittest testes/test_logica.py
bash testes/test_terminal.sh        # precisa de tmux; ~1 minuto
bash testes/test_instalador.sh
python3 testes/simulacao_balanceamento.py source/td.py 3    # alguns minutos
python3 testes/benchmark.py 2> resultado.txt                # num terminal
```
