# PVN Controle TV — roteiro de teste e próximos passos

## Roteiro de teste no seu celular (2.1.0)

Faça na ordem e anote o que aparecer diferente do esperado.

| # | Faça | Esperado |
|---|---|---|
| 1 | Instale o app Termux:API pelo F-Droid e abra uma vez | O app abre e fecha (não tem tela própria) |
| 2 | Instale pelo pack (`bash ~/storage/downloads/instalar-pack.sh`) | Termina com "controle 2.1.0 instalado" e "emissor IR pronto" |
| 3 | `tv --diagnostico` | `OK   emissor IR pronto (…kHz)` |
| 4 | `tv`, toque na marca da sua TV | O controle abre com "TV: <marca>" no topo |
| 5 | Aponte para a TV e toque em LIGAR | A TV liga ou desliga; o rodapé mostra "✓ Ligar/desligar enviado" |
| 6 | VOL +, VOL −, MUDO, CH +, CH − | A TV reage a cada um |
| 7 | Toque em 7 | A TV muda para o canal 7 |
| 8 | Setas, OK, VOLTAR, MENU, INÍCIO | O menu da TV responde |
| 9 | Se a marca não reagiu: `d` (descobrir) | Alguma marca faz a TV reagir; toque em SIM |
| 10 | `tv --atalhos` e adicione o widget do Termux:Widget | Os atalhos da tela inicial ligam a TV e mudam o volume |
| 11 | Com o `tv` aberto, olhe a barra de teclas do Termux | É a barra da TV (SAIR, LIGAR, MUDO, VOL+...) |
| 12 | Segure VOL+ na barra por 2 s e solte | O volume sobe sem parar e para logo ao soltar |
| 13 | Saia com SAIR ou `q` | A barra volta a ser a de antes (padrão melhorado, se você escolheu) |

Se nenhuma marca embutida funcionar, me diga a marca e o modelo da TV (a etiqueta atrás dela) e o modelo do celular.

## Próximos passos

| # | Tarefa | Ganho | Custo |
|---|---|---|---|
| 1 | Perfis embutidos de Philco, TCL, AOC e Semp, depois que você confirmar os modelos | Funciona sem importar arquivo | Baixo por marca, mas exige o modelo real para não embutir código errado |
| 2 | Botões da LG além da tela (Guia, Q.Menu, cores, play/pausa, ligar e desligar separados) | Aproveita o controle LG inteiro | Médio: uma segunda página de botões |
| 3 | Botões extras quando o perfil importado tiver (Netflix, YouTube, legendas) | Aproveita tudo o que o arquivo do Flipper traz | Médio |
| 4 | Controle por Wi-Fi para Smart TVs, como alternativa ao IR | Funciona em celulares sem emissor | Alto; depende da marca da TV |
| 5 | Macros (ex.: ligar, trocar para HDMI 2 e baixar o volume num toque) | Rotinas de uso diário | Médio |
