#!/usr/bin/env python3
"""
Post-Webflow-export fixup for speakers.html.

Empties the speakers-collection div (Webflow may inject placeholder
content) and ensures the js/speakers.js script tag is present.
The actual speaker grid is rendered client-side from data/speakers.json.

Usage:
    cd /path/to/capetown-2027
    python3 scripts/generate_speakers_grid.py
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEAKERS_JSON = REPO_ROOT / "data" / "speakers.json"
SPEAKERS_HTML = REPO_ROOT / "speakers.html"

SCRIPT_TAG = '<script src="js/speakers.js"></script>'

# Match the speakers-collection div and whatever it currently contains,
# whether Webflow collapsed it to one line (<div class="speakers-collection"></div>)
# or left it multi-line with placeholder content inside. The [\s\S]*? is
# non-greedy so it stops at the FIRST closing </div>.
COLLECTION_RE = re.compile(
    r'<div class="speakers-collection">[\s\S]*?</div>'
)
# Canonical empty form we normalise to.
COLLECTION_EMPTY = '<div class="speakers-collection"></div>'


def main():
    html = SPEAKERS_HTML.read_text()
    speakers = json.loads(SPEAKERS_JSON.read_text())
    changes = []

    # 1. Empty the speakers-collection div (remove any Webflow placeholder content).
    #    Robust to both the collapsed one-line form and the old multi-line form.
    m = COLLECTION_RE.search(html)
    if m:
        block = m.group(0)
        inner = block[len('<div class="speakers-collection">'):-len('</div>')]
        if inner.strip() and block != COLLECTION_EMPTY:
            html = html[:m.start()] + COLLECTION_EMPTY + html[m.end():]
            changes.append("emptied speakers-collection div")

    # 2. Ensure js/speakers.js script tag is present
    if SCRIPT_TAG not in html:
        # Insert before jQuery
        jquery_marker = '  <script src="https://d3e54v103j8qbb.cloudfront.net/js/jquery'
        if jquery_marker in html:
            html = html.replace(jquery_marker, f"  {SCRIPT_TAG}\n{jquery_marker}")
            changes.append("added speakers.js script tag")
        else:
            # Fallback: insert before </body>
            html = html.replace("</body>", f"  {SCRIPT_TAG}\n</body>")
            changes.append("added speakers.js script tag (before </body>)")

    if changes:
        SPEAKERS_HTML.write_text(html)
        print(f"Done: {', '.join(changes)} ({len(speakers)} speakers in JSON)")
    else:
        print(f"No changes needed ({len(speakers)} speakers in JSON, collection already empty, script tag present)")


if __name__ == "__main__":
    main()
