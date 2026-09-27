# Changelog — Teclado Termux

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento semântico.

## [1.1.0] — 2026-09-27

A barra de um app nunca fica presa. Se o `td` ou o `tv` for encerrado pelo Android sem chamar `teclas --sair`, a barra da pessoa volta sozinha.

### Adicionado
- **Dono da barra.** `teclas --entrar <perfil> --dono <processo>` guarda qual processo pediu a barra, junto da hora em que ele começou. Quem chama sem `--dono` continua funcionando como antes.
- **Devolução automática.** Toda chamada do `teclas` (o menu, `--estado`, uma troca de perfil) confere primeiro se o dono da barra ainda está vivo. Se não está, devolve a barra antes de fazer o que foi pedido. Na prática: o jogo foi encerrado pela bateria, a pessoa volta ao Termux e a primeira coisa que ela fizer com o `teclas` já corrige a barra.
- **Processo zumbi conta como morto** (morreu, o pai ainda não o recolheu), e **número de processo reaproveitado** não segura mais a barra: o Android reaproveita PID, e a hora de início separa um processo do outro.

### Mudado
- **`--sair` solta a barra presa mesmo sem ter o que devolver guardado.** Antes ele saía sem fazer nada. Agora, se a barra na tela é de um app e não foi a pessoa que a escolheu, ele volta para a escolha dela. A barra que a pessoa escolheu de propósito (`teclas jogo`, `teclas tv`) continua intacta.
- **A escolha da pessoa fica guardada** (`escolha` no estado), para ser o destino de uma barra presa.

### Testes
- 12 verificações novas (41 no total): dono morto, dono vivo, zumbi, PID reaproveitado, `--sair` repetido, `--sair` sem barra de app na tela, `--entrar` sem `--dono`, abrir outro app com a barra presa e a barra escolhida à mão.

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
