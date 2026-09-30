"""Render the Open Graph images (1200x630) for every page and language, and the touch icon.

Reads the built pages in public/, so run the build first. Writes public/og/<lang>/<view>.png,
public/og.png (the English home image, kept for old links) and public/apple-touch-icon.png.

Usage: python3 scripts/make_images.py   (needs: pip install playwright && playwright install chromium)
"""

import html as htmllib
import re
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402
import seo  # noqa: E402

CSS = (ROOT / "src" / "lib" / "shared.css").read_text()
PUBLIC = ROOT / "public"
DOMAIN = build.SITE_URL.split("//")[-1]
COUNT = {
    "en": lambda n: f"{n} interview questions",
    "ro": lambda n: (
        f"{n} de întrebări de interviu"
        if n % 100 >= 20 or n % 100 == 0
        else f"{n} întrebări de interviu"
    ),
}
TAG = {"en": "Interactive explorer", "ro": "Explicație interactivă"}
LINES = {"en": "5 lines", "ro": "5 linii"}


def tok(name):
    return re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{3,8}})", CSS).group(1)


def esc(s):
    return htmllib.escape(s, quote=False)


def page_data(lang, view):
    html = build.page_file(lang, view).read_text()
    labels = {}
    for k, _, _, c, b, _, _, _ in build.VIEWS:
        m = re.search(
            rf'data-v="{k}"[^>]*>.*?<span class="m-t">(.*?)<small>', html, re.S
        )
        labels[k] = (c, b, seo.text(m.group(1)))
    h1 = seo.text(
        re.search(r"<h1\b[^>]*>(.*?)</h1>", seo.element(html, f"v-{view}"), re.S).group(
            1
        )
    )
    desc = seo.meta(html, "description")
    prefix = {v[0]: v[2] for v in build.VIEWS}
    questions = len(seo.qa(html, prefix[view])) if view != "home" else 0
    return labels, h1, desc, questions


def card(lang, view):
    labels, h1, desc, questions = page_data(lang, view)
    ring = ", ".join(
        f"{tok(c)} {i * 72}deg {(i + 1) * 72}deg"
        for i, (c, _, _) in enumerate(labels.values())
    )
    base = f"""
  body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; background: {tok("paper")};
    font-family: Overpass, system-ui, sans-serif; color: {tok("ink")}; position: relative; }}
  .ring {{ position: absolute; left: 72px; top: 60px; width: 64px; height: 64px; border-radius: 50%;
    background: conic-gradient({ring}); }}
  .ring::after {{ content: ""; position: absolute; inset: 15px; border-radius: 50%; background: {tok("paper")}; }}
  .brand {{ position: absolute; left: 152px; top: 70px; font-size: 36px; font-weight: 900; letter-spacing: -0.02em; }}
  .domain {{ position: absolute; right: 72px; top: 78px; font-size: 24px; font-weight: 800; color: {tok("ink-2")}; }}
  .track {{ position: absolute; left: 0; right: 0; height: 10px; opacity: 0.9; }}
  .pill {{ display: flex; align-items: center; gap: 9px; padding: 6px 15px 6px 6px; border-radius: 999px;
    background: #fff; font-size: 19px; font-weight: 800; white-space: nowrap; box-shadow: 0 4px 14px rgba(12, 19, 34, 0.12); }}
  .pill span {{ display: grid; place-items: center; width: 32px; height: 32px; border-radius: 50%; color: #fff;
    font-size: 15px; font-weight: 900; }}"""
    head = (
        '<div class="ring"></div><div class="brand">Runtime lines</div>'
        f'<div class="domain">{DOMAIN}</div>'
    )
    if view == "home":
        tracks = "".join(
            f'<div class="track" style="background:{tok(c)};top:{330 + i * 26}px"></div>'
            for i, (c, _, _) in enumerate(labels.values())
        )
        pills = "".join(
            f'<div class="pill"><span style="background:{tok(c)}">{b}</span>{esc(n)}</div>'
            for c, b, n in labels.values()
        )
        style = (
            base
            + """
  h1 { position: absolute; left: 72px; top: 160px; width: 1060px; margin: 0; font-size: 64px; line-height: 1.04;
    letter-spacing: -0.03em; font-weight: 900; }
  .pills { position: absolute; left: 72px; right: 40px; bottom: 52px; display: flex; flex-wrap: wrap; gap: 10px; }"""
        )
        body = f'{head}<h1>{esc(h1)}</h1>{tracks}<div class="pills">{pills}</div>'
    else:
        c, b, name = labels[view]
        color = tok(c)
        style = base + f"""
  .main {{ position: absolute; left: 72px; top: 170px; width: 1056px; display: flex; flex-direction: column; gap: 24px; }}
  .line {{ display: flex; align-items: center; gap: 16px;
    font-size: 30px; font-weight: 850; color: {color}; }}
  .bul {{ display: grid; place-items: center; width: 56px; height: 56px; border-radius: 50%; background: {color};
    color: #fff; font-size: 28px; font-weight: 900; }}
  h1 {{ margin: 0; font-size: 60px; line-height: 1.05;
    letter-spacing: -0.03em; font-weight: 900; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
  .desc {{ width: 1000px; margin: 0; font-size: 25px; line-height: 1.4;
    color: {tok("ink-2")}; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
  .foot {{ position: absolute; left: 72px; bottom: 58px; display: flex; gap: 12px; }}
  .track {{ bottom: 0; height: 18px; background: {color}; }}"""
        body = (
            f'{head}<div class="main"><div class="line"><span class="bul">{b}</span>{esc(name)}</div>'
            f'<h1>{esc(h1)}</h1><p class="desc">{esc(desc)}</p></div>'
            f'<div class="foot"><div class="pill"><span style="background:{color}">?</span>{COUNT[lang](questions)}</div>'
            f'<div class="pill"><span style="background:{color}">&#9654;</span>{TAG[lang]}</div></div>'
            '<div class="track"></div>'
        )
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Overpass:wght@400..900&display=swap">'
        f"<style>{style}</style></head><body>{body}</body></html>"
    )


def main():
    views = ["home"] + [v[0] for v in build.VIEWS]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 630})
        for lang, _ in build.LANGS:
            for view in views:
                out = PUBLIC / build.og_path(lang, view).lstrip("/")
                out.parent.mkdir(parents=True, exist_ok=True)
                page.set_content(card(lang, view), wait_until="networkidle")
                page.evaluate("document.fonts.ready")
                page.wait_for_timeout(150)
                page.screenshot(path=str(out))
        shutil.copyfile(PUBLIC / "og" / "en" / "home.png", PUBLIC / "og.png")
        icon = (PUBLIC / "favicon.svg").read_text()
        page.set_viewport_size({"width": 180, "height": 180})
        page.set_content(
            "<html><body style='margin:0;background:#fff;display:grid;place-items:center;height:180px'>"
            f"<div style='width:150px;height:150px'>{icon.replace('<svg ', '<svg width=150 height=150 ')}</div></body></html>"
        )
        page.screenshot(path=str(PUBLIC / "apple-touch-icon.png"))
        browser.close()
    print(
        f"{len(views) * len(build.LANGS)} Open Graph images, og.png and apple-touch-icon.png written"
    )


if __name__ == "__main__":
    main()
