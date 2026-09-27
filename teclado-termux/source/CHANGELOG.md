# Changelog — Teclado Termux

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento semântico.

## [1.0.0] — 2026-09-27

Primeira versão.

### Adicionado
- **Comando `teclas`:** troca a barra de teclas extras do Termux entre cinco escolhas:
  - **padrão melhorado:** 📺 abre a TV, 🏰 o jogo e TECLAS o menu; ao deslizar para cima, dá ^C, ~, |, PGUP, PGDN, limpar e colar;
  - **jogo:** Tower Defense;
  - **TV:** VOL nas teclas que o Termux repete ao segurar;
  - **padrão do Termux;**
  - **a barra que a pessoa tinha antes.**
- **Menu na tela:** funciona pelo toque, com a prévia de cada barra, a barra atual marcada e a chave da troca automática.
- **Troca automática:** `teclas --entrar <perfil>` e `teclas --sair`, usados pelo `tv` e pelo `td`. A barra anterior volta idêntica. Uma trava por arquivo põe as trocas em ordem, e um fechamento sem `--sair` se corrige na próxima vez.
- **Só a linha `extra-keys` é tocada:**
  - valores em várias linhas são tratados;
  - as outras opções ficam no lugar;
  - a barra fixada pelo instalador do Tower Defense 3.1 é reconhecida, e a "de antes" vem do backup dele.
- **Gravação à prova de versão:** emojis e acentos vão como `\uXXXX`. Depois de cada troca, o Termux recarrega com `termux-reload-settings`.
- **Instalador:** `--melhorado`, `--sem-melhorado` e `--remover`. O `--remover` devolve a barra de antes byte a byte e apaga o `termux.properties` se ele não existia.

### Testes
- 29 de unidade: perfis lidos como o Termux lê, arquivo, troca automática (inclusive `--entrar` e `--sair` ao mesmo tempo) e remoção.
- 21 de tela, no tmux.
- 19 do instalador.
