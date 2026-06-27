#!/usr/bin/env python3
"""Validate the static guide and its committed Equipment catalogue snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from urllib.parse import parse_qs, urlsplit
from pathlib import Path
from typing import Any

EXPECTED_CATEGORY_COUNT = 18
EXPECTED_ITEM_COUNT = 350
PHASES = ("Main game", "Post-game")
EXPECTED_PHASE_CARD_COUNT = EXPECTED_CATEGORY_COUNT * len(PHASES)
REQUIRED_AI_IDS = {
    "partenza", "decisioni", "preset", "ai-velvet", "ai-rokurou", "ai-magilou",
    "ai-laphicet", "ai-eizen", "ai-eleanor", "titles", "adattamenti", "consenso", "checklist-ai",
}
REQUIRED_IDS = {
    "adesso", "personaggi", "come-leggere", "fondamenti", "statistiche", "rarity", "common-rare",
    "master-skill", "enhancement", "smith", "costi", "main-ingredient", "dismantle",
    "fluid", "ricette", "matching", "ricette-common", "ricette-rare", "alchemist", "armory",
    "farming", "farming-equipment", "common-target", "catalogo",
    "primo-set", "consigli-storia", "postgame", "massimizzazione", "random-skills", "glacite", "sovereign",
    "glossario", "checklist",
}
PUBLIC_URL = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
ALLOWED_REMOTE_IMAGE_PREFIX = "https://aselia.fandom.com/wiki/Special:Redirect/file/"
FORBIDDEN_PUBLIC_REFERENCE = re.compile("game" + "faqs|game" + "spot", re.IGNORECASE)
EXPECTED_CHARACTER_CATEGORIES = {
    "Velvet": ("Blades", "Belts", "Women’s Armor", "Rings", "Shoes", "Women’s Shoes"),
    "Rokurou": ("Short Swords", "Talismans", "Men’s Armor", "Rings", "Shoes", "Men’s Shoes"),
    "Laphicet": ("Paper", "Bags", "Men’s Armor", "Rings", "Shoes", "Men’s Shoes"),
    "Eizen": ("Bracelets", "Pendants", "Men’s Armor", "Rings", "Shoes", "Men’s Shoes"),
    "Magilou": ("Guardians", "Earrings", "Women’s Armor", "Rings", "Shoes", "Women’s Shoes"),
    "Eleanor": ("Spears", "Ribbons", "Women’s Armor", "Rings", "Shoes", "Women’s Shoes"),
}

CANONICAL_SHOE_CATEGORIES = {
    "shoes": ("Shoes", "Shoes", "All"),
    "mens-shoes": ("Men’s Shoes", "Men’s Shoes", "Rokurou · Laphicet · Eizen"),
    "womens-shoes": ("Women’s Shoes", "Women’s Shoes", "Velvet · Magilou · Eleanor"),
}

SOURCE_NOTE_GROUPS = {
    "fluoric-boots": ({"Fluoric Boots"}, 6, "rotelle"),
    "quartz-boots": ({"Quartz Boots"}, 3, "carenti"),
    "unnamed-boots": ({"Unnamed Boots"}, 6, "universali post-game"),
    "protective-hops": ({"Protective Hops"}, 3, "fuori di testa"),
    "hyper-velocity-boots": ({"Hyper Velocity Boots"}, 3, "Disgustose"),
    "kaiser-road": ({"Kaiser Road"}, 1, "bomba subatomica"),
    "mens-shoes-postgame": ({"Gigant Shoes", "Turbulent Shoes"}, 6, "Salta le prime"),
    "cast-heels": ({"Cast Heels"}, 3, "Ridicole"),
    "shimmery-shoes": ({"Shimmery Shoes"}, 3, "ancora più Focus"),
    "pegasus-wings": ({"Pegasus Wings"}, 3, "disponibilità tremenda"),
    "womens-shoes-postgame": ({"Grounded Shoes", "Queen Ellis Heels"}, 6, "assurdamente rotto"),
    "force-barrier-rings": ({"Force Ring", "Barrier Ring"}, 12, "Consiglio vivamente"),
    "offensive-rings": ({"Anthro Ring", "Plated Ring"}, 12, "quattro Rings"),
    "postgame-rings": ({"Lindworm Ring", "Unnamed Ring"}, 12, "Demon Ring"),
    "garish-pink-shirt": ({"Garish Pink Shirt"}, 3, "assenza di una statistica Defense"),
    "pure-white-quartz-garment": ({"Pure White Veil", "Quartz Garment"}, 6, "generalista"),
    "elder-garden-survivors-garb": ({"Elder Garden", "Survivor's Garb"}, 6, "non hanno molte armature"),
    "womens-armor-postgame": ({"Uprising Veil", "Empress Shield", "Unnamed Garment"}, 9, "mitica"),
    "jet-black-waistcoat": ({"Jet Black Waistcoat"}, 3, "armatura maschile universale"),
    "summertime-topaz-waistcoat": ({"Summertime Waistcoat", "Topaz Waistcoat"}, 6, "endgame"),
    "mythril-reflex-waistcoat": ({"Mythril Waistcoat", "Reflex Waistcoat"}, 6, "eccellenti per tutti e tre"),
    "mens-armor-postgame": ({"Zero Impact Waistcoat", "Mumbane", "Unnamed Vestments"}, 9, "Nulla di particolarmente impressionante"),
    "cassandra-sash": ({"Cassandra Sash"}, 1, "miglior Belt dell’inizio gioco"),
    "gloire-des-mousseux-sash": ({"Gloire des Mousseux Sash"}, 1, "più forte dell’intero gioco"),
    "helmut-schmidt-sash": ({"Helmut Schmidt Sash"}, 1, "Semplicemente stellare"),
    "belts-postgame": ({"Intrigue Sash", "Jeanne d'Arc Sash", "Unnamed Belt"}, 3, "Bottino d’oro"),
    "exquisite-charm": ({"Exquisite Charm"}, 1, "puro acciaio Rangetsu"),
    "stoic-idol": ({"Stoic Idol"}, 1, "deliziosa torta di accessorio"),
    "soothing-knife": ({"Soothing Knife"}, 1, "vero Talisman offensivo"),
    "talismans-postgame": ({"Long Life Charm", "Perfect Bulwark", "Unnamed Talisman"}, 3, "Rokurou"),
    "mars-satchel": ({"Mars Satchel"}, 1, "oggetti più frustranti"),
    "topaz-bag": ({"Topaz Bag"}, 1, "È fantastico, usalo"),
    "adamantine-bag": ({"Adamantine Bag"}, 1, "potenziamento difficile"),
    "bags-postgame": ({"Solar Satchel", "Galactic Satchel", "Unnamed Bag"}, 3, "non tutti validi"),
    "feldspar-pendant": ({"Feldspar Pendant"}, 1, "vento di distruzione"),
    "pumper-upper": ({"Pumper-Upper"}, 1, "La comodità definisce"),
    "gnomes-force": ({"Gnome's Force"}, 1, "accessorio perfetto"),
    "pendants-postgame": ({"Sylph's Invitation", "Undine's Heart", "Unnamed Pendant"}, 3, "solido come una roccia"),
    "mana-earrings": ({"Mana Earrings"}, 1, "Potere puro"),
    "leviathan-satan-earrings": ({"Leviathan Earrings", "Satan's Wrath Earrings"}, 2, "predisposizione per l’elemento Water"),
    "adamantine-earrings": ({"Adamantine Earrings"}, 1, "Le statistiche non mentono"),
    "earrings-postgame": ({"Lucifer's Pride Earrings", "Lucky Rabbit Earrings", "Unnamed Earrings"}, 3, "Lucifer’s Pride è il più forte"),
    "con-fuoco": ({"Con Fuoco"}, 1, "unico accessorio disponibile"),
    "spiritoso": ({"Spiritoso"}, 1, "miglior Ribbon"),
    "brillante": ({"Brillante"}, 1, "accessorio di utilità"),
    "ribbons-postgame": ({"Perdendosi", "Grandioso", "Unnamed Ribbon"}, 3, "tutti piuttosto validi"),
    "amphibole-blade": ({"Amphibole Blade"}, 1, "arma mono-stat"),
    "fonon-blade": ({"Fonon Blade"}, 1, "arma anti-endgame ideale"),
    "adamantine-blade": ({"Adamantine Blade"}, 1, "arma da main game più forte"),
    "blades-postgame": ({"Demon's Bane", "Dragon Slayer", "Unnamed Blade"}, 3, "inchinati davanti all’Unnamed Blade"),
    "feldspar-daggers": ({"Feldspar Daggers"}, 1, "pugnali più lineari"),
    "kurogane-daggers": ({"Kurogane Daggers"}, 1, "sorprendentemente solidi"),
    "stygian-daggers": ({"Stygian Daggers"}, 1, "arma da “pro”"),
    "short-swords-postgame": ({"Ephemeral Wings", "Lunar Tempests", "Unnamed Daggers"}, 3, "Lunar Tempests è solo materiale da mastery fooder"),
    "secret-histories": ({"Secret Histories"}, 1, "dovrebbe essere una priorità"),
    "old-flyers": ({"Old Flyers"}, 1, "armi puramente difensive"),
    "ember-paper": ({"Ember Paper"}, 1, "scelta di prim’ordine"),
    "papers-postgame": ({"Ragnarok", "Lost Parlance", "Unnamed Paper"}, 3, "questi due colossi"),
    "armstrong": ({"Armstrong"}, 1, "armi preferite"),
    "perpetuity": ({"Perpetuity"}, 1, "opzione più desiderabile"),
    "finger-of-god": ({"Finger of God"}, 1, "caster dedicato"),
    "bracelets-postgame": ({"Titan's Knuckles", "Broken Shackle", "Unnamed Bracelet"}, 3, "non sono troppo esaltanti"),
    "feldspar-doll": ({"Feldspar Doll"}, 1, "Magilou vuole davvero"),
    "secret-agent-doll": ({"Secret Agent Doll"}, 1, "arma preferita del main game"),
    "twoside-doll": ({"Twoside Doll"}, 1, "solida arma offensiva"),
    "guardians-postgame": ({"Corpore Sano", "Doppelganger", "Unnamed Guardian"}, 3, "stelle d’oro"),
    "mana-lance": ({"Mana Lance"}, 1, "arma iniziale più utile"),
    "valkyrie": ({"Valkyrie"}, 1, "armi preferite"),
    "guandao": ({"Guandao"}, 1, "paladina spear"),
    "spears-postgame": ({"Final Scepter", "Gae Bolg", "Nameless Spear"}, 3, "grandi scelte"),
}

SOURCE_NOTE_PAIRS = {
    "mens-shoes-postgame": {"Gigant Shoes", "Turbulent Shoes"},
    "womens-shoes-postgame": {"Grounded Shoes", "Queen Ellis Heels"},
    "force-barrier-rings": {"Force Ring", "Barrier Ring"},
    "offensive-rings": {"Anthro Ring", "Plated Ring"},
    "postgame-rings": {"Lindworm Ring", "Unnamed Ring"},
    "pure-white-quartz-garment": {"Pure White Veil", "Quartz Garment"},
    "elder-garden-survivors-garb": {"Elder Garden", "Survivor's Garb"},
    "summertime-topaz-waistcoat": {"Summertime Waistcoat", "Topaz Waistcoat"},
    "mythril-reflex-waistcoat": {"Mythril Waistcoat", "Reflex Waistcoat"},
}



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
        for url in PUBLIC_URL.findall(text):
            if not url.startswith(ALLOWED_REMOTE_IMAGE_PREFIX):
                fail(f"Unapproved external URL found in published file: {path.relative_to(site)}")
        if FORBIDDEN_PUBLIC_REFERENCE.search(text):
            fail(f"Forbidden source reference found in published file: {path.relative_to(site)}")


def html_ids(path: Path) -> set[str]:
    return set(re.findall(r'\bid=["\']([^"\']+)["\']', path.read_text(encoding="utf-8")))


def href_values(path: Path) -> list[str]:
    return re.findall(r'<a\s+[^>]*\bhref=["\']([^"\']+)["\']', path.read_text(encoding="utf-8"), flags=re.IGNORECASE)


def validate_local_href(href: str, source: Path, site: Path, guide_ids: set[str], ai_ids: set[str]) -> None:
    if href.startswith(("mailto:", "tel:")):
        return
    if href.startswith(("http://", "https://", "//")):
        fail(f"Published navigation must not use a remote page: {source.relative_to(site)} -> {href}")
    if href.startswith("./?"):
        fail(f"Ambiguous root link found; use ./index.html explicitly: {source.relative_to(site)} -> {href}")

    parsed = urlsplit(href)
    path = parsed.path
    fragment = parsed.fragment

    if not path:
        targets = guide_ids if source.name in {"index.html", "guide.html"} else ai_ids
        if fragment and fragment not in targets:
            fail(f"Broken in-page anchor: {source.relative_to(site)} -> #{fragment}")
        return

    if path in {"./", "index.html", "./index.html"}:
        if set(parse_qs(parsed.query)) - {"character", "category"}:
            fail(f"Unsupported guide query parameter: {source.relative_to(site)} -> {href}")
        if fragment and fragment not in guide_ids:
            fail(f"Broken guide anchor: {source.relative_to(site)} -> {href}")
        return

    if path in {"ai.html", "./ai.html"}:
        if parsed.query:
            fail(f"Unexpected query on AI page link: {source.relative_to(site)} -> {href}")
        if fragment and fragment not in ai_ids:
            fail(f"Broken AI-page anchor: {source.relative_to(site)} -> {href}")
        return

    target = (source.parent / path).resolve()
    if not target.is_file() or site.resolve() not in target.parents:
        fail(f"Broken local file link: {source.relative_to(site)} -> {href}")
    if fragment:
        target_ids = html_ids(target) if target.suffix.lower() == ".html" else set()
        if fragment not in target_ids:
            fail(f"Broken local-file anchor: {source.relative_to(site)} -> {href}")


def validate_navigation(site: Path) -> None:
    guide = site / "content" / "guide.html"
    ai = site / "ai.html"
    index = site / "index.html"
    guide_ids = html_ids(guide) | html_ids(index)
    ai_ids = html_ids(ai)

    for source in (index, guide, ai):
        for href in href_values(source):
            validate_local_href(href, source, site, guide_ids, ai_ids)


def validate_character_configuration(script: Path) -> None:
    text = script.read_text(encoding="utf-8")
    required_navigation_tokens = (
        'return `./index.html${query ? `?${query}` : ""}#catalogo`;', 
        "const aiHref = `./ai.html#ai-",
        "data-catalogue-link",
        "function scrollToGuideAnchor()",
    )
    for token in required_navigation_tokens:
        if token not in text:
            fail("Character navigation no longer has an explicit, auditable route: " + token)
    if text.count("scrollToGuideAnchor();") < 2:
        fail("Dynamic guide anchors must be handled after both initial rendering and hash changes")

    found: dict[str, tuple[str, ...]] = {}
    for match in re.finditer(r'name:\s*"([^"\\]+)".*?categories:\s*\[([^\]]*)\]', text, flags=re.DOTALL):
        name = match.group(1)
        categories = tuple(re.findall(r'"([^"]+)"', match.group(2)))
        if name in EXPECTED_CHARACTER_CATEGORIES:
            found[name] = categories

    if found != EXPECTED_CHARACTER_CATEGORIES:
        missing = sorted(set(EXPECTED_CHARACTER_CATEGORIES) - set(found))
        wrong = {
            name: {"expected": EXPECTED_CHARACTER_CATEGORIES[name], "found": found.get(name)}
            for name in EXPECTED_CHARACTER_CATEGORIES
            if found.get(name) != EXPECTED_CHARACTER_CATEGORIES[name]
        }
        fail(f"Character Equipment categories are incomplete or incorrect. Missing: {missing}; differences: {wrong}")


def validate_guide(guide: Path) -> list[str]:
    text = guide.read_text(encoding="utf-8")
    ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', text))
    missing = REQUIRED_IDS - ids
    if missing:
        fail(f"Guide is missing required anchors: {', '.join(sorted(missing))}")
    if text.count("<table") < 21:
        fail("Guide must retain at least 21 static explanatory tables alongside the runtime growth tables")
    if "catalogo-dinamico" not in text or "reference-cards-dynamic" not in text or "recommended-equipment-dynamic" not in text or "growth-table-dynamic" not in text or "character-cards-dynamic" not in text:
        fail("Guide is missing dynamic catalogue, growth, recommendation, reference-card, or character-card container")
    if "filtro anti-spoiler" not in text.lower() or "data-spoiler-stage" not in text:
        fail("Guide is missing the spoiler-safe character flow")
    if "Footwear" in text:
        fail("Guide must use the canonical Shoes, Men’s Shoes, and Women’s Shoes category labels")

    script_path = guide.parent.parent / "assets" / "site.js"
    validate_character_configuration(script_path)
    script = script_path.read_text(encoding="utf-8")
    if "Footwear" in script:
        fail("Runtime UI must use the canonical Shoes, Men’s Shoes, and Women’s Shoes category labels")
    for token in (
        "battleAdvice", "equipmentAdvice", "catalogueLink", "cataloguePendingCategory",
        "Preset AI", "Target Strong Enemies", "Wind Master", "Aqua Split", "Flame Beast", "renderRecommendedEquipment", "character.html", "renderGrowthTable", "Arte Attack",
    ):
        if token not in script:
            fail(f"Character cards are missing role-specific guidance or direct navigation: {token}")

    dossier_page = guide.parent.parent / "character.html"
    dossier_script = guide.parent.parent / "assets" / "character.js"
    if not dossier_page.exists() or not dossier_script.exists():
        fail("Dedicated character dossier page or its runtime script is missing")
    dossier = dossier_script.read_text(encoding="utf-8")
    for token in ("source_note_group", "Best in slot", "Really recommended", "Suggested", "Wind Master", "Aqua Split", "Flame Beast", "catalogo.json", "sourceTierByItem", "dossier-item-tier-badge"):
        if token not in dossier:
            fail(f"Character dossier is missing required guide content: {token}")
    if "recommendationTier(group, groups, index)" in dossier or "postgame || maxRarity" in dossier:
        fail("Character dossier must not assign Best in slot automatically from post-game status or rarity")
    if "\"Titan's Knuckles\": { key: \"bis\"" in dossier or "\"Broken Shackle\": { key: \"bis\"" in dossier or "\"Unnamed Bracelet\": { key: \"bis\"" in dossier:
        fail("Character dossier incorrectly marks the entire Eizen post-game Bracelet set as Best in slot")
    if "character-category-list a" not in (guide.parent.parent / "assets" / "site.css").read_text(encoding="utf-8"):
        fail("Character-category chips must remain direct links")
    if ("Nota della guida" not in script and "Nota della guida" not in dossier) or "Guide recommendation" in script or "Guide recommendation" in dossier:
        fail("Recommendation source-note label must be localized in Italian")

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


def validate_ai_page(page: Path, script: Path) -> None:
    text = page.read_text(encoding="utf-8")
    ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', text))
    missing = REQUIRED_AI_IDS - ids
    if missing:
        fail(f"AI page is missing required anchors: {', '.join(sorted(missing))}")
    if "./assets/ai.js" not in text:
        fail("AI page must load its dedicated behavior script")
    if "Go All Out" not in text:
        fail("AI page is missing the mandatory battle-start command")
    for token in ("Attaccante fisica", "Duellante fisico", "Mago di supporto", "Fist Bruiser", "Combattente ibrida", "./index.html?character="):
        if token not in text:
            fail(f"AI page is missing role-specific character guidance or equipment back-links: {token}")
    if "data-ai-advance-party" not in text or "ai-spoiler-filter" not in text:
        fail("AI page is missing spoiler-safe progress controls")
    if text.count("data-spoiler-stage") < 7:
        fail("AI page must protect all future-character sections and Title guidance")
    if text.count("<table") < 4:
        fail("AI page must retain its novice-oriented explanation tables")
    for skill in ("Scale Crusher", "Hell Gate", "Stone Lance", "Flame Beast", "Maelstrom", "Incapacitator"):
        if skill not in text:
            fail(f"AI page is missing a required final-preset reference: {skill}")
    anchors = re.findall(r'<a\s+[^>]*href=["\']#([^"\']+)["\']', text)
    missing_targets = sorted({anchor for anchor in anchors if anchor not in ids})
    if missing_targets:
        fail(f"AI page has broken internal anchors: {', '.join(missing_targets)}")
    if not script.is_file():
        fail("AI page behavior script is missing")
    script_text = script.read_text(encoding="utf-8")
    for token in ("tob-equipment-guide-spoiler-mode", "tob-equipment-guide-spoiler-progress", "injectVisiblePortraits", "applySpoilerMask"):
        if token not in script_text:
            fail(f"AI behavior script is missing required spoiler-state behavior: {token}")


def validate_catalogue(catalogue: Path, item_refs: list[str], allow_unbuilt: bool) -> None:
    payload: dict[str, Any] = json.loads(catalogue.read_text(encoding="utf-8"))
    if payload.get("complete") is not True:
        if allow_unbuilt:
            return
        fail("Catalogue snapshot is not complete. The deployment workflow must materialize the initial local snapshot first.")

    if payload.get("schema_version") != 6:
        fail("Catalogue schema version is not current")
    categories = payload.get("categories")
    items = payload.get("items")
    cards = payload.get("reference_cards")
    growth = payload.get("character_growth")
    recommendations = payload.get("recommended_equipment")
    integrity = payload.get("integrity")
    if not isinstance(categories, list) or len(categories) != EXPECTED_CATEGORY_COUNT:
        fail("Catalogue must contain exactly 18 categories")
    if not isinstance(items, list) or len(items) != EXPECTED_ITEM_COUNT:
        fail("Catalogue must contain exactly 350 items")
    if not isinstance(cards, list) or len(cards) != EXPECTED_PHASE_CARD_COUNT:
        fail("Catalogue must contain exactly 36 category/phase reference cards")
    if not isinstance(growth, list) or len(growth) != 6:
        fail("Catalogue must contain the six character growth records")
    if not isinstance(recommendations, list) or len(recommendations) < 70:
        fail("Catalogue must contain the complete slot-by-slot recommended-equipment routes")
    if not isinstance(integrity, dict):
        fail("Catalogue integrity metadata is missing")

    category_ids = {entry.get("id") for entry in categories}
    if len(category_ids) != EXPECTED_CATEGORY_COUNT or None in category_ids:
        fail("Catalogue category IDs are invalid")

    category_by_label = {normalized(str(entry.get("label", ""))): entry for entry in categories}
    category_by_id = {str(entry.get("id", "")): entry for entry in categories}
    for identifier, (label, slot, character) in CANONICAL_SHOE_CATEGORIES.items():
        category = category_by_id.get(identifier)
        if category is None:
            fail(f"Missing canonical shoe category: {identifier}")
        if (category.get("label"), category.get("slot"), category.get("character")) != (label, slot, character):
            fail(f"Incorrect canonical shoe category metadata for {identifier}")
    expected_shoe_slot_by_label = {
        label: slot
        for label, slot, _ in CANONICAL_SHOE_CATEGORIES.values()
    }
    for member, required_categories in EXPECTED_CHARACTER_CATEGORIES.items():
        for label in required_categories:
            category = category_by_label.get(normalized(label))
            if category is None:
                fail(f"Character-card category is absent from the catalogue: {member} -> {label}")
            users = {normalized(value) for value in re.split(r"[·,;/]", str(category.get("character", ""))) if value.strip()}
            if normalized(member) not in users and "all" not in users:
                fail(f"Character-card category has the wrong catalogue user: {member} -> {label}")

    found_ids = {entry.get("category_id") for entry in items}
    if category_ids != found_ids:
        fail("Catalogue category coverage is incomplete")

    required_pairs = {(str(category_id), phase) for category_id in category_ids for phase in PHASES}
    if len(required_pairs) != EXPECTED_PHASE_CARD_COUNT:
        fail("Catalogue category/phase matrix is inconsistent")

    found_pairs: set[tuple[str, str]] = set()
    seen: set[tuple[Any, ...]] = set()
    item_names: set[str] = set()
    items_by_name: dict[str, dict[str, Any]] = {}
    for item in items:
        stats = item.get("stats")
        stats_plus10 = item.get("stats_plus10")
        key = (item.get("category_id"), item.get("rarity"), normalized(str(item.get("name", ""))))
        if key in seen:
            fail(f"Duplicate catalogue entry: {key}")
        seen.add(key)
        item_names.add(normalized(str(item.get("name", ""))))
        items_by_name[normalized(str(item.get("name", "")))] = item
        rarity = item.get("rarity")
        if not isinstance(rarity, int) or not 1 <= rarity <= 21:
            fail(f"Invalid rarity: {item.get('name')}")
        if item.get("phase") != expected_phase(rarity):
            fail(f"Incorrect phase: {item.get('name')}")
        expected_shoe_slot = expected_shoe_slot_by_label.get(str(item.get("category", "")))
        if expected_shoe_slot and item.get("slot") != expected_shoe_slot:
            fail(f"Incorrect canonical shoe category metadata on item: {item.get('name')}")
        found_pairs.add((str(item.get("category_id")), str(item.get("phase"))))
        if not isinstance(stats, list) or len(stats) != 5 or not all(isinstance(value, int) and value >= 0 for value in stats):
            fail(f"Invalid base stats: {item.get('name')}")
        if stats_plus10 != plus_ten(stats):
            fail(f"Invalid +10 stats: {item.get('name')}")
        for field in ("name", "max_name", "master_skill", "enhancement_bonus", "main_ingredient", "rare_drop", "source_kind", "acquisition"):
            value = str(item.get(field, "")).strip()
            if not value or value == "—":
                fail(f"Missing {field}: {item.get('name')}")
            if PUBLIC_URL.search(value) or FORBIDDEN_PUBLIC_REFERENCE.search(value):
                fail(f"Forbidden content in {field}: {item.get('name')}")

    if found_pairs != required_pairs:
        missing = sorted(required_pairs - found_pairs)
        unexpected = sorted(found_pairs - required_pairs)
        fail(f"Catalogue category/phase coverage is incomplete. Missing: {missing}; unexpected: {unexpected}")

    expected_growth = ("Velvet", "Rokurou", "Laphicet", "Eizen", "Magilou", "Eleanor")
    if tuple(entry.get("name") for entry in growth) != expected_growth:
        fail("Character growth metadata must be in party/story order")
    for entry in growth:
        for field in ("base", "level_200"):
            values = entry.get(field)
            if not isinstance(values, list) or len(values) != 6 or not all(isinstance(value, (int, float)) and value >= 0 for value in values):
                fail(f"Invalid growth vector for {entry.get('name')}: {field}")

    recommendation_counts = {name: 0 for name in expected_growth}
    for entry in recommendations:
        character = entry.get("character")
        item = normalized(str(entry.get("item", "")))
        if character != "All" and character not in recommendation_counts:
            fail(f"Unknown recommendation character: {character}")
        catalogue_item = items_by_name.get(item)
        if catalogue_item is None:
            fail(f"Recommended equipment is absent from the catalogue: {entry.get('item')}")
        if entry.get("category") != catalogue_item.get("category") or entry.get("rarity") != catalogue_item.get("rarity"):
            fail(f"Recommended equipment metadata does not match the catalogue: {entry.get('item')}")
        for field in ("slot", "checkpoint", "category", "source_note_group"):
            if not str(entry.get(field, "")).strip():
                fail(f"Recommended equipment is missing {field}: {entry.get('item')}")
        if "reason" in entry:
            fail(f"Published recommendations must not contain generated commentary: {entry.get('item')}")
        if "source_note" in entry and not str(entry.get("source_note", "")).strip():
            fail(f"Source note cannot be empty: {entry.get('item')}")
        if entry.get("slot") not in {"Weapon", "Accessory", "Armor", "Rings", "Shoes"}:
            fail(f"Recommendation has an invalid logical slot: {entry.get('item')}")
        if "Footwear" in str(entry.get("source_note", "")):
            fail(f"Recommendation source note uses a non-canonical shoe category label: {entry.get('item')}")
        if character in recommendation_counts:
            recommendation_counts[character] += 1

    required_slots = {"Weapon", "Accessory", "Armor", "Rings", "Shoes"}
    for name in expected_growth:
        personal = [entry for entry in recommendations if entry.get("character") == name]
        missing_slots = sorted(required_slots - {str(entry.get("slot", "")) for entry in personal})
        if missing_slots:
            fail(f"Recommended equipment is missing logical slot coverage for {name}: {', '.join(missing_slots)}")
        if len(personal) < 10:
            fail(f"Recommended equipment route is too short for {name}")

    missing_routes = [name for name, count in recommendation_counts.items() if count < 10]
    if missing_routes:
        fail(f"Recommended-equipment route is incomplete: {', '.join(missing_routes)}")

    source_noted = {str(entry.get("item")) for entry in recommendations if str(entry.get("source_note", "")).strip()}
    expected_source_notes = set().union(*(items for items, _, _ in SOURCE_NOTE_GROUPS.values()))
    missing_source_notes = sorted(expected_source_notes - source_noted)
    if missing_source_notes:
        fail(f"Expected source-note recommendations are missing: {', '.join(missing_source_notes)}")

    for group, (expected_items, expected_count, italian_marker) in SOURCE_NOTE_GROUPS.items():
        grouped_entries = [entry for entry in recommendations if entry.get("source_note_group") == group]
        if len(grouped_entries) != expected_count:
            fail(f"Source-note group has the wrong entry count: {group}")
        if {str(entry.get("item")) for entry in grouped_entries} != expected_items:
            fail(f"Source-note group is incomplete: {group}")
        notes = {str(entry.get("source_note", "")).strip() for entry in grouped_entries}
        if len(notes) != 1 or not next(iter(notes), ""):
            fail(f"Source-note group must publish one shared note: {group}")
        note_text = next(iter(notes))
        if italian_marker.lower() not in note_text.lower():
            fail(f"Source-note group is not using the Italian translation: {group}")

    for group, expected_items in SOURCE_NOTE_PAIRS.items():
        for character in expected_growth:
            pair_entries = [entry for entry in recommendations if entry.get("character") == character and entry.get("source_note_group") == group]
            if group in {"mens-shoes-postgame", "jet-black-waistcoat", "summertime-topaz-waistcoat", "mythril-reflex-waistcoat", "mens-armor-postgame"} and character not in {"Rokurou", "Laphicet", "Eizen"}:
                continue
            if group in {"womens-shoes-postgame", "garish-pink-shirt", "pure-white-quartz-garment", "elder-garden-survivors-garb", "womens-armor-postgame"} and character not in {"Velvet", "Magilou", "Eleanor"}:
                continue
            if {entry.get("item") for entry in pair_entries} != expected_items:
                fail(f"Source-note pair is incomplete for {character}: {group}")

    for character in ("Velvet", "Magilou", "Eleanor"):
        pair_entries = [entry for entry in recommendations if entry.get("character") == character and entry.get("source_note_group") == "womens-shoes-postgame"]
        if {entry.get("item") for entry in pair_entries} != {"Grounded Shoes", "Queen Ellis Heels"}:
            fail(f"Post-game Women’s Shoes pair is incomplete for {character}")
    for character in ("Rokurou", "Laphicet", "Eizen"):
        pair_entries = [entry for entry in recommendations if entry.get("character") == character and entry.get("source_note_group") == "mens-shoes-postgame"]
        if {entry.get("item") for entry in pair_entries} != {"Gigant Shoes", "Turbulent Shoes"}:
            fail(f"Post-game Men’s Shoes pair is incomplete for {character}")

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
    validate_navigation(site)
    item_refs = validate_guide(site / "content" / "guide.html")
    validate_ai_page(site / "ai.html", site / "assets" / "ai.js")
    validate_catalogue(site / "content" / "catalogo.json", item_refs, args.allow_unbuilt)
    print("Static-site validation passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
