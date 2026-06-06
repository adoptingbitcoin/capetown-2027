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

# Markers used to find the speakers-collection div
COLLECTION_OPEN = '<div class="speakers-collection">'
COLLECTION_CLOSE_AND_SPACER = """\
      </div>
      <div class="es-100"></div>"""


def main():
    html = SPEAKERS_HTML.read_text()
    speakers = json.loads(SPEAKERS_JSON.read_text())
    changes = []

    # 1. Empty the speakers-collection div (remove any Webflow placeholder content)
    if COLLECTION_OPEN in html:
        start = html.index(COLLECTION_OPEN)
        end = html.index(COLLECTION_CLOSE_AND_SPACER, start)
        current_content = html[start + len(COLLECTION_OPEN):end]

        if current_content.strip():
            # There's content inside — empty it
            new_block = f"{COLLECTION_OPEN}\n{COLLECTION_CLOSE_AND_SPACER}"
            html = html[:start] + new_block + html[end + len(COLLECTION_CLOSE_AND_SPACER):]
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
