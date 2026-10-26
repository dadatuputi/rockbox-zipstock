"""Render a TTF into a Rockbox anti-aliased .fnt (RB12, depth 1 = 4 bits per pixel).

Follows tools/convttf.c: glyphs are full font height, row-major, two pixels
per byte with the first pixel in the low nibble, and 15 means background.
"""
import struct, sys
from PIL import Image, ImageDraw, ImageFont

CHARS = list(range(32, 256)) + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026]


def convert(ttf, px, weight, outdir, name, pad_top=0, pad_bottom=0, track=0):
    font = ImageFont.truetype(ttf, px)
    if weight:
        font.set_variation_by_name(weight)
    asc, desc = font.getmetrics()
    # Tight line height: what plain Latin text uses, not the font's line gap.
    # Accents over capitals get clipped by a pixel or two, as in most small fonts.
    top = min(font.getbbox(c, anchor="ls")[1] for c in "Abdfhkl'")
    bot = max(font.getbbox(c, anchor="ls")[3] for c in "gjpqy,")
    a = -top + 1 + pad_top
    d = bot + pad_bottom
    height = a + d
    first, last = min(CHARS), max(CHARS)
    have = set(CHARS)
    glyphs, widths, offsets = bytearray(), [], []
    default = ord("?")
    for code in range(first, last + 1):
        if code not in have:
            offsets.append(None); widths.append(None); continue
        ch = chr(code)
        # round down unless nearly whole: Rockbox has no kerning, so rounding up
        # leaves visible gaps after wide letters such as m
        adv = int(font.getlength(ch) + 0.25) + track
        if adv <= 0:
            adv = 1
        img = Image.new("L", (adv + 4, height), 0)
        ImageDraw.Draw(img).text((0, a), ch, font=font, fill=255, anchor="ls")
        img = img.crop((0, 0, adv, height))
        px_ = list(img.tobytes())
        nib = [(255 - v + 8) // 17 for v in px_]
        if len(nib) % 2:
            nib.append(15)
        offsets.append(len(glyphs))
        widths.append(adv)
        for i in range(0, len(nib), 2):
            glyphs.append(nib[i] | (nib[i + 1] << 4))
    dflt = default - first
    offsets = [o if o is not None else offsets[dflt] for o in offsets]
    widths = [w if w is not None else widths[dflt] for w in widths]
    size = last - first + 1
    nbits = len(glyphs)
    long_off = nbits >= 0xFFDB
    out_b = bytearray(b"RB12")
    out_b += struct.pack("<HHHH", max(widths), height, a, 1)
    out_b += struct.pack("<IIIIII", first, default, size, nbits, size, size)
    out_b += glyphs
    if long_off:
        out_b += b"\0" * (((nbits + 3) & ~3) - nbits)
        for o in offsets: out_b += struct.pack("<I", o)
    else:
        out_b += b"\0" * (((nbits + 1) & ~1) - nbits)
        for o in offsets: out_b += struct.pack("<H", o)
    out_b += bytes(widths)
    out = f"{outdir}/{height}-{name}.fnt"
    open(out, "wb").write(out_b)
    print(out, "height", height, "ascent", a, "bytes", len(out_b))


if __name__ == "__main__":
    ttf = sys.argv[1]
    outdir = sys.argv[2]
    # List rows: 12 px type with room above and below, so the selection bar
    # is 16 pixels tall and five rows fill the screen under the header.
    convert(ttf, 12, b"Bold", outdir, "Nunito-Bold", pad_top=2, pad_bottom=1)
    convert(ttf, 10, b"Bold", outdir, "Nunito-Bold")
    convert(ttf, 17, b"ExtraBold", outdir, "Nunito-ExtraBold")
