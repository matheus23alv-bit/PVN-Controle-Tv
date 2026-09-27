# Tower Defense (Termux)

Tower defense com emojis que roda dentro do terminal do Termux, em tela cheia com o celular em pé. É um único arquivo Python que usa só a biblioteca padrão (`curses`), e dá para jogar inteiro pelo toque ou pelo teclado. O jogo traz um criador de mapas para você desenhar e gerar as suas fases.

A versão está no arquivo `VERSION` desta pasta, que é a única fonte oficial do número de versão. O histórico está em `CHANGELOG.md`.

## Instalação no Termux

Com internet, um comando só:

```bash
pkg update -y
curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/tower-defense/source/instalar.sh | bash
```

Ou, com esta pasta já no celular: `bash instalar.sh`.

O instalador confere o Python (instala se faltar) e cria os comandos `td` e `tower-defense`. No Termux, ele pergunta se pode trocar a barra de teclas extras por uma feita para o jogo, deixar o Termux em tela cheia e instalar a fonte do jogo. Tudo é feito com backup. No fim, ele oferece abrir o tutorial. Depois é só digitar `td`.

Para atualizar, rode o instalador de novo. Para desinstalar: `bash ~/.local/share/tower-defense/instalar.sh --remover`. Sem instalar: `python td.py` nesta pasta.

## Tela

O jogo usa a tela inteira em retrato. As casas crescem até o mapa preencher a altura: num celular comum (cerca de 46×50 caracteres) cada casa ocupa 4 colunas × 2 linhas, e em tablets chega a 6×3. Com o teclado aberto o jogo volta à escala 1 e continua jogável a partir de **30 colunas × 24 linhas**, que é o mínimo para os mapas 11×19. Abaixo disso aparece "Tela pequena demais": esconda o teclado ou diminua a fonte com o gesto de pinça.

**Opções → Ajustar tela** mostra o tamanho da sua tela e a escala. Mostra também quanto diminuir a fonte para a próxima escala e uma régua para conferir se cada emoji e símbolo cabe nas suas 2 colunas. Por ali você ativa, com um toque:

- **Tela cheia do Termux:** esconde a barra de status e a de navegação do Android e zera a margem lateral. Sobram mais linhas para o jogo.
- **Fonte do jogo:** DejaVu Sans Mono em `~/.termux/font.ttf`. Com ela, ★, barras de vida, pontes e miniaturas saem sem falhas, e os emojis continuam coloridos. A sua fonte fica guardada.

As mesmas opções existem no instalador: `--tela-cheia`, `--fonte`, `--so-tela` (só essas opções, sem reinstalar) e as versões `--sem-tela-cheia` e `--sem-fonte`. O `--remover` devolve a configuração e a fonte originais.

Se os emojis aparecerem desalinhados no seu celular, vá em **Opções → Emojis: NÃO** (ou abra com `td --sem-emoji`) para jogar com letras coloridas.

## Como jogar

Os monstros saem da 🚪 e seguem a trilha até a 🏰. Cada um que chega tira 💗, e cada abate dá 💰. Construa torres na grama; árvores e água não aceitam torre. As ondas não acabam: o objetivo é ir o mais longe possível, e o recorde fica salvo por mapa. Na primeira vez, abra o **Tutorial**: são 9 passos jogando de verdade.

| Torre | Custo | Especialidade | Habilidade no nível 3 |
|---|---|---|---|
| 🏹 Arqueiro | 20 | Rápido, alvo único | Atira em 2 monstros |
| 💣 Canhão | 50 | Explode e atinge os vizinhos do alvo | Explosão meia casa maior |
| 🔮 Mago | 35 | Maior alcance, enxerga fantasmas e ignora casco | O raio atravessa e acerta quem vem atrás |
| 🌀 Vórtice | 40 | Deixa lentos os monstros perto do alvo | Congela o alvo por 0,5 s (chefe e morcego não) |

Toda torre pode ser melhorada até o nível 3, com mais dano e alcance a cada nível, e as estrelas ★ acima dela mostram o nível. O nível 2 custa 0,7× o preço da torre; o nível 3 traz a habilidade e custa 2,2×. Vender devolve metade do que foi gasto.

Cada torre tem uma **mira** (🎯 ou tecla `t`): o mais adiantado (padrão), o de mais vida ou o mais perto. Com o cursor numa torre, o painel mostra o dano por segundo, quantos monstros ela derrotou e a mira.

| Monstro | Vida | A partir da onda | Detalhe |
|---|---|---|---|
| 👾 Invasor | 28 | 1 | Comum |
| 🐀 Rato | 15 | 2 | Rápido |
| 👹 Ogro | 100 | 3 | Lento, tira 2 💗 |
| 🐌 Lesma | 70 | 4 | Se cura depois de 1 s sem apanhar |
| 🐢 Tartaruga | 55 | 5 | Casco: cada tiro perde 4 de dano (o Mago ignora) |
| 🦇 Morcego | 24 | 6 | Rápido e nunca fica lento |
| 👻 Fantasma | 40 | 8 | Some por 1,2 s a cada 3,7 s; sumido, só o Mago vê |
| 🐉 Dragão | 520 | a cada 5 | Chefe, tira 5 💗; ferido pela metade, chama 3 ratos |

A vida dos monstros cresce 16% a cada onda. Cada monstro anda num ritmo um pouco diferente, então a fila se espalha pela trilha. A linha abaixo do placar mostra quem vem na próxima onda.

## Controles

A barra de torres e a barra de ações ficam embaixo, perto do polegar.

| Toque | Ação |
|---|---|
| Numa casa | Põe o cursor e mostra o alcance |
| De novo na mesma casa | Constrói a torre escolhida, ou melhora a torre que já está ali |
| Barra de torres | Escolhe a torre (mostra custo e nome) |
| ▶ Onda | Chama a próxima onda |
| ⏩ | Velocidade 1× ou 2× |
| 🎯 Mira | Troca a mira da torre do cursor |
| ⏫ Melhorar / 💲 Vender | Agem na torre do cursor, com o preço no botão |
| `||` no topo | Pausa |

| Tecla | Ação | Tecla | Ação |
|---|---|---|---|
| Setas / `w a s d` | Mover | `1`–`4` | Escolher torre |
| Enter / Espaço | Construir ou melhorar | `u` | Melhorar |
| `x` | Vender | `n` | Próxima onda |
| `f` | Velocidade 2× | `p` / `q` / Esc | Pausa |
| `t` | Trocar a mira | `h` | Ajuda |

### Na tela

- **Tiros:** a flecha e a bala voam até o alvo. A explosão do Canhão pinta de laranja a área exata do dano, o Mago solta um raio e o Vórtice pulsa um anel azul.
- **Monstros atingidos:** piscam em branco, azul quando estão lentos e azul-claro quando congelados. Os números de dano sobem em vermelho, e em cinza quando o casco reduz o dano.
- **Monstros juntos:** aparecem lado a lado, e um número amarelo mostra quantos estão no mesmo lugar.
- **Chefe:** a barra de vida do Dragão fica no topo enquanto ele está vivo, com faixas avisando a chegada e a derrota.
- **Base atingida:** o mapa treme e o celular vibra, pelo Termux:API.
- **Opções:** números de dano e vibração podem ser desligados.

## Criar mapas

No menu, **Criar mapa** abre o editor com um mapa em branco. **Mapas** lista os prontos e os seus, com miniatura, e deixa jogar, editar, gerar ou apagar. Um mapa pronto nunca é alterado: editar cria uma cópia.

1. Escolha **Entrada** e toque na casa de onde os monstros saem. O editor já troca para a ferramenta **Trilha**.
2. Toque nas casas de **canto** do caminho. A reta desde o último ponto, marcado em laranja, é preenchida sozinha. Tocar numa trilha que já existe continua a partir dela.
3. Escolha **Base** e toque no fim do caminho. Se estiver na mesma linha ou coluna do último canto, a reta também é preenchida.
4. Enfeite com **Árvore** e **Água**, que não aceitam torre. Trilha em cima da água vira ponte. **Grama** apaga.
5. A linha de cima diz "✔ Pronto para jogar" ou o que falta, e a casa com problema fica vermelha. **▶ Testar** joga na hora e a pausa volta ao editor.
6. **💾 Salvar** pede um nome (use a tecla KEYBOARD da barra do Termux para abrir o teclado).

A trilha precisa ser um caminho único da entrada até a base: não pode se dividir nem encostar nela mesma. Deixe uma casa de grama entre as voltas. **🎲 Gerar** cria um mapa aleatório pronto para jogar, que você pode ajustar. No menu **||** do editor ficam Renomear, Tamanho (9×15, 11×19 ou 13×23), Limpar tudo e Sair. **« Desfazer** volta até 80 passos.

Teclas do editor: setas movem, Enter pinta, `1`–`6` escolhem a ferramenta, `u` desfaz, `g` gera, `t` testa, `v` salva, `q` abre o menu.

### Arquivo `.mapa`

Os mapas ficam em `~/.config/td-termux/mapas/`, um arquivo de texto por mapa, que também pode ser editado no `nano`:

```
nome: Meu vale
.S.........
.#.........
.#######...
.......#.T.
~~~~~~~#~~~
.......#...
.B######...
```

`.` grama · `#` trilha · `S` entrada · `B` base · `T` árvore · `~` água. Linhas com `:` são informações, e linhas vazias ou começando com `;` são ignoradas. O tamanho vai de 5×5 a 24×40.

```bash
td --mapas                        # lista os mapas prontos e os seus
td --gerar 11x19 42 > vale.mapa   # mapa aleatório; a mesma semente gera o mesmo mapa
td --validar vale.mapa            # diz se dá para jogar ou onde está o erro
td --importar vale.mapa           # copia para os seus mapas
td --jogar "Meu vale"             # joga direto nesse mapa
td --editor Rio                   # edita uma cópia do mapa Rio
```

## Opções de linha de comando

`td --tutorial`, `td --jogar [MAPA]`, `td --editor [MAPA]`, `td --mapas`, `td --gerar [LxA] [SEMENTE]`, `td --validar ARQUIVO`, `td --importar ARQUIVO`, `td --sem-emoji`, `td --sem-toque`, `td --versao`, `td --ajuda`.

## Arquivos

| Arquivo | Função |
|---|---|
| `td.py` | Jogo completo: lógica, telas, tutorial, editor e gerador de mapas |
| `instalar.sh` | Instalador, atualizador e desinstalador; tela cheia e fonte do Termux |
| `fontes/` | Fonte DejaVu Sans Mono (opcional no Termux) e a licença dela |
| `VERSION` | Número da versão |
| `CHANGELOG.md` | Histórico de alterações |

Opções e recordes ficam em `~/.config/td-termux/config.json`, e os seus mapas em `~/.config/td-termux/mapas/`.
