# Tower Defense — roteiro de teste e próximos passos

## Roteiro de teste no seu celular (3.0.0)

Faça na ordem, com o celular em pé, e anote o que aparecer diferente do esperado.

| # | Faça | Esperado |
|---|---|---|
| 1 | Instale pelo pack (`bash ~/storage/downloads/instalar-pack.sh`) e digite `td` | Menu centralizado; se é a primeira vez, "🎓 Tutorial · comece aqui" vem selecionado |
| 2 | Abra o Tutorial | O mapa ocupa a tela; placar e `||` no topo; barras de torres e de ações embaixo |
| 3 | Faça os 9 passos só com toques | Tudo avança sozinho; no fim, "Boa sorte!" |
| 4 | Chame algumas ondas | Monstros deslizam entre as casas, cada um no seu ritmo; barra de vida aparece quando apanham; "+ouro" sobe no abate |
| 5 | Chegue à onda 8 | Aparecem 🐌 🐢 🦇 👻; o 👻 vira "░░" quando some e só o Mago acerta |
| 6 | Na onda 5 | O 🐉 ferido pela metade chama 3 🐀 com um ✨ |
| 7 | Menu → Criar mapa | Editor vazio, linha de cima "✘ Falta a entrada (S)" |
| 8 | Toque numa casa (entrada), depois em 3 ou 4 cantos, depois Base e o fim | As retas se completam; aparece "✔ Pronto para jogar" |
| 9 | Pinte água atravessando a trilha e depois trilha por cima | A casa vira vermelha com o erro e depois vira ponte |
| 10 | ▶ Testar, jogue, `||` → Voltar ao editor | O desenho continua lá |
| 11 | 💾 Salvar, abra o teclado (KEYBOARD) e digite um nome com acento | "Salvo: ..."; o mapa aparece em Mapas → Meus mapas |
| 12 | Mapas → 🎲 Gerar algumas vezes | Mapas diferentes, todos prontos para jogar |
| 13 | Abra o teclado no meio da partida | O jogo encolhe para a escala 1 e continua; ao esconder, volta ao tamanho grande |
| 14 | Se algo desalinhou: Opções → Emojis: NÃO | Tudo passa a letras coloridas |

Me diga também em que onda você perdeu em cada mapa pronto: é o dado que falta para confirmar a dificuldade.

## Próximos passos

| # | Tarefa | Ganho | Custo |
|---|---|---|---|
| 1 | Ajustar a dificuldade com as suas partidas reais | Curva certa para quem joga de verdade | Baixo: números no código |
| 2 | Pintar arrastando o dedo no editor | Desenhar lagos e florestas mais rápido | Médio: o Termux manda arraste como rolagem; precisa testar no aparelho |
| 3 | Escolher o alvo da torre (primeiro, mais forte, mais perto) | Mais estratégia contra fantasmas e chefes | Médio |
| 4 | Chamar a onda antes da hora com bônus de ouro | Ritmo para quem está forte | Baixo |
| 5 | Duas entradas ou dois caminhos no mesmo mapa | Mapas mais variados | Alto: muda o motor de trilha e a validação |
| 6 | Compartilhar mapa por texto (copiar e colar o `.mapa`) | Trocar mapas com outras pessoas | Baixo: o formato já é texto |
| 7 | Sons curtos com `termux-media-player` (opcional) | Resposta ao abate e ao chefe | Médio; depende do Termux:API |
