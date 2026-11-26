#!/usr/bin/env python3
"""Builds the Retirement Plan Karo blog.

Reads content/posts/*.md (front matter between --- lines) and writes the
static site to public/. Run: python3 build.py
"""
import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import markdown
from cover import make_cover

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "content" / "posts"
OUT = ROOT / "public"
SITE_URL = "https://blog.retirementplankaro.com"
MAIN_SITE = "https://retirementplankaro.com"
SITE_NAME = "Retirement Plan Karo Blog"

CSS = """
:root{--brand:#0f5132;--brand2:#198754;--accent:#f59f00;--ink:#1d2433;--muted:#5b6475;--bg:#f7f8fa;--card:#fff;--line:#e6e9ef}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans","Noto Sans Devanagari",sans-serif;color:var(--ink);background:var(--bg);line-height:1.7;font-size:17px}
a{color:var(--brand2)}header.top{background:var(--brand);color:#fff}header.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 18px}
header.top a{color:#fff;text-decoration:none;font-weight:700}.logo{font-size:20px}.logo span{color:var(--accent)}
.cta-btn{background:var(--accent);color:#1d2433!important;padding:8px 14px;border-radius:8px;font-size:14px;white-space:nowrap}
.wrap{max-width:780px;margin:0 auto;padding:0 18px}main{padding:28px 0 40px}
h1{font-size:30px;line-height:1.3;margin:0 0 10px}h2{font-size:23px;margin-top:34px}h3{font-size:19px}
.meta{color:var(--muted);font-size:14px;margin-bottom:22px}
article{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:26px}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:15px}th,td{border:1px solid var(--line);padding:9px 10px;text-align:left}th{background:#eef6f1}
blockquote{margin:16px 0;padding:12px 16px;background:#fff8e6;border-left:4px solid var(--accent);border-radius:6px}
.tool-box{margin:28px 0;padding:20px;border-radius:12px;background:linear-gradient(135deg,#0f5132,#198754);color:#fff}
.tool-box a{display:inline-block;margin-top:10px;background:var(--accent);color:#1d2433;padding:10px 18px;border-radius:8px;font-weight:700;text-decoration:none}
.post-list{list-style:none;padding:0;margin:0}.post-list li{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:14px}
.post-list a.t{font-size:20px;font-weight:700;text-decoration:none;color:var(--ink)}.post-list p{margin:6px 0 0;color:var(--muted)}
.disclaimer{font-size:13px;color:var(--muted);margin-top:28px;border-top:1px solid var(--line);padding-top:12px}
footer{text-align:center;color:var(--muted);font-size:14px;padding:24px 0 40px}
@media(max-width:600px){h1{font-size:25px}article{padding:18px}body{font-size:16px}}
"""

DISCLAIMER = ("This article is for education only and is not investment advice. "
              "Returns shown are assumptions, not guarantees. Please consult a "
              "SEBI-registered adviser before making investment decisions.")


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path.name}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    for key in ("title", "description", "date", "slug"):
        if not meta.get(key):
            raise ValueError(f"{path.name}: front matter needs '{key}'")
    meta["body_md"] = m.group(2)
    meta["dt"] = datetime.strptime(meta["date"], "%Y-%m-%d")
    return meta


def page(title, description, canonical, body, extra_head=""):
    t, d = html.escape(title), html.escape(description)
    return f"""<!DOCTYPE html>
<html lang="{'hi' if re.search('[ऀ-ॿ]', title) else 'en'}">
<head>
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','GTM-P2T92LMS');</script>
<!-- End Google Tag Manager -->
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{SITE_URL}/rss.xml">
<style>{CSS}</style>
{extra_head}
</head>
<body>
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-P2T92LMS"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
<header class="top"><div class="wrap">
<a class="logo" href="/">Retirement Plan <span>Karo</span></a>
<a class="cta-btn" href="{MAIN_SITE}/retirement-planner/?utm_source=blog&amp;utm_medium=header&amp;utm_campaign=blog-header">Free Retirement Plan &rarr;</a>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer>&copy; {datetime.now().year} <a href="{MAIN_SITE}/?utm_source=blog&amp;utm_medium=footer&amp;utm_campaign=blog-footer">retirementplankaro.com</a> &middot; <a href="/">Blog</a> &middot; <a href="/rss.xml">RSS</a></footer>
</body>
</html>
"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    posts = sorted((parse(p) for p in POSTS_DIR.glob("*.md")),
                   key=lambda p: p["date"], reverse=True)
    slugs = [p["slug"] for p in posts]
    if len(slugs) != len(set(slugs)):
        raise ValueError("duplicate slug in content/posts")

    md = markdown.Markdown(extensions=["tables", "toc", "sane_lists"])
    for p in posts:
        md.reset()
        body_html = md.convert(p["body_md"])
        url = f"{SITE_URL}/{p['slug']}/"
        tool = ""
        if p.get("tool_url"):
            if "utm_source=" not in p["tool_url"]:
                sep = "&" if "?" in p["tool_url"] else "?"
                p["tool_url"] += f"{sep}utm_source=blog&utm_medium=article&utm_campaign={p['slug']}"
            tool = (f'<div class="tool-box"><strong>{html.escape(p.get("tool_name", "Free Calculator"))}</strong>'
                    f'<div>Apna exact number 30 second mein nikaalein, bilkul free.</div>'
                    f'<a href="{html.escape(p["tool_url"])}">Try it free &rarr;</a></div>')
        schema = {
            "@context": "https://schema.org", "@type": "BlogPosting",
            "headline": p["title"], "description": p["description"],
            "datePublished": p["date"], "dateModified": p["date"],
            "mainEntityOfPage": url,
            "author": {"@type": "Organization", "name": "Retirement Plan Karo", "url": MAIN_SITE},
            "publisher": {"@type": "Organization", "name": "Retirement Plan Karo", "url": MAIN_SITE},
        }
        make_cover(p["title"], p.get("tool_name", ""), OUT / p["slug"] / "cover.jpg")
        cover_url = f"{SITE_URL}/{p['slug']}/cover.jpg"
        schema["image"] = cover_url
        head = (f'<meta property="og:type" content="article"><meta property="og:title" content="{html.escape(p["title"])}">'
                f'<meta property="og:description" content="{html.escape(p["description"])}">'
                f'<meta property="og:url" content="{url}"><meta property="og:image" content="{cover_url}">'
                f'<meta name="twitter:card" content="summary_large_image">\n'
                f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>')
        faq = re.findall(r"^### (.+\?)\s*\n+(.+?)(?=\n### |\n## |\Z)", p["body_md"], re.M | re.S)
        if faq:
            faq_schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q.strip(),
                 "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"\s+", " ", a).strip()}}
                for q, a in faq]}
            head += f'\n<script type="application/ld+json">{json.dumps(faq_schema, ensure_ascii=False)}</script>'
        body = (f'<article><h1>{html.escape(p["title"])}</h1>'
                f'<div class="meta">{p["dt"].strftime("%d %B %Y")} &middot; Retirement Plan Karo</div>'
                f'{body_html}{tool}<p class="disclaimer">{DISCLAIMER}</p></article>')
        d = OUT / p["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page(p["title"], p["description"], url, body, head), encoding="utf-8")

    items = "".join(
        f'<li><a class="t" href="/{p["slug"]}/">{html.escape(p["title"])}</a>'
        f'<p>{html.escape(p["description"])}</p></li>' for p in posts)
    index_body = ('<h1>Retirement Plan Karo Blog</h1>'
                  '<p class="meta">Retirement, SIP, tax, EPF, NPS, PPF: simple language mein, roz ek naya article.</p>'
                  f'<ul class="post-list">{items}</ul>')
    (OUT / "index.html").write_text(page(
        "Retirement Plan Karo Blog: Retirement, SIP, Tax and Pension Guides",
        "Simple guides on retirement planning, SIP, income tax, EPF, NPS and PPF for Indian families.",
        SITE_URL + "/", index_body), encoding="utf-8")

    urls = [f"<url><loc>{SITE_URL}/</loc></url>"] + [
        f"<url><loc>{SITE_URL}/{p['slug']}/</loc><lastmod>{p['date']}</lastmod></url>" for p in posts]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls) + "</urlset>\n", encoding="utf-8")
    rss_items = "".join(
        f"<item><title>{html.escape(p['title'])}</title><link>{SITE_URL}/{p['slug']}/</link>"
        f"<guid>{SITE_URL}/{p['slug']}/</guid><pubDate>{p['dt'].strftime('%a, %d %b %Y 06:00:00 +0530')}</pubDate>"
        f"<description>{html.escape(p['description'])}</description></item>" for p in posts[:30])
    (OUT / "rss.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE_NAME}</title>'
        f"<link>{SITE_URL}/</link><description>Retirement and money guides for India</description>{rss_items}</channel></rss>\n",
        encoding="utf-8")
    # LinkedIn feed: every article with its cover image (enclosure), links carry LinkedIn UTM tags.
    # Read by the free Zapier "RSS -> LinkedIn company update" automation (posts as an image post).
    li_items = []
    for p in posts[:15]:
        utm = f"utm_source=linkedin&utm_medium=social&utm_campaign={p['slug']}"
        link = f"{SITE_URL}/{p['slug']}/?{utm}"
        tool = re.sub(r"utm_source=blog&utm_medium=article", "utm_source=linkedin&utm_medium=social", p.get("tool_url", ""))
        text = p.get("linkedin_text") or (
            f"{p['title']}\n\n{p['description']}\n\n"
            + (f"{p.get('tool_name', 'Free calculator')}: {tool}\n\n" if tool else "")
            + f"Pura article padhein: {link}\n\n#RetirementPlanning #PersonalFinance #MoneyTips")
        li_items.append(
            f"<item><title>{html.escape(p['title'])}</title><link>{html.escape(link)}</link>"
            f"<guid isPermaLink=\"false\">{SITE_URL}/{p['slug']}/</guid>"
            f"<pubDate>{p['dt'].strftime('%a, %d %b %Y 06:00:00 +0530')}</pubDate>"
            f"<description>{html.escape(text)}</description>"
            f'<enclosure url="{SITE_URL}/{p["slug"]}/cover.jpg" type="image/jpeg" length="0"/></item>')
    (OUT / "linkedin.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE_NAME} LinkedIn</title>'
        f"<link>{SITE_URL}/</link><description>New articles for LinkedIn</description>{''.join(li_items)}</channel></rss>\n",
        encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(posts)} post(s) into {OUT}")


if __name__ == "__main__":
    build()
