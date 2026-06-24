#!/usr/bin/env python3
"""Build the complete, local Tales of Berseria Equipment catalogue.

The deployed site receives only the generated JSON. This builder collects structured
item data, enriches it with progression/acquisition text, derives exact +10 values,
and refuses to produce a partial catalogue.
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
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup, Tag

WIKI_API_URL = "https://aselia.fandom.com/api.php"
REFERENCE_GUIDE_URL = "https://gamefaqs.gamespot.com/pc/184665-tales-of-berseria/faqs/74517?print=1"
TIMEOUT_SECONDS = 60
HEADERS = {
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "User-Agent": "TalesOfBerseriaGuideBuilder/2.0 (static GitHub Pages build)",
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

REQUIRED_FIELDS = {
    "rarity", "name", "p_atk", "a_atk", "p_def", "a_def", "focus",
    "master_skill", "enhancement_bonus", "main_ingredient", "rare_drop", "max_name",
}

LOCATION_WORDS = re.compile(
    r"\b(shop|chest|common drop|code red|story|titania|innominat|heavenly|figahl|"
    r"hellawes|yseult|taliesin|meirchio|zekson|katz|ruins|forest|marsh|isle|"
    r"mount|grotto|cavern|tunnel|laban|faldies|earthpulse|aldina|davahl|baird|"
    r"morgana|vortigern|hexen|hallowed|ex-dungeon)\b",
    re.IGNORECASE,
)


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


def fetch_reference_text(session: requests.Session) -> str:
    response = session.get(REFERENCE_GUIDE_URL, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n", strip=True)
    text = text.replace("\r", "")
    if len(text) < 100_000:
        raise RuntimeError("The reference guide response is unexpectedly short; refusing to build incomplete data.")
    return text


def fetch_wiki_page(session: requests.Session, page: str) -> str:
    response = session.get(
        WIKI_API_URL,
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
        raise RuntimeError(f"Structured item data error for {page}: {payload['error'].get('info', 'unknown error')}")
    content = payload.get("parse", {}).get("text")
    if isinstance(content, dict):
        content = content.get("*")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(f"No structured item table returned for {page}")
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
    raise RuntimeError("Equipment table not found on structured item page")


def category_main_game_marker(reference: str, category: Category) -> int | None:
    """Return the actual equipment-table marker, never the table-of-contents entry.

    The printable guide repeats every category name in its table of contents.  The
    ``<Category> (Main Game)`` marker occurs only in the actual category section,
    so it is the reliable delimiter for the source text.
    """
    labels = (category.label, category.label.replace("’", "'"), category.label.replace("'", "’"))
    candidates: list[int] = []
    for label in labels:
        for match in re.finditer(rf"(?im)^\s*{re.escape(label)}\s*\(Main\s*Game\)\s*$", reference):
            candidates.append(match.start())
    return min(candidates) if candidates else None


def find_category_segment(reference: str, category: Category) -> str:
    marker = category_main_game_marker(reference, category)
    if marker is None:
        raise RuntimeError(f"Main-game source section not found for {category.label}")

    labels = (category.label, category.label.replace("’", "'"), category.label.replace("'", "’"))
    heading_positions: list[int] = []
    for label in labels:
        for match in re.finditer(rf"(?im)^\s*(?:###\s*)?{re.escape(label)}\s*$", reference[:marker]):
            heading_positions.append(match.start())
    start = max(heading_positions) if heading_positions else marker

    later_markers = [
        candidate
        for other in CATEGORIES
        if other.identifier != category.identifier
        for candidate in [category_main_game_marker(reference, other)]
        if candidate is not None and candidate > marker
    ]
    end = min(later_markers) if later_markers else len(reference)
    return reference[start:end]


def line_window(value: str, start: int, end: int) -> list[str]:
    segment = value[start:end]
    return [clean(line) for line in segment.splitlines() if clean(line)]


def source_records(reference_segment: str) -> list[dict[str, Any]]:
    """Split the equipment-table portion of a category into Rarity entries.

    The source uses one Rarity marker per table row.  Names differ slightly in a few
    places between data sources, so retaining the ordered Rarity record is more
    reliable than matching only a display name.
    """
    base = re.split(r"(?im)^\s*(?:####\s*)?Noteworthy\b", reference_segment, maxsplit=1)[0]
    matches = list(re.finditer(r"(?m)^\s*R\s*(\d{1,2})\b", base))
    records: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(base)
        before = normalized(base[:match.start()])
        records.append({
            "rarity": int(match.group(1)),
            "entry": base[match.start():end],
            "phase": "Post-game" if re.search(r"post[- ]?game|ex[- ]?dungeon", before, re.IGNORECASE) else "Main game",
        })
    return records


def item_entry(records: list[dict[str, Any]], rarity: int, name: str, occurrence: int) -> tuple[str, str]:
    escaped = re.escape(name).replace("\\ ", r"\s+")
    pattern = re.compile(rf"\bR\s*{rarity}\s+{escaped}\b", re.IGNORECASE)
    exact = [record for record in records if pattern.search(record["entry"])]
    if exact:
        return exact[0]["entry"], exact[0]["phase"]
    same_rarity = [record for record in records if record["rarity"] == rarity]
    if occurrence < len(same_rarity):
        return same_rarity[occurrence]["entry"], same_rarity[occurrence]["phase"]
    if same_rarity:
        return same_rarity[-1]["entry"], same_rarity[-1]["phase"]
    return "", "Main game" if rarity <= 17 else "Post-game"


def acquisition_from_entry(entry: str, rare_drop: str) -> str:
    if not entry:
        if rare_drop and rare_drop not in {"—", "N/A"}:
            return f"Rare drop: {rare_drop}"
        return "Fonte da verificare nella scheda di gioco"

    lines = [clean(line) for line in entry.splitlines() if clean(line)]
    marked = [index for index, line in enumerate(lines) if LOCATION_WORDS.search(line)]
    if marked:
        # Start at the first explicit acquisition marker.  The Monster is carried in
        # the structured ``rare_drop`` field and is prepended below when applicable;
        # this avoids accidentally treating a preceding stat line as a location.
        result = " ".join(lines[marked[0]:])
        result = re.sub(r"\s+", " ", result)
        if rare_drop and rare_drop not in {"—", "N/A"} and normalized(rare_drop) not in normalized(result):
            result = f"Rare drop: {rare_drop} · {result}"
        if len(result) > 360:
            result = result[:357].rstrip() + "…"
        return result

    if rare_drop and rare_drop not in {"—", "N/A"}:
        return f"Rare drop: {rare_drop}"
    return "Fonte da verificare nella scheda di gioco"


def noteworthy_reason(item: dict[str, Any]) -> str:
    """Write a short Italian, data-backed recommendation for a selected Item."""
    labels = ("Atk", "A.Atk", "Def", "A.Def", "Focus")
    primary_by_slot = {"Weapon": "Atk", "Accessory": "A.Atk", "Armor": "Def", "Ring": "A.Def", "Footwear": "Focus"}
    stats = [int(value) for value in item["stats"]]
    total = sum(stats)
    nonzero = [(label, value) for label, value in zip(labels, stats) if value > 0]
    primary = primary_by_slot[item["slot"]]
    primary_value = stats[labels.index(primary)]

    if total and primary_value / total >= 0.75:
        stat_note = f"concentra quasi tutti i suoi punti in {primary}"
    elif len(nonzero) == 1:
        stat_note = f"concentra tutti i suoi punti in {nonzero[0][0]}"
    else:
        split = " e ".join(f"{label} {value}" for label, value in nonzero)
        stat_note = f"distribuisce le statistiche tra {split}"

    period = "durante la storia" if item["phase"] == "Main game" else "nel post-game"
    return (
        f"Scelta consigliata {period}: {stat_note}. "
        f"La Master Skill è {item['master_skill']}; l'Enhancement Bonus è {item['enhancement_bonus']}."
    )


def category_rows(session: requests.Session, category: Category, reference: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(fetch_wiki_page(session, category.page), "html.parser")
    table, positions = find_equipment_table(soup)
    reference_segment = find_category_segment(reference, category)
    records = source_records(reference_segment)
    rarity_occurrences: dict[int, int] = {}
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
        occurrence = rarity_occurrences.get(rarity, 0)
        rarity_occurrences[rarity] = occurrence + 1
        entry, phase = item_entry(records, rarity, name, occurrence)
        rows.append({
            "category_id": category.identifier,
            "category": category.label,
            "slot": category.slot,
            "character": category.character,
            "rarity": rarity,
            "phase": phase,
            "name": name,
            "max_name": first_english(cells[positions["max_name"]]),
            "stats": stats,
            "stats_plus10": exact_plus_ten(stats),
            "master_skill": all_english(cells[positions["master_skill"]]),
            "enhancement_bonus": all_english(cells[positions["enhancement_bonus"]]),
            "main_ingredient": first_english(cells[positions["main_ingredient"]]),
            "rare_drop": rare_drop,
            "acquisition": acquisition_from_entry(entry, rare_drop),
        })
    if not rows:
        raise RuntimeError(f"No rows parsed for {category.label}")
    return rows


def notable_entries(reference: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in items:
        category_label = item["category"]
        category_pattern = re.escape(category_label).replace("’", "[’']").replace("'", "[’']")
        heading = re.compile(rf"Noteworthy\s+{category_pattern}", re.IGNORECASE)
        found = heading.search(reference)
        if not found:
            continue
        window = reference[found.end():found.end() + 35_000]
        pattern = re.compile(rf"\bR\s*{item['rarity']}\s+{re.escape(item['name']).replace('\\ ', r'\s+')}\b", re.IGNORECASE)
        if not pattern.search(window):
            continue
        results.append({
            "category_id": item["category_id"],
            "category": item["category"],
            "character": item["character"],
            "rarity": item["rarity"],
            "name": item["name"],
            "phase": item["phase"],
            "reason": noteworthy_reason(item),
        })
    unique: dict[tuple[str, int, str], dict[str, Any]] = {}
    for entry in results:
        unique[(entry["category_id"], entry["rarity"], entry["name"])] = entry
    return sorted(unique.values(), key=lambda entry: (entry["phase"] != "Main game", entry["rarity"], entry["name"].lower()))


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
        raise RuntimeError(f"Only {len(noteworthy)} noteworthy entries found; expected at least 36")
    noteworthy_categories = {entry["category_id"] for entry in noteworthy}
    if noteworthy_categories != expected:
        raise RuntimeError("Noteworthy recommendations must cover all 18 categories")

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
        for field in ("name", "master_skill", "enhancement_bonus", "main_ingredient", "acquisition"):
            if not str(item.get(field, "")).strip() or str(item.get(field)).strip() == "—":
                raise RuntimeError(f"Missing {field} for {item['name']}")
        if re.search(r"https?://|gamefaqs|gamespot", item["acquisition"], re.IGNORECASE):
            raise RuntimeError(f"External reference leaked into acquisition for {item['name']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a complete local Equipment catalogue.")
    parser.add_argument("--output", type=Path, default=Path("site/content/catalogo.json"))
    parser.add_argument("--reference-cache", type=Path, default=None, help="Optional cached reference text for reproducible/offline builds.")
    args = parser.parse_args()

    session = requests.Session()
    if args.reference_cache and args.reference_cache.exists():
        reference = args.reference_cache.read_text(encoding="utf-8")
    else:
        print("[catalogue] fetching reference text", file=sys.stderr)
        reference = fetch_reference_text(session)
        if args.reference_cache:
            args.reference_cache.parent.mkdir(parents=True, exist_ok=True)
            args.reference_cache.write_text(reference, encoding="utf-8")

    categories = [
        {"id": category.identifier, "label": category.label, "slot": category.slot, "character": category.character}
        for category in CATEGORIES
    ]
    items: list[dict[str, Any]] = []
    for category in CATEGORIES:
        print(f"[catalogue] {category.label}", file=sys.stderr)
        items.extend(category_rows(session, category, reference))

    items.sort(key=lambda item: (item["category_id"], item["rarity"], normalized(item["name"])))
    noteworthy = notable_entries(reference, items)
    validate(categories, items, noteworthy)

    payload = {
        "schema_version": 2,
        "complete": True,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "categories": categories,
        "items": items,
        "noteworthy": noteworthy,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[catalogue] wrote {len(items)} items and {len(noteworthy)} noteworthy entries to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
