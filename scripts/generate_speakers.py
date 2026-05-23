#!/usr/bin/env python3
"""
Generate individual speaker pages for Adopting Bitcoin Cape Town (ZA27).

Usage:
    cd /path/to/capetown-2027
    python3 scripts/generate_speakers.py

Reads:
    data/speakers.json          — speaker data
    detail_speakers.html        — Webflow template

Writes:
    speakers/{slug}.html        — one page per speaker
"""

import json
import os
import re
import sys
from pathlib import Path
from html import escape

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEAKERS_JSON = REPO_ROOT / "data" / "speakers.json"
TEMPLATE_FILE = REPO_ROOT / "detail_speakers.html"
SPEAKERS_DIR = REPO_ROOT / "speakers"

# Base URL for OG image tags (no trailing slash)
BASE_URL = "https://za27.adoptingbitcoin.org"


def load_speakers() -> list[dict]:
    with open(SPEAKERS_JSON, "r") as f:
        return json.load(f)


def load_template() -> str:
    with open(TEMPLATE_FILE, "r") as f:
        return f.read()


def display_name(speaker: dict) -> str:
    return f"{speaker['name']} {speaker.get('surname', '')}".strip()


def make_slug(speaker: dict) -> str:
    return speaker.get("slug", display_name(speaker).lower().replace(" ", "-"))


def adjust_paths(html: str) -> str:
    """Prefix relative paths with ../ for speakers/ subdirectory."""
    # CSS
    html = re.sub(r'href="css/', 'href="../css/', html)
    # JS
    html = re.sub(r'src="js/', 'src="../js/', html)
    # Images (src and srcset)
    html = re.sub(r'src="images/', 'src="../images/', html)
    html = re.sub(r'srcset="images/', 'srcset="../images/', html)
    # Fix srcset with multiple entries (images/ after commas)
    html = re.sub(r',\s*images/', ', ../images/', html)
    # Fonts
    html = re.sub(r'url\(fonts/', 'url(../fonts/', html)
    html = re.sub(r'href="fonts/', 'href="../fonts/', html)
    # Internal page links (*.html but not http*, mailto, #, or already prefixed)
    html = re.sub(r'href="(?!https?://|mailto:|#|\.\./)([^"]+\.html)', r'href="../\1', html)
    return html


def inject_speaker(template: str, speaker: dict) -> str:
    """Fill the template placeholders with speaker data."""
    html = template
    name = display_name(speaker)
    esc_name = escape(name)
    company = escape(speaker.get("company", ""))
    role = escape(speaker.get("role", ""))
    bio = speaker.get("bio", "")
    photo = speaker.get("photo", "")
    twitter = speaker.get("twitter", "")
    nostr = speaker.get("nostr", "")
    website = speaker.get("website", "")
    youtube = speaker.get("youtube", "")

    # Adjust photo path for subdirectory
    photo_rel = f"../{photo}" if photo and not photo.startswith("http") else photo
    photo_abs = f"{BASE_URL}/{photo}" if photo and not photo.startswith("http") else photo

    # --- <title> ---
    html = re.sub(
        r"<title>[^<]*</title>",
        f"<title>{esc_name} — Adopting Bitcoin Cape Town 2027</title>",
        html,
        count=1,
    )

    # --- meta description ---
    bio_desc = escape(bio[:160]) if bio else f"{esc_name} speaks at Adopting Bitcoin Cape Town 2027"
    html = re.sub(
        r'<meta content="[^"]*" name="description">',
        f'<meta content="{bio_desc}" name="description">',
        html,
        count=1,
    )

    # --- og:title ---
    html = re.sub(
        r'<meta content="[^"]*" property="og:title">',
        f'<meta content="{esc_name} speaks at Adopting Bitcoin Cape Town 2027" property="og:title">',
        html,
        count=1,
    )

    # --- og:description ---
    html = re.sub(
        r'<meta content="[^"]*" property="og:description">',
        f'<meta content="{bio_desc}" property="og:description">',
        html,
        count=1,
    )

    # --- og:image ---
    html = re.sub(
        r'<meta content="[^"]*" property="og:image">',
        f'<meta content="{photo_abs}" property="og:image">',
        html,
        count=1,
    )

    # --- twitter:title ---
    html = re.sub(
        r'<meta content="[^"]*" name="twitter:title">',
        f'<meta content="{esc_name} speaks at Adopting Bitcoin Cape Town 2027" name="twitter:title">',
        html,
        count=1,
    )

    # --- twitter:description ---
    html = re.sub(
        r'<meta content="[^"]*" name="twitter:description">',
        f'<meta content="{bio_desc}" name="twitter:description">',
        html,
        count=1,
    )

    # --- twitter:image ---
    html = re.sub(
        r'<meta content="[^"]*" name="twitter:image">',
        f'<meta content="{photo_abs}" name="twitter:image">',
        html,
        count=1,
    )

    # --- Speaker heading (h2.speaker-heading) ---
    html = re.sub(
        r'<h2 class="speaker-heading[^"]*">[^<]*</h2>',
        f'<h2 class="speaker-heading">{esc_name}</h2>',
        html,
    )

    # --- Speaker title/company link ---
    if website:
        html = re.sub(
            r'<a href="[^"]*" class="speaker-title speaker-page w-inline-block">\s*<div[^>]*>[^<]*</div>\s*</a>',
            f'<a href="{escape(website)}" target="_blank" class="speaker-title speaker-page w-inline-block">\n              <div>{company}</div>\n            </a>',
            html,
        )
    else:
        html = re.sub(
            r'<a href="[^"]*" class="speaker-title speaker-page w-inline-block">\s*<div[^>]*>[^<]*</div>\s*</a>',
            f'<a href="#" class="speaker-title speaker-page w-inline-block">\n              <div>{company}</div>\n            </a>',
            html,
        )

    # --- Speaker role (non-link div) ---
    html = re.sub(
        r'<div class="speaker-title speaker-page w-dyn-bind-empty"></div>',
        f'<div class="speaker-title speaker-page">{role}</div>' if role else '<div class="speaker-title speaker-page"></div>',
        html,
    )

    # --- Twitter social link ---
    if twitter:
        html = re.sub(
            r'(<a href=")[^"]*(" class="speaker-socials-icon w-inline-block"><img src="[^"]*x-icon)',
            f'\\1{escape(twitter)}\\2',
            html,
        )
    else:
        # Hide the X icon link if no twitter
        html = re.sub(
            r'<a href="[^"]*" class="speaker-socials-icon w-inline-block"><img src="[^"]*x-icon\.svg[^>]*></a>',
            '',
            html,
        )

    # --- Nostr social link ---
    if nostr:
        nostr_url = nostr if nostr.startswith("http") else f"https://primal.net/p/{nostr}"
        html = re.sub(
            r'<a href="https://primal\.net/p/[^"]*"',
            f'<a href="{escape(nostr_url)}"',
            html,
        )
    else:
        # Hide nostr embed div if no nostr
        html = re.sub(
            r'<div class="w-embed">\s*<a href="https://primal\.net/p/[^"]*"[^<]*<img[^>]*>[^<]*</a>\s*</div>',
            '',
            html,
            flags=re.DOTALL,
        )

    # --- Speaker bio ---
    if bio:
        bio_html = "".join(f"<p>{escape(p.strip())}</p>" for p in bio.split("\n\n") if p.strip())
        html = re.sub(
            r'<div class="speaker-bio[^"]*">[^<]*</div>',
            f'<div class="speaker-bio w-richtext">{bio_html}</div>',
            html,
        )
    else:
        html = re.sub(
            r'<div class="speaker-bio[^"]*">[^<]*</div>',
            '<div class="speaker-bio w-richtext"></div>',
            html,
        )

    # --- Speaker photo ---
    html = re.sub(
        r'<img src="[^"]*" loading="lazy" alt="[^"]*" class="speaker-page-image[^"]*"',
        f'<img src="{photo_rel}" loading="lazy" alt="{esc_name}" class="speaker-page-image"',
        html,
    )

    # --- YouTube embed ---
    if youtube:
        embed_url = youtube.replace("watch?v=", "embed/").split("&")[0]
        video_html = f'<div class="w-video w-embed"><iframe src="{escape(embed_url)}" frameborder="0" allowfullscreen style="width:100%;aspect-ratio:16/9;"></iframe></div>'
        html = re.sub(
            r'<div class="w-dyn-bind-empty w-video w-embed"></div>',
            video_html,
            html,
        )
    else:
        html = re.sub(
            r'<div class="w-dyn-bind-empty w-video w-embed"></div>',
            '',
            html,
        )

    return html


def main():
    if not SPEAKERS_JSON.exists():
        print(f"ERROR: {SPEAKERS_JSON} not found")
        sys.exit(1)

    if not TEMPLATE_FILE.exists():
        print(f"ERROR: {TEMPLATE_FILE} not found")
        sys.exit(1)

    speakers = load_speakers()
    template = load_template()
    adjusted_template = adjust_paths(template)

    SPEAKERS_DIR.mkdir(exist_ok=True)

    generated = []
    for speaker in speakers:
        slug = make_slug(speaker)
        name = display_name(speaker)
        output_path = SPEAKERS_DIR / f"{slug}.html"

        page_html = inject_speaker(adjusted_template, speaker)
        output_path.write_text(page_html)
        generated.append(name)
        print(f"  ✓ speakers/{slug}.html — {name}")

    # Clean up orphaned speaker pages
    existing_slugs = {make_slug(s) for s in speakers}
    for html_file in SPEAKERS_DIR.glob("*.html"):
        if html_file.stem not in existing_slugs:
            html_file.unlink()
            print(f"  ✗ removed orphan: speakers/{html_file.name}")

    print(f"\nDone: {len(generated)} speaker pages generated.")


if __name__ == "__main__":
    main()
