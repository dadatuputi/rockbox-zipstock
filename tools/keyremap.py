"""Write .rockbox/keyremap.kmf: the Clip Zip's back button goes back, as on
the stock firmware.

Rockbox maps a short press of that button (BUTTON_HOME) to "main menu" in
lists and to "Now Playing" on the main menu, so it seems to do nothing. This
remaps only that button, in the list and menu contexts: a short press is
Back (ACTION_STD_CANCEL), holding it is the main menu (ACTION_STD_MENU).
Everything else keeps Rockbox's own keymap.

The file is apps/core_keymap.c's format: an array of struct button_mapping
(three int32: action, button, pre-button), little-endian. Entry 0 is a header
Rockbox checks against its own build (version, LAST_ACTION_PLACEHOLDER and
TARGET_ID), so a firmware whose action numbers differ refuses the file at
boot instead of misreading it. Then a lookup table of contexts, then each
context's mappings, each list ending in a sentinel.

The numbers come from a Clip Zip simulator built from Rockbox's source of
2026-10-25 (gdb on rockboxui), and from button-target.h and button.h.
"""
import struct
import sys

# apps/action.h, as built for the Clip Zip
ACTION_STD_CANCEL = 11
ACTION_STD_MENU = 13
LAST_ACTION_PLACEHOLDER = 179
CONTEXT_STD, CONTEXT_TREE, CONTEXT_MAINMENU, CONTEXT_LIST = 0, 2, 4, 6
CONTEXT_REMAPPED = 0x08000000
CONTEXT_STOPSEARCHING = 0xFFFFFFFF
TARGET_ID = 68                      # sansaclipzip
KEYREMAP_VERSION = 1

# firmware: button-target.h (sansa-clipzip) and export/button.h
BUTTON_NONE = 0
BUTTON_HOME = 0x00000001
BUTTON_REL = 0x02000000
BUTTON_REPEAT = 0x04000000

BACK = [
    (ACTION_STD_CANCEL, BUTTON_HOME | BUTTON_REL, BUTTON_HOME),
    (ACTION_STD_MENU, BUTTON_HOME | BUTTON_REPEAT, BUTTON_HOME),
]
CONTEXTS = [CONTEXT_STD, CONTEXT_TREE, CONTEXT_MAINMENU, CONTEXT_LIST]
SENTINEL = (CONTEXT_STOPSEARCHING, BUTTON_NONE, BUTTON_NONE)


def build():
    lut, blocks = [], []
    first = len(CONTEXTS) + 1                  # after the table and its end
    for ctx in CONTEXTS:
        lut.append((CONTEXT_REMAPPED | ctx, first + len(blocks), len(BACK)))
        blocks += BACK + [SENTINEL]
    body = lut + [SENTINEL] + blocks
    header = (KEYREMAP_VERSION, LAST_ACTION_PLACEHOLDER | (TARGET_ID << 8), len(body) + 1)
    return b"".join(struct.pack("<III", *(v & 0xFFFFFFFF for v in e)) for e in [header] + body)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "theme/.rockbox/keyremap.kmf"
    with open(out, "wb") as f:
        f.write(build())
    print(out)
