# Teclado Termux

Barras de teclas extras do Termux para cada uso, com volta garantida à sua barra de antes. O comando `teclas` troca a barra na hora, e o controle da TV (`tv`) e o Tower Defense (`td`) põem a barra deles ao abrir e devolvem a anterior ao fechar. É um único arquivo Python, só com a biblioteca padrão, e mexe apenas na linha `extra-keys` do `~/.termux/termux.properties`.

A versão está no arquivo `VERSION` desta pasta. O histórico está em `CHANGELOG.md`.

## Instalação no Termux

```bash
curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/teclado-termux/source/instalar.sh | bash
```

Ou, com esta pasta no celular: `bash instalar.sh`. O `setup-teste.sh` e o pack zip da raiz também instalam o teclado junto com os outros dois projetos.

O instalador cria o comando `teclas` e pergunta se você quer usar o padrão melhorado no dia a dia. Para escolher sem pergunta, use `--melhorado` ou `--sem-melhorado`. Para desinstalar e ter a sua barra de volta: `bash ~/.local/share/teclado-termux/instalar.sh --remover`.

## As barras

| Perfil | Para quê | Teclas |
|---|---|---|
| **Padrão melhorado** | Dia a dia no terminal | As do padrão do Termux, mais 📺 (abre a TV), 🏰 (abre o jogo), ⌨ (mostra ou esconde o teclado) e TECLAS (abre o menu) |
| **Jogo** | Tower Defense | 🏹 💣 🔮 🌀 (torres), ⏫ melhorar, 💲 vender, ONDA, ⏩ 2×, 🎯 mira, `||` pausa, setas e OK |
| **TV** | Controle da TV | LIGAR, MUDO, FONTE, VOL+ e VOL−, CH+ e CH−, VOLTAR, INÍCIO, MENU, INFO, setas, OK e SAIR |
| **Padrão do Termux** | A barra que vem com o Termux | ESC / - HOME ↑ END PGUP, TAB CTRL ALT ← ↓ → PGDN |
| **A sua de antes** | A barra que você tinha antes do teclas, do jeito que estava | Aparece só se você tinha uma |

**No padrão melhorado, deslize o dedo para cima numa tecla:**
- ESC vira `^C`, que interrompe um comando;
- `/` vira `~`, e `-` vira `|`;
- HOME vira PGUP, e END vira PGDN;
- TAB vira "limpar", que limpa a tela;
- ⌨ vira "colar".

**Na barra da TV, segure VOL+ ou VOL− para repetir.** Essas teclas saem pelo PGUP e pelo PGDN, que o Termux repete sozinho. O controle só manda o sinal seguinte quando o anterior terminou, e o volume para assim que você solta.

## Usar

- `teclas` abre o menu. Toque numa barra para usar: a prévia mostra as teclas, e a tecla `a` (ou um toque) liga ou desliga a troca automática.
- `teclas melhorado`, `teclas jogo`, `teclas tv`, `teclas padrao` e `teclas original` trocam direto.
- `teclas --estado` mostra a barra atual e a troca automática.
- `teclas --auto sim` e `teclas --auto nao` ligam e desligam a troca automática.
- `teclas --lista` e `teclas --ajuda`.

## Troca automática

Ligada por padrão. O `tv` e o `td` chamam `teclas --entrar tv` (ou `jogo`) ao abrir e `teclas --sair` ao fechar. A barra que estava antes é guardada e volta idêntica, mesmo que seja uma barra sua feita à mão.

**Se o app fechar sem avisar**, como ao fechar a sessão do Termux no meio do jogo, a barra dele continua. Ela volta sozinha na próxima vez que você abrir e fechar o `tv` ou o `td`, ou na hora, com `teclas melhorado`.

**Uma escolha feita por você no menu vale até você trocar de novo.** Por exemplo, `teclas jogo` deixa a barra do jogo fixa.

## Segurança da sua configuração

- **O que o teclas mexe:** só a linha `extra-keys`, marcada com `# teclas: <perfil>`. As outras opções do `termux.properties` ficam onde estão.
- **Primeira troca:** a sua barra fica guardada (`~/.config/teclas/estado.json`), e o arquivo inteiro também (`termux.properties.antes-do-teclas`).
- **Remover:** devolve a sua barra de antes. Se o arquivo não existia, ele é apagado.
- **Barra do jogo que o instalador do Tower Defense 3.1 fixava:** é reconhecida. A "sua de antes" passa a ser a barra que você tinha antes do jogo.
- **Emojis e acentos:** são gravados como `\uXXXX`, que o Termux lê em qualquer versão.
- **Recarga:** depois de cada troca, o teclas roda o `termux-reload-settings`. A barra muda na hora, sem fechar o Termux.

## Arquivos

| Arquivo | Função |
|---|---|
| `teclas.py` | Perfis, leitura e escrita do `termux.properties`, troca automática, menu e linha de comando |
| `instalar.sh` | Instalador, atualizador e desinstalador |
| `VERSION` | Número da versão |
| `CHANGELOG.md` | Histórico de alterações |
