#!/usr/bin/env python3
"""
Static blog generator for the Adopting Bitcoin Cape Town 2027 site.

Mirrors the speakers workflow, but reads Markdown files instead of JSON:
  - Each post is a Markdown file in content/blog/<slug>.md
  - The post TITLE is inferred from the first top-level `# ` heading
  - date / author / thumbnail / slug are passed as CLI args (no front-matter)

It produces static HTML (no CMS, no client-side rendering), matching how the
rest of the site is built:

  1. blog/<slug>.html   — one post page per Markdown file, stamped from
                          detail_blog.html (title, author, date, cover image,
                          and the article body converted from Markdown).
  2. blog.html          — the listing page: the .blog-list is rebuilt with one
                          .blog-item card per post found in content/blog/.

Because post pages live one directory down (blog/), all root-relative asset
and internal-link references from the template are rewritten to ../ .

Usage:
    cd /path/to/capetown-2027
    # build/refresh a single post (metadata via flags):
    python3 scripts/generate_blog.py \
        --md content/blog/adopting-bitcoin-cape-town-a-crossroads.md \
        --slug adopting-bitcoin-cape-town-a-crossroads \
        --author "Hermann" \
        --date "6 September 2026" \
        --thumbnail images/karoo.jpg

    # rebuild the listing from all posts recorded in the index:
    python3 scripts/generate_blog.py --rebuild-index

Post metadata for the listing is persisted to content/blog/index.json so the
listing can be rebuilt without re-passing every post's flags. Re-running for an
existing slug updates that entry.
"""

import argparse
import html as html_lib
import json
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content" / "blog"
INDEX_JSON = CONTENT_DIR / "index.json"
BLOG_DIR = REPO_ROOT / "blog"
BLOG_LISTING = REPO_ROOT / "blog.html"
DETAIL_TEMPLATE = REPO_ROOT / "detail_blog.html"

# ---------------------------------------------------------------------------
# Minimal, dependency-free Markdown -> HTML for the article body.
# Handles: #..###### headings, paragraphs, unordered lists, bold/italic,
# inline links, and inline code. This is enough for the manifesto-style posts;
# extend as needed rather than pulling in a Markdown lib the runner may lack.
# ---------------------------------------------------------------------------

def _inline(text: str) -> str:
    # escape first, then re-introduce our own tags
    text = html_lib.escape(text, quote=False)
    # links [label](url)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
                  r'<a href="\2" target="_blank">\1</a>', text)
    # bold **x** / __x__  (before italic)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    # italic *x* / _x_
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<em>\1</em>", text)
    # inline code `x`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def markdown_to_html(md: str):
    """Return (title, body_html). title = first '# ' heading, stripped from body."""
    lines = md.replace("\r\n", "\n").split("\n")
    title = None
    out = []
    i = 0
    n = len(lines)
    para = []

    def flush_para():
        if para:
            joined = " ".join(l.strip() for l in para).strip()
            if joined:
                out.append(f"<p>{_inline(joined)}</p>")
            para.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush_para()
            level = len(m.group(1))
            heading_text = m.group(2).strip().rstrip("\\").strip()
            if level == 1 and title is None:
                # First H1 is the post title — rendered in the hero, not the body.
                title = heading_text
            else:
                # Demote body headings by one level so the article body never
                # contains an <h1> (the hero <h1> is the single page title).
                # A markdown '#' section heading becomes <h2>, '##' -> <h3>, etc.
                body_level = min(level + 1, 6)
                out.append(f"<h{body_level}>{_inline(heading_text)}</h{body_level}>")
            i += 1
            continue

        # unordered list
        if re.match(r"^[-*+]\s+", stripped):
            flush_para()
            items = []
            while i < n and re.match(r"^[-*+]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*+]\s+", "", lines[i].strip()))
                i += 1
            lis = "".join(f"<li>{_inline(it)}</li>" for it in items)
            out.append(f"<ul role=\"list\">{lis}</ul>")
            continue

        # blank line -> paragraph break
        if stripped == "":
            flush_para()
            i += 1
            continue

        para.append(line)
        i += 1

    flush_para()
    if title is None:
        title = "Untitled"
    return title, "\n".join(out)


# ---------------------------------------------------------------------------
# Path rewriting: post pages live in blog/, template refs are root-relative.
# ---------------------------------------------------------------------------
INTERNAL_PAGES = None  # computed lazily from repo root *.html


def _internal_pages():
    global INTERNAL_PAGES
    if INTERNAL_PAGES is None:
        INTERNAL_PAGES = {p.name for p in REPO_ROOT.glob("*.html")}
    return INTERNAL_PAGES


def rewrite_paths_for_subdir(page: str) -> str:
    """Rewrite root-relative asset + internal-page refs to ../ for blog/ pages."""
    # asset dirs
    page = re.sub(r'(src|href)="(images|css|js|data|fonts)/',
                  r'\1="../\2/', page)
    # bare internal .html page links -> ../page.html  (skip anchors and abs urls)
    pages = _internal_pages()

    def repl(m):
        attr, target = m.group(1), m.group(2)
        base = target.split("#")[0].split("?")[0]
        if base in pages:
            return f'{attr}="../{target}"'
        return m.group(0)

    page = re.sub(r'(href)="([a-zA-Z0-9_\-]+\.html(?:[#?][^"]*)?)"', repl, page)
    return page


# ---------------------------------------------------------------------------
# Detail page stamping.
# ---------------------------------------------------------------------------

def build_post_page(title, body_html, author, date, thumbnail):
    tpl = DETAIL_TEMPLATE.read_text()

    # 1) rewrite asset/link paths for the blog/ subdir
    page = rewrite_paths_for_subdir(tpl)
    # thumbnail is repo-root-relative (e.g. images/karoo.jpg) -> ../images/...
    cover = thumbnail
    if re.match(r'^(images|css|js|data)/', cover):
        cover = "../" + cover

    # 2) <title> and og/twitter meta
    esc_title = html_lib.escape(title)
    plain = re.sub(r"<[^>]+>", "", body_html)
    desc = html_lib.escape(" ".join(plain.split())[:200])
    page = re.sub(r"<title>[^<]*</title>",
                  f"<title>{esc_title} — Adopting Bitcoin Cape Town</title>", page, count=1)
    page = re.sub(r'(<meta content=")("[^>]*property="og:title">)',
                  rf'\g<1>{esc_title}\g<2>', page, count=1)
    page = re.sub(r'(<meta content=")("[^>]*property="og:image">)',
                  rf'\g<1>{html_lib.escape(cover)}\g<2>', page, count=1)
    page = re.sub(r'(<meta property="og:description" content=")("[^>]*>)',
                  rf'\g<1>{desc}\g<2>', page, count=1)
    page = re.sub(r'(<meta name="twitter:description" content=")("[^>]*>)',
                  rf'\g<1>{desc}\g<2>', page, count=1)

    # 3) hero fields — fill the empty Webflow bind divs, drop w-dyn-bind-empty
    page = page.replace(
        '<h1 class="h2 w-dyn-bind-empty"></h1>',
        f'<h1 class="h2">{esc_title}</h1>', 1)
    page = page.replace(
        '<div class="blogpost-author w-dyn-bind-empty"></div>',
        f'<div class="blogpost-author">{html_lib.escape(author)}</div>', 1)
    page = page.replace(
        '<div class="blogpost-date w-dyn-bind-empty"></div>',
        f'<div class="blogpost-date">{html_lib.escape(date)}</div>', 1)
    # cover image
    page = re.sub(
        r'<img src="[^"]*"([^>]*?)class="blog-post-cover-img w-dyn-bind-empty">',
        f'<img src="{html_lib.escape(cover)}"\\1class="blog-post-cover-img">',
        page, count=1)

    # 4) article body -> the .w-richtext container
    page = page.replace(
        '<div class="w-dyn-bind-empty w-richtext"></div>',
        f'<div class="w-richtext">\n{body_html}\n</div>', 1)

    return page


# ---------------------------------------------------------------------------
# Listing (blog.html) rebuild.
# ---------------------------------------------------------------------------
BLOG_LIST_RE = re.compile(r'<div class="blog-list">[\s\S]*?</div>\s*</div>\s*</div>')


def _card(entry):
    slug = entry["slug"]
    thumb = entry.get("thumbnail", "images/karoo.jpg")
    # responsive srcset if a -p-500 variant exists next to the thumbnail
    p500 = re.sub(r'(\.[a-zA-Z]+)$', r'-p-500\1', thumb)
    has_p500 = (REPO_ROOT / p500).exists()
    if has_p500:
        srcset = f'srcset="{p500} 500w, {thumb} 600w" '
    else:
        srcset = f'srcset="{thumb} 500w, {thumb} 600w" '
    href = f"blog/{slug}.html"
    title = html_lib.escape(entry["title"])
    date = html_lib.escape(entry["date"])
    return (
        f'          <div class="blog-item">\n'
        f'            <a href="{href}" class="blog-image w-inline-block">'
        f'<img src="{thumb}" loading="lazy" sizes="(max-width: 600px) 100vw, 600px" '
        f'{srcset}alt="" class="blog-img"></a>\n'
        f'            <div class="es-20"></div>\n'
        f'            <a href="{href}" class="w-inline-block">\n'
        f'              <div class="blog-title">{title}</div>\n'
        f'            </a>\n'
        f'            <div class="blog-date">{date}</div>\n'
        f'          </div>'
    )


def rebuild_listing(index):
    html = BLOG_LISTING.read_text()
    # newest first by parsed date, fall back to insertion order
    def key(e):
        for fmt in ("%d %B %Y", "%B %d, %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(e["date"], fmt)
            except ValueError:
                continue
        return datetime.min
    entries = sorted(index, key=key, reverse=True)
    cards = "\n".join(_card(e) for e in entries) if entries else ""
    new_block = f'<div class="blog-list">\n{cards}\n        </div>\n      </div>\n    </div>'
    if not BLOG_LIST_RE.search(html):
        raise SystemExit("ERROR: could not find .blog-list block in blog.html")
    html = BLOG_LIST_RE.sub(new_block, html, count=1)
    BLOG_LISTING.write_text(html)
    return len(entries)


# ---------------------------------------------------------------------------
# Index persistence.
# ---------------------------------------------------------------------------

def load_index():
    if INDEX_JSON.exists():
        return json.loads(INDEX_JSON.read_text())
    return []


def save_index(index):
    INDEX_JSON.write_text(json.dumps(index, indent=2) + "\n")


def upsert(index, entry):
    for i, e in enumerate(index):
        if e["slug"] == entry["slug"]:
            index[i] = entry
            return index
    index.append(entry)
    return index


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Build blog post HTML from Markdown.")
    ap.add_argument("--md", help="path to the Markdown source file")
    ap.add_argument("--slug", help="URL slug -> blog/<slug>.html")
    ap.add_argument("--author", default="Adopting Bitcoin Cape Town")
    ap.add_argument("--date", help="human date, e.g. '6 September 2026'")
    ap.add_argument("--thumbnail", default="images/karoo.jpg",
                    help="repo-root-relative thumbnail path (placeholder ok)")
    ap.add_argument("--rebuild-index", action="store_true",
                    help="only rebuild blog.html listing from content/blog/index.json")
    args = ap.parse_args()

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    BLOG_DIR.mkdir(parents=True, exist_ok=True)

    if args.rebuild_index and not args.md:
        index = load_index()
        n = rebuild_listing(index)
        print(f"Rebuilt blog.html listing from index: {n} post(s).")
        return

    if not (args.md and args.slug and args.date):
        ap.error("--md, --slug and --date are required to build a post "
                 "(or use --rebuild-index alone).")

    md_path = Path(args.md)
    if not md_path.is_absolute():
        md_path = REPO_ROOT / md_path
    if not md_path.exists():
        ap.error(f"Markdown file not found: {md_path}")

    title, body = markdown_to_html(md_path.read_text())
    page = build_post_page(title, body, args.author, args.date, args.thumbnail)

    out = BLOG_DIR / f"{args.slug}.html"
    out.write_text(page)
    print(f"  ✓ wrote blog/{args.slug}.html  (title: {title!r})")

    # update index + rebuild listing
    index = load_index()
    upsert(index, {
        "slug": args.slug,
        "title": title,
        "author": args.author,
        "date": args.date,
        "thumbnail": args.thumbnail,
        "source": f"content/blog/{md_path.name}",
    })
    save_index(index)
    n = rebuild_listing(index)
    print(f"  ✓ updated content/blog/index.json and rebuilt blog.html ({n} post(s))")
    print(f"\nDone. Post URL: blog/{args.slug}.html")


if __name__ == "__main__":
    main()
