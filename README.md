# PVN Workspace

Este repositório contém dois projetos independentes. Cada um tem seu próprio pacote de código, versão, histórico e testes; nada é compartilhado entre eles.

| Projeto | O que é | Rodar |
|---|---|---|
| [`controle-tv/`](controle-tv/source/LEIA-ME.md) | Controle remoto de TV pelo infravermelho do celular, no terminal do Termux (Python) | `tv` depois de instalar |
| [`tower-defense/`](tower-defense/source/LEIA-ME.md) | Jogo tower defense de terminal para Termux (Python) | `td` depois de instalar |

## Teste completo em um comando

No Termux (com o app **Termux:API** do F-Droid já instalado e aberto uma vez):

```bash
curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/setup-teste.sh | bash
```

Instala os dois projetos, confere o emissor infravermelho do celular e mostra o roteiro de teste. Cada projeto também tem seu instalador próprio, descrito no LEIA-ME dele.

## Pelo pack zip (sem baixar do GitHub)

Cada entrega vem com um `PVN-pack-<data>-controle-<versão>-td-<versão>-<commit>.zip`, com o repositório daquele commit e um `PACK-INFO.txt` (versões e SHA-256 de cada arquivo), e com o `instalar-pack.sh`. Salve os dois na pasta **Download** do celular e rode no Termux:

```bash
termux-setup-storage
bash ~/storage/downloads/instalar-pack.sh
```

O primeiro comando só é preciso uma vez: toque em **Permitir** na janela do Android. O instalador pega o pack mais recente da pasta Download (aceita nomes como `... (1).zip`), confere o SHA-256 de cada arquivo, extrai em `~/pvn-pack` e instala controle e jogo a partir dele. Com internet, dá para rodar o instalador sem salvá-lo:

```bash
curl -fsSL https://raw.githubusercontent.com/matheus23alv-bit/PVN-Controle-Tv/HEAD/instalar-pack.sh | bash
```

Para gerar um pack: `bash empacotar.sh [pasta] [commit]`.

## Estrutura de cada projeto

```
<projeto>/
├── source/     arquivos de funcionamento + VERSION + CHANGELOG.md + LEIA-ME.md
├── legados/    versões anteriores preservadas, sem uso
├── testes/     testes automatizados, resultados e capturas
└── docs/       relatório de testes e roadmap da próxima versão
```

Na raiz: `setup-teste.sh` (instala os dois projetos), `instalar-pack.sh` (instala a partir do pack zip), `empacotar.sh` (gera o pack) e `testes/test_pack.sh` (testa os três).

Para publicar ou copiar um projeto, basta a pasta `source/` dele. O número de versão fica somente em `source/VERSION`.
