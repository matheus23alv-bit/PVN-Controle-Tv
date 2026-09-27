# Relatório de testes — PVN Controle TV 2.0.2

Data: 2026-09-26, revisado na auditoria de 2026-09-27 (`docs/AUDITORIA-2026-09-27.md` na raiz) · Python 3.11 · terminal real via `tmux` (44×40, retrato de celular) · Termux:API substituído por um emissor falso em `testes/mock-termux-api/`, que registra exatamente o comando que o Android receberia.

## Resultado

| Bateria | Resultado |
|---|---|
| Codificação IR, importação e linha de comando (`test_ir.py`) | 25 / 25 |
| Tela: toque, teclado, troca de TV, descoberta, erros, lista longa de TVs (`test_tela.sh`) | 30 / 30 |
| Instalador: Termux com e sem emissor, `curl \| bash`, conflito, remoção (`test_instalador.sh`) | 9 / 9 |

## O que foi conferido

**Códigos:** cada botão embutido é codificado e lido de volta, e o resultado é comparado ao código publicado da marca. São 20 botões da LG (ex.: ligar `20DF10EF`), 20 da Samsung (ex.: ligar `E0E040BF`) e 16 da Sony (ex.: ligar `A90`). Todos os padrões respeitam o limite de 2 s do Android e terminam com pulso ligado.

**Protocolos:** NEC com endereço de 8 e 16 bits, Sony em 3 quadros de 45 ms, e RC5 e RC6 decodificados de volta para os bits originais.

**Importação:** um arquivo no formato do Flipper-IRDB com NECext, NEC, raw, um protocolo não suportado (Kaseikyo) e um botão sem equivalente. Os três primeiros entram e os dois últimos são listados como ignorados.

**Erros:** falta do pacote termux-api, app Termux:API que não responde (limite de 10 s), celular sem emissor, botão sem código na TV escolhida e tela pequena.

## Corrigido na auditoria (2.0.2)

- **RC5/RC6 (TVs Philips importadas):** o bit de alternância passou a mudar a cada toque. Antes, um mesmo botão repetido podia ser ignorado pela TV.
- **Sem o app Termux:API:** os toques acumulados durante a espera de 10 s são descartados. Antes, a tela ficava minutos em "enviando...".
- **Lista de TVs:** rola quando há muitas importadas.
- **Rótulo "importado":** fica certo mesmo com nome de marca embutida.
- **`--perfil` com TV inexistente:** a mensagem ficou clara.

Cada correção tem teste de regressão.

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
