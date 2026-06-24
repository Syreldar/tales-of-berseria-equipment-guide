#!/usr/bin/env python3
"""Verify required guide sections and the generated local catalogue."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CATALOGUE = SITE / "content" / "catalogo.json"
EXPECTED_CATEGORIES = {
    "blades", "short-swords", "paper", "bracelets", "guardians", "spears",
    "belts", "talismans", "bags", "pendants", "earrings", "ribbons",
    "mens-armor", "womens-armor", "rings", "shoes", "mens-shoes", "womens-shoes",
}
REQUIRED_IDS = {
    "come-usare", "regole", "fondamenti", "enhancement", "materiali", "piani",
    "armory", "drop", "catalogo", "scelte", "random-skills", "sovereign", "checklist",
}
FORBIDDEN = ("game" + "faqs", "game" + "spot", "for" + "um")


def fail(message: str) -> None:
    raise RuntimeError(message)


def check_text_files() -> None:
    for path in SITE.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {".html", ".js", ".css", ".json"}:
            continue

        content = path.read_text(encoding="utf-8").lower()

        for forbidden in FORBIDDEN:
            if forbidden in content:
                fail(f"Forbidden reference in {path.relative_to(ROOT)}")

        if path.suffix.lower() == ".html" and re.search(r"(?:href|src)=[\"']https?://", content):
            fail(f"External link in published page: {path.relative_to(ROOT)}")


def check_guide() -> None:
    guide = (SITE / "content" / "guide.html").read_text(encoding="utf-8")
    found = set(re.findall(r'<section\s+id="([^"]+)"', guide))
    missing = REQUIRED_IDS - found

    if missing:
        fail(f"Missing guide sections: {', '.join(sorted(missing))}")

    if guide.count("<table") < 15:
        fail("Guide has too few tables for the complete reference")


def check_catalogue(allow_stub: bool) -> None:
    data: dict[str, Any] = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    categories = data.get("categories", [])
    items = data.get("items", [])

    if not items and allow_stub:
        return

    if not isinstance(categories, list) or not isinstance(items, list):
        fail("Catalogue JSON has an invalid shape")

    category_ids = {category.get("id") for category in categories if isinstance(category, dict)}

    if category_ids != EXPECTED_CATEGORIES:
        fail("Catalogue categories are incomplete or unexpected")

    if len(items) < 300:
        fail(f"Catalogue has {len(items)} rows; expected at least 300")

    seen: set[tuple[str, int, str]] = set()

    for item in items:
        required = {"category_id", "rarity", "name", "stats", "master_skill", "enhancement_bonus", "main_ingredient", "rare_drop", "max_name"}

        if not required.issubset(item):
            fail("Catalogue row is missing required fields")

        if item["category_id"] not in EXPECTED_CATEGORIES:
            fail(f"Unknown category in catalogue: {item['category_id']}")

        if not isinstance(item["rarity"], int) or not 1 <= item["rarity"] <= 21:
            fail(f"Invalid rarity for {item['name']}")

        if not isinstance(item["stats"], list) or len(item["stats"]) != 5:
            fail(f"Invalid stat vector for {item['name']}")

        key = (item["category_id"], item["rarity"], item["name"])

        if key in seen:
            fail(f"Duplicate catalogue item: {item['name']}")

        seen.add(key)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the static site before deployment.")
    parser.add_argument("--allow-stub", action="store_true", help="Allow the ungenerated local catalogue placeholder.")
    args = parser.parse_args()

    check_text_files()
    check_guide()
    check_catalogue(args.allow_stub)
    print("Site verification passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
