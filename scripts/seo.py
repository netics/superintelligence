"""Search and LLM metadata built from the final (translated) pages.

Everything here reads the HTML the build already produced, so the English and
Romanian versions describe themselves in their own language:

- JSON-LD: WebSite, Person, and per line a LearningResource, BreadcrumbList
  and FAQPage made from the interview questions on that page
- Markdown versions of every page (/node.md, /ro/node.md, ...), /llms.txt,
  /llms-full.txt and /ro/llms-full.txt for LLMs and AI search
- sitemap.xml with hreflang alternates and images, and robots.txt
"""

import html as htmllib
import json
import re
from html.parser import HTMLParser

# Crawlers that feed AI assistants and AI search. All are welcome.
AI_BOTS = [
    "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot",
    "Claude-User", "anthropic-ai", "PerplexityBot", "Perplexity-User",
    "Google-Extended", "Applebot-Extended", "Bingbot", "DuckAssistBot",
    "Amazonbot", "meta-externalagent", "MistralAI-User", "cohere-ai", "CCBot",
]  # fmt: skip

WORDS = {
    "en": {
        "audience": "Full-stack software engineers preparing for technical interviews",
        "types": ["Interactive explainer", "Interview questions"],
        "level": "Intermediate",
        "lines": "Lines",
        "questions": "Interview questions",
        "full": "Full text of every line in one file",
        "other": "Romanian version",
        "source": "Source page",
    },
    "ro": {
        "audience": "Ingineri software full-stack care se pregătesc pentru interviuri tehnice",
        "types": ["Explicație interactivă", "Întrebări de interviu"],
        "level": "Intermediar",
        "lines": "Linii",
        "questions": "Întrebări de interviu",
        "full": "Textul complet al tuturor liniilor, într-un singur fișier",
        "other": "Versiunea în engleză",
        "source": "Pagina sursă",
    },
}


def text(fragment):
    """Plain text of an HTML fragment."""
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = htmllib.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"\s+([,.;:!?)])", r"\1", t).replace("( ", "(")


def element(html, id_):
    """Inner HTML of the element with this id (matching nested tags of the same name)."""
    m = re.search(rf'<([a-z][\w-]*)\b[^>]*\bid="{re.escape(id_)}"[^>]*>', html)
    if not m:
        return ""
    name, depth, i = m.group(1), 1, m.end()
    for t in re.finditer(rf"<(/?){name}\b[^>]*>", html[i:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return html[i : i + t.start()]
    return html[i:]


def qa(html, prefix):
    """(question, answer) pairs from a line's interview section, as plain text."""
    ref = element(html, f"{prefix}ref")
    return [
        (text(q), text(a))
        for q, a in re.findall(
            r'<summary>(.*?)</summary><div class="qa-a">(.*?)</div></details>',
            ref,
            re.S,
        )
    ]


def meta(html, name):
    m = re.search(rf'<meta (?:name|property)="{name}" content="([^"]*)"', html)
    return htmllib.unescape(m.group(1)) if m else ""


def jsonld(html, *, lang, view, prefix, url, home_url, site, image, author, names):
    website = f"{site}/#website"
    person = f"{site}/#author"
    title = text(re.search(r"<title>(.*?)</title>", html, re.S).group(1))
    desc = meta(html, "description")
    graph = [
        {
            "@type": "WebSite",
            "@id": website,
            "url": f"{site}/",
            "name": "Runtime lines",
            "alternateName": site.split("//")[-1],
            "inLanguage": ["en", "ro"],
            "publisher": {"@id": person},
        },
        {
            "@type": "Person",
            "@id": person,
            "name": author["name"],
            "url": author["url"],
            "jobTitle": "Senior Software Engineer",
            "sameAs": [author["url"], author["linkedin"]],
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Cluj-Napoca",
                "addressCountry": "RO",
            },
        },
    ]
    page = {
        "@type": "WebPage",
        "@id": f"{url}#webpage",
        "url": url,
        "name": title,
        "description": desc,
        "inLanguage": lang,
        "isPartOf": {"@id": website},
        "author": {"@id": person},
        "primaryImageOfPage": {
            "@type": "ImageObject",
            "url": image,
            "width": 1200,
            "height": 630,
        },
    }
    graph.append(page)
    w = WORDS[lang]
    if view == "home":
        page["@type"] = "CollectionPage"
        page["hasPart"] = [{"@id": f"{u}#resource"} for u in names.values()]
        page["about"] = [{"@type": "Thing", "name": n} for n in names]
        return {"@context": "https://schema.org", "@graph": graph}
    name = next(n for n, u in names.items() if u == url)
    h1 = text(
        re.search(r"<h1\b[^>]*>(.*?)</h1>", element(html, f"v-{view}"), re.S).group(1)
    )
    pairs = qa(html, prefix)
    page["breadcrumb"] = {"@id": f"{url}#breadcrumb"}
    page["mainEntity"] = {"@id": f"{url}#resource"}
    graph += [
        {
            "@type": "LearningResource",
            "@id": f"{url}#resource",
            "name": h1,
            "headline": title,
            "description": desc,
            "url": url,
            "image": image,
            "inLanguage": lang,
            "isAccessibleForFree": True,
            "learningResourceType": w["types"],
            "educationalLevel": w["level"],
            "audience": {"@type": "Audience", "audienceType": w["audience"]},
            "teaches": [q for q, _ in pairs[:12]],
            "about": {"@type": "Thing", "name": name},
            "author": {"@id": person},
            "isPartOf": {"@id": website},
            "hasPart": {"@id": f"{url}#faq"},
        },
        {
            "@type": "BreadcrumbList",
            "@id": f"{url}#breadcrumb",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Runtime lines",
                    "item": home_url,
                },
                {"@type": "ListItem", "position": 2, "name": name, "item": url},
            ],
        },
        {
            "@type": "FAQPage",
            "@id": f"{url}#faq",
            "url": url,
            "name": f"{w['questions']}: {name}",
            "inLanguage": lang,
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a},
                }
                for q, a in pairs
            ],
        },
    ]
    return {"@context": "https://schema.org", "@graph": graph}


def script_tag(data):
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return (
        '<script type="application/ld+json">' + raw.replace("</", "<\\/") + "</script>"
    )


# markdown ------------------------------------------------------------------
class Markdown(HTMLParser):
    """Turn the static content of a view into readable Markdown.

    Interactive parts (buttons, the simulators, SVG, navigation) are skipped;
    what remains is the explanatory text and the interview questions.
    """

    SKIP = {
        "script",
        "style",
        "svg",
        "button",
        "nav",
        "select",
        "input",
        "textarea",
        "template",
    }
    SKIP_CLASS = re.compile(
        r"\b(stage|dock|route|hero-jump|nextline|qa-tools|sr-only|lab|panel|sim)\b"
    )
    VOID = {"br", "img", "hr", "input", "meta", "link", "source", "wbr"}

    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base, self.out, self.skip, self.stack = base, [], 0, []
        self.list_depth, self.href = 0, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.VOID:
            if tag == "br" and not self.skip:
                self.out.append("  \n")
            return
        if self.skip:
            self.stack.append((tag, False))
            return
        skip = (
            tag in self.SKIP
            or "hidden" in a
            or a.get("aria-hidden") == "true"
            or self.SKIP_CLASS.search(a.get("class") or "")
        )
        self.stack.append((tag, bool(skip)))
        if skip:
            self.skip = 1
            return
        emit = {
            "h1": "\n\n# ", "h2": "\n\n## ", "h3": "\n\n### ", "p": "\n\n", "summary": "\n\n### ",
            "b": "**", "strong": "**", "em": "*", "i": "*", "code": "`",
        }.get(tag)  # fmt: skip
        if tag in ("ul", "ol"):
            self.list_depth += 1
        elif tag == "li":
            self.out.append("\n" + "  " * (self.list_depth - 1) + "- ")
        elif tag == "a" and a.get("href"):
            href = a["href"]
            self.href = self.base + href if href.startswith("/") else href
            self.out.append("[")
        elif emit:
            self.out.append(emit)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        while self.stack:
            t, started_skip = self.stack.pop()
            if started_skip:
                self.skip = 0
            elif not self.skip:
                self.close(t)
            if t == tag:
                break

    def close(self, tag):
        if tag in ("ul", "ol"):
            self.list_depth -= 1
            self.out.append("\n")
        elif tag in ("b", "strong"):
            self.out.append("**")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag == "code":
            self.out.append("`")
        elif tag == "a" and self.href:
            self.out.append(f"]({self.href})")
            self.href = None
        elif tag in (
            "p",
            "h1",
            "h2",
            "h3",
            "summary",
            "section",
            "details",
            "div",
            "header",
        ):
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(re.sub(r"\s+", " ", data))

    def result(self):
        md = "".join(self.out)
        md = re.sub(r"`\s*`|\*\*\s*\*\*", "", md)
        md = re.sub(r"^(\s*- \*\*[^*\n]+?)\*\*(?=\w)", r"\1:** ", md, flags=re.M)
        md = re.sub(r"[ \t]+\n", "\n", md)
        md = re.sub(r"\n[ \t]+(?=[^\s-])", "\n", md)
        return re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"


def markdown(html, view, site, url, title, desc, alternates):
    conv = Markdown(site)
    conv.feed(element(html, f"v-{view}"))
    body = conv.result()
    head = f"---\ntitle: {json.dumps(title, ensure_ascii=False)}\ndescription: {json.dumps(desc, ensure_ascii=False)}\nurl: {url}\n"
    head += "".join(f"alternate_{lang}: {u}\n" for lang, u in alternates.items())
    return head + "---\n\n" + body


def llms_txt(site, desc, author, pages):
    """pages: {lang: [(title, md_url, description)]} with the home page first."""
    out = [
        "# Runtime lines",
        "",
        f"> {desc}",
        "",
        f"An interactive reference built by {author['name']} ({author['url']}). Five explorers, drawn as lines on a "
        "transit map, step through real programs; every output shown was checked against real Node.js and CPython, "
        "and each line ends with about 30 interview questions with short answers. The whole site is available in "
        "English and in Romanian. The links below are clean Markdown versions of each page.",
        "",
    ]
    for lang, items in pages.items():
        out.append(
            f"## {WORDS[lang]['lines']} ({'English' if lang == 'en' else 'română'})"
        )
        out.append("")
        out += [f"- [{t}]({u}): {d}" for t, u, d in items]
        out.append("")
    out += ["## Optional", ""]
    out.append(
        f"- [llms-full.txt]({site}/llms-full.txt): {WORDS['en']['full']} (English)"
    )
    out.append(
        f"- [ro/llms-full.txt]({site}/ro/llms-full.txt): {WORDS['ro']['full']} (română)"
    )
    out.append(f"- [Sitemap]({site}/sitemap.xml)")
    return "\n".join(out) + "\n"


def sitemap(entries, today):
    """entries: [(url, {lang: url}, image_url)]."""
    rows = []
    for url, alts, image in entries:
        links = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{u}"/>'
            for l, u in alts.items()
        )
        links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{alts["en"]}"/>'
        rows.append(
            f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{today}</lastmod>{links}\n"
            f"    <image:image><image:loc>{image}</image:loc></image:image>\n  </url>\n"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        + "".join(rows)
        + "</urlset>\n"
    )


def robots(site):
    out = ["# Runtime lines, " + site, "User-agent: *", "Allow: /", ""]
    out.append("# AI assistants and AI search are welcome to read and cite this site.")
    for bot in AI_BOTS:
        out += [f"User-agent: {bot}", "Allow: /", ""]
    out += [f"Sitemap: {site}/sitemap.xml", ""]
    return "\n".join(out)
