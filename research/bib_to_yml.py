#!/usr/bin/env python3
"""
bib_to_yml.py  —  Convert papers.bib to publications.yml, the data source for
                  the publication listing in pub-listing.qmd.

Usage:
    python bib_to_yml.py                         # uses default paths below
    python bib_to_yml.py input.bib output.yml    # custom paths

Runs automatically before each render (pre-render in _quarto.yml). Needs only
the Python standard library. The yml is rewritten only when its content changes.

Which section a paper appears in comes from its `keywords` field (see
KEYWORD_SECTIONS), or from a `section = {...}` field if you add one.

Standard fields used: author, title, journal/journaltitle/booktitle, year,
month/date, volume, number/issue, pages, doi, url, eprint (arXiv).
The title links to `url`, else the DOI, else the arXiv page.

Optional extra fields add links/lines to an entry (see pub-listing.ejs):
    pdf, preprint, code, software, github, data, supplemental,
    slides, poster, video, shareit                   -> [label] links after the authors
    awards, mediacoverage, invitedpresentation       -> extra lines (markdown ok)
    highlycited, hotpaper = {1}                      -> badges
e.g.  code = {https://github.com/me/repo},
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

# ── Default file paths (edit here or pass as command-line args) ──────────────
DEFAULT_INPUT = "papers.bib"
DEFAULT_OUTPUT = "publications.yml"

# ── Keywords → Section ───────────────────────────────────────────────────────
# The Section value must match an `include: section:` filter in pub-listing.qmd,
# otherwise the entry won't show up on the page.
KEYWORD_SECTIONS = {
    "peerjournal": "Peer-reviewed",
    "unpublished": "Preprint",
    "techreport":  "Technical reports",
}

# Your name as it is formatted in the author list (regex); matches are bolded.
MY_NAME = r"G\.(?: [A-Z]\.)* Moran"

# biblatex author annotations (author+an = {1=first; 3=student}) → superscript
# marks after that author's name. Explain them in the key on pub-listing.qmd.
ANNOTATION_MARKS = {
    "first":   "*",    # co-first author / equal contribution
    "equal":   "*",
    "student": "†",    # student advisee
}

# Extra bib fields passed straight through to the listing template.
PASSTHROUGH = ["pdf", "preprint", "code", "software", "github", "data", "supplemental",
               "slides", "poster", "video", "shareit",
               "awards", "mediacoverage", "invitedpresentation"]
FLAG_FIELDS = ["highlycited", "hotpaper"]

FIELD_ORDER = [
    "section", "authors", "year", "date", "title", "path", "journal",
    "volume", "issue", "pages", "doi", *PASSTHROUGH, *FLAG_FIELDS, "categories",
]

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


# ═════════════════════════════ BibTeX parsing ════════════════════════════════

def _match_brace(s: str, i: int) -> int:
    """s[i] == '{'; return the index just past its matching '}'."""
    depth = 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced braces")


FIELD_RE = re.compile(r"\s*([A-Za-z][\w+\-:.]*)\s*=\s*")


def _parse_fields(body: str) -> dict:
    fields, pos, n = {}, 0, len(body)
    while pos < n:
        m = FIELD_RE.match(body, pos)
        if not m:                                  # junk: skip to the next comma
            nxt = body.find(",", pos)
            if nxt < 0:
                break
            pos = nxt + 1
            continue
        name, pos = m.group(1).lower(), m.end()
        if pos < n and body[pos] == "{":
            end = _match_brace(body, pos)
            value = body[pos + 1:end - 1]
        elif pos < n and body[pos] == '"':
            end = pos + 1
            depth = 0
            while end < n and not (body[end] == '"' and depth == 0 and body[end - 1] != "\\"):
                depth += body[end] == "{"
                depth -= body[end] == "}"
                end += 1
            value, end = body[pos + 1:end], end + 1
        else:
            m2 = re.compile(r"[^,}\s]*").match(body, pos)
            value, end = m2.group(0), m2.end()
        fields[name] = " ".join(value.split())     # collapse newlines/indentation
        pos = end
        while pos < n and body[pos] in " \t\r\n,":
            pos += 1
    return fields


def parse_bib(text: str) -> list[dict]:
    """Return [{'_type':..., '_key':..., field: raw value, ...}, ...] in file order."""
    entries, i = [], 0
    head = re.compile(r"@\s*(\w+)\s*\{")
    while True:
        m = head.search(text, i)
        if not m:
            break
        etype = m.group(1).lower()
        start = m.end() - 1
        try:
            end = _match_brace(text, start)
        except ValueError:
            print(f"WARNING: unbalanced braces in @{etype} entry near: {text[m.start():m.start()+60]!r}")
            break
        i = end
        if etype in ("comment", "preamble", "string"):
            continue
        body = text[start + 1:end - 1]
        key, _, rest = body.partition(",")
        rec = _parse_fields(rest)
        rec["_type"], rec["_key"] = etype, key.strip()
        entries.append(rec)
    return entries


# ═════════════════════════════ LaTeX → Unicode ═══════════════════════════════

ACCENTS = {"'": "\u0301", "`": "\u0300", '"': "\u0308", "^": "\u0302", "~": "\u0303",
           "=": "\u0304", ".": "\u0307", "u": "\u0306", "v": "\u030C", "H": "\u030B",
           "c": "\u0327", "k": "\u0328", "r": "\u030A"}
SPECIAL = {"ss": "ß", "aa": "å", "AA": "Å", "ae": "æ", "AE": "Æ", "oe": "œ", "OE": "Œ",
           "o": "ø", "O": "Ø", "l": "ł", "L": "Ł", "i": "ı", "j": "ȷ"}


def _accent(cmd: str, base: str) -> str:
    base = {"\\i": "i", "\\j": "j"}.get(base, base)
    return unicodedata.normalize("NFC", base + ACCENTS[cmd])


def latex_to_unicode(s: str) -> str:
    # accents: \'a  \'{a}  {\'a}  \v{c}  \c c  \'{\i}
    s = re.sub(r"\\([\'`\"^~=.])\s*(?:\{\s*(\\?[A-Za-z])\s*\}|(\\?[A-Za-z]))",
               lambda m: _accent(m.group(1), m.group(2) or m.group(3)), s)
    s = re.sub(r"\\([uvHckr])\s*(?:\{\s*(\\?[A-Za-z])\s*\}|\s+([A-Za-z]))",
               lambda m: _accent(m.group(1), m.group(2) or m.group(3)), s)
    s = re.sub(r"\\(ss|aa|AA|ae|AE|oe|OE|o|O|l|L|i|j)(?![A-Za-z])\s?",
               lambda m: SPECIAL[m.group(1)], s)
    # simple formatting commands: keep their content
    s = re.sub(r"\\(?:emph|textit|textbf|textsc|textrm|mathrm|text)\s*\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\([&%$#_{}])", r"\1", s)              # escaped symbols
    s = s.replace("---", "—").replace("--", "–").replace("``", "“").replace("''", "”")
    s = re.sub(r"(?<!\\)~", " ", s)                     # tie
    s = s.replace("{", "").replace("}", "")
    return unicodedata.normalize("NFC", " ".join(s.split()))


# ═════════════════════════════ Field helpers ═════════════════════════════════

def split_authors(raw: str) -> list[str]:
    """Split on ' and ' outside braces."""
    parts, depth, last = [], 0, 0
    for m in re.finditer(r"[{}]|\s+and\s+", raw):
        tok = m.group(0)
        if tok == "{":
            depth += 1
        elif tok == "}":
            depth -= 1
        elif depth == 0:
            parts.append(raw[last:m.start()])
            last = m.end()
    parts.append(raw[last:])
    return [p.strip() for p in parts if p.strip()]


def format_author(raw: str) -> str:
    """'Moran, Gemma E.' or 'Gemma E. Moran' -> 'G. E. Moran'."""
    if raw.startswith("{") and raw.endswith("}") and _match_brace(raw, 0) == len(raw):
        return latex_to_unicode(raw)                     # {Corporate Author}
    name = latex_to_unicode(raw)
    if "," in name:
        parts = [p.strip() for p in name.split(",")]
        family, given = parts[0], parts[-1] if len(parts) > 1 else ""
    else:
        toks = name.split()
        k = next((i for i, t in enumerate(toks[:-1]) if t[:1].islower()), len(toks) - 1)
        family, given = " ".join(toks[k:]), " ".join(toks[:k])  # keeps "de la Cruz"
    # 'Gemma E.' -> 'G. E.';  'Jean-Paul' -> 'J.-P.'
    initials = " ".join("-".join(f"{p[0]}." for p in tok.split("-") if p)
                        for tok in given.replace(".", ". ").split())
    return f"{initials} {family}".strip()


def parse_annotations(raw: str, key: str = "") -> dict[int, list[str]]:
    """'1=first; 2=first, highlight' -> {1: ['first'], 2: ['first', 'highlight']}.

    biblatex syntax: ';' between authors, ',' between labels of one author.
    Anything after a comma that looks like 'N=...' is ignored, with a warning.
    """
    if re.search(r",\s*\d+\s*=", raw):
        print(f"WARNING: {key}: author+an must use ';' between authors "
              f"(e.g. 1=student; 2=student) — marks after the comma are ignored: {{{raw}}}")
    notes = {}
    for part in raw.split(";"):
        pos, _, labels = part.partition("=")
        if pos.strip().isdigit():
            notes.setdefault(int(pos), []).extend(
                l.strip().lower() for l in labels.split(",") if l.strip() and "=" not in l)
    return notes


def format_authors(raw: str, annotations: str = "", key: str = "") -> str:
    names = [format_author(a) for a in split_authors(raw)]
    notes = parse_annotations(annotations, key)
    for pos, labels in notes.items():
        if pos > len(names):
            print(f"WARNING: {key}: author+an refers to author {pos}, but there are only {len(names)} authors")
        elif "highlight" in labels and not re.fullmatch(MY_NAME, names[pos - 1]):
            print(f"WARNING: {key}: author+an highlights author {pos} ({names[pos - 1]}), "
                  "which isn't you — check the author numbers")
    out = []
    for i, a in enumerate(names, 1):
        s = f"<strong>{a}</strong>" if re.fullmatch(MY_NAME, a) else a
        marks = "".join(dict.fromkeys(ANNOTATION_MARKS[l] for l in notes.get(i, []) if l in ANNOTATION_MARKS))
        marks = marks.replace("*", "&#42;")      # literal *, not Markdown emphasis
        out.append(s + (f"<sup>{marks}</sup>" if marks else ""))
    return ", ".join(out)


def make_date(f: dict, year) -> str | None:
    if f.get("date"):
        m = re.match(r"(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", f["date"])
        if m:
            y, mo, d = m.groups()
            return f"{y}-{int(mo or 1):02d}-{int(d or 1):02d}"
    if not year:
        return None
    month = 1
    raw = f.get("month", "").strip().lower()
    if raw.isdigit():
        month = int(raw)
    elif raw[:3] in MONTHS:
        month = MONTHS[raw[:3]]
    return f"{year}-{month:02d}-01"


def section_for(f: dict) -> str | None:
    if f.get("section"):
        return latex_to_unicode(f["section"])
    for kw in re.split(r"[,;|]", f.get("keywords", "")):
        if kw.strip().lower() in KEYWORD_SECTIONS:
            return KEYWORD_SECTIONS[kw.strip().lower()]
    return None


def entry_to_record(f: dict) -> dict:
    rec = {}
    sec = section_for(f)
    if sec:
        rec["section"] = sec
    if f.get("author"):
        rec["authors"] = format_authors(f["author"], f.get("author+an", ""), f.get("_key", ""))

    year = None
    ymatch = re.search(r"\d{4}", f.get("year", "") or f.get("date", ""))
    if ymatch:
        year = int(ymatch.group(0))
        rec["year"] = year
    date = make_date(f, year)
    if date:
        rec["date"] = date

    if f.get("title"):
        rec["title"] = latex_to_unicode(f["title"])

    venue = f.get("journal") or f.get("journaltitle") or f.get("booktitle") or ""
    eprint = f.get("eprint", "").strip()
    is_arxiv = "arxiv" in f.get("archiveprefix", f.get("eprinttype", "")).lower()
    if not venue and eprint and is_arxiv:
        venue = f"arXiv preprint arXiv:{eprint}"
    if venue:
        venue = latex_to_unicode(venue)
        rec["journal"] = re.sub(r"(arXiv:\d{4}\.)\s+(\d)", r"\1\2", venue)

    for bib_key, key in (("volume", "volume"), ("number", "issue"), ("issue", "issue")):
        if f.get(bib_key, "").strip() and key not in rec:
            rec[key] = latex_to_unicode(f[bib_key])
    if f.get("pages", "").strip():
        rec["pages"] = re.sub(r"\s*-{1,3}\s*", "–", f["pages"].strip())

    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", f.get("doi", "").strip())
    if doi:
        rec["doi"] = doi

    url = f.get("url", "").strip().split()[0] if f.get("url", "").strip() else ""
    if url:
        rec["path"] = url
    elif doi:
        rec["path"] = f"https://doi.org/{doi}"
    else:
        arxiv = re.search(r"arXiv:\s*(\d{4}\.\d{4,5})", rec.get("journal", ""))
        if arxiv or (eprint and is_arxiv):
            rec["path"] = "https://arxiv.org/abs/" + (arxiv.group(1) if arxiv else eprint)

    for key in PASSTHROUGH:
        if f.get(key, "").strip():
            rec[key] = f[key].strip()
    for key in FLAG_FIELDS:
        if f.get(key, "").strip():
            try:
                rec[key] = int(f[key])
            except ValueError:
                pass
    if f.get("categories", "").strip():
        rec["categories"] = [c.strip() for c in re.split(r"[,;|]", f["categories"]) if c.strip()]
    return rec


# ═════════════════════════════ YAML output ═══════════════════════════════════

def yaml_value(key: str, value) -> str:
    if isinstance(value, int) or key == "date":
        return str(value)                        # unquoted so Quarto sees a date
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(v, ensure_ascii=False) for v in value) + "]"
    return json.dumps(value, ensure_ascii=False)  # JSON strings are valid YAML


def record_to_yaml(rec: dict) -> str:
    lines = []
    for key in FIELD_ORDER:
        if key in rec:
            prefix = "- " if not lines else "  "
            lines.append(f"{prefix}{key}: {yaml_value(key, rec[key])}")
    return "\n".join(lines)


def convert(input_path: str, output_path: str) -> None:
    text = Path(input_path).read_text(encoding="utf-8")
    entries = parse_bib(text)
    records = [entry_to_record(e) for e in entries]

    counts = {}
    for r in records:
        counts[r.get("section")] = counts.get(r.get("section"), 0) + 1
    print(f"bib_to_yml: {len(records)} entries from {input_path} — "
          + ", ".join(f"{s} ({n})" for s, n in counts.items() if s))
    missing = [(e["_key"], r.get("title", "?")) for e, r in zip(entries, records) if "section" not in r]
    if missing:
        print(f"WARNING: {len(missing)} entries have no known keyword "
              f"({', '.join(KEYWORD_SECTIONS)}) and won't appear on pub-listing.qmd:")
        for key, title in missing:
            print(f"  - {key}: {title}")

    output_text = "\n\n".join(record_to_yaml(r) for r in records) + "\n"
    out = Path(output_path)
    if out.exists() and out.read_text(encoding="utf-8") == output_text:
        print(f"bib_to_yml: {output_path} already up to date")
        return
    out.write_text(output_text, encoding="utf-8")
    print(f"bib_to_yml: wrote {output_path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    convert(args[0] if len(args) > 0 else DEFAULT_INPUT,
            args[1] if len(args) > 1 else DEFAULT_OUTPUT)
