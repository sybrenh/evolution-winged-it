# Nature's Workarounds

Live at https://sybrenh.github.io/evolution-winged-it/ (English) and
https://sybrenh.github.io/evolution-winged-it/nl/ (Nederlands).

A one-page picture book about the funny ways evolution shaped certain animals:
the dolphin that went back to sea, the panda's false thumb, the kiwi's oversized
egg, and seven more. Several stories come from Stephen Jay Gould's essays.

## Editing

The page is written once, in English, in `src/page.html`. Dutch lives in
`i18n/nl.json`, which maps each English string to its translation.

```bash
python3 build.py
```

That writes `index.html`, `nl/index.html` and `sitemap.xml`, including the search
and link-preview tags. The build stops and lists any string that has no Dutch
translation yet. `python3 build.py --extract` lists every translatable string.

The link-preview images `og.png` and `og-nl.png` are screenshots of
`src/og-card.html` (add `?lang=nl` for Dutch) at 1200x630.
