"""End-to-end checks for the built site: every explorer, the shell and the CSP.

Serves public/ with the headers from vercel.json, drives Chromium with Playwright,
and fails if any expected output differs or the console reports an error.

Usage: python3 tests/test_site.py   (needs: pip install playwright && playwright install chromium)
"""

import json
import re
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from serve import make_server  # noqa: E402

SHOTS = ROOT / "tests" / "screenshots"
FAILS = []


def check(name, ok, detail=""):
    print(
        ("ok   " if ok else "FAIL ")
        + name
        + (f"  {detail}" if detail and not ok else "")
    )
    if not ok:
        FAILS.append(name)


def step_all(page, dock, limit=80):
    nxt = page.locator(f"{dock} [data-a=next]")
    n = 0
    while n < limit and nxt.is_enabled():
        nxt.click()
        page.wait_for_timeout(40)
        n += 1


def lines(page, sel):
    return [t.strip() for t in page.locator(f"{sel} li").all_inner_texts()]


def go(page, key):
    page.click(f".menu [data-v='{key}']")
    page.wait_for_timeout(400)


def open_page(p, url, width, height, reduced=True, dark=False, locale="en-US"):
    browser = p.chromium.launch()
    ctx = browser.new_context(
        viewport={"width": width, "height": height},
        reduced_motion="reduce" if reduced else "no-preference",
        color_scheme="dark" if dark else "light",
        locale=locale,
    )
    page = ctx.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url)
    page.wait_for_timeout(700)
    return browser, page, errors


def explorers(page):
    node = [
        ["A", "E", "D", "C", "B"],
        ["1: start", "2: inside greet", "3: end", "4: hello Ada"],
        ["1: file read", "2: immediate", "3: timeout"],
        ["loop done at 100 ms", "timer (wanted 10 ms) 106"],
        ["tick 1", "promise 1", "promise 2", "tick 2"],
    ]
    go(page, "node")
    for i, want in enumerate(node):
        page.click(f"#n-route .stn[data-i='{i}']")
        step_all(page, "#n-dock")
        check(
            f"node scenario {i + 1}",
            lines(page, "#n-out") == want,
            lines(page, "#n-out"),
        )
    go(page, "memory")
    for i, want in [(2, ["2"]), (3, ["True False True"])]:
        page.click(f"#m-scSeg button[data-i='{i}']")
        step_all(page, "#m-dock")
        check(
            f"memory scenario {i + 1}",
            lines(page, "#m-out") == want,
            lines(page, "#m-out"),
        )
    go(page, "gil")
    walls = {}
    for w in range(3):
        page.click(f"#g-wlSeg button[data-i='{w}']")
        for m in range(3):
            page.click(f"#g-mdSeg button[data-i='{m}']")
            page.click("#g-simPlay")
            page.wait_for_timeout(120)
            walls[(w, m)] = page.inner_text("#g-simStatus")
    want = {(0, 0): "160", (0, 1): "42.8", (0, 2): "50", (1, 0): "48", (1, 1): "42.5"}
    want.update({(1, 2): "52", (2, 0): "72", (2, 1): "64.2", (2, 2): "70"})
    bad = {k: v for k, v in walls.items() if want[k] not in v}
    check("gil wall-clock times", not bad, bad)
    step_all(page, "#g-raceDock")
    race = lines(page, "#g-raceOut")
    page.click("#g-raceSeg button[data-i='1']")
    step_all(page, "#g-raceDock")
    check(
        "gil race 130 / 180", race == ["130"] and lines(page, "#g-raceOut") == ["180"]
    )
    go(page, "js-types")
    page.click("#j-jxAll")
    page.wait_for_timeout(300)
    arr = page.eval_on_selector_all(
        "#j-dests .dest", "ls => ls.map(l => l.querySelectorAll('.arr').length)"
    )
    check("typeof arrivals", arr == [1, 1, 3, 1, 1, 1, 5, 2], arr)
    step_all(page, "#j-cpDock")
    check(
        "copy.js output",
        lines(page, "#j-cpOut")
        == ["10 20 Bob [ 'dev', 'ops' ] [ 'dev', 'ops', 'qa' ]"],
    )
    for op in ["==", "===", "is"]:
        page.click(f"#j-mxSeg button[data-op='{op}']")
        cells = page.eval_on_selector_all(
            "#j-eqMx button[data-i]", "bs => bs.map(b => b.dataset.r === '1')"
        )
        native = page.evaluate(
            """(op) => {
              const V = [() => 0, () => 1, () => -0, () => "", () => "0", () => "1", () => "abc", () => true,
                () => false, () => null, () => undefined, () => NaN, () => [], () => [0], () => ({})];
              const f = { "==": (a, b) => a == b, "===": (a, b) => a === b, is: Object.is }[op];
              return V.flatMap((a) => V.map((b) => f(a(), b())));
            }""",
            op,
        )
        check(f"{op} matrix matches the engine", cells == native)
    go(page, "py-types")
    uses = json.loads((ROOT / "src" / "data" / "uses.json").read_text())
    bad = []
    for t, code in uses.items():
        page.click(f"#p-tmap .tst[data-t='{t}']")
        if page.inner_text("#p-tdetail .td-code").rstrip("\n") != code:
            bad.append(t)
    check("type usage snippets", not bad, bad)
    step_all(page, "#p-iaDock")
    check(
        "+= stepper ends in TypeError",
        "does not support item assignment" in " ".join(lines(page, "#p-iaOut")),
    )
    step_all(page, "#p-hsDock")
    check(
        "dict ends with two keys",
        page.inner_text("#p-hsRepr") == "d == {1: 'float one', '1': 'str one'}",
    )


def languages(p, url):
    browser, page, errors = open_page(p, url + "gil", 1440, 900)
    check(
        "english page is lang=en",
        page.evaluate("document.documentElement.lang") == "en",
    )
    page.click(".lang a[hreflang='ro']")
    page.wait_for_timeout(700)
    check(
        "switcher opens the same line in Romanian",
        page.evaluate("location.pathname") == "/ro/gil" and page.is_visible("#v-gil"),
        page.url,
    )
    check(
        "romanian page is lang=ro",
        page.evaluate("document.documentElement.lang") == "ro",
    )
    check(
        "romanian page is translated",
        "Întrebări de interviu" in page.inner_text("#g-ref"),
    )
    page.goto(url)
    page.wait_for_timeout(700)
    check("the language choice is remembered", "/ro" in page.url, page.url)
    page.click(".lang a[hreflang='en']")
    page.wait_for_timeout(700)
    check(
        "switching back to English sticks",
        not page.url.rstrip("/").endswith("/ro"),
        page.url,
    )
    check("no console errors while switching language", not errors, errors[:3])
    browser.close()
    browser, page, errors = open_page(p, url, 1440, 900, locale="ro-RO")
    check("romanian browsers start in Romanian", "/ro" in page.url, page.url)
    browser.close()


def urls(p, url):
    for path, view, lang in (
        ("gil", "gil", "en"),
        ("ro/js-types", "js-types", "ro"),
        ("ro", "home", "ro"),
    ):
        browser, page, errors = open_page(p, url + path, 1440, 900)
        check(
            f"/{path} opens its own page",
            page.is_visible(f"#v-{view}")
            and page.evaluate("document.documentElement.lang") == lang
            and page.evaluate(
                "document.querySelector('link[rel=canonical]').href"
            ).endswith("/" + path),
        )
        check(f"no console errors on /{path}", not errors, errors[:3])
        browser.close()
    browser, page, errors = open_page(p, url + "#memory", 1440, 900)
    check(
        "old #hash links move to the line's URL",
        page.evaluate("location.pathname") == "/memory"
        and page.is_visible("#v-memory"),
        page.url,
    )
    browser.close()


def files():
    public = ROOT / "public"
    pages = [public / "index.html", public / "ro" / "index.html"]
    pages += [
        public / f"{k}.html" for k in ("node", "memory", "gil", "js-types", "py-types")
    ]
    pages += [
        public / "ro" / f"{k}.html"
        for k in ("node", "memory", "gil", "js-types", "py-types")
    ]
    bad = []
    for f in pages:
        html = f.read_text()
        ld = re.search(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S
        )
        og = re.search(
            r'<meta property="og:image" content="https://[^/]+(/[^"]+)"', html
        )
        md = re.search(
            r'<link rel="alternate" type="text/markdown" href="https://[^/]+(/[^"]+)"',
            html,
        )
        ok = (
            ld
            and json.loads(ld.group(1).replace("<\\/", "</"))
            and og
            and (public / og.group(1).lstrip("/")).exists()
            and md
            and (public / md.group(1).lstrip("/")).exists()
            and html.count('rel="alternate" hreflang=') == 3
        )
        if not ok:
            bad.append(f.name)
    check(
        "every page has JSON-LD, hreflang, an OG image and a Markdown twin",
        not bad,
        bad,
    )
    for name in (
        "llms.txt",
        "llms-full.txt",
        "ro/llms-full.txt",
        "sitemap.xml",
        "robots.txt",
    ):
        check(f"{name} exists", (public / name).stat().st_size > 200)


def shell(page, base=""):
    check(
        "home is the default view",
        page.is_visible("#v-home") and not page.is_visible("#v-node"),
    )
    page.click("#v-home .lcard:nth-child(3) [data-jump='g-ref']")
    page.wait_for_timeout(500)
    top = page.evaluate("document.getElementById('g-ref').getBoundingClientRect().top")
    check(
        "card jumps to GIL interview questions",
        page.is_visible("#v-gil") and 0 <= top < 200,
        top,
    )
    check(
        "the URL follows the view", page.evaluate("location.pathname") == base + "/gil"
    )
    page.click("#g-ref [data-qa='open']")
    opened = page.eval_on_selector_all("#g-ref details", "ds => ds.every(d => d.open)")
    check("open all interview answers", opened)
    go(page, "js-types")
    page.go_back()
    page.wait_for_timeout(300)
    check("back button returns to the previous line", page.is_visible("#v-gil"))
    check(
        "footer credits the author", "sergiuvlad.com" in page.inner_text(".site-foot")
    )


with make_server(8765) as httpd:
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:8765/"
    with sync_playwright() as p:
        for lang, path in (("en", ""), ("ro", "ro/")):
            print(f"-- {lang}")
            browser, page, errors = open_page(p, url + path, 1440, 900)
            check("page title", page.title().startswith("Runtime lines"))
            shell(page, "" if lang == "en" else "/" + lang)
            explorers(page)
            check(
                "no console errors or CSP violations (desktop)", not errors, errors[:3]
            )
            browser.close()
        print("-- languages")
        languages(p, url)
        print("-- urls and files")
        urls(p, url)
        files()
        print("-- mobile")
        browser, page, errors = open_page(p, url, 390, 844, reduced=False)
        page.click(".menu-btn")
        check("mobile menu opens", page.is_visible("#menu"))
        page.click(".menu [data-v='py-types']")
        page.wait_for_timeout(500)
        check(
            "mobile menu closes after picking a line",
            not page.is_visible("#menu") and page.is_visible("#v-py-types"),
        )
        check(
            "no horizontal overflow on mobile",
            page.evaluate("document.documentElement.scrollWidth") <= 390,
        )
        check("no console errors or CSP violations (mobile)", not errors, errors[:3])
        browser.close()
    httpd.shutdown()

print(f"\n{len(FAILS)} failure(s)" if FAILS else "\nall checks passed")
sys.exit(1 if FAILS else 0)
