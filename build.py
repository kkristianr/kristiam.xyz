#!/usr/bin/env python3
"""Build static crawlable HTML from src/pages + posts/*.md."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
SRC_PAGES = ROOT / "src" / "pages"
POSTS_DIR = ROOT / "posts"
LOGO = (ROOT / "src" / "partials" / "logo.svg").read_text(encoding="utf-8").strip()

SITE_ORIGIN = "https://kristiam.xyz"
SITE_NAME = "kristiam.xyz"
PERSON_ID = f"{SITE_ORIGIN}/#person"
FOOTER_UPDATED = "11.10.2026"

MENU = [
    ("/dev-ai", "dev"),
    ("/running", "running"),
    ("/random", "xyz"),
    ("/cv", "cv"),
]

PAGES = [
    {
        "key": "home",
        "path": "/",
        "outfile": "index.html",
        "title": "Kristian Ristic - data scientist",
        "description": "Hello, I (he/him) am a software/ai engineer based in Vienna, Austria. I like exploring new technologies and building practical solutions.",
        "h1": "Kristian Ristic - personal website of a data scientist and runner",
        "active": None,
        "src": "home.html",
    },
    {
        "key": "cv",
        "path": "/cv",
        "outfile": "cv.html",
        "title": "KR - curriculum vitae",
        "description": "Curriculum vitae of Kristian Ristic: work experience, education, projects, and skills.",
        "h1": "Kristian Ristic - curriculum vitae",
        "active": "/cv",
        "src": "cv.html",
    },
    {
        "key": "running",
        "path": "/running",
        "outfile": "running.html",
        "title": "KR - my running journey",
        "description": "Running journey of Kristian Ristic: personal bests, goals, and training updates.",
        "h1": "Kristian Ristic - running",
        "active": "/running",
        "src": "running.html",
    },
    {
        "key": "running-tools",
        "path": "/running-tools",
        "outfile": "running-tools.html",
        "title": "Running tools",
        "description": "Minimal running pace, lap, and performance planning tools.",
        "h1": "Running tools",
        "active": "/running",
        "src": "running-tools.html",
        "extra_head": (
            '    <link rel="stylesheet" href="/running-tools.css">\n'
            '    <link rel="manifest" href="/running-tools.webmanifest">\n'
            '    <meta name="apple-mobile-web-app-capable" content="yes">\n'
            '    <meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
            '    <meta name="apple-mobile-web-app-title" content="Running tools">\n'
            '    <meta name="theme-color" content="#ffffff">'
        ),
        "extra_scripts": '    <script src="/running-tools.js"></script>',
        "body_class": "running-tools-body",
    },
    {
        "key": "dev-ai",
        "path": "/dev-ai",
        "outfile": "dev-ai.html",
        "title": "KR - my projects",
        "description": "AI, NLP, and data science projects and articles by Kristian Ristic.",
        "h1": "Kristian Ristic - AI and data science writing",
        "active": "/dev-ai",
        "src": "dev-ai.html",
    },
    {
        "key": "random",
        "path": "/random",
        "outfile": "random.html",
        "title": "KR - random stuff",
        "description": "Random notes and thoughts by Kristian Ristic.",
        "h1": "Kristian Ristic - random thoughts",
        "active": "/random",
        "src": "random.html",
    },
]

PROFILES = [
    ("LinkedIn", "https://linkedin.com/in/kristianristic"),
    ("XING", "https://www.xing.com/profile/Kristian_Ristic3"),
    ("GitHub", "https://github.com/kkristianr"),
    ("Strava", "https://www.strava.com/athletes/ristick"),
    ("Instagram", "https://www.instagram.com/kristic_an/"),
    ("UTMB", "https://utmb.world/en/runner/9094640.kristian.ristic"),
    ("ÖFB", "https://www.oefb.at/Profile/Spieler/999386?Kristian-Ristic"),
    ("Thesis", "https://repositum.tuwien.at/handle/20.500.12708/216545"),
    ("DOI", "https://doi.org/10.34726/hss.2025.130460"),
    ("RacePace", "https://findracepace.com"),
]

SAME_AS = [url for _, url in PROFILES]

KNOWS_ABOUT = [
    "Artificial Intelligence",
    "Natural Language Processing",
    "Data Science",
    "Track & field",
    "Running",
    "Running coach",
    "Sports data",
    "Performance analysis",
    "Performance predictions",
    "Trail running",
]

HOME_KEYWORDS = [
    "Kristian Ristic",
    "data scientist",
    "AI engineer",
    "Vienna",
    "NLP",
    "running",
    "RacePace",
    "ProTeam Vienna",
    "AK Smederevo",
]

SITEMAP_PRIORITY = {
    "/": "1.0",
    "/cv": "0.8",
    "/running": "0.8",
    "/dev-ai": "0.8",
    "/random": "0.6",
}

DEV_CATEGORIES = frozenset({"ai", "nlp", "stats"})
PARENT_BY_CATEGORY = {
    "running": "/running",
    "random": "/random",
}


# --- posts -----------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match:
        return {}, text

    meta: dict = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        value = raw.strip()
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip('"') for v in value[1:-1].split(",") if v.strip()]
        elif len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        meta[key.strip()] = value
    return meta, match.group(2)


def parse_eu_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    if "." in date_str:
        day, month, year = date_str.split(".")
        return datetime(int(year), int(month), int(day))
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None


def format_display_date(date_str: str) -> str:
    dt = parse_eu_date(date_str)
    if not dt:
        return date_str or ""
    return f"{dt.day} {dt.strftime('%B')} {dt.year}"


def iso_date(date_str: str) -> str | None:
    dt = parse_eu_date(date_str)
    return dt.date().isoformat() if dt else None


def load_posts() -> list[dict]:
    posts = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        categories = meta.get("categories") or []
        if isinstance(categories, str):
            categories = [categories]
        posts.append(
            {
                "slug": path.stem,
                "categories": categories,
                "title": meta.get("title") or "No title",
                "date": meta.get("date") or "",
                "excerpt": meta.get("excerpt") or "",
                "body": body,
                "sort": parse_eu_date(meta.get("date") or "") or datetime.min,
            }
        )
    posts.sort(key=lambda p: p["sort"], reverse=True)
    return posts


def md_to_html(body: str) -> str:
    return markdown.markdown(
        body,
        extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
    )


def article_parent(post: dict) -> str:
    for category, path in PARENT_BY_CATEGORY.items():
        if category in post["categories"]:
            return path
    return "/dev-ai"


def post_path(post: dict) -> str:
    return f"{article_parent(post)}/{post['slug']}"


def posts_with_any(posts: list[dict], categories: frozenset[str] | set[str]) -> list[dict]:
    return [p for p in posts if categories.intersection(p["categories"])]


# --- JSON-LD ---------------------------------------------------------------


def person_jsonld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "@id": PERSON_ID,
        "name": "Kristian Ristic",
        "url": SITE_ORIGIN,
        "image": f"{SITE_ORIGIN}/favicon/apple-touch-icon.png",
        "jobTitle": ["Data Scientist", "AI Engineer"],
        "description": "Data scientist / AI engineer and passionate runner based in Vienna, Austria.",
        "worksFor": {
            "@type": "Organization",
            "name": "RacePace",
            "url": "https://findracepace.com",
        },
        "alumniOf": [{"@type": "CollegeOrUniversity", "name": "TU Wien"}],
        "memberOf": [
            {"@type": "SportsOrganization", "name": "ProTeam Vienna"},
            {"@type": "SportsOrganization", "name": "AK Smederevo"},
        ],
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Vienna",
            "addressCountry": "AT",
        },
        "knowsAbout": KNOWS_ABOUT,
        "sameAs": SAME_AS,
    }


def website_jsonld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": f"{SITE_ORIGIN}/#website",
        "name": SITE_NAME,
        "url": SITE_ORIGIN,
        "author": {"@id": PERSON_ID},
        "publisher": {"@id": PERSON_ID},
        "inLanguage": "en",
    }


def profile_page_jsonld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "@id": f"{SITE_ORIGIN}/#profilepage",
        "url": f"{SITE_ORIGIN}/",
        "name": "Kristian Ristic",
        "isPartOf": {"@id": f"{SITE_ORIGIN}/#website"},
        "mainEntity": {"@id": PERSON_ID},
        "about": {"@id": PERSON_ID},
    }


def article_jsonld(post: dict) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": post["excerpt"] or post["title"],
        "datePublished": iso_date(post["date"]),
        "author": {"@id": PERSON_ID},
        "mainEntityOfPage": f"{SITE_ORIGIN}{post_path(post)}",
        "url": f"{SITE_ORIGIN}{post_path(post)}",
        "inLanguage": "en",
        "keywords": ", ".join(post["categories"]),
    }


def script_ld(blocks: list[dict]) -> str:
    return "".join(
        f'<script type="application/ld+json">\n{json.dumps(block, ensure_ascii=False, indent=2)}\n</script>\n'
        for block in blocks
    )


# --- HTML fragments --------------------------------------------------------


def menu_html(active: str | None) -> str:
    parts = []
    for href, label in MENU:
        cls = "menu-link active" if active == href else "menu-link"
        parts.append(f'<a class="{cls}" href="{href}">{label}</a>')
    return " ".join(parts)


def render_post_list(posts: list[dict], *, container_id: str, empty: str) -> str:
    if not posts:
        return f'<div id="{container_id}"><div class="no-posts">{empty}</div></div>'
    items = []
    for post in posts:
        display = format_display_date(post["date"])
        items.append(
            f'<a class="post-list-item" href="{post_path(post)}">'
            f'<span class="post-list-date">{html.escape(display)}</span>'
            f'<span class="post-list-title">- {html.escape(post["title"])}</span>'
            f"</a>"
        )
    return f'<div id="{container_id}">{"".join(items)}</div>'


def render_post_cards(posts: list[dict]) -> str:
    if not posts:
        return '<div id="posts-container"><div class="no-posts">no posts found</div></div>'
    items = []
    for post in posts:
        cats = " ".join(post["categories"])
        items.append(
            f'<a class="post-item" href="{post_path(post)}" data-categories="{html.escape(cats)}">'
            f'<h3 class="post-title">{html.escape(post["title"])}</h3>'
            f'<p class="post-excerpt">{html.escape(post["excerpt"])}</p>'
            f'<div class="post-meta"><span class="post-date">{html.escape(format_display_date(post["date"]))}</span></div>'
            f"</a>"
        )
    return f'<div id="posts-container">{"".join(items)}</div>'


def fill_post_markers(content: str, posts: list[dict]) -> str:
    running = [p for p in posts if "running" in p["categories"]]
    random_posts = [p for p in posts if "random" in p["categories"]]
    dev_posts = posts_with_any(posts, DEV_CATEGORIES)
    return (
        content.replace(
            "<!--POSTS:running-->",
            render_post_list(running, container_id="running-posts", empty="no posts yet :("),
        )
        .replace(
            "<!--POSTS:random-->",
            render_post_list(random_posts, container_id="random-posts", empty="no posts yet :("),
        )
        .replace("<!--POSTS:dev-ai-->", render_post_cards(dev_posts))
    )


def home_extra_head() -> str:
    me_links = "\n".join(f'    <link rel="me" href="{url}">' for url in SAME_AS)
    return (
        '    <meta name="author" content="Kristian Ristic">\n'
        '    <meta name="robots" content="index, follow">\n'
        f'    <meta name="keywords" content="{html.escape(", ".join(HOME_KEYWORDS))}">\n'
        f"{me_links}"
    )


def layout(
    *,
    title: str,
    description: str,
    canonical_path: str,
    h1: str | None,
    active: str | None,
    body: str,
    extra_head: str = "",
    extra_scripts: str = "",
    body_class: str = "",
    json_ld: list[dict] | None = None,
    og_type: str = "website",
) -> str:
    canonical = f"{SITE_ORIGIN}/" if canonical_path == "/" else f"{SITE_ORIGIN}{canonical_path}"
    safe_title = html.escape(title, quote=True)
    safe_desc = html.escape(description, quote=True)
    h1_html = f'    <h1 class="h1-title">{html.escape(h1)}</h1>\n' if h1 else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <meta name="description" content="{safe_desc}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:type" content="{og_type}">
    <meta property="og:title" content="{safe_title}">
    <meta property="og:description" content="{safe_desc}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:site_name" content="{SITE_NAME}">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{safe_title}">
    <meta name="twitter:description" content="{safe_desc}">
    <link rel="stylesheet" href="/index.css">
    <link rel="icon" type="image/png" href="/favicon/favicon-96x96.png" sizes="96x96">
    <link rel="icon" type="image/svg+xml" href="/favicon/favicon.svg">
    <link rel="shortcut icon" href="/favicon/favicon.ico">
    <link rel="apple-touch-icon" sizes="180x180" href="/favicon/apple-touch-icon.png">
    <meta name="apple-mobile-web-app-title" content="Kristian R.">
    <link rel="manifest" href="/favicon/site.webmanifest">
    <meta name="theme-color" content="#1a1a1a">
{extra_head}
{script_ld(json_ld or [])}</head>
<body{f' class="{body_class}"' if body_class else ''}>
{h1_html}    <div class="header-container">
        <p class="site-title">
            <a href="/" style="text-decoration: none; color: inherit;">
                {LOGO}
                <span id="mainTitle">kristiam.xyz</span><span class="cursor">|</span>
            </a>
        </p>
        <div>
            {menu_html(active)}
            <svg class="theme-toggle" id="theme-toggle" width="16" height="16" viewBox="0 0 16 16" role="button" aria-label="Toggle theme">
                <circle cx="8" cy="8" r="7" fill="currentColor"/>
            </svg>
        </div>
    </div>

    <div class="body-wrapper">
        <div class="main-content">
{body}
        </div>
    </div>

    <footer class="footer">
        <p class="footer-updated">last updated: {FOOTER_UPDATED}</p>
        <p class="footer-links">
        <a href="mailto:kristian dot ristic at gmail dot com" target="_blank" rel="noopener noreferrer">contact</a> |
        <a href="https://github.com/kkristianr" target="_blank" rel="noopener noreferrer">github</a> |
        <a href="https://linkedin.com/in/kristianristic" target="_blank" rel="noopener noreferrer">linkedin</a>
        </p>
    </footer>

    <script src="/script.js"></script>
{extra_scripts}
</body>
</html>
"""


# --- writers ---------------------------------------------------------------


def build_pages(posts: list[dict]) -> list[str]:
    urls = []
    for page in PAGES:
        body = fill_post_markers((SRC_PAGES / page["src"]).read_text(encoding="utf-8"), posts)
        extra_head = ""
        extra_scripts = ""
        body_class = ""
        json_ld: list[dict] = []
        if page["key"] == "home":
            extra_head = home_extra_head()
            json_ld = [profile_page_jsonld(), person_jsonld(), website_jsonld()]
        extra_head = page.get("extra_head", extra_head)
        extra_scripts = page.get("extra_scripts", extra_scripts)
        body_class = page.get("body_class", body_class)
        html_out = layout(
            title=page["title"],
            description=page["description"],
            canonical_path=page["path"],
            h1=page["h1"],
            active=page["active"],
            body=body,
            extra_head=extra_head,
            extra_scripts=extra_scripts,
            body_class=body_class,
            json_ld=json_ld,
        )
        (ROOT / page["outfile"]).write_text(html_out, encoding="utf-8")
        urls.append(page["path"])
        print(f"wrote {page['outfile']}")
    return urls


def build_articles(posts: list[dict]) -> list[str]:
    urls = []
    for post in posts:
        parent = article_parent(post)
        content_class = " article-running" if "running" in post["categories"] else ""
        body = f"""            <a href="{parent}" class="back-link">&#8592; back</a>
            <article class="article-header">
                <h1 class="article-title">{html.escape(post["title"])}</h1>
                <div class="article-meta">
                    <span class="article-date">{html.escape(format_display_date(post["date"]))}</span>
                </div>
            </article>
            <div class="article-content{content_class}">{md_to_html(post["body"])}</div>
"""
        path = post_path(post)
        html_out = layout(
            title=post["title"],
            description=post["excerpt"] or post["title"],
            canonical_path=path,
            h1=None,
            active=parent,
            body=body,
            json_ld=[article_jsonld(post), person_jsonld()],
            og_type="article",
        )
        outfile = f"{path.lstrip('/')}.html"
        dest = ROOT / outfile
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html_out, encoding="utf-8")
        urls.append(path)
        print(f"wrote {outfile}")
    return urls


def write_sitemap(paths: list[str]) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = []
    for path in paths:
        loc = f"{SITE_ORIGIN}/" if path == "/" else f"{SITE_ORIGIN}{path}"
        entries.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{now}</lastmod>\n"
            "    <changefreq>weekly</changefreq>\n"
            f"    <priority>{SITEMAP_PRIORITY.get(path, '0.7')}</priority>\n"
            "  </url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    print("wrote sitemap.xml")


def write_robots() -> None:
    if (ROOT / ".devstage").exists():
        text = """User-agent: *
Disallow: /
"""
    else:
        text = f"""User-agent: *
Content-Signal: ai-train=no, search=yes, ai-input=yes
Allow: /

Sitemap: {SITE_ORIGIN}/sitemap.xml
"""
    (ROOT / "robots.txt").write_text(text, encoding="utf-8")
    print("wrote robots.txt")


def write_llms_txt(posts: list[dict]) -> None:
    lines = [
        f"# {SITE_NAME}",
        "",
        "> Personal website of Kristian Ristic — AI engineer / data scientist and passionate runner based in Vienna, Austria.",
        "",
        "## Person",
        f"- Home: {SITE_ORIGIN}/",
        f"- CV: {SITE_ORIGIN}/cv",
        "- Clubs: ProTeam Vienna, AK Smederevo",
        "",
        "## Writing",
        f"- AI / NLP / stats: {SITE_ORIGIN}/dev-ai",
        f"- Running: {SITE_ORIGIN}/running",
        f"- Other: {SITE_ORIGIN}/random",
        "",
        "## Articles",
    ]
    lines.extend(f"- [{post['title']}]({SITE_ORIGIN}{post_path(post)})" for post in posts)
    lines += ["", "## External profiles"]
    lines.extend(f"- {label}: {url}" for label, url in PROFILES)
    lines.append("")
    (ROOT / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    print("wrote llms.txt")


class _HtmlToMarkdown(HTMLParser):
    _SKIP = {"script", "style", "svg"}
    _HEADINGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip_depth = 0
        self.href: str | None = None
        self.link_text: list[str] | None = None
        self.in_pre = False
        self.table_rows: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.skip_depth or (self.link_text is not None and tag != "a"):
            if self.skip_depth:
                self.skip_depth += 1
            return
        if tag in self._SKIP:
            self.skip_depth = 1
            return
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())
        if tag == "span" and "skill-separator" in classes:
            self._write(", ")
            return
        if tag == "br":
            self._write("\n")
            return
        if tag == "a":
            href = attr.get("href", "")
            if href and not href.startswith("#"):
                self.href = href
                self.link_text = []
            return
        if tag in self._HEADINGS:
            self._write("\n\n" + self._HEADINGS[tag] + " ")
            return
        if tag in {"p", "div", "section"}:
            self._write("\n\n")
            return
        if tag == "li":
            self._write("\n- ")
            return
        if tag == "pre":
            self.in_pre = True
            self._write("\n\n```\n")
            return
        if tag == "table":
            self.table_rows = []
            return
        if tag == "tr" and self.table_rows is not None:
            self.row = []
            return
        if tag in {"td", "th"} and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag: str) -> None:
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if tag == "a" and self.link_text is not None:
            text = re.sub(r"\s+", " ", "".join(self.link_text)).strip()
            href = self.href or ""
            self.link_text = None
            self.href = None
            if text:
                self._write(f"[{text}]({href})")
            return
        if self.link_text is not None:
            return
        if tag == "pre" and self.in_pre:
            self.in_pre = False
            self._write("\n```\n")
            return
        if tag in {"td", "th"} and self.cell is not None and self.row is not None:
            value = re.sub(r"\s+", " ", "".join(self.cell)).strip().replace("|", "\\|")
            self.row.append(value)
            self.cell = None
            return
        if tag == "tr" and self.row is not None and self.table_rows is not None:
            if any(self.row):
                self.table_rows.append(self.row)
            self.row = None
            return
        if tag == "table" and self.table_rows is not None:
            rows = self.table_rows
            self.table_rows = None
            self._write(_markdown_table(rows))

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.cell is not None:
            self.cell.append(data)
            return
        if self.link_text is not None:
            self.link_text.append(data)
            return
        if self.in_pre:
            self._write(data)
            return
        text = re.sub(r"[ \t\r\f\v]+", " ", data.replace("\n", " "))
        if text:
            self._write(text)

    def _write(self, text: str) -> None:
        self.out.append(text)

    def markdown(self) -> str:
        text = "".join(self.out)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def _markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    header, *body = normalized
    lines = [
        "",
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n" + "\n".join(lines) + "\n"


def html_to_markdown(fragment: str) -> str:
    parser = _HtmlToMarkdown()
    parser.feed(fragment)
    parser.close()
    return parser.markdown()


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _token_estimate(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def _frontmatter(title: str, description: str) -> str:
    return f"---\ntitle: {_yaml_quote(title)}\ndescription: {_yaml_quote(description)}\n---\n\n"


def _posts_html_list(posts: list[dict]) -> str:
    items = []
    for post in posts:
        label = f"{format_display_date(post['date'])} — {post['title']}"
        if post["excerpt"]:
            label += f": {post['excerpt']}"
        items.append(f'<li><a href="{post_path(post)}">{html.escape(label)}</a></li>')
    if not items:
        return "<p>no posts yet</p>"
    return "<ul>" + "".join(items) + "</ul>"


def _page_markdown(page: dict, posts: list[dict]) -> str:
    if page["key"] == "dev-ai":
        body = "Categories: all, ai, nlp, stats.\n\n" + html_to_markdown(
            _posts_html_list(posts_with_any(posts, DEV_CATEGORIES))
        )
    else:
        fragment = (SRC_PAGES / page["src"]).read_text(encoding="utf-8")
        fragment = fragment.replace("<!--POSTS:running-->", _posts_html_list(
            [p for p in posts if "running" in p["categories"]]
        ))
        fragment = fragment.replace("<!--POSTS:random-->", _posts_html_list(
            [p for p in posts if "random" in p["categories"]]
        ))
        body = html_to_markdown(fragment)
    heading = f"# {page['h1']}\n\n" if page["h1"] else ""
    return _frontmatter(page["title"], page["description"]) + heading + body


def _article_markdown(post: dict) -> str:
    published = format_display_date(post["date"])
    body = post["body"].strip() + "\n"
    return (
        _frontmatter(post["title"], post["excerpt"] or post["title"])
        + f"# {post['title']}\n\n"
        + (f"{published}\n\n" if published else "")
        + body
    )


def _markdown_file(url_path: str) -> Path:
    out_dir = ROOT / "md"
    if url_path == "/":
        return out_dir / "index.md"
    # A section with notes is a directory, so its page is index.md inside it.
    if url_path in {path for _, path in PARENT_BY_CATEGORY.items()} | {"/dev-ai"}:
        return out_dir / url_path.lstrip("/") / "index.md"
    return out_dir / f"{url_path.lstrip('/')}.md"


def write_markdown(posts: list[dict]) -> None:
    out_dir = ROOT / "md"
    out_dir.mkdir(exist_ok=True)
    documents: list[tuple[str, str]] = []
    for page in PAGES:
        documents.append((page["path"], _page_markdown(page, posts)))
        dest = _markdown_file(page["path"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(documents[-1][1], encoding="utf-8")
    for post in posts:
        path = post_path(post)
        documents.append((path, _article_markdown(post)))
        dest = _markdown_file(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(documents[-1][1], encoding="utf-8")

    lines = ["map {http.request.uri.path} {md_tokens} {html_tokens} {"]
    for path, markdown_text in documents:
        html_name = "index.html" if path == "/" else f"{path.lstrip('/')}.html"
        html_text = (ROOT / html_name).read_text(encoding="utf-8")
        lines.append(
            f"\t{path}\t{_token_estimate(markdown_text)}\t{_token_estimate(html_text)}"
        )
    lines.append("\tdefault\t0\t0")
    lines.append("}")
    lines.append("")
    (out_dir / "tokens.caddy").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote markdown for {len(documents)} pages")


def main() -> None:
    posts = load_posts()
    paths = list(dict.fromkeys(build_pages(posts) + build_articles(posts)))
    write_sitemap(paths)
    write_robots()
    write_llms_txt(posts)
    write_markdown(posts)
    print(f"done: {len(paths)} URLs")


if __name__ == "__main__":
    main()
