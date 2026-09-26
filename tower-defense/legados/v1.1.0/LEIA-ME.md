# Tower Defense (Termux)

Jogo de tower defense em modo texto para o terminal. Um único arquivo Python usando só a biblioteca padrão (`curses`): roda no Termux, Linux e macOS sem instalar pacotes além do Python.

A versão instalada está no arquivo `VERSION` desta pasta, que é a única fonte oficial do número de versão. O histórico está em `CHANGELOG.md`.

## Instalação no Termux

Um comando só, com internet:

```bash
curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/refs/heads/claude/tower-defense-termux-yjzaeb/tower-defense/source/instalar.sh | bash
```

Ou, com esta pasta já no celular: `bash instalar.sh`. Depois é só digitar `td`.

O instalador verifica o Python (instala se faltar), cria os comandos `td` e `tower-defense` e pergunta se você quer trocar a barra de teclas extras do Termux por uma feita para o jogo (com backup). Para atualizar, rode o instalador de novo. Para desinstalar: `bash ~/.local/share/tower-defense/instalar.sh --remover`.

Sem instalar: `python td.py` nesta pasta.

O jogo precisa de pelo menos **32 colunas × 16 linhas**. Se aparecer "Tela pequena demais", esconda o teclado ou diminua a fonte com o gesto de pinça.

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
| `h` | Ajuda |
| `q` ou Esc | Sair (durante a partida, `q` de novo confirma) |
| Toque numa célula | Move o cursor; tocar de novo constrói |
| Toque no seletor / rodapé | Escolhe a torre / chama a onda ou reinicia |

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
| `instalar.sh` | Instalador, atualizador e desinstalador |
| `VERSION` | Número da versão atual |
| `CHANGELOG.md` | Histórico de alterações |
