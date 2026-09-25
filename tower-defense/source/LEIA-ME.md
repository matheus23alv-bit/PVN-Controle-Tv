# Tower Defense (Termux)

Jogo de tower defense em modo texto para o terminal. Um único arquivo Python usando só a biblioteca padrão (`curses`): roda no Termux, Linux e macOS sem instalar pacotes além do Python.

A versão instalada está no arquivo `VERSION` desta pasta, que é a única fonte oficial do número de versão. O histórico está em `CHANGELOG.md`.

## Instalação no Termux

```bash
pkg update -y && pkg install python git -y
git clone https://github.com/matheus23alv-bit/PVN-Controle-Tv.git
cd PVN-Controle-Tv/tower-defense/source
python td.py
```

O jogo precisa de uma tela de pelo menos **36 colunas × 21 linhas**. Se aparecer "Tela pequena demais", diminua a fonte do Termux com o gesto de pinça na tela e o jogo continua sozinho.

Para usar as setas, ative a barra de teclas extras do Termux (Volume Baixo + Q). Sem ela, use `w` `a` `s` `d`.

## Objetivo

Inimigos saem do `S` e seguem o caminho `#` até a base `B`. Cada inimigo que chega tira vida; com a vida em zero a partida acaba. Construa torres na grama `.` ao lado do caminho. As ondas não têm fim: o objetivo é ir o mais longe possível.

## Controles

| Tecla | Ação |
|---|---|
| Setas ou `w` `a` `s` `d` | Mover o cursor |
| `1` `2` `3` | Escolher a torre |
| Enter ou Espaço | Construir no cursor |
| `x` | Vender a torre do cursor (devolve metade) |
| `n` | Chamar a próxima onda |
| `p` | Pausar / continuar |
| `r` | Nova partida (depois de perder) |
| `q` ou Esc | Sair (pede confirmação durante a partida) |

## Torres

| Torre | Custo | Alcance | Dano | Intervalo entre tiros |
|---|---|---|---|---|
| `A` Arqueiro | 20 | 4 | 8 | 0,6 s |
| `C` Canhão | 50 | 3 | 30 | 1,6 s |
| `M` Mago | 35 | 6 | 14 | 1,0 s |

Cada torre atira no inimigo mais adiantado dentro do alcance.

## Inimigos

| Símbolo | Tipo | Característica |
|---|---|---|
| `o` | Normal | Equilibrado |
| `*` | Rápido | Pouca vida, quase o dobro da velocidade |
| `@` | Tanque | Muita vida, lento, tira 2 de vida da base; aparece a partir da onda 3 |

Cada onda traz dois inimigos a mais que a anterior, e a vida deles cresce 18% por onda.

## Arquivos

| Arquivo | Função |
|---|---|
| `td.py` | Jogo completo: lógica e interface |
| `VERSION` | Número da versão atual |
| `CHANGELOG.md` | Histórico de alterações |
