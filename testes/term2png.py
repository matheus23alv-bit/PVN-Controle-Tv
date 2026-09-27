"""Converte uma captura do tmux (capture-pane -e -p) em PNG fiel: 256 cores, emojis de 2 colunas.

Uso: python3 testes/term2png.py captura.ans saida.png [colunas]
Precisa de node com o pacote playwright (Chromium) e das fontes DejaVu Sans Mono e Noto Color Emoji.
NODE_PATH pode apontar para onde o playwright está instalado (padrão: /opt/node22/lib/node_modules).
Mais fácil: bash testes/captura.sh <sessão-tmux> <nome> [colunas]
"""
import html
import re
import subprocess
import sys
import unicodedata

SGR = re.compile(r"\x1b\[([0-9;:]*)m")
BASE16 = ["#000000", "#cd0000", "#00cd00", "#cdcd00", "#0000ee", "#cd00cd", "#00cdcd", "#e5e5e5",
          "#7f7f7f", "#ff0000", "#00ff00", "#ffff00", "#5c5cff", "#ff00ff", "#00ffff", "#ffffff"]
DEF_FG, DEF_BG = "#e8e8e8", "#000000"


def c256(n):
    if n < 16:
        return BASE16[n]
    if n < 232:
        n -= 16
        lv = [0, 95, 135, 175, 215, 255]
        return "#%02x%02x%02x" % (lv[n // 36], lv[(n // 6) % 6], lv[n % 6])
    g = 8 + 10 * (n - 232)
    return "#%02x%02x%02x" % (g, g, g)


def width(ch):
    if unicodedata.combining(ch) or ch in "️‍":
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def parse(text, cols):
    rows = []
    fg = bg = None
    bold = rev = dim = False
    for raw in text.split("\n"):
        row = []
        pos = 0
        for m in list(SGR.finditer(raw)) + [None]:
            seg = raw[pos:m.start()] if m else raw[pos:]
            for ch in seg:
                w = width(ch)
                if w == 0:
                    continue
                row.append((ch, fg, bg, bold, rev, dim, w))
                if w == 2:
                    row.append(None)
            if not m:
                break
            ps = [int(p) if p else 0 for p in m.group(1).replace(":", ";").split(";")] or [0]
            i = 0
            while i < len(ps):
                p = ps[i]
                if p == 0:
                    fg = bg = None; bold = rev = dim = False
                elif p == 1: bold = True
                elif p == 2: dim = True
                elif p == 22: bold = dim = False
                elif p == 7: rev = True
                elif p == 27: rev = False
                elif p == 39: fg = None
                elif p == 49: bg = None
                elif 30 <= p <= 37: fg = BASE16[p - 30]
                elif 90 <= p <= 97: fg = BASE16[p - 90 + 8]
                elif 40 <= p <= 47: bg = BASE16[p - 40]
                elif 100 <= p <= 107: bg = BASE16[p - 100 + 8]
                elif p in (38, 48) and i + 2 < len(ps) and ps[i + 1] == 5:
                    if p == 38: fg = c256(ps[i + 2])
                    else: bg = c256(ps[i + 2])
                    i += 2
                i += 1
            pos = m.end()
        rows.append(row)
    return rows


def to_html(rows, cols):
    out = []
    for row in rows:
        cells = []
        n = 0
        for c in row:
            if c is None:
                continue
            ch, fg, bg, bold, rev, dim, w = c
            f, b = fg or DEF_FG, bg or DEF_BG
            if rev:
                f, b = b, f
            style = f"background:{b};color:{f};width:{w}ch"
            if bold: style += ";font-weight:700"
            if dim: style += ";opacity:.6"
            cells.append(f'<span style="{style}">{html.escape(ch) if ch != " " else "&nbsp;"}</span>')
            n += w
        if n < cols:
            cells.append(f'<span style="width:{cols - n}ch;background:{DEF_BG}"></span>')
        out.append("<div>" + "".join(cells) + "</div>")
    return f"""<html><head><meta charset="utf-8"><style>
body{{margin:0;background:{DEF_BG}}}
.t{{font:17px/1.25 "DejaVu Sans Mono","Noto Color Emoji",monospace;padding:12px;width:{cols}ch;background:{DEF_BG}}}
.t div{{display:flex;height:1.25em}}
.t span{{display:inline-block;text-align:center;overflow:visible;white-space:pre;font-family:"DejaVu Sans Mono","Noto Color Emoji",monospace}}
</style></head><body><div class="t">{"".join(out)}</div></body></html>"""


if __name__ == "__main__":
    import os
    src, dst = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else 44
    rows = parse(open(src, encoding="utf-8").read(), cols)
    while rows and not rows[-1]:
        rows.pop()
    page = dst.rsplit(".", 1)[0] + ".html"
    open(page, "w", encoding="utf-8").write(to_html(rows, cols))
    js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();
const p=await b.newPage({{deviceScaleFactor:1.5}});await p.goto('file://{page}');
const el=await p.$('.t');await el.screenshot({{path:'{dst}'}});await b.close();}})();"""
    subprocess.run(["node", "-e", js], check=True, env=dict(os.environ, NODE_PATH=os.environ.get("NODE_PATH", "/opt/node22/lib/node_modules")))
