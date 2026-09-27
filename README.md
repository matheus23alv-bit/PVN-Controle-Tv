# PVN Workspace

Este repositório contém dois projetos independentes. Cada um tem seu próprio pacote de código, versão, histórico e testes. Nada é compartilhado entre eles: o controle só chama o comando `teclas` se ele existir.

| Projeto | O que é | Rodar |
|---|---|---|
| [`controle-tv/`](controle-tv/source/LEIA-ME.md) | Controle remoto de TV pelo infravermelho do celular, no terminal do Termux (Python) | `tv` depois de instalar |
| [`teclado-termux/`](teclado-termux/source/LEIA-ME.md) | Barras de teclas extras do Termux: padrão melhorado, jogo e TV, que trocam sozinhas ao abrir o `tv` e o `td`, com volta à sua barra de antes (Python) | `teclas` depois de instalar |

## O Tower Defense mudou de repositório

O jogo era a pasta `tower-defense/` daqui. Agora ele mora no repositório dedicado a ele, **[matheus23alv-bit/TOWER-DEFENSE---TERMUX-](https://github.com/matheus23alv-bit/TOWER-DEFENSE---TERMUX-)**, com o histórico do jogo preservado, e é lá que ele continua sendo desenvolvido. Para instalar o jogo:

```bash
curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/TOWER-DEFENSE---TERMUX-/HEAD/setup-teste.sh | bash
```

A barra de teclas do jogo continua vindo do **Teclado Termux** deste repositório: com o `teclas` instalado, o `td` põe a barra do jogo ao abrir e devolve a sua ao fechar. Os dois projetos seguem independentes — cada um funciona sem o outro.

## Teste completo em um comando

No Termux (com o app **Termux:API** do F-Droid já instalado e aberto uma vez):

```bash
curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/setup-teste.sh | bash
```

Instala os dois projetos, confere o emissor infravermelho do celular e mostra o roteiro de teste. Cada projeto também tem seu instalador próprio, descrito no LEIA-ME dele.

## Pelo pack zip (sem baixar do GitHub)

Cada entrega vem com um `PVN-pack-<data>-controle-<versão>-teclado-<versão>-<commit>.zip`, com o repositório daquele commit e um `PACK-INFO.txt` (versões e SHA-256 de cada arquivo), e com o `instalar-pack.sh`. Salve os dois na pasta **Download** do celular e rode no Termux:

```bash
termux-setup-storage
bash ~/storage/downloads/instalar-pack.sh
```

O primeiro comando só é preciso uma vez: toque em **Permitir** na janela do Android. O instalador pega o `PVN-pack-*.zip` mais recente da pasta Download (aceita nomes como `... (1).zip`), confere o SHA-256 de cada arquivo, extrai em `~/pvn-pack` e instala o teclado e o controle a partir dele. O pack do jogo (`TD-pack-*.zip`) tem instalador próprio e os dois podem ficar juntos na pasta Download sem confusão. Com internet, dá para rodar o instalador sem salvá-lo:

```bash
curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/instalar-pack.sh | bash
```

Para gerar um pack: `bash empacotar.sh [pasta] [commit]`.

## Estado do projeto e continuidade

- [`CHECKPOINT.md`](CHECKPOINT.md): estado atual, mapa do código, decisões, pendências e o prompt para continuar em outra sessão.
- [`docs/AUDITORIA-2026-09-27.md`](docs/AUDITORIA-2026-09-27.md): última auditoria completa (problemas achados, correções e testes). A parte do jogo está no checkpoint do repositório dele.

## Estrutura de cada projeto

```
<projeto>/
├── source/     arquivos de funcionamento + VERSION + CHANGELOG.md + LEIA-ME.md
├── legados/    versões anteriores preservadas, sem uso
├── testes/     testes automatizados, resultados e capturas
└── docs/       relatório de testes e roadmap da próxima versão
```

Na raiz: `setup-teste.sh` (instala os dois projetos, ou só o que vier no pack), `instalar-pack.sh` (instala a partir do pack zip), `empacotar.sh` (gera o pack), `testes/test_pack.sh` (testa os dois juntos) e `testes/captura.sh` (captura a tela do tmux em PNG para revisão visual).

Para publicar ou copiar um projeto, basta a pasta `source/` dele. O número de versão fica somente em `source/VERSION`.
