#!/usr/bin/env python3
"""Build the site from src/page.html and i18n/nl.json.

  python3 build.py                  write index.html, nl/index.html and sitemap.xml
  python3 build.py --artifact DIR   also write the two pages in the layout a Claude artifact uses
  python3 build.py --extract        list every translatable string, in page order
  python3 build.py --bootstrap FILE turn a numbered list of Dutch lines into i18n/nl.json
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "https://sybrenh.github.io/evolution-winged-it/"
META = {
    "en": {
        "name": "Nature's Workarounds",
        "title": "Nature's Workarounds: 10 funny ways evolution shaped animals",
        "desc": "Why dolphins went back to the sea, pandas have a fake thumb and kiwis lay giant eggs. "
                "Ten illustrated stories of evolution's odd fixes, after Stephen Jay Gould.",
        "locale": "en_US", "url": SITE, "image": SITE + "og.png",
    },
    "nl": {
        "name": "Noodoplossingen van de natuur",
        "title": "Noodoplossingen van de natuur: 10 grappige manieren waarop evolutie dieren vormde",
        "desc": "Waarom dolfijnen terugkeerden naar zee, panda's een nepduim hebben en kiwi's reuzeneieren leggen. "
                "Tien geïllustreerde verhalen over de rare oplossingen van de evolutie, naar Stephen Jay Gould.",
        "locale": "nl_NL", "url": SITE + "nl/", "image": SITE + "og-nl.png",
    },
}
LANG_NAMES = {"en": "English", "nl": "Nederlands"}
TEXT = re.compile(r">([^<>]+)<")
ATTR = re.compile(r'(aria-label)="([^"]*)"')
HAS_LETTER = re.compile(r"[A-Za-z]")


def split(src):
    """Head part (title, fonts, styles), body markup, and the script block."""
    cut = src.index("</style>") + len("</style>")
    head, rest = src[:cut], src[cut:].strip()
    s = rest.index("<script>")
    return head, rest[:s], rest[s:]


def segments(markup):
    seen, out = set(), []
    def add(t):
        if t and HAS_LETTER.search(t) and t not in seen:
            seen.add(t)
            out.append(t)
    for m in TEXT.finditer(markup):
        add(m.group(1).strip())
    for m in ATTR.finditer(markup):
        add(m.group(2))
    return out


def translate(markup, script, table):
    missing = []
    def text(m):
        raw = m.group(1)
        core = raw.strip()
        if not core or not HAS_LETTER.search(core):
            return m.group(0)
        if core not in table:
            missing.append(core)
            return m.group(0)
        return ">" + raw.replace(core, table[core], 1) + "<"
    def attr(m):
        if m.group(2) not in table:
            missing.append(m.group(2))
            return m.group(0)
        return '%s="%s"' % (m.group(1), table[m.group(2)])
    markup = ATTR.sub(attr, TEXT.sub(text, markup))
    for en, nl in table.get("_js", {}).items():
        if en not in script:
            missing.append("JS: " + en)
        script = script.replace(en, nl)
    if missing:
        sys.exit("Untranslated strings:\n  " + "\n  ".join(missing))
    return markup, script


def lang_switch(lang, hrefs):
    parts = []
    for code, label in LANG_NAMES.items():
        if code == lang:
            parts.append('<span lang="%s" aria-current="page">%s</span>' % (code, label))
        else:
            parts.append('<a href="%s" lang="%s" hreflang="%s">%s</a>' % (hrefs[code], code, code, label))
    return '<nav class="lang" aria-label="%s">%s</nav>' % ("Taal" if lang == "nl" else "Language", "".join(parts))


def seo(lang):
    m = META[lang]
    e = lambda s: html.escape(s, quote=True)
    other = "nl" if lang == "en" else "en"
    ld = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": m["title"], "description": m["desc"], "inLanguage": lang,
        "url": m["url"], "mainEntityOfPage": m["url"], "image": m["image"],
        "isAccessibleForFree": True,
        "about": [{"@type": "Thing", "name": "Evolution"},
                  {"@type": "Person", "name": "Stephen Jay Gould"}],
    }
    return "\n".join([
        '<meta name="description" content="%s">' % e(m["desc"]),
        '<link rel="canonical" href="%s">' % m["url"],
        '<link rel="alternate" hreflang="en" href="%s">' % META["en"]["url"],
        '<link rel="alternate" hreflang="nl" href="%s">' % META["nl"]["url"],
        '<link rel="alternate" hreflang="x-default" href="%s">' % META["en"]["url"],
        '<meta property="og:type" content="article">',
        '<meta property="og:site_name" content="%s">' % e(m["name"]),
        '<meta property="og:title" content="%s">' % e(m["title"]),
        '<meta property="og:description" content="%s">' % e(m["desc"]),
        '<meta property="og:url" content="%s">' % m["url"],
        '<meta property="og:image" content="%s">' % m["image"],
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:locale" content="%s">' % m["locale"],
        '<meta property="og:locale:alternate" content="%s">' % META[other]["locale"],
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % e(m["title"]),
        '<meta name="twitter:description" content="%s">' % e(m["desc"]),
        '<meta name="twitter:image" content="%s">' % m["image"],
        '<meta name="google-site-verification" content="vvnTfavHYszdzstcURbWgC-BSp-oZDf7bgH32fe8dt0">',
        '<meta name="theme-color" content="#17607A">',
        '<link rel="icon" type="image/svg+xml" href="%sfavicon.svg">' % SITE,
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False),
    ])


def document(lang, head, body, script, extra=""):
    head = head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    return ("<!doctype html>\n<html lang=\"%s\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            "%s\n%s\n</head>\n<body>\n%s\n%s\n</body>\n</html>\n") % (lang, extra, head, body, script)


def retitle(head, title):
    return re.sub(r"<title>.*?</title>", "<title>%s</title>" % html.escape(title, quote=False), head, count=1)


def main():
    src = (ROOT / "src" / "page.html").read_text(encoding="utf-8")
    head, body, script = split(src)
    args = sys.argv[1:]

    if args[:1] == ["--extract"]:
        for i, s in enumerate(segments(body), 1):
            print("%d\t%s" % (i, s))
        return

    nl_path = ROOT / "i18n" / "nl.json"
    if args[:1] == ["--bootstrap"]:
        segs = segments(body)
        table = {}
        for line in Path(args[1]).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            n, _, text = line.partition("|")
            table[int(n)] = text
        gaps = [i for i in range(1, len(segs) + 1) if i not in table]
        if gaps or len(table) != len(segs):
            sys.exit("Expected %d lines; missing %s" % (len(segs), gaps))
        old = json.loads(nl_path.read_text(encoding="utf-8")) if nl_path.exists() else {}
        out = {s: (s if table[i] == "=" else table[i]) for i, s in enumerate(segs, 1)}
        out["_js"] = old.get("_js", {})
        nl_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("wrote", nl_path, len(segs), "strings")
        return

    table = json.loads(nl_path.read_text(encoding="utf-8"))
    pages = {"en": (body, script), "nl": translate(body, script, table)}

    # The public site: / and /nl/
    site_hrefs = {"en": {"en": "./", "nl": "nl/"}, "nl": {"en": "../", "nl": "./"}}
    for lang, (b, s) in pages.items():
        out = ROOT / ("index.html" if lang == "en" else "nl/index.html")
        out.parent.mkdir(exist_ok=True)
        page_body = b.replace("<!--LANG-->", lang_switch(lang, site_hrefs[lang]))
        out.write_text(document(lang, retitle(head, META[lang]["title"]), page_body, s, seo(lang)), encoding="utf-8")
        print("wrote", out.relative_to(ROOT))

    urls = "".join(
        "  <url>\n    <loc>%s</loc>\n%s  </url>\n" % (
            META[l]["url"],
            "".join('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>\n' % (k, META[k]["url"]) for k in META))
        for l in META)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + urls + "</urlset>\n", encoding="utf-8")
    print("wrote sitemap.xml")

    # The Claude artifact: the English page without a document shell, Dutch beside it as nl.html
    if args[:1] == ["--artifact"]:
        d = Path(args[1])
        en_b, en_s = pages["en"]
        nl_b, nl_s = pages["nl"]
        (d / "natures-workarounds.html").write_text(
            head + "\n\n" + en_b.replace("<!--LANG-->", lang_switch("en", {"nl": "nl.html"})) + "\n" + en_s + "\n",
            encoding="utf-8")
        (d / "nl.html").write_text(
            document("nl", retitle(head, META["nl"]["name"]),
                     nl_b.replace("<!--LANG-->", lang_switch("nl", {"en": "index.html"})), nl_s),
            encoding="utf-8")
        print("wrote artifact pages in", d)


if __name__ == "__main__":
    main()
