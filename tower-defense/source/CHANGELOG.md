# Changelog — Tower Defense (Termux)

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento semântico.

## [1.0.1] — 2026-09-25

### Corrigido
- Jogo impossível de perder: a vida dos inimigos crescia de forma linear e a economia sempre vencia (em simulação, qualquer estratégia passava de 40 ondas). Agora cresce 18% por onda de forma composta; um jogador automático perfeito chega à onda ~28.
- Em telas de 40 colunas (Termux em retrato) o painel de torres e a linha de controles ficavam cortados. HUD e controles foram reescritos para caber em 36 colunas.
- A última coluna da tela nunca era desenhada.
- Em tela menor que o grid, o mapa e a base ficavam cortados sem aviso. Agora aparece "Tela pequena demais" com o tamanho atual e o mínimo, e o jogo fica pausado até a tela caber.
- `q` ou Esc (que fica ao lado das setas na barra do Termux) encerrava a partida na hora. Agora pede confirmação durante a partida.
- Esc demorava cerca de 1 s para responder (`ESCDELAY` padrão do curses).

### Adicionado
- `r` inicia nova partida depois de perder. Antes era preciso sair e abrir o jogo de novo.
- Linha de status com dica "Pressione n para a próxima onda" entre ondas.

### Interno
- Estado da partida agrupado em `new_game()`; removida a variável global `PATH`.

## [1.0.0] — 2026-09-25

Versão inicial: grid 32×13, 3 torres, 3 inimigos, ondas infinitas, venda de torres e pausa. Preservada em `legados/v1.0.0/`.
