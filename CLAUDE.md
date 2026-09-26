# Convenções do PVN Workspace

## Entrega (obrigatório em toda entrega ao usuário)

1. **Merge** da atualização no branch principal do repositório (`claude/tv-remote-control-app-lu248i`, o default) por PR, depois de rodar os testes abaixo.
2. **Pack zip** gerado do commit já mesclado e enviado ao usuário como arquivo:
   `git fetch origin && bash empacotar.sh <pasta> origin/claude/tv-remote-control-app-lu248i`
3. Na resposta: o que mudou, resultado dos testes, o comando de instalação e o que o usuário precisa testar.

## Direção dos projetos

- Os dois projetos rodam **no terminal do Termux**, não no navegador.
- `controle-tv`: controle remoto real pelo **emissor infravermelho do próprio celular** (Termux:API, `termux-infrared-transmit`). O simulador web é legado.
- `tower-defense`: jogo independente e leve, visual com emojis em casas de 2 colunas; setup, menu e tutorial ficam dentro do terminal. O usuário tem outro projeto TD, complexo, separado deste.

## Estrutura

- Cada projeto: `source/` (só arquivos de funcionamento + `VERSION` + `CHANGELOG.md` + `LEIA-ME.md`), `legados/`, `testes/`, `docs/`.
- Um único `VERSION` por projeto. Toda mudança de código sobe a versão e ganha entrada no `CHANGELOG.md`.
- Textos de interface, documentação e respostas em português do Brasil.
- Instaladores baixam pelo branch principal (`raw.githubusercontent.com/.../HEAD/...`).

## Testes antes do merge

```bash
cd controle-tv && python3 -m unittest testes/test_ir.py && bash testes/test_tela.sh && bash testes/test_instalador.sh
cd tower-defense && python3 -m unittest testes/test_logica.py && bash testes/test_terminal.sh && bash testes/test_instalador.sh
```

Os testes de tela precisam de `tmux`. O controle é testado com o Termux:API falso de `controle-tv/testes/mock-termux-api/`.
