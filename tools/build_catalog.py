#!/usr/bin/env python3
"""Build a reviewed, local Equipment catalogue snapshot.

This command materializes the local Equipment catalogue snapshot.  The Pages
workflow runs it only once when the repository still contains the initial
placeholder; later deployments publish the committed JSON file without fetching
catalogue data from the network.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

WIKI_API_URL = "https://aselia.fandom.com/api.php"
TIMEOUT_SECONDS = 60
EXPECTED_CATEGORY_COUNT = 18
EXPECTED_ITEM_COUNT = 350
PHASES = ("Main game", "Post-game")
EXPECTED_REFERENCE_CARD_COUNT = EXPECTED_CATEGORY_COUNT * len(PHASES)
HEADERS = {
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
    "User-Agent": "TalesOfBerseriaEquipmentGuide/4.0 (catalogue snapshot)",
}


@dataclass(frozen=True)
class Category:
    identifier: str
    label: str
    slot: str
    character: str
    page: str


CATEGORIES: tuple[Category, ...] = (
    Category("blades", "Blades", "Weapon", "Velvet", "ToB - Weapons (Blades)"),
    Category("short-swords", "Short Swords", "Weapon", "Rokurou", "ToB - Weapons (Short Swords)"),
    Category("paper", "Paper", "Weapon", "Laphicet", "ToB - Weapons (Paper)"),
    Category("bracelets", "Bracelets", "Weapon", "Eizen", "ToB - Weapons (Bracelets)"),
    Category("guardians", "Guardians", "Weapon", "Magilou", "ToB - Weapons (Guardians)"),
    Category("spears", "Spears", "Weapon", "Eleanor", "ToB - Weapons (Spears)"),
    Category("belts", "Belts", "Accessory", "Velvet", "ToB - Equipment (Belts)"),
    Category("talismans", "Talismans", "Accessory", "Rokurou", "ToB - Equipment (Talismans)"),
    Category("bags", "Bags", "Accessory", "Laphicet", "ToB - Equipment (Bags)"),
    Category("pendants", "Pendants", "Accessory", "Eizen", "ToB - Equipment (Pendants)"),
    Category("earrings", "Earrings", "Accessory", "Magilou", "ToB - Equipment (Earrings)"),
    Category("ribbons", "Ribbons", "Accessory", "Eleanor", "ToB - Equipment (Ribbons)"),
    Category("mens-armor", "Men’s Armor", "Armor", "Rokurou · Laphicet · Eizen", "ToB - Equipment (Men's Armor)"),
    Category("womens-armor", "Women’s Armor", "Armor", "Velvet · Magilou · Eleanor", "ToB - Equipment (Women's Armor)"),
    Category("rings", "Rings", "Ring", "All", "ToB - Equipment (Rings)"),
    Category("shoes", "Shoes", "Footwear", "All", "ToB - Equipment (Shoes)"),
    Category("mens-shoes", "Men’s Shoes", "Footwear", "Rokurou · Laphicet · Eizen", "ToB - Equipment (Men's Shoes)"),
    Category("womens-shoes", "Women’s Shoes", "Footwear", "Velvet · Magilou · Eleanor", "ToB - Equipment (Women's Shoes)"),
)

HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "rarity": ("rarity",),
    "name": ("name",),
    "p_atk": ("p.atk", "p atk", "physical attack"),
    "a_atk": ("a.atk", "a atk", "arte attack"),
    "p_def": ("p.def", "p def", "physical defense"),
    "a_def": ("a.def", "a def", "arte defense"),
    "focus": ("focus",),
    "master_skill": ("master skill",),
    "enhancement_bonus": ("enhancement bonus",),
    "main_ingredient": ("dismantle materials", "dismantle material"),
    "rare_drop": ("rare drop",),
    "max_name": ("max enhancement name",),
}
REQUIRED_FIELDS = set(HEADER_ALIASES)


def clean(value: str) -> str:
    value = html.unescape(value).replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" ·|–—-\t\r\n")


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", clean(value))
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = value.lower().replace("’", "'")
    value = re.sub(r"[^a-z0-9+%]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def english_lines(cell: Tag) -> list[str]:
    values: list[str] = []
    for line in cell.get_text("\n", strip=True).splitlines():
        line = clean(line)
        if not line or not re.search(r"[A-Za-z0-9]", line):
            continue
        if re.search(r"[\u3040-\u30ff\u3400-\u9fff\uff00-\uffef]", line):
            continue
        if line not in values:
            values.append(line)
    return values


def first_english(cell: Tag, default: str = "—") -> str:
    values = english_lines(cell)
    return values[0] if values else default


def all_english(cell: Tag, default: str = "—") -> str:
    values = english_lines(cell)
    return " / ".join(values) if values else default


def number_from_cell(cell: Tag) -> int:
    match = re.search(r"\d+", all_english(cell, "0"))
    return int(match.group(0)) if match else 0


def rarity_from_cell(cell: Tag) -> int | None:
    match = re.search(r"\b(\d{1,2})\b", all_english(cell, ""))
    if not match:
        return None
    rarity = int(match.group(1))
    return rarity if 1 <= rarity <= 21 else None


def exact_plus_ten(stats: list[int]) -> list[int]:
    """Return the displayed +10 values: each stat receives floor(100 * stat / total)."""
    total = sum(stats)
    if total <= 0:
        return list(stats)
    return [value + ((100 * value) // total) for value in stats]


def phase_from_rarity(rarity: int) -> str:
    """R19, R20 and R21 are the post-game equipment tiers."""
    return "Post-game" if rarity >= 19 else "Main game"


def source_from_fields(rarity: int, rare_drop: str) -> tuple[str, str]:
    """Create a transparent acquisition label without inventing a location."""
    has_rare_monster = rare_drop and rare_drop not in {"—", "N/A"}
    if has_rare_monster:
        return "rare_drop", f"Rare drop — {rare_drop}"
    if rarity <= 18 and rarity % 2 == 0:
        return "common_drop", "Common drop — Rarity pari; usa la regola Common Target nella sezione Farming."
    if rarity <= 18:
        return "chest_or_story", "Chest / shop / storia — nessun Monster Rare è registrato per questa scheda."
    if rarity in {19, 20}:
        return "postgame_chest_or_drop", "Post-game — chest o altra fonte di end-game; nessun Monster Rare è registrato per questa scheda."
    return "postgame_enemy_drop", "Post-game enemy drop — nessun Monster è registrato nella tabella strutturata."


def make_session() -> requests.Session:
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=1.5,
        allowed_methods=frozenset({"GET"}),
        status_forcelist=(429, 500, 502, 503, 504),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch_wiki_page(session: requests.Session, page: str) -> str:
    response = session.get(
        WIKI_API_URL,
        params={
            "action": "parse",
            "page": page,
            "prop": "text",
            "format": "json",
            "formatversion": "2",
            "origin": "*",
        },
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        detail = payload["error"].get("info", "unknown error")
        raise RuntimeError(f"Structured catalogue data error for {page}: {detail}")
    content = payload.get("parse", {}).get("text")
    if isinstance(content, dict):
        content = content.get("*")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(f"No equipment table returned for {page}")
    return content


def header_positions(table: Tag) -> dict[str, int] | None:
    header_row = table.find("tr")
    if not header_row:
        return None
    cells = header_row.find_all(["th", "td"], recursive=False)
    headers = [normalized(all_english(cell, "")) for cell in cells]
    positions: dict[str, int] = {}
    for field, aliases in HEADER_ALIASES.items():
        for index, header in enumerate(headers):
            if any(alias in header for alias in aliases):
                positions[field] = index
                break
    return positions if REQUIRED_FIELDS.issubset(positions) else None


def find_equipment_table(soup: BeautifulSoup) -> tuple[Tag, dict[str, int]]:
    for table in soup.find_all("table"):
        positions = header_positions(table)
        if positions:
            return table, positions
    raise RuntimeError("Equipment table not found on structured catalogue page")


def category_rows(session: requests.Session, category: Category) -> list[dict[str, Any]]:
    soup = BeautifulSoup(fetch_wiki_page(session, category.page), "html.parser")
    table, positions = find_equipment_table(soup)
    rows: list[dict[str, Any]] = []

    for row in table.find_all("tr")[1:]:
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) <= max(positions.values()):
            continue
        rarity = rarity_from_cell(cells[positions["rarity"]])
        name = first_english(cells[positions["name"]], "")
        if rarity is None or not name:
            continue
        stats = [
            number_from_cell(cells[positions["p_atk"]]),
            number_from_cell(cells[positions["a_atk"]]),
            number_from_cell(cells[positions["p_def"]]),
            number_from_cell(cells[positions["a_def"]]),
            number_from_cell(cells[positions["focus"]]),
        ]
        rare_drop = first_english(cells[positions["rare_drop"]], "—")
        source_kind, acquisition = source_from_fields(rarity, rare_drop)
        rows.append({
            "category_id": category.identifier,
            "category": category.label,
            "slot": category.slot,
            "character": category.character,
            "rarity": rarity,
            "phase": phase_from_rarity(rarity),
            "name": name,
            "max_name": first_english(cells[positions["max_name"]]),
            "stats": stats,
            "stats_plus10": exact_plus_ten(stats),
            "master_skill": all_english(cells[positions["master_skill"]]),
            "enhancement_bonus": all_english(cells[positions["enhancement_bonus"]]),
            "main_ingredient": first_english(cells[positions["main_ingredient"]]),
            "rare_drop": rare_drop,
            "source_kind": source_kind,
            "acquisition": acquisition,
        })
    if not rows:
        raise RuntimeError(f"No equipment rows parsed for {category.label}")
    return rows


def reference_reason(item: dict[str, Any]) -> str:
    labels = ("Atk", "A.Atk", "Def", "A.Def", "Focus")
    stats = [int(value) for value in item["stats"]]
    strongest_index = max(range(len(stats)), key=lambda index: stats[index])
    strongest_label = labels[strongest_index]
    strongest_value = stats[strongest_index]
    period = "storia" if item["phase"] == "Main game" else "post-game"
    return (
        f"Scheda di confronto per la {period}: Rarity {item['rarity']}, "
        f"{strongest_label} {strongest_value} come valore più alto. "
        f"Confronta Master Skill e Enhancement Bonus prima di decidere."
    )


def expected_category_phase_pairs(categories: list[dict[str, str]]) -> set[tuple[str, str]]:
    """Return the complete category/phase matrix required by the source catalogue."""
    return {(str(category["id"]), phase) for category in categories for phase in PHASES}


def category_phase_pairs(items: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {(str(item["category_id"]), str(item["phase"])) for item in items}


def reference_cards(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select one comparison card for every required category/phase pair."""
    cards: list[dict[str, Any]] = []
    available_pairs = category_phase_pairs(items)
    expected_pairs = expected_category_phase_pairs([
        {"id": category.identifier}
        for category in CATEGORIES
    ])
    missing_pairs = sorted(expected_pairs - available_pairs)
    if missing_pairs:
        raise RuntimeError(f"Catalogue is missing required category/phase pairs: {missing_pairs}")

    for category in CATEGORIES:
        for phase in PHASES:
            candidates = [
                item for item in items
                if item["category_id"] == category.identifier and item["phase"] == phase
            ]
            selected = max(candidates, key=lambda item: (sum(item["stats"]), item["rarity"], item["name"].lower()))
            cards.append({
                "category_id": selected["category_id"],
                "category": selected["category"],
                "character": selected["character"],
                "rarity": selected["rarity"],
                "name": selected["name"],
                "phase": selected["phase"],
                "reason": reference_reason(selected),
            })
    return sorted(cards, key=lambda entry: (entry["phase"] != "Main game", entry["rarity"], entry["category_id"]))


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


def validate(categories: list[dict[str, str]], items: list[dict[str, Any]], cards: list[dict[str, Any]]) -> None:
    if len(categories) != EXPECTED_CATEGORY_COUNT:
        raise RuntimeError(f"The category manifest must contain exactly {EXPECTED_CATEGORY_COUNT} categories")
    if len(items) != EXPECTED_ITEM_COUNT:
        raise RuntimeError(f"Catalogue has {len(items)} items; expected exactly {EXPECTED_ITEM_COUNT}")

    expected_categories = {category["id"] for category in categories}
    found_categories = {item["category_id"] for item in items}
    if found_categories != expected_categories:
        raise RuntimeError(f"Category mismatch. Missing: {sorted(expected_categories - found_categories)}; unexpected: {sorted(found_categories - expected_categories)}")

    keys: set[tuple[str, int, str]] = set()
    found_pairs: set[tuple[str, str]] = set()
    for item in items:
        key = (str(item["category_id"]), int(item["rarity"]), normalized(str(item["name"])))
        if key in keys:
            raise RuntimeError(f"Duplicate catalogue row: {key}")
        keys.add(key)
        expected_phase = phase_from_rarity(int(item["rarity"]))
        if item["phase"] != expected_phase:
            raise RuntimeError(f"Incorrect phase for {item['name']}: expected {expected_phase}")
        found_pairs.add((str(item["category_id"]), str(item["phase"])))
        if len(item["stats"]) != 5 or len(item["stats_plus10"]) != 5:
            raise RuntimeError(f"Invalid stat vector for {item['name']}")
        if item["stats_plus10"] != exact_plus_ten(item["stats"]):
            raise RuntimeError(f"Incorrect +10 values for {item['name']}")
        for field in ("name", "max_name", "master_skill", "enhancement_bonus", "main_ingredient", "rare_drop", "source_kind", "acquisition"):
            value = str(item.get(field, "")).strip()
            if not value or value == "—":
                raise RuntimeError(f"Missing {field} for {item['name']}")
            if re.search(r"https?://", value, re.IGNORECASE):
                raise RuntimeError(f"External URL leaked into item field: {item['name']}")

    required_pairs = expected_category_phase_pairs(categories)
    if len(required_pairs) != EXPECTED_REFERENCE_CARD_COUNT:
        raise RuntimeError(
            f"Internal category/phase matrix has {len(required_pairs)} pairs; "
            f"expected exactly {EXPECTED_REFERENCE_CARD_COUNT}"
        )
    if found_pairs != required_pairs:
        missing = sorted(required_pairs - found_pairs)
        unexpected = sorted(found_pairs - required_pairs)
        raise RuntimeError(f"Catalogue category/phase coverage mismatch. Missing: {missing}; unexpected: {unexpected}")

    card_pairs = {(str(card["category_id"]), str(card["phase"])) for card in cards}
    if len(cards) != EXPECTED_REFERENCE_CARD_COUNT:
        raise RuntimeError(
            f"Reference cards have {len(cards)} entries; expected exactly {EXPECTED_REFERENCE_CARD_COUNT}"
        )
    if card_pairs != required_pairs:
        missing = sorted(required_pairs - card_pairs)
        unexpected = sorted(card_pairs - required_pairs)
        raise RuntimeError(f"Reference-card coverage mismatch. Missing: {missing}; unexpected: {unexpected}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the committed local Equipment catalogue snapshot.")
    parser.add_argument("--output", type=Path, default=Path("site/content/catalogo.json"))
    args = parser.parse_args()

    session = make_session()
    categories = [
        {"id": category.identifier, "label": category.label, "slot": category.slot, "character": category.character}
        for category in CATEGORIES
    ]
    items: list[dict[str, Any]] = []
    for category in CATEGORIES:
        print(f"[catalogue] {category.label}", file=sys.stderr)
        items.extend(category_rows(session, category))

    items.sort(key=lambda item: (item["category_id"], item["rarity"], normalized(item["name"])))
    cards = reference_cards(items)
    validate(categories, items, cards)

    payload = {
        "schema_version": 4,
        "complete": True,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "categories": categories,
        "items": items,
        "reference_cards": cards,
        "integrity": {
            "expected_categories": EXPECTED_CATEGORY_COUNT,
            "expected_items": EXPECTED_ITEM_COUNT,
            "expected_category_phase_pairs": EXPECTED_REFERENCE_CARD_COUNT,
            "identity_sha256": identity_sha256(items),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[catalogue] wrote {len(items)} items and {len(cards)} reference cards to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
