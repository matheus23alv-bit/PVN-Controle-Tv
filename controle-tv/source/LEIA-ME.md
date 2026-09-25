# PVN Controle TV

Simulador web de controle remoto de TV com emissão de infravermelho simulada. HTML, CSS e JavaScript puros: sem build, sem dependências e sem servidor obrigatório.

A versão instalada está no arquivo `VERSION` desta pasta, que é a única fonte oficial do número de versão. O histórico de mudanças está em `CHANGELOG.md`.

## Como rodar

Abra `index.html` direto no navegador, ou sirva esta pasta com qualquer servidor estático:

```bash
python3 -m http.server 8080
# acesse http://localhost:8080
```

Para publicar, envie o conteúdo desta pasta para qualquer hospedagem estática (Vercel, Netlify, GitHub Pages, Firebase Hosting). Não há configuração extra.

## Arquivos

| Arquivo | Função |
|---|---|
| `index.html` | Estrutura da TV, do controle e do painel de sinais |
| `style.css` | Visual, animações e layout responsivo |
| `app.js` | Estado, comandos, persistência e atalhos de teclado |
| `VERSION` | Número da versão atual |
| `CHANGELOG.md` | Histórico de alterações |

## Funcionalidades

A TV liga e desliga com animação; volume, mudo e troca de canal (botões, teclado numérico de até dois dígitos e último canal) exibem OSD na tela. A fonte alterna entre TV, HDMI 1, HDMI 2 e AV. Cada comando pisca o LED do controle e é registrado no painel "Sinais infravermelho". Canal, volume, mudo e fonte ficam salvos no navegador (`localStorage`, chave `pvn-controle-tv:state`).

## Atalhos de teclado

| Tecla | Comando |
|---|---|
| Espaço | Liga/desliga |
| `+` / `-` | Volume |
| `m` | Mudo |
| `0`–`9` | Canal direto |
| Setas / Enter | Navegação / OK |
| Backspace | Voltar |
| Esc | Início (volta para a fonte TV) |

Atalhos com Ctrl, Alt ou Cmd são ignorados para não conflitar com o navegador.

## Limitações conhecidas

Menu, setas, OK e Voltar emitem o sinal mas ainda não têm efeito visual na TV (planejado para a v1.1). O infravermelho é simulado: navegadores não têm acesso a emissores IR. Controlar uma TV física exige app nativo com IR blaster ou um hub IR em rede (ex.: Broadlink).
