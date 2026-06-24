#!/usr/bin/env python3
"""Validate the static site before Pages deployment."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_IDS = {
    "adesso", "fondamenti", "master-skill", "enhancement", "smith", "costi",
    "main-ingredient", "dismantle", "fluid", "ricette", "armory", "farming",
    "catalogo", "primo-set", "postgame", "random-skills", "glacite", "sovereign", "glossario",
}
FORBIDDEN_PUBLIC = re.compile(r"https?://", re.IGNORECASE)


def plus_ten(stats: list[int]) -> list[int]:
    total = sum(stats)
    if total <= 0:
        return list(stats)
    return [value + ((100 * value) // total) for value in stats]


def fail(message: str) -> None:
    raise RuntimeError(message)


def text_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".html", ".css", ".js", ".json", ".txt", ".md"}]


def validate_public_tree(site: Path) -> None:
    for path in text_files(site):
        text = path.read_text(encoding="utf-8")
        if FORBIDDEN_PUBLIC.search(text):
            fail(f"External URL found in published file: {path.relative_to(site)}")


def validate_guide(guide: Path) -> None:
    text = guide.read_text(encoding="utf-8")
    ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', text))
    missing = REQUIRED_IDS - ids
    if missing:
        fail(f"Guide is missing required anchors: {', '.join(sorted(missing))}")
    if text.count("<table") < 16:
        fail("Guide must retain the complete explanatory table set")
    if "catalogo-dinamico" not in text or "noteworthy-dynamic" not in text:
        fail("Guide is missing dynamic catalogue or noteworthy container")
    anchors = re.findall(r'<a\s+[^>]*href=["\']#([^"\']+)["\']', text)
    if len(anchors) < 25:
        fail("Guide has too few internal cross-links for a novice-oriented navigation flow")
    missing_targets = sorted({anchor for anchor in anchors if anchor not in ids})
    if missing_targets:
        fail(f"Guide has broken internal anchors: {', '.join(missing_targets)}")


def validate_catalogue(catalogue: Path, allow_unbuilt: bool) -> None:
    payload: dict[str, Any] = json.loads(catalogue.read_text(encoding="utf-8"))
    if payload.get("complete") is not True:
        if allow_unbuilt:
            return
        fail("Catalogue was not built before validation")
    categories = payload.get("categories")
    items = payload.get("items")
    noteworthy = payload.get("noteworthy")
    if not isinstance(categories, list) or len(categories) != 18:
        fail("Catalogue must contain exactly 18 categories")
    if not isinstance(items, list) or len(items) < 350:
        fail("Catalogue must contain at least 350 items")
    if not isinstance(noteworthy, list) or len(noteworthy) < 34:
        fail("Catalogue must retain at least 34 noteworthy navigation entries")
    category_ids = {entry.get("id") for entry in categories}
    found_ids = {entry.get("category_id") for entry in items}
    if category_ids != found_ids:
        fail("Catalogue category coverage is incomplete")
    seen: set[tuple[Any, ...]] = set()
    for item in items:
        stats = item.get("stats")
        stats_plus10 = item.get("stats_plus10")
        key = (item.get("category_id"), item.get("rarity"), item.get("name"))
        if key in seen:
            fail(f"Duplicate catalogue entry: {key}")
        seen.add(key)
        if item.get("phase") not in {"Main game", "Post-game"}:
            fail(f"Invalid phase: {item.get('name')}")
        if not isinstance(stats, list) or len(stats) != 5 or not all(isinstance(value, int) for value in stats):
            fail(f"Invalid base stats: {item.get('name')}")
        if stats_plus10 != plus_ten(stats):
            fail(f"Invalid +10 stats: {item.get('name')}")
        for field in ("name", "max_name", "master_skill", "enhancement_bonus", "main_ingredient", "acquisition"):
            value = str(item.get(field, "")).strip()
            if not value or value == "—":
                fail(f"Missing {field}: {item.get('name')}")
            if FORBIDDEN_PUBLIC.search(value):
                fail(f"External URL in item field: {item.get('name')}")

    expected_pairs = {(item.get("category_id"), item.get("phase")) for item in items}
    noteworthy_pairs = {(entry.get("category_id"), entry.get("phase")) for entry in noteworthy}
    if len(noteworthy_pairs) != len(noteworthy):
        fail("Noteworthy navigation entries duplicate a category/phase pair")
    if noteworthy_pairs != expected_pairs:
        missing = sorted(expected_pairs - noteworthy_pairs)
        unexpected = sorted(noteworthy_pairs - expected_pairs)
        fail(
            "Noteworthy navigation does not cover the catalogue phases. "
            f"Missing: {missing}; unexpected: {unexpected}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the complete static guide.")
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--allow-unbuilt", action="store_true")
    args = parser.parse_args()
    site = args.site.resolve()
    if not site.is_dir():
        fail(f"Site directory not found: {site}")
    validate_public_tree(site)
    validate_guide(site / "content" / "guide.html")
    validate_catalogue(site / "content" / "catalogo.json", args.allow_unbuilt)
    print("Static-site validation passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
