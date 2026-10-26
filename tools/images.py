"""Draw the ZipStock bitmaps. Rockbox reads 24-bit BMP, magenta is transparent."""
import math, sys
from PIL import Image, ImageDraw

OUT = sys.argv[1]
MAG = (255, 0, 255)
S = 4  # supersampling for the smooth shapes


def save(img, name):
    img.convert("RGB").save(f"{OUT}/{name}")


def vgrad(w, h, top, bot):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return img


# Header bar over a black page
HEAD_TOP, HEAD_BOT = (70, 70, 74), (28, 28, 30)
bd = Image.new("RGB", (96, 96), (0, 0, 0))
bd.paste(vgrad(96, 12, HEAD_TOP, HEAD_BOT), (0, 0))
save(bd, "backdrop.bmp")


def pixels(rows, colours):
    h, w = len(rows), len(rows[0])
    img = Image.new("RGB", (w, h), MAG)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in colours:
                img.putpixel((x, y), colours[c])
    return img


W = (235, 235, 235)
G = (150, 150, 150)
# Battery, 15x8: unknown, then 0-19, 20-39, 40-59, 60-79, 80-99, full
batt = Image.new("RGB", (15, 56), MAG)
fills = [(0, None), (2, (230, 60, 50)), (4, (240, 170, 40)), (6, W), (8, W), (11, W), (11, W)]
for i, (n, col) in enumerate(fills):
    f = Image.new("RGB", (15, 8), MAG)
    d = ImageDraw.Draw(f)
    d.rectangle([0, 0, 12, 7], outline=W)
    d.rectangle([13, 2, 14, 5], fill=W)
    if col:
        d.rectangle([2, 2, 1 + n, 5], fill=col)
    elif i == 0:
        d.rectangle([5, 3, 7, 4], fill=G)
    batt.paste(f, (0, i * 8))
save(batt, "battery.bmp")

charge = pixels([
    "WWWWWWWWWWWWW..",
    "W.....Y......W.",
    "W....YY......WW",
    "W...YYYYYY...WW",
    "W......YY....WW",
    "W......Y.....WW",
    "W............W.",
    "WWWWWWWWWWWWW..",
], {"W": W, "Y": (255, 205, 40)})
# a cleaner outline: redraw the frame and nub over it
d = ImageDraw.Draw(charge)
d.rectangle([0, 0, 12, 7], outline=W)
d.rectangle([13, 2, 14, 5], fill=W)
save(charge, "charging.bmp")

lock = pixels([
    ".WWW...",
    "W...W..",
    "W...W..",
    "WWWWW..",
    "WWWWW..",
    "WW.WW..",
    "WWWWW..",
    ".......",
], {"W": W})
save(lock, "lock.bmp")

state = pixels([
    # play
    "W.......", "WWW.....", "WWWWW...", "WWWWWWW.", "WWWWW...", "WWW.....", "W.......", "........",
    # pause
    "WW..WW..", "WW..WW..", "WW..WW..", "WW..WW..", "WW..WW..", "WW..WW..", "WW..WW..", "........",
    # stop
    "........", "WWWWWW..", "WWWWWW..", "WWWWWW..", "WWWWWW..", "WWWWWW..", "WWWWWW..", "........",
], {"W": W})
save(state, "state.bmp")

arrows = pixels([
    "...GG...", "..GGGG..", ".GG..GG.", "GG....GG", "........",
    "GG....GG", ".GG..GG.", "..GGGG..", "...GG...", "........",
], {"G": (110, 110, 110)})
save(arrows, "arrows.bmp")


def smooth(size, draw_fn, bg=(0, 0, 0)):
    w, h = size
    big = Image.new("RGB", (w * S, h * S), bg)
    draw_fn(ImageDraw.Draw(big), big, S)
    return big.resize((w, h), Image.LANCZOS)


def bar(w, h, top, bot, name):
    def fn(d, img, s):
        g = vgrad(w * s, h * s, top, bot)
        mask = Image.new("L", (w * s, h * s), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=h * s // 2, fill=255)
        img.paste(g, (0, 0), mask)
    save(smooth((w, h), fn), name)


BLUE_T, BLUE_B = (95, 170, 255), (30, 100, 210)
bar(90, 5, (58, 58, 62), (40, 40, 44), "pb-bg.bmp")
bar(90, 5, BLUE_T, BLUE_B, "pb-fill.bmp")
bar(53, 5, (58, 58, 62), (40, 40, 44), "vol-bg.bmp")
bar(53, 5, BLUE_T, BLUE_B, "vol-fill.bmp")


def tile(d, img, s, top, bot, size=40):
    g = vgrad(size * s, size * s, top, bot)
    mask = Image.new("L", (size * s, size * s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size * s - 1, size * s - 1], radius=9 * s, fill=255)
    img.paste(g, (0, 0), mask)
    # soft gloss on the top half
    gl = Image.new("L", (size * s, size * s), 0)
    ImageDraw.Draw(gl).rounded_rectangle([2 * s, 2 * s, size * s - 3 * s, size * s // 2], radius=8 * s, fill=38)
    img.paste((255, 255, 255), (0, 0), gl)


def R(s, *xy):
    return [v * s for v in xy]


def g_library(d, s):  # books on a shelf
    for x, h, c in [(9, 20, (255, 255, 255)), (15, 22, (235, 235, 235)), (21, 18, (255, 255, 255))]:
        d.rounded_rectangle(R(s, x, 30 - h, x + 5, 30), radius=s, fill=c)
    d.polygon([(27 * s, 12 * s), (31 * s, 11 * s), (35 * s, 29 * s), (31 * s, 30 * s)], fill=(240, 240, 240))
    d.rectangle(R(s, 7, 31, 34, 33), fill=(255, 255, 255))


def g_play(d, s):
    d.polygon([(14 * s, 10 * s), (14 * s, 30 * s), (31 * s, 20 * s)], fill=(255, 255, 255))


def g_bookmark(d, s):
    d.polygon([(12 * s, 8 * s), (28 * s, 8 * s), (28 * s, 32 * s), (20 * s, 25 * s), (12 * s, 32 * s)], fill=(255, 255, 255))


def g_folder(d, s):
    d.rounded_rectangle(R(s, 8, 11, 19, 16), radius=2 * s, fill=(255, 255, 255))
    d.rounded_rectangle(R(s, 8, 14, 32, 30), radius=2 * s, fill=(255, 255, 255))


def g_radio(d, s):
    d.line(R(s, 12, 17, 28, 9), fill=(255, 255, 255), width=2 * s)
    d.rounded_rectangle(R(s, 8, 16, 32, 31), radius=3 * s, fill=(255, 255, 255))
    d.ellipse(R(s, 11, 19, 20, 28), fill=(0, 150, 140))
    for y in (20, 24, 28):
        d.line(R(s, 23, y, 29, y), fill=(0, 150, 140), width=s * 3 // 2)


def g_voice(d, s):
    d.rounded_rectangle(R(s, 16, 7, 24, 23), radius=4 * s, fill=(255, 255, 255))
    d.arc(R(s, 11, 13, 29, 28), 0, 180, fill=(255, 255, 255), width=2 * s)
    d.line(R(s, 20, 28, 20, 32), fill=(255, 255, 255), width=2 * s)
    d.line(R(s, 15, 32, 25, 32), fill=(255, 255, 255), width=2 * s)


def g_gear(d, s):
    cx, cy = 20 * s, 20 * s
    for k in range(8):
        a = k * math.pi / 4
        x, y = cx + math.cos(a) * 11 * s, cy + math.sin(a) * 11 * s
        d.ellipse([x - 3 * s, y - 3 * s, x + 3 * s, y + 3 * s], fill=(255, 255, 255))
    d.ellipse([cx - 10 * s, cy - 10 * s, cx + 10 * s, cy + 10 * s], fill=(255, 255, 255))
    d.ellipse([cx - 4 * s, cy - 4 * s, cx + 4 * s, cy + 4 * s], fill=(110, 110, 120))


def g_list(d, s):
    for y in (11, 18, 25):
        d.rounded_rectangle(R(s, 9, y, 31, y + 3), radius=s, fill=(255, 255, 255))


def g_apps(d, s):
    for x in (10, 21):
        for y in (10, 21):
            d.rounded_rectangle(R(s, x, y, x + 8, y + 8), radius=2 * s, fill=(255, 255, 255))


def g_info(d, s):
    d.ellipse(R(s, 18, 8, 23, 13), fill=(255, 255, 255))
    d.rounded_rectangle(R(s, 18, 16, 23, 32), radius=s, fill=(255, 255, 255))


def g_dot(d, s):
    d.ellipse(R(s, 15, 15, 25, 25), fill=(255, 255, 255))


# Rockbox's themable icon numbers (apps/gui/icon.h) for the root menu items
ICONS = {
    0: ((255, 150, 40), (220, 85, 20), g_library),      # Database -> library
    25: ((80, 160, 255), (25, 90, 210), g_play),        # Now Playing
    10: ((95, 205, 95), (35, 140, 50), g_bookmark),     # Recent bookmarks -> resume
    29: ((255, 205, 60), (225, 150, 20), g_folder),     # Files -> folders
    28: ((40, 200, 185), (0, 140, 130), g_radio),       # FM radio
    21: ((255, 95, 95), (200, 35, 45), g_voice),        # Recording -> voice
    20: ((160, 160, 170), (95, 95, 105), g_gear),       # Settings
    2: ((175, 120, 255), (110, 60, 210), g_list),       # Playlists
    9: ((120, 140, 160), (70, 85, 105), g_apps),        # Plugins -> apps
    24: ((90, 130, 200), (45, 75, 140), g_info),        # System
}
strip = Image.new("RGB", (40, 40 * 33), (0, 0, 0))
for i in range(33):
    top, bot, glyph = ICONS.get(i, ((120, 120, 130), (70, 70, 80), g_dot))

    def fn(d, img, s, top=top, bot=bot, glyph=glyph):
        tile(d, img, s, top, bot)
        glyph(ImageDraw.Draw(img), s)
    strip.paste(smooth((40, 40), fn), (0, i * 40))
save(strip, "bigicons.bmp")


def nocover(d, img, s):
    tile(d, img, s, (70, 70, 76), (40, 40, 46), size=42)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(R(s, 12, 9, 30, 33), radius=2 * s, fill=(200, 200, 205))
    d.rectangle(R(s, 12, 9, 15, 33), fill=(160, 160, 165))
    d.line(R(s, 18, 15, 27, 15), fill=(120, 120, 125), width=s)
    d.line(R(s, 18, 19, 25, 19), fill=(120, 120, 125), width=s)
save(smooth((42, 42), nocover), "nocover.bmp")


def radio(d, img, s):
    d.line(R(s, 3, 6, 13, 1), fill=(200, 200, 205), width=s)
    d.rounded_rectangle(R(s, 1, 5, 15, 15), radius=2 * s, fill=(200, 200, 205))
    d.ellipse(R(s, 3, 7, 9, 13), fill=(0, 0, 0))
save(smooth((16, 16), radio), "radio.bmp")
