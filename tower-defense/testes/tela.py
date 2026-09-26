"""Ajuda os testes de tela a achar onde tocar, lendo a tela capturada do tmux.

  python3 tela.py achar "TEXTO" [n]     coluna e linha (1-based) do meio do n-ésimo TEXTO na tela
  python3 tela.py casa X Y [LxA]         coluna e linha da casa (X, Y) do mapa (padrão 11x19)

As posições das casas saem do mesmo cálculo de layout do jogo; o painel do tutorial
é descoberto pela linha "TUTORIAL" na tela.
"""
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("td", os.path.join(HERE, "..", "source", "td.py"))
td = importlib.util.module_from_spec(spec)
spec.loader.exec_module(td)
SESSION = os.environ.get("TD_TMUX", "tdt")


def screen():
    out = subprocess.run(["tmux", "capture-pane", "-p", "-t", SESSION], capture_output=True, text=True).stdout
    return out.split("\n")


def size():
    out = subprocess.run(["tmux", "display", "-p", "-t", SESSION, "#{pane_width} #{pane_height}"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]), int(out[1])


def find(text, n=1):
    for row, line in enumerate(screen()):
        start = 0
        while True:
            i = line.find(text, start)
            if i < 0:
                break
            n -= 1
            if n == 0:
                col = td.text_width(line[:i]) + td.text_width(text) // 2
                return col + 1, row + 1
            start = i + 1
    return None


def cell(x, y, mw=11, mh=19):
    w, h = size()
    lines = screen()
    tut = next((r for r, ln in enumerate(lines) if "TUTORIAL " in ln), None)
    panel = 1
    if tut is not None:
        for p in range(1, 10):
            L = td.compute_layout(h, w, mw, mh, p)
            if L and L.panel_y == tut:
                panel = p
                break
    L = td.compute_layout(h, w, mw, mh, panel)
    row, col = L.anchor(x, y)
    return col + 1, row + 1


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "achar":
        pos = find(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1)
        if pos is None:
            sys.exit(1)
    else:
        mw, mh = (int(v) for v in (sys.argv[4] if len(sys.argv) > 4 else "11x19").split("x"))
        pos = cell(int(sys.argv[2]), int(sys.argv[3]), mw, mh)
    print(*pos)
