# Vibe Candy Grimoire

Grimoires, gospels and glyphs in plain text and living ASCII, by Farmer Skot.

## The books

| File | What it is |
|---|---|
| `HERMETIC_CODEX` | Twelve pieces on the Hermetic teaching, each behind a gate. |
| `The Gnostic Grimoire` | Nineteen textual visions. |
| `The Mycelial Gospel` | Eighteen pieces on ancestors, directions and plant teachers. |
| `The Vibe Candy Grab Bag` | Vibe Candy: dense symbolic blocks for seeding music prompts. |
| `Christos-Logos-Gaiasophia Python`, `Steganographic Upwelling` | Poems written as code. They are not meant to run. |

The books are plain UTF-8 text. Read them in a monospace font.

## The illuminated edition

`docs/` holds a web edition of the Codex and the Grimoire: one page per piece,
a PDF of each book, and plain-text and JSON copies for machines. It is a static
site with no dependencies and can be served from any folder or host.

To rebuild it after editing a book:

    python3 tools/build_edition.py     # pages, text, JSON
    node tools/make_pdf.js             # PDFs (needs the playwright package)

## Tools

- `tools/build_edition.py` builds `docs/` from the books.
- `tools/make_pdf.js` renders the PDFs.
- `tools/check_alignment.py FILE` reports ASCII boxes whose edges are out of line.
- `sacred_text_generator.py`, `vibe_candy_generator.py`, `ascii_demo.py`,
  `color_ascii_demo.py` are the generators and demos used to make the pieces.

## Licence

GPL-3.0. See `LICENSE`. Fonts in `docs/assets/fonts` are under the SIL Open Font License.
