"""Fill research interests from faculty.iiitdmj.ac.in home cards into faculty.json."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from scripts.fetch_faculty import HOME, OUT, _get, _parse_home  # noqa: E402

PACKAGED = BACKEND / "app" / "faculty_data.json"


def main() -> int:
    status, home = _get(HOME, timeout=25)
    print(f"home HTTP {status}, {len(home)} bytes", flush=True)
    if status != 200:
        return 1
    cards = _parse_home(home)
    with_research = sum(1 for r in cards.values() if r.get("research"))
    print(f"cards {len(cards)}, with research {with_research}", flush=True)

    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"items": []}
    by_slug = {((r.get("slug") or "").lower()): r for r in data.get("items") or []}
    updated = 0
    for slug, card in cards.items():
        if slug not in by_slug:
            by_slug[slug] = card
            updated += 1
            continue
        if card.get("research"):
            by_slug[slug]["research"] = card["research"]
            updated += 1
        elif not by_slug[slug].get("research"):
            pass
        if card.get("name") and not by_slug[slug].get("name"):
            by_slug[slug]["name"] = card["name"]
    rows = sorted(by_slug.values(), key=lambda r: (r.get("name") or "").lower())
    payload = json.dumps(
        {"items": rows, "source": HOME, "count": len(rows)},
        ensure_ascii=False,
        indent=2,
    )
    OUT.write_text(payload, encoding="utf-8")
    PACKAGED.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT, PACKAGED)
    print(f"updated {updated} rows, {len(rows)} faculty -> {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
