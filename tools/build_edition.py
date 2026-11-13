#!/usr/bin/env python3
"""Build the illuminated web edition in docs/ from the plain-text books.

Standard library only.  Run from the repository root:

    python3 tools/build_edition.py

Outputs, per book, under docs/<slug>/:
    index.html            contents (for the Codex: the Twelve Gates)
    NN-<piece>.html       one page per piece
    text/NN-<piece>.txt   the piece as plain text (machine readable)
    print.html            every piece on one page (source of the PDF)
    book.json             manifest: titles, gates, paths, hashes
plus docs/index.html (the shelf), docs/llms.txt and docs/.nojekyll.
"""
import hashlib
import html
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs")
REPO_URL = "https://github.com/Farmer-Skot/Vibe-Candy-Grimoire"
HOME_URL = "https://farmerskot.com/library/"
AUTHOR = "Farmer Skot"

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII",
         "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII",
         "XXIII", "XXIV"]

BOOKS = [
    {
        "slug": "hermetic-codex",
        "source": "HERMETIC_CODEX",
        "title": "The Hermetic Codex",
        "subtitle": "Transmissions from the Thrice-Great",
        "unit": "Gate",
        "blurb": "Twelve pieces on the Hermetic teaching, from the Emerald Tablet "
                 "to the sealing of the vessel. Each stands behind a gate.",
    },
    {
        "slug": "gnostic-grimoire",
        "source": "The Gnostic Grimoire",
        "title": "The Gnostic Grimoire",
        "subtitle": "Print-Worthy Textual Visions",
        "unit": "Vision",
        "blurb": "Nineteen textual visions in living ASCII: the primordial word "
                 "and what followed it.",
    },
]

SMALL = {"Of", "The", "And", "Et", "In", "To", "A", "An", "For", "On", "At", "By"}


def nice_title(s):
    words = s.strip().title().split(" ")
    out = []
    for i, w in enumerate(words):
        out.append(w.lower() if (i and w in SMALL) else w)
    return " ".join(out).replace("'S", "'s")


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def plain_initial(s):
    """Gate sentences open with a fraktur capital; return them in plain letters."""
    return unicodedata.normalize("NFKC", s)


def trim(lines):
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines


def parse(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    heads = [i for i, l in enumerate(lines) if re.match(r"^## PIECE \d+:", l)]
    pieces, extras = [], []
    for n, h in enumerate(heads):
        m = re.match(r"^## PIECE (\d+): (.*)$", lines[h])
        chunk = lines[h + 1: heads[n + 1] if n + 1 < len(heads) else len(lines)]
        gate, segs, cur, fenced = None, [], [], False
        i = 0
        while i < len(chunk):
            l = chunk[i]
            if l.startswith("```"):
                if fenced:
                    segs.append(("pre", trim(cur)))
                    cur = []
                fenced = not fenced
            elif fenced:
                cur.append(l.rstrip())
            elif l.strip().startswith("⟨ GATE"):
                gate = plain_initial(chunk[i + 1].strip())
                i += 1
            elif l.strip() and l.strip() != "---" and l.strip() != "'''":
                segs.append(("prose", l.strip()))
            i += 1
        segs = [s for s in segs if s[1]]
        # a colophon may follow the last piece
        keep = []
        for kind, body in segs:
            if kind == "pre" and any("⟨ COLOPHON ⟩" in x for x in body):
                extras.append(("Colophon", body))
            else:
                keep.append((kind, body))
        pieces.append({"n": int(m.group(1)), "raw_title": m.group(2).strip(),
                       "title": nice_title(m.group(2)), "gate": gate, "segs": keep})
    return pieces, extras


def esc(s):
    return html.escape(s, quote=False)


def render_pre(body):
    out = []
    for l in body:
        e = esc(l)
        st = l.strip()
        if st.startswith("⟨") and st.endswith("⟩") and len(st) < 70:
            lead = l[: len(l) - len(l.lstrip())]
            e = lead + '<span class="r">' + esc(st) + "</span>"
        else:
            e = re.sub(r"([◉☿])", r'<span class="r">\1</span>', e)
        out.append(e)
    return "\n".join(out)


def cols_of(body):
    def w(s):
        return sum(0 if unicodedata.category(c) in ("Mn", "Me", "Cf") else 1 for c in s)
    return max([w(l) for l in body] + [40])


def plait(n=3):
    rows = []
    for r in range(n * 2):
        unit = "╲╱" if r % 2 == 0 else "╱╲"
        rows.append(f'<span class="k{(r // 2) % 3}">' + unit * 120 + "</span>")
    return '<pre class="plait" aria-hidden="true">' + "".join(rows) + "</pre>"


def head(title, desc, css, extra=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="author" content="{AUTHOR}">
<link rel="stylesheet" href="{css}">
{extra}</head>
"""


def jsonld(obj):
    return ('<script type="application/ld+json">'
            + json.dumps(obj, ensure_ascii=False) + "</script>\n")


def initial_html(sentence):
    return (f'<span class="init" aria-hidden="true">{esc(sentence[0])}</span>'
            f'<span class="sr">{esc(sentence[0])}</span>'
            f'<span class="rest">{esc(sentence[1:])}</span>')


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def foot(up="../"):
    return f"""<footer class="colophon-foot">
<p>Set in plain text and living ASCII by {AUTHOR}.
<a href="{REPO_URL}">Source on GitHub</a> · <a href="{HOME_URL}">Back to the Library</a></p>
</footer>
"""


def build_book(book):
    pieces, extras = parse(os.path.join(ROOT, book["source"]))
    slug, unit = book["slug"], book["unit"]
    bdir = os.path.join(OUT, slug)
    total = len(pieces)
    width = max(cols_of(b) for p in pieces for k, b in p["segs"] if k == "pre") + 2
    for p in pieces:
        p["file"] = f"{p['n']:02d}-{slugify(p['raw_title'])}"
        p["numeral"] = ROMAN[p["n"] - 1]
        p["text"] = "\n\n".join("\n".join(b) if k == "pre" else b for k, b in p["segs"]) + "\n"
        p["sha256"] = hashlib.sha256(p["text"].encode("utf-8")).hexdigest()

    book_ld = {"@type": "Book", "name": book["title"],
               "author": {"@type": "Person", "name": AUTHOR}, "inLanguage": "en"}

    def body_html(p):
        parts = []
        for kind, b in p["segs"]:
            if kind == "pre":
                parts.append(f'<pre class="art" style="--cols:{width}">{render_pre(b)}</pre>')
            else:
                parts.append(f'<p class="gloss">{esc(b)}</p>')
        return "\n".join(parts)

    # ── piece pages
    for i, p in enumerate(pieces):
        prev_p = pieces[i - 1] if i else None
        next_p = pieces[i + 1] if i + 1 < total else None
        desc = p["gate"] or f"{unit} {p['numeral']} of {book['title']}."
        extra = (f'<link rel="alternate" type="text/plain" href="text/{p["file"]}.txt">\n'
                 + (f'<link rel="prev" href="{prev_p["file"]}.html">\n' if prev_p else "")
                 + (f'<link rel="next" href="{next_p["file"]}.html">\n' if next_p else "")
                 + jsonld({"@context": "https://schema.org", "@type": "Chapter",
                           "name": p["title"], "position": p["n"],
                           "description": desc, "isPartOf": book_ld}))
        gate = (f'<p class="gate">{initial_html(p["gate"])}</p>' if p["gate"] else "")
        nav = ['<nav class="turn" aria-label="Pages">']
        nav.append(f'<a class="prev" href="{prev_p["file"]}.html" rel="prev"><span>{unit} {prev_p["numeral"]}</span>{esc(prev_p["title"])}</a>'
                   if prev_p else '<span class="prev"></span>')
        nav.append(f'<a class="up" href="./">All {total}</a>')
        nav.append(f'<a class="next" href="{next_p["file"]}.html" rel="next"><span>{unit} {next_p["numeral"]}</span>{esc(next_p["title"])}</a>'
                   if next_p else '<span class="next"></span>')
        nav.append("</nav>")
        page = head(f"{p['title']} · {book['title']}", desc, "../assets/codex.css", extra) + f"""<body class="leaf">
<header class="running"><a href="./">{esc(book['title'])}</a><span>{unit} {p['numeral']} of {ROMAN[total - 1]}</span></header>
<main>
<article>
<header class="opening">
<p class="numeral">{unit} {p['numeral']}</p>
<h1>{esc(p['title'])}</h1>
{gate}
</header>
{plait(1)}
{body_html(p)}
<p class="alt"><a href="text/{p['file']}.txt">Plain text of this piece</a></p>
</article>
</main>
{chr(10).join(nav)}
{foot()}</body>
</html>
"""
        write(os.path.join(bdir, p["file"] + ".html"), page)
        write(os.path.join(bdir, "text", p["file"] + ".txt"), p["text"])

    # ── extras (colophon)
    extra_links = []
    for name, body in extras:
        f = slugify(name)
        page = head(f"{name} · {book['title']}", f"{name} of {book['title']}.",
                    "../assets/codex.css") + f"""<body class="leaf">
<header class="running"><a href="./">{esc(book['title'])}</a><span>{esc(name)}</span></header>
<main><article>
<header class="opening"><h1>{esc(name)}</h1></header>
{plait(1)}
<pre class="art" style="--cols:{width}">{render_pre(body)}</pre>
</article></main>
<nav class="turn" aria-label="Pages"><span class="prev"></span><a class="up" href="./">All {total}</a><span class="next"></span></nav>
{foot()}</body>
</html>
"""
        write(os.path.join(bdir, f + ".html"), page)
        write(os.path.join(bdir, "text", f + ".txt"), "\n".join(body) + "\n")
        extra_links.append((name, f + ".html"))

    # ── contents
    rows = []
    for p in pieces:
        sent = (f'<span class="sent">{initial_html(p["gate"])}</span>' if p["gate"]
                else '<span class="sent"><span class="init plain" aria-hidden="true">'
                     + esc(p["title"][0]) + "</span></span>")
        rows.append(f'<li><a href="{p["file"]}.html"><span class="num">{p["numeral"]}</span>'
                    f'<span class="name">{esc(p["title"])}</span>{sent}</a></li>')
    more = "".join(f' · <a href="{h}">{esc(n)}</a>' for n, h in extra_links)
    pdf = f"{slug}.pdf"
    contents = head(book["title"], book["blurb"], "../assets/codex.css",
                    '<link rel="alternate" type="application/json" href="book.json">\n'
                    + jsonld(dict({"@context": "https://schema.org"}, **book_ld,
                                  description=book["blurb"], numberOfPages=total))) + f"""<body class="contents">
<header class="carpet">
{plait(7)}
<div class="cartouche">
<p class="shelf"><a href="../">The Vibe Candy Library</a></p>
<h1>{esc(book['title'])}</h1>
<p class="sub">{esc(book['subtitle'])}</p>
</div>
</header>
<main>
<p class="lede">{esc(book['blurb'])}</p>
<ol class="gates">
{chr(10).join(rows)}
</ol>
<p class="formats">Read it another way:
<a href="{pdf}">PDF</a> ·
<a href="print.html">one long page</a> ·
<a href="text/">plain text</a> ·
<a href="book.json">JSON</a>{more}</p>
</main>
{foot()}</body>
</html>
"""
    write(os.path.join(bdir, "index.html"), contents)

    # ── plain text index
    tl = "\n".join(f'<li><a href="{p["file"]}.txt">{p["numeral"]}. {esc(p["title"])}</a></li>' for p in pieces)
    tl += "".join(f'\n<li><a href="{slugify(n)}.txt">{esc(n)}</a></li>' for n, _ in extras)
    write(os.path.join(bdir, "text", "index.html"),
          head(f"Plain text · {book['title']}", "Plain-text files.", "../../assets/codex.css")
          + f'<body class="leaf"><main><article><header class="opening"><h1>Plain text</h1>'
            f'<p class="numeral">{esc(book["title"])}</p></header><ol class="plainlist">{tl}</ol>'
            f'<p class="alt"><a href="../">Back to the contents</a></p></article></main></body></html>\n')

    # ── print page
    secs = []
    for p in pieces:
        gate = f'<p class="gate">{initial_html(p["gate"])}</p>' if p["gate"] else ""
        secs.append(f'<section class="sheet"><header class="opening"><p class="numeral">{unit} {p["numeral"]}</p>'
                    f'<h1>{esc(p["title"])}</h1>{gate}</header>\n{body_html(p)}</section>')
    for name, body in extras:
        secs.append(f'<section class="sheet"><header class="opening"><h1>{esc(name)}</h1></header>'
                    f'<pre class="art" style="--cols:{width}">{render_pre(body)}</pre></section>')
    toc = "".join(f'<li><span>{p["numeral"]}</span> {esc(p["title"])}</li>' for p in pieces)
    write(os.path.join(bdir, "print.html"),
          head(book["title"] + " (complete)", book["blurb"], "../assets/codex.css")
          + f"""<body class="leaf print">
<section class="sheet title">
<h1>{esc(book['title'])}</h1>
<p class="sub">{esc(book['subtitle'])}</p>
<p class="by">{AUTHOR}</p>
<ol class="toc">{toc}</ol>
</section>
{chr(10).join(secs)}
</body>
</html>
""")

    # ── manifest
    manifest = {
        "title": book["title"], "subtitle": book["subtitle"], "author": AUTHOR,
        "source": REPO_URL, "source_file": book["source"], "pieces": [
            {"number": p["n"], "numeral": p["numeral"], "title": p["title"],
             "gate": p["gate"], "html": p["file"] + ".html",
             "text": "text/" + p["file"] + ".txt",
             "lines": p["text"].count("\n"), "sha256": p["sha256"]} for p in pieces],
        "extras": [{"title": n, "html": h, "text": "text/" + slugify(n) + ".txt"}
                   for n, h in extra_links],
        "pdf": pdf, "complete_html": "print.html",
    }
    write(os.path.join(bdir, "book.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def build_shelf(manifests):
    cards = []
    for b, m in zip(BOOKS, manifests):
        cards.append(f"""<li><a href="{b['slug']}/">
<span class="init plain" aria-hidden="true">{esc(b['title'].split(' ')[1][0])}</span>
<span class="name">{esc(b['title'])}</span>
<span class="sent">{esc(b['blurb'])}</span>
<span class="count">{len(m['pieces'])} pieces</span></a></li>""")
    page = head("The Vibe Candy Library", "Illuminated editions of the Vibe Candy grimoires.",
                "assets/codex.css") + f"""<body class="contents shelfpage">
<header class="carpet">
{plait(7)}
<div class="cartouche">
<p class="shelf"><a href="{HOME_URL}">farmerskot.com</a></p>
<h1>The Vibe Candy Library</h1>
<p class="sub">Grimoires in living ASCII, illuminated for reading</p>
</div>
</header>
<main>
<ol class="gates books">
{chr(10).join(cards)}
</ol>
<p class="formats">For machines: <a href="llms.txt">llms.txt</a> ·
<a href="hermetic-codex/book.json">Codex JSON</a> ·
<a href="gnostic-grimoire/book.json">Grimoire JSON</a></p>
</main>
{foot("")}</body>
</html>
"""
    write(os.path.join(OUT, "index.html"), page)
    lines = ["# The Vibe Candy Library", "",
             f"> Grimoires in plain text and ASCII art by {AUTHOR}. "
             "Every piece is available as plain UTF-8 text.", ""]
    for b, m in zip(BOOKS, manifests):
        lines += [f"## {m['title']}", "", f"- [Manifest (JSON)]({b['slug']}/book.json)"]
        for p in m["pieces"]:
            g = f": {p['gate']}" if p["gate"] else ""
            lines.append(f"- [{p['numeral']}. {p['title']}]({b['slug']}/{p['text']}){g}")
        lines.append("")
    lines += [f"Source repository: {REPO_URL}", ""]
    write(os.path.join(OUT, "llms.txt"), "\n".join(lines))
    write(os.path.join(OUT, ".nojekyll"), "")


if __name__ == "__main__":
    ms = [build_book(b) for b in BOOKS]
    build_shelf(ms)
    for m in ms:
        print(m["title"], "-", len(m["pieces"]), "pieces")
