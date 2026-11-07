#!/usr/bin/env python3
"""Build the blog from Markdown.

Source:  content/blog/<slug>/article.md  (front matter + Markdown)
         content/blog/<slug>/images/*.png (originals; convert with cwebp, see below)
Output:  blog/<slug>.html, blog.html, and marked blocks in sitemap.xml, llms.txt, llms-full.txt

Images are served from assets/blog/<slug>/<name>.webp. Convert new ones with:
  cwebp -quiet -resize 1600 0 -q 80 -m 6 in.png -o assets/blog/<slug>/<name>.webp
and make a 1200x630 og.jpg from the hero (sips, see README in CLAUDE.md).

The page shell (fonts, CSS, nav, footer, contact modal, scripts) is copied from
case-study-air-waterfall.html, so site-wide edits to that page flow into the blog
on the next build. Run:  python3 scripts/build_blog.py
"""
import datetime as dt
import glob
import html
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://f1rstword.com'
LINKEDIN = 'https://www.linkedin.com/in/rudra-trivedi-t04/'
TEMPLATE = os.path.join(ROOT, 'case-study-air-waterfall.html')
WPM = 220

LI_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M19 3a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h14zM8.34 18v-8.4H5.67V18h2.67zM7 8.4a1.55 1.55 0 100-3.1 1.55 1.55 0 000 3.1zM18.34 18v-4.6c0-2.46-1.31-3.61-3.06-3.61-1.41 0-2.04.78-2.39 1.32v-1.13H10.2c.04.75 0 8.02 0 8.02h2.69v-4.48c0-.24.02-.48.09-.65.2-.48.63-.98 1.37-.98.97 0 1.36.74 1.36 1.82V18h2.63z"/></svg>')

ARROW = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">\n'
         '        <path d="M5 12h14M13 6l6 6-6 6" />\n      </svg>')

BLOG_CSS = """
.post-hero .hero-headline{font-size:clamp(2rem,4.8vw,3.5rem);line-height:1.05;max-width:22ch}
.post-hero .hero-sub{max-width:52ch;margin-top:1rem}
.byline{position:relative;z-index:2;display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:.45rem .9rem;margin-top:1.5rem;font-size:.92rem;font-weight:500;color:var(--ink)}
.byline-who{display:inline-flex;align-items:center;gap:.55rem;background:rgba(255,253,249,.88);border:1.5px solid var(--ink);border-radius:999px;padding:.3rem .8rem .3rem .3rem;box-shadow:2px 2px 0 var(--ink)}
.byline-who img{width:32px;height:32px;border-radius:50%;border:1.5px solid var(--ink);object-fit:cover;display:block}
.byline-who a.name{color:var(--ink);font-weight:700;text-decoration:none}
.byline-who a.name:hover{text-decoration:underline}
.li-link{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:5px;background:#0A66C2;color:#fff;transition:transform .15s ease}
.li-link svg{width:14px;height:14px}
.li-link:hover{transform:translate(-1px,-1px)}
.byline-meta{display:inline-flex;align-items:center;gap:.5rem;background:rgba(255,253,249,.7);border:1.5px solid var(--ink);border-radius:999px;padding:.35rem .85rem}
.post-body{background:var(--cream);padding:clamp(2rem,4vw,3rem) 1.25rem clamp(2.5rem,5vw,3.5rem)}
.post-inner{max-width:720px;margin:0 auto}
.post-top{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.75rem;margin-bottom:1.75rem}
.post-tags{display:flex;flex-wrap:wrap;gap:.4rem;list-style:none;padding:0;margin:0}
.post-tags li{font-size:.76rem;font-weight:700;background:#FFFDF9;border:1.5px solid var(--ink);border-radius:999px;padding:.2rem .65rem}
.post-toc{background:var(--cream-2);border:2px solid var(--ink);border-radius:18px;box-shadow:4px 4px 0 var(--ink);padding:1.1rem 1.3rem;margin:0 0 2.25rem}
.post-toc h2{font-family:'Space Grotesk',sans-serif;font-size:.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:var(--coral-dark);margin:0 0 .6rem}
.post-toc ol{margin:0;padding-left:1.2rem}
.post-toc li{margin:.3rem 0;font-size:.95rem;line-height:1.4}
.post-toc a{color:var(--ink);text-decoration:none;font-weight:500}
.post-toc a:hover{color:var(--coral-dark);text-decoration:underline}
.prose{font-size:1.08rem;line-height:1.75;color:var(--ink)}
.prose>*+*{margin-top:1.15rem}
.prose h2{font-family:'Fraunces',serif;font-weight:800;font-size:clamp(1.5rem,3.4vw,2rem);line-height:1.15;letter-spacing:-.01em;margin-top:2.75rem;scroll-margin-top:6rem}
.prose h3{font-family:'Fraunces',serif;font-weight:700;font-size:1.3rem;margin-top:2rem}
.prose a{color:var(--coral-dark);font-weight:600;text-decoration:underline;text-underline-offset:2px}
.prose strong{font-weight:700}
.prose code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.88em;background:#FFF1B8;border:1.5px solid var(--ink);border-radius:6px;padding:.05em .35em;word-break:break-word}
.prose ul,.prose ol{padding-left:1.4rem}
.prose li{margin:.45rem 0}
.prose li::marker{color:var(--coral-dark);font-weight:700}
.prose blockquote{margin:2rem 0;background:#FFF1B8;border:2px solid var(--ink);border-radius:20px;box-shadow:5px 5px 0 var(--ink);padding:1.25rem 1.5rem;font-family:'Fraunces',serif;font-size:clamp(1.2rem,2.6vw,1.45rem);line-height:1.35;transform:rotate(-.6deg)}
.prose blockquote p{margin:0}
.prose figure{margin:2rem 0}
.prose figure img{display:block;width:100%;height:auto;border:2px solid var(--ink);border-radius:14px;box-shadow:5px 5px 0 var(--ink);background:#FFFDF9}
.prose figcaption{margin-top:.85rem;font-size:.88rem;line-height:1.5;color:var(--ink-soft);text-align:center}
.prose .post-note{font-size:.98rem;color:var(--ink-soft);font-style:italic}
.author-card{display:flex;gap:1.1rem;align-items:center;margin:3rem 0 2rem;background:var(--cream-2);border:2px solid var(--ink);border-radius:22px;box-shadow:5px 5px 0 var(--ink);padding:1.25rem 1.4rem}
.author-card img{width:76px;height:76px;border-radius:50%;border:2px solid var(--ink);object-fit:cover;flex-shrink:0}
.author-card .k{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:var(--coral-dark)}
.author-card h2{font-family:'Fraunces',serif;font-weight:800;font-size:1.3rem;margin:.15rem 0 .3rem;display:flex;align-items:center;gap:.5rem}
.author-card h2 a.name{color:var(--ink);text-decoration:none}
.author-card p{font-size:.95rem;line-height:1.5;margin:0}
.author-card .author-links{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.7rem}
.author-card .author-links a{font-size:.85rem;font-weight:700;color:var(--ink);background:#FFFDF9;border:1.5px solid var(--ink);border-radius:999px;padding:.35rem .85rem;text-decoration:none;box-shadow:2px 2px 0 var(--ink)}
.author-card .author-links a:hover{transform:translate(-1px,-1px);box-shadow:3px 3px 0 var(--ink)}
.related-proj{display:block;margin:0 0 2rem;text-decoration:none;color:var(--ink);background:#FFFDF9;border:2px solid var(--ink);border-radius:18px;box-shadow:4px 4px 0 var(--ink);padding:1rem 1.25rem;transition:transform .2s ease,box-shadow .2s ease}
.related-proj:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--ink)}
.related-proj .k{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:var(--coral-dark)}
.related-proj strong{display:block;font-family:'Fraunces',serif;font-size:1.15rem;margin-top:.2rem}
.blog-list{display:grid;gap:1.75rem;max-width:820px;margin:0 auto}
.post-card{display:block;text-decoration:none;color:var(--ink);background:var(--cream-2);border:2px solid var(--ink);border-radius:22px;box-shadow:5px 5px 0 var(--ink);overflow:hidden;transition:transform .2s ease,box-shadow .2s ease}
.post-card:hover{transform:translateY(-4px);box-shadow:7px 9px 0 var(--ink)}
.post-card img{display:block;width:100%;height:auto;border-bottom:2px solid var(--ink)}
.post-card-body{padding:1.25rem 1.4rem 1.4rem}
.post-card .meta{font-size:.84rem;font-weight:600;color:var(--ink-soft)}
.post-card h2{font-family:'Fraunces',serif;font-weight:800;font-size:clamp(1.35rem,3vw,1.75rem);line-height:1.15;margin:.4rem 0 .55rem}
.post-card p{font-size:1rem;line-height:1.55;margin:0 0 .9rem}
.post-card .post-tags{margin-bottom:1rem}
.post-card .go{font-weight:700;color:var(--coral-dark)}
@media (max-width:560px){.prose{font-size:1.02rem}.author-card{flex-direction:column;align-items:flex-start}.prose blockquote{transform:none;padding:1.1rem 1.2rem}.byline-meta{font-size:.85rem}}
"""


# ---------- small helpers ----------

def esc(s):
    return html.escape(s, quote=True)


def webp_size(path):
    d = open(path, 'rb').read(30)
    if d[12:16] == b'VP8 ':
        w, h = struct.unpack('<HH', d[26:30])
        return w & 0x3fff, h & 0x3fff
    if d[12:16] == b'VP8L':
        b = d[21:25]
        bits = int.from_bytes(b, 'little')
        return (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
    if d[12:16] == b'VP8X':
        return int.from_bytes(d[24:27], 'little') + 1, int.from_bytes(d[27:30], 'little') + 1
    raise ValueError('unknown webp: ' + path)


def slugify(s):
    s = re.sub(r'<[^>]+>', '', s).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:60].rstrip('-')


def nice_date(d):
    return f'{d.day} {d.strftime("%B %Y")}'


def iso(d):
    return f'{d.isoformat()}T00:00:00+05:30'


# ---------- Markdown (the subset the posts use) ----------

def inline(text):
    codes = []

    def keep(m):
        codes.append('<code>' + esc(m.group(1)) + '</code>')
        return f'\x00{len(codes) - 1}\x00'
    text = re.sub(r'`([^`]+)`', keep, text)
    text = esc(text)

    def link(m):
        label, url = m.group(1), html.unescape(m.group(2))
        ext = url.startswith('http')
        attrs = ' target="_blank" rel="noopener"' if ext else ''
        return f'<a href="{esc(url)}"{attrs}>{label}</a>'
    text = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', link, text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', text)
    return re.sub(r'\x00(\d+)\x00', lambda m: codes[int(m.group(1))], text)


def render_markdown(md, slug):
    """Return (html, toc, plain_text). The first '# ' heading and the italic
    line right after it are taken by the hero, so they are skipped here."""
    lines = md.split('\n')
    out, toc, plain = [], [], []
    i, first_img = 0, True
    skipped_title = skipped_sub = False
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith('# ') and not skipped_title:
            skipped_title = True
            i += 1
            continue
        if skipped_title and not skipped_sub and re.fullmatch(r'\*[^*].*\*', s):
            skipped_sub = True
            i += 1
            continue
        skipped_sub = True
        m = re.fullmatch(r'(#{2,3}) (.+)', s)
        if m:
            level = len(m.group(1))
            txt = inline(m.group(2))
            hid = slugify(m.group(2))
            if level == 2:
                toc.append((hid, txt))
            out.append(f'<h{level} id="{hid}">{txt}</h{level}>')
            plain.append(m.group(2))
            i += 1
            continue
        m = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', s)
        if m:
            alt, src = m.group(1), m.group(2)
            name = os.path.splitext(os.path.basename(src))[0]
            rel = f'assets/blog/{slug}/{name}.webp'
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                sys.exit(f'Missing image {rel}; convert {src} with cwebp first.')
            if not alt.strip():
                sys.exit(f'Image {src} has no alt text. Every image needs one.')
            w, h = webp_size(path)
            load = 'fetchpriority="high"' if first_img else 'loading="lazy"'
            first_img = False
            out.append(f'<figure>\n  <img src="/{rel}" alt="{esc(alt)}" width="{w}" height="{h}" {load} decoding="async">\n'
                       f'  <figcaption>{inline(alt)}</figcaption>\n</figure>')
            i += 1
            continue
        if s.startswith('>'):
            buf = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f'<blockquote><p>{inline(" ".join(buf))}</p></blockquote>')
            plain.append(' '.join(buf))
            continue
        if re.match(r'[-*] ', s) or re.match(r'\d+\. ', s):
            ordered = bool(re.match(r'\d+\. ', s))
            pat = r'\d+\. ' if ordered else r'[-*] '
            items = []
            while i < len(lines) and re.match(pat, lines[i].strip()):
                items.append(re.sub('^' + pat, '', lines[i].strip()))
                i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>\n' + '\n'.join(f'  <li>{inline(x)}</li>' for x in items) + f'\n</{tag}>')
            plain.extend(items)
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r'(#{1,3} |!\[|>|[-*] |\d+\. )', lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        # "**Lead line.**" on its own line, with text under it, becomes an h3
        lead = re.fullmatch(r'\*\*(.+)\*\*', buf[0])
        if lead and len(buf) > 1:
            out.append(f'<h3 id="{slugify(lead.group(1))}">{inline(lead.group(1))}</h3>')
            plain.append(lead.group(1))
            buf = buf[1:]
        para = ' '.join(buf)
        cls = ' class="post-note"' if re.fullmatch(r'\*[^*].*\*', para) else ''
        if cls:
            para = para[1:-1]
        out.append(f'<p{cls}>{inline(para)}</p>')
        plain.append(para)
    return '\n'.join(out), toc, ' '.join(plain)


def parse_post(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n', raw, re.S)
    if not m:
        sys.exit(f'{path}: missing front matter')
    meta = {}
    for line in m.group(1).split('\n'):
        k, _, v = line.partition(':')
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] == '"':
            v = v[1:-1]
        meta[k.strip()] = v
    body = raw[m.end():]
    for k in ('slug', 'title', 'seo_title', 'description', 'date'):
        if not meta.get(k):
            sys.exit(f'{path}: front matter needs "{k}"')
    meta['date'] = dt.date.fromisoformat(meta['date'])
    meta['updated'] = dt.date.fromisoformat(meta.get('updated') or meta['date'].isoformat())
    meta['tags'] = [t.strip() for t in meta.get('tags', '').split(',') if t.strip()]
    sub = re.search(r'^# .+\n+\*([^*].*)\*\s*$', body, re.M)
    meta['subtitle'] = sub.group(1) if sub else meta['description']
    meta['html'], meta['toc'], plain = render_markdown(body, meta['slug'])
    meta['words'] = len(re.findall(r"[\w'’]+", plain))
    meta['minutes'] = max(1, round(meta['words'] / WPM))
    meta['url'] = f'{SITE}/blog/{meta["slug"]}'
    meta['path'] = f'/blog/{meta["slug"]}'
    hero = f'assets/blog/{meta["slug"]}/01-hero.webp'
    meta['card_img'] = hero if os.path.exists(os.path.join(ROOT, hero)) else None
    og = f'assets/blog/{meta["slug"]}/og.jpg'
    meta['og'] = f'{SITE}/{og}' if os.path.exists(os.path.join(ROOT, og)) else f'{SITE}/assets/og-image.png'
    return meta


# ---------- page shell from the template ----------

def load_shell():
    t = open(TEMPLATE, encoding='utf-8').read()
    style = re.search(r'\n(  <style>.*?</style>\n(?:  <link rel="stylesheet"[^\n]*\n)*)</head>', t, re.S)
    nav = re.search(r'(  <!-- NAVBAR -->\n.*?<div class="nav-scrim"[^\n]*\n)', t, re.S)
    foot = re.search(r'(  <!-- FOOTER -->\n.*</html>\n?)', t, re.S)
    bridge = re.search(r'(      <aside class="svc-bridge.*?</aside>\n)', t, re.S)
    assert style and nav and foot and bridge, 'template markers not found'
    style = style.group(1).replace('</style>', BLOG_CSS.strip() + '</style>', 1)
    nav = nav.group(1)
    assert nav.count(' class="active"') == 1 and nav.count('<a href="/blog">') == 1
    nav = nav.replace(' class="active"', '').replace('<a href="/blog">', '<a href="/blog" class="active" aria-current="page">')
    return style, nav, foot.group(1), bridge.group(1)


def head(title, desc, url, og_type, image, schema, extra=''):
    return f'''<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}">
  <meta name="author" content="Rudra Trivedi">
  <link rel="canonical" href="{url}">
  <link rel="alternate" type="application/rss+xml" title="Rudra Trivedi: Blog" href="{SITE}/blog/feed.xml">
  <link rel="manifest" href="/site.webmanifest">
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="Rudra Trivedi">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:image" content="{image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
{extra}  <meta property="twitter:card" content="summary_large_image">
  <meta property="twitter:url" content="{url}">
  <meta property="twitter:title" content="{esc(title)}">
  <meta property="twitter:description" content="{esc(desc)}">
  <meta property="twitter:image" content="{image}">
  <link rel="icon" type="image/x-icon" href="/assets/favicon.ico">
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/assets/favicon-180.png">
  <link rel="icon" type="image/png" sizes="192x192" href="/assets/favicon-192.png">
  <meta name="theme-color" content="#FF5233">

  <script type="application/ld+json">
{json.dumps(schema, indent=2, ensure_ascii=False)}
  </script>
'''


PERSON = {'@type': 'Person', '@id': f'{SITE}/#person', 'name': 'Rudra Trivedi',
          'url': f'{SITE}/about', 'sameAs': [LINKEDIN], 'jobTitle': 'GTM Engineer'}
ORG = {'@type': 'Organization', '@id': f'{SITE}/#org', 'name': 'Firstword', 'url': f'{SITE}/',
       'logo': {'@type': 'ImageObject', 'url': f'{SITE}/assets/f1rstword-logo.png'}}


def byline(p):
    return f'''    <div class="byline">
      <span class="byline-who">
        <img src="/assets/rudra-480.webp" alt="Rudra Trivedi" width="32" height="32">
        <span>Written by <a class="name" href="/about" rel="author">Rudra Trivedi</a></span>
        <a class="li-link" href="{LINKEDIN}" target="_blank" rel="noopener me" aria-label="Rudra Trivedi on LinkedIn" title="Rudra Trivedi on LinkedIn">{LI_SVG}</a>
      </span>
      <span class="byline-meta"><time datetime="{p['date'].isoformat()}">{nice_date(p['date'])}</time> · {p['minutes']} min read</span>
    </div>'''


def tags_html(tags):
    if not tags:
        return ''
    return '<ul class="post-tags" aria-label="Topics">' + ''.join(f'<li>{esc(t)}</li>' for t in tags) + '</ul>'


def build_post(p, shell):
    style, nav, foot, bridge = shell
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'BlogPosting', '@id': p['url'] + '#article', 'url': p['url'],
         'mainEntityOfPage': {'@type': 'WebPage', '@id': p['url']},
         'headline': p['title'], 'description': p['description'],
         'image': [p['og']] + ([f'{SITE}/{p["card_img"]}'] if p['card_img'] else []),
         'datePublished': iso(p['date']), 'dateModified': iso(p['updated']),
         'author': PERSON, 'publisher': ORG,
         'isPartOf': {'@type': 'Blog', '@id': f'{SITE}/blog#blog', 'name': 'Rudra Trivedi: Blog'},
         'keywords': ', '.join(p['tags']), 'wordCount': p['words'],
         'timeRequired': f'PT{p["minutes"]}M', 'inLanguage': 'en',
         **({'about': {'@type': 'CreativeWork', 'name': p['project'], 'url': SITE + p['project_url']}} if p.get('project') else {})},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{SITE}/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': f'{SITE}/blog'},
            {'@type': 'ListItem', 'position': 3, 'name': p['title'], 'item': p['url']}]}]}
    extra = (f'  <meta property="article:published_time" content="{iso(p["date"])}">\n'
             f'  <meta property="article:modified_time" content="{iso(p["updated"])}">\n'
             f'  <meta property="article:author" content="{LINKEDIN}">\n'
             + ''.join(f'  <meta property="article:tag" content="{esc(t)}">\n' for t in p['tags']))
    toc = ''
    if len(p['toc']) >= 3:
        toc = ('      <nav class="post-toc" aria-labelledby="toc-h">\n        <h2 id="toc-h">In this post</h2>\n        <ol>\n'
               + ''.join(f'          <li><a href="#{hid}">{txt}</a></li>\n' for hid, txt in p['toc'])
               + '        </ol>\n      </nav>\n')
    related = ''
    if p.get('project'):
        related = (f'      <a class="related-proj" href="{esc(p["project_url"])}">\n'
                   f'        <span class="k">The project behind this post</span>\n'
                   f'        <strong>{esc(p["project"])}: read the case study →</strong>\n      </a>\n')
    updated = ''
    if p['updated'] != p['date']:
        updated = f' · Updated <time datetime="{p["updated"].isoformat()}">{nice_date(p["updated"])}</time>'
    return head(p['seo_title'], p['description'], p['url'], 'article', p['og'], schema, extra) + style + f'''</head>

<body>

{nav}
  <!-- HERO -->
  <section class="hero post-hero">
    <div class="hero-eyebrow"><span class="dot"></span> Blog{' · ' + esc(p['tags'][0]) if p['tags'] else ''}</div>
    <h1 class="hero-headline">{esc(p['title'])}</h1>
    <p class="hero-sub">{inline(p['subtitle'])}</p>
{byline(p)}
  </section>

  <svg class="wave-divider" viewBox="0 0 1440 60" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M0,30 C360,60 1080,0 1440,30 L1440,60 L0,60 Z" fill="#FFF6EE"/>
  </svg>

  <!-- POST -->
  <main class="post-body">
    <article class="post-inner">
      <div class="post-top">
        <a href="/blog" class="back-btn">← All posts</a>
        {tags_html(p['tags'])}
      </div>
      <p class="cs-updated">Published <time datetime="{p['date'].isoformat()}">{nice_date(p['date'])}</time>{updated}</p>
{toc}
      <div class="prose">
{p['html']}
      </div>

      <aside class="author-card" aria-label="About the author">
        <img src="/assets/rudra-480.webp" alt="Rudra Trivedi" width="76" height="76" loading="lazy">
        <div>
          <span class="k">Written by</span>
          <h2><a class="name" href="/about" rel="author">Rudra Trivedi</a> <a class="li-link" href="{LINKEDIN}" target="_blank" rel="noopener me" aria-label="Rudra Trivedi on LinkedIn" title="Rudra Trivedi on LinkedIn">{LI_SVG}</a></h2>
          <p>Freelance GTM engineer in Mumbai. I build go to market systems that run without you, and I write about what I build, what it costs and what breaks.</p>
          <div class="author-links"><a href="/about">More about me</a><a href="/case-studies">See my work</a><a href="{LINKEDIN}" target="_blank" rel="noopener">Follow on LinkedIn</a></div>
        </div>
      </aside>

{related}{bridge}
    </article>
  </main>

  <!-- FINAL CTA -->
  <section class="final-cta">
    <h2 class="reveal">Not sure what your stack is worth?</h2>
    <p class="reveal delay-1">I help founders and sales teams build go to market systems that show what works and what it costs. It starts with a free 30-minute diagnostic.</p>
    <button type="button" class="cta-btn reveal delay-2" onclick="openContactModal()" id="finalCtaBtn">
      Book a free diagnostic
      {ARROW}
    </button>
  </section>

''' + foot


def build_index(posts, shell):
    style, nav, foot, _ = shell
    url = f'{SITE}/blog'
    title = 'Blog: GTM Build Stories and Lessons | Rudra Trivedi'
    desc = ('Build stories from go to market work by Rudra Trivedi: what I tried, what it cost, '
            'what broke, and what I would do next. Lead data, outbound, automation and GTM systems.')
    modified = max(p['updated'] for p in posts)
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Blog', '@id': url + '#blog', 'url': url, 'name': 'Rudra Trivedi: Blog',
         'description': desc, 'inLanguage': 'en', 'author': PERSON, 'publisher': ORG,
         'isPartOf': {'@id': f'{SITE}/#website'}, 'dateModified': iso(modified),
         'blogPost': [{'@type': 'BlogPosting', '@id': p['url'] + '#article', 'url': p['url'],
                       'headline': p['title'], 'datePublished': iso(p['date']),
                       'dateModified': iso(p['updated']), 'author': {'@id': f'{SITE}/#person'},
                       'image': p['og']} for p in posts]},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{SITE}/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': url}]}]}
    cards = []
    for n, p in enumerate(posts):
        img = ''
        if p['card_img']:
            w, h = webp_size(os.path.join(ROOT, p['card_img']))
            load = 'fetchpriority="high"' if n == 0 else 'loading="lazy"'
            img = f'\n        <img src="/{p["card_img"]}" alt="" width="{w}" height="{h}" {load} decoding="async">'
        cards.append(f'''      <a class="post-card" href="{p['path']}">{img}
        <div class="post-card-body">
          <span class="meta"><time datetime="{p['date'].isoformat()}">{nice_date(p['date'])}</time> · {p['minutes']} min read</span>
          <h2>{esc(p['title'])}</h2>
          <p>{esc(p['description'])}</p>
          {tags_html(p['tags'])}
          <span class="go">Read the post →</span>
        </div>
      </a>''')
    return head(title, desc, url, 'website', f'{SITE}/assets/og-image.png', schema) + style + f'''</head>

<body>

{nav}
  <!-- HERO -->
  <section class="hero post-hero">
    <div class="hero-eyebrow"><span class="dot"></span> Blog · Build stories</div>
    <h1 class="hero-headline">Notes From the Build.</h1>
    <p class="hero-sub">What I tried, what it cost, what broke, and what I would do next. Written from real go to market work, numbers included.</p>
    <div class="byline">
      <span class="byline-who">
        <img src="/assets/rudra-480.webp" alt="Rudra Trivedi" width="32" height="32">
        <span>Written by <a class="name" href="/about" rel="author">Rudra Trivedi</a></span>
        <a class="li-link" href="{LINKEDIN}" target="_blank" rel="noopener me" aria-label="Rudra Trivedi on LinkedIn" title="Rudra Trivedi on LinkedIn">{LI_SVG}</a>
      </span>
    </div>
  </section>

  <svg class="wave-divider" viewBox="0 0 1440 60" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M0,30 C360,60 1080,0 1440,30 L1440,60 L0,60 Z" fill="#FFF6EE"/>
  </svg>

  <main class="post-body">
    <h2 class="kicker" style="text-align:center;font-size:.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:var(--coral-dark);margin:0 0 1.5rem">Latest posts</h2>
    <div class="blog-list">
{chr(10).join(cards)}
    </div>
  </main>

  <!-- FINAL CTA -->
  <section class="final-cta">
    <h2 class="reveal">Want this built for your team?</h2>
    <p class="reveal delay-1">Everything I write about comes from systems I build. If your go to market needs one, it starts with a free 30-minute diagnostic.</p>
    <button type="button" class="cta-btn reveal delay-2" onclick="openContactModal()" id="finalCtaBtn">
      Book a free diagnostic
      {ARROW}
    </button>
  </section>

''' + foot


def build_feed(posts):
    def rfc(d):
        return dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime('%a, %d %b %Y %H:%M:%S %z')
    items = ''.join(f'''  <item>
    <title>{esc(p['title'])}</title>
    <link>{p['url']}</link>
    <guid isPermaLink="true">{p['url']}</guid>
    <pubDate>{rfc(p['date'])}</pubDate>
    <description>{esc(p['description'])}</description>
  </item>
''' for p in posts)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>Rudra Trivedi: Blog</title>
  <link>{SITE}/blog</link>
  <atom:link href="{SITE}/blog/feed.xml" rel="self" type="application/rss+xml"/>
  <description>Build stories from go to market work by Rudra Trivedi.</description>
  <language>en</language>
  <lastBuildDate>{rfc(max(p['updated'] for p in posts))}</lastBuildDate>
{items}</channel>
</rss>
'''


def replace_block(path, start, end, body, anchor):
    s = open(path, encoding='utf-8').read()
    block = f'{start}\n{body}{end}\n'
    if start in s:
        s = re.sub(re.escape(start) + r'.*?' + re.escape(end) + r'\n', lambda _: block, s, count=1, flags=re.S)
    else:
        assert s.count(anchor) == 1, f'{path}: anchor not found once'
        s = s.replace(anchor, block + anchor)
    open(path, 'w', encoding='utf-8').write(s)


def main():
    posts = [parse_post(f) for f in glob.glob(os.path.join(ROOT, 'content/blog/*/article.md'))]
    if not posts:
        sys.exit('no posts')
    posts.sort(key=lambda p: p['date'], reverse=True)
    shell = load_shell()
    os.makedirs(os.path.join(ROOT, 'blog'), exist_ok=True)
    for p in posts:
        open(os.path.join(ROOT, 'blog', p['slug'] + '.html'), 'w', encoding='utf-8').write(build_post(p, shell))
        print(f'blog/{p["slug"]}.html  {p["words"]} words, {p["minutes"]} min')
    open(os.path.join(ROOT, 'blog.html'), 'w', encoding='utf-8').write(build_index(posts, shell))
    open(os.path.join(ROOT, 'blog', 'feed.xml'), 'w', encoding='utf-8').write(build_feed(posts))

    newest = max(p['updated'] for p in posts).isoformat()
    sm = f'  <url>\n    <loc>{SITE}/blog</loc>\n    <lastmod>{newest}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
    for p in posts:
        sm += (f'  <url>\n    <loc>{p["url"]}</loc>\n    <lastmod>{p["updated"].isoformat()}</lastmod>\n'
               f'    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n')
    replace_block(os.path.join(ROOT, 'sitemap.xml'), '  <!-- blog:start -->', '  <!-- blog:end -->', sm, '</urlset>')

    ll = '## Blog\n\n' + f'- [Blog]({SITE}/blog): Build stories from go to market work by Rudra Trivedi, with real numbers.\n'
    ll += ''.join(f'- [{p["title"]}]({p["url"]}): {p["description"]}\n' for p in posts) + '\n'
    replace_block(os.path.join(ROOT, 'llms.txt'), '<!-- blog:start -->', '<!-- blog:end -->', ll, '## Detailed Context')

    lf = '## Blog (`/blog`)\n\nWritten by Rudra Trivedi. Build stories with the method, the numbers and what broke.\n\n'
    for p in posts:
        lf += (f'### {p["title"]} (`{p["path"]}`)\n- **Published**: {p["date"].isoformat()}\n'
               f'- **Topics**: {", ".join(p["tags"])}\n- **Summary**: {p["description"]}\n')
        if p['toc']:
            lf += '- **Sections**: ' + '; '.join(re.sub(r'<[^>]+>', '', html.unescape(t)) for _, t in p['toc']) + '\n'
        if p.get('project'):
            lf += f'- **Related project**: {p["project"]} ({p["project_url"]})\n'
        lf += '\n'
    replace_block(os.path.join(ROOT, 'llms-full.txt'), '<!-- blog:start -->', '<!-- blog:end -->', lf, '---\n\n## Contact')
    print('blog.html, blog/feed.xml, sitemap.xml, llms.txt, llms-full.txt updated')


if __name__ == '__main__':
    main()
