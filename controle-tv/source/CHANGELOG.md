# Changelog — PVN Controle TV

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento semântico.

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
