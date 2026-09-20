"""Combines viz_template.html with logs/viz_data.json into demo/viz.html, the
self-contained page ready to publish or open directly.

Kept separate from the template so the template (markup, style, rendering
logic) and the data (produced by export_visualization_data.py, itself derived
from replaying the two demo logs) can each change independently. Run this
after export_visualization_data.py, or whenever the template changes.
"""

import json
from pathlib import Path

DEMO_DIR = Path(__file__).parent
PLACEHOLDER = "/*__VIZ_DATA_JSON__*/"


def main() -> None:
    data_path = DEMO_DIR / "logs" / "viz_data.json"
    template_path = DEMO_DIR / "viz_template.html"
    out_path = DEMO_DIR / "viz.html"

    if not data_path.exists():
        raise SystemExit("Run demo/export_visualization_data.py first.")

    data = json.loads(data_path.read_text(encoding="utf-8"))
    template = template_path.read_text(encoding="utf-8")

    if PLACEHOLDER not in template:
        raise SystemExit(f"Template is missing the {PLACEHOLDER!r} placeholder.")

    page = template.replace(PLACEHOLDER, json.dumps(data))
    out_path.write_text(page, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
