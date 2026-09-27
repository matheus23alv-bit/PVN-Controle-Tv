# Relatório de testes — Teclado Termux 1.0.0

Data: 2026-09-27 · Python 3.11 · terminal real via `tmux` em retrato de celular (46×50, 46×20 e 28×10). O Termux é simulado num HOME temporário, com `TERMUX_VERSION` e um `termux-reload-settings` falso que registra cada recarga.

## Resultado

| Bateria | Resultado |
|---|---|
| Unidade (`test_teclas.py`) | 29 / 29 |
| Tela (`test_tela.sh`) | 21 / 21 |
| Instalador (`test_instalador.sh`) | 19 / 19 |
| Os três projetos juntos, no pack (`testes/test_pack.sh`, raiz) | incluído nos 37 / 37 |

## O que foi conferido

**Perfis lidos como o Termux lê.** Cada linha gerada passa pelo que o Termux faz:
- primeiro, o `java.util.Properties`, que desfaz os `\uXXXX`, inclusive os pares de emoji;
- depois, o JSON tolerante do org.json, com aspas simples e palavras sem aspas.

O teste confere as duas linhas de cada barra com o mesmo número de colunas e as setas ↑ e ↓ uma embaixo da outra. Também confere, depois dessa leitura:
- os emojis e o "INÍCIO";
- as macros 📺 e 🏰;
- o ^C que aparece ao deslizar.

**O arquivo do Termux.**
- Barra da pessoa em várias linhas (com `\`) trocada por inteiro, na mesma posição.
- Outras opções intactas.
- Nada duplica ao repetir, e o Termux não recarrega à toa.
- `teclas original` devolve o arquivo byte a byte.
- `teclas padrao` tira a linha, e o arquivo criado pelo teclas é apagado quando ele não existia.

**A barra fixada pelo Tower Defense 3.1.** É reconhecida:
- a marca da barra do jogo sai;
- a marca da tela cheia do jogo fica;
- "a sua de antes" vem do backup que o instalador do jogo tinha feito.

**Troca automática.**
- `--entrar` e `--sair` devolvem a barra exata, mesmo uma barra própria.
- Um fechamento sem `--sair`, com outro app abrindo em seguida, não perde a barra de volta.
- Uma escolha manual cancela a volta.
- Com a troca desligada, nada muda; fora do Termux, também não.
- `--sair` começando antes do `--entrar` terminar (o td fechado na hora, com a recarga levando 0,5 s) termina na barra certa: a trava põe as trocas em ordem.

**Tela.** Mostra:
- a barra atual e as escolhas;
- "A sua de antes" só quando existe;
- a prévia de cada barra.

Pelo uso:
- o toque, o número e as setas com Enter aplicam;
- a tecla `a` e o toque ligam e desligam a troca automática;
- com 20 linhas (teclado aberto), as escolhas cabem; abaixo de 30×12, aparece o aviso;
- `q` e Esc saem.

**Instalador.**
- Linux e Termux.
- `--melhorado`, reinstalação sem pergunta, `--sem-melhorado` e migração da barra do td 3.1.
- `curl | bash` e `--remover`, que devolve a barra byte a byte e apaga comando, estado e backup.
- Sem internet, a mensagem é clara, e um `teclas` de outro programa não é sobrescrito.

**Os três juntos (pack).** Com o pack completo instalado num Termux simulado e o `teclas` de verdade:
- `teclas melhorado` grava a barra do dia a dia;
- abrir o `td` grava a do jogo, e fechar volta ao melhorado;
- abrir o `tv` grava a da TV, o VOL− da barra transmite o código da LG, e fechar volta ao melhorado;
- `teclas original` volta ao padrão do Termux.

## O que só o seu celular confirma

- A barra mudando na hora com o `termux-reload-settings` (Termux 0.118 ou mais novo).
- Os emojis na barra, desenhados pela fonte do Android.
- A repetição ao segurar VOL+ na barra da TV. O controle presume que o Termux repete a cada ~0,08 s.
- As macros 📺 e 🏰, que digitam `tv` ou `td` e Enter no prompt.

## Como rodar

```bash
cd teclado-termux
python3 -m unittest testes/test_teclas.py
bash testes/test_tela.sh          # precisa de tmux
bash testes/test_instalador.sh
```
