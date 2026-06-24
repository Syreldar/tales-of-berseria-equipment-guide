#!/usr/bin/env python3
"""Validate the static guide and its committed Equipment catalogue snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

EXPECTED_CATEGORY_COUNT = 18
EXPECTED_ITEM_COUNT = 350
PHASES = ("Main game", "Post-game")
EXPECTED_PHASE_CARD_COUNT = EXPECTED_CATEGORY_COUNT * len(PHASES)
REQUIRED_IDS = {
    "adesso", "come-leggere", "fondamenti", "statistiche", "rarity", "common-rare",
    "master-skill", "enhancement", "smith", "costi", "main-ingredient", "dismantle",
    "fluid", "ricette", "matching", "ricette-common", "ricette-rare", "alchemist", "armory",
    "farming", "farming-equipment", "common-target", "catalogo",
    "primo-set", "postgame", "massimizzazione", "random-skills", "glacite", "sovereign",
    "glossario", "checklist",
}
FORBIDDEN_PUBLIC_URL = re.compile(r"https?://", re.IGNORECASE)
FORBIDDEN_PUBLIC_REFERENCE = re.compile("game" + "faqs|game" + "spot", re.IGNORECASE)


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value).strip())
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = value.lower().replace("’", "'")
    value = re.sub(r"[^a-z0-9+%]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def plus_ten(stats: list[int]) -> list[int]:
    total = sum(stats)
    if total <= 0:
        return list(stats)
    return [value + ((100 * value) // total) for value in stats]


def item_identity(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "category_id": item["category_id"],
        "rarity": item["rarity"],
        "name": normalized(item["name"]),
        "max_name": normalized(item["max_name"]),
        "stats": item["stats"],
        "master_skill": normalized(item["master_skill"]),
        "enhancement_bonus": normalized(item["enhancement_bonus"]),
        "main_ingredient": normalized(item["main_ingredient"]),
        "rare_drop": normalized(item["rare_drop"]),
        "source_kind": item["source_kind"],
    }


def identity_sha256(items: list[dict[str, Any]]) -> str:
    canonical = json.dumps([item_identity(item) for item in items], ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def expected_phase(rarity: int) -> str:
    return "Post-game" if rarity >= 19 else "Main game"


def fail(message: str) -> None:
    raise RuntimeError(message)


def text_files(root: Path) -> list[Path]:
    suffixes = {".html", ".css", ".js", ".json", ".txt", ".md"}
    return [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffixes]


def validate_public_tree(site: Path) -> None:
    for path in text_files(site):
        text = path.read_text(encoding="utf-8")
        if FORBIDDEN_PUBLIC_URL.search(text):
            fail(f"External URL found in published file: {path.relative_to(site)}")
        if FORBIDDEN_PUBLIC_REFERENCE.search(text):
            fail(f"Forbidden source reference found in published file: {path.relative_to(site)}")


def validate_guide(guide: Path) -> list[str]:
    text = guide.read_text(encoding="utf-8")
    ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', text))
    missing = REQUIRED_IDS - ids
    if missing:
        fail(f"Guide is missing required anchors: {', '.join(sorted(missing))}")
    if text.count("<table") < 21:
        fail("Guide must retain at least 21 explanatory tables for the novice flow")
    if "catalogo-dinamico" not in text or "reference-cards-dynamic" not in text:
        fail("Guide is missing dynamic catalogue or reference-card container")

    anchors = re.findall(r'<a\s+[^>]*href=["\']#([^"\']+)["\']', text)
    if len(anchors) < 40:
        fail("Guide has too few internal cross-links for a novice-oriented navigation flow")
    missing_targets = sorted({anchor for anchor in anchors if anchor not in ids})
    if missing_targets:
        fail(f"Guide has broken internal anchors: {', '.join(missing_targets)}")

    item_refs = re.findall(r'data-item-ref=["\']([^"\']+)["\']', text)
    if len(item_refs) < 18:
        fail("Guide needs at least 18 direct Equipment references")
    return item_refs


def validate_catalogue(catalogue: Path, item_refs: list[str], allow_unbuilt: bool) -> None:
    payload: dict[str, Any] = json.loads(catalogue.read_text(encoding="utf-8"))
    if payload.get("complete") is not True:
        if allow_unbuilt:
            return
        fail("Catalogue snapshot is not complete. The deployment workflow must materialize the initial local snapshot first.")

    if payload.get("schema_version") != 4:
        fail("Catalogue schema version is not current")
    categories = payload.get("categories")
    items = payload.get("items")
    cards = payload.get("reference_cards")
    integrity = payload.get("integrity")
    if not isinstance(categories, list) or len(categories) != EXPECTED_CATEGORY_COUNT:
        fail("Catalogue must contain exactly 18 categories")
    if not isinstance(items, list) or len(items) != EXPECTED_ITEM_COUNT:
        fail("Catalogue must contain exactly 350 items")
    if not isinstance(cards, list) or len(cards) != EXPECTED_PHASE_CARD_COUNT:
        fail("Catalogue must contain exactly 36 category/phase reference cards")
    if not isinstance(integrity, dict):
        fail("Catalogue integrity metadata is missing")

    category_ids = {entry.get("id") for entry in categories}
    if len(category_ids) != EXPECTED_CATEGORY_COUNT or None in category_ids:
        fail("Catalogue category IDs are invalid")
    found_ids = {entry.get("category_id") for entry in items}
    if category_ids != found_ids:
        fail("Catalogue category coverage is incomplete")

    required_pairs = {(str(category_id), phase) for category_id in category_ids for phase in PHASES}
    if len(required_pairs) != EXPECTED_PHASE_CARD_COUNT:
        fail("Catalogue category/phase matrix is inconsistent")

    found_pairs: set[tuple[str, str]] = set()
    seen: set[tuple[Any, ...]] = set()
    item_names: set[str] = set()
    for item in items:
        stats = item.get("stats")
        stats_plus10 = item.get("stats_plus10")
        key = (item.get("category_id"), item.get("rarity"), normalized(str(item.get("name", ""))))
        if key in seen:
            fail(f"Duplicate catalogue entry: {key}")
        seen.add(key)
        item_names.add(normalized(str(item.get("name", ""))))
        rarity = item.get("rarity")
        if not isinstance(rarity, int) or not 1 <= rarity <= 21:
            fail(f"Invalid rarity: {item.get('name')}")
        if item.get("phase") != expected_phase(rarity):
            fail(f"Incorrect phase: {item.get('name')}")
        found_pairs.add((str(item.get("category_id")), str(item.get("phase"))))
        if not isinstance(stats, list) or len(stats) != 5 or not all(isinstance(value, int) and value >= 0 for value in stats):
            fail(f"Invalid base stats: {item.get('name')}")
        if stats_plus10 != plus_ten(stats):
            fail(f"Invalid +10 stats: {item.get('name')}")
        for field in ("name", "max_name", "master_skill", "enhancement_bonus", "main_ingredient", "rare_drop", "source_kind", "acquisition"):
            value = str(item.get(field, "")).strip()
            if not value or value == "—":
                fail(f"Missing {field}: {item.get('name')}")
            if FORBIDDEN_PUBLIC_URL.search(value) or FORBIDDEN_PUBLIC_REFERENCE.search(value):
                fail(f"Forbidden content in {field}: {item.get('name')}")

    if found_pairs != required_pairs:
        missing = sorted(required_pairs - found_pairs)
        unexpected = sorted(found_pairs - required_pairs)
        fail(f"Catalogue category/phase coverage is incomplete. Missing: {missing}; unexpected: {unexpected}")

    card_pairs = {(str(entry.get("category_id")), str(entry.get("phase"))) for entry in cards}
    if card_pairs != required_pairs:
        missing = sorted(required_pairs - card_pairs)
        unexpected = sorted(card_pairs - required_pairs)
        fail(f"Reference cards do not cover every required category/phase pair. Missing: {missing}; unexpected: {unexpected}")
    if len(card_pairs) != len(cards):
        fail("Reference cards duplicate a category/phase pair")

    missing_refs = sorted({reference for reference in item_refs if normalized(reference) not in item_names})
    if missing_refs:
        fail(f"Guide Equipment cross-references are absent from the catalogue: {', '.join(missing_refs)}")

    if integrity.get("expected_categories") != EXPECTED_CATEGORY_COUNT:
        fail("Catalogue integrity category count is incorrect")
    if integrity.get("expected_items") != EXPECTED_ITEM_COUNT:
        fail("Catalogue integrity item count is incorrect")
    if integrity.get("expected_category_phase_pairs") != EXPECTED_PHASE_CARD_COUNT:
        fail("Catalogue integrity phase-pair count is incorrect")
    if integrity.get("identity_sha256") != identity_sha256(items):
        fail("Catalogue integrity hash does not match the committed Item rows")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the complete static guide.")
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--allow-unbuilt", action="store_true", help="Only for local copy checks before the first catalogue snapshot.")
    args = parser.parse_args()
    site = args.site.resolve()
    if not site.is_dir():
        fail(f"Site directory not found: {site}")
    validate_public_tree(site)
    item_refs = validate_guide(site / "content" / "guide.html")
    validate_catalogue(site / "content" / "catalogo.json", item_refs, args.allow_unbuilt)
    print("Static-site validation passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
