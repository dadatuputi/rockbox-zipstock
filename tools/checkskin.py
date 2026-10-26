"""Static check of Rockbox skins against the tag table in lib/skin_parser/tag_table.c.

Not Rockbox's checkwps: it checks tag names, parameter counts and types,
conditional nesting, image and font files, labels, and viewport geometry.
"""
import os, re, struct, sys

RB, ROOT = sys.argv[1], sys.argv[2]  # rockbox source, theme root holding .rockbox
LCD = 96
src = open(os.path.join(RB, "lib/skin_parser/tag_table.c")).read()
src = src.replace("BAR_PARAMS", '"?[iP][iP][iP][iP]|s*"')
TAGS = {}
for name, params in re.findall(r'TAG\(\s*\w+\s*,\s*"([^"]*)"\s*,\s*((?:"[^"]*"\s*)+),', src):
    TAGS.setdefault(name, "".join(re.findall(r'"([^"]*)"', params)))
ESC = set("%(,);#<|>")
errors = []


def err(f, line, msg):
    errors.append(f"{f}:{line}: {msg}")


def spec_slots(spec):
    """Expand a param spec into (types, required_count, unbounded)."""
    optional_all = spec.startswith("?")
    spec = spec.lstrip("?")
    slots, req, star = [], None, False
    i = 0
    while i < len(spec):
        c = spec[i]
        if c == "|":
            req = len(slots); i += 1; continue
        if c == "*":
            star = True; i += 1; continue
        if c == "\n":
            break
        n = 1
        if c.isdigit():
            n = int(c); i += 1; c = spec[i]
        if c == "[":
            j = spec.index("]", i)
            c = spec[i + 1:j]; i = j
        slots += [c] * n
        i += 1
    if req is None:
        req = len(slots)
    if optional_all:
        req = 0
    return slots, req, star


def fnt_height(path):
    d = open(path, "rb").read(16)
    return struct.unpack("<H", d[6:8])[0]


class Parser:
    def __init__(self, fname, text):
        self.f, self.t, self.i, self.line = fname, text, 0, 1
        self.images, self.labels, self.fonts = {}, set(), {1: 16}
        self.used_images, self.used_labels = [], []
        self.vps = []  # (label, x, y, w, h, font, lines, line)
        self.cur = None
        self.in_switch = False

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else ""

    def args(self):
        """Split a ( ... ) list at top-level commas; tags inside are kept as text."""
        assert self.peek() == "("
        self.i += 1
        out, cur, depth = [], "", 0
        while self.i < len(self.t):
            c = self.t[self.i]
            if c == "#":
                raise SyntaxError("comment inside a parameter list")
            if c == "%" and self.t[self.i + 1:self.i + 2] in ESC:
                cur += c + self.t[self.i + 1]; self.i += 2; continue
            if c == "(":
                depth += 1
            if c == ")":
                if depth == 0:
                    self.i += 1
                    out.append(cur.strip())
                    return out
                depth -= 1
            if c == "," and depth == 0:
                out.append(cur.strip()); cur = ""; self.i += 1; continue
            if c == "\n":
                self.line += 1
            cur += c
            self.i += 1
        raise SyntaxError("unclosed (")

    def param_ok(self, kind, val):
        if val == "-":
            return any(k in kind for k in "idpsf")
        if val.startswith("%"):
            name = val[1:]
            return ("T" in kind or "C" in kind) and any(name.startswith(n) for n in TAGS)
        if re.fullmatch(r"-?\d+", val):
            return any(k in kind for k in "IiDdPp") or any(k in kind for k in "Ss")
        if re.fullmatch(r"-?\d+(\.\d+)?%?", val):
            return any(k in kind for k in "DdPp")
        return any(k in kind for k in "SsFf")

    def tag(self):
        start = self.line
        self.i += 1
        cond = False
        if self.peek() in ESC and self.peek() != "?":
            self.i += 1; self.cur and self.cur.__setitem__("text", True); return
        if self.peek() == "?":
            cond = True; self.i += 1
        name = None
        for n in (3, 2, 1):
            cand = self.t[self.i:self.i + n]
            if cand in TAGS and len(cand) == n:
                name = cand; break
        if not name:
            err(self.f, start, f"unknown tag %{self.t[self.i:self.i + 3]}")
            self.i += 1
            return
        self.i += len(name)
        params = []
        if self.peek() == "(":
            params = self.args()
        # the tag that picks a conditional's branch prints nothing itself
        self.in_switch = cond
        slots, req, star = spec_slots(TAGS[name])
        if len(params) < req:
            err(self.f, start, f"%{name} needs {req} params, has {len(params)}")
        if not star and len(params) > len(slots):
            err(self.f, start, f"%{name} takes at most {len(slots)} params, has {len(params)}")
        for k, v in enumerate(params):
            kind = slots[k] if k < len(slots) else (slots[-1] if slots else "s")
            if not self.param_ok(kind, v):
                err(self.f, start, f"%{name} param {k + 1} '{v}' does not fit type {kind}")
        self.semantics(name, params, start)
        self.in_switch = False
        if cond:
            if self.peek() != "<":
                err(self.f, start, f"%?{name} without <...>")
            else:
                self.i += 1
                self.body(stop=">")

    def semantics(self, name, p, line):
        if name in ("V", "Vl", "Vi"):
            label = None
            if name in ("Vl", "Vi"):
                label, p = p[0], p[1:]
                self.labels.add(label)
            x, y = int(p[0]), int(p[1])
            w = LCD - x if p[2] == "-" else int(p[2])
            h = LCD - y if p[3] == "-" else int(p[3])
            font = 1 if len(p) < 5 or p[4] == "-" else int(p[4])
            if x < 0 or y < 0 or x + w > LCD or y + h > LCD:
                err(self.f, line, f"viewport {x},{y},{w},{h} is off the {LCD}x{LCD} screen")
            self.cur = {"label": label, "x": x, "y": y, "w": w, "h": h, "font": font, "lines": 0, "line": line, "text": False}
            self.vps.append(self.cur)
        elif name == "Fl":
            path = os.path.join(ROOT, ".rockbox/fonts", p[1])
            if not os.path.exists(path):
                err(self.f, line, f"font {p[1]} missing")
            else:
                self.fonts[int(p[0])] = fnt_height(path)
        elif name in ("xl", "X", "x"):
            fn = p[1] if name != "X" else p[0]
            path = os.path.join(ROOT, ".rockbox/wps", os.path.splitext(os.path.basename(self.f))[0], fn)
            if not os.path.exists(path):
                err(self.f, line, f"image {fn} missing")
            elif name == "xl":
                from PIL import Image
                w, h = Image.open(path).size
                n = int(p[4]) if len(p) > 4 else 1
                if h % n:
                    err(self.f, line, f"{fn}: height {h} is not a multiple of {n} images")
                self.images[p[0]] = (w, h // n, n)
        elif name == "xd":
            if len(p) == 1 and len(p[0]) == 2:  # old style %xd(Ab): image A, subimage b
                self.used_images.append((p[0][0], str(ord(p[0][1]) - ord("a") + 1), line))
            else:
                self.used_images.append((p[0], p[1] if len(p) > 1 else None, line))
        elif name == "Vd":
            self.used_labels.append((p[0], line))
        elif name == "Lb":
            self.used_labels.append((p[0], line))
        elif name in ("pb", "pv", "LB", "bl") and p and p[0] != "":
            if self.cur:
                x, y = int(p[0]), int(p[1])
                w, h = int(p[2]), int(p[3])
                if x + w > self.cur["w"] or y + h > self.cur["h"]:
                    err(self.f, line, f"%{name} bar {x},{y},{w},{h} overflows its {self.cur['w']}x{self.cur['h']} viewport")
            if "image" in p:
                fn = p[p.index("image") + 1]
                path = os.path.join(ROOT, ".rockbox/wps", os.path.splitext(os.path.basename(self.f))[0], fn)
                if not os.path.exists(path):
                    err(self.f, line, f"bar image {fn} missing")
        silent = {"V", "Vl", "Vi", "Fl", "xl", "X", "x", "xd", "Vf", "Vb", "Vg", "Vs", "Cl", "Cd",
                  "wd", "we", "Lb", "Vd", "VI", "dr", "pb", "LB", "ac", "al", "ar", "aL", "aR", "ax", "s", "t", "if"}
        bar = name in ("pv", "bl", "pX", "pP", "tr", "St") and p
        if name not in silent and not bar and self.cur is not None and not self.in_switch:
            self.cur["text"] = True

    def body(self, stop=None):
        while self.i < len(self.t):
            c = self.peek()
            if stop and c == stop:
                self.i += 1
                return
            if c == "#":
                while self.peek() not in ("\n", ""):
                    self.i += 1
                continue
            if c == "%":
                self.tag(); continue
            if c == "\n":
                if self.cur is not None and self.cur["text"]:
                    self.cur["lines"] += 1
                    self.cur["text"] = False
                self.line += 1
                self.i += 1
                continue
            if c in "<>" and not stop:
                err(self.f, self.line, f"stray {c}")
            if c == "|" and stop:
                self.i += 1
                continue
            if c not in " \t" and self.cur is not None:
                self.cur["text"] = True
            self.i += 1
        if stop:
            err(self.f, self.line, f"missing {stop}")

    def finish(self):
        for label, sub, line in self.used_images:
            if label not in self.images:
                err(self.f, line, f"%xd({label}) has no %xl")
            elif sub and re.fullmatch(r"\d+", sub) and not 1 <= int(sub) <= self.images[label][2]:
                err(self.f, line, f"%xd({label},{sub}) past its {self.images[label][2]} images")
        for label, line in self.used_labels:
            if label not in self.labels:
                err(self.f, line, f"no viewport labelled {label}")
        for v in self.vps:
            fh = self.fonts.get(v["font"])
            if fh is None:
                err(self.f, v["line"], f"font {v['font']} not loaded")
            elif v["lines"] * fh > v["h"]:
                err(self.f, v["line"], f"{v['lines']} lines of {fh} px font do not fit in {v['h']} px")


for skin in sys.argv[3:]:
    p = Parser(skin, open(skin).read())
    try:
        p.body()
        p.finish()
    except SyntaxError as e:
        err(skin, p.line, str(e))
    print(f"{os.path.basename(skin)}: {len(p.vps)} viewports, {len(p.images)} images, fonts {p.fonts}")
print("\n".join(errors) if errors else "no problems found")
sys.exit(1 if errors else 0)
