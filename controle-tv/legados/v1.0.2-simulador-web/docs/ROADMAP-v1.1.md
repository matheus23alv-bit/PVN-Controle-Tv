# Próxima versão — PVN Controle TV v1.1

Lista completa de tarefas, em ordem de prioridade dentro de cada grupo. Cada item diz o ganho e, quando existe, o custo.

## O que você precisa fazer

1. **Decidir o destino do projeto.** Se é demonstração/portfólio, o foco é o visual da TV (itens V1–V4). Se deve controlar uma TV física, o próximo passo é outro: um app Android com IR blaster ou um hub IR em rede (ex.: Broadlink RM4), e esta interface passa a chamar a API do hub. Essa decisão muda metade da lista abaixo.
2. **Revisar e aprovar o merge** do branch `claude/tower-defense-termux-yjzaeb`, que traz a separação dos dois projetos e a v1.0.1.
3. **Publicar** a pasta `controle-tv/source/` em uma hospedagem estática, se quiser um link público (Vercel, Netlify ou GitHub Pages — nenhum precisa de configuração).
4. **Rodar a bateria de testes** (`docs/RELATORIO-TESTES.md`) antes de cada nova versão e atualizar `source/VERSION` e `source/CHANGELOG.md` juntos.

## Funcional

| # | Tarefa | Ganho | Custo |
|---|---|---|---|
| F1 | Menu na tela da TV (imagem, som, idioma) navegável por setas/OK/Voltar | Dá sentido a 6 botões que hoje não fazem nada | Médio: novo componente de UI e estado de foco |
| F2 | Tela "Início" com grade de apps (Netflix, YouTube fictícios) | Completa o fluxo Home → app → Voltar | Médio |
| F3 | Nome real e cor/logo por canal, editável via JSON | Tela menos genérica que "Canal 1…12" | Baixo |
| F4 | Guia de programação (botão Info/Guia) | Recurso esperado em TV | Médio |
| F5 | Segurar VOL/CH repete o comando | Comportamento de controle real | Baixo |
| F6 | Faixa de canais configurável além de 12 e digitação de 3 dígitos | Escala para grades reais | Baixo |
| F7 | Mudo mantido ao desligar/ligar (hoje é zerado) | Fiel a TVs reais | Baixo |
| F8 | Vibração curta no celular ao tocar (`navigator.vibrate`) | Resposta tátil | Muito baixo |
| F9 | PWA (manifest + service worker) para instalar e usar offline | Abre como app no celular | Baixo |
| F10 | Integração opcional com hub IR em rede | Controle de TV física | Alto; depende do item 1 acima |

## Visual

| # | Tarefa | Ganho | Custo |
|---|---|---|---|
| V1 | Conteúdo na tela ligada (gradiente animado ou imagem por canal) | Hoje a tela ligada é um azul vazio | Baixo |
| V2 | Transição ao trocar canal (ruído/fade curto) | Deixa a troca perceptível | Baixo |
| V3 | OSD de volume no rodapé da tela, como TVs reais | Hoje fica no meio da tela | Muito baixo |
| V4 | No celular, TV fixa no topo enquanto rola o controle | Hoje a TV sai da tela ao usar o teclado numérico | Baixo |
| V5 | Trocar emojis (🔇 🔊) por ícones SVG | Emojis mudam de aparência entre Android, iOS e Windows | Baixo |
| V6 | Controle visualmente "apagado" com a TV desligada (a classe `.is-off` já existe sem CSS) | Indica que só o Power tem efeito | Muito baixo |
| V7 | Desktop: centralizar a composição na vertical e reduzir o vazio abaixo da TV | Composição mais equilibrada | Muito baixo |
| V8 | Painel de sinais recolhível no celular | Hoje ocupa espaço no fim da página | Baixo |
| V9 | Tema claro opcional | Preferência de uso | Baixo |

## Técnico

| # | Tarefa | Ganho |
|---|---|---|
| T1 | Rodar `testes/e2e.test.js` em CI (GitHub Actions) a cada push | Impede regressões dos 8 erros já corrigidos |
| T2 | `package.json` em `testes/` fixando a versão do Playwright | Testes reprodutíveis em qualquer máquina |
| T3 | Remover atributos `data-group` sem uso no HTML | Menos código morto |
