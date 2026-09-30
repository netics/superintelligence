"""Run and black-check the 'where you'd use it' snippets, then emit uses.json."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNIPS = ROOT / "src" / "snippets" / "python-types"
ORDER = ["bool", "int", "float", "complex", "str", "bytes", "bytearray"]
ORDER += ["tuple", "list", "range", "frozenset", "set", "dict", "NoneType"]

subprocess.run(["black", "--check", "-q", str(SNIPS)], check=True)
out = {}
for t in ORDER:
    path = SNIPS / f"{t}.py"
    run = subprocess.run(
        [sys.executable, str(path)], capture_output=True, text=True, check=True
    )
    print(f"--- {t}\n{run.stdout}", end="")
    out[t] = path.read_text().rstrip("\n")
(ROOT / "src" / "data" / "uses.json").write_text(json.dumps(out, ensure_ascii=False))
print("uses.json written")
