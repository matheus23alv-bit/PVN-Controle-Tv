# Tower Defense — roteiro de teste e próximos passos

## Roteiro de teste no seu celular (2.0.0)

Faça na ordem e anote o que aparecer diferente do esperado.

| # | Faça | Esperado |
|---|---|---|
| 1 | Rode o instalador e responda `s` às duas perguntas | Moldura "TOWER DEFENSE · instalador", 4 etapas com ✔, e o tutorial abre sozinho |
| 2 | Olhe a barra de teclas do Termux | Duas linhas: ESC 1 2 3 4 u x ↑ ⏎ e p n f h q ⌨ ← ↓ → |
| 3 | Observe o mapa | Emojis alinhados nas casas, sem pedaços cortados; trilha de terra contínua da 🚪 até a 🏰 |
| 4 | Faça o tutorial só com toques | Os 9 passos avançam; no fim começa a partida com "Boa sorte!" |
| 5 | Toque numa casa de grama | Aparece o alcance em verde claro; o segundo toque constrói |
| 6 | Toque duas vezes numa torre | Ela vai para o nível 2 e o fundo fica esverdeado |
| 7 | Toque na barra verde de baixo | A onda começa e os monstros andam sem precisar de mais nada |
| 8 | Toque no topo da tela | Abre a PAUSA; tocar no mapa não constrói nada |
| 9 | Jogue até perder | "A BASE CAIU!", placar e "Novo recorde"; o recorde aparece no menu |
| 10 | Mostre o teclado com ⌨ durante o jogo | O jogo continua ou mostra "Tela pequena demais"; ao esconder, volta sozinho |
| 11 | Deixe parado entre ondas por 2 minutos | O celular não esquenta |
| 12 | Se algo desalinhou: Opções → Emojis: NÃO | O mapa passa a usar letras coloridas |

Me diga também em que onda você perdeu nas 3 primeiras partidas: é o dado que falta para confirmar a dificuldade.

## Próximos passos

| # | Tarefa | Ganho | Custo |
|---|---|---|---|
| 1 | Ajustar a dificuldade com as suas partidas reais | Curva certa para quem joga de verdade | Baixo: um número no código |
| 2 | Segundo e terceiro mapa, escolhidos no menu | Rejogabilidade | Médio |
| 3 | Mostrar vários monstros na mesma casa (ex.: 👾×3) | Hoje um esconde o outro | Baixo |
| 4 | Escolher o alvo da torre (primeiro, mais forte, mais perto) | Mais estratégia | Médio |
| 5 | Chamar a onda antes da hora com bônus de ouro | Ritmo para quem está forte | Baixo |
| 6 | Sons curtos com `termux-media-player` (opcional) | Resposta ao abate e ao chefe | Médio; depende do Termux:API |
