# Controle Remoto de TV (PVN)

Aplicação web estática (HTML + CSS + JS puro, sem build e sem dependências) que simula um controle remoto de TV com emissão de sinal infravermelho e uma TV que reage aos comandos em tempo real.

## Como rodar

Não precisa de instalação. Basta subir um servidor estático na raiz do projeto:

```bash
python3 -m http.server 8080
# ou
npx serve .
```

Depois acesse `http://localhost:8080`. Também é possível abrir `index.html` direto no navegador.

## Estrutura

| Arquivo | Responsabilidade |
|---|---|
| `index.html` | Marcação da TV, do controle e do log de sinais |
| `style.css` | Visual (TV, corpo do controle, botões, LED de IV, animações) |
| `app.js` | Estado da aplicação, persistência e lógica dos comandos |

## Funcionalidades

- **Liga/desliga** a TV, com tela apagando/acendendo de forma animada.
- **Volume** (+/-) e **mudo**, com indicador OSD na tela que some sozinho.
- **Canal** (+/-), **teclado numérico** (troca direta por dois dígitos, com timeout de confirmação) e **último canal** (⟲).
- **Navegação** (setas + OK), **voltar**, **início** e **menu**.
- **Fonte** alterna entre TV / HDMI 1 / HDMI 2 / AV, exibido no canto da tela.
- **Atalhos de teclado**: espaço (power), setas, `+`/`-` (volume), `m` (mudo), dígitos 0-9, Enter (OK), Backspace (voltar), Esc (início).
- **Estado persistido** em `localStorage` (`pvn-controle-tv:state`) — fechar e reabrir a página mantém canal, volume, mudo e entrada selecionados.

## Sobre o infravermelho

Não existe uma API padrão de navegador para emitir infravermelho real — isso depende de hardware (blaster IR) e de um app nativo com acesso a ele. Por isso a aplicação **simula** a emissão: a cada comando, o LED vermelho no topo do controle pisca (com glow e animação de pulso) e o sinal é registrado no painel lateral **"Sinais infravermelho"**, com o nome do comando e o horário — reproduzindo visualmente e funcionalmente o comportamento de um controle IV real, mas dentro do que é tecnicamente possível em uma página web.

Se o objetivo for controlar um aparelho de TV físico de verdade, a via viável é um app nativo (Android, por exemplo, com API de IR blaster) ou um dispositivo IV em rede (ex.: Broadlink, Wi-Fi/HTTP) comandado a partir desta interface — não uma página web sozinha.

## Testado

Fluxo validado via Playwright/Chromium: ligar/desligar, troca de canal (botão e teclado numérico), volume, mudo, layout responsivo (mobile 390px e desktop), e persistência de estado no `localStorage` — sem erros de console.
