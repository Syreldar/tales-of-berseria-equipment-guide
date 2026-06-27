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
    "User-Agent": "TalesOfBerseriaEquipmentGuide/5.0 (catalogue snapshot)",
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

CHARACTER_GROWTH: tuple[dict[str, Any], ...] = (
    {"name": "Velvet", "stage": 0, "base": [66, 2.44, 2.44, 2.85, 1.63, 2.85], "level_200": [6864, 253.8, 253.8, 296.4, 169.5, 296.4]},
    {"name": "Rokurou", "stage": 1, "base": [70, 2.75, 1.97, 3.15, 1.97, 1.97], "level_200": [7280, 286, 204.9, 327.6, 204.9, 204.9]},
    {"name": "Laphicet", "stage": 2, "base": [54, 1.81, 3.17, 2.26, 3.62, 2.72], "level_200": [5616, 188.2, 329.7, 235, 376.5, 282.9]},
    {"name": "Eizen", "stage": 3, "base": [64, 2.48, 2.48, 1.65, 2.48, 3.31], "level_200": [6656, 257.9, 257.9, 171.6, 257.9, 344.2]},
    {"name": "Magilou", "stage": 4, "base": [58, 2.18, 3.49, 2.62, 3.05, 1.75], "level_200": [6032, 226.7, 363, 272.5, 317.2, 182]},
    {"name": "Eleanor", "stage": 5, "base": [62, 3.37, 1.68, 2.53, 2.53, 2.53], "level_200": [6448, 350.5, 174.7, 263.1, 263.1, 263.1]},
)

RECOMMENDED_EQUIPMENT: tuple[dict[str, Any], ...] = (
    {"character": "All", "stage": 0, "order": 10, "checkpoint": "Taliesin shop", "item": "Force Ring", "category": "Rings", "rarity": 10, "reason": "Reliable Arte Defense option when the party reaches its first R10 shop upgrade."},
    {"character": "All", "stage": 0, "order": 20, "checkpoint": "Stonebury shop", "item": "Quartz Boots", "category": "Shoes", "rarity": 12, "reason": "Universal Footwear pick with a useful Stun-oriented skill while replacing older common drops."},
    {"character": "All", "stage": 0, "order": 30, "checkpoint": "Mount Killaraus", "item": "Barrier Ring", "category": "Rings", "rarity": 15, "reason": "High Arte Defense Ring for encounters where arte damage is the main danger."},
    {"character": "All", "stage": 0, "order": 40, "checkpoint": "Innominat / Katz routes", "item": "Plated Ring", "category": "Rings", "rarity": 17, "reason": "Convenient late-story universal Ring when moving into the final equipment tiers."},

    {"character": "Velvet", "stage": 0, "order": 10, "checkpoint": "Warg Forest", "item": "Cassandra Sash", "category": "Belts", "rarity": 7, "reason": "Early Arte Attack Belt with fire-hit utility; a meaningful upgrade as rare R7 equipment begins appearing."},
    {"character": "Velvet", "stage": 0, "order": 20, "checkpoint": "Yseult shop", "item": "Amphibole Blade", "category": "Blades", "rarity": 8, "reason": "Accessible R8 Blade that keeps physical offense moving without waiting for a rare drop."},
    {"character": "Velvet", "stage": 0, "order": 30, "checkpoint": "Hexen Isle", "item": "Fonon Blade", "category": "Blades", "rarity": 15, "reason": "Late-story Blade with an offensive distribution suited to a frontline set."},
    {"character": "Velvet", "stage": 0, "order": 40, "checkpoint": "Innominat", "item": "Helmut Schmidt Sash", "category": "Belts", "rarity": 17, "reason": "Final-story Belt checkpoint before replacing the set with endgame equipment."},
    {"character": "Velvet", "stage": 0, "order": 50, "checkpoint": "Innominat", "item": "Pegasus Wings", "category": "Women’s Shoes", "rarity": 17, "reason": "Late Footwear upgrade for the final route; compare its Master Skill before dismantling older shoes."},
    {"character": "Velvet", "stage": 0, "order": 60, "checkpoint": "End of main game", "item": "Adamantine Blade", "category": "Blades", "rarity": 18, "reason": "R18 main-game Blade to complete the progression before post-game tiers."},

    {"character": "Rokurou", "stage": 1, "order": 10, "checkpoint": "Story reward", "item": "Kurogane Daggers", "category": "Short Swords", "rarity": 15, "reason": "Keep the story weapon long enough to learn its Master Skill; it has a notably balanced offensive spread."},
    {"character": "Rokurou", "stage": 1, "order": 20, "checkpoint": "Taliesin shop", "item": "Feldspar Daggers", "category": "Short Swords", "rarity": 10, "reason": "Direct shop replacement that is easy to obtain while entering the R10 equipment tier."},
    {"character": "Rokurou", "stage": 1, "order": 30, "checkpoint": "Innominat", "item": "Soothing Knife", "category": "Talismans", "rarity": 17, "reason": "Late-story Short Swords choice with a final-tier Master Skill to learn."},
    {"character": "Rokurou", "stage": 1, "order": 40, "checkpoint": "Innominat / Katz routes", "item": "Stygian Daggers", "category": "Short Swords", "rarity": 17, "reason": "Alternative final R17 Short Swords route, useful when the other weapon has already taught its skill."},
    {"character": "Rokurou", "stage": 1, "order": 50, "checkpoint": "Empyrean’s Throne return", "item": "Kaiser Road", "category": "Men’s Shoes", "rarity": 17, "reason": "Late Footwear upgrade for a durable close-range set."},
    {"character": "Rokurou", "stage": 1, "order": 60, "checkpoint": "Meirchio shop", "item": "Mythril Waistcoat", "category": "Men’s Armor", "rarity": 16, "reason": "Reliable Armor shop upgrade before the final R17 route."},

    {"character": "Laphicet", "stage": 2, "order": 10, "checkpoint": "Vester Tunnels", "item": "Mars Satchel", "category": "Bags", "rarity": 7, "reason": "Early Bag with strong Arte Attack value and a burn-oriented Master Skill."},
    {"character": "Laphicet", "stage": 2, "order": 20, "checkpoint": "Manann Reef", "item": "Secret Histories", "category": "Paper", "rarity": 9, "reason": "Rare Paper checkpoint for a caster-focused stat split before the R10 shops."},
    {"character": "Laphicet", "stage": 2, "order": 30, "checkpoint": "Baird Marsh", "item": "Old Flyers", "category": "Paper", "rarity": 13, "reason": "Chest reward that provides a practical R13 Paper upgrade on the story route."},
    {"character": "Laphicet", "stage": 2, "order": 40, "checkpoint": "Port Zekson shop", "item": "Topaz Bag", "category": "Bags", "rarity": 14, "reason": "Shop Bag checkpoint that avoids relying on a rare drop for the next tier."},
    {"character": "Laphicet", "stage": 2, "order": 50, "checkpoint": "Zamahl Grotto / Katz routes", "item": "Ember Paper", "category": "Paper", "rarity": 17, "reason": "Late Paper route for learning a final main-game Master Skill."},
    {"character": "Laphicet", "stage": 2, "order": 60, "checkpoint": "End of main game", "item": "Adamantine Bag", "category": "Bags", "rarity": 18, "reason": "R18 Bag to close out the story progression before post-game equipment."},

    {"character": "Eizen", "stage": 3, "order": 10, "checkpoint": "Barona Catacombs", "item": "Armstrong", "category": "Bracelets", "rarity": 5, "reason": "Obtain it early, then keep it ready until Eizen joins; its Atk focus fits the Fist Bruiser phase."},
    {"character": "Eizen", "stage": 3, "order": 20, "checkpoint": "Taliesin shop", "item": "Feldspar Pendant", "category": "Pendants", "rarity": 10, "reason": "Convenient R10 Pendant upgrade when advancing from early rare drops."},
    {"character": "Eizen", "stage": 3, "order": 30, "checkpoint": "Baird Marsh", "item": "Perpetuity", "category": "Bracelets", "rarity": 13, "reason": "Rare R13 Pendant checkpoint with a useful late-story Master Skill to learn."},
    {"character": "Eizen", "stage": 3, "order": 40, "checkpoint": "Hexen Isle", "item": "Pumper-Upper", "category": "Pendants", "rarity": 13, "reason": "Chest option that can fill the same tier while farming other Master Skills."},
    {"character": "Eizen", "stage": 3, "order": 50, "checkpoint": "Mount Killaraus", "item": "Finger of God", "category": "Bracelets", "rarity": 15, "reason": "Strong R15 Pendant milestone when switching toward late-story equipment."},
    {"character": "Eizen", "stage": 3, "order": 60, "checkpoint": "Mount Killaraus", "item": "Gnome's Force", "category": "Pendants", "rarity": 17, "reason": "Final-story Pendant option for the last equipment tier."},

    {"character": "Magilou", "stage": 4, "order": 10, "checkpoint": "Brigid Ravine", "item": "Mana Earrings", "category": "Earrings", "rarity": 5, "reason": "Early Earrings with a direct Arte Attack bonus for a ranged casting set."},
    {"character": "Magilou", "stage": 4, "order": 20, "checkpoint": "Taliesin shop", "item": "Feldspar Doll", "category": "Guardians", "rarity": 10, "reason": "Straightforward R10 Guardian upgrade from the shop tier."},
    {"character": "Magilou", "stage": 4, "order": 30, "checkpoint": "Mount Killaraus", "item": "Secret Agent Doll", "category": "Guardians", "rarity": 15, "reason": "R15 Guardian target with a caster-oriented progression point."},
    {"character": "Magilou", "stage": 4, "order": 40, "checkpoint": "Empyrean’s Throne return", "item": "Leviathan Earrings", "category": "Earrings", "rarity": 15, "reason": "Late Earrings route for completing an Arte Attack-focused set."},
    {"character": "Magilou", "stage": 4, "order": 50, "checkpoint": "Zamahl Grotto / Katz routes", "item": "Twoside Doll", "category": "Guardians", "rarity": 17, "reason": "Final main-game Guardian upgrade before post-game tiers."},
    {"character": "Magilou", "stage": 4, "order": 60, "checkpoint": "End of main game", "item": "Adamantine Earrings", "category": "Earrings", "rarity": 18, "reason": "R18 Earrings to finish the main-game equipment path."},

    {"character": "Eleanor", "stage": 5, "order": 10, "checkpoint": "East Labann Tunnel", "item": "Mana Lance", "category": "Spears", "rarity": 7, "reason": "R7 Spear whose Master Skill improves equipment-learning efficiency; learn it early once Eleanor is available."},
    {"character": "Eleanor", "stage": 5, "order": 20, "checkpoint": "Perniya Cliffside", "item": "Con Fuoco", "category": "Ribbons", "rarity": 11, "reason": "Mid-story Spear milestone for an Atk-focused Martial Artes setup."},
    {"character": "Eleanor", "stage": 5, "order": 30, "checkpoint": "Tranquil Woods", "item": "Spiritoso", "category": "Ribbons", "rarity": 13, "reason": "R13 Spear choice when preparing the stronger story-area equipment tiers."},
    {"character": "Eleanor", "stage": 5, "order": 40, "checkpoint": "Earthpulse", "item": "Guandao", "category": "Spears", "rarity": 15, "reason": "Late-story Spear upgrade before the final route."},
    {"character": "Eleanor", "stage": 5, "order": 50, "checkpoint": "Earthpulse", "item": "Shimmery Shoes", "category": "Women’s Shoes", "rarity": 15, "reason": "Women’s Shoes route that supplies a useful late Footwear upgrade."},
    {"character": "Eleanor", "stage": 5, "order": 60, "checkpoint": "Innominat", "item": "Brillante", "category": "Ribbons", "rarity": 17, "reason": "Final-story Spear target for completing the main-game progression."},
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
    labels = ("Atk", "Arte Attack", "Def", "Arte Defense", "Focus")
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


def validate_recommendation_data(items: list[dict[str, Any]]) -> None:
    items_by_name = {normalized(str(item["name"])): item for item in items}
    names = set(items_by_name)
    expected_names = ("Velvet", "Rokurou", "Laphicet", "Eizen", "Magilou", "Eleanor")
    growth_names = tuple(entry.get("name") for entry in CHARACTER_GROWTH)
    if growth_names != expected_names:
        raise RuntimeError("Character growth metadata must cover the six party members in story order")

    for entry in CHARACTER_GROWTH:
        for field in ("base", "level_200"):
            values = entry.get(field)
            if not isinstance(values, list) or len(values) != 6 or not all(isinstance(value, (int, float)) and value >= 0 for value in values):
                raise RuntimeError(f"Invalid {field} growth vector for {entry.get('name')}")

    covered = {name: 0 for name in expected_names}
    for entry in RECOMMENDED_EQUIPMENT:
        character = str(entry.get("character", ""))
        if character != "All" and character not in covered:
            raise RuntimeError(f"Unknown recommendation character: {character}")
        item = items_by_name.get(normalized(str(entry.get("item", ""))))
        if item is None:
            raise RuntimeError(f"Recommended item is absent from the catalogue: {entry.get('item')}")
        if entry.get("category") != item.get("category") or entry.get("rarity") != item.get("rarity"):
            raise RuntimeError(f"Recommended equipment metadata does not match the catalogue: {entry.get('item')}")
        for field in ("checkpoint", "category", "reason"):
            if not str(entry.get(field, "")).strip():
                raise RuntimeError(f"Recommended equipment is missing {field}: {entry.get('item')}")
        if character in covered:
            covered[character] += 1

    missing = [name for name, count in covered.items() if count < 5]
    if missing:
        raise RuntimeError(f"Every party member needs a full recommended-equipment route: {missing}")


def validate(categories: list[dict[str, str]], items: list[dict[str, Any]], cards: list[dict[str, Any]]) -> None:
    validate_recommendation_data(items)
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
        "schema_version": 5,
        "complete": True,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "categories": categories,
        "items": items,
        "reference_cards": cards,
        "character_growth": list(CHARACTER_GROWTH),
        "recommended_equipment": list(RECOMMENDED_EQUIPMENT),
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
