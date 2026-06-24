#!/usr/bin/env python3
"""Build the local Equipment catalogue used by the static site."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

API_URL = "https://aselia.fandom.com/api.php"
TIMEOUT_SECONDS = 45
HEADERS = {
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
    "User-Agent": "TalesOfBerseriaEquipmentGuide/1.0 (static catalogue builder)",
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

HEADER_ALIASES = {
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


def normalize_header(value: str) -> str:
    value = value.lower()
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def clean_line(value: str) -> str:
    value = html.unescape(value).replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" ·|–—-\t\r\n")


def english_lines(cell: Tag) -> list[str]:
    lines: list[str] = []

    for raw_line in cell.get_text("\n", strip=True).splitlines():
        line = clean_line(raw_line)

        if not line:
            continue

        if not re.search(r"[A-Za-z0-9]", line):
            continue

        if re.search(r"[\u3040-\u30ff\u3400-\u9fff\uff00-\uffef]", line):
            continue

        if line not in lines:
            lines.append(line)

    return lines


def first_english(cell: Tag, default: str = "—") -> str:
    lines = english_lines(cell)

    if not lines:
        return default

    return lines[0]


def all_english(cell: Tag, default: str = "—") -> str:
    lines = english_lines(cell)

    if not lines:
        return default

    return " / ".join(lines)


def number_from_cell(cell: Tag) -> int:
    match = re.search(r"\d+", all_english(cell, "0"))
    return int(match.group(0)) if match else 0


def rarity_from_cell(cell: Tag) -> int | None:
    match = re.search(r"\b(\d{1,2})\b", all_english(cell, ""))

    if not match:
        return None

    value = int(match.group(1))
    return value if 1 <= value <= 21 else None


def fetch_page_html(session: requests.Session, page: str) -> str:
    response = session.get(
        API_URL,
        params={
            "action": "parse",
            "page": page,
            "prop": "text",
            "format": "json",
            "formatversion": "2",
        },
        headers=HEADERS,
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()

    if "error" in payload:
        raise RuntimeError(f"API error for {page}: {payload['error'].get('info', 'unknown error')}")

    parsed = payload.get("parse", {})
    content = parsed.get("text")

    if isinstance(content, dict):
        content = content.get("*")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(f"No parsed HTML returned for {page}")

    return content


def header_positions(table: Tag) -> dict[str, int] | None:
    row = table.find("tr")

    if not row:
        return None

    cells = row.find_all(["th", "td"], recursive=False)
    headers = [normalize_header(all_english(cell, "")) for cell in cells]
    positions: dict[str, int] = {}

    for field, aliases in HEADER_ALIASES.items():
        for index, header in enumerate(headers):
            if any(alias in header for alias in aliases):
                positions[field] = index
                break

    required = {"rarity", "name", "p_atk", "a_atk", "p_def", "a_def", "focus", "master_skill", "enhancement_bonus", "main_ingredient", "rare_drop", "max_name"}
    return positions if required.issubset(positions) else None


def find_equipment_table(soup: BeautifulSoup) -> tuple[Tag, dict[str, int]]:
    for table in soup.find_all("table"):
        positions = header_positions(table)

        if positions:
            return table, positions

    raise RuntimeError("Equipment table not found")


def parse_category(session: requests.Session, category: Category) -> list[dict[str, Any]]:
    soup = BeautifulSoup(fetch_page_html(session, category.page), "html.parser")
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

        rows.append(
            {
                "category_id": category.identifier,
                "rarity": rarity,
                "name": name,
                "stats": [
                    number_from_cell(cells[positions["p_atk"]]),
                    number_from_cell(cells[positions["a_atk"]]),
                    number_from_cell(cells[positions["p_def"]]),
                    number_from_cell(cells[positions["a_def"]]),
                    number_from_cell(cells[positions["focus"]]),
                ],
                "master_skill": all_english(cells[positions["master_skill"]]),
                "enhancement_bonus": all_english(cells[positions["enhancement_bonus"]]),
                "main_ingredient": first_english(cells[positions["main_ingredient"]]),
                "rare_drop": first_english(cells[positions["rare_drop"]], "N/A"),
                "max_name": first_english(cells[positions["max_name"]]),
                "availability": "Common / shop / chest / story",
            }
        )

    if not rows:
        raise RuntimeError(f"No equipment rows parsed for {category.label}")

    return rows


def validate_catalogue(categories: list[dict[str, str]], items: list[dict[str, Any]]) -> None:
    found = {item["category_id"] for item in items}
    expected = {category["id"] for category in categories}
    missing = expected - found

    if missing:
        raise RuntimeError(f"Missing catalogue categories: {', '.join(sorted(missing))}")

    if len(items) < 300:
        raise RuntimeError(f"Catalogue has only {len(items)} items; expected at least 300")

    duplicate_keys: set[tuple[str, int, str]] = set()

    for item in items:
        key = (item["category_id"], item["rarity"], item["name"])

        if key in duplicate_keys:
            raise RuntimeError(f"Duplicate catalogue row: {key}")

        duplicate_keys.add(key)

        if len(item["stats"]) != 5:
            raise RuntimeError(f"Invalid stat vector for {item['name']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the complete local Equipment catalogue.")
    parser.add_argument("--output", type=Path, default=Path("site/content/catalogo.json"))
    args = parser.parse_args()

    session = requests.Session()
    categories = [
        {
            "id": category.identifier,
            "label": category.label,
            "slot": category.slot,
            "character": category.character,
        }
        for category in CATEGORIES
    ]
    items: list[dict[str, Any]] = []

    for category in CATEGORIES:
        print(f"[catalogue] {category.label}", file=sys.stderr)
        items.extend(parse_category(session, category))

    items.sort(key=lambda item: (item["category_id"], item["rarity"], item["name"].lower()))
    validate_catalogue(categories, items)

    payload = {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "categories": categories,
        "items": items,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[catalogue] wrote {len(items)} items to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
