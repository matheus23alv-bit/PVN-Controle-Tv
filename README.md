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

## Estrutura de cada projeto

```
<projeto>/
├── source/     arquivos de funcionamento + VERSION + CHANGELOG.md + LEIA-ME.md
├── legados/    versões anteriores preservadas, sem uso
├── testes/     testes automatizados, resultados e capturas
└── docs/       relatório de testes e roadmap da próxima versão
```

Para publicar ou copiar um projeto, basta a pasta `source/` dele. O número de versão fica somente em `source/VERSION`.
