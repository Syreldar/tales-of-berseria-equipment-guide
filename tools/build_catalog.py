#!/usr/bin/env python3
"""Build the published Tales of Berseria Equipment catalogue.

This script deliberately has no dependency on the original guide host.  It reads
structured equipment tables from the Aselia Wiki API, turns them into a local JSON
file, validates the complete result, and the Pages workflow publishes that file as
part of the static artifact.
"""

from __future__ import annotations

import argparse
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
HEADERS = {
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
    "User-Agent": "TalesOfBerseriaEquipmentGuide/3.0 (+static Pages build)",
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
    total = sum(stats)
    if total <= 0:
        return list(stats)
    return [value + ((100 * value) // total) for value in stats]


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


def phase_from_rarity(rarity: int) -> str:
    """The standard lists place the final Rarity tier in post-game."""
    return "Post-game" if rarity >= 21 else "Main game"


def acquisition_from_fields(rarity: int, rare_drop: str) -> str:
    if rare_drop and rare_drop not in {"—", "N/A"}:
        return f"Rare drop: {rare_drop}"
    if rarity % 2 == 0:
        return "Common drop: Rarity pari; può provenire da Monster, chest, shop o storia."
    return "Acquisizione non specificata nella tabella strutturata; verifica l’area di gioco."


def noteworthy_reason(item: dict[str, Any]) -> str:
    labels = ("Atk", "A.Atk", "Def", "A.Def", "Focus")
    stats = [int(value) for value in item["stats"]]
    total = sum(stats)
    strongest_index = max(range(len(stats)), key=lambda index: stats[index])
    strongest_label = labels[strongest_index]
    strongest_value = stats[strongest_index]
    period = "durante la storia" if item["phase"] == "Main game" else "nel post-game"
    return (
        f"Riferimento utile {period}: totale statistiche {total}, con {strongest_label} {strongest_value} come valore principale. "
        f"Controlla anche la Master Skill ({item['master_skill']}) prima di sostituire l’Equipment attuale."
    )


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
            "acquisition": acquisition_from_fields(rarity, rare_drop),
        })
    if not rows:
        raise RuntimeError(f"No equipment rows parsed for {category.label}")
    return rows


def notable_entries(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select one late-story and one post-game reference item per category.

    These are navigation aids derived from the static statistics; they are not a
    replacement for the detailed progression explanations in the guide.
    """
    results: list[dict[str, Any]] = []
    for category in CATEGORIES:
        group = [item for item in items if item["category_id"] == category.identifier]
        for phase in ("Main game", "Post-game"):
            candidates = [item for item in group if item["phase"] == phase]
            if not candidates:
                continue
            selected = max(candidates, key=lambda item: (sum(item["stats"]), item["rarity"], item["name"].lower()))
            results.append({
                "category_id": selected["category_id"],
                "category": selected["category"],
                "character": selected["character"],
                "rarity": selected["rarity"],
                "name": selected["name"],
                "phase": selected["phase"],
                "reason": noteworthy_reason(selected),
            })
    return sorted(results, key=lambda entry: (entry["category_id"], entry["phase"], entry["rarity"]))


def validate(categories: list[dict[str, str]], items: list[dict[str, Any]], noteworthy: list[dict[str, Any]]) -> None:
    expected = {category["id"] for category in categories}
    found = {item["category_id"] for item in items}
    if found != expected:
        raise RuntimeError(f"Category mismatch. Missing: {sorted(expected - found)}; unexpected: {sorted(found - expected)}")
    if len(categories) != 18:
        raise RuntimeError("The category manifest must contain all 18 categories")
    if len(items) < 350:
        raise RuntimeError(f"Catalogue has {len(items)} items; at least 350 are required")
    if len(noteworthy) < 36:
        raise RuntimeError(f"Only {len(noteworthy)} navigation entries found; expected at least 36")
    noteworthy_categories = {entry["category_id"] for entry in noteworthy}
    if noteworthy_categories != expected:
        raise RuntimeError("Navigation entries must cover all 18 categories")

    keys: set[tuple[str, int, str]] = set()
    for item in items:
        key = (item["category_id"], int(item["rarity"]), normalized(item["name"]))
        if key in keys:
            raise RuntimeError(f"Duplicate catalogue row: {key}")
        keys.add(key)
        if item["phase"] not in {"Main game", "Post-game"}:
            raise RuntimeError(f"Invalid phase for {item['name']}")
        if len(item["stats"]) != 5 or len(item["stats_plus10"]) != 5:
            raise RuntimeError(f"Invalid stat vector for {item['name']}")
        if item["stats_plus10"] != exact_plus_ten(item["stats"]):
            raise RuntimeError(f"Incorrect +10 values for {item['name']}")
        for field in ("name", "max_name", "master_skill", "enhancement_bonus", "main_ingredient", "acquisition"):
            value = str(item.get(field, "")).strip()
            if not value or value == "—":
                raise RuntimeError(f"Missing {field} for {item['name']}")
            if re.search(r"https?://", value, re.IGNORECASE):
                raise RuntimeError(f"External URL leaked into item field: {item['name']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the published local Equipment catalogue.")
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
    noteworthy = notable_entries(items)
    validate(categories, items, noteworthy)

    payload = {
        "schema_version": 3,
        "complete": True,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "categories": categories,
        "items": items,
        "noteworthy": noteworthy,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[catalogue] wrote {len(items)} items and {len(noteworthy)} navigation entries to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
