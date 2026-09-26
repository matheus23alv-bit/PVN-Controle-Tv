# Relatório de testes — PVN Controle TV 2.0.0

Data: 2026-09-26 · Python 3.11 · terminal real via `tmux` (44×40, retrato de celular) · Termux:API substituído por um emissor falso em `testes/mock-termux-api/`, que registra exatamente o comando que o Android receberia.

## Resultado

| Bateria | Resultado |
|---|---|
| Codificação IR, importação e linha de comando (`test_ir.py`) | 20 / 20 |
| Tela: toque, teclado, troca de TV, descoberta, erros (`test_tela.sh`) | 27 / 27 |
| Instalador: Termux com e sem emissor, `curl \| bash`, conflito, remoção (`test_instalador.sh`) | 9 / 9 |

## O que foi conferido

**Códigos:** cada botão embutido é codificado e lido de volta, e o resultado é comparado ao código publicado da marca. São 20 botões da LG (ex.: ligar `20DF10EF`), 20 da Samsung (ex.: ligar `E0E040BF`) e 16 da Sony (ex.: ligar `A90`). Todos os padrões respeitam o limite de 2 s do Android e terminam com pulso ligado.

**Protocolos:** NEC com endereço de 8 e 16 bits, Sony em 3 quadros de 45 ms, e RC5 e RC6 decodificados de volta para os bits originais.

**Importação:** um arquivo no formato do Flipper-IRDB com NECext, NEC, raw, um protocolo não suportado (Kaseikyo) e um botão sem equivalente. Os três primeiros entram e os dois últimos são listados como ignorados.

**Erros:** falta do pacote termux-api, app Termux:API que não responde (limite de 10 s), celular sem emissor, botão sem código na TV escolhida e tela pequena.

## Bug encontrado e corrigido durante os testes

Depois de um toque, o rodapé ficava em "enviando..." até a próxima tecla, embora o sinal já tivesse saído. Cada toque gera dois eventos, apertar e soltar. O programa pedia só o de apertar, e o ncurses, ao descartar o de soltar, deixava a leitura de teclas bloqueada, ignorando o tempo limite. A correção foi aceitar os dois eventos e ignorar o de soltar. Há teste de regressão ("Rodapé confirma o envio logo após o toque").

## O que só pode ser testado no seu celular

A saída de luz infravermelha e a reação da TV. Os testes provam que o comando entregue ao Termux:API está correto para cada marca, mas não substituem apontar o celular para a TV. O roteiro está no fim do `docs/ROADMAP.md`.

## Como rodar

```bash
cd controle-tv
python3 -m unittest testes/test_ir.py
bash testes/test_tela.sh          # precisa de tmux
bash testes/test_instalador.sh
```
