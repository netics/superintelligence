"""Trace Python's binary-operator protocol with real objects and emit JSON."""

from pathlib import Path
import json
import operator

VALUES = [
    ("7", 7),
    ("2.5", 2.5),
    ("True", True),
    ('"ab"', "ab"),
    ("[1, 2]", [1, 2]),
    ("(1, 2)", (1, 2)),
    ('{"k": 1}', {"k": 1}),
    ("{1, 2}", {1, 2}),
    ("None", None),
]
ARITH = {
    "+": ("__add__", "__radd__", operator.add),
    "*": ("__mul__", "__rmul__", operator.mul),
}
CMP = {"==": ("__eq__", "__eq__", operator.eq), "<": ("__lt__", "__gt__", operator.lt)}


def tn(x):
    return type(x).__name__


def call(obj, name, other):
    """Call type(obj).name(obj, other) like the interpreter does."""
    meth = getattr(type(obj), name, None)
    if meth is None:
        return {"call": f"{tn(obj)}.{name}", "kind": "missing"}
    try:
        res = meth(obj, other)
    except TypeError as exc:
        return {"call": f"{tn(obj)}.{name}", "kind": "raise", "msg": str(exc)}
    if res is NotImplemented:
        return {"call": f"{tn(obj)}.{name}", "kind": "ni"}
    return {
        "call": f"{tn(obj)}.{name}",
        "kind": "ok",
        "repr": repr(res),
        "type": tn(res),
    }


def trace(a, op, b):
    steps = []
    if op in ARITH:
        fwd, ref, fn = ARITH[op]
        order = [(a, fwd, b, "left")]
        if type(a) is not type(b):
            sub_first = issubclass(type(b), type(a)) and getattr(
                type(b), ref, None
            ) is not getattr(type(a), ref, None)
            refl = (b, ref, a, "right")
            order = [refl, order[0]] if sub_first else order + [refl]
    else:
        fwd, ref, fn = CMP[op]
        order = [(a, fwd, b, "left"), (b, ref, a, "right")]
        if type(a) is not type(b) and issubclass(type(b), type(a)):
            order.reverse()
    final = None
    for obj, name, other, side in order:
        st = call(obj, name, other)
        st["side"] = side
        steps.append(st)
        if st["kind"] in ("ok", "raise"):
            break
    try:
        res = fn(a, b)
        final = {"kind": "ok", "repr": repr(res), "type": tn(res)}
    except TypeError as exc:
        final = {"kind": "error", "msg": f"TypeError: {exc}"}
    last = steps[-1]
    if final["kind"] == "ok" and last["kind"] != "ok":
        assert op == "==", (a, op, b)  # identity fallback only exists for ==
        steps.append(
            {
                "kind": "fallback",
                "call": "identity check (a is b)",
                "repr": final["repr"],
            }
        )
    if final["kind"] == "ok" and last["kind"] == "ok":
        assert last["repr"] == final["repr"], (a, op, b, last, final)
    if final["kind"] == "error":
        assert last["kind"] in ("raise", "ni", "missing"), (a, op, b)
    return {"steps": steps, "final": final}


out = {"values": [{"src": s, "type": tn(v)} for s, v in VALUES], "ops": {}}
for op in list(ARITH) + list(CMP):
    table = []
    for _, a in VALUES:
        row = []
        for _, b in VALUES:
            row.append(trace(a, op, b))
        table.append(row)
    out["ops"][op] = table

with open(Path(__file__).resolve().parents[1] / "src" / "data" / "ops.json", "w") as fh:
    json.dump(out, fh, separators=(",", ":"))
print("ok", len(json.dumps(out)), "bytes")
t = out["ops"]
for i, j, op in [
    (0, 1, "+"),
    (3, 0, "+"),
    (0, 3, "*"),
    (1, 3, "*"),
    (0, 2, "=="),
    (0, 3, "=="),
    (8, 8, "<"),
    (7, 7, "<"),
]:
    print(VALUES[i][0], op, VALUES[j][0], "->", json.dumps(t[op][i][j]))
