"""Copy the inline script out of public/index.html so ESLint can check it."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

html = (ROOT / "public" / "index.html").read_text()
scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
(ROOT / ".cache").mkdir(exist_ok=True)
(ROOT / ".cache" / "site.js").write_text("\n".join(scripts))
print(f".cache/site.js: {len(scripts)} inline script block(s)")
