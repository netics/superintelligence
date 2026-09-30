/* ===================== memory map: frames, heap objects, reference wires ===================== */
/* @region TYPE_COLOR typeColor */
const TYPE_COLOR = {
  list: "orange",
  tuple: "yellow",
  dict: "red",
  set: "pink",
  frozenset: "pink",
  str: "green",
  int: "blue",
  float: "teal",
  bool: "purple",
  NoneType: "slate",
  function: "slate",
  module: "slate",
  number: "blue",
  string: "green",
  boolean: "purple",
  Object: "orange",
  Array: "yellow",
  bigint: "teal",
  symbol: "pink",
  undefined: "slate",
  null: "slate",
};
const typeColor = (t) => TYPE_COLOR[t] || "slate";
/* @endregion */

/* @region MemView */
const SVG_NS = "http://www.w3.org/2000/svg";

function roundPath(pts, r = 12) {
  let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
  for (let i = 1; i < pts.length - 1; i += 1) {
    const [x0, y0] = pts[i - 1];
    const [x1, y1] = pts[i];
    const [x2, y2] = pts[i + 1];
    const l1 = Math.hypot(x1 - x0, y1 - y0) || 1;
    const l2 = Math.hypot(x2 - x1, y2 - y1) || 1;
    const rr = Math.min(r, l1 / 2, l2 / 2);
    const ax = x1 - ((x1 - x0) / l1) * rr;
    const ay = y1 - ((y1 - y0) / l1) * rr;
    const bx = x1 + ((x2 - x1) / l2) * rr;
    const by = y1 + ((y2 - y1) / l2) * rr;
    d += `L${ax.toFixed(1)},${ay.toFixed(1)}Q${x1.toFixed(1)},${y1.toFixed(1)} ${bx.toFixed(1)},${by.toFixed(1)}`;
  }
  const [xn, yn] = pts[pts.length - 1];
  return `${d}L${xn.toFixed(1)},${yn.toFixed(1)}`;
}

const ENTRY_DIR = { L: [1, 0], T: [0, 1], B: [0, -1], U: [0, -1] };

function wirePath(w) {
  const dir = ENTRY_DIR[w.side];
  const ex = w.tx - dir[0] * 7;
  const ey = w.ty - dir[1] * 7;
  const { sx, sy, side } = w;
  const dx = ex - sx;
  const dy = ey - sy;
  if (side === "L" && dx - 18 >= Math.abs(dy)) {
    if (Math.abs(dy) < 1.5) {
      return { d: `M${sx.toFixed(1)},${sy.toFixed(1)}L${ex.toFixed(1)},${sy.toFixed(1)}`, dir };
    }
    const run = (dx - Math.abs(dy)) / 2;
    return {
      d: roundPath([
        [sx, sy],
        [sx + run, sy],
        [sx + run + Math.abs(dy), ey],
        [ex, ey],
      ]),
      dir,
    };
  }
  if (side === "T" || side === "B") {
    if (Math.abs(dx) < 1.5) {
      return { d: `M${sx.toFixed(1)},${sy.toFixed(1)}L${sx.toFixed(1)},${ey.toFixed(1)}`, dir };
    }
    const midY = (sy + ey) / 2;
    return {
      d: roundPath([
        [sx, sy],
        [sx, midY],
        [ex, midY],
        [ex, ey],
      ]),
      dir,
    };
  }
  if (side === "U") {
    const low = Math.max(w.sb, w.box.b) + 18;
    return {
      d: roundPath([
        [sx, sy],
        [sx, low],
        [ex, low],
        [ex, ey],
      ]),
      dir,
    };
  }
  const k = clamp(Math.hypot(dx, dy) / 2.2, 34, 140);
  const c1x = sx + k;
  const c1y = sy;
  const c2x = ex - dir[0] * k;
  const c2y = ey - dir[1] * k;
  return {
    d: `M${sx.toFixed(1)},${sy.toFixed(1)}C${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${ex.toFixed(1)},${ey.toFixed(1)}`,
    dir,
  };
}

function headPath(tx, ty, dir) {
  const [ux, uy] = dir;
  const bx = tx - ux * 10;
  const by = ty - uy * 10;
  const px = -uy * 5.5;
  const py = ux * 5.5;
  return `M${tx.toFixed(1)},${ty.toFixed(1)}L${(bx + px).toFixed(1)},${(by + py).toFixed(1)}L${(bx - px).toFixed(1)},${(by - py).toFixed(1)}Z`;
}

function MemView(host, { refc = true, cols = 3, emptyHeap = "Nothing on the heap yet", framesLabel = "" } = {}) {
  host.classList.add("memwrap");
  host.innerHTML = `<div class="mem" style="--cols:${cols}">
      <div class="frames" aria-label="${esc(framesLabel || "Frames")}"></div>
      <div class="heap" aria-label="Heap"></div>
      <svg class="wires" aria-hidden="true"></svg>
    </div>`;
  const mem = $(".mem", host);
  const framesEl = $(".frames", mem);
  const heapEl = $(".heap", mem);
  const svg = $(".wires", mem);
  const groups = new Map();
  let wireCls = {};
  let trackToken = 0;
  let scale = 1;
  let last = null;
  let narrow = false;

  const portHtml = (id, to) => `<span class="port" data-port="${esc(id)}" data-to="${esc(to)}"></span>`;
  const chip = (v, t) => `<span class="vchip" style="--c:var(--${typeColor(t)})">${esc(v)}</span>`;

  function varHtml(fid, v) {
    const val = v.to ? portHtml(`${fid}:${v.n}`, v.to) : chip(v.v, v.t);
    const cls = ["var", v.to ? "is-ref" : "", v.hot ? "is-hot" : ""].join(" ").trim();
    return `<div class="${cls}" data-k="v:${fid}:${esc(v.n)}" data-v="${esc(v.to || v.v)}"><span class="vn">${esc(v.n)}</span>${val}</div>`;
  }

  function frameHtml(f) {
    const body = f.vars.length ? f.vars.map((v) => varHtml(f.id, v)).join("") : '<div class="none">no names yet</div>';
    return `<div class="frame${f.top ? " is-top" : ""}" data-k="f:${f.id}"><div class="frame-h">${esc(f.name)}</div>${body}</div>`;
  }

  function slotHtml(o, it, i) {
    const key = `s:${o.id}:${i}`;
    if (it.to) {
      return `<span class="slot ref" data-k="${key}" data-v="${esc(it.to)}">${portHtml(`${o.id}:${i}`, it.to)}</span>`;
    }
    return `<span class="slot${it.hot ? " is-hot" : ""}" data-k="${key}" data-v="${esc(it.v)}" style="--c:var(--${typeColor(it.t)})">${esc(it.v)}</span>`;
  }

  function propHtml(o, p) {
    const key = `p:${o.id}:${p.k}`;
    const val = p.to ? portHtml(`${o.id}:${p.k}`, p.to) : chip(p.v, p.t);
    return `<div class="prop" data-k="${esc(key)}" data-v="${esc(p.to || p.v)}"><span class="pk">${esc(p.k)}</span>${val}</div>`;
  }

  function objHtml(o) {
    let body;
    if (o.items) {
      body = `<div class="slots">${o.items.map((it, i) => slotHtml(o, it, i)).join("") || '<span class="none">empty</span>'}</div>`;
    } else if (o.props) {
      body = `<div class="props">${o.props.map((p) => propHtml(o, p)).join("") || '<span class="none">empty</span>'}</div>`;
    } else {
      body = `<div class="val" data-k="val:${o.id}" data-v="${esc(o.val)}">${esc(o.val)}</div>`;
    }
    let rc = "";
    if (refc && o.rc !== undefined && o.rc !== null) {
      const label = o.rc === "imm" ? "immortal" : `refs ${o.rc}`;
      rc = `<span class="rc${o.rc === "imm" ? " imm" : ""}" data-k="rc:${o.id}" data-v="${o.rc}" title="reference count">${label}</span>`;
    }
    const gcr =
      o.gcr !== undefined && o.gcr !== null
        ? `<span class="gcr" data-k="gcr:${o.id}" data-v="${o.gcr}">gc_refs ${o.gcr}</span>`
        : "";
    const cls = ["obj", o.dim ? "is-dim" : "", o.hot ? "is-hot" : "", o.mark ? `is-${o.mark}` : ""].join(" ").trim();
    const addr = o.addr ? `<div class="obj-id">id ${esc(o.addr)}</div>` : "";
    const tag = o.tag ? `<div class="obj-tag">${o.tag}</div>` : "";
    const perRow = last && last.cols ? last.cols : cols;
    const col = narrow ? 1 : o.at[0] + 1;
    const row = narrow ? o.at[1] * perRow + o.at[0] + 1 : o.at[1] + 1;
    return `<div class="${cls}" data-k="o:${o.id}" data-obj="${o.id}" data-exit="poof" style="--c:var(--${typeColor(o.type)});grid-column:${col};grid-row:${row}"><div class="obj-h"><span class="bul">${esc(o.label || o.type)}</span>${rc}</div>${body}${addr}${tag}${gcr}</div>`;
  }

  function geometry() {
    const base = mem.getBoundingClientRect();
    const list = [];
    for (const p of mem.querySelectorAll("[data-port]")) {
      if (p.closest(".ghost-layer")) {
        continue;
      }
      const t = heapEl.querySelector(`[data-obj="${CSS.escape(p.dataset.to)}"]`);
      if (!t) {
        continue;
      }
      const pr = p.getBoundingClientRect();
      const tr = t.getBoundingClientRect();
      if (!pr.width || !tr.width) {
        continue;
      }
      const sx = (pr.left + pr.width / 2 - base.left) / scale;
      const sy = (pr.top + pr.height / 2 - base.top) / scale;
      const box = {
        l: (tr.left - base.left) / scale,
        t: (tr.top - base.top) / scale,
        r: (tr.right - base.left) / scale,
        b: (tr.bottom - base.top) / scale,
      };
      let side = "U";
      if (box.l >= sx + 22) {
        side = "L";
      } else if (box.t >= sy + 10) {
        side = "T";
      } else if (box.b <= sy - 30) {
        side = "B";
      }
      const src = p.closest(".obj");
      const sb = src ? (src.getBoundingClientRect().bottom - base.top) / scale : sy + 12;
      list.push({
        key: `${p.dataset.port}>${p.dataset.to}`,
        sx,
        sy,
        sb,
        box,
        side,
        to: p.dataset.to,
        color: t.style.getPropertyValue("--c"),
      });
    }
    const bySide = new Map();
    for (const w of list) {
      const gk = `${w.to}|${w.side}`;
      if (!bySide.has(gk)) {
        bySide.set(gk, []);
      }
      bySide.get(gk).push(w);
    }
    for (const g of bySide.values()) {
      const horiz = g[0].side !== "L";
      g.sort((a, b) => (horiz ? a.sx - b.sx : a.sy - b.sy));
      g.forEach((w, i) => {
        const { box } = w;
        if (horiz) {
          const f = (i + 1) / (g.length + 1);
          w.tx = box.l + (box.r - box.l) * f;
          w.ty = w.side === "T" ? box.t : box.b;
        } else {
          const h = box.b - box.t;
          const step = Math.min(13, Math.max(6, (h - 26) / Math.max(1, g.length)));
          w.ty = Math.min(box.b - 9, box.t + 17 + i * step);
          w.tx = w.side === "L" ? box.l : box.r;
        }
      });
    }
    return list;
  }

  function group(key) {
    let g = groups.get(key);
    if (g) {
      return g;
    }
    const el = document.createElementNS(SVG_NS, "g");
    const halo = document.createElementNS(SVG_NS, "path");
    const line = document.createElementNS(SVG_NS, "path");
    const head = document.createElementNS(SVG_NS, "path");
    halo.setAttribute("class", "halo");
    line.setAttribute("class", "line");
    head.setAttribute("class", "head");
    el.append(halo, line, head);
    svg.appendChild(el);
    g = { el, halo, line, head, fresh: true, dying: false };
    groups.set(key, g);
    return g;
  }

  function draw(dur, first) {
    const live = new Set();
    for (const w of geometry()) {
      live.add(w.key);
      const g = group(w.key);
      if (g.dying) {
        g.dying = false;
        g.el.getAnimations().forEach((a) => a.cancel());
        g.el.style.opacity = "";
      }
      const { d, dir } = wirePath(w);
      g.halo.setAttribute("d", d);
      g.line.setAttribute("d", d);
      g.head.setAttribute("d", headPath(w.tx, w.ty, dir));
      g.el.style.setProperty("--c", w.color);
      g.el.setAttribute("class", `wire ${wireCls[w.key] || ""}`.trim());
      if (g.fresh) {
        g.fresh = false;
        if (dur && first) {
          const L = Math.max(1, g.line.getTotalLength());
          const opts = { duration: dur * 0.8, delay: dur * 0.35, easing: "ease-out", fill: "backwards" };
          const kf = [
            { strokeDasharray: `${L} ${L}`, strokeDashoffset: L },
            { strokeDasharray: `${L} ${L}`, strokeDashoffset: 0 },
          ];
          g.line.animate(kf, opts);
          g.halo.animate(kf, opts);
          g.head.animate([{ opacity: 0 }, { opacity: 1 }], { duration: dur * 0.25, delay: dur * 1.05, fill: "backwards" });
        }
      }
    }
    for (const [key, g] of groups) {
      if (live.has(key) || g.dying) {
        continue;
      }
      if (!dur) {
        g.el.remove();
        groups.delete(key);
        continue;
      }
      g.dying = true;
      g.el
        .animate([{ opacity: 1 }, { opacity: 0 }], { duration: dur * 0.5, fill: "forwards" })
        .finished.catch(() => {})
        .then(() => {
          if (g.dying) {
            g.el.remove();
            groups.delete(key);
          }
        });
    }
  }

  function track(dur) {
    const my = ++trackToken;
    draw(dur, true);
    if (!dur) {
      return Promise.resolve();
    }
    const t0 = performance.now();
    return new Promise((resolve) => {
      const tick = (now) => {
        if (my !== trackToken) {
          resolve();
          return;
        }
        draw(dur, false);
        if (now - t0 < dur * 1.3 + 80) {
          requestAnimationFrame(tick);
        } else {
          resolve();
        }
      };
      requestAnimationFrame(tick);
    });
  }

  function floats(st, prev) {
    const before = new Map(prev.objs.map((o) => [o.id, o.rc]));
    for (const o of st.objs) {
      const a = before.get(o.id);
      if (typeof o.rc !== "number" || typeof a !== "number" || a === o.rc) {
        continue;
      }
      const diff = o.rc - a;
      const badge = heapEl.querySelector(`[data-k="rc:${CSS.escape(o.id)}"]`);
      floatText(badge, diff > 0 ? `+${diff}` : `\u2212${-diff}`, diff > 0 ? "green" : "red");
    }
  }

  function fit() {
    mem.style.transform = "";
    host.style.height = "";
    const need = mem.scrollWidth;
    const have = host.clientWidth - 8;
    scale = need > have + 1 ? have / need : 1;
    if (scale < 1) {
      mem.style.transformOrigin = "0 0";
      mem.style.transform = `scale(${scale.toFixed(4)})`;
      host.style.height = `${Math.ceil(mem.offsetHeight * scale) + 24}px`;
    }
  }

  function paint(st) {
    wireCls = st.wires || {};
    narrow = host.clientWidth < 600;
    mem.classList.toggle("is-narrow", narrow);
    mem.style.setProperty("--cols", String(narrow ? 1 : st.cols || cols));
    framesEl.innerHTML = [...st.frames].reverse().map(frameHtml).join("");
    heapEl.innerHTML = st.objs.length
      ? st.objs.map(objHtml).join("")
      : `<p class="empty heap-empty">${esc(emptyHeap)}</p>`;
    fit();
  }

  let lastWidth = 0;
  new ResizeObserver(() => {
    const w = host.clientWidth;
    if (last && Math.abs(w - lastWidth) > 1) {
      lastWidth = w;
      paint(last);
    }
    draw(0, false);
  }).observe(host);
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(() => draw(0, false));
  }

  return {
    root: mem,
    render(st, ctx = {}) {
      last = st;
      lastWidth = host.clientWidth;
      paint(st);
      const dur = ctx.dur || 0;
      if (dur && ctx.prev && ctx.prev.objs && refc) {
        setTimeout(() => floats(st, ctx.prev), dur * 0.55);
      }
      return track(dur);
    },
    redraw: () => draw(0, false),
  };
}
/* @endregion */
