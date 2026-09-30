/* ===================== shared runtime ===================== */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const ESC_MAP = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ESC_MAP[c]);
const sleep = (ms) =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const reduceMq = window.matchMedia("(prefers-reduced-motion: reduce)");
const motionOk = () => !reduceMq.matches;
const plain = (html) => String(html || "").replace(/<[^>]+>/g, "");
/* @region cssVar */
const cssVar = (name, el = document.documentElement) => getComputedStyle(el).getPropertyValue(name).trim();
/* @endregion */

/* @region onThemeChange */
function onThemeChange(fn) {
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", fn);
  new MutationObserver(fn).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme", "class"],
  });
}
/* @endregion */

/* @region tokHtml */
/* route-bullet token: <span class="tok"> with a coloured bullet */
function tokHtml(k, color, bullet, text, cls = "tok", extra = "") {
  const key = k ? ` data-k="${esc(k)}"` : "";
  return `<span class="${cls}"${key}${extra} style="--c:var(--${color})"><span class="bul">${esc(bullet)}</span><span class="tx">${esc(text)}</span></span>`;
}
/* @endregion */

/* @region ICON */
/* ---------- icons ---------- */
const ICON = {
  play: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5.6v12.8a1 1 0 0 0 1.52.85l10.2-6.4a1 1 0 0 0 0-1.7L9.52 4.75A1 1 0 0 0 8 5.6Z"/></svg>',
  pause:
    '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="5" width="4.2" height="14" rx="1.2" fill="currentColor"/><rect x="13.8" y="5" width="4.2" height="14" rx="1.2" fill="currentColor"/></svg>',
  back: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" d="M15 5l-7 7 7 7"/></svg>',
  next: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>',
  restart:
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" d="M4.5 12a7.5 7.5 0 1 0 2.2-5.3M4.5 4.5v4.2h4.2"/></svg>',
};
/* @endregion */

/* @region LANGS hlLine */
/* ---------- syntax highlighting ---------- */
const LANGS = {
  py: {
    kw: new Set(
      "False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield".split(
        " ",
      ),
    ),
    bi: new Set(
      "print len int str list dict set tuple float bool id type range isinstance hash repr super object bytes sum min max sorted open complex frozenset bytearray".split(
        " ",
      ),
    ),
    re: /(#.*$)|((?:\b[rbfRBF]{1,2})?"(?:[^"\\]|\\.)*"|(?:\b[rbfRBF]{1,2})?'(?:[^'\\]|\\.)*')|(\b\d[\d_]*(?:\.\d+)?(?:e[+-]?\d+)?j?\b)|([A-Za-z_]\w*)|(\s+)|(.)/g,
  },
  js: {
    kw: new Set(
      "async await break case catch class const continue default delete do else export extends false finally for from function if import in instanceof let new null of return switch this throw true try typeof undefined var void while yield".split(
        " ",
      ),
    ),
    bi: new Set(
      "console Promise setTimeout setImmediate setInterval process require Object Array Number String Boolean Symbol BigInt Date JSON Math Buffer structuredClone NaN Infinity globalThis Error".split(
        " ",
      ),
    ),
    re: /(\/\/.*$)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)|(\b\d[\d_]*(?:\.\d+)?(?:e[+-]?\d+)?n?\b)|([A-Za-z_$][\w$]*)|(\s+)|(.)/g,
  },
};

function hlLine(line, lang) {
  const L = LANGS[lang];
  const re = new RegExp(L.re.source, "g");
  let html = "";
  let m = re.exec(line);
  while (m !== null) {
    const [tok, com, str, num, id] = m;
    if (com) {
      html += `<span class="t-c">${esc(com)}</span>`;
    } else if (str) {
      html += `<span class="t-s">${esc(str)}</span>`;
    } else if (num) {
      html += `<span class="t-n">${esc(num)}</span>`;
    } else if (id) {
      const rest = line.slice(re.lastIndex);
      if (L.kw.has(id)) {
        html += `<span class="t-k">${id}</span>`;
      } else if (L.bi.has(id)) {
        html += `<span class="t-b">${id}</span>`;
      } else if (/^\s*\(/.test(rest)) {
        html += `<span class="t-f">${esc(id)}</span>`;
      } else {
        html += esc(id);
      }
    } else {
      html += esc(tok);
    }
    m = re.exec(line);
  }
  return html;
}
/* @endregion */

/* @region hlBlock */
function hlBlock(code, lang) {
  return code
    .split("\n")
    .map((ln) => hlLine(ln, lang))
    .join("\n");
}
/* @endregion */

/* @region codePanel */
/* code panel drawn as a timetable: a route line in the gutter, a station per line */
function codePanel(el, code, lang) {
  const lines = code.replace(/\n+$/, "").split("\n");
  el.innerHTML = lines
    .map(
      (ln, i) =>
        `<li><span class="ln">${i + 1}</span><span class="stop"></span><span class="src">${hlLine(ln, lang) || " "}</span></li>`,
    )
    .join("");
  const items = $$("li", el);
  return {
    count: lines.length,
    set(cur, seen) {
      items.forEach((li, i) => {
        const n = i + 1;
        li.classList.toggle("is-cur", n === cur);
        li.classList.toggle("is-seen", n !== cur && seen.has(n));
      });
      const li = items[cur - 1];
      if (!li || el.scrollHeight <= el.clientHeight + 2) {
        return;
      }
      const top = li.offsetTop;
      const bottom = top + li.offsetHeight;
      const behavior = motionOk() ? "smooth" : "auto";
      if (top < el.scrollTop + 10) {
        el.scrollTo({ top: Math.max(0, top - 10), behavior });
      } else if (bottom > el.scrollTop + el.clientHeight - 10) {
        el.scrollTo({ top: bottom - el.clientHeight + 10, behavior });
      }
    },
  };
}
/* @endregion */

/* @region GHOST_PROPS inlineStyles Flip */
/* ---------- FLIP motion between two renders ---------- */
const GHOST_PROPS = [
  "display",
  "flex-direction",
  "flex-wrap",
  "align-items",
  "justify-content",
  "gap",
  "grid-template-columns",
  "place-items",
  "padding-top",
  "padding-right",
  "padding-bottom",
  "padding-left",
  "border-top",
  "border-right",
  "border-bottom",
  "border-left",
  "border-radius",
  "background-color",
  "background-image",
  "color",
  "font-family",
  "font-size",
  "font-weight",
  "font-style",
  "line-height",
  "letter-spacing",
  "white-space",
  "text-align",
  "text-overflow",
  "overflow",
  "box-shadow",
  "opacity",
  "width",
  "height",
  "min-width",
  "box-sizing",
  "position",
  "top",
  "right",
  "bottom",
  "left",
];

function inlineStyles(src, dst) {
  const cs = getComputedStyle(src);
  for (const p of GHOST_PROPS) {
    dst.style.setProperty(p, cs.getPropertyValue(p));
  }
  const c = cs.getPropertyValue("--c");
  if (c) {
    dst.style.setProperty("--c", c);
  }
  const a = src.children;
  const b = dst.children;
  for (let i = 0; i < a.length && i < b.length; i += 1) {
    inlineStyles(a[i], b[i]);
  }
}

const Flip = {
  snap(root) {
    const base = root.getBoundingClientRect();
    const map = new Map();
    for (const el of root.querySelectorAll("[data-k]")) {
      if (el.closest(".ghost-layer")) {
        continue;
      }
      const r = el.getBoundingClientRect();
      if (!r.width && !r.height) {
        continue;
      }
      const clone = el.cloneNode(true);
      inlineStyles(el, clone);
      const anc = el.parentElement ? el.parentElement.closest("[data-k]") : null;
      map.set(el.dataset.k, {
        x: r.left - base.left,
        y: r.top - base.top,
        w: r.width,
        h: r.height,
        k: el.offsetWidth ? r.width / el.offsetWidth : 1,
        v: el.dataset.v === undefined ? null : el.dataset.v,
        clone,
        parentK: anc && root.contains(anc) ? anc.dataset.k : null,
        exit: el.dataset.exit || "",
      });
    }
    return map;
  },

  play(root, snap, { dur = 560 } = {}) {
    const base = root.getBoundingClientRect();
    const now = new Map();
    for (const el of root.querySelectorAll("[data-k]")) {
      if (el.closest(".ghost-layer")) {
        continue;
      }
      const r = el.getBoundingClientRect();
      now.set(el.dataset.k, { el, x: r.left - base.left, y: r.top - base.top, w: r.width, h: r.height });
    }
    const jobs = [];
    const delta = new Map();
    for (const [k, n] of now) {
      const o = snap.get(k);
      if (o) {
        delta.set(k, { dx: o.x - n.x, dy: o.y - n.y });
      }
    }
    for (const [k, n] of now) {
      const o = snap.get(k);
      const ancEl = n.el.parentElement ? n.el.parentElement.closest("[data-k]") : null;
      const anc = ancEl && root.contains(ancEl) ? ancEl.dataset.k : null;
      if (!o) {
        if ((anc && !snap.has(anc)) || (!n.w && !n.h)) {
          continue;
        }
        const a = n.el.animate(
          [
            { opacity: 0, transform: "scale(0.55)" },
            { opacity: 1, transform: "none" },
          ],
          { duration: dur * 0.75, delay: dur * 0.3, easing: "cubic-bezier(.2,.9,.3,1.2)", fill: "backwards" },
        );
        jobs.push(a.finished.catch(() => {}));
        continue;
      }
      let { dx, dy } = delta.get(k);
      if (anc && delta.has(anc)) {
        dx -= delta.get(anc).dx;
        dy -= delta.get(anc).dy;
      }
      const scale = n.el.offsetWidth ? n.w / n.el.offsetWidth : 1;
      if (scale > 0 && Math.abs(scale - 1) > 0.01) {
        dx /= scale;
        dy /= scale;
      }
      if (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5) {
        const el = n.el;
        const staticPos = getComputedStyle(el).position === "static";
        if (staticPos) {
          el.style.position = "relative";
        }
        el.style.zIndex = "30";
        const a = el.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: "none" }], {
          duration: dur,
          easing: "cubic-bezier(.55,0,.25,1)",
        });
        jobs.push(
          a.finished
            .catch(() => {})
            .then(() => {
              el.style.zIndex = "";
              if (staticPos) {
                el.style.position = "";
              }
            }),
        );
      }
      const nv = n.el.dataset.v === undefined ? null : n.el.dataset.v;
      if (o.v !== null && nv !== null && o.v !== nv) {
        n.el.classList.add("flash");
        setTimeout(() => n.el.classList.remove("flash"), 1200);
      }
    }
    let layer = null;
    for (const [k, o] of snap) {
      if (now.has(k) || (o.parentK && snap.has(o.parentK) && !now.has(o.parentK))) {
        continue;
      }
      if (!layer) {
        layer = document.createElement("div");
        layer.className = "ghost-layer";
        root.appendChild(layer);
      }
      const g = o.clone;
      g.removeAttribute("data-k");
      g.querySelectorAll("[data-k]").forEach((e) => {
        if (now.has(e.dataset.k)) {
          e.style.visibility = "hidden";
        }
        e.removeAttribute("data-k");
      });
      const sc = o.k || 1;
      Object.assign(g.style, {
        position: "absolute",
        left: `${o.x}px`,
        top: `${o.y}px`,
        right: "auto",
        bottom: "auto",
        width: `${o.w / sc}px`,
        height: `${o.h / sc}px`,
        margin: "0",
        transformOrigin: "0 0",
      });
      layer.appendChild(g);
      const grow = o.exit === "poof" ? 1.35 : 0.8;
      const shift = `translate(${((o.w * (1 - grow)) / 2).toFixed(1)}px, ${((o.h * (1 - grow)) / 2).toFixed(1)}px)`;
      const frames =
        o.exit === "poof"
          ? [
              { opacity: 1, transform: `scale(${sc})`, filter: "blur(0px)" },
              { opacity: 0, transform: `${shift} scale(${sc * grow})`, filter: "blur(4px)" },
            ]
          : [
              { opacity: 1, transform: `scale(${sc})` },
              { opacity: 0, transform: `${shift} scale(${sc * grow})` },
            ];
      const a = g.animate(frames, { duration: dur * (o.exit === "poof" ? 0.9 : 0.6), easing: "ease-in", fill: "forwards" });
      jobs.push(a.finished.catch(() => {}).then(() => g.remove()));
    }
    return Promise.all(jobs).then(() => {
      if (layer) {
        layer.remove();
      }
    });
  },
};
/* @endregion */

/* @region floatText */
function floatText(anchor, text, color) {
  if (!anchor || !motionOk()) {
    return;
  }
  const r = anchor.getBoundingClientRect();
  if (!r.width) {
    return;
  }
  const f = document.createElement("span");
  f.className = "fx-float";
  f.textContent = text;
  f.style.left = `${r.left + r.width / 2}px`;
  f.style.top = `${r.top - 6}px`;
  f.style.setProperty("--c", `var(--${color})`);
  document.body.appendChild(f);
  f.addEventListener("animationend", () => f.remove());
  setTimeout(() => f.remove(), 1600);
}
/* @endregion */

/* @region PLAYERS Player */
/* ---------- stepper player (narration + controls) ---------- */
const PLAYERS = [];

function Player({ dock, root, render, codeEl = null, outEl = null, emptyOut = "Nothing printed yet" }) {
  dock.innerHTML = `
    <div class="note" aria-live="polite"></div>
    <div class="player">
      <button type="button" class="btn icon" data-a="restart" aria-label="Restart" title="Restart">${ICON.restart}</button>
      <button type="button" class="btn icon" data-a="back" aria-label="Previous step" title="Previous step">${ICON.back}</button>
      <button type="button" class="btn primary" data-a="play"></button>
      <button type="button" class="btn icon" data-a="next" aria-label="Next step" title="Next step">${ICON.next}</button>
      <div class="progress" aria-hidden="true"><i></i></div>
      <span class="count"></span>
      <div class="seg" role="group" aria-label="Playback speed">
        <button type="button" data-s="0.6" aria-pressed="false">Slow</button>
        <button type="button" data-s="1" aria-pressed="true">Normal</button>
        <button type="button" data-s="1.8" aria-pressed="false">Fast</button>
      </div>
      <span class="keys"><kbd>&larr;</kbd> <kbd>&rarr;</kbd> step, <kbd>Space</kbd> play</span>
    </div>`;
  const note = $(".note", dock);
  const btnPlay = $('[data-a="play"]', dock);
  const btnBack = $('[data-a="back"]', dock);
  const btnNext = $('[data-a="next"]', dock);
  const bar = $(".progress i", dock);
  const count = $(".count", dock);
  let states = [{ note: "" }];
  let idx = 0;
  let codeView = null;
  let seenCache = [];
  let playing = false;
  let busy = false;
  let pending = null;
  let speed = 1;
  let token = 0;
  let shownOut = 0;
  const self = { ratio: 0, used: 0 };

  function seenAt(i) {
    if (!seenCache[i]) {
      const set = new Set();
      for (let j = 0; j <= i; j += 1) {
        const ln = states[j].line;
        if (Array.isArray(ln)) {
          ln.forEach((x) => set.add(x));
        } else if (ln) {
          set.add(ln);
        }
      }
      seenCache[i] = set;
    }
    return seenCache[i];
  }

  function paintOut(st, animate) {
    if (!outEl) {
      return;
    }
    const lines = st.out || [];
    if (!lines.length) {
      outEl.innerHTML = `<li class="empty">${esc(emptyOut)}</li>`;
      shownOut = 0;
      return;
    }
    outEl.innerHTML = lines
      .map((line, j) => {
        const isObj = typeof line === "object";
        const text = isObj ? line.t : line;
        const cls = [isObj && line.err ? "err" : "", animate && j >= shownOut ? "new" : ""].join(" ").trim();
        return `<li${cls ? ` class="${cls}"` : ""}>${esc(text)}</li>`;
      })
      .join("");
    shownOut = lines.length;
  }

  function paintChrome(st, animate) {
    note.innerHTML = st.note || "";
    note.classList.remove("swap");
    if (animate) {
      void note.offsetWidth;
      note.classList.add("swap");
    }
    if (codeView) {
      const ln = Array.isArray(st.line) ? st.line[0] : st.line;
      codeView.set(ln || 0, seenAt(idx));
    }
    paintOut(st, animate);
    const last = states.length - 1;
    bar.style.width = `${last ? (idx / last) * 100 : 0}%`;
    count.textContent = `Step ${idx + 1} of ${states.length}`;
    btnBack.disabled = idx === 0;
    btnNext.disabled = idx === last;
    setPlayBtn();
  }

  function setPlayBtn() {
    const atEnd = idx === states.length - 1;
    if (playing) {
      btnPlay.innerHTML = `${ICON.pause}<span>Pause</span>`;
    } else if (atEnd && states.length > 1) {
      btnPlay.innerHTML = `${ICON.restart}<span>Replay</span>`;
    } else {
      btnPlay.innerHTML = `${ICON.play}<span>Play</span>`;
    }
  }

  async function show(i, instant = false) {
    const target = clamp(i, 0, states.length - 1);
    if (busy) {
      pending = { i: target, instant };
      return;
    }
    busy = true;
    const prev = states[idx];
    const back = target < idx;
    const adjacent = Math.abs(target - idx) === 1;
    const dur = !instant && adjacent && motionOk() ? Math.round(620 / speed) : 0;
    const snap = dur ? Flip.snap(root) : null;
    if (!adjacent || instant) {
      shownOut = (states[target].out || []).length;
    }
    idx = target;
    paintChrome(states[idx], Boolean(dur));
    const r = render(states[idx], { prev, dur, back });
    const f = snap ? Flip.play(root, snap, { dur }) : null;
    try {
      await Promise.all([r, f]);
    } finally {
      busy = false;
    }
    if (pending) {
      const p = pending;
      pending = null;
      await show(p.i, p.instant);
    }
  }

  function holdFor(st) {
    const len = plain(st.note).length;
    return clamp((900 + len * 21) / speed, 700, 8000);
  }

  function pause() {
    playing = false;
    token += 1;
    setPlayBtn();
  }

  async function play() {
    if (playing) {
      return;
    }
    if (idx >= states.length - 1) {
      await show(0, true);
      await sleep(350);
    }
    playing = true;
    const my = ++token;
    setPlayBtn();
    while (playing && my === token && idx < states.length - 1) {
      await show(idx + 1);
      if (!playing || my !== token) {
        break;
      }
      if (idx < states.length - 1) {
        await sleep(holdFor(states[idx]));
      }
    }
    if (my === token) {
      playing = false;
      setPlayBtn();
    }
  }

  function reveal() {
    if (self.revealed) {
      return;
    }
    self.revealed = true;
    const r = root.getBoundingClientRect();
    const pad = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
    if (r.top > 40 + pad && r.bottom > window.innerHeight) {
      window.scrollBy({ top: r.top - 10 - pad, behavior: motionOk() ? "smooth" : "auto" });
    }
  }

  const api = {
    load(newStates, { code = null, lang = "js" } = {}) {
      pause();
      states = newStates;
      seenCache = [];
      idx = 0;
      shownOut = 0;
      if (codeEl && code !== null) {
        codeView = codePanel(codeEl, code, lang);
      }
      busy = false;
      pending = null;
      paintChrome(states[0], false);
      return render(states[0], { prev: null, dur: 0, back: false });
    },
    next() {
      pause();
      self.used = Date.now();
      reveal();
      return show(idx + 1);
    },
    back() {
      pause();
      self.used = Date.now();
      reveal();
      return show(idx - 1);
    },
    restart() {
      pause();
      self.used = Date.now();
      return show(0, true);
    },
    toggle() {
      self.used = Date.now();
      reveal();
      if (playing) {
        pause();
      } else {
        play();
      }
    },
    go: (i) => show(i, true),
    pause,
    get index() {
      return idx;
    },
    get length() {
      return states.length;
    },
    get state() {
      return states[idx];
    },
  };
  self.api = api;
  self.root = root;

  dock.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) {
      return;
    }
    if (b.dataset.s) {
      speed = Number(b.dataset.s);
      $$(".seg button", dock).forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      return;
    }
    const a = b.dataset.a;
    if (a === "play") {
      api.toggle();
    } else if (a === "next") {
      api.next();
    } else if (a === "back") {
      api.back();
    } else if (a === "restart") {
      api.restart();
    }
  });

  const io = new IntersectionObserver(
    (entries) => {
      for (const en of entries) {
        self.ratio = en.isIntersecting ? en.intersectionRect.height : 0;
      }
    },
    { threshold: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1] },
  );
  io.observe(root);
  PLAYERS.push(self);
  return api;
}

document.addEventListener("keydown", (e) => {
  if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey) {
    return;
  }
  const t = e.target;
  if (t && t.closest && t.closest("input, textarea, select, [contenteditable]")) {
    return;
  }
  let best = null;
  for (const p of PLAYERS) {
    if (p.ratio <= 0) {
      continue;
    }
    if (!best || p.ratio > best.ratio + 40 || (Math.abs(p.ratio - best.ratio) <= 40 && p.used > best.used)) {
      best = p;
    }
  }
  if (!best) {
    return;
  }
  if (e.key === "ArrowRight") {
    e.preventDefault();
    best.api.next();
  } else if (e.key === "ArrowLeft") {
    e.preventDefault();
    best.api.back();
  } else if (e.key === " " && !(t && t.closest && t.closest("button, a"))) {
    e.preventDefault();
    best.api.toggle();
  }
});
/* @endregion */

/* @region routeMap */
/* ---------- hero route map ---------- */
function routeMap(nav, stations, { current = 0, onPick = null } = {}) {
  nav.innerHTML = `<span class="route-track" aria-hidden="true"></span>${stations
    .map(
      (s, i) =>
        `<button type="button" class="stn" data-i="${i}" aria-current="${i === current}"><span class="dot"></span><span class="lbl">${s.label}</span>${s.sub ? `<span class="sub">${s.sub}</span>` : ""}</button>`,
    )
    .join("")}`;
  const track = $(".route-track", nav);
  const btns = $$(".stn", nav);
  const size = () => {
    const a = $(".dot", btns[0]).getBoundingClientRect();
    const b = $(".dot", btns[btns.length - 1]).getBoundingClientRect();
    const n = nav.getBoundingClientRect();
    track.style.left = `${a.left - n.left + nav.scrollLeft + a.width / 2}px`;
    track.style.width = `${Math.max(0, b.left - a.left)}px`;
    track.style.top = `${a.top - n.top + a.height / 2 - 4}px`;
  };
  size();
  new ResizeObserver(size).observe(nav);
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(size);
  }
  const set = (i) => btns.forEach((b, j) => b.setAttribute("aria-current", String(j === i)));
  nav.addEventListener("click", (e) => {
    const b = e.target.closest(".stn");
    if (!b) {
      return;
    }
    const i = Number(b.dataset.i);
    set(i);
    if (onPick) {
      onPick(i);
    }
  });
  return { set };
}
/* @endregion */

/* @region routeSpy */
/* highlight the station whose section is on screen */
function routeSpy(route, sections) {
  const io = new IntersectionObserver(
    (entries) => {
      for (const en of entries) {
        if (en.isIntersecting) {
          route.set(sections.indexOf(en.target));
        }
      }
    },
    { rootMargin: "-35% 0px -60% 0px" },
  );
  sections.forEach((s) => io.observe(s));
}
/* @endregion */

/* @region scrollToEl */
function scrollToEl(el) {
  el.scrollIntoView({ behavior: motionOk() ? "smooth" : "auto", block: "start" });
}
/* @endregion */

/* @region buildStates */
/* build a list of states from an initial state and step functions */
function buildStates(init, steps, reset = []) {
  const out = [init];
  let cur = init;
  for (const fn of steps) {
    const nx = structuredClone(cur);
    for (const key of reset) {
      delete nx[key];
    }
    fn(nx);
    out.push(nx);
    cur = nx;
  }
  return out;
}
/* @endregion */

