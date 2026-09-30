# Runtime lines

An interactive, visual reference for full-stack engineers preparing for interviews: how Node.js and Python actually run your code, drawn as a transit map. In English at `/` and Romanian at `/ro`.

Five explorers ("lines"), each ending with about 30 interview questions and short answers:

| Line | Link | What it covers |
| --- | --- | --- |
| Node event loop | `/#node` | Call stack, `nextTick` and promise queues, timers, libuv phases, the thread pool |
| Python memory | `/#memory` | Names and references, reference counting, the cycle collector, pymalloc |
| The GIL | `/#gil` | CPU-bound vs I/O-bound threads, free-threaded Python, processes, race conditions |
| JavaScript types | `/#js-types` | `typeof`, V8 representations, copies vs references, the `==` algorithm, truthiness, IEEE 754 |
| Python types | `/#py-types` | Built-in types and where to use them, operator dispatch, `+=`, dict hashing |

Built by [Sergiu Vlad](https://sergiuvlad.com).

## Deploy to Vercel

The site is fully static. `public/` is committed and served as-is; Vercel runs no build step.

**With the CLI**

```bash
npm i -g vercel
vercel          # preview deployment
vercel --prod   # production
```

**From Git**: push the repository, then in Vercel choose *Add New Project* and import it. `vercel.json` already sets the framework to *Other* and the output directory to `public`, so leave the build settings at their defaults.

**Once you know the domain**, rebuild with it so the page gets a canonical URL, an absolute `og:image` and a `sitemap.xml`, then commit `public/`:

```bash
SITE_URL=https://your-domain.com npm run site
```

**Security headers.** `vercel.json` sends a Content Security Policy plus `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and `Permissions-Policy`. The CSP allows only the site itself and Google Fonts. On preview deployments it also blocks the Vercel toolbar (`vercel.live`); add that origin to `script-src`, `connect-src` and `frame-src` if you want the toolbar there.

## Working on it

Requirements: Python 3.12+ and Node.js 20+.

```bash
npm install                  # ESLint for `npm run lint`
npm run site                 # rebuild public/index.html and public/ro/index.html from src/
npm run i18n                 # add new or changed English text to src/i18n/ro.json (then translate the nulls)
npm run i18n:check           # fail if any Romanian translation is missing
npm run dev                  # serve public/ on http://127.0.0.1:8000 with the vercel.json headers
npm run lint                 # ESLint: the built page script and the Node verification programs
npm run format:check         # black: build scripts, tests, Python snippets (pip install black)
npm test                     # end-to-end checks (pip install playwright && python -m playwright install chromium)
```

Less frequent tasks:

```bash
python3 scripts/make_images.py   # regenerate public/og.png and public/apple-touch-icon.png
python3 scripts/gen_ops.py       # re-record the operator dispatch traces from real CPython (src/data/ops.json)
python3 scripts/gen_uses.py      # run and black-check the "Where you'd use it" snippets, then write src/data/uses.json
```

`npm test` serves `public/` with the same headers as production, drives Chromium through every explorer, compares each printed output with the expected one, checks all 225 pairs of the `==`, `===` and `Object.is` grids against the real engine, and fails on any console error, including CSP violations.

## Layout

```
public/              what Vercel serves: index.html, ro/index.html, 404.html, favicon.svg, og.png, robots.txt
src/
  pages/             one source page per explorer, each still a standalone HTML file
  lib/               shared design system and runtime (shared.css/js) and the memory map (mem.css/js)
  partials/          home view (home.html) and site shell styles (shell.css)
  reference/         interview questions for each line
  data/              generated data: operator dispatch traces, type usage snippets
  snippets/          the Python snippets shown in "Where you'd use it" (black-formatted, runnable)
  i18n/ro.json       Romanian catalog: English text unit -> Romanian
scripts/             build, local server, image and data generators
tests/               end-to-end test suite
verify/              the programs behind every output shown in the explorers
```

## How the build works

`scripts/build.py` reads each page in `src/pages/`, then:

1. extracts its CSS, markup and script;
2. prefixes every element id (`n-`, `m-`, `g-`, `j-`, `p-`) so the five pages can share one document, and scopes each page's CSS to its view (`#v-node`, and so on);
3. wraps each page script in a function that runs the first time its view is opened;
4. keeps only the regions of the shared library that some page actually uses;
5. adds the home view, the interview sections, the header menu and the footer, and writes one self-contained `public/index.html`.

Routing uses the URL hash (`#node`, `#gil`, ...), so it works on any static host without rewrites, and the back button moves between lines.

## Languages

English is the source. `scripts/i18n.py` walks the built English page and collects every piece of text a reader sees: text runs in the markup (inline tags such as `<code>` stay inside the unit), readable attributes (`aria-label`, `title`, `alt`, meta descriptions), and the text inside JavaScript strings and template literals, where `${...}` becomes a numbered placeholder (`{0}`, `{1}`) that a translation may move. `src/i18n/ro.json` maps each unit to Romanian; code, program output and names map to themselves. The build writes `public/ro/index.html` from the same page and the catalog, so the explorers' logic exists once.

After changing English text:

```bash
npm run site && npm run i18n   # new units appear in src/i18n/ro.json as null
# translate them, then
npm run site && npm run i18n:check
```

Missing translations fall back to English, and the build prints a warning. Mark text that must never be translated with `translate="no"`. The header switch keeps the current line (`/#gil` to `/ro#gil`) and remembers the choice; a first visit from a browser set to Romanian starts at `/ro`.

## Verification

Everything the explorers print comes from a real run:

```bash
node verify/node/s1.js        # A E D C B (scenarios s1 to s5, and copy.js)
python3 verify/python/m1.py   # Python memory scenarios m1 to m4
python3 verify/python/race.py # 130, 150 or 180 depending on timing; race_lock.py always prints 180
```

The Node programs are CommonJS on purpose: run as ES modules, top-level promise callbacks run before `process.nextTick` callbacks and scenario 1 prints `A E C D B` instead.
