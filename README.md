# ZipStock

A Rockbox theme for the SanDisk Sansa Clip Zip that looks like the player's original firmware. It also adds database menus for audiobooks, listing them by author, by series, or as all books. These menus use the tags your books already have, so you don't need to retag anything.

![ZipStock in the Rockbox simulator](screenshots/zipstock-simulator.png)
![Audiobooks by author and series](screenshots/zipstock-series.png)

The screenshots are screen dumps from the Rockbox simulator for the Clip Zip.

## Features

- **Main menu**: one large picture per page with a lower-case name, the way the original firmware shows it. Up and Down move between pages, and Select opens one. The pages are playing, library, resume, folders, radio and settings.
- **Lists**: five rows in a rounded font, with a blue selection bar. Long lines scroll sooner and faster than Rockbox's default.
- **Now Playing**: the cover, author, book, series (or part number), chapter title, a progress bar, and time gone and left. The volume shows while you change it.
- **Audiobooks**: the library opens on Authors, Series and All Books, followed by the usual music menus with the books left out.
- **Resume**: each book picks up where you left it, however you open it.
- **Back button**: a short press goes back one screen, and holding it goes to the main menu, as on the original firmware.

## Requirements

- A Sansa Clip Zip already running Rockbox. The theme is made for the Clip Zip's 96x96 colour screen only.
- A computer to copy files to the player: Windows, macOS or Linux.

It was tested against a Rockbox development build from October 2026. Older releases may lack some of the skin features it uses. See [The back button](#the-back-button) for one known difference between builds.

## Install

1. **Get the files.** Download `zipstock-theme-<version>.zip` from [Releases](../../releases) and unzip it.
2. **Copy the theme.** Connect the player and copy the `.rockbox` folder from the zip onto the player's internal drive, not the microSD card. Merge it with the `.rockbox` folder that is already there. None of Rockbox's own files are replaced.
   - macOS and Linux hide folders whose names start with a dot. To show them, press Cmd+Shift+. (period) in Finder, or Ctrl+H in most Linux file managers. Windows shows them as they are.
3. **Pick the theme.** Eject the player, then go to Settings > Theme Settings > Browse Theme Files > `zipstock`.
4. **Load the settings.** Go to Settings > General Settings > Manage Settings > Browse .cfg Files > `zipstock-setup`. This sets the main menu order, autoresume, bookmarks and faster scrolling. The main menu pictures come from Rockbox's icons, so leave Settings > Theme Settings > Show Icons on.
5. **Build the database.** Go to Settings > General Settings > Database > Initialize Now. It scans in the background, so give it a few minutes for a large library. Then turn the player off and on again.
   - Don't start playback until you've restarted. The scan holds the memory Rockbox needs to load a playlist, so opening Now Playing during the scan shows `playlist_resume(): OOM`. This is harmless: the scan carries on.
   - At start-up Rockbox asks whether to finish the database. Press Select, or wait 5 seconds. Any other button says no.
   - After that, the database updates itself at start-up whenever files change.
6. **Browse.** Go to the main menu, then library, then Audiobooks.

## Audiobooks

| Menu | What it lists |
| --- | --- |
| **Authors** | Each author, then their books. A book in a series starts with its series and number, so a series lists in order, for example "Harry Potter #5: Harry Potter and the Order of the Phoenix". |
| **Series** | Each series and number, then the book. Two editions of the same book both appear. |
| **All Books** | Every book, by name. |

Rockbox adds [All tracks] and [Random] to the top of the Authors and Series lists. A theme can't remove them.

### How books are found

- A file counts as an audiobook when it is inside a folder named `AUDIOBOOKS`, on the player or the card, or when its name ends in `.m4b`. The music menus leave these files out.
- Books are listed by their album tag, which holds the book title in most audiobook files. A book with no album tag is listed by its file name.
- A book split into several files gets one line per file, for example "Book" and "Book, part 2". Picking a book queues the rest of the list, so the next one starts when it ends.
- Series come from the grouping tag, written as `Series #N`. Several series can be separated by `; `, for example `Harry Potter #5; Wizarding World #5`.
  - This is the format [Audiobookshelf](https://www.audiobookshelf.org/)'s Embed Metadata tool writes. Any tag editor can set it too.
  - Only groupings that contain a `#` count as series, because Rockbox fills an empty grouping with the track title.
  - Books without a series still appear under their author and in All Books.

### Covers

Rockbox shows covers embedded in the file as JPEG, or a `cover.jpg` or `folder.jpg` file next to the book. It can't show PNG or progressive JPEG covers, so those books get a plain book picture instead.

### Chapters

Rockbox doesn't read the chapters inside `.m4b` files. If a book has a cue sheet with the same name next to it (for example `Book.cue` beside `Book.m4b`), `zipstock-setup` turns on cue sheet support. Then Next and Previous skip between chapters.

## The back button

`.rockbox/keyremap.kmf` changes only the back button, and only in lists and menus:

- A short press goes back one screen.
- Holding it goes to the main menu.

Left still goes back as well. Everything else keeps Rockbox's own key layout.

Rockbox checks this file against its own build at start-up. If the build numbers its actions differently, Rockbox shows "key remap failed" and ignores the file. In that case, delete `/.rockbox/keyremap.kmf`. The rest of the theme works without it.

## Undo

- **Theme**: go to Settings > Theme Settings > Browse Theme Files and pick `cabbiev2`, Rockbox's default.
- **Audiobook menus**: delete `/.rockbox/tagnavi_user.config`.
- **Back button**: delete `/.rockbox/keyremap.kmf` and restart the player.

## Development

### Layout

| Path | What it is |
| --- | --- |
| `theme/.rockbox/` | The theme, exactly as it is copied to the player. |
| `INSTALL.txt` | The plain-text install notes that ship inside the zip as `ZIPSTOCK-README.txt`. |
| `tools/ttf2fnt.py` | Converts a TTF font to Rockbox's anti-aliased `.fnt` format. |
| `tools/images.py` | Draws the bitmaps. |
| `tools/checkskin.py` | Checks the skins against Rockbox's own tag table. |
| `tools/keyremap.py` | Writes `keyremap.kmf`. |
| `tools/sim.sh` | Drives a Rockbox simulator under Xvfb, for screenshots. |
| `build.sh` | Builds `zipstock-theme.zip`. |

### Rebuilding the assets

```sh
pip3 install pillow
python3 tools/images.py theme/.rockbox/wps/zipstock
python3 tools/ttf2fnt.py Nunito[wght].ttf theme/.rockbox/fonts
python3 tools/keyremap.py theme/.rockbox/keyremap.kmf
python3 tools/checkskin.py <rockbox source> theme theme/.rockbox/wps/zipstock.{sbs,wps,fms}
./build.sh
```

`Nunito[wght].ttf` is the variable font from [Google Fonts](https://fonts.google.com/specimen/Nunito). The action numbers in `tools/keyremap.py` must match the Rockbox build the file is meant for. They are documented in the script.

### Notes on Rockbox's database menus

These behaviours were found while testing `tagnavi_user.config` in the simulator:

- In a `%format` condition, clauses are joined by spaces. An `&` silently ends the condition.
- An empty tag compares as `<Untagged>`. Rockbox's own `tagnavi.config` tests for `[Untagged]`, which never matches.
- A missing track number is stored as -1, and an empty grouping is stored as the track title.
- `[All tracks]` and `[Random]` are added to every list above the title level, and a config can't remove them.
- A `%format` condition on a text tag only works if the list's own search has opened that tag, or if the database is loaded into RAM. Otherwise the condition silently fails. The book menus carry always-true clauses (`album !~ "~~~"`) to open the tags their formats test.

### CI and releases

CI runs on every push. It checks three things:

- the skins, against the tag table of the Rockbox source the theme was tested on (`ROCKBOX_SHA` in `.github/workflows/ci.yml`);
- `keyremap.kmf`, byte for byte, against what `tools/keyremap.py` writes;
- that the zip holds every file the install notes name.

CI doesn't run the simulator. The screenshots are taken by hand with `tools/sim.sh`.

To release, push a tag, or run **Release** from the Actions tab and give it the tag name:

```sh
git tag v1.0.0 && git push origin v1.0.0
```

The release workflow runs the same checks, then publishes `zipstock-theme-<tag>.zip`. A tag containing a hyphen, such as `v1.1.0-beta.1`, is published as a prerelease.

## Licence

ZipStock is under the [MIT License](LICENSE): the theme files, menus and tools.

The fonts are [Nunito](https://github.com/googlefonts/nunito), © 2014 The Nunito Project Authors, under the SIL Open Font License 1.1 (`theme/.rockbox/fonts/Nunito-OFL.txt`).
