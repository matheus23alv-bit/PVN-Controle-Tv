# Tower Defense (Termux)

Tower defense com emojis que roda dentro do terminal do Termux. Um único arquivo Python, só com a biblioteca padrão (`curses`). Dá para jogar inteiro pelo toque ou pelo teclado.

A versão está no arquivo `VERSION` desta pasta, que é a única fonte oficial do número de versão. O histórico está em `CHANGELOG.md`.

## Instalação no Termux

Com internet, um comando só:

```bash
pkg update -y
curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/refs/heads/claude/tower-defense-termux-yjzaeb/tower-defense/source/instalar.sh | bash
```

Ou, com esta pasta já no celular: `bash instalar.sh`.

O instalador confere o Python (instala se faltar), cria os comandos `td` e `tower-defense`, pergunta se pode trocar a barra de teclas extras do Termux por uma feita para o jogo (com backup) e oferece abrir o tutorial. Depois é só digitar `td`.

Para atualizar, rode o instalador de novo. Para desinstalar: `bash ~/.local/share/tower-defense/instalar.sh --remover`.

Sem instalar: `python td.py` nesta pasta.

## Tela

O jogo precisa de pelo menos **38 colunas × 17 linhas**. Se aparecer "Tela pequena demais", esconda o teclado ou diminua a fonte com o gesto de pinça. Se os emojis aparecerem desalinhados no seu celular, vá em **Opções → Emojis: NÃO** (ou abra com `td --sem-emoji`) para jogar com letras coloridas.

## Como jogar

Os monstros saem da 🚪 e seguem a trilha de terra até a 🏰. Cada um que chega tira 💗. Construa torres na grama; cada abate dá 💰. As ondas não acabam e a cada 5 vem um chefe 🐉. O objetivo é ir o mais longe possível: o recorde fica salvo.

Na primeira vez, abra o **Tutorial** no menu: são 9 passos jogando de verdade.

| Torre | Custo | Especialidade |
|---|---|---|
| 🏹 Arqueiro | 20 | Rápido, alvo único |
| 💣 Canhão | 50 | Explode e atinge os vizinhos do alvo |
| 🔮 Mago | 35 | Maior alcance |
| 🌀 Vórtice | 40 | Deixa lentos os monstros perto do alvo |

Toda torre pode ser melhorada até o nível 3 (mais dano e alcance). O fundo da torre mostra o nível: esverdeado no 2, dourado no 3.

| Monstro | Vida | Detalhe |
|---|---|---|
| 👾 Invasor | 28 | Comum |
| 🐀 Rato | 15 | Rápido, a partir da onda 2 |
| 👹 Ogro | 100 | Lento, tira 2 💗, a partir da onda 3 |
| 🐉 Dragão | 520 | Chefe a cada 5 ondas, tira 5 💗 |

A vida dos monstros cresce 16% a cada onda.

## Controles

| Toque | Ação |
|---|---|
| Numa casa | Move o cursor e mostra o alcance |
| De novo na mesma casa | Constrói a torre escolhida, ou melhora a torre que já está ali |
| Numa torre da linha 2 | Escolhe a torre |
| Na barra verde de baixo | Chama a próxima onda |
| No topo | Pausa |

| Tecla | Ação | Tecla | Ação |
|---|---|---|---|
| Setas / `w a s d` | Mover | `1`–`4` | Escolher torre |
| Enter / Espaço | Construir ou melhorar | `u` | Melhorar |
| `x` | Vender (devolve metade) | `n` | Próxima onda |
| `f` | Velocidade 2× | `p` / `q` / Esc | Pausa |
| `h` | Ajuda | | |

## Opções de linha de comando

`td --tutorial`, `td --jogar`, `td --sem-emoji`, `td --sem-toque`, `td --versao`, `td --ajuda`.

## Arquivos

| Arquivo | Função |
|---|---|
| `td.py` | Jogo completo: lógica, telas, tutorial |
| `instalar.sh` | Instalador, atualizador e desinstalador |
| `VERSION` | Número da versão |
| `CHANGELOG.md` | Histórico de alterações |

Recorde e opções ficam em `~/.config/td-termux/config.json`.
