# PVN Controle TV

Controle remoto de TV que usa o **emissor infravermelho do próprio celular**, direto no terminal do Termux. Toque nos botões da tela e o celular dispara o sinal para a TV, como um controle comum.

A versão está no arquivo `VERSION` desta pasta, que é a única fonte oficial do número de versão. O histórico está em `CHANGELOG.md`.

## Do que você precisa

| Item | Onde conseguir |
|---|---|
| Celular com emissor infravermelho | Comum em Xiaomi, Redmi e POCO. Confira com `tv --diagnostico` |
| App **Termux** | F-Droid |
| App **Termux:API** | F-Droid, da mesma loja do Termux (versões de lojas diferentes não conversam) |

## Instalação

No Termux, com internet:

```bash
pkg update -y
curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/refs/heads/claude/tower-defense-termux-yjzaeb/controle-tv/source/instalar.sh | bash
```

Ou, com esta pasta já no celular: `bash instalar.sh`.

O instalador instala o Python e o pacote `termux-api`, testa o emissor do celular, cria o comando `tv` e pergunta se você quer atalhos na tela inicial. Depois abra o app Termux:API uma vez e digite `tv`.

Para atualizar, rode o instalador de novo. Para desinstalar: `bash ~/.local/share/pvn-controle-tv/instalar.sh --remover`.

## Primeiro uso

1. Digite `tv`. Na primeira vez aparece "Qual é a marca da sua TV?".
2. Toque na marca (Samsung, LG ou Sony). Se não souber, toque em **Descobrir automaticamente**: o controle envia o LIGAR de cada marca e pergunta se a TV reagiu.
3. Aponte o topo do celular para a TV, a até uns 3 metros, e toque nos botões.

O rodapé confirma cada envio (`✓ Volume + enviado`) ou diz o que deu errado.

## Outras marcas (Philco, TCL, AOC, Semp...)

Baixe o arquivo `.ir` do seu modelo no banco público **Flipper-IRDB** (pasta `TVs/<marca>`), salve no celular e importe:

```bash
termux-setup-storage
tv --importar ~/storage/downloads/Philco_PTV32.ir --nome "Philco sala"
```

Os botões com nomes padrão (Power, Vol_up, Vol_dn, Ch_next, Ch_prev, Mute, Input, setas, Ok, números) são reconhecidos. Protocolos aceitos: NEC, NECext, Samsung32, SIRC, SIRC15, SIRC20, RC5, RC5X, RC6 e sinais brutos (raw).

## Comandos

| Comando | O que faz |
|---|---|
| `tv` | Abre o controle |
| `tv ligar`, `tv vol+`, `tv canal-`, `tv 7` | Envia um botão e sai |
| `tv --perfil LG ligar` | Usa outra TV só naquele comando |
| `tv --listar` | Lista as TVs disponíveis |
| `tv --importar arquivo.ir --nome "Minha TV"` | Importa uma TV do Flipper-IRDB |
| `tv --diagnostico` | Confere o emissor infravermelho |
| `tv --atalhos` | Cria 6 atalhos para o app Termux:Widget |
| `tv --simular` | Abre sem transmitir, para ver a tela |

## Teclas dentro do controle

| Tecla | Botão | Tecla | Botão |
|---|---|---|---|
| `l` | Ligar/desligar | `m` | Mudo |
| `+` `-` | Volume | `.` `,` | Canal |
| Setas, Enter | Navegação, OK | `v` | Voltar |
| `i` / `n` | Início / Menu | `f` | Fonte |
| `0`–`9` | Números | `t` / `d` | Trocar TV / Descobrir |
| `?` | Ajuda | `q` | Sair |

## Arquivos

| Arquivo | Função |
|---|---|
| `tv.py` | Controle completo: tela, protocolos IR, perfis e linha de comando |
| `instalar.sh` | Instalador, atualizador e desinstalador |
| `VERSION` | Número da versão |
| `CHANGELOG.md` | Histórico de alterações |

A TV escolhida e as TVs importadas ficam em `~/.config/pvn-tv/`.
