# ZipStock

A Rockbox theme for the SanDisk Sansa Clip Zip (96x96 colour) that looks like the stock firmware, plus a database menu for audiobooks: author, then series, then the books in order.

![ZipStock in the Rockbox simulator](screenshots/zipstock-simulator.png)
![Audiobooks by author and series](screenshots/zipstock-series.png)

All screenshots are screen dumps from the Rockbox simulator for the Clip Zip.

## What's here

| Path | What it is |
| --- | --- |
| `theme/.rockbox/` | The theme. Copy it onto the player's own drive, merging with the `.rockbox` folder there. |
| `tag-books.py` | Writes series, number in the series and a short title into each `.m4b`, from the Audiobookshelf index on the card, so the database can list books by series. Dry run by default; `--apply`, `--undo`. Needs `mutagen`. |
| `INSTALL.txt` | The plain-text install notes that ship inside the zip. |
| `tools/` | How the theme was made: `ttf2fnt.py` (TTF to Rockbox anti-aliased `.fnt`), `images.py` (draws the bitmaps), `checkskin.py` (static check of the skins), `sim.sh` (drives a Rockbox simulator under Xvfb). |
| `build.sh` | Builds `zipstock-theme.zip` for release. |

## Install

You need a Clip Zip already running Rockbox, and a Mac or PC to copy files.

1. **Get the files.** Download `zipstock-theme.zip` from Releases, or clone this repo and run `./build.sh`. Unzip it.
2. **Copy the theme.** Plug in the player and copy the `.rockbox` folder onto the player's own drive (not the microSD card), merging it with the `.rockbox` folder already there. Nothing of Rockbox's is replaced. On a Mac, Finder hides dot folders; press Cmd+Shift+. to show them.
3. **Pick the theme.** Eject, then on the player: Settings > Theme Settings > Browse Theme Files > `zipstock`.
4. **Load the settings.** Settings > General Settings > Manage Settings > Browse .cfg Files > `zipstock-setup`. It sets the main menu, autoresume, bookmarks and faster scrolling. Don't load `simple.cfg` after it: that turns icons off, and the main menu pictures come from the icons.
5. **Tag the books.** Rockbox's database only knows what is in each file's tags. `tag-books.py` writes the series, the number in the series and a short title into each `.m4b` on the card, from the Audiobookshelf index (`<card>/.absh/index.json`). With the card in the computer:
   ```sh
   pip3 install mutagen
   python3 tag-books.py /Volumes/MUSICSD/AUDIOBOOKS           # shows what it would write
   python3 tag-books.py /Volumes/MUSICSD/AUDIOBOOKS --apply   # writes it
   ```
   Check the list from the first command before you apply. Only tags change, in place, never the audio. The old tags are saved to `<card>/.absh/tag-books-undo.json`, and `--undo` puts them back. Books in no series go under "Standalone books". Run it again whenever you add books.
6. **Build the database.** On the player: Settings > General Settings > Database > Initialize Now. It scans in the background; give it a few minutes for a big library. Then turn the player off and on. At boot it asks to finish the database: press Select or wait 5 seconds (any other button says no). After that it updates itself at boot when files change.
7. **Browse.** Main menu > library > Audiobooks:
   - **Authors**: author, then series, then the books numbered 1 to N
   - **Series**: series, then the books in order
   - **All Books**: every book by name

   A second edition shows its tag first, e.g. "5. (Full Cast) Order of the Phoenix". A book in several files shows "5.2 ..." for its second file.

### How books are found

A file counts as an audiobook when its path has a folder named `AUDIOBOOKS` or it ends in `.m4b`. Music menus leave those files out. Each book resumes where you left it, however you open it.

### Covers

Rockbox shows embedded JPEG covers, or `cover.jpg` / `folder.jpg` beside the file. It can't show PNG or progressive JPEG; those books get a plain book picture.

### Undo

- Theme: Settings > Theme Settings > Browse Theme Files > `cabbiev2`.
- Database menus: delete `/.rockbox/tagnavi_user.config`.
- Tags: `python3 tag-books.py /Volumes/MUSICSD/AUDIOBOOKS --undo`.

## Rebuilding the assets

```sh
pip3 install pillow
python3 tools/images.py theme/.rockbox/wps/zipstock
python3 tools/ttf2fnt.py Nunito[wght].ttf theme/.rockbox/fonts
python3 tools/checkskin.py <rockbox source> theme theme/.rockbox/wps/zipstock.{sbs,wps,fms}
```

`Nunito[wght].ttf` is the variable font from Google Fonts.

## Notes on Rockbox's database menus

Found while testing `tagnavi_user.config` in the simulator:

- In a `%format` condition, clauses are joined by spaces. An `&` silently ends the condition.
- An empty tag compares as `<Untagged>`. Stock `tagnavi.config` tests for `[Untagged]`, which never matches.
- A missing track number is stored as -1.
- `[All tracks]` and `[Random]` are added to every list above the title level; a config can't remove them.

## Licence

The fonts are Nunito, under the SIL Open Font License (`theme/.rockbox/fonts/Nunito-OFL.txt`).
