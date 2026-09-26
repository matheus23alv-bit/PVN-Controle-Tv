# Relatório de testes — PVN Controle TV

Data: 2026-09-25 · Navegador: Chromium (Playwright 1.56) · Viewports: 360, 390, 768 e 1280 px

## Resultado

| Versão | Aprovados | Falhas | Pendentes |
|---|---|---|---|
| 1.0.0 (legado) | 22 / 31 | 8 | 1 |
| 1.0.1 (source) | 30 / 31 | 0 | 1 |

O único pendente nas duas versões é Menu, Navegação e OK sem efeito visível, que é funcionalidade nova planejada para a v1.1 e não defeito de regressão.

## Erros encontrados na 1.0.0

Todos foram reproduzidos no navegador e estão corrigidos na 1.0.1.

| # | Gravidade | Erro | Como reproduzir |
|---|---|---|---|
| 1 | Alta | App quebra com estado salvo inválido (`Cannot read properties of undefined`) | Salvar `channelIndex: 99` no `localStorage` e recarregar |
| 2 | Alta | Espaço com botão focado dispara dois comandos | Clicar em CH+, depois apertar Espaço: liga a TV **e** troca o canal |
| 3 | Média | LED IV fica aceso para sempre | Apertar qualquer botão e esperar |
| 4 | Média | Número pendente preso na tela após recarregar | Digitar `5` e recarregar antes de 1 s |
| 5 | Média | "Último canal" perdido | Ir do 11 ao 7, digitar `7` de novo e apertar ⟲: fica no 7 |
| 6 | Baixa | Canal inexistente sem aviso | Digitar `99` |
| 7 | Baixa | 12 botões sem rótulo acessível | Teclado numérico, ⟲ e ⌫ |
| 8 | Baixa | Zoom bloqueado no celular | `user-scalable=no` no viewport |

Também corrigido, fora da bateria automática: Ctrl+- (zoom do navegador) diminuía o volume.

## Cobertura da bateria

Ligar/desligar; CH± com volta ao início da lista; canal direto com 1 e 2 dígitos; último canal; volume com limite de 100; mudo e retirada do mudo pelo volume; OSD aparecendo e sumindo; comandos ignorados com TV desligada; LED; foco + Espaço; rolagem com setas; estado corrompido; recarga durante digitação; persistência de canal e fonte; ausência de rolagem horizontal nos quatro tamanhos; `aria-label` e zoom.

## Como rodar

```bash
# na raiz do repositório
python3 -m http.server 8080 &
npm i -D playwright            # uma vez; ou use um Playwright global
node controle-tv/testes/e2e.test.js
BASE_URL=http://localhost:8080/controle-tv/legados/v1.0.0/index.html node controle-tv/testes/e2e.test.js
```

Resultados em `testes/resultados/*.json` e capturas em `testes/screenshots/`.
