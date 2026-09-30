"""Render public/og.png (1200x630) and public/apple-touch-icon.png with Playwright.

Usage: python3 scripts/make_images.py   (needs: pip install playwright && playwright install chromium)
"""

import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "src" / "lib" / "shared.css").read_text()


def tok(name):
    return re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{3,8}})", CSS).group(1)


LINES = [
    ("green", "N", "Node event loop"),
    ("blue", "M", "Python memory"),
    ("red", "G", "The GIL"),
    ("orange", "J", "JavaScript types"),
    ("purple", "P", "Python types"),
]
ring = ", ".join(
    f"{tok(c)} {i * 72}deg {(i + 1) * 72}deg" for i, (c, _, _) in enumerate(LINES)
)
pills = "".join(
    f'<div class="pill"><span style="background:{tok(c)}">{b}</span>{label}</div>'
    for c, b, label in LINES
)
tracks = "".join(
    f'<div class="track" style="background:{tok(c)};top:{318 + i * 26}px"></div>'
    for i, (c, _, _) in enumerate(LINES)
)
OG = f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Overpass:wght@400..900&display=swap">
<style>
  body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; background: {tok("paper")};
    font-family: Overpass, system-ui, sans-serif; color: {tok("ink")}; position: relative; }}
  .ring {{ position: absolute; left: 72px; top: 64px; width: 84px; height: 84px; border-radius: 50%;
    background: conic-gradient({ring}); }}
  .ring::after {{ content: ""; position: absolute; inset: 20px; border-radius: 50%; background: {tok("paper")}; }}
  .brand {{ position: absolute; left: 176px; top: 78px; font-size: 44px; font-weight: 900; letter-spacing: -0.02em; }}
  h1 {{ position: absolute; left: 72px; top: 170px; width: 1000px; margin: 0; font-size: 66px; line-height: 1.02;
    letter-spacing: -0.03em; font-weight: 900; }}
  .track {{ position: absolute; left: 0; right: 0; height: 10px; opacity: 0.9; }}
  .pills {{ position: absolute; left: 72px; right: 40px; bottom: 56px; display: flex; gap: 10px; }}
  .pill {{ display: flex; align-items: center; gap: 9px; padding: 6px 15px 6px 6px; border-radius: 999px;
    background: #fff; font-size: 19px; font-weight: 800; white-space: nowrap; box-shadow: 0 4px 14px rgba(12, 19, 34, 0.12); }}
  .pill span {{ display: grid; place-items: center; width: 32px; height: 32px; border-radius: 50%; color: #fff;
    font-size: 15px; font-weight: 900; }}
  .by {{ position: absolute; right: 72px; top: 92px; font-size: 22px; font-weight: 700; color: {tok("ink-2")}; }}
</style></head><body>
<div class="ring"></div><div class="brand">Runtime lines</div><div class="by">by Sergiu Vlad</div>
<h1>How Node.js and Python actually run your code</h1>
{tracks}
<div class="pills">{pills}</div>
</body></html>"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 630})
    page.set_content(OG, wait_until="networkidle")
    page.wait_for_timeout(300)
    page.screenshot(path=str(ROOT / "public" / "og.png"))
    icon = (ROOT / "public" / "favicon.svg").read_text()
    page.set_viewport_size({"width": 180, "height": 180})
    page.set_content(
        "<html><body style='margin:0;background:#fff;display:grid;place-items:center;height:180px'>"
        f"<div style='width:150px;height:150px'>{icon.replace('<svg ', '<svg width=150 height=150 ')}</div></body></html>"
    )
    page.screenshot(path=str(ROOT / "public" / "apple-touch-icon.png"))
    browser.close()
print("public/og.png and public/apple-touch-icon.png written")
