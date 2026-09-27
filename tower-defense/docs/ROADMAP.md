# Tower Defense — roteiro de teste e próximos passos

## Roteiro de teste no seu celular (3.1.2)

Faça na ordem, com o celular em pé, e anote o que aparecer diferente do esperado.

| # | Faça | Esperado |
|---|---|---|
| 1 | Instale pelo pack (`bash ~/storage/downloads/instalar-pack.sh`; o pack só do jogo serve) e responda `s` a tela cheia e fonte | O Termux recarrega sem as barras do Android e com a fonte nova |
| 2 | `td` → Opções → Ajustar tela | Tamanho da tela, escala e régua: cada emoji entre duas barras, ★ e barras sem vãos |
| 3 | Jogue uma partida e chame 3 ondas | Faixa "ONDA N", flechas e balas voando, explosão laranja, raio magenta do Mago |
| 4 | Olhe os monstros atingidos | Piscam em branco; números de dano vermelhos (cinza na Tartaruga); 💥 e 💨 na morte, "+ouro" subindo |
| 5 | Deixe monstros se acumularem numa curva | Aparecem lado a lado e com um número amarelo; nenhuma célula preta no mapa |
| 6 | Toque numa torre e em 🎯 | A mira passa por 1º, forte e perto; o painel mostra dano por segundo e abates |
| 7 | Melhore uma torre até o nível 3 | Mensagem com a habilidade e ★★ acima da torre |
| 8 | Chegue à onda 5 | "CHEFE CHEGOU", barra de vida do Dragão no topo e o celular vibra |
| 9 | Deixe um monstro chegar à base | O mapa treme e o celular vibra |
| 10 | Abra o teclado (KEYBOARD) no meio da partida | Escala 1 com placar e botões curtos, sem texto cortado no meio |
| 11 | Toque nos botões | Cada botão pisca ao toque |
| 12 | Opções: desligue Números de dano e Vibrar | Somem os números e a vibração |
| 13 | Ajustar tela: Tirar tela cheia e Tirar a fonte | O Termux volta ao que era |

Me diga também em que onda você perdeu em cada mapa pronto: é o dado que falta para confirmar a dificuldade.

## Próximos passos

| # | Tarefa | Ganho | Custo |
|---|---|---|---|
| 1 | Ajustar a dificuldade com as suas partidas reais | Curva certa para quem joga de verdade | Baixo: números no código |
| 2 | Pintar arrastando o dedo no editor | Desenhar lagos e florestas mais rápido | Médio: o Termux manda arraste como rolagem; precisa testar no aparelho |
| 3 | 30 quadros por segundo na escala 2 (opção) | Movimento mais fluido | Baixo; gasta um pouco mais de bateria |
| 4 | Chamar a onda antes da hora com bônus de ouro | Ritmo para quem está forte | Baixo |
| 5 | Duas entradas ou dois caminhos no mesmo mapa | Mapas mais variados | Alto: muda o motor de trilha e a validação |
| 6 | Compartilhar mapa por texto (copiar e colar o `.mapa`) | Trocar mapas com outras pessoas | Baixo: o formato já é texto |
| 7 | Sons curtos com `termux-media-player` (opcional) | Resposta ao abate e ao chefe | Médio; depende do Termux:API |
