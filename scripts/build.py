"""Build the Runtime lines site into public/.

Reads the page sources in src/pages, the shared library in src/lib, the
partials in src/partials and src/reference, and the generated data in
src/data, then writes one self-contained public/index.html plus the small
static files Vercel serves next to it.

Usage:
    python3 scripts/build.py
    SITE_URL=https://example.com python3 scripts/build.py   # absolute og:image, canonical, sitemap
"""

import json
import os
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
LIB = SRC / "lib"
OUT = ROOT / "public"
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")

AUTHOR = {
    "name": "Sergiu Vlad",
    "url": "https://sergiuvlad.com",
    "linkedin": "https://www.linkedin.com/in/netics/",
    "email": "me@sergiuvlad.com",
}
SITE_NAME = "Runtime lines"
SITE_TITLE = "Runtime lines: how Node.js and Python actually run your code"
SITE_DESC = (
    "An interactive, visual reference for full-stack engineers preparing for interviews: "
    "the Node.js event loop, Python memory and the GIL, and the JavaScript and Python type systems, "
    "step by step, with interview questions for each."
)

VIEWS = [
    # key, source page, id prefix, colour, bullet, label, subtitle, document title
    (
        "node",
        "node-event-loop",
        "n-",
        "green",
        "N",
        "Node event loop",
        "call stack, queues, phases",
        "The Node.js event loop",
    ),
    (
        "memory",
        "python-memory",
        "m-",
        "blue",
        "M",
        "Python memory",
        "names, refcounts, GC, pymalloc",
        "Python memory",
    ),
    (
        "gil",
        "python-gil",
        "g-",
        "red",
        "G",
        "The GIL",
        "threads, cores, races",
        "Python's GIL",
    ),
    (
        "js-types",
        "js-types",
        "j-",
        "orange",
        "J",
        "JavaScript types",
        "typeof, ==, copies, floats",
        "JavaScript types",
    ),
    (
        "py-types",
        "python-types",
        "p-",
        "purple",
        "P",
        "Python types",
        "dispatch, +=, hashing",
        "Python types",
    ),
]

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Overpass:wght@400..900&family=Overpass+Mono:wght@400..700&display=swap">"""

DARK_RE = re.compile(r"/\* @dark-begin \*/(.*?)/\* @dark-end \*/", re.S)
REGION_RE = re.compile(r"/\* @region ([^*]+?) \*/\n(.*?)\n/\* @endregion \*/\n?", re.S)


def expand_dark(css):
    """Turn each dark token block into the media query plus the explicit theme selector."""

    def repl(match):
        body = match.group(1).strip()
        return (
            "@media (prefers-color-scheme: dark) {\n"
            ':root:not([data-theme="light"]) {\n' + body + "\n}\n}\n"
            ':root[data-theme="dark"] {\n' + body + "\n}\n"
        )

    return DARK_RE.sub(repl, css)


def shake(lib, page_js):
    """Keep only the library regions that the pages (or other kept regions) reference."""
    matches = list(REGION_RE.finditer(lib))
    corpus = page_js + REGION_RE.sub("", lib)
    keep = set()
    changed = True
    while changed:
        changed = False
        for idx, m in enumerate(matches):
            if idx in keep:
                continue
            names = m.group(1).split()
            if any(
                re.search(rf"(?<![\w$]){re.escape(n)}(?![\w$])", corpus) for n in names
            ):
                keep.add(idx)
                corpus += m.group(2)
                changed = True
    out = []
    pos = 0
    for idx, m in enumerate(matches):
        out.append(lib[pos : m.start()])
        if idx in keep:
            out.append(m.group(2) + "\n\n")
        pos = m.end()
    out.append(lib[pos:])
    return re.sub(r"\n{3,}", "\n\n", "".join(out))


def extract(name):
    """Split a page source into its CSS, <main> markup and page script."""
    src = (SRC / "pages" / f"{name}.html").read_text()
    css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
    css = css.replace("/*@SHARED_CSS@*/", "").replace("/*@MEM_CSS@*/", "")
    body = re.search(r'<main class="wrap">(.*?)</main>', src, re.S).group(1)
    script = re.search(r"<script>(.*?)</script>", src, re.S).group(1)
    js = script.split("//@SHARED_JS@", 1)[1].replace("//@MEM_JS@\n", "").rstrip()
    assert js.endswith("})();"), name
    js = js[: -len("})();")].rstrip() + "\n"
    if "//@OPS_JSON@" in js:
        ops = json.loads((SRC / "data" / "ops.json").read_text())
        js = js.replace(
            "//@OPS_JSON@",
            "const OPS = " + json.dumps(ops, separators=(",", ":")) + ";",
        )
    if "//@USES_JSON@" in js:
        js = js.replace(
            "//@USES_JSON@",
            "const USES = " + (SRC / "data" / "uses.json").read_text() + ";",
        )
    return css, body, js


def prefix_ids(texts, p):
    """Give every id in a page a prefix so five pages can share one document."""
    joined = "".join(texts)
    ids = set(re.findall(r'(?<![\w-])id="([A-Za-z][\w-]*)"', joined))
    stems = set()
    for i in ids:
        m = re.match(r"^([A-Za-z][\w-]*?[A-Za-z_-])\d+$", i)
        if m:
            stems.add(m.group(1))

    def attr(m):
        return f'{m.group(1)}="{p}{m.group(2)}"' if m.group(2) in ids else m.group(0)

    def ref(m):
        name = m.group(1)
        after = m.string[m.end() : m.end() + 2]
        if name in ids or (name in stems and after == "${"):
            return f"#{p}{name}"
        return m.group(0)

    out = []
    for t in texts:
        t = re.sub(
            r'(?<![\w-])(id|for|aria-labelledby|aria-describedby|aria-controls)="([A-Za-z][\w-]*)"',
            attr,
            t,
        )
        t = re.sub(r"#([A-Za-z][\w-]*)", ref, t)
        out.append(t)
    return out


def split_sel(head):
    parts, depth, cur = [], 0, ""
    for ch in head:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [x.strip() for x in parts if x.strip()]


def scope_sel(head, scope):
    out = []
    for s in split_sel(head):
        if s in ("body", "html", ":root"):
            out.append(scope)
        elif s.startswith(("body ", "html ")):
            out.append(scope + s[4:])
        else:
            out.append(f"{scope} {s}")
    return ", ".join(out)


def scope_css(css, scope):
    """Prefix every selector in a page's CSS with its view container."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = []
    i = 0
    while True:
        j = css.find("{", i)
        if j < 0:
            break
        head = css[i:j].strip()
        if head.startswith("@"):
            depth, k = 1, j + 1
            while depth:
                if css[k] == "{":
                    depth += 1
                elif css[k] == "}":
                    depth -= 1
                k += 1
            inner = css[j + 1 : k - 1]
            if head.startswith(("@media", "@supports")):
                out.append(f"{head} {{\n{scope_css(inner, scope)}}}\n")
            else:
                out.append(f"{head} {{{inner}}}\n")
            i = k
        else:
            k = css.find("}", j)
            out.append(f"{scope_sel(head, scope)} {{{css[j + 1 : k]}}}\n")
            i = k + 1
    return "".join(out)


def token(name):
    """Read a colour token from the light theme block of shared.css."""
    css = (LIB / "shared.css").read_text()
    return re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{3,8}})", css).group(1)


ROUTER = """
  const ORDER = %s;
  const TITLES = %s;
  const started = new Set();
  const head = $(".site-head");
  const menuBtn = $(".menu-btn");
  let current = "";

  function setMenu(open) {
    head.classList.toggle("open", open);
    menuBtn.setAttribute("aria-expanded", String(open));
  }

  function showView(key, scroll) {
    const k = ORDER.includes(key) ? key : "home";
    current = k;
    ORDER.forEach((v) => {
      document.getElementById(`v-${v}`).hidden = v !== k;
    });
    $$(".menu [data-v]").forEach((b) => b.setAttribute("aria-current", b.dataset.v === k ? "page" : "false"));
    document.title = TITLES[k];
    if (!started.has(k)) {
      started.add(k);
      if (VIEWS[k]) {
        VIEWS[k]();
      }
    }
    if (scroll) {
      window.scrollTo(0, 0);
    }
  }

  function go(key, jump) {
    const k = ORDER.includes(key) ? key : "home";
    if (k !== current) {
      try {
        const url = k === "home" ? window.location.pathname + window.location.search : `#${k}`;
        window.history.pushState(null, "", url);
      } catch {
        /* sandboxed previews may block history changes; the view still switches */
      }
      showView(k, !jump);
    }
    setMenu(false);
    if (jump) {
      requestAnimationFrame(() => {
        const target = document.getElementById(jump);
        if (target) {
          scrollToEl(target);
        }
      });
    }
  }

  document.addEventListener("click", (e) => {
    if (e.target.closest(".menu-btn")) {
      setMenu(!head.classList.contains("open"));
      return;
    }
    const qa = e.target.closest("[data-qa]");
    if (qa) {
      const open = qa.dataset.qa === "open";
      $$("details", qa.closest(".ref")).forEach((d) => {
        d.open = open;
      });
      return;
    }
    const b = e.target.closest("[data-v], [data-jump]");
    if (b) {
      if (b.dataset.v) {
        go(b.dataset.v, b.dataset.jump);
      } else {
        setMenu(false);
        scrollToEl(document.getElementById(b.dataset.jump));
      }
      return;
    }
    if (head.classList.contains("open") && !e.target.closest(".site-head")) {
      setMenu(false);
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && head.classList.contains("open")) {
      setMenu(false);
      menuBtn.focus();
    }
  });
  window.addEventListener("popstate", () => {
    const h = window.location.hash.slice(1);
    if (!h || ORDER.includes(h)) {
      showView(h || "home", false);
    }
  });
  showView(window.location.hash.slice(1), false);
"""


def header_html():
    items = "".join(
        f'<button type="button" data-v="{k}" style="--c: var(--{c})" aria-current="false"><span class="bul">{b}</span>'
        f'<span class="m-t">{label}<small>{sub}</small></span></button>'
        for k, _, _, c, b, label, sub, _ in VIEWS
    )
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="site-head">
  <div class="wrap sh-in">
    <button type="button" class="brand" data-v="home" aria-label="{SITE_NAME}, home"><span class="brand-mark" aria-hidden="true"></span>{SITE_NAME}</button>
    <nav class="menu" id="menu" aria-label="Main">
      <button type="button" data-v="home" class="m-home" aria-current="false"><span class="m-t">Start here<small>overview and study route</small></span></button>
      {items}
      <button type="button" data-jump="about" class="m-about"><span class="m-t">About<small>the author</small></span></button>
    </nav>
    <button type="button" class="menu-btn" aria-expanded="false" aria-controls="menu"><span class="mb-icon" aria-hidden="true"></span>Menu</button>
  </div>
</header>"""


def footer_html():
    lines = "".join(
        f'<li><button type="button" data-v="{k}"><span class="bul" style="--c: var(--{c})">{b}</span>{label}</button></li>'
        for k, _, _, c, b, label, _, _ in VIEWS
    )
    year = date.today().year
    return f"""<footer class="site-foot" id="about">
  <div class="wrap sf-grid">
    <div class="sf-col">
      <div class="sf-brand"><span class="brand-mark" aria-hidden="true"></span>{SITE_NAME}</div>
      <p>An interactive reference for full-stack engineers preparing for interviews: how Node.js and Python actually run your code, drawn as a transit map you can step through.</p>
    </div>
    <nav class="sf-col sf-lines" aria-label="Lines">
      <h2>The lines</h2>
      <ul>{lines}</ul>
    </nav>
    <div class="sf-col sf-author">
      <h2>About the author</h2>
      <p><b>{AUTHOR["name"]}</b> is a senior software engineer with 15+ years of building secure ML, cloud, data and full-stack systems, working remote-first from Cluj-Napoca, Romania. He built {SITE_NAME} as a reference for anyone preparing for a full-stack engineering role.</p>
      <p class="sf-links">
        <a class="primary" href="{AUTHOR["url"]}" rel="author">sergiuvlad.com</a>
        <a href="{AUTHOR["linkedin"]}" rel="me noopener" target="_blank">LinkedIn</a>
        <a href="mailto:{AUTHOR["email"]}">{AUTHOR["email"]}</a>
      </p>
    </div>
  </div>
  <div class="wrap sf-bottom">
    <span>&copy; {year} {AUTHOR["name"]}. All outputs checked against Node.js 22 and CPython 3.12.</span>
    <span>Spotted a mistake? <a href="mailto:{AUTHOR["email"]}?subject=Runtime%20lines">Let me know</a>.</span>
  </div>
</footer>"""


def head_meta():
    og_image = f"{SITE_URL}/og.png" if SITE_URL else "/og.png"
    canonical = (
        f'<link rel="canonical" href="{SITE_URL}/">\n<meta property="og:url" content="{SITE_URL}/">\n'
        if SITE_URL
        else ""
    )
    ld = {
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": SITE_NAME,
        "headline": SITE_TITLE,
        "description": SITE_DESC,
        "learningResourceType": "Interactive explainer",
        "educationalLevel": "Intermediate",
        "inLanguage": "en",
        "about": [
            "Node.js event loop",
            "Python memory management",
            "Python GIL",
            "JavaScript types",
            "Python types",
        ],
        "author": {
            "@type": "Person",
            "name": AUTHOR["name"],
            "url": AUTHOR["url"],
            "jobTitle": "Senior Software Engineer",
            "sameAs": [AUTHOR["linkedin"]],
        },
    }
    if SITE_URL:
        ld["url"] = f"{SITE_URL}/"
    return f"""<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{SITE_DESC}">
<meta name="author" content="{AUTHOR["name"]}">
<meta name="theme-color" content="{token("paper")}" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0c1322" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
{canonical}<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{SITE_TITLE}">
<meta property="og:description" content="{SITE_DESC}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{SITE_NAME}: five coloured lines for the event loop, memory, the GIL and types">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{SITE_TITLE}">
<meta name="twitter:description" content="{SITE_DESC}">
<meta name="twitter:image" content="{og_image}">
<script type="application/ld+json">{json.dumps(ld)}</script>
{FONTS}"""


def favicon_svg():
    colours = [token(c) for c in ("green", "blue", "red", "orange", "purple")]
    circ = 2 * 3.14159265 * 22
    seg = circ / 5
    arcs = "".join(
        f'<circle cx="32" cy="32" r="22" stroke="{c}" stroke-dasharray="{seg - 1.5:.2f} {circ - seg + 1.5:.2f}" stroke-dashoffset="{-i * seg:.2f}"/>'
        for i, c in enumerate(colours)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<circle cx="32" cy="32" r="30" fill="#ffffff"/>'
        f'<g fill="none" stroke-width="11" transform="rotate(-90 32 32)">{arcs}</g></svg>\n'
    )


def not_found_html():
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Not found | {SITE_NAME}</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>
  body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #eef2f6; color: #16202e;
    font: 17px/1.5 system-ui, sans-serif; text-align: center; padding: 24px; }}
  @media (prefers-color-scheme: dark) {{ body {{ background: #0c1322; color: #e6edf5; }} }}
  h1 {{ font-size: 32px; margin: 16px 0 8px; }}
  a {{ display: inline-block; margin-top: 18px; padding: 10px 18px; border-radius: 999px; background: currentColor; }}
  a span {{ color: #eef2f6; font-weight: 700; }}
  @media (prefers-color-scheme: dark) {{ a span {{ color: #0c1322; }} }}
</style>
</head>
<body>
<main>
  <img src="/favicon.svg" width="64" height="64" alt="">
  <h1>This stop isn&rsquo;t on the map</h1>
  <p>The page you were looking for doesn&rsquo;t exist.</p>
  <a href="/"><span>Back to {SITE_NAME}</span></a>
</main>
</body>
</html>
"""


def main():
    css_parts, bodies, scripts = [], [], []
    home = (SRC / "partials" / "home.html").read_text()
    bodies.append(f'<div class="view" id="v-home" hidden>{home}</div>')
    for n, (key, page, p, color, bul, label, sub, _) in enumerate(VIEWS):
        css, body, js = extract(page)
        css, body, js = prefix_ids([css, body, js], p)
        css_parts.append(scope_css(css, f"#v-{key}"))
        jump = f'<p class="hero-jump"><button type="button" class="jump" data-jump="{p}ref">Interview questions for this line</button></p>\n    '
        at = body.index('<nav class="route"')
        body = body[:at] + jump + body[at:]
        ref = (SRC / "reference" / f"{key}.html").read_text()
        foot = body.rfind('<p class="foot">')
        body = body[:foot] + ref + body[foot:] if foot >= 0 else body + ref
        nk, _, _, ncolor, nbul, nlabel, _, _ = VIEWS[(n + 1) % len(VIEWS)]
        nxt = (
            f'<nav class="nextline" aria-label="Next line"><button type="button" data-v="{nk}" style="--c: var(--{ncolor})">'
            f'<span class="bul" style="--c: var(--{ncolor})">{nbul}</span><span><small>Next line</small><b>{nlabel}</b></span></button></nav>'
        )
        bodies.append(f'<div class="view" id="v-{key}" hidden>{body}{nxt}</div>')
        scripts.append(f'  VIEWS["{key}"] = () => {{\n{js}  }};\n')
    page_js = "".join(scripts)
    order = ["home"] + [v[0] for v in VIEWS]
    titles = {"home": SITE_TITLE, **{v[0]: f"{v[7]} | {SITE_NAME}" for v in VIEWS}}
    router = ROUTER % (json.dumps(order), json.dumps(titles))
    lib = (LIB / "shared.js").read_text() + "\n" + (LIB / "mem.js").read_text()
    lib = shake(lib, page_js + router)
    shell_css = (SRC / "partials" / "shell.css").read_text()
    styles = expand_dark(
        (LIB / "shared.css").read_text() + (LIB / "mem.css").read_text() + shell_css
    ) + "".join(css_parts)
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
{head_meta()}
<title>{SITE_TITLE}</title>
<style>
{styles}
</style>
</head>
<body>
{header_html()}
<main class="wrap" id="main" tabindex="-1">
{"".join(bodies)}
</main>
{footer_html()}
<script>
(() => {{
  "use strict";
{lib}
  const VIEWS = {{}};
{page_js}{router}}})();
</script>
</body>
</html>
"""
    leftovers = re.findall(
        r"@(?:HEAD|SHARED_CSS|MEM_CSS|SHARED_JS|MEM_JS|OPS_JSON|USES_JSON)@|@dark-(?:begin|end)",
        html,
    )
    assert not leftovers, leftovers
    script = html.split("<script>\n(() =>", 1)[1].rsplit("</script>", 1)[0]
    assert "</script" not in script, "nested </script> inside inline JS"
    ids = re.findall(r'(?<![\w-])id="([^"$]+)"', html.split("<script>\n(() =>")[0])
    dup = sorted({i for i in ids if ids.count(i) > 1})
    assert not dup, dup
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(html)
    (OUT / "favicon.svg").write_text(favicon_svg())
    (OUT / "404.html").write_text(not_found_html())
    robots = "User-agent: *\nAllow: /\n"
    if SITE_URL:
        robots += f"Sitemap: {SITE_URL}/sitemap.xml\n"
        (OUT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"  <url><loc>{SITE_URL}/</loc><lastmod>{date.today().isoformat()}</lastmod></url>\n"
            "</urlset>\n"
        )
    (OUT / "robots.txt").write_text(robots)
    print(f"public/index.html {len(html.encode()) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
