# Tower Defense (Termux)

Jogo de tower defense em modo texto, feito em Python puro (biblioteca padrão `curses`).
Sem dependências externas — roda em qualquer Termux com Python instalado.

## Instalação no Termux

```bash
pkg update -y
pkg install python -y
```

Copie a pasta `tower-defense-termux/` para o seu dispositivo (via `git clone`, `curl`,
transferência de arquivo, etc.) e rode:

```bash
cd tower-defense-termux
python td.py
```

ⓘ Se a tela ficar cortada, diminua a fonte do Termux (Volume Down + `-`, ou pelo menu
lateral em *Style → Font size*) para caber o grid de 32×13 na tela do celular.

## Objetivo

Defenda a base (`B`) impedindo que os inimigos que nascem em `S` (spawn) percorram o
caminho (`#`) até o final. Cada inimigo que chega tira vida da base; se a vida chegar a
zero, o jogo acaba.

## Controles

| Tecla | Ação |
|---|---|
| Setas ou `w`/`a`/`s`/`d` | Move o cursor pelo grid |
| `1`, `2`, `3` | Seleciona o tipo de torre a construir |
| `Enter` ou `Espaço` | Constrói a torre selecionada na posição do cursor |
| `x` | Vende a torre sob o cursor (devolve metade do custo) |
| `n` | Inicia a próxima onda de inimigos |
| `p` | Pausa/despausa |
| `q` ou `Esc` | Sai do jogo |

## Torres

| Torre | Custo | Alcance | Dano | Cadência |
|---|---|---|---|---|
| Arqueiro (`A`) | 20 ouro | médio | baixo | rápida |
| Canhão (`C`) | 50 ouro | curto | alto | lenta |
| Mago (`M`) | 35 ouro | longo | médio | média |

Torres só podem ser construídas em células de grama (`.`), nunca sobre o caminho.

## Inimigos

- `o` normal — equilibrado.
- `*` rápido — pouca vida, alta velocidade.
- `@` tanque — muita vida, lento, causa mais dano à base se chegar (a partir da onda 3).

Cada onda fica mais numerosa e mais forte que a anterior. Não há limite de ondas:
o objetivo é sobreviver o máximo possível e acumular abates.

## Estrutura do projeto

```
tower-defense-termux/
├── td.py        # jogo completo (lógica + interface curses)
└── README.md
```

Todo o código está em um único arquivo por portabilidade — basta um `python td.py`
para jogar, sem instalar pacotes adicionais além do interpretador Python.
