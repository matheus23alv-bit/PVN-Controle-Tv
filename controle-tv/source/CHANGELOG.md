# Changelog — PVN Controle TV

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento semântico.

## [2.0.0] — 2026-09-26

Mudança de direção: o controle agora comanda a TV de verdade, pelo emissor infravermelho do próprio celular, dentro do terminal do Termux. O simulador de navegador (1.0.x) foi para `legados/v1.0.2-simulador-web/`.

### Adicionado
- `tv.py`: controle remoto em tela cheia no Termux, com botões grandes para tocar (ligar, mudo, fonte, volume, canal, setas, OK, voltar, início, menu, info, exit e teclado numérico) e atalhos de teclado.
- Transmissão real pelo Termux:API (`termux-infrared-transmit`), em segundo plano para a tela não travar; o rodapé confirma cada envio ou explica o erro.
- Códigos embutidos de Samsung, LG e Sony, conferidos bit a bit contra os códigos publicados (ex.: Samsung ligar `E0E040BF`, LG ligar `20DF10EF`, Sony ligar `A90`).
- Codificadores NEC, NEC estendido, Samsung32, Sony SIRC 12/15/20, Philips RC5/RC6 e sinal bruto (raw).
- Importação de arquivos `.ir` do banco Flipper-IRDB (`tv --importar`), para qualquer outra marca: Philco, TCL, AOC, Semp e outras.
- "Descobrir TV": envia o LIGAR de cada marca e pergunta se a TV reagiu.
- Verificação do emissor ao abrir e em `tv --diagnostico`: avisa quando falta o pacote termux-api, quando o app Termux:API não responde e quando o celular não tem emissor IR.
- Linha de comando para um botão só (`tv ligar`, `tv vol+`, `tv 7`) e atalhos de tela inicial para o app Termux:Widget (`tv --atalhos`).
- `instalar.sh`: instala Python e termux-api, testa o emissor, cria o comando `tv` e, se quiser, os atalhos; `--remover` desinstala.
- Modo `--simular` para ver a tela num aparelho sem emissor.

### Removido
- Simulador de navegador (`index.html`, `style.css`, `app.js`, `iniciar.bat`, `iniciar.sh`), agora em `legados/v1.0.2-simulador-web/`.

## [1.0.2] — 2026-09-25

### Adicionado
- `iniciar.bat`: abre o controle no navegador padrão do Windows com dois cliques.
- `iniciar.sh`: abre no Linux/macOS; no Termux sobe um servidor local e abre no navegador do Android, escolhendo sozinho uma porta livre entre 8080 e 8099.
- Contorno de foco visível (`:focus-visible`) para quem navega pelo teclado com Tab.

### Corrigido
- "Canal NaN indisponível" aparecia ao apertar ⌫ ou desligar a TV logo depois de digitar um número (regressão da 1.0.1).
- Segurar Espaço ligava e desligava a TV em rajada; agora só volume, canal e setas repetem ao segurar a tecla.
- Atalho `m` não funcionava com Caps Lock ligado (`M`).
- No celular, dois toques rápidos no mesmo botão (ex.: VOL+) davam zoom na página (regressão da 1.0.1, que liberou o zoom); o zoom por pinça continua disponível.

## [1.0.1] — 2026-09-25

### Corrigido
- LED infravermelho ficava aceso para sempre após o primeiro comando; agora apaga após o pulso (220 ms).
- Espaço ou Enter com um botão focado disparavam dois comandos (o atalho e o clique do botão focado).
- Estado inválido no `localStorage` (ex.: canal fora da lista) quebrava o app com erro de JavaScript; o estado agora é validado campo a campo ao carregar.
- Recarregar a página no meio da digitação de um canal deixava o número pendente preso na tela; dígitos pendentes não são mais persistidos.
- Digitar o canal que já está no ar apagava a memória de "último canal".
- Canal inexistente (ex.: 99) era ignorado em silêncio; agora a TV mostra "Canal 99 indisponível".
- Atalhos com Ctrl/Alt/Cmd (ex.: Ctrl+- para zoom) também alteravam o volume.

### Acessibilidade
- Teclado numérico, último canal e apagar ganharam `aria-label`.
- Zoom do navegador liberado (removido `user-scalable=no` / `maximum-scale=1`).

### Interno
- Log de sinais montado com `textContent` em vez de `innerHTML`.
- Relógio da TV atualiza a cada 5 s (antes 30 s, podia ficar quase um minuto atrasado).
- Lista de fontes centralizada em uma constante.

## [1.0.0] — 2026-09-25

Versão inicial: TV com liga/desliga, volume, mudo, canais, teclado numérico, fonte, painel de sinais IV simulados e persistência local. Preservada em `legados/v1.0.0/`.
