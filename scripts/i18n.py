"""Translate the built site through a catalog of text units.

The English page is the source of truth. This module walks a built page and
finds every piece of text a reader sees: runs of text in the markup (inline
tags such as <code> and <b> stay inside the run), readable attributes
(aria-label, title, alt, placeholder, meta descriptions), and the text inside
JavaScript strings and template literals, which is where the explorers keep
their step notes. `${...}` expressions in a template become numbered
placeholders ({0}, {1}, ...) in the unit, so a translation can move them.

Each language has a catalog, src/i18n/<lang>.json, that maps an English unit
to its translation. Units that are code or names are stored unchanged.

Usage:
    python3 scripts/i18n.py extract [lang]   # add new units to the catalog, list stale ones
    python3 scripts/i18n.py check [lang]     # report missing and invalid translations
"""

import html as htmllib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "src" / "i18n"

INLINE = {
    "a", "abbr", "b", "br", "code", "em", "i", "kbd", "mark", "q", "s",
    "samp", "small", "strong", "sub", "sup", "time", "u", "var", "wbr",
}  # fmt: skip
SKIP = {"style", "pre", "textarea"}
ATTRS = {"aria-label", "title", "alt", "placeholder"}
META = {
    "description", "og:title", "og:description", "og:image:alt",
    "twitter:title", "twitter:description",
}  # fmt: skip
KEYWORDS = {
    "return", "typeof", "case", "do", "else", "in", "of", "new", "delete",
    "void", "throw", "yield", "await", "instanceof",
}  # fmt: skip

TAG_RE = re.compile(
    r"<!--.*?-->|<(/?)([A-Za-z][\w-]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*)(/?)>", re.S
)
ATTR_RE = re.compile(r"(\s)([\w:-]+)=(\"([^\"]*)\"|'([^']*)')")
PH_RE = re.compile(r"\x00(\d+)\x00")
WORD = re.compile(r"[A-Za-z]{2,}")
JS_PROSE = re.compile(
    r"[A-Za-z]{2,}(?:[,:;!?()’']?\s+|[,:;!?]\s*)[A-Za-z]{2,}|^[A-Z][a-z]+[.!?:]?$|^an? [a-z]{3,}$"
)
CODE_TOKEN = re.compile(r"[a-z]+(?:-[a-z]+)+|[\w-]+\.(?:py|js)")


def visible(run):
    """The words a reader sees in a run: tags and inline code removed."""
    t = re.sub(r"<code\b[^>]*>.*?</code>", " ", run, flags=re.S)
    t = TAG_RE.sub(" ", t)
    t = PH_RE.sub(" ", t)
    return htmllib.unescape(t)


def is_prose(run, js):
    text = visible(run)
    if not WORD.search(text):
        return False
    if js:
        if re.search(r"[<>]|=\"|^\W*$", TAG_RE.sub("", run)):
            return False
        bare = TAG_RE.sub("", re.sub(r"<code\b[^>]*>.*?</code>", "", run, flags=re.S))
        tokens = PH_RE.sub(" ", bare).split()
        if any(re.match(r"[.#\[][\w-]", t) for t in tokens) or all(
            CODE_TOKEN.fullmatch(t) for t in tokens
        ):
            return False  # selectors, class names, CSS properties, file names
        counted = re.search(r"(?:\d|\x00)\s*[a-z]{3,}\b|\b[a-z]{3,}\s*(?:\d|\x00)", run)
        words = any(re.fullmatch(r"[A-Za-z]{3,}[,.:;!?]?", t) for t in tokens)
        return bool(
            JS_PROSE.search(text.strip()) or counted or (len(tokens) > 1 and words)
        )
    return True


def to_key(run):
    """Collapse whitespace and number the placeholders in order of appearance."""
    order = []

    def ph(m):
        order.append(m.group(1))
        return "{%d}" % (len(order) - 1)

    return re.sub(r"\s+", " ", PH_RE.sub(ph, run)).strip(), order


def from_key(text, order):
    return re.sub(r"\{(\d+)\}", lambda m: f"\x00{order[int(m.group(1))]}\x00", text)


class Walker:
    """Visit every unit; `fn(key, ctx)` returns a replacement or None."""

    def __init__(self, fn):
        self.fn = fn
        self.src = ""

    def unit(self, run, pos, js, order_ok=True):
        key, order = to_key(run)
        if not key or not is_prose(run, js):
            return None
        new = self.fn(key, pos)
        if new is None or new == key:
            return (
                None  # unchanged units keep their original bytes, whitespace included
            )
        if sorted(re.findall(r"\{\d+\}", new)) != sorted(re.findall(r"\{\d+\}", key)):
            raise ValueError(f"placeholders differ: {key!r} -> {new!r}")
        return from_key(new, order)

    # markup ---------------------------------------------------------------
    def markup(self, s, pos=0, js=False):
        out, i, run_start = [], 0, None

        def flush(end):
            nonlocal run_start
            if run_start is None:
                return
            seg = s[run_start:end]
            core = seg.strip()
            new = self.unit(core, pos + run_start, js) if core else None
            if new is None:
                out.append(seg)
            else:
                out.append(
                    seg[: len(seg) - len(seg.lstrip())] + new + seg[len(seg.rstrip()) :]
                )
            run_start = None

        for m in TAG_RE.finditer(s):
            if m.start() < i:
                continue
            if m.start() > i and run_start is None:
                run_start = i
            name = (m.group(2) or "").lower()
            if (
                name
                and not m.group(1)
                and not m.group(4)
                and 'translate="no"' in (m.group(3) or "")
            ):
                flush(m.start())
                end = close_of(s, name, m.end())
                out.append(s[m.start() : end])
                i = end
                continue
            if name in INLINE:
                if run_start is None:
                    run_start = m.start()
                i = m.end()
                continue
            flush(m.start())
            tag = m.group(0)
            if name and not m.group(1):
                tag = self.attrs(tag, name, m.group(3) or "", pos + m.start(), js)
            out.append(tag)
            i = m.end()
            if name in SKIP | {"script"} and not m.group(1):
                end = s.lower().find(f"</{name}", i)
                end = len(s) if end < 0 else end
                inner = s[i:end]
                if name == "script" and not js:
                    inner = self.js(inner, pos + i)
                out.append(inner)
                i = end
        if i < len(s) and run_start is None:
            run_start = i
        flush(len(s))
        return "".join(out)

    def attrs(self, tag, name, attrs, pos, js):
        names = dict(
            (a.group(2).lower(), a.group(4) if a.group(4) is not None else a.group(5))
            for a in ATTR_RE.finditer(attrs)
        )
        meta = name == "meta" and (
            names.get("name") in META or names.get("property") in META
        )

        def repl(a):
            key = a.group(2).lower()
            if not (key in ATTRS or (meta and key == "content")):
                return a.group(0)
            val = a.group(4) if a.group(4) is not None else a.group(5)
            new = self.unit(val, pos, js=False) if WORD.search(visible(val)) else None
            if new is None:
                return a.group(0)
            q = '"' if a.group(4) is not None else "'"
            return f"{a.group(1)}{a.group(2)}={q}{new}{q}"

        return tag[: len(name) + 1] + ATTR_RE.sub(repl, tag[len(name) + 1 :])

    # javascript -----------------------------------------------------------
    def js(self, code, pos=0):
        out, i, n, last = [], 0, len(code), ""
        while i < n:
            c = code[i]
            if c in "\"'":
                j = scan_string(code, i)
                body = code[i + 1 : j - 1]
                new = self.markup(body, pos + i + 1, js=True)
                out.append(c + escape(new, c, body) + c)
                i, last = j, "x"
            elif c == "`":
                j = self.template(code, i, pos, out)
                i, last = j, "x"
            elif code.startswith("//", i):
                j = code.find("\n", i)
                j = n if j < 0 else j
                out.append(code[i:j])
                i = j
            elif code.startswith("/*", i):
                j = code.index("*/", i) + 2
                out.append(code[i:j])
                i = j
            elif c == "/" and (
                last == "" or last in "(,=:[!&|?{};+-*%<>~^" or last in KEYWORDS
            ):
                j = scan_regex(code, i)
                out.append(code[i:j])
                i, last = j, "x"
            elif c.isalnum() or c in "_$":
                j = i
                while j < n and (code[j].isalnum() or code[j] in "_$."):
                    j += 1
                word = code[i:j]
                out.append(word)
                i, last = j, (word if word in KEYWORDS else "x")
            elif c.isspace():
                out.append(c)
                i += 1
            else:
                out.append(c)
                i += 1
                last = ")" if c in ")]" else c
        return "".join(out)

    def template(self, code, i, pos, out):
        chunks, exprs, j, cur = [], [], i + 1, []
        while True:
            c = code[j]
            if c == "\\":
                cur.append(code[j : j + 2])
                j += 2
            elif c == "`":
                chunks.append("".join(cur))
                j += 1
                break
            elif code.startswith("${", j):
                chunks.append("".join(cur))
                cur = []
                end = scan_expr(code, j + 2)
                exprs.append((code[j + 2 : end], j + 2))
                j = end + 1
            else:
                cur.append(c)
                j += 1
        joined = chunks[0] + "".join(
            f"\x00{k}\x00{chunks[k + 1]}" for k in range(len(exprs))
        )
        new = self.markup(joined, pos + i + 1, js=True)
        new = escape(new, "`", joined)
        new = PH_RE.sub(
            lambda m: "${"
            + self.js(exprs[int(m.group(1))][0], pos + exprs[int(m.group(1))][1])
            + "}",
            new,
        )
        out.append("`" + new + "`")
        return j


def close_of(s, name, i):
    """Index just past the tag that closes an element opened before i."""
    depth = 1
    for m in re.finditer(rf"<(/?){name}\b[^>]*>", s[i:], re.I):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return i + m.end()
    return len(s)


def scan_string(code, i):
    q, j = code[i], i + 1
    while code[j] != q:
        j += 2 if code[j] == "\\" else 1
    return j + 1


def scan_regex(code, i):
    j, cls = i + 1, False
    while True:
        c = code[j]
        if c == "\\":
            j += 2
            continue
        if c == "[":
            cls = True
        elif c == "]":
            cls = False
        elif c == "/" and not cls:
            j += 1
            break
        j += 1
    while j < len(code) and code[j].isalpha():
        j += 1
    return j


def scan_expr(code, j):
    """Return the index of the `}` that closes a template expression starting at j."""
    depth = 0
    walker = Walker(lambda k, p: None)
    while True:
        c = code[j]
        if c in "\"'":
            j = scan_string(code, j)
        elif c == "`":
            j = walker.template(code, j, 0, [])
        elif c == "{":
            depth += 1
            j += 1
        elif c == "}":
            if depth == 0:
                return j
            depth -= 1
            j += 1
        else:
            j += 1


def escape(new, quote, old):
    """Escape a translation for the JS string it goes back into (only if it changed)."""
    if new == old:
        return new
    out, i = [], 0
    while i < len(new):
        c = new[i]
        if c == "\\":
            out.append(new[i : i + 2])
            i += 2
            continue
        if c == quote or (quote == "`" and new.startswith("${", i)):
            out.append("\\" + c)
        elif c == "\n":
            out.append("\\n")
        else:
            out.append(c)
        i += 1
    return "".join(out)


# catalog -------------------------------------------------------------------
def catalog_path(lang):
    return I18N / f"{lang}.json"


def load(lang):
    p = catalog_path(lang)
    return json.loads(p.read_text()) if p.exists() else {}


def units(html):
    """All units of a built page, in document order, with their first position."""
    found = {}

    def fn(key, pos):
        found.setdefault(key, pos)

    Walker(fn).markup(html)
    return found


def localize(html, lang):
    """Return the page translated with the catalog, and the units still missing."""
    table = load(lang)
    missing = []

    def fn(key, pos):
        t = table.get(key)
        if t is None:
            missing.append(key)
        return t

    return Walker(fn).markup(html), missing


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    lang = sys.argv[2] if len(sys.argv) > 2 else "ro"
    html = (ROOT / "public" / "index.html").read_text()
    found = units(html)
    table = load(lang)
    stale = [k for k in table if k not in found]
    missing = [k for k in found if table.get(k) is None]
    if cmd == "extract":
        merged = {k: table.get(k) for k in found}
        catalog_path(lang).parent.mkdir(parents=True, exist_ok=True)
        catalog_path(lang).write_text(
            json.dumps(merged, ensure_ascii=False, indent=1) + "\n"
        )
        todo = ROOT / ".cache" / f"i18n-{lang}-todo.json"
        todo.parent.mkdir(exist_ok=True)
        todo.write_text(
            json.dumps(
                [
                    {"en": k, "context": html[max(0, p - 160) : p + len(k) + 80]}
                    for k, p in found.items()
                    if table.get(k) is None
                ],
                ensure_ascii=False,
                indent=1,
            )
        )
        print(
            f"{len(found)} units, {len(missing)} to translate (see {todo.relative_to(ROOT)}), {len(stale)} stale removed"
        )
    else:
        print(f"{len(found)} units, {len(missing)} missing, {len(stale)} stale")
        for k in missing[:20]:
            print("  missing:", k[:100])
    return 1 if cmd == "check" and missing else 0


if __name__ == "__main__":
    sys.exit(main())
