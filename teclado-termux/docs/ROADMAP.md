# Teclado Termux — roteiro de teste e próximos passos

## Roteiro de teste no seu celular (1.0.0)

Faça na ordem e anote o que aparecer diferente do esperado.

| # | Faça | Esperado |
|---|---|---|
| 1 | Instale pelo pack (`bash ~/storage/downloads/instalar-pack.sh`) e responda `s` a "Usar o padrão melhorado no dia a dia?" | A barra do Termux muda na hora, com 📺 🏰 e TECLAS no fim |
| 2 | Deslize o dedo para cima no ESC, no `-` e no ⌨ | Aparecem ^C, `|` e "colar" |
| 3 | Toque em TECLAS na barra | Abre o menu, com a barra atual marcada com ✔ |
| 4 | No menu, toque em "Controle da TV" e depois em "Padrão melhorado" | A barra troca a cada toque, sem fechar o Termux |
| 5 | Toque em 🏰 | O jogo abre com a barra do jogo (🏹 💣 🔮 🌀...) |
| 6 | Saia do jogo | A barra volta ao padrão melhorado |
| 7 | Toque em 📺 | O controle abre com a barra da TV (LIGAR, MUDO, VOL+...) |
| 8 | Segure VOL+ por 2 s, apontando para a TV, e solte | O volume sobe sem parar e para logo ao soltar |
| 9 | Saia do controle (SAIR) | A barra volta ao padrão melhorado |
| 10 | `teclas original` | Volta a barra que você tinha antes de tudo |

**Se a barra não mudar num passo:**
- confira se o app Termux está atualizado (0.118 ou mais novo);
- rode `termux-reload-settings`;
- me mande a saída de `teclas --estado` e uma captura da barra.

## Próximos passos

| # | Tarefa | Ganho | Custo |
|---|---|---|---|
| 1 | Perfil próprio montado no menu (escolher as teclas de cada posição) | Barra do seu jeito sem editar arquivo | Médio |
| 2 | Terceira linha opcional nas barras (números ou funções F1–F12) | Mais atalhos em telas grandes | Baixo; ocupa mais espaço da tela |
| 3 | Atalhos de macros na barra da TV (ex.: ligar e ir para o HDMI 2) | Rotinas num toque | Médio; depende do controle |
