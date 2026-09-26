# Próxima versão — Tower Defense v1.1

Lista completa de tarefas, em ordem de prioridade dentro de cada grupo.

## O que você precisa fazer

1. **Jogar no seu Termux real** pelo menos até a onda 10 e anotar: o tamanho da tela funcionou sem zoom? a dificuldade está boa? Os testes rodaram em terminal Linux emulado, não em um celular. Se a tela não couber, me diga o tamanho mostrado no aviso.
2. **Ajustar a dificuldade ao seu gosto**, se precisar, mudando uma linha em `source/td.py`: `HP_GROWTH = 1.18`. Use 1,15 para mais fácil ou 1,22 para mais difícil.
3. **Revisar e aprovar o merge** do branch `claude/tower-defense-termux-yjzaeb`.
4. **Considerar mover o jogo para um repositório próprio.** Ele não tem relação com o controle de TV; separado, o `git clone` no Termux baixa só o jogo.

## Funcional

| # | Tarefa | Ganho | Custo |
|---|---|---|---|
| F1 | Toque na tela para posicionar o cursor (`curses.mousemask`) | No celular é muito mais rápido que setas; o Termux envia toques como mouse | Baixo |
| F2 | Economia com limite: custo da torre sobe a cada compra, ou juros sobre ouro guardado | Hoje o bot ainda enche o mapa inteiro; a dificuldade vem só da vida dos inimigos | Baixo |
| F3 | Upgrade de torre (nível 1→3) com `u` | Decisão estratégica além de "construir mais" | Médio |
| F4 | Recorde salvo em `~/.td_recorde` | Motivo para jogar de novo | Muito baixo |
| F5 | Painel da torre sob o cursor (dano, alcance, valor de venda) | Hoje não há como ver os números no jogo | Baixo |
| F6 | Chamar onda mais cedo com bônus de ouro | Ritmo mais rápido para quem está forte | Baixo |
| F7 | Chefe a cada 10 ondas | Marcos na progressão | Baixo |
| F8 | Novo inimigo voador que ignora o caminho, ou blindado que resiste ao Arqueiro | Força variar as torres | Médio |
| F9 | 2–3 mapas selecionáveis no início | Rejogabilidade | Médio |
| F10 | Velocidade 2× (`f`) | Ondas tardias demoram | Muito baixo |

## Visual

| # | Tarefa | Ganho | Custo |
|---|---|---|---|
| V1 | Mostrar o alcance da torre selecionada ao passar o cursor | Hoje é preciso decorar os números | Baixo |
| V2 | Rastro do disparo (linha ou `·`) entre torre e alvo por 1 quadro | Hoje não se vê quem está atirando em quem | Baixo |
| V3 | Cor do inimigo muda conforme a vida (vermelho → amarelo) | Mostra dano sem barra de vida | Muito baixo |
| V4 | Quando dois inimigos ocupam a mesma célula, mostrar um número (`2`, `3`) | Hoje um esconde o outro | Muito baixo |
| V5 | O spawn `S` some quando um inimigo passa por cima; manter o `S` por baixo | Referência visual constante | Muito baixo |
| V6 | Barra de vida da base no HUD | Leitura mais rápida que o número | Muito baixo |
| V7 | Tela inicial com título e instruções curtas | Primeiro contato mais claro | Baixo |

## Técnico

| # | Tarefa | Ganho |
|---|---|---|
| T1 | Separar lógica (`td_logica.py`) da interface quando passar de ~600 linhas | Hoje um arquivo é vantagem para instalar; vira problema ao crescer |
| T2 | Rodar `test_logica.py` em CI (GitHub Actions) | Impede regressões |
| T3 | Loop com tempo fixo por quadro em vez de `sleep(0.03)` | Mesma velocidade em celulares lentos |
