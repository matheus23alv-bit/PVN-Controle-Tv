# Relatório de testes — Tower Defense (Termux)

Data: 2026-09-25 · Python 3.11 · Terminal real via `tmux` nos tamanhos 40×22 (Termux em retrato), 80×24 e 32×14 (tela pequena)

## Resultado

| Bateria | 1.0.0 (legado) | 1.0.1 (source) |
|---|---|---|
| Lógica (`test_logica.py`) | 13 / 15 | 15 / 15 |
| Terminal (`test_terminal.sh`) | 7 / 15 | 15 / 15 |
| Balanceamento (onda média de um bot perfeito) | 40+ (nunca perde) | ~28 |

Das 8 falhas de terminal da 1.0.0, 6 são defeitos reais, 1 é só diferença no formato do texto do HUD ("Onda:  1" em vez de "Onda 1") e 1 é consequência de outra falha (cancelar a saída não existe sem a confirmação).

## Erros encontrados na 1.0.0

Todos corrigidos na 1.0.1.

| # | Gravidade | Erro | Evidência |
|---|---|---|---|
| 1 | Alta | Impossível perder | Simulação com 20 partidas × 4 estratégias: todas chegaram à onda 40 e encheram o mapa (342 torres) |
| 2 | Alta | HUD e controles cortados em 40 colunas | Captura em 40×22: `Torre [1] Arqueiro custo: 20 >1:Arquei`, `Setas/WASD move  1-3 torre  Enter const` |
| 3 | Alta | Tela pequena sem aviso: base `B` e controles invisíveis | Captura em 32×14 |
| 4 | Média | Esc/`q` encerra a partida sem confirmar | Esc fica ao lado das setas na barra do Termux |
| 5 | Média | Sem reinício após perder | Única opção era sair |
| 6 | Baixa | Última coluna do terminal nunca desenhada | `safe_addstr` cortava 1 caractere a mais |
| 7 | Baixa | Esc com ~1 s de atraso | `ESCDELAY` padrão |

Um bug foi encontrado e corrigido **durante** o desenvolvimento da 1.0.1, antes da entrega: após `r`, a nova partida já nascia perdida porque o laço ainda lia a vida da partida anterior. Existe teste de regressão para ele ("r reinicia com partida limpa").

## Balanceamento

O bot compra torres entre as ondas sempre na posição que cobre mais caminho. Isso é jogo perfeito; um humano tende a ficar entre as ondas 15 e 25.

| Crescimento de vida por onda | Onda média do bot |
|---|---|
| Linear +15% (1.0.0) | 40+ |
| 1,12 composto | 38–40 |
| 1,15 composto | 32–35 |
| **1,18 composto (1.0.1)** | **28–31** |
| 1,22 composto | 22–25 |

As 4 estratégias (só Arqueiro, só Canhão, só Mago, misto) terminaram com diferença de até 2 ondas entre si, então nenhuma torre é dominante.

## Como rodar

```bash
cd tower-defense
python3 -m unittest testes/test_logica.py
bash testes/test_terminal.sh                 # precisa de tmux; leva ~45 s
python3 testes/simulacao_balanceamento.py    # leva alguns minutos
# para testar o legado:
TD_PATH=legados/v1.0.0/td.py python3 -m unittest testes/test_logica.py
bash testes/test_terminal.sh legados/v1.0.0/td.py
```
