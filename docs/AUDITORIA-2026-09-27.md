# Auditoria e depuração — PVN Workspace, 2026-09-27

Escopo: todo o repositório. Entram o controle da TV (2.0.1), o Tower Defense (3.1.1) e as ferramentas da raiz (`setup-teste.sh`, `instalar-pack.sh`, `empacotar.sh` e o teste do pack). Tudo o que foi achado foi corrigido. O resultado são o controle **2.0.2** e o Tower Defense **3.1.2**.

## Como foi feita

1. **Análise estática:** `pyflakes` em todo o código Python ativo e `shellcheck` em todos os scripts ativos, além de `bash -n` e da conferência de permissões de execução.
2. **Linha de base:** todas as baterias de teste rodaram antes de qualquer mudança, e todas passaram.
3. **Revisão linha a linha do controle (`tv.py`):** protocolos IR, importação de arquivos do Flipper, emissor, fila de envio, telas e linha de comando.
4. **Sondagem de casos de borda do Tower Defense:** tamanhos extremos de mapa no gerador e no editor, configuração corrompida, Ctrl+C, tela pequena demais no meio da edição e processos filhos (vibração).
5. **Revisão da documentação:** versões e números citados, roteiros e LEIA-MEs.
6. **Correção com teste:** cada problema real ganhou correção e teste de regressão, e as baterias completas rodaram de novo.

## Problemas encontrados e corrigidos

Gravidade: **alta** quando o programa cai, perde dados ou faz a TV não obedecer; **média** quando atrapalha o uso; **baixa** quando é texto ou acabamento.

| # | Projeto | Gravidade | Problema | Correção | Teste |
|---|---|---|---|---|---|
| C1 | Controle | Alta | RC5/RC6 (TVs Philips importadas) mandavam o bit de alternância sempre em 0. A TV usa esse bit para separar um toque novo de uma tecla segurada, então "1" e "1" (canal 11) podia virar um "1" só. | O bit alterna a cada toque na tela e também entre execuções de `tv <botão>`, guardado na configuração. | Unidade: os padrões diferem e o bit decodificado é 0/1. Linha de comando: duas execuções mandam padrões diferentes. |
| T1 | Jogo | Alta | O gerador falhava em mapas de 5 casas de largura ou altura, que o formato aceita. Com um mapa assim no editor, 🎲 Gerar derrubava o jogo. | Zigue-zague de ponta a ponta para mapas estreitos, e o editor mostra uma mensagem em vez de cair. | Gerador em 25 combinações de tamanho, de 5×5 a 24×40; editor com mapa 5×5; `td --gerar 5x5`. |
| T2 | Jogo | Alta | Um `config.json` com tipo errado (ex.: `"recordes"` como lista, `"mapa"` como número) impedia o jogo de abrir. | Os valores inválidos são descartados na leitura. | Unidade com configuração corrompida. |
| T4 | Jogo | Alta | No editor com a tela pequena demais (teclado aberto), `q` fechava o jogo e perdia o mapa sem salvar, sem aviso. | `q` não fecha enquanto houver mudanças sem salvar, e o aviso diz "Mapa sem salvar: aumente a tela para salvar". | Tela: encolhe, `q`, o jogo continua vivo e, ao crescer, o desenho está lá. |
| C2 | Controle | Média | Sem o app Termux:API, cada toque esperava 10 s até falhar e os toques se enfileiravam, deixando "enviando..." por minutos. | Depois de uma falha dessas, os toques acumulados são descartados e a mensagem diz quantos. O tempo limite pode ser ajustado (`TV_IR_TIMEOUT`). | Unidade com emissor travado: 3 toques viram 1 envio e "2 toques descartados". |
| C3 | Controle | Média | Com muitas TVs importadas, a lista de escolha não rolava. As que passavam da tela ficavam invisíveis, mas ainda podiam ser escolhidas às cegas. | A lista acompanha a seleção, com ▲ e ▼ indicando que há mais. | Tela com 12 TVs importadas: rola, mostra e escolhe a que estava fora. |
| T3 | Jogo | Média | Ctrl+C despejava um erro técnico (`KeyboardInterrupt`) no terminal. | Saída limpa com código 130, igual ao controle. | Tela: Ctrl+C, código 130 e nenhum `Traceback`. |
| C4 | Controle | Baixa | TV importada com nome de marca embutida (ex.: "Samsung") aparecia como "embutido". | O rótulo segue o arquivo em `~/.config/pvn-tv/perfis`. | Unidade. |
| C5 | Controle | Baixa | `tv --perfil X ligar` com X inexistente dizia "Nenhuma TV escolhida". | Diz "TV desconhecida: X". | Unidade. |
| T5 | Jogo | Baixa | Se o Termux:API travasse durante uma vibração, o processo ficava solto depois de sair. | Encerrado na saída do jogo. | Revisão de código. Não dá para simular o travamento real do app. |
| T6 | Jogo | Baixa | A mensagem do gerador no editor saía cortada em 46 colunas. | Ganhou versão curta ("Gerado (semente N)"). | Tela (teste atualizado). |
| C6 | Controle | Baixa | O roteiro de teste citava a versão 2.0.0. | Atualizado para 2.0.2. | — |
| Q1 | Testes | Baixa | Variável sem uso em `test_logica.py`. | Passou a ser conferida (dano do casco = 4). | `pyflakes` limpo. |
| Q2 | Testes | Baixa | Scripts de teste sem permissão de execução. | `chmod +x` nos scripts de `testes/`. | — |

## Achados que não eram problema

- **`shellcheck` SC2034, "variável sem uso",** em vários testes. As variáveis são usadas dentro das strings avaliadas pelo `check` com `eval`, que o shellcheck não enxerga. Falso positivo.
- **`shellcheck` SC2046 em `cell()` do teste de tela.** A separação das palavras é intencional: a função devolve coluna e linha.
- **Instaladores, `setup-teste.sh`, `instalar-pack.sh` e `empacotar.sh`:** revisados sem falha funcional. Backup e restauração byte a byte, recusa de pasta estranha, zip corrompido e adulterado, sem `unzip` e `curl | bash` já têm testes.

## Resultado dos testes

| Bateria | Antes | Depois |
|---|---|---|
| Controle — IR, importação, linha de comando | 20 / 20 | **25 / 25** |
| Controle — tela | 27 / 27 | **30 / 30** |
| Controle — instalador | 9 / 9 | 9 / 9 |
| Jogo — lógica | 71 / 71 | **75 / 75** |
| Jogo — tela | 90 / 90 | **95 / 95** |
| Jogo — instalador | 29 / 29 | 29 / 29 |
| Pack (raiz) | 18 / 18 | 18 / 18 |

As baterias existentes já passavam antes da auditoria. Os problemas estavam em caminhos que elas não cobriam, e agora cobrem.

## O que continua sem teste automático

- **Emissor infravermelho real e a reação de cada TV:** incluindo o bit de alternância numa Philips de verdade.
- **Emojis, fonte, tela cheia, vibração e toque no Android real:** a régua em Opções → Ajustar tela ajuda a conferir.
- **Dificuldade sentida por um jogador humano.**

## Orientação do próximo passo

1. **Teste no celular:** instale o pack e siga os roteiros em `controle-tv/docs/ROADMAP.md` (10 passos) e `tower-defense/docs/ROADMAP.md` (13 passos). Priorize:
   - o controle ligando a **sua** TV;
   - a régua de emojis;
   - a tela cheia e a fonte;
   - a onda em que você perde em cada mapa.
2. **Mande de volta:**
   - marca e modelo da TV (etiqueta de trás) e se ligou;
   - modelo do celular;
   - capturas de tela de qualquer desalinhamento;
   - as ondas alcançadas.
3. **Desenvolvimento seguinte, nesta ordem:**
   1. Ajustar a dificuldade com as suas ondas reais. É barato e muda a experiência.
   2. Perfis embutidos das marcas que você tem (Philco, TCL, AOC, Semp). Depende do modelo real para não embutir código errado.
   3. Segurar VOL/CH repete o envio, no controle.
   4. Opção de 30 quadros por segundo no jogo.
   5. Compartilhar mapas por texto.

A continuação do projeto em outra sessão está descrita em `CHECKPOINT.md`, na raiz.
