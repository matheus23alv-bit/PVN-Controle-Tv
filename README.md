# PVN Workspace

Este repositório contém dois projetos independentes. Cada um tem seu próprio pacote de código, versão, histórico e testes; nada é compartilhado entre eles.

| Projeto | O que é | Rodar |
|---|---|---|
| [`controle-tv/`](controle-tv/source/LEIA-ME.md) | Controle remoto de TV pelo infravermelho do celular, no terminal do Termux (Python) | `tv` depois de instalar |
| [`tower-defense/`](tower-defense/source/LEIA-ME.md) | Jogo tower defense de terminal para Termux (Python) | `td` depois de instalar |

## Estrutura de cada projeto

```
<projeto>/
├── source/     arquivos de funcionamento + VERSION + CHANGELOG.md + LEIA-ME.md
├── legados/    versões anteriores preservadas, sem uso
├── testes/     testes automatizados, resultados e capturas
└── docs/       relatório de testes e roadmap da próxima versão
```

Para publicar ou copiar um projeto, basta a pasta `source/` dele. O número de versão fica somente em `source/VERSION`.
