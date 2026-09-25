// Testes E2E do PVN Controle TV.
// Uso (na raiz do repositório):
//   python3 -m http.server 8080
//   node controle-tv/testes/e2e.test.js                                   -> testa source/
//   BASE_URL=http://localhost:8080/controle-tv/legados/v1.0.0/index.html node controle-tv/testes/e2e.test.js
const { chromium } = require("playwright");

const BASE = process.env.BASE_URL || "http://localhost:8080/controle-tv/source/index.html";
const results = [];

function record(name, ok, detail = "", pending = false) {
  results.push({ name, ok, detail, pending });
  const tag = ok ? "PASS" : pending ? "TODO" : "FAIL";
  console.log(`${tag}  ${name}${!ok && detail ? "  — " + detail : ""}`);
}

async function fresh(browser, viewport = { width: 1280, height: 800 }) {
  const ctx = await browser.newContext({ viewport });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  await page.goto(BASE);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  return { ctx, page, errors };
}

const txt = (page, sel) => page.locator(sel).textContent();
const power = (page) => page.getAttribute("#tv", "data-power");

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });

  // 1. Ligar / desligar
  {
    const { ctx, page, errors } = await fresh(browser);
    record("Inicia desligada", (await power(page)) === "off");
    await page.click('[data-cmd="power"]');
    record("Liga pelo botão", (await power(page)) === "on");
    await page.click('[data-cmd="power"]');
    record("Desliga pelo botão", (await power(page)) === "off");
    record("Sem erros de console (fluxo básico)", errors.length === 0, errors.join(" | "));
    await ctx.close();
  }

  // 2. Canais, dígitos e último canal
  {
    const { ctx, page } = await fresh(browser);
    await page.click('[data-cmd="power"]');
    await page.click('[data-cmd="chan-up"]');
    record("CH+ vai para canal 2", (await txt(page, "#channelNum")) === "2");
    await page.click('[data-cmd="chan-down"]');
    await page.click('[data-cmd="chan-down"]');
    record("CH- faz wrap para canal 12", (await txt(page, "#channelNum")) === "12");
    await page.click('[data-digit="7"]');
    await page.waitForTimeout(1100);
    record("Dígito único troca canal (7)", (await txt(page, "#channelNum")) === "7");
    await page.click('[data-digit="1"]');
    await page.click('[data-digit="1"]');
    await page.waitForTimeout(1100);
    record("Dois dígitos troca canal (11)", (await txt(page, "#channelNum")) === "11");
    await page.click('[data-cmd="last-channel"]');
    record("Último canal volta para 7", (await txt(page, "#channelNum")) === "7");

    // digitar o canal atual não deve destruir o "último canal"
    await page.click('[data-digit="7"]');
    await page.waitForTimeout(1100);
    await page.click('[data-cmd="last-channel"]');
    const afterSame = await txt(page, "#channelNum");
    record("Último canal preservado ao digitar canal atual", afterSame === "11", `mostrou ${afterSame}, esperado 11`);

    await page.click('[data-digit="9"]');
    await page.click('[data-digit="9"]');
    await page.waitForTimeout(1100);
    const invalid = await txt(page, "#channelNum");
    const feedback = await page.locator("#screen").innerText();
    record("Canal inexistente (99) dá feedback ao usuário", /inexistente|inválido|indispon/i.test(feedback), `tela: "${invalid}" sem aviso`);
    await ctx.close();
  }

  // 3. Volume e mudo
  {
    const { ctx, page } = await fresh(browser);
    await page.click('[data-cmd="power"]');
    await page.click('[data-cmd="vol-up"]');
    record("VOL+ sobe de 20 para 22", (await txt(page, "#osdVolumeVal")) === "22");
    record("OSD de volume aparece", await page.locator("#osdVolume.show").count() === 1);
    await page.waitForTimeout(2100);
    record("OSD de volume some sozinho", await page.locator("#osdVolume.show").count() === 0);
    await page.click('[data-cmd="mute"]');
    record("Mudo exibe selo MUDO", await page.locator("#osdMute.show").count() === 1);
    await page.click('[data-cmd="vol-up"]');
    record("VOL+ remove mudo", await page.locator("#osdMute.show").count() === 0);
    for (let i = 0; i < 60; i++) await page.click('[data-cmd="vol-up"]');
    record("Volume limitado a 100", (await txt(page, "#osdVolumeVal")) === "100");
    await ctx.close();
  }

  // 4. Comandos com TV desligada não alteram estado
  {
    const { ctx, page } = await fresh(browser);
    await page.click('[data-cmd="chan-up"]');
    await page.click('[data-cmd="vol-up"]');
    const st = await page.evaluate(() => JSON.parse(localStorage.getItem("pvn-controle-tv:state")));
    record("TV desligada ignora CH/VOL", st.channelIndex === 0 && st.volume === 20);
    await ctx.close();
  }

  // 5. LED infravermelho deve apagar após o pulso
  {
    const { ctx, page } = await fresh(browser);
    await page.click('[data-cmd="power"]');
    await page.waitForTimeout(800);
    const stillOn = await page.locator("#irLed.active").count();
    record("LED IV apaga após o disparo", stillOn === 0, stillOn ? "classe .active permanece — LED fica aceso para sempre" : "");
    await ctx.close();
  }

  // 6. Espaço com botão focado não pode disparar duas vezes
  {
    const { ctx, page } = await fresh(browser);
    await page.click('[data-cmd="chan-up"]'); // foca um botão qualquer
    await page.keyboard.press("Space");
    await page.waitForTimeout(200);
    const p = await power(page);
    const logCount = await page.locator("#irLogList li").count();
    record("Espaço com botão focado liga a TV uma única vez", p === "on" && logCount === 2, `power=${p}, sinais=${logCount} (esperado on/2)`);
    await ctx.close();
  }

  // 7. Atalhos não devem rolar a página
  {
    const { ctx, page } = await fresh(browser, { width: 390, height: 500 });
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("ArrowDown");
    const y = await page.evaluate(() => window.scrollY);
    record("Setas não rolam a página ao usar atalhos", y === 0, `scrollY=${y}`);
    await ctx.close();
  }

  // 8. Estado corrompido no localStorage
  {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(BASE);
    await page.evaluate(() => localStorage.setItem("pvn-controle-tv:state", JSON.stringify({ power: true, channelIndex: 99, volume: "abc" })));
    await page.reload();
    await page.waitForTimeout(300);
    record("Estado corrompido não quebra o app", errors.length === 0, errors.join(" | "));
    await ctx.close();
  }

  // 9. Recarregar no meio da digitação
  {
    const { ctx, page } = await fresh(browser);
    await page.click('[data-cmd="power"]');
    await page.click('[data-digit="5"]');
    await page.reload();
    await page.waitForTimeout(1200);
    const shown = await txt(page, "#channelNum");
    record("Recarregar durante digitação não trava número pendente", shown === "1", `tela mostra "${shown}" indefinidamente`);
    await ctx.close();
  }

  // 10. Persistência
  {
    const { ctx, page } = await fresh(browser);
    await page.click('[data-cmd="power"]');
    await page.click('[data-cmd="chan-up"]');
    await page.click('[data-cmd="source"]');
    await page.reload();
    record("Persistência de canal e fonte", (await txt(page, "#channelNum")) === "2" && (await txt(page, "#osdInput")) === "HDMI 1");
    await ctx.close();
  }

  // 11. Botões sem efeito (menu / navegação)
  {
    const { ctx, page } = await fresh(browser);
    await page.click('[data-cmd="power"]');
    const before = await page.locator("#screen").innerHTML();
    await page.click('[data-cmd="menu"]');
    await page.click('[data-cmd="nav-down"]');
    await page.click('[data-cmd="ok"]');
    const after = await page.locator("#screen").innerHTML();
    record("Menu/Navegação/OK produzem efeito visível", before !== after, "tela idêntica antes e depois (pendente v1.1)", true);
    await ctx.close();
  }

  // 12. Layout responsivo sem rolagem horizontal
  for (const w of [360, 390, 768, 1280]) {
    const { ctx, page } = await fresh(browser, { width: w, height: 800 });
    const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    record(`Sem rolagem horizontal em ${w}px`, over <= 0, `excesso ${over}px`);
    if (w === 390) await page.screenshot({ path: __dirname + `/screenshots/${BASE.includes("legados") ? "v1.0.0" : "source"}-mobile-390.png`, fullPage: true });
    if (w === 1280) {
      await page.click('[data-cmd="power"]');
      await page.click('[data-cmd="vol-up"]');
      await page.waitForTimeout(450);
      await page.screenshot({ path: __dirname + `/screenshots/${BASE.includes("legados") ? "v1.0.0" : "source"}-desktop-1280.png` });
    }
    await ctx.close();
  }

  // 13. Acessibilidade básica
  {
    const { ctx, page } = await fresh(browser);
    const noLabel = await page.$$eval(".btn", (bs) => bs.filter((b) => !b.getAttribute("aria-label")).map((b) => b.textContent.trim()));
    record("Todos os botões têm aria-label", noLabel.length === 0, `sem rótulo: ${noLabel.join(" ")}`);
    const zoomLocked = await page.$eval('meta[name="viewport"]', (m) => /user-scalable=no|maximum-scale=1/.test(m.content));
    record("Zoom do usuário permitido", !zoomLocked, "viewport bloqueia zoom");
    await ctx.close();
  }

  await browser.close();
  const failed = results.filter((r) => !r.ok && !r.pending);
  const todo = results.filter((r) => !r.ok && r.pending);
  console.log(`\n${results.length - failed.length - todo.length}/${results.length} aprovados, ${failed.length} falhas, ${todo.length} pendentes`);
  require("fs").writeFileSync(__dirname + "/resultados/resultado-" + (BASE.includes("legados") ? "v1.0.0" : "source") + ".json", JSON.stringify(results, null, 2));
  process.exit(failed.length ? 1 : 0);
})();
