#!/usr/bin/env python3
"""Tower Defense para o terminal do Termux.

Um arquivo, só biblioteca padrão (curses). Tela cheia em retrato (9:16), jogue pelo
toque ou pelo teclado e crie os seus mapas no editor. Veja: td --ajuda
"""
import bisect
import curses
import hashlib
import json
import locale
import math
import os
import random
import re
import sys
import time
import unicodedata

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "td-termux")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
MAPS_DIR = os.path.join(CONFIG_DIR, "mapas")

FPS = 20
IDLE_WAIT = 0.25
MIN_UI_W = 30   # largura mínima para as barras de botões
MAX_K = 3       # escala máxima: cada casa vira 2k colunas x k linhas

TOWERS = {
    "1": {"name": "Arqueiro", "emoji": "🏹", "text": "A", "cost": 20, "range": 3.0, "dmg": 6, "rate": 0.5,
          "info": "rápido, alvo único"},
    "2": {"name": "Canhão", "emoji": "💣", "text": "C", "cost": 50, "range": 2.3, "dmg": 20, "rate": 1.4,
          "splash": 1.1, "info": "explode e atinge vizinhos"},
    "3": {"name": "Mago", "emoji": "🔮", "text": "M", "cost": 35, "range": 4.0, "dmg": 10, "rate": 0.9,
          "info": "maior alcance, vê fantasmas, fura casco"},
    "4": {"name": "Vórtice", "emoji": "🌀", "text": "V", "cost": 40, "range": 2.6, "dmg": 4, "rate": 0.8,
          "slow": 0.5, "slow_time": 1.6, "slow_area": 1.2, "info": "deixa lento quem está perto"},
}
MAGE = "3"  # a torre que enxerga fantasmas e ignora casco

# wave: primeira onda em que aparece; weight: peso no sorteio das ondas
ENEMIES = {
    "normal": {"name": "Invasor", "emoji": "👾", "text": "i", "hp": 28, "speed": 1.5, "gold": 4, "dmg": 1,
               "wave": 1, "weight": 12, "info": "comum"},
    "rapido": {"name": "Rato", "emoji": "🐀", "text": "r", "hp": 15, "speed": 2.6, "gold": 4, "dmg": 1,
               "wave": 2, "weight": 5, "info": "rápido"},
    "tanque": {"name": "Ogro", "emoji": "👹", "text": "O", "hp": 100, "speed": 0.85, "gold": 10, "dmg": 2,
               "wave": 3, "weight": 3, "info": "muita vida"},
    "lesma": {"name": "Lesma", "emoji": "🐌", "text": "l", "hp": 70, "speed": 0.75, "gold": 7, "dmg": 1,
              "wave": 4, "weight": 3, "regen": 0.05, "info": "se cura depois de 1 s sem apanhar"},
    "tartaruga": {"name": "Tartaruga", "emoji": "🐢", "text": "t", "hp": 55, "speed": 0.95, "gold": 8, "dmg": 1,
                  "wave": 5, "weight": 3, "armor": 4, "info": "casco: cada tiro perde 4 de dano"},
    "morcego": {"name": "Morcego", "emoji": "🦇", "text": "m", "hp": 24, "speed": 2.1, "gold": 6, "dmg": 1,
                "wave": 6, "weight": 3, "noslow": True, "info": "rápido e nunca fica lento"},
    "fantasma": {"name": "Fantasma", "emoji": "👻", "text": "f", "hp": 40, "speed": 1.3, "gold": 8, "dmg": 1,
                 "wave": 8, "weight": 2, "ghost": True, "info": "some de vez em quando: só o Mago vê"},
    "chefe": {"name": "Dragão", "emoji": "🐉", "text": "D", "hp": 520, "speed": 0.6, "gold": 50, "dmg": 5,
              "wave": 5, "weight": 0, "summon": 3, "info": "chefe a cada 5 ondas; ferido, chama 3 ratos"},
}
START_GOLD = 100
START_LIFE = 20
SPAWN_INTERVAL = 0.7
HP_GROWTH = 1.16
MAX_LEVEL = 3
STEP = 0.05          # passo máximo da simulação, para nada atravessar alcance entre quadros
SPEED_JITTER = 0.06  # cada monstro anda até 6% mais rápido ou mais devagar: a fila se espalha
GHOST_SHOW, GHOST_HIDE = 2.5, 1.2
REGEN_DELAY = 1.0

BG = 234  # fundo da tela cheia
LEVEL_BG = {1: 239, 2: 65, 3: 136}
RANGE_BG = {28: 70, 137: 179, 25: 31, 94: 136}
TEXT_COLORS = {"1": 51, "2": 226, "3": 201, "4": 39, "normal": 196, "rapido": 250, "tanque": 160,
               "lesma": 214, "tartaruga": 34, "morcego": 99, "fantasma": 255, "chefe": 201}
EIGHTHS = " ▏▎▍▌▋▊▉█"

GLYPHS = {  # emoji / texto, sempre 2 colunas
    "spawn": ("🚪", "S "), "base": ("🏰", "B "), "tree": ("🌳", "♣ "), "kill": ("💥", "x "),
    "mark": ("✨", "<>"), "summon": ("✨", "**"), "life": ("💗", "V:"), "gold": ("💰", "$:"),
    "wave": ("🌊", "O:"), "kills": ("💀", "K:"), "trophy": ("🏆", "* "), "party": ("🎉", "! "),
    "fast": ("⏩", ">>"), "up": ("⏫", "^ "), "sell": ("💲", "$ "), "dice": ("🎲", "? "),
    "save": ("💾", "# "), "edit": ("📝", "E "), "new": ("➕", "+ "), "del": ("❌", "X "),
    "maps": ("🧭", "M "), "learn": ("🎓", "T "), "help": ("❓", "? "), "opts": ("🔧", "O "),
    "exit": ("🚪", "< "),
}


def read_version():
    try:
        with open(os.path.join(APP_DIR, "VERSION"), encoding="utf-8") as f:
            return f.read().strip() or "dev"
    except OSError:
        return "dev"


def load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG_FILE)
    except OSError:
        pass


# ================================================================ mapas
#
# Arquivo .mapa: texto, uma linha por fileira de casas.
#   .  grama (constrói)   #  trilha   S  entrada   B  base   T  árvore   ~  água
# Linhas com ":" são informações (nome: Meu mapa). Linhas vazias ou com ";" são ignoradas.

TILES = {"S": "Entrada", "#": "Trilha", "B": "Base", ".": "Grama", "T": "Árvore", "~": "Água"}
WALK = "#SB"
MAP_SIZES = [(9, 15), (11, 19), (13, 23)]
MAP_MIN, MAP_MAX_W, MAP_MAX_H = 5, 24, 40
MIN_PATH = 10
MIN_GRASS = 4


class MapError(ValueError):
    def __init__(self, msg, pos=None):
        super().__init__(msg)
        self.msg, self.pos = msg, pos


def where(p):
    return f"col {p[0] + 1}, lin {p[1] + 1}"


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:30] or "mapa"


def line_cells(a, b):
    """Casas de a (exclusive) até b (inclusive), em linha reta."""
    (x, y), (x1, y1) = a, b
    dx, dy = (x1 > x) - (x1 < x), (y1 > y) - (y1 < y)
    out = []
    while (x, y) != (x1, y1):
        x, y = x + dx, y + dy
        out.append((x, y))
    return out


class Mapa:
    def __init__(self, rows, name="Sem nome", builtin=False, file=None):
        self.name, self.builtin, self.file = name, builtin, file
        self.seed = None
        self.version = 0
        self._checked = -1
        self._path = self._err = None
        self.set_rows(rows)

    def set_rows(self, rows):
        self.grid = [list(r) for r in rows]
        self.h, self.w = len(self.grid), len(self.grid[0])
        self.version += 1

    def rows(self):
        return ["".join(r) for r in self.grid]

    def at(self, x, y):
        return self.grid[y][x]

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def put(self, x, y, ch):
        if self.grid[y][x] != ch:
            self.grid[y][x] = ch
            self.version += 1

    def find(self, ch):
        return [(x, y) for y in range(self.h) for x in range(self.w) if self.grid[y][x] == ch]

    def copy(self, name=None):
        m = Mapa(self.rows(), name or self.name, file=None if name else self.file)
        m.seed = self.seed
        return m

    def resized(self, w, h):
        old = self.rows()
        return [(old[y] if y < self.h else "")[:w].ljust(w, ".") for y in range(h)]

    @property
    def key(self):
        """Identifica o desenho do mapa: o recorde fica ligado a ele."""
        return hashlib.sha1("\n".join(self.rows()).encode()).hexdigest()[:10]

    def to_text(self):
        head = [f"nome: {self.name}"]
        if self.seed is not None:
            head.append(f"semente: {self.seed}")
        return "\n".join(head + self.rows()) + "\n"

    @classmethod
    def from_text(cls, text, name=None, file=None):
        meta, rows = {}, []
        for n, raw in enumerate(text.splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith(";"):
                continue
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip().lower()] = v.strip()
                continue
            row = []
            for c in line:
                c = c.upper() if c in "sbt" else c
                if c not in TILES:
                    raise MapError(f"Letra '{c}' desconhecida na linha {n}")
                row.append(c)
            rows.append(row)
        if not rows:
            raise MapError("O arquivo não tem mapa")
        w, h = max(len(r) for r in rows), len(rows)
        if w < MAP_MIN or h < MAP_MIN:
            raise MapError(f"Mapa pequeno demais ({w}×{h}); o mínimo é {MAP_MIN}×{MAP_MIN}")
        if w > MAP_MAX_W or h > MAP_MAX_H:
            raise MapError(f"Mapa grande demais ({w}×{h}); o máximo é {MAP_MAX_W}×{MAP_MAX_H}")
        m = cls([r + ["."] * (w - len(r)) for r in rows], meta.get("nome") or name or "Sem nome", file=file)
        if meta.get("semente", "").isdigit():
            m.seed = int(meta["semente"])
        return m

    def neighbors(self, p):
        x, y = p
        return [(a, b) for a, b in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                if 0 <= a < self.w and 0 <= b < self.h and self.grid[b][a] in WALK]

    def trace(self):
        """Segue a trilha da entrada até a base. Devolve as casas em ordem ou levanta MapError."""
        starts, bases = self.find("S"), self.find("B")
        if not starts:
            raise MapError("Falta a entrada (S)")
        if len(starts) > 1:
            raise MapError("Só pode haver uma entrada", starts[1])
        if not bases:
            raise MapError("Falta a base (B)")
        if len(bases) > 1:
            raise MapError("Só pode haver uma base", bases[1])
        start, base = starts[0], bases[0]
        path, prev, cur = [start], None, start
        while cur != base:
            nxt = [q for q in self.neighbors(cur) if q != prev]
            if not nxt:
                raise MapError("A entrada não encosta na trilha" if cur == start
                               else f"Trilha sem saída em {where(cur)}", cur)
            if len(nxt) > 1:
                raise MapError(f"Trilha se divide ou encosta em {where(cur)}", cur)
            prev, cur = cur, nxt[0]
            path.append(cur)
            if len(path) > self.w * self.h:
                raise MapError("A trilha anda em círculo", cur)
        if len(self.neighbors(base)) > 1:
            raise MapError("A trilha encosta na base por dois lados", base)
        on_path = set(path)
        loose = [p for p in self.find("#") if p not in on_path]
        if loose:
            raise MapError(f"Trilha solta em {where(loose[0])}", loose[0])
        if len(path) < MIN_PATH:
            raise MapError(f"Trilha curta: {len(path)} casas (mínimo {MIN_PATH})")
        if sum(r.count(".") for r in self.grid) < MIN_GRASS:
            raise MapError("Falta grama para construir torres")
        return path

    def check(self):
        """(trilha, None) se o mapa pode ser jogado, senão (None, MapError). Guarda o resultado."""
        if self._checked != self.version:
            try:
                self._path, self._err = self.trace(), None
            except MapError as e:
                self._path, self._err = None, e
            self._checked = self.version
        return self._path, self._err


def _snake(W, H, rng):
    """Trilha em zigue-zague com faixas horizontais separadas por 2 a 4 fileiras de grama."""
    ys, y = [], rng.randint(1, 2)
    while y <= H - 2:
        ys.append(y)
        y += rng.choice((3, 3, 3, 4, 4, 5))
    if len(ys) < 2:
        return None
    right = rng.random() < 0.5
    if rng.random() < 0.5:
        x = 0 if right else W - 1  # entrada na lateral
        pts = [(x, ys[0])]
    else:
        x = rng.randint(1, W // 2 - 1) if right else rng.randint(W // 2 + 1, W - 2)
        pts = [(x, 0), (x, ys[0])]  # entrada no topo
    for i, ly in enumerate(ys):
        last = i == len(ys) - 1
        long = rng.random() < 0.7  # a maioria das faixas cruza o mapa quase todo
        if right:
            lo, hi = max(x + 3, W - 3 if long else W // 2 + 1), W - 2
        else:
            lo, hi = 1, min(x - 3, 2 if long else W // 2 - 1)
        if lo > hi:
            return None
        end = rng.random()
        if last and end < 0.35:
            tx = W - 1 if right else 0  # base na lateral
        else:
            tx = rng.randint(lo, hi)
        pts.append((tx, ly))
        if not last:
            pts.append((tx, ys[i + 1]))
        elif end > 0.7 and ly < H - 1:
            pts.append((tx, H - 1))  # base embaixo
        x, right = tx, not right
    g = [["."] * W for _ in range(H)]
    g[pts[0][1]][pts[0][0]] = "#"
    for a, b in zip(pts, pts[1:]):
        for cx, cy in line_cells(a, b):
            g[cy][cx] = "#"
    g[pts[0][1]][pts[0][0]] = "S"
    g[pts[-1][1]][pts[-1][0]] = "B"
    return g


def _decorate(m, path, rng):
    near = {(x + dx, y + dy) for x, y in path for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    far = [(x, y) for x, y in m.find(".") if (x, y) not in near]
    rng.shuffle(far)
    far_set = set(far)
    used = set()
    if far and rng.random() < 0.6:  # lago
        pond = [far[0]]
        for _ in range(rng.randint(3, 8)):
            x, y = rng.choice(pond)
            dx, dy = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            q = (x + dx, y + dy)
            if q in far_set and q not in pond:
                pond.append(q)
        for x, y in pond:
            m.put(x, y, "~")
        used.update(pond)
    trees = max(2, m.w * m.h // 35)
    for x, y in far:
        if trees <= 0:
            break
        if (x, y) not in used:
            m.put(x, y, "T")
            trees -= 1


def generate_map(w=11, h=19, seed=None, name=None):
    """Gera um mapa jogável. A mesma semente sempre gera o mesmo mapa."""
    if seed is None:
        seed = random.randrange(1, 1_000_000)
    rng = random.Random(seed)
    for _ in range(500):
        vertical = min(w, h) >= 9 and rng.random() < 0.3  # às vezes as faixas ficam em pé
        grid = _snake(h, w, rng) if vertical else _snake(w, h, rng)
        if grid is None:
            continue
        if vertical:
            grid = [list(r) for r in zip(*grid)]
        m = Mapa(grid, name or f"Aleatório {seed}")
        path, err = m.check()
        if err or len(path) < max(MIN_PATH, w * h // 5):
            continue
        _decorate(m, path, rng)
        m.seed = seed
        return m
    raise RuntimeError("não consegui gerar um mapa com esse tamanho")


BUILTIN_TEXT = {
    "Serpente": [
        ".S....T....", ".#.........", ".#########.", ".........#.", ".........#.", ".#########.",
        ".#........T", ".#.........", ".#########.", ".........#.", "T........#.", ".#########.",
        ".#........T", ".#.........", ".#########.", ".........#.", ".........#.", ".B########.",
        ".....T.....",
    ],
    "Espiral": [
        "..........T", "S#########.", ".........#.", ".........#.", ".........#.", ".######..#.",
        ".#....#..#.", ".#....#..#.", ".#....#..#.", ".#..B.#..#.", ".#..#.#..#.", ".#..#.#..#.",
        ".#..#.#..#.", ".#..###..#.", ".#.......#.", ".#...T...#.", ".#.......#.", ".#########.",
        "T.........T",
    ],
    "Rio": [
        ".....T.....", "S#########.", ".........#.", "..T......#.", ".#########.", ".#.......T.",
        ".#.........", ".#######...", "T......#..T", "~~~~~~~#~~~", "~~~~~~~#~~~", ".T.....#...",
        ".#######...", ".#.......T.", ".#.........", ".#########.", ".........#.", "..T......#.",
        ".B########.",
    ],
}
_BUILTIN = []


def builtin_maps():
    if not _BUILTIN:
        _BUILTIN.extend(Mapa(rows, name, builtin=True) for name, rows in BUILTIN_TEXT.items())
    return list(_BUILTIN)


def load_map_file(path, keep_file=False):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        raise MapError(f"Não consegui ler {path}: {e}")
    stem = os.path.splitext(os.path.basename(path))[0]
    return Mapa.from_text(text, name=stem, file=path if keep_file else None)


def user_maps():
    try:
        names = sorted(os.listdir(MAPS_DIR))
    except OSError:
        return []
    out = []
    for fn in names:
        if fn.endswith(".mapa"):
            try:
                out.append(load_map_file(os.path.join(MAPS_DIR, fn), keep_file=True))
            except MapError:
                continue
    return sorted(out, key=lambda m: m.name.lower())


def save_user_map(m, name, old_file=None):
    """Salva em ~/.config/td-termux/mapas/<nome>.mapa. Levanta MapError com o motivo."""
    name = " ".join(name.split())[:24]
    if not name:
        raise MapError("Digite um nome")
    s = slug(name)
    if any(slug(b.name) == s for b in builtin_maps()):
        raise MapError("Esse nome é de um mapa pronto")
    path = os.path.join(MAPS_DIR, s + ".mapa")
    same = old_file and os.path.abspath(old_file) == os.path.abspath(path)
    if os.path.exists(path) and not same:
        raise MapError("Já existe um mapa com esse nome")
    old_name = m.name
    m.name = name
    try:
        os.makedirs(MAPS_DIR, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(m.to_text())
        os.replace(tmp, path)
    except OSError as e:
        m.name = old_name
        raise MapError(f"Não consegui salvar: {e.strerror or e}")
    if old_file and not same:
        try:
            os.remove(old_file)
        except OSError:
            pass
    m.file = path
    return path


def map_ref(m):
    if m.builtin:
        return "pronto:" + slug(m.name)
    return "meu:" + os.path.basename(m.file) if m.file else None


def find_map(ref):
    kind, _, val = (ref or "").partition(":")
    if kind == "pronto":
        return next((m for m in builtin_maps() if slug(m.name) == val), None)
    if kind == "meu":
        return next((m for m in user_maps() if os.path.basename(m.file) == val), None)
    return None


def resolve_map(ref):
    """Mapa pelo nome (pronto ou seu) ou pelo caminho de um arquivo .mapa."""
    s = slug(ref)
    for m in builtin_maps() + user_maps():
        if slug(m.name) == s:
            return m
    if os.path.isfile(ref):
        return load_map_file(ref)
    raise MapError(f"Mapa não encontrado: {ref}")


def next_map_name(prefix="Meu mapa"):
    taken = {slug(m.name) for m in builtin_maps() + user_maps()}
    n = 1
    while slug(f"{prefix} {n}") in taken:
        n += 1
    return f"{prefix} {n}"


# ================================================================ lógica

class Tower:
    def __init__(self, x, y, key):
        self.x, self.y, self.key = x, y, key
        self.level = 1
        self.spent = TOWERS[key]["cost"]
        self.last = -999.0
        self.span = None

    @property
    def cfg(self):
        return TOWERS[self.key]

    @property
    def damage(self):
        return self.cfg["dmg"] * (1 + 0.6 * (self.level - 1))

    @property
    def range(self):
        return self.cfg["range"] + 0.4 * (self.level - 1)

    @property
    def rate(self):
        return self.cfg["rate"]

    @property
    def upgrade_cost(self):
        return None if self.level >= MAX_LEVEL else int(self.cfg["cost"] * 0.7 * self.level)

    @property
    def refund(self):
        return self.spent // 2


class Enemy:
    def __init__(self, kind, wave, hp_scale=1.0, rng=None):
        base = ENEMIES[kind]
        self.kind = kind
        self.max_hp = base["hp"] * (HP_GROWTH ** (wave - 1)) * hp_scale
        self.hp = self.max_hp
        self.speed = base["speed"] * (1 + rng.uniform(-SPEED_JITTER, SPEED_JITTER) if rng else 1)
        self.gold = int(base["gold"] * (1 + 0.02 * (wave - 1)))
        self.dmg = base["dmg"]
        self.armor = base.get("armor", 0)
        self.regen = base.get("regen", 0.0)
        self.noslow = base.get("noslow", False)
        self.ghost = base.get("ghost", False)
        self.phase = rng.uniform(0, GHOST_SHOW + GHOST_HIDE) if rng and self.ghost else 0.0
        self.summon = base.get("summon", 0)
        self.summoned = False
        self.progress = 0.0
        self.alive = True
        self.leaked = False
        self.slow_until = -1.0
        self.slow_factor = 1.0
        self.hit_until = -1.0
        self.last_hit = -999.0

    def hidden(self, now):
        return self.ghost and (now + self.phase) % (GHOST_SHOW + GHOST_HIDE) >= GHOST_SHOW


def tower_span(t, path):
    # um inimigo entre as casas i e i+1 fica a no máximo 1 casa de path[i]
    reach = t.range + 1
    idx = [i for i, (x, y) in enumerate(path) if math.hypot(x - t.x, y - t.y) <= reach]
    return (idx[0], idx[-1]) if idx else (0, -1)


def make_wave(n, rng):
    pool = [(k, c["weight"]) for k, c in ENEMIES.items() if c["weight"] and n >= c["wave"]]
    kinds = rng.choices([k for k, _ in pool], [w for _, w in pool], k=min(4 + 2 * n, 60))
    if n % 5 == 0:
        kinds += ["chefe"] * (n // 10 + 1)
    return kinds


class Game:
    def __init__(self, mapa=None, seed=None, tutorial=False):
        self.mapa = mapa or builtin_maps()[0]
        path, err = self.mapa.check()
        if err:
            raise err
        self.path = path
        self.path_set = set(path)
        self.w, self.h = self.mapa.w, self.mapa.h
        self.rng = random.Random(seed)
        self.tutorial = tutorial
        self.gold, self.life, self.wave, self.kills = START_GOLD, START_LIFE, 0, 0
        self.towers = {}
        self.enemies, self.queue = [], []
        self.next_queue = self.plan_wave(1)
        self.spawn_timer = 0.0
        self.wave_active = False
        self.over = False
        self.time = 0.0
        self.speed = 1
        self.effects = []  # (tipo, x, y, início, fim, texto)
        self.leak_until = -1.0
        self.spawn_until = -1.0

    def plan_wave(self, n):
        return ["normal"] * 4 if self.tutorial else make_wave(n, self.rng)

    # ------------------------------------------------------ ações
    def can_build(self, x, y):
        return self.mapa.inside(x, y) and self.mapa.at(x, y) == "." and (x, y) not in self.towers

    def build(self, x, y, key):
        if not self.mapa.inside(x, y):
            return False, "Fora do mapa"
        if (x, y) in self.towers:
            return False, "Já tem torre aqui"
        c = self.mapa.at(x, y)
        if c != ".":
            what = {"T": "na árvore", "~": "na água"}.get(c, "na trilha")
            return False, f"Não dá para construir {what}"
        cfg = TOWERS[key]
        if self.gold < cfg["cost"]:
            return False, f"Falta ouro: {cfg['name']} custa {cfg['cost']}"
        self.gold -= cfg["cost"]
        self.towers[(x, y)] = Tower(x, y, key)
        return True, f"{cfg['name']} construído"

    def upgrade(self, x, y):
        t = self.towers.get((x, y))
        if t is None:
            return False, "Nenhuma torre aqui"
        cost = t.upgrade_cost
        if cost is None:
            return False, f"{t.cfg['name']} já está no nível máximo"
        if self.gold < cost:
            return False, f"Falta ouro: melhorar custa {cost}"
        self.gold -= cost
        t.spent += cost
        t.level += 1
        t.span = None
        return True, f"{t.cfg['name']} agora é nível {t.level}"

    def sell(self, x, y):
        t = self.towers.pop((x, y), None)
        if t is None:
            return False, "Nenhuma torre aqui"
        self.gold += t.refund
        return True, f"{t.cfg['name']} vendido (+{t.refund})"

    def next_wave(self):
        if self.over:
            return False, ""
        if self.wave_active or self.enemies:
            return False, "Aguarde o fim da onda"
        self.wave += 1
        self.queue = self.next_queue
        self.next_queue = self.plan_wave(self.wave + 1)
        self.wave_active = True
        self.spawn_timer = 0.0
        return True, f"Onda {self.wave}!"

    def enemy_pos(self, e):
        path = self.path
        i = int(e.progress)
        if i >= len(path) - 1:
            return path[-1]
        f = e.progress - i
        (x0, y0), (x1, y1) = path[i], path[i + 1]
        return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f

    # ------------------------------------------------------ tempo
    def update(self, dt):
        dt *= self.speed
        while dt > 1e-9 and not self.over:
            step = min(dt, STEP)
            self._step(step)
            dt -= step

    def _step(self, dt):
        self.time += dt
        now = self.time
        if self.wave_active:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and self.queue:
                scale = 0.6 if self.tutorial else 1.0
                self.enemies.append(Enemy(self.queue.pop(0), self.wave, scale, self.rng))
                self.spawn_timer = SPAWN_INTERVAL
                self.spawn_until = now + 0.25
        end = len(self.path) - 1
        for e in self.enemies:
            if not e.alive:
                continue
            f = e.slow_factor if now < e.slow_until else 1.0
            e.progress += e.speed * f * dt
            if e.regen and e.hp < e.max_hp and now - e.last_hit >= REGEN_DELAY:
                e.hp = min(e.max_hp, e.hp + e.regen * e.max_hp * dt)
            if e.progress >= end:
                e.alive = False
                e.leaked = True
                self.life -= e.dmg
                self.leak_until = now + 0.5
                bx, by = self.path[-1]
                self.effects.append(("leak", bx, by, now, now + 0.8, f"-{e.dmg}"))
        self._fire()
        self.enemies = [e for e in self.enemies if e.alive]
        if self.effects:
            self.effects = [fx for fx in self.effects if fx[4] > now]
        if self.wave_active and not self.queue and not self.enemies:
            self.wave_active = False
            self.gold += 3 + self.wave
        if self.life <= 0:
            self.life = 0
            self.over = True

    def _fire(self):
        now = self.time
        ready = [t for t in self.towers.values() if now - t.last >= t.rate]
        if not ready or not self.enemies:
            return
        alive = sorted((e for e in self.enemies if e.alive), key=lambda e: e.progress)
        progress = [e.progress for e in alive]
        positions = [self.enemy_pos(e) for e in alive]
        hidden = [e.hidden(now) for e in alive]
        for t in ready:
            if t.span is None:
                t.span = tower_span(t, self.path)
            lo, hi = t.span
            r2 = t.range ** 2
            sees = t.key == MAGE
            j = bisect.bisect_left(progress, hi + 1) - 1
            stop = bisect.bisect_left(progress, lo)
            while j >= stop:
                e = alive[j]
                if e.alive and (sees or not hidden[j]):
                    ex, ey = positions[j]
                    if (ex - t.x) ** 2 + (ey - t.y) ** 2 <= r2:
                        self._hit(t, e, ex, ey, alive, positions)
                        t.last = now
                        break
                j -= 1

    def _hit(self, t, target, tx, ty, alive, positions):
        cfg = t.cfg
        dmg = t.damage
        now = self.time
        hits = [(target, dmg)]
        if "splash" in cfg:
            s2 = cfg["splash"] ** 2
            for e, (ex, ey) in zip(alive, positions):
                if e is not target and e.alive and (ex - tx) ** 2 + (ey - ty) ** 2 <= s2:
                    hits.append((e, dmg * 0.5))
        if "slow" in cfg:
            a2 = cfg["slow_area"] ** 2
            for e, (ex, ey) in zip(alive, positions):
                if e.alive and not e.noslow and (ex - tx) ** 2 + (ey - ty) ** 2 <= a2:
                    e.slow_until = now + cfg["slow_time"]
                    e.slow_factor = max(cfg["slow"], 0.8) if e.kind == "chefe" else cfg["slow"]
        magic = t.key == MAGE
        for e, d in hits:
            if e.armor and not magic:
                d = max(d * 0.25, d - e.armor)
            e.hp -= d
            e.hit_until = now + 0.08
            e.last_hit = now
            if e.hp <= 0 and e.alive:
                e.alive = False
                self.gold += e.gold
                self.kills += 1
                x, y = self.enemy_pos(e)
                self.effects.append(("kill", x, y, now, now + 0.3, ""))
                self.effects.append(("gold", x, y, now + 0.15, now + 0.9, f"+{e.gold}"))
            elif e.summon and e.alive and not e.summoned and e.hp <= e.max_hp / 2:
                e.summoned = True
                self._summon(e)

    def _summon(self, boss):
        now = self.time
        for i in range(boss.summon):
            m = Enemy("rapido", self.wave, 1.0, self.rng)
            m.progress = max(0.0, boss.progress - 0.4 * (i + 1))
            self.enemies.append(m)
        x, y = self.enemy_pos(boss)
        self.effects.append(("summon", x, y, now, now + 0.5, ""))


# ================================================================ editor (sem tela)

class Editor:
    TOOLS = ["S", "#", "B", ".", "T", "~"]
    HINTS = {
        "S": "Entrada: de onde os monstros saem",
        "#": "Trilha: toque nos cantos; a reta se forma",
        "B": "Base: o que você defende",
        ".": "Grama: apaga; aqui se constroem torres",
        "T": "Árvore: enfeite; não aceita torre",
        "~": "Água: lago ou rio; trilha em cima = ponte",
    }

    def __init__(self, mapa, back="menu", dirty=False):
        self.mapa = mapa
        self.back = back
        self.dirty = dirty
        self.tool = "#" if mapa.find("S") else "S"
        self.undo_stack = []
        self.anchor = None
        self.cursor = [mapa.w // 2, mapa.h // 2]
        self.kbd = False

    def _save_undo(self):
        self.undo_stack.append((self.mapa.rows(), self.anchor))
        del self.undo_stack[:-80]
        self.dirty = True

    def undo(self):
        if not self.undo_stack:
            return False
        rows, self.anchor = self.undo_stack.pop()
        self.mapa.set_rows(rows)
        self.cursor = [min(self.cursor[0], self.mapa.w - 1), min(self.cursor[1], self.mapa.h - 1)]
        self.dirty = True
        return True

    def aligned(self, x, y):
        a = self.anchor
        return a is not None and a != (x, y) and (a[0] == x or a[1] == y)

    def paint(self, x, y):
        """Pinta a casa com a ferramenta atual. Devolve uma mensagem para a tela, ou None."""
        m, tool = self.mapa, self.tool
        cur = m.at(x, y)
        if tool == "#":
            if cur in WALK:
                self.anchor = (x, y)
                return "Continuando a trilha daqui"
            cells = line_cells(self.anchor, (x, y)) if self.aligned(x, y) else [(x, y)]
            self._save_undo()
            for c in cells:
                if m.at(*c) not in "SB":
                    m.put(*c, "#")
            self.anchor = (x, y)
            return None
        if cur == tool:
            return None
        self._save_undo()
        if tool in "SB":
            for p in m.find(tool):
                m.put(*p, ".")
            if tool == "B" and self.aligned(x, y):
                for c in line_cells(self.anchor, (x, y))[:-1]:
                    if m.at(*c) not in "SB":
                        m.put(*c, "#")
            m.put(x, y, tool)
            if tool == "S":
                self.anchor = (x, y)
                self.tool = "#"
                return "Entrada posta: agora toque nos cantos da trilha"
            self.anchor = None
            return None
        m.put(x, y, tool)
        if self.anchor == (x, y):
            self.anchor = None
        return None

    def resize(self, w, h):
        self._save_undo()
        self.mapa.set_rows(self.mapa.resized(w, h))
        self.anchor = None
        self.cursor = [min(self.cursor[0], w - 1), min(self.cursor[1], h - 1)]

    def clear(self):
        self._save_undo()
        self.mapa.set_rows(["." * self.mapa.w] * self.mapa.h)
        self.anchor = None
        self.tool = "S"

    def generate(self, seed=None):
        g = generate_map(self.mapa.w, self.mapa.h, seed)
        self._save_undo()
        self.mapa.set_rows(g.rows())
        self.mapa.seed = g.seed
        self.anchor = None
        self.tool = "#"
        return g.seed


# ================================================================ tutorial

def tutorial_spots(g):
    """Casas do Mago e do Arqueiro no tutorial: as que mais cobrem o começo da trilha."""
    early = g.path[:max(MIN_PATH, len(g.path) * 2 // 5)]
    free = [(x, y) for x, y in g.mapa.find(".")]

    def cover(c, r):
        return sum(1 for p in early if math.hypot(p[0] - c[0], p[1] - c[1]) <= r)
    mage = min(free, key=lambda c: (-cover(c, TOWERS["3"]["range"]), c[1], c[0]))
    archer = min((c for c in free if max(abs(c[0] - mage[0]), abs(c[1] - mage[1])) >= 2),
                 key=lambda c: (-cover(c, TOWERS["1"]["range"]), c[1], c[0]))
    return mage, archer


def tutorial_steps(g):
    mage, archer = tutorial_spots(g)
    return [
        {"text": "Os monstros saem da {spawn} e seguem a trilha até o {base}. Não deixe nenhum chegar lá!",
         "marks": [g.path[0], g.path[-1]], "wait": None},
        {"text": "Escolha o Mago: toque em {t3} na barra de torres (ou aperte 3).",
         "marks": [], "wait": lambda a: a.selected == "3"},
        {"text": "Toque na casa {mark} para pôr o cursor nela. Toque de novo para construir.",
         "marks": [mage], "wait": lambda a: mage in a.game.towers},
        {"text": "O verde claro é o alcance do Mago. Chame a onda: toque em ▶ Onda (ou n).",
         "marks": [], "wait": lambda a: a.game.wave >= 1},
        {"text": "Cada monstro derrotado dá {gold}. Se algum chegar ao {base}, você perde {life}. "
                 "Espere a onda acabar.",
         "marks": [], "wait": lambda a: a.game.wave >= 1 and not a.game.wave_active},
        {"text": "Agora o Arqueiro: toque em {t1} e construa na casa {mark}.",
         "marks": [archer], "wait": lambda a: archer in a.game.towers,
         "setup": lambda a: setattr(a.game, "gold", max(a.game.gold, 20))},
        {"text": "Toque 2 vezes no Mago (ou em {up}Melhorar). Nível maior = mais dano e alcance.",
         "marks": [mage], "wait": lambda a: a.game.towers.get(mage) and a.game.towers[mage].level >= 2,
         "setup": lambda a: setattr(a.game, "gold", max(a.game.gold, 24))},
        {"text": "{sell}Vender devolve metade. {fast} acelera. || no topo pausa. "
                 "{t4} Vórtice deixa os monstros lentos.",
         "marks": [], "wait": None},
        {"text": "Pronto {party} As ondas crescem, surgem monstros novos e a cada 5 vem o {boss}. "
                 "Crie os seus mapas em Mapas!",
         "marks": [], "wait": None},
    ]


# ================================================================ tela

def cell_width(ch):
    if unicodedata.combining(ch) or ch in "️‍":
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def text_width(s):
    return sum(cell_width(c) for c in s)


def clip(s, cells):
    out, used = [], 0
    for c in s:
        w = cell_width(c)
        if used + w > cells:
            break
        out.append(c)
        used += w
    return "".join(out)


def wrap(text, width):
    lines, cur = [], ""
    for word in text.split():
        cand = f"{cur} {word}" if cur else word
        if text_width(cand) <= width or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return [clip(ln, width) for ln in lines] or [""]


BASIC = {  # equivalente em 8 cores para terminais sem 256 cores
    16: 0, 22: 2, 25: 4, 28: 2, 31: 6, 34: 2, 39: 6, 45: 6, 46: 2, 51: 6, 52: 1, 64: 2, 65: 2, 70: 2,
    76: 2, 94: 3, 99: 5, 101: 7, 114: 2, 124: 1, 136: 3, 137: 3, 143: 3, 160: 1, 179: 3, 180: 3,
    196: 1, 201: 5, 208: 1, 214: 3, 220: 3, 226: 3, 229: 7, 231: 7, 234: 0, 235: 0, 236: 0, 237: 0,
    238: 0, 239: 0, 240: 0, 244: 7, 250: 7, 255: 7, -1: -1,
}


class Palette:
    def __init__(self):
        self.pairs = {}
        self.ok = curses.has_colors()
        self.full = False
        if self.ok:
            curses.start_color()
            try:
                curses.use_default_colors()
            except curses.error:
                pass
            self.full = curses.COLORS >= 256
        self.next_id = 1

    def __call__(self, fg=-1, bg=-1, bold=False):
        if not self.ok:
            return curses.A_BOLD if bold else 0
        if not self.full:
            fg, bg = BASIC.get(fg, 7), BASIC.get(bg, 0)
        key = (fg, bg)
        if key not in self.pairs:
            if self.next_id >= curses.COLOR_PAIRS:
                return curses.A_BOLD if bold else 0
            try:
                curses.init_pair(self.next_id, fg, bg)
            except curses.error:
                return 0
            self.pairs[key] = curses.color_pair(self.next_id)
            self.next_id += 1
        return self.pairs[key] | (curses.A_BOLD if bold else 0)


def put(win, y, x, text, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    text = clip(text, w - x)
    if text:
        try:
            win.addstr(y, x, text, attr)
        except curses.error:
            pass  # a última célula da tela gera erro, mas o texto é desenhado


class Layout:
    """Onde cada parte da tela cheia fica. Casa (x, y) ocupa 2k colunas por k linhas."""

    def __init__(self, k, top, left, mw, mh, panel_y, panel, bars_y, bar, w, h):
        self.k, self.top, self.left, self.mw, self.mh = k, top, left, mw, mh
        self.panel_y, self.panel, self.bars_y, self.bar, self.w, self.h = panel_y, panel, bars_y, bar, w, h

    def anchor(self, fx, fy):
        """Linha e coluna do emoji de algo na posição (fx, fy), que pode estar entre duas casas."""
        k = self.k
        return (self.top + int(math.floor(fy * k + 0.5)) + k // 2,
                self.left + int(math.floor(fx * 2 * k + 0.5)) + k - 1)

    def tile_at(self, row, col):
        if row < self.top or col < self.left:
            return None
        x, y = (col - self.left) // (2 * self.k), (row - self.top) // self.k
        return (x, y) if x < self.mw and y < self.mh else None


def compute_layout(h, w, mw, mh, panel=1):
    """Maior escala em que o mapa cabe com o topo (2 linhas), o painel e as 2 barras de botões."""
    avail = h - 2 - panel - 2
    if avail <= 0 or w < MIN_UI_W:
        return None
    k = min(MAX_K, w // (2 * mw), avail // mh)
    if k < 1:
        return None
    spare = avail - k * mh
    bar = 2 if spare >= 2 else 1
    bars_y = h - 2 * bar
    panel_y = bars_y - panel
    top = 2 + (panel_y - 2 - k * mh) // 2
    left = (w - 2 * k * mw) // 2
    return Layout(k, top, left, mw, mh, panel_y, panel, bars_y, bar, w, h)


def min_size(mw, mh, panel=1):
    return max(MIN_UI_W, 2 * mw), mh + 4 + panel


def texture(c, x, y, k):
    """Desenho de fundo de uma casa: k linhas de 2k caracteres."""
    n = 2 * k
    if k == 1:
        if c in ".T":
            return ["· " if (x * 7 + y * 13) % 6 == 0 else "  "]
        if c == "~":
            return ["~ " if (x + y) % 2 == 0 else " ~"]
        return ["  "]
    rows = []
    for r in range(k):
        s = []
        for i in range(n):
            gx, gy = x * n + i, y * k + r
            v = ((gx * 73856093) ^ (gy * 19349663)) & 1023
            if c in ".T":
                s.append("·" if v % 13 == 0 else ("'" if v % 31 == 7 else " "))
            elif c == "~":
                s.append("~" if (gx + 2 * gy) % 5 == 0 else " ")
            else:
                s.append(" ")
        rows.append("".join(s))
    return rows


MENU_ITEMS = [("play", "Jogar"), ("maps", "Mapas"), ("create", "Criar mapa"), ("tutorial", "Tutorial"),
              ("help", "Como jogar"), ("options", "Opções"), ("quit", "Sair")]
MENU_ICONS = {"play": "base", "maps": "maps", "create": "edit", "tutorial": "learn", "help": "help",
              "options": "opts", "quit": "exit"}


class App:
    def __init__(self, scr, emoji=None, touch=None, start=None, start_map=None):
        self.scr = scr
        self.version = read_version()
        self.cfg = load_config()
        self.emoji = self.cfg.get("emoji", True) if emoji is None else emoji
        self.touch = self.cfg.get("toque", True) if touch is None else touch
        self.pal = None
        self.screen = "menu"
        self.menu_i = 0 if self.cfg.get("tutorial_visto") else 3  # primeira vez: Tutorial selecionado
        self.opt_i = 0
        self.help_scroll = 0
        self.help_back = "menu"
        self.game = None
        self.from_editor = False
        self.tut = None
        self.tut_i = 0
        self.overlay = None
        self.new_record = False
        self.selected = "1"
        self.cursor = [0, 0]
        self.cursor_moved = False
        self.message, self.message_until = "", 0.0
        self.hits = []
        self.map_hit = None
        self.done = False
        self.anim = 0.0
        self.too_small = False
        self.maps, self.maps_i, self.maps_scroll = [], 0, 0
        self.ed = None
        self.utf8 = b""
        self._tiles_map, self._tiles_key, self._tiles = None, None, None
        self.mapa = find_map(self.cfg.get("mapa")) or builtin_maps()[0]
        self._init_curses()
        if start == "tutorial":
            self.start_game(tutorial=True)
        elif start == "play":
            self.start_game(start_map)
        elif start == "editor":
            self.open_editor(start_map or Mapa(["." * 11] * 19, next_map_name()), back="menu")

    def _init_curses(self):
        curses.curs_set(0)
        self.scr.keypad(True)
        self.pal = Palette()
        try:
            self.scr.bkgd(" ", self.pal(250, BG))
        except curses.error:
            pass
        self.apply_touch()

    def apply_touch(self):
        try:
            if self.touch:
                # RELEASED na máscara: um evento de soltar descartado pelo ncurses
                # deixa o getch() bloqueado até a próxima tecla, ignorando o timeout
                curses.mousemask(curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED | curses.BUTTON1_CLICKED)
                curses.mouseinterval(0)
            else:
                curses.mousemask(0)
        except curses.error:
            pass

    def g(self, name):
        return GLYPHS[name][0 if self.emoji else 1]

    def tower_glyph(self, key):
        return TOWERS[key]["emoji"] if self.emoji else TOWERS[key]["text"] + " "

    def enemy_glyph(self, kind):
        return ENEMIES[kind]["emoji"] if self.emoji else ENEMIES[kind]["text"] + " "

    def say(self, text, secs=2.0):
        self.message, self.message_until = text, time.monotonic() + secs

    def has_message(self):
        return bool(self.message) and time.monotonic() < self.message_until

    def record(self, mapa):
        return self.cfg.get("recordes", {}).get(mapa.key)

    # ------------------------------------------------------ janelas (pausa, fim, confirmações)
    def open_menu(self, kind, title, items, cancel=None):
        self.overlay = {"kind": kind, "title": title, "items": items, "i": 0, "cancel": cancel}

    def overlay_choose(self, i):
        action = self.overlay["items"][i][1]
        self.overlay = None
        action()

    def ask_name(self, title, text, on_ok):
        self.utf8 = b""
        self.overlay = {"kind": "name", "title": title, "text": text, "on_ok": on_ok, "error": ""}

    def name_ok(self):
        ov = self.overlay
        err = ov["on_ok"](ov["text"])
        if err and self.overlay is ov:
            ov["error"] = err

    # ------------------------------------------------------ partida
    def start_game(self, mapa=None, tutorial=False, from_editor=False):
        mapa = builtin_maps()[0] if tutorial else (mapa or self.mapa)
        _, err = mapa.check()
        if err:
            self.say(f"Mapa com erro: {err.msg}", 3)
            return False
        self.game = Game(mapa, tutorial=tutorial)
        self.from_editor = from_editor
        self.overlay = None
        self.new_record = False
        self.selected = "1"
        self.cursor = [mapa.w // 2, mapa.h // 2]
        self.cursor_moved = False
        self.message = ""
        self.screen = "game"
        self.tut = tutorial_steps(self.game) if tutorial else None
        self.tut_i = 0
        return True

    def restart_game(self):
        g = self.game
        self.start_game(g.mapa, g.tutorial, self.from_editor)

    def to_menu(self):
        self.overlay = None
        self.screen = "menu"
        self.game = None

    def tut_step(self):
        return self.tut[self.tut_i] if self.tut and self.tut_i < len(self.tut) else None

    def tut_advance(self):
        self.tut_i += 1
        step = self.tut_step()
        if step is None:
            self.cfg["tutorial_visto"] = True
            save_config(self.cfg)
            self.start_game()
            self.say("Boa sorte! Chame a onda quando quiser", 3)
        elif "setup" in step:
            step["setup"](self)

    def check_tutorial(self):
        step = self.tut_step()
        if step and step["wait"] and step["wait"](self):
            self.tut_advance()

    def finish_game(self):
        g = self.game
        self.new_record = False
        if not g.tutorial and not self.from_editor:
            recs = self.cfg.setdefault("recordes", {})
            rec = recs.get(g.mapa.key, {"onda": 0, "abates": 0})
            if (g.wave, g.kills) > (rec.get("onda", 0), rec.get("abates", 0)):
                recs[g.mapa.key] = {"onda": g.wave, "abates": g.kills, "mapa": g.mapa.name}
                save_config(self.cfg)
                self.new_record = True
        title = [f"{self.enemy_glyph('chefe')} A BASE CAIU!", f"Onda {g.wave} · {g.kills} abates"]
        if self.new_record:
            title.append(f"{self.g('trophy')} Novo recorde em {g.mapa.name}!")
        items = [("Jogar de novo", self.restart_game)]
        if self.from_editor:
            items.append(("Voltar ao editor", self.back_to_editor))
        else:
            items += [("Trocar de mapa", self.open_maps), ("Menu principal", self.to_menu)]
        self.open_menu("over", title, items, cancel=lambda: None)

    def open_pause(self):
        g = self.game
        items = [("Continuar", lambda: None), ("Reiniciar partida", self.restart_game),
                 ("Como jogar", lambda: self.open_help("game"))]
        if self.from_editor:
            items.append(("Voltar ao editor", self.back_to_editor))
        else:
            items.append(("Menu principal", self.to_menu))
        self.open_menu("pause", ["PAUSA", f"Mapa: {g.mapa.name}"], items, cancel=lambda: None)

    def act_on_cursor(self):
        g = self.game
        x, y = self.cursor
        if (x, y) in g.towers:
            ok, msg = g.upgrade(x, y)
        else:
            ok, msg = g.build(x, y, self.selected)
        self.say(msg)

    def tap_cell(self, x, y):
        if [x, y] == self.cursor and self.cursor_moved:
            self.act_on_cursor()
        else:
            self.cursor = [x, y]
            self.cursor_moved = True

    def move_cursor(self, cursor, w, h, k, ch):
        dx = (k == curses.KEY_RIGHT or ch in ("d", "D")) - (k == curses.KEY_LEFT or ch in ("a", "A"))
        dy = (k == curses.KEY_DOWN or ch in ("s", "S")) - (k == curses.KEY_UP or ch in ("w", "W"))
        cursor[0] = min(w - 1, max(0, cursor[0] + dx))
        cursor[1] = min(h - 1, max(0, cursor[1] + dy))

    def call_wave(self):
        g = self.game
        if g.tutorial and self.tut_step() and self.tut_i < 3:
            self.say("Siga o tutorial primeiro")
            return
        ok, msg = g.next_wave()
        if msg:
            self.say(msg, 1.5)

    def toggle_speed(self):
        g = self.game
        g.speed = 2 if g.speed == 1 else 1
        self.say(f"Velocidade {g.speed}x", 1.2)

    def do_upgrade(self):
        if tuple(self.cursor) not in self.game.towers:
            self.say("Toque numa torre primeiro")
            return
        self.say(self.game.upgrade(*self.cursor)[1])

    def do_sell(self):
        if tuple(self.cursor) not in self.game.towers:
            self.say("Toque numa torre primeiro")
            return
        self.say(self.game.sell(*self.cursor)[1])

    # ------------------------------------------------------ mapas
    def open_maps(self):
        self.overlay = None
        self.game = None
        self.maps = builtin_maps() + user_maps()
        ref = map_ref(self.mapa)
        self.maps_i = next((i for i, m in enumerate(self.maps) if map_ref(m) == ref), 0)
        self.screen = "maps"

    def maps_sel(self):
        return self.maps[self.maps_i] if self.maps else None

    def maps_play(self):
        m = self.maps_sel()
        _, err = m.check()
        if err:
            self.say(f"Ainda não dá para jogar: {err.msg}", 3)
            return
        self.mapa = m
        self.cfg["mapa"] = map_ref(m)
        save_config(self.cfg)
        self.start_game(m)

    def maps_edit(self):
        m = self.maps_sel()
        if m.builtin:
            self.open_editor(m.copy(f"{m.name} (cópia)"), back="maps", dirty=True)
            self.say("Mapa pronto: você edita uma cópia", 2.5)
        else:
            self.open_editor(m.copy(), back="maps")

    def maps_new(self):
        self.open_editor(Mapa(["." * 11] * 19, next_map_name()), back="maps")
        self.say("Comece pela entrada: toque numa casa", 3)

    def maps_generate(self):
        m = generate_map(11, 19)
        m.name = next_map_name("Aleatório")
        self.open_editor(m, back="maps", dirty=True)
        self.say(f"Mapa gerado (semente {m.seed}). Teste ou salve!", 3)

    def maps_delete(self):
        m = self.maps_sel()
        if m.builtin:
            self.say("Mapas prontos não podem ser apagados")
            return

        def delete():
            try:
                os.remove(m.file)
            except OSError as e:
                self.say(f"Não consegui apagar: {e.strerror}")
                return
            if map_ref(self.mapa) == map_ref(m):
                self.mapa = builtin_maps()[0]
                self.cfg["mapa"] = map_ref(self.mapa)
                save_config(self.cfg)
            self.open_maps()
            self.say(f"{m.name} apagado")
        self.open_menu("confirm", [f"Apagar {m.name}?", "Não tem como desfazer."],
                       [("Apagar", delete), ("Cancelar", lambda: None)], cancel=lambda: None)

    def maps_tap(self, i):
        if i == self.maps_i:
            self.maps_play()
        else:
            self.maps_i = i

    # ------------------------------------------------------ editor
    def open_editor(self, mapa, back="menu", dirty=False):
        self.ed = Editor(mapa, back, dirty)
        self.game = None
        self.overlay = None
        self.screen = "editor"

    def ed_tap(self, x, y):
        ed = self.ed
        ed.cursor, ed.kbd = [x, y], False
        msg = ed.paint(x, y)
        if msg:
            self.say(msg, 2.5)

    def ed_tool(self, tool):
        self.ed.tool = tool
        self.say(Editor.HINTS[tool], 2.5)

    def ed_undo(self):
        self.say("Desfeito" if self.ed.undo() else "Nada para desfazer", 1.2)

    def ed_generate(self):
        seed = self.ed.generate()
        self.say(f"Mapa gerado (semente {seed}). Toque de novo para outro", 2.5)

    def ed_test(self):
        _, err = self.ed.mapa.check()
        if err:
            self.say(f"Ainda não dá para jogar: {err.msg}", 3)
            return
        self.start_game(self.ed.mapa.copy(), from_editor=True)
        self.say("Teste: || no topo volta ao editor", 3)

    def back_to_editor(self):
        self.game = None
        self.overlay = None
        self.from_editor = False
        self.screen = "editor"

    def ed_save(self, after=None, rename=False):
        m = self.ed.mapa
        if m.file is None or rename:
            self.ask_name("Nome do mapa", m.name, lambda name: self.ed_do_save(name, after))
        else:
            self.ed_do_save(m.name, after)

    def ed_do_save(self, name, after=None):
        m = self.ed.mapa
        try:
            save_user_map(m, name, m.file)
        except MapError as e:
            if not (self.overlay and self.overlay["kind"] == "name"):
                self.say(e.msg, 3)
            return e.msg
        if self.overlay and self.overlay["kind"] == "name":
            self.overlay = None
        self.ed.dirty = False
        _, err = m.check()
        self.say(f"Salvo: {m.name}" + ("" if not err else " (ainda com erro na trilha)"), 2.5)
        if after:
            after()
        return None

    def ed_exit(self):
        if self.ed.dirty:
            self.open_menu("confirm", ["Sair sem salvar?", "As mudanças serão perdidas."],
                           [("Salvar e sair", lambda: self.ed_save(self.ed_leave)),
                            ("Sair sem salvar", self.ed_leave), ("Continuar editando", lambda: None)],
                           cancel=lambda: None)
        else:
            self.ed_leave()

    def ed_leave(self):
        back = self.ed.back
        self.ed = None
        self.overlay = None
        if back == "maps":
            self.open_maps()
        else:
            self.screen = "menu"

    def ed_menu(self):
        m = self.ed.mapa
        sizes = MAP_SIZES
        cur = (m.w, m.h)
        nw, nh = sizes[(sizes.index(cur) + 1) % len(sizes)] if cur in sizes else sizes[1]

        def resize():
            self.ed.resize(nw, nh)
            self.say(f"Tamanho {nw}×{nh} (desfazer volta)", 2.5)

        def clear():
            self.ed.clear()
            self.say("Mapa limpo (desfazer volta)", 2)
        items = [("Continuar editando", lambda: None), ("Salvar", self.ed_save),
                 ("Renomear", lambda: self.ed_save(rename=True)),
                 (f"Tamanho {m.w}×{m.h} → {nw}×{nh}", resize), ("Limpar tudo", clear),
                 ("Como editar", lambda: self.open_help("editor")), ("Sair do editor", self.ed_exit)]
        self.open_menu("ed_menu", ["EDITOR", m.name], items, cancel=lambda: None)

    def open_help(self, back):
        self.help_back = back
        self.help_scroll = 0
        self.screen = "help"

    # ------------------------------------------------------ entrada
    def on_key(self, k):
        if k == curses.KEY_RESIZE:
            return
        if k == curses.KEY_MOUSE:
            self.on_mouse()
            return
        ch = chr(k) if 0 <= k < 256 else ""
        if self.overlay and self.overlay["kind"] == "name":
            self.key_name(k, ch)
            return
        if self.too_small:
            if ch in ("q", "Q"):
                self.done = True
            return
        if self.overlay:
            self.key_overlay(k, ch)
            return
        getattr(self, "key_" + self.screen)(k, ch)

    def _nav(self, k, ch, i, n):
        if k == curses.KEY_UP or ch in ("w", "W", "k"):
            return (i - 1) % n
        if k == curses.KEY_DOWN or ch in ("s", "S", "j"):
            return (i + 1) % n
        return i

    @staticmethod
    def is_enter(k, ch):
        return k in (10, 13, curses.KEY_ENTER) or ch == " "

    def key_menu(self, k, ch):
        self.menu_i = self._nav(k, ch, self.menu_i, len(MENU_ITEMS))
        if self.is_enter(k, ch):
            self.menu_choose(self.menu_i)
        elif ch in ("q", "Q") or k == 27:
            self.done = True

    def menu_choose(self, i):
        action = MENU_ITEMS[i][0]
        if action == "play":
            self.start_game()
        elif action == "maps":
            self.open_maps()
        elif action == "create":
            self.open_editor(Mapa(["." * 11] * 19, next_map_name()), back="menu")
            self.say("Comece pela entrada: toque numa casa", 3)
        elif action == "tutorial":
            self.start_game(tutorial=True)
        elif action == "help":
            self.open_help("menu")
        elif action == "options":
            self.screen, self.opt_i = "options", 0
        else:
            self.done = True

    def options(self):
        n = len(self.cfg.get("recordes", {}))
        return [
            ("emoji", f"Emojis: {'SIM' if self.emoji else 'NÃO (letras)'}"),
            ("touch", f"Toque na tela: {'SIM' if self.touch else 'NÃO'}"),
            ("reset", "Zerar recordes" + (f" ({n})" if n else "")),
            ("back", "Voltar"),
        ]

    def key_options(self, k, ch):
        opts = self.options()
        self.opt_i = self._nav(k, ch, self.opt_i, len(opts))
        if self.is_enter(k, ch):
            self.option_choose(self.opt_i)
        elif ch in ("q", "Q") or k in (27, curses.KEY_BACKSPACE, 127):
            self.screen = "menu"

    def option_choose(self, i):
        action = self.options()[i][0]
        if action == "emoji":
            self.emoji = not self.emoji
            self.cfg["emoji"] = self.emoji
        elif action == "touch":
            self.touch = not self.touch
            self.cfg["toque"] = self.touch
            self.apply_touch()
        elif action == "reset":
            self.cfg.pop("recordes", None)
            self.cfg.pop("recorde", None)
            self.say("Recordes zerados")
        else:
            self.screen = "menu"
            return
        save_config(self.cfg)

    def key_help(self, k, ch):
        if k == curses.KEY_DOWN or ch in ("s", "j"):
            self.help_scroll += 1
        elif k == curses.KEY_UP or ch in ("w", "k"):
            self.help_scroll = max(0, self.help_scroll - 1)
        elif k == curses.KEY_NPAGE:
            self.help_scroll += 10
        elif k == curses.KEY_PPAGE:
            self.help_scroll = max(0, self.help_scroll - 10)
        else:
            self.help_leave()

    def help_leave(self):
        self.screen = self.help_back
        if self.help_back == "game" and self.game:
            self.open_pause()  # a partida continua parada até o jogador tocar em Continuar

    def key_game(self, k, ch):
        g = self.game
        step = self.tut_step()
        if step and step["wait"] is None and self.is_enter(k, ch):
            self.tut_advance()
            return
        if ch in ("q", "Q", "p", "P") or k == 27:
            self.open_pause()
        elif ch in ("h", "H", "?"):
            self.open_help("game")
        elif ch in ("1", "2", "3", "4"):
            self.selected = ch
        elif k in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT) or (ch and ch in "wWaAsSdD"):
            self.move_cursor(self.cursor, g.w, g.h, k, ch)
            self.cursor_moved = True
        elif self.is_enter(k, ch):
            self.act_on_cursor()
        elif ch in ("u", "U"):
            self.do_upgrade()
        elif ch in ("x", "X"):
            self.do_sell()
        elif ch in ("n", "N"):
            self.call_wave()
        elif ch in ("f", "F"):
            self.toggle_speed()

    def key_maps(self, k, ch):
        if self.maps:
            self.maps_i = self._nav(k, ch, self.maps_i, len(self.maps))
        if self.is_enter(k, ch) and self.maps:
            self.maps_play()
        elif ch in ("e", "E") and self.maps:
            self.maps_edit()
        elif ch in ("n", "N"):
            self.maps_new()
        elif ch in ("g", "G"):
            self.maps_generate()
        elif (ch in ("x", "X") or k == curses.KEY_DC) and self.maps:
            self.maps_delete()
        elif ch in ("q", "Q") or k in (27, curses.KEY_BACKSPACE, 127):
            self.screen = "menu"

    def key_editor(self, k, ch):
        ed = self.ed
        m = ed.mapa
        if k in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT) or (ch and ch in "wWaAsSdD"):
            self.move_cursor(ed.cursor, m.w, m.h, k, ch)
            ed.kbd = True
        elif self.is_enter(k, ch):
            ed.kbd = True
            msg = ed.paint(*ed.cursor)
            if msg:
                self.say(msg, 2.5)
        elif ch and ch in "123456":
            self.ed_tool(Editor.TOOLS[int(ch) - 1])
        elif ch in ("u", "U", "z", "Z"):
            self.ed_undo()
        elif ch in ("g", "G"):
            self.ed_generate()
        elif ch in ("t", "T"):
            self.ed_test()
        elif ch in ("v", "V"):  # salvar (s já move o cursor)
            self.ed_save()
        elif ch in ("h", "H", "?"):
            self.open_help("editor")
        elif ch in ("q", "Q", "p", "P") or k == 27:
            self.ed_menu()

    def key_overlay(self, k, ch):
        ov = self.overlay
        n = len(ov["items"])
        ov["i"] = self._nav(k, ch, ov["i"], n)
        if self.is_enter(k, ch):
            self.overlay_choose(ov["i"])
        elif k == 27 or (ch in ("p", "P") and ov["kind"] == "pause"):
            self.overlay = None
            if ov["cancel"]:
                ov["cancel"]()
        elif ch in ("q", "Q"):
            self.overlay_choose(n - 1)

    def key_name(self, k, ch):
        ov = self.overlay
        if k in (10, 13, curses.KEY_ENTER):
            self.name_ok()
        elif k == 27:
            self.overlay = None
        elif k in (curses.KEY_BACKSPACE, 127, 8):
            ov["text"] = ov["text"][:-1]
            self.utf8 = b""
        elif 32 <= k < 127:
            self._name_add(chr(k))
        elif 128 <= k < 256:  # o curses entrega letras acentuadas byte a byte (UTF-8)
            self.utf8 += bytes([k])
            try:
                c = self.utf8.decode("utf-8")
            except UnicodeDecodeError:
                if len(self.utf8) >= 4:
                    self.utf8 = b""
                return
            self.utf8 = b""
            self._name_add(c)

    def _name_add(self, c):
        ov = self.overlay
        if (c.isalnum() or c in " -_") and len(ov["text"]) < 24:
            ov["text"] += c
            ov["error"] = ""

    def on_mouse(self):
        try:
            _, mx, my, _, bstate = curses.getmouse()
        except curses.error:
            return
        if not bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
            return
        if self.too_small and not (self.overlay and self.overlay["kind"] == "name"):
            return
        for (y0, x0, y1, x1, action) in reversed(self.hits):
            if y0 <= my <= y1 and x0 <= mx <= x1:
                action()
                return
        if self.map_hit:
            layout, fn = self.map_hit
            tile = layout.tile_at(my, mx)
            if tile:
                fn(*tile)

    # ------------------------------------------------------ desenho: peças
    def busy(self):
        if self.has_message():
            return True
        g = self.game
        if self.screen == "game" and g and not self.overlay:
            return g.wave_active or bool(g.enemies) or bool(g.effects) or self.tut_step() is not None
        return False

    def render(self):
        scr = self.scr
        scr.erase()
        self.hits = []
        self.map_hit = None
        self.too_small = False
        h, w = scr.getmaxyx()
        if w < MIN_UI_W or h < 12:
            self.draw_small(h, w, MIN_UI_W, 12)
        else:
            getattr(self, "draw_" + self.screen)(h, w)
        if self.overlay and (not self.too_small or self.overlay["kind"] == "name"):
            self.hits = []  # com a janela aberta, só os botões dela respondem ao toque
            self.map_hit = None
            if self.overlay["kind"] == "name":
                self.draw_name(h, w)
            else:
                self.draw_overlay(h, w)
        scr.refresh()

    def draw_small(self, h, w, need_w, need_h):
        self.too_small = True
        lines = ["Tela pequena demais", f"atual {w}x{h}", f"mínimo {need_w}x{need_h}",
                 "Esconda o teclado ou", "diminua a fonte (pinça)", "q sai"]
        for i, line in enumerate(lines):
            put(self.scr, i, 0, line, curses.A_BOLD if i == 0 else 0)

    def center(self, y, text, attr=0, w=None, x0=0):
        w = w or self.scr.getmaxyx()[1]
        x = x0 + max(0, (w - text_width(text)) // 2)
        put(self.scr, y, x, text, attr)
        return x

    def block(self, y, x, width, height, lines, attr, action=None):
        """Botão retangular com as linhas de texto centralizadas."""
        for r in range(height):
            put(self.scr, y + r, x, " " * width, attr)
        n = min(len(lines), height)
        y0 = y + (height - n) // 2
        for i in range(n):
            t = clip(lines[i], width)
            put(self.scr, y0 + i, x + max(0, (width - text_width(t)) // 2), t, attr)
        if action:
            self.hits.append((y, x, y + height - 1, x + width - 1, action))

    def bar_row(self, y, text, attr, w):
        put(self.scr, y, 0, clip(text + " " * w, w), attr)

    def row_buttons(self, y, height, w, buttons):
        """Barra de botões iguais na largura toda: buttons = [(linhas, attr, ação)]."""
        n = len(buttons)
        for i, (lines, attr, action) in enumerate(buttons):
            x0, x1 = w * i // n, w * (i + 1) // n
            self.block(y, x0, x1 - x0, height, lines if height > 1 else lines[:1], attr, action)

    def top_bar(self, w, text, action, label="||", whole_row=True):
        P = self.pal
        attr = P(255, 235, True)
        self.bar_row(0, text, attr, w)
        if whole_row:
            self.hits.append((0, 0, 0, w - 1, action))
        bw = text_width(label) + 4
        self.block(0, w - bw, bw, 1, [label], P(16, 220, True), action)

    # ------------------------------------------------------ desenho: tabuleiro
    def static_tiles(self, mapa, k):
        key = (mapa.version, k, self.emoji)
        if self._tiles_map is mapa and self._tiles_key == key:  # guarda o objeto: id() pode ser reusado
            return self._tiles
        tiles = {}
        grid = mapa.grid
        for y in range(mapa.h):
            for x in range(mapa.w):
                c = grid[y][x]
                glyph, fg, texfg, bg = None, -1, 34, 28
                tex = texture(c, x, y, k)
                if c in WALK:
                    bg = 137
                    left = x > 0 and grid[y][x - 1] == "~"
                    right = x < mapa.w - 1 and grid[y][x + 1] == "~"
                    up = y > 0 and grid[y - 1][x] == "~"
                    down = y < mapa.h - 1 and grid[y + 1][x] == "~"
                    if c == "#" and left and right:
                        bg, texfg, tex = 94, 180, ["═" * 2 * k] * k   # ponte: travessia em pé
                    elif c == "#" and up and down:
                        bg, texfg, tex = 94, 180, ["│" * 2 * k] * k   # ponte: travessia deitada
                    if c == "S":
                        glyph, fg = self.g("spawn"), 255
                    elif c == "B":
                        glyph, fg = self.g("base"), 255
                elif c == "~":
                    bg, texfg = 25, 45
                elif c == "T":
                    glyph, fg = self.g("tree"), 34
                tiles[(x, y)] = (bg, glyph, fg, tex, texfg)
        self._tiles_map, self._tiles_key, self._tiles = mapa, key, tiles
        return tiles

    def draw_tiles(self, L, mapa, towers=None, in_range=(), cursor=None, marks=(), alert=None,
                   anchor=None, base_flash=False, spawn_flash=False):
        P, k = self.pal, L.k
        add = self.scr.addstr
        blink = int(time.monotonic() * 3) % 2 == 0
        towers = towers or {}
        tiles = self.static_tiles(mapa, k)
        ar = k // 2
        blank = {k: [" " * 2 * k] * k}
        for (x, y), (bg, glyph, fg, tex, texfg) in tiles.items():
            pos = (x, y)
            if pos in in_range:
                bg = RANGE_BG.get(bg, bg)
            top_text = None
            t = towers.get(pos)
            if t is not None:
                glyph, fg, bg = self.tower_glyph(t.key), TEXT_COLORS[t.key], LEVEL_BG[t.level]
                if k >= 2 and t.level > 1:
                    top_text = "★" * (t.level - 1)
            c = mapa.grid[y][x]
            if (base_flash and c == "B") or (spawn_flash and c == "S"):
                bg = 196 if c == "B" else 99
            if pos == anchor:
                bg = 208
            if pos == alert:
                bg = 196
            if pos in marks and blink:
                bg = 226
                if glyph is None:
                    glyph = self.g("mark")
            is_cursor = cursor is not None and pos == tuple(cursor)
            if is_cursor:
                bg = 226 if not self.emoji or glyph else 220
            if (is_cursor and c in ".~") or t is not None:
                tex = blank[k]
            row0, col0 = L.top + y * k, L.left + x * 2 * k
            attr = P(texfg, bg)
            for r in range(k):
                try:
                    add(row0 + r, col0, tex[r], attr)
                except curses.error:
                    pass
            if glyph:
                gattr = P(16 if is_cursor and not self.emoji else (fg if not self.emoji else -1), bg, True)
                try:
                    add(row0 + ar, col0 + k - 1, glyph, gattr)
                except curses.error:
                    pass
            if top_text:
                try:
                    add(row0 + ar - 1, col0 + (2 * k - len(top_text)) // 2, top_text, P(226, bg, True))
                except curses.error:
                    pass

    def tile_bg(self, mapa, x, y, in_range):
        xi, yi = int(x + 0.5), int(y + 0.5)
        if not mapa.inside(xi, yi):
            return 137
        c = mapa.grid[yi][xi]
        bg = 137 if c in WALK else (25 if c == "~" else 28)
        return RANGE_BG.get(bg, bg) if (xi, yi) in in_range else bg

    def draw_sprites(self, L, g, in_range):
        P, k = self.pal, L.k
        add = self.scr.addstr
        now = g.time
        for e in sorted(g.enemies, key=lambda e: e.progress):
            if not e.alive:
                continue
            fx, fy = g.enemy_pos(e)
            row, col = L.anchor(fx, fy)
            ratio = max(0.0, e.hp / e.max_hp)
            hidden = e.hidden(now)
            bg = self.tile_bg(g.mapa, fx, fy, in_range)
            if now < e.hit_until:
                bg = 231
            elif k == 1 and ratio < 0.35:
                bg = 196
            elif k == 1 and ratio < 0.7:
                bg = 208
            elif now < e.slow_until:
                bg = 45
            if hidden:
                glyph, attr = ("░░" if self.emoji else "::"), P(250, bg)
            else:
                glyph = self.enemy_glyph(e.kind)
                fg = TEXT_COLORS[e.kind]
                if not self.emoji and bg in (196, 208, 231, 45):
                    fg = 16
                attr = P(fg if not self.emoji else -1, bg, True)
            try:
                add(row, col, glyph, attr)
            except curses.error:
                pass
            if k >= 2 and not hidden and (ratio < 1 or e.kind == "chefe"):
                n = max(1, int(ratio * 16 + 0.5))
                bar = EIGHTHS[min(8, n)] + EIGHTHS[max(0, n - 8)]
                color = 46 if ratio > 0.6 else (226 if ratio > 0.3 else 196)
                try:
                    add(row - 1, col, bar, P(color, 236))
                except curses.error:
                    pass
        for kind, x, y, t0, t1, text in g.effects:
            if now < t0:
                continue
            row, col = L.anchor(x, y)
            if kind == "kill":
                put(self.scr, row, col, self.g("kill"), P(226, self.tile_bg(g.mapa, x, y, in_range), True))
            elif kind == "summon":
                put(self.scr, row, col, self.g("summon"), P(226, self.tile_bg(g.mapa, x, y, in_range), True))
            elif kind == "gold":
                rise = int((now - t0) / (t1 - t0) * k) + (1 if k >= 2 else 0)
                put(self.scr, row - rise, col, text, P(226, 236, True))
            elif kind == "leak" and k >= 2:
                put(self.scr, row - 1, col, text, P(231, 196, True))

    # ------------------------------------------------------ desenho: telas
    def draw_menu(self, h, w):
        P = self.pal
        n = len(MENU_ITEMS)
        avail = h - 10
        ih = 2 if avail >= n * 3 - 1 else 1
        gap = 1 if avail >= n * (ih + 1) - 1 else 0
        top = max(0, (h - 1 - (7 + n * (ih + gap) - gap)) // 2)  # bloco centralizado na altura
        self.center(top + 1, f"{self.g('base')}  TOWER DEFENSE  {self.g('base')}", P(220, BG, True))
        self.center(top + 2, "edição Termux", P(244, BG))
        self.draw_strip(top + 4, w)
        items_y = top + 8
        bw = min(w - 4, 44)
        x0 = (w - bw) // 2
        seen = self.cfg.get("tutorial_visto")
        rec = self.record(self.mapa)
        subs = {
            "play": f"mapa {self.mapa.name}" + (f" · {self.g('trophy')} onda {rec['onda']}" if rec else ""),
            "maps": "escolher, gerar e editar", "create": "desenhe a sua trilha",
            "tutorial": "comece aqui" if not seen else "aprenda em 2 minutos",
            "help": "torres, monstros e teclas", "options": "emojis, toque, recordes", "quit": "",
        }
        for i, (action, label) in enumerate(MENU_ITEMS):
            y = items_y + i * (ih + gap)
            if y + ih > h - 1:
                break
            sel = i == self.menu_i
            attr = P(16, 220, True) if sel else P(255, 237)
            self.block(y, x0, bw, ih, [], attr, lambda i=i: self.menu_choose(i))
            head = f"{'▶' if sel else ' '} {self.g(MENU_ICONS[action])} {label}"
            sub = subs[action]
            if ih == 1:
                if sub and text_width(head) + text_width(sub) + 5 <= bw:
                    head += "  · " + sub
                put(self.scr, y, x0 + 1, clip(head, bw - 2), attr)
            else:
                put(self.scr, y, x0 + 1, clip(head, bw - 2), attr)
                if sub:
                    put(self.scr, y + 1, x0 + 6, clip(sub, bw - 7), P(16 if sel else 250, 220 if sel else 237))
        self.center(h - 1, f"v{self.version}  ·  toque ou setas + Enter", P(244, BG))

    def draw_strip(self, y, w):
        """Faixa animada do menu: monstros andando pela trilha, torres na grama."""
        P = self.pal
        for r, bg in ((0, 28), (1, 137), (2, 28)):
            line = "".join("·" if bg == 28 and (i * 7 + r * 5) % 9 == 0 else " " for i in range(w))
            put(self.scr, y + r, 0, line, P(34, bg))
        put(self.scr, y, (w // 3) & ~1, self.tower_glyph("3"), P(TEXT_COLORS["3"], 28, True))
        put(self.scr, y + 2, (2 * w // 3) & ~1, self.tower_glyph("1"), P(TEXT_COLORS["1"], 28, True))
        span = w + 30
        for i, kind in enumerate(("normal", "rapido", "tartaruga", "morcego", "chefe")):
            col = int(self.anim * 4 + i * (span // 5)) % span - 4
            if 0 <= col <= w - 2:
                put(self.scr, y + 1, col, self.enemy_glyph(kind), P(TEXT_COLORS[kind], 137, True))

    def help_lines(self, w):
        t, e = self.tower_glyph, self.enemy_glyph
        blocks = [
            ("h", "COMO JOGAR"),
            ("", f"Os monstros saem da {self.g('spawn')} e seguem a trilha até o {self.g('base')}. "
                 "Construa torres na grama para derrotá-los. Cada monstro derrotado dá ouro; "
                 "cada um que chega tira vida."),
            ("h", "TORRES"),
        ]
        for k, c in TOWERS.items():
            blocks.append(("", f"{k} {t(k)} {c['name']} · {c['cost']} ouro · {c['info']}"))
        blocks += [("", "Melhore até o nível 3 (mais dano e alcance). Vender devolve metade do gasto."),
                   ("h", "MONSTROS")]
        for kind, c in ENEMIES.items():
            when = "" if kind == "chefe" else f" (onda {c['wave']})"
            blocks.append(("", f"{e(kind)} {c['name']}{when}: {c['info']}"))
        blocks += [
            ("h", "TOQUE"),
            ("", "Casa: põe o cursor; tocar de novo constrói ou melhora."),
            ("", f"Barra de torres escolhe a torre. ▶ Onda chama a onda. {self.g('up')}Melhorar e "
                 f"{self.g('sell')}Vender agem na torre do cursor. || no topo pausa."),
            ("h", "TECLAS"),
            ("", "setas ou wasd move · Enter constrói · 1-4 torre · u melhora · x vende · "
                 "n onda · f acelera · p pausa · h ajuda"),
            ("h", "CRIAR MAPAS"),
            ("", f"Menu → Criar mapa (ou Mapas → {self.g('new')}Novo). Ferramentas: 1 Entrada, 2 Trilha, "
                 "3 Base, 4 Grama (apaga), 5 Árvore, 6 Água."),
            ("", "Trilha: toque nos cantos, a reta entre eles é preenchida. Tocar numa trilha "
                 "existente continua dela. A entrada já liga a ferramenta Trilha."),
            ("", "A trilha não pode se dividir nem encostar nela mesma: deixe uma casa de grama "
                 "entre as voltas. A linha de cima diz o que falta e a casa com problema fica vermelha."),
            ("", f"{self.g('dice')}Gerar cria um mapa aleatório. ▶ Testar joga na hora. "
                 f"{self.g('save')}Salvar guarda em ~/.config/td-termux/mapas."),
            ("", "Teclas do editor: setas movem, Enter pinta, 1-6 ferramenta, u desfaz, g gera, "
                 "t testa, v salva, q menu."),
            ("h", "ARQUIVO .mapa"),
            ("", "Texto simples, uma linha por fileira: . grama  # trilha  S entrada  B base  "
                 "T árvore  ~ água. Linhas com ':' são informações (nome: Meu mapa)."),
            ("", "td --gerar 11x19 > novo.mapa · td --validar novo.mapa · td --importar novo.mapa"),
            ("", ""),
            ("", "Toque ou qualquer tecla volta"),
        ]
        lines = []
        for style, text in blocks:
            if style == "h":
                lines += [("", False), (text, True)]
            else:
                lines += [(ln, False) for ln in wrap(text, w - 2)] if text else [("", False)]
        return lines[1:]

    def draw_help(self, h, w):
        lines = self.help_lines(w)
        self.help_scroll = min(self.help_scroll, max(0, len(lines) - h + 1))
        P = self.pal
        for i, (text, strong) in enumerate(lines[self.help_scroll:self.help_scroll + h - 1]):
            put(self.scr, i, 1, text, P(220, BG, True) if strong else P(255, BG))
        if len(lines) > h - 1:
            put(self.scr, h - 1, 1, "↑↓ rola · outra tecla volta", P(244, BG))
        self.hits.append((0, 0, h - 1, w - 1, self.help_leave))

    def draw_options(self, h, w):
        P = self.pal
        self.center(1, "OPÇÕES", P(220, BG, True))
        bw = min(w - 4, 44)
        x0 = (w - bw) // 2
        for i, (action, label) in enumerate(self.options()):
            y = 3 + i * 3
            sel = i == self.opt_i
            attr = P(16, 220, True) if sel else P(255, 237)
            self.block(y, x0, bw, 2, [], attr, lambda i=i: self.option_choose(i))
            put(self.scr, y, x0 + 1, ("▶ " if sel else "  ") + label, attr)
        y = 3 + len(self.options()) * 3
        for ln in wrap("Use NÃO em Emojis se as figuras aparecerem desalinhadas no mapa.", bw):
            put(self.scr, y, x0, ln, P(244, BG))
            y += 1
        put(self.scr, y + 1, x0, clip("Seus mapas: ~/.config/td-termux/mapas", bw), P(244, BG))
        if self.has_message():
            put(self.scr, y + 3, x0, self.message, P(114, BG, True))

    def range_cells(self):
        g = self.game
        cx, cy = self.cursor
        t = g.towers.get((cx, cy))
        if t is None and not self.cursor_moved:
            return set()
        r = t.range if t else (TOWERS[self.selected]["range"] if g.can_build(cx, cy) else 0)
        if not r:
            return set()
        return {(x, y) for x in range(g.w) for y in range(g.h) if (x - cx) ** 2 + (y - cy) ** 2 <= r * r}

    def tut_lines(self, step, w):
        return wrap(step["text"].format(
            spawn=self.g("spawn"), base=self.g("base"), mark=self.g("mark"), gold=self.g("gold"),
            life=self.g("life"), fast=self.g("fast"), party=self.g("party"), up=self.g("up"),
            sell=self.g("sell"), boss=self.enemy_glyph("chefe"), t1=self.tower_glyph("1"),
            t3=self.tower_glyph("3"), t4=self.tower_glyph("4")), w - 2)

    def draw_game(self, h, w):
        g, P = self.game, self.pal
        panel = 1
        if self.tut:
            panel = 2 + max(len(self.tut_lines(s, w)) for s in self.tut)
        L = compute_layout(h, w, g.w, g.h, panel)
        if L is None:
            self.draw_small(h, w, *min_size(g.w, g.h, panel))
            return
        # topo: placar (tocar pausa)
        hud = (f" {self.g('life')}{g.life}  {self.g('gold')}{g.gold}  {self.g('wave')}{g.wave}"
               f"  {self.g('kills')}{g.kills}")
        if g.speed == 2:
            hud += f"  {self.g('fast')}"
        self.top_bar(w, hud, self.open_pause)
        # linha 2: onda atual ou a próxima
        if g.wave_active or g.enemies:
            text = f" Onda {g.wave}: faltam {len(g.queue) + len(g.enemies)}"
            if any(e.kind == "chefe" for e in g.enemies):
                text += f" · chefe {self.enemy_glyph('chefe')}"
            self.bar_row(1, text, P(229, 236, True), w)
        else:
            self.bar_row(1, f" Próxima onda {g.wave + 1}: {self.wave_preview(g.next_queue)}", P(250, 236), w)
        # mapa
        in_range = self.range_cells()
        step = self.tut_step()
        self.draw_tiles(L, g.mapa, g.towers, in_range, self.cursor, set(step["marks"]) if step else (),
                        base_flash=g.time < g.leak_until, spawn_flash=g.time < g.spawn_until)
        self.draw_sprites(L, g, in_range)
        self.map_hit = (L, self.tap_cell)
        # painel e barras
        if step:
            self.draw_tutorial(L, step, w)
        else:
            self.draw_info(L.panel_y, w)
        self.draw_tower_bar(L.bars_y, L.bar, w)
        self.draw_action_bar(L.bars_y + L.bar, L.bar, w)

    def wave_preview(self, kinds):
        counts = {}
        for k in kinds:
            counts[k] = counts.get(k, 0) + 1
        return " ".join(f"{self.enemy_glyph(k).strip()}{counts[k]}" for k in ENEMIES if k in counts)

    def draw_tutorial(self, L, step, w):
        P = self.pal
        y = L.panel_y
        self.bar_row(y, f" TUTORIAL {self.tut_i + 1}/{len(self.tut)}", P(16, 114, True), w)
        lines = self.tut_lines(step, w)
        for i in range(L.panel - 1):
            self.bar_row(y + 1 + i, "", P(255, 236), w)
        for i, ln in enumerate(lines):
            put(self.scr, y + 1 + i, 1, ln, P(255, 236, True))
        last = y + L.panel - 1
        if step["wait"] is None:
            self.block(last, 0, w, 1, ["Toque aqui ou Enter para seguir ▶"], P(16, 220, True), self.tut_advance)
        elif self.has_message():
            put(self.scr, last, 1, self.message, P(229, 236, True))

    def draw_info(self, y, w):
        g, P = self.game, self.pal
        if self.has_message():
            self.bar_row(y, " " + self.message, P(229, 238, True), w)
            return
        cx, cy = self.cursor
        t = g.towers.get((cx, cy))
        c = g.mapa.at(cx, cy)
        if t:
            info = f" {self.tower_glyph(t.key)} {t.cfg['name']} nv{t.level} · dano {t.damage:.0f} · alc {t.range:.1f}"
        elif not self.cursor_moved:
            info = " Toque numa casa de grama para construir"
        elif c == ".":
            s = TOWERS[self.selected]
            info = f" {self.tower_glyph(self.selected)} {s['name']} {s['cost']}: {s['info']}"
        else:
            info = f" {TILES[c]}: não dá para construir"
        self.bar_row(y, info, P(250, 234), w)

    def draw_tower_bar(self, y, bar, w):
        g, P = self.game, self.pal
        buttons = []
        for i, (k, c) in enumerate(TOWERS.items()):
            sel = k == self.selected
            afford = g.gold >= c["cost"]
            attr = P(16, 220, True) if sel else P(255 if afford else 244, 237 if i % 2 == 0 else 238, afford)
            top = f"{self.tower_glyph(k)} {c['cost']}" if bar == 2 else f"{k}{self.tower_glyph(k)}{c['cost']}"
            buttons.append(([top, c["name"]], attr, lambda k=k: setattr(self, "selected", k)))
        self.row_buttons(y, bar, w, buttons)

    def draw_action_bar(self, y, bar, w):
        g, P = self.game, self.pal
        off = P(244, 236)
        if g.wave_active or g.enemies:
            wave = ([f"Onda {g.wave}", f"faltam {len(g.queue) + len(g.enemies)}"], off, self.call_wave)
        else:
            wave = ([f"▶ Onda {g.wave + 1}", "chamar"], P(16, 114, True), self.call_wave)
        speed = ([f"{self.g('fast')} {g.speed}x", "rápido" if g.speed == 2 else "normal"],
                 P(16, 39, True) if g.speed == 2 else P(255, 238, True), self.toggle_speed)
        t = g.towers.get(tuple(self.cursor))
        if t:
            up = t.upgrade_cost
            can = up is not None and g.gold >= up
            upgrade = ([f"{self.g('up')}{up if up else 'máx'}", "Melhorar"],
                       P(16, 214, True) if can else P(250, 238), self.do_upgrade)
            sell = ([f"{self.g('sell')}+{t.refund}", "Vender"], P(255, 94, True), self.do_sell)
        else:
            upgrade = ([f"{self.g('up')}", "Melhorar"], off, self.do_upgrade)
            sell = ([f"{self.g('sell')}", "Vender"], off, self.do_sell)
        self.row_buttons(y, bar, w, [wave, speed, upgrade, sell])

    def draw_maps(self, h, w):
        P = self.pal
        self.top_bar(w, f" {self.g('maps')} MAPAS", lambda: setattr(self, "screen", "menu"), "◀ Voltar", False)
        if not self.maps:
            self.maps = builtin_maps()
        self.maps_i = min(self.maps_i, len(self.maps) - 1)
        m = self.maps_sel()
        bh = 2 if h >= 34 else 1
        by = h - 2 * bh
        # lista com seções
        entries = [("PRONTOS", None)]
        entries += [(mp.name, i) for i, mp in enumerate(self.maps) if mp.builtin]
        entries.append(("MEUS MAPAS", None))
        mine = [(mp.name, i) for i, mp in enumerate(self.maps) if not mp.builtin]
        entries += mine or [("  nenhum ainda: toque em Novo", None)]
        full = (m.h + 2) + min(len(entries), 6) <= by - 3
        prev_h = (m.h if full else (m.h + 1) // 2) + 2
        list_h = max(3, min(len(entries), by - 3 - prev_h))
        sel_row = next(r for r, (_, i) in enumerate(entries) if i == self.maps_i)
        self.maps_scroll = min(max(self.maps_scroll, sel_row - list_h + 1), sel_row)
        self.maps_scroll = max(0, min(self.maps_scroll, max(0, len(entries) - list_h)))
        for r, (label, i) in enumerate(entries[self.maps_scroll:self.maps_scroll + list_h]):
            y = 2 + r
            if i is None:
                put(self.scr, y, 1, label, P(220, BG, True) if label.isupper() else P(244, BG))
                continue
            mp = self.maps[i]
            sel = i == self.maps_i
            attr = P(16, 220, True) if sel else P(255, 237)
            rec = self.record(mp)
            _, err = mp.check()
            right = f"{mp.w}×{mp.h}" + (" rascunho" if err else "") + (
                f" {self.g('trophy')}{rec['onda']}" if rec else "")
            self.block(y, 1, w - 2, 1, [], attr, lambda i=i: self.maps_tap(i))
            put(self.scr, y, 2, clip(("▶ " if sel else "  ") + mp.name, w - 4 - text_width(right)), attr)
            put(self.scr, y, w - 2 - text_width(right), right, attr)
        # prévia do mapa escolhido
        free_top = 2 + list_h + 1
        py = free_top + max(0, (by - 1 - free_top - prev_h) // 2)
        self.draw_preview(m, py, w, full)
        path, err = m.check()
        rows = m.h if full else (m.h + 1) // 2
        info = f"Trilha com {len(path)} casas · {sum(r.count('.') for r in m.grid)} de grama" if path else err.msg
        self.center(py + rows, clip(info, w - 2), P(250 if path else 196, BG))
        # botões
        btn = P(255, 237, True)
        self.row_buttons(by, bh, w, [
            ([f"▶ Jogar"], P(16, 114, True), self.maps_play),
            ([f"{self.g('edit')}Editar"], btn, self.maps_edit),
            ([f"{self.g('new')}Novo"], btn, self.maps_new)])
        self.row_buttons(by + bh, bh, w, [
            ([f"{self.g('dice')}Gerar"], btn, self.maps_generate),
            ([f"{self.g('del')}Apagar"], P(255, 52, True) if not m.builtin else P(244, 236), self.maps_delete),
            (["◀ Voltar"], btn, lambda: setattr(self, "screen", "menu"))])
        if self.has_message():
            self.bar_row(by - 1, " " + self.message, P(229, 238, True), w)

    def draw_preview(self, m, y, w, full):
        """Miniatura do mapa: 2 colunas por casa, ou meia linha por casa com ▀."""
        P = self.pal
        color = {".": 28, "#": 137, "S": 201, "B": 196, "T": 22, "~": 25}
        if full:
            x0 = (w - 2 * m.w) // 2
            for yy in range(m.h):
                for xx in range(m.w):
                    put(self.scr, y + yy, x0 + 2 * xx, "  ", P(-1, color[m.grid[yy][xx]]))
            return
        x0 = (w - m.w) // 2
        for r in range((m.h + 1) // 2):
            for xx in range(m.w):
                up = color[m.grid[2 * r][xx]]
                down = color[m.grid[2 * r + 1][xx]] if 2 * r + 1 < m.h else BG
                put(self.scr, y + r, x0 + xx, "▀", P(up, down))

    def draw_editor(self, h, w):
        ed, P = self.ed, self.pal
        m = ed.mapa
        L = compute_layout(h, w, m.w, m.h, 1)
        if L is None:
            self.draw_small(h, w, *min_size(m.w, m.h))
            return
        self.top_bar(w, f" {self.g('edit')}EDITOR · {m.name}{' *' if ed.dirty else ''}  {m.w}×{m.h}", self.ed_menu)
        path, err = m.check()
        if err:
            self.bar_row(1, f" ✘ {err.msg}", P(255, 52, True), w)
        else:
            self.bar_row(1, f" ✔ Pronto para jogar: trilha com {len(path)} casas", P(16, 114, True), w)
        self.draw_tiles(L, m, cursor=ed.cursor if ed.kbd else None, alert=err.pos if err else None,
                        anchor=ed.anchor if ed.tool in "#B" else None)
        self.map_hit = (L, self.ed_tap)
        if self.has_message():
            self.bar_row(L.panel_y, " " + self.message, P(229, 238, True), w)
        else:
            hint = Editor.HINTS[ed.tool]
            if ed.tool in "#B" and ed.anchor:
                hint = "Siga em linha reta a partir do laranja"
            self.bar_row(L.panel_y, " " + hint, P(250, 234), w)
        # ferramentas
        swatch = {".": ("  ", 28, 34), "#": ("  ", 137, -1), "~": ("~~", 25, 45),
                  "S": (self.g("spawn"), 137, 255), "B": (self.g("base"), 137, 255), "T": (self.g("tree"), 28, 34)}
        n = len(Editor.TOOLS)
        y = L.bars_y
        for i, t in enumerate(Editor.TOOLS):
            x0, x1 = w * i // n, w * (i + 1) // n
            bw = x1 - x0
            sel = t == ed.tool
            attr = P(16, 220, True) if sel else P(255, 237 if i % 2 == 0 else 238)
            name = TILES[t]
            self.block(y, x0, bw, L.bar, [] if L.bar == 1 else ["", name], attr, lambda t=t: self.ed_tool(t))
            text, sbg, sfg = swatch[t]
            if L.bar == 1:
                label = clip(f"{i + 1}{name}", max(0, bw - 3))
                sx = x0 + max(0, (bw - 2 - text_width(label)) // 2)
                put(self.scr, y, sx, text, P(sfg, sbg, True))
                put(self.scr, y, sx + 2, label, attr)
            else:
                put(self.scr, y, x0 + (bw - 2) // 2, text, P(sfg if not self.emoji or t in ".#~" else -1, sbg, True))
        btn = P(255, 238, True)
        self.row_buttons(L.bars_y + L.bar, L.bar, w, [
            (["« Desfazer"], btn, self.ed_undo),
            ([f"{self.g('dice')}Gerar"], btn, self.ed_generate),
            (["▶ Testar"], P(16, 114, True), self.ed_test),
            ([f"{self.g('save')}Salvar"], btn, self.ed_save)])

    def draw_overlay(self, h, w):
        P = self.pal
        ov = self.overlay
        title, items = ov["title"], ov["items"]
        box_w = min(w - 4, 40)
        x0 = (w - box_w) // 2
        ih = 2 if h >= len(title) + 4 + len(items) * 3 else 1
        height = len(title) + 2 + len(items) * (ih + 1)
        y0 = max(0, (h - height) // 2)
        frame = P(220, 236, True)
        put(self.scr, y0, x0, "╭" + "─" * (box_w - 2) + "╮", frame)
        for i in range(1, height):
            put(self.scr, y0 + i, x0, "│" + " " * (box_w - 2) + "│", frame)
        put(self.scr, y0 + height, x0, "╰" + "─" * (box_w - 2) + "╯", frame)
        for i, t in enumerate(title):
            t = clip(t, box_w - 4)
            put(self.scr, y0 + 1 + i, x0 + max(2, (box_w - text_width(t)) // 2), t, P(255, 236, True))
        for i, (label, _) in enumerate(items):
            y = y0 + len(title) + 2 + i * (ih + 1)
            sel = i == ov["i"]
            attr = P(16, 220, True) if sel else P(255, 238, True)
            self.block(y, x0 + 2, box_w - 4, ih, [label], attr, lambda i=i: self.overlay_choose(i))

    def draw_name(self, h, w):
        P = self.pal
        ov = self.overlay
        box_w = min(w - 2, 40)
        x0 = (w - box_w) // 2
        y0 = max(0, min((h - 10) // 2, h - 10))
        frame = P(220, 236, True)
        for i in range(10):
            put(self.scr, y0 + i, x0, "│" + " " * (box_w - 2) + "│", frame)
        put(self.scr, y0, x0, "╭" + "─" * (box_w - 2) + "╮", frame)
        put(self.scr, y0 + 9, x0, "╰" + "─" * (box_w - 2) + "╯", frame)
        put(self.scr, y0 + 1, x0 + 2, ov["title"], P(255, 236, True))
        field = clip(ov["text"] + "▏", box_w - 6)
        put(self.scr, y0 + 3, x0 + 2, " " + field + " " * (box_w - 6 - text_width(field)) + " ", P(16, 255, True))
        if ov["error"]:
            put(self.scr, y0 + 4, x0 + 2, clip("✘ " + ov["error"], box_w - 4), P(196, 236, True))
        else:
            put(self.scr, y0 + 4, x0 + 2, clip("Teclado: KEYBOARD na barra de teclas", box_w - 4), P(244, 236))
        half = (box_w - 6) // 2
        self.block(y0 + 6, x0 + 2, half, 2, ["Salvar"], P(16, 114, True), self.name_ok)
        self.block(y0 + 6, x0 + 4 + half, box_w - 6 - half, 2, ["Cancelar"], P(255, 238, True),
                   lambda: setattr(self, "overlay", None))

    # ------------------------------------------------------ laço
    def run(self):
        last = frame = time.monotonic()
        was_busy = True  # garante o primeiro desenho
        while not self.done:
            if self.screen == "menu" and not self.overlay:
                wait = 0.15  # animação do menu devagar: poupa bateria
            elif self.busy():
                wait = 1 / FPS - (time.monotonic() - frame)
            else:
                wait = IDLE_WAIT
            self.scr.timeout(max(0, int(wait * 1000)))
            k = self.scr.getch()
            self.scr.timeout(0)
            had_input = False
            while k != -1 and not self.done:
                self.on_key(k)
                had_input = True
                k = self.scr.getch()
            if self.done:
                break
            frame = now = time.monotonic()
            dt = min(now - last, 0.25)
            last = now
            self.anim += dt
            if self.screen == "game" and self.game and not self.overlay and not self.too_small:
                self.game.update(dt)
                if self.tut:
                    self.check_tutorial()
                if self.game and self.game.over and self.overlay is None:
                    self.finish_game()
            busy = self.busy() or (self.screen == "menu" and not self.overlay)
            # parado e sem tecla: nada mudou na tela, então não redesenha (poupa bateria)
            if had_input or busy or was_busy:
                self.render()
            was_busy = busy


USAGE = """Tower Defense para o terminal do Termux

Uso: td [opções]
  --tutorial               começa direto no tutorial
  --jogar [MAPA]           começa uma partida (nome de um mapa ou arquivo .mapa)
  --editor [MAPA]          abre o criador de mapas (vazio ou com esse mapa)
  --mapas                  lista os mapas prontos e os seus
  --gerar [LxA] [SEMENTE]  escreve um mapa aleatório, ex.: td --gerar 11x19 42 > meu.mapa
  --validar ARQUIVO        confere se um arquivo .mapa pode ser jogado
  --importar ARQUIVO       copia um arquivo .mapa para os seus mapas
  --sem-emoji              desenha com letras (se os emojis desalinharem)
  --sem-toque              desativa o toque na tela
  --versao                 mostra a versão
  --ajuda                  mostra esta ajuda

Seus mapas ficam em ~/.config/td-termux/mapas
"""


def _arg_after(args, flag):
    i = args.index(flag)
    if i + 1 < len(args) and not args[i + 1].startswith("--"):
        return args[i + 1]
    return None


def cli_maps():
    print("Mapas prontos:")
    for m in builtin_maps():
        print(f"  {m.name:<20} {m.w}×{m.h}  trilha {len(m.check()[0])}")
    mine = user_maps()
    print(f"\nSeus mapas ({MAPS_DIR}):")
    for m in mine:
        path, err = m.check()
        print(f"  {m.name:<20} {m.w}×{m.h}  " + (f"trilha {len(path)}" if path else f"rascunho: {err.msg}"))
    if not mine:
        print("  nenhum ainda: td --editor")
    return 0


def cli_generate(args):
    size, seed = "11x19", None
    i = args.index("--gerar")
    for a in args[i + 1:i + 3]:
        if re.fullmatch(r"\d+x\d+", a):
            size = a
        elif a.isdigit():
            seed = int(a)
    w, h = (int(v) for v in size.split("x"))
    if not (MAP_MIN <= w <= MAP_MAX_W and MAP_MIN <= h <= MAP_MAX_H):
        print(f"ERRO: tamanho entre {MAP_MIN}x{MAP_MIN} e {MAP_MAX_W}x{MAP_MAX_H}", file=sys.stderr)
        return 2
    try:
        sys.stdout.write(generate_map(w, h, seed).to_text())
    except RuntimeError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    return 0


def cli_validate(path):
    try:
        m = load_map_file(path)
        trail = m.trace()
    except MapError as e:
        print(f"ERRO: {e.msg}" + (f" (col {e.pos[0] + 1}, lin {e.pos[1] + 1})" if e.pos and "col" not in e.msg else ""))
        return 1
    print(f"OK: {m.name}, {m.w}×{m.h}, trilha com {len(trail)} casas")
    return 0


def cli_import(path):
    try:
        m = load_map_file(path)
        m.trace()
        dest = save_user_map(m, m.name)
    except MapError as e:
        print(f"ERRO: {e.msg}")
        return 1
    print(f"OK: {m.name} importado para {dest}")
    return 0


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if "--versao" in args or "-v" in args:
        print(read_version())
        return 0
    if "--ajuda" in args or "-h" in args:
        print(USAGE)
        return 0
    if "--mapas" in args:
        return cli_maps()
    if "--gerar" in args:
        return cli_generate(args)
    for flag, fn in (("--validar", cli_validate), ("--importar", cli_import)):
        if flag in args:
            path = _arg_after(args, flag)
            if not path:
                print(f"Uso: td {flag} ARQUIVO.mapa")
                return 2
            return fn(path)
    start, start_map = None, None
    for flag, mode in (("--tutorial", "tutorial"), ("--jogar", "play"), ("--editor", "editor")):
        if flag in args:
            start = mode
            ref = _arg_after(args, flag) if mode != "tutorial" else None
            if ref:
                try:
                    start_map = resolve_map(ref)
                except MapError as e:
                    print(f"ERRO: {e.msg}")
                    return 1
                if mode == "play" and start_map.check()[1]:
                    print(f"ERRO: {start_map.check()[1].msg}")
                    return 1
                if mode == "editor":
                    start_map = start_map.copy() if not start_map.builtin else start_map.copy(f"{start_map.name} (cópia)")
            break
    os.environ.setdefault("ESCDELAY", "25")
    locale.setlocale(locale.LC_ALL, "")
    emoji = False if "--sem-emoji" in args else None
    touch = False if "--sem-toque" in args else None
    curses.wrapper(lambda scr: App(scr, emoji, touch, start, start_map).run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
