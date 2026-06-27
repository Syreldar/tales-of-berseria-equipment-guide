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
    Category("shoes", "Shoes", "Shoes", "All", "ToB - Equipment (Shoes)"),
    Category("mens-shoes", "Men’s Shoes", "Men’s Shoes", "Rokurou · Laphicet · Eizen", "ToB - Equipment (Men's Shoes)"),
    Category("womens-shoes", "Women’s Shoes", "Women’s Shoes", "Velvet · Magilou · Eleanor", "ToB - Equipment (Women's Shoes)"),
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
    {'character': 'Velvet', 'stage': 0, 'slot': 'Weapon', 'order': 10, 'checkpoint': 'Early game · Yseult shop', 'item': 'Amphibole Blade', 'category': 'Blades', 'rarity': 8, 'reason': 'A focused physical weapon with a broadly useful non-elemental boost. Its Common rarity keeps enhancement practical while it remains competitive for a long stretch.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Weapon', 'order': 20, 'checkpoint': 'Late game · Hexen Isle', 'item': 'Fonon Blade', 'category': 'Blades', 'rarity': 15, 'reason': 'Trade some raw Attack for Focus and a strong anti-Armored matchup. It is especially valuable as the final dungeons fill with Armored enemies.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Accessory', 'order': 110, 'checkpoint': 'Early-mid game · Warg Forest', 'item': 'Cassandra Sash', 'category': 'Belts', 'rarity': 7, 'reason': 'A high Arte Attack Belt that also strengthens Velvet’s fire-oriented attacks. Excellent while building an early Hidden Arte setup, before later belts overtake it.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Accessory', 'order': 120, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Gloire des Mousseux Sash', 'category': 'Belts', 'rarity': 15, 'reason': 'The main-game Belt for maximum Arte Attack. It arrives late, but its raw scaling makes it a major offensive upgrade when available.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Accessory', 'order': 130, 'checkpoint': 'Final dungeon · Innominat / shop level 10', 'item': 'Helmut Schmidt Sash', 'category': 'Belts', 'rarity': 17, 'reason': 'A final-dungeon Focus and Break Soul option. It supports Soul retention and recovery without abandoning Velvet’s Arte Attack completely.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Armor', 'order': 210, 'checkpoint': 'Early-mid game · Burnack Plateau', 'item': 'Garish Pink Shirt', 'category': 'Women’s Armor', 'rarity': 7, 'reason': 'An aggressive Women’s Armor choice: Attack and Focus are substantial, while its healing effects reward an absorb-HP arte route instead of direct Defense.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Armor', 'order': 220, 'checkpoint': 'Mid game · Aldina Plains', 'item': 'Pure White Veil', 'category': 'Women’s Armor', 'rarity': 11, 'reason': 'Use this when the set needs straightforward physical durability. It is the highest-Defense main-game Women’s Armor and a reliable generalist fallback.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Rings', 'order': 310, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Force Ring', 'category': 'Rings', 'rarity': 10, 'reason': 'A strong Arte Defense milestone that stays efficient well past its rarity. Keep one for magical encounters and for learning Ring skills.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Rings', 'order': 320, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Barrier Ring', 'category': 'Rings', 'rarity': 15, 'reason': 'The upgraded Arte Defense staple. It is the cleanest answer when incoming arte damage matters more than niche offensive ring bonuses.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'source_note_group': 'fluoric-boots', 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Early-mid game · Fens of Nog', 'item': 'Cast Heels', 'category': 'Women’s Shoes', 'rarity': 7, 'source_note_group': 'cast-heels', 'reason': 'A standout Women’s Shoes pickup: very high Focus plus BG gain and extra maximum BG. It is worth targeting even if later footwear has higher rarity.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Late game · Earthpulse', 'item': 'Shimmery Shoes', 'category': 'Women’s Shoes', 'rarity': 15, 'source_note_group': 'shimmery-shoes', 'reason': 'A higher-Focus alternative with SG economy. Use it when Cast Heels are unavailable or when weak-point combos make the SG return more useful.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Weapon', 'order': 10, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Feldspar Daggers', 'category': 'Short Swords', 'rarity': 10, 'reason': 'High Attack, accessible Common materials, and a Fatigue trigger that repairs Rokurou’s weak Focus. The default straightforward damage choice.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Weapon', 'order': 20, 'checkpoint': 'Story reward', 'item': 'Kurogane Daggers', 'category': 'Short Swords', 'rarity': 15, 'reason': 'A balanced story weapon with useful fire coverage and excellent Break Soul recovery. Its extra Arte Attack helps Hidden Artes more than the stat line first suggests.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Weapon', 'order': 30, 'checkpoint': 'Final dungeon · Innominat', 'item': 'Stygian Daggers', 'category': 'Short Swords', 'rarity': 17, 'reason': 'A specialist Focus weapon for deep combo play. It turns Rokurou’s usual weakness into a resource, but is only worth prioritizing for an active Rokurou build.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Accessory', 'order': 110, 'checkpoint': 'Mid game · Titania', 'item': 'Exquisite Charm', 'category': 'Talismans', 'rarity': 9, 'reason': 'Pairs a large Arte Attack boost with a huge Defense payoff after Slow. Rokurou can trigger it naturally through Slow-inflicting combo resets.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Accessory', 'order': 120, 'checkpoint': 'Late game · Hexen Isle', 'item': 'Stoic Idol', 'category': 'Talismans', 'rarity': 13, 'reason': 'A defensive accessory for caster-heavy areas. The large Arte Defense gain and healing synergy give Rokurou a safer answer to enemy artes.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Armor', 'order': 210, 'checkpoint': 'Early-mid game · Warg Forest', 'item': 'Jet Black Waistcoat', 'category': 'Men’s Armor', 'rarity': 7, 'reason': 'A universal Men’s Armor pick against the predominantly non-elemental damage of the early and middle game. Strong before the later specialized choices arrive.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Armor', 'order': 220, 'checkpoint': 'Late game · Baird Marsh', 'item': 'Summertime Waistcoat', 'category': 'Men’s Armor', 'rarity': 13, 'reason': 'An endgame-viable Armor with a meaningful Attack component. It is especially well suited to Rokurou’s physical pressure.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Rings', 'order': 310, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Force Ring', 'category': 'Rings', 'rarity': 10, 'reason': 'A strong Arte Defense milestone that stays efficient well past its rarity. Keep one for magical encounters and for learning Ring skills.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Rings', 'order': 320, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Barrier Ring', 'category': 'Rings', 'rarity': 15, 'reason': 'The upgraded Arte Defense staple. It is the cleanest answer when incoming arte damage matters more than niche offensive ring bonuses.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'source_note_group': 'fluoric-boots', 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Mid game · Hellawes return', 'item': 'Quartz Boots', 'category': 'Shoes', 'rarity': 12, 'source_note_group': 'quartz-boots', 'reason': 'A universal Focus pair with stun-oriented effects. Easy Common materials make it a practical backup for male physical builds.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Mid game · Faldies Ruins', 'item': 'Protective Hops', 'category': 'Men’s Shoes', 'rarity': 11, 'source_note_group': 'protective-hops', 'reason': 'Choose this defensive Men’s Shoes option when survival and faster item use matter more than Focus. It is a deliberate utility alternative, not a damage upgrade.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Shoes', 'order': 440, 'checkpoint': 'Late game · Gaiburk Icefield', 'item': 'Hyper Velocity Boots', 'category': 'Men’s Shoes', 'rarity': 15, 'source_note_group': 'hyper-velocity-boots', 'reason': 'A late Focus spike with stronger status pressure and a stun-finishing bonus. Excellent when the party can repeatedly create Stunned targets.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Weapon', 'order': 10, 'checkpoint': 'Mid game · Manann Reef', 'item': 'Secret Histories', 'category': 'Paper', 'rarity': 9, 'reason': 'The key offensive Paper for a caster route: it raises Focus, boosts almost all of Laphicet’s non-elemental damage, and shortens most of his casts.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Weapon', 'order': 20, 'checkpoint': 'Late game · Baird Marsh', 'item': 'Old Flyers', 'category': 'Paper', 'rarity': 13, 'reason': 'A defensive Paper for support-focused play. Select it for survivability and Break Soul support rather than for direct spell damage.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Weapon', 'order': 30, 'checkpoint': 'Final stretch · Zamahl Grotto', 'item': 'Ember Paper', 'category': 'Paper', 'rarity': 17, 'reason': 'The strongest campaign Paper for Malak Arte damage. Its Focus lead makes it preferable for endgame casting even though Laphicet cannot exploit its Burn enhancement bonus.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Accessory', 'order': 110, 'checkpoint': 'Early-mid game · Vester Tunnels', 'item': 'Mars Satchel', 'category': 'Bags', 'rarity': 7, 'reason': 'An unusually early Arte Attack Bag with stats that remain useful for a long time. Its Burn payoff is unavailable to Laphicet, so treat it as raw caster value.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Accessory', 'order': 120, 'checkpoint': 'Late game · Port Zekson shop', 'item': 'Topaz Bag', 'category': 'Bags', 'rarity': 14, 'reason': 'A cleaner late-game replacement: more Arte Attack, extra toughness, Common materials, and an additional percentage boost to his core stat.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Armor', 'order': 210, 'checkpoint': 'Early-mid game · Warg Forest', 'item': 'Jet Black Waistcoat', 'category': 'Men’s Armor', 'rarity': 7, 'reason': 'A universal Men’s Armor pick against the predominantly non-elemental damage of the early and middle game. Strong before the later specialized choices arrive.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Armor', 'order': 220, 'checkpoint': 'Late game · Hellawes return', 'item': 'Topaz Waistcoat', 'category': 'Men’s Armor', 'rarity': 14, 'reason': 'A common-material Armor that gives Laphicet useful Arte Attack alongside Defense. Its combat skill is modest, but the stat split fits a caster better than the physical option.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Rings', 'order': 310, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Force Ring', 'category': 'Rings', 'rarity': 10, 'reason': 'A strong Arte Defense milestone that stays efficient well past its rarity. Keep one for magical encounters and for learning Ring skills.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Rings', 'order': 320, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Barrier Ring', 'category': 'Rings', 'rarity': 15, 'reason': 'The upgraded Arte Defense staple. It is the cleanest answer when incoming arte damage matters more than niche offensive ring bonuses.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'source_note_group': 'fluoric-boots', 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Mid game · Hellawes return', 'item': 'Quartz Boots', 'category': 'Shoes', 'rarity': 12, 'source_note_group': 'quartz-boots', 'reason': 'A universal Focus pair with stun-oriented effects. Easy Common materials make it a practical backup for male physical builds.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Mid game · Faldies Ruins', 'item': 'Protective Hops', 'category': 'Men’s Shoes', 'rarity': 11, 'source_note_group': 'protective-hops', 'reason': 'Choose this defensive Men’s Shoes option when survival and faster item use matter more than Focus. It is a deliberate utility alternative, not a damage upgrade.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Shoes', 'order': 440, 'checkpoint': 'Late game · Gaiburk Icefield', 'item': 'Hyper Velocity Boots', 'category': 'Men’s Shoes', 'rarity': 15, 'source_note_group': 'hyper-velocity-boots', 'reason': 'A late Focus spike with stronger status pressure and a stun-finishing bonus. Excellent when the party can repeatedly create Stunned targets.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Weapon', 'order': 10, 'checkpoint': 'Early game · Barona Catacombs', 'item': 'Armstrong', 'category': 'Bracelets', 'rarity': 5, 'reason': 'An early Attack-focused Bracelet that stays useful through the whole campaign. Its purpose is simple and exactly matches Eizen’s preferred physical stat.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Weapon', 'order': 20, 'checkpoint': 'Late game · Baird Marsh', 'item': 'Perpetuity', 'category': 'Bracelets', 'rarity': 13, 'reason': 'A Focus-heavy alternative that still retains workable Attack. Its Break Soul effects give the extra Focus a concrete payoff instead of making it a passive stat pile.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Accessory', 'order': 110, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Feldspar Pendant', 'category': 'Pendants', 'rarity': 10, 'reason': 'A dependable Arte Attack and Focus Pendant whose Fatigue bonus is easy for Eizen to trigger with several of his artes.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Accessory', 'order': 120, 'checkpoint': 'Late game · Hexen Isle / shop level 8', 'item': 'Pumper-Upper', 'category': 'Pendants', 'rarity': 13, 'reason': 'A convenience-focused Pendant with very high Arte Attack and faster equipment learning. It is easy to obtain when its skill still has time to matter.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Armor', 'order': 210, 'checkpoint': 'Early-mid game · Warg Forest', 'item': 'Jet Black Waistcoat', 'category': 'Men’s Armor', 'rarity': 7, 'reason': 'A universal Men’s Armor pick against the predominantly non-elemental damage of the early and middle game. Strong before the later specialized choices arrive.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Armor', 'order': 220, 'checkpoint': 'Late game · Baird Marsh', 'item': 'Summertime Waistcoat', 'category': 'Men’s Armor', 'rarity': 13, 'reason': 'A top physical Armor choice for Eizen: it combines Defense with Attack and remains worthwhile through the end of the main campaign.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Armor', 'order': 230, 'checkpoint': 'Late game · Hellawes return', 'item': 'Topaz Waistcoat', 'category': 'Men’s Armor', 'rarity': 14, 'reason': 'A second late-game Armor route for a more mixed offensive setup. It trades physical emphasis for Arte Attack and is easier to enhance as a Common piece.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Rings', 'order': 310, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Force Ring', 'category': 'Rings', 'rarity': 10, 'reason': 'A strong Arte Defense milestone that stays efficient well past its rarity. Keep one for magical encounters and for learning Ring skills.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Rings', 'order': 320, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Barrier Ring', 'category': 'Rings', 'rarity': 15, 'reason': 'The upgraded Arte Defense staple. It is the cleanest answer when incoming arte damage matters more than niche offensive ring bonuses.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'source_note_group': 'fluoric-boots', 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Mid game · Hellawes return', 'item': 'Quartz Boots', 'category': 'Shoes', 'rarity': 12, 'source_note_group': 'quartz-boots', 'reason': 'A universal Focus pair with stun-oriented effects. Easy Common materials make it a practical backup for male physical builds.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Mid game · Faldies Ruins', 'item': 'Protective Hops', 'category': 'Men’s Shoes', 'rarity': 11, 'source_note_group': 'protective-hops', 'reason': 'Choose this defensive Men’s Shoes option when survival and faster item use matter more than Focus. It is a deliberate utility alternative, not a damage upgrade.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Shoes', 'order': 440, 'checkpoint': 'Late game · Gaiburk Icefield', 'item': 'Hyper Velocity Boots', 'category': 'Men’s Shoes', 'rarity': 15, 'source_note_group': 'hyper-velocity-boots', 'reason': 'A late Focus spike with stronger status pressure and a stun-finishing bonus. Excellent when the party can repeatedly create Stunned targets.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Weapon', 'order': 10, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Feldspar Doll', 'category': 'Guardians', 'rarity': 10, 'reason': 'A Common Guardian for a Hidden Arte-oriented Magilou. It has the highest Focus among the common options while retaining useful Attack.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Weapon', 'order': 20, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Secret Agent Doll', 'category': 'Guardians', 'rarity': 15, 'reason': 'A high-end Guardian with strong mixed stats, fire power, and faster fire casting. Its only real drawback is arriving near the end of the campaign.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Accessory', 'order': 110, 'checkpoint': 'Early-mid game · Brigid Ravine', 'item': 'Mana Earrings', 'category': 'Earrings', 'rarity': 5, 'reason': 'A long-lasting Arte Attack staple. It appears early and remains Magilou’s strongest pure Arte Attack accessory until very late in the story.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Accessory', 'order': 120, 'checkpoint': 'Late game · Hexen Isle', 'item': "Satan's Wrath Earrings", 'category': 'Earrings', 'rarity': 13, 'reason': 'A large direct Arte Attack upgrade with a percentage multiplier. Pick it when raw spell power matters more than elemental specialization.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Accessory', 'order': 130, 'checkpoint': 'Late game · Empyrean’s Throne return', 'item': 'Leviathan Earrings', 'category': 'Earrings', 'rarity': 15, 'reason': 'A Water-focused caster option with extra Focus and faster Water casting. It matches Magilou’s Water bias and improves an important healing arte.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Armor', 'order': 210, 'checkpoint': 'Mid game · Hellawes return', 'item': 'Quartz Garment', 'category': 'Women’s Armor', 'rarity': 12, 'reason': 'An easier-to-enhance Women’s Armor that adds useful Arte Attack while still improving Defense. It is the offensive alternative to a pure-defense set.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Armor', 'order': 220, 'checkpoint': 'Final dungeon · Innominat', 'item': "Survivor's Garb", 'category': 'Women’s Armor', 'rarity': 17, 'reason': 'A late hybrid Armor that turns Focus and healing effects into practical durability. Prefer it when Magilou needs to keep casting under pressure.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Rings', 'order': 310, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Force Ring', 'category': 'Rings', 'rarity': 10, 'reason': 'A strong Arte Defense milestone that stays efficient well past its rarity. Keep one for magical encounters and for learning Ring skills.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Rings', 'order': 320, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Barrier Ring', 'category': 'Rings', 'rarity': 15, 'reason': 'The upgraded Arte Defense staple. It is the cleanest answer when incoming arte damage matters more than niche offensive ring bonuses.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'source_note_group': 'fluoric-boots', 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Early-mid game · Fens of Nog', 'item': 'Cast Heels', 'category': 'Women’s Shoes', 'rarity': 7, 'source_note_group': 'cast-heels', 'reason': 'A standout Women’s Shoes pickup: very high Focus plus BG gain and extra maximum BG. It is worth targeting even if later footwear has higher rarity.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Late game · Earthpulse', 'item': 'Shimmery Shoes', 'category': 'Women’s Shoes', 'rarity': 15, 'source_note_group': 'shimmery-shoes', 'reason': 'A higher-Focus alternative with SG economy. Use it when Cast Heels are unavailable or when weak-point combos make the SG return more useful.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Weapon', 'order': 10, 'checkpoint': 'Recruitment · East Laban Tunnel', 'item': 'Mana Lance', 'category': 'Spears', 'rarity': 7, 'reason': 'An exceptional starting Spear with solid long-term stats, faster equipment learning, and improved drops. Learn it early as soon as Eleanor becomes available.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Weapon', 'order': 20, 'checkpoint': 'Late game · Baird Marsh', 'item': 'Valkyrie', 'category': 'Spears', 'rarity': 13, 'reason': 'The main-game Spear for a balanced playstyle: it improves both Attack and Arte Attack while reinforcing Break Soul use.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Weapon', 'order': 30, 'checkpoint': 'Late game · Earthpulse', 'item': 'Guandao', 'category': 'Spears', 'rarity': 15, 'reason': 'A physical Spear upgrade with strong enemy-defeat recovery. It is a good choice when Eleanor is staying close and trading hits.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Accessory', 'order': 110, 'checkpoint': 'Mid game · Perniya Cliffside', 'item': 'Con Fuoco', 'category': 'Ribbons', 'rarity': 11, 'reason': 'One of the few main-game accessories that meaningfully improves both Attack and Arte Attack. Eleanor can trigger its Burn follow-up naturally with her fire artes.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Accessory', 'order': 120, 'checkpoint': 'Late game · Tranquil Woods', 'item': 'Spiritoso', 'category': 'Ribbons', 'rarity': 13, 'reason': 'A clean Arte Attack Ribbon with a multiplicative bonus. Use it when the build needs reliable spell scaling rather than a situational status effect.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Accessory', 'order': 130, 'checkpoint': 'Final dungeon · Innominat', 'item': 'Brillante', 'category': 'Ribbons', 'rarity': 17, 'reason': 'A final-story Ribbon with fast equipment learning and stronger drop rates. Great to learn before the campaign closes, even if another Ribbon is equipped for damage.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Armor', 'order': 210, 'checkpoint': 'Early-mid game · Burnack Plateau', 'item': 'Garish Pink Shirt', 'category': 'Women’s Armor', 'rarity': 7, 'reason': 'An aggressive Women’s Armor choice: Attack and Focus are substantial, while its healing effects reward an absorb-HP arte route instead of direct Defense.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Armor', 'order': 220, 'checkpoint': 'Final dungeon · Innominat', 'item': "Survivor's Garb", 'category': 'Women’s Armor', 'rarity': 17, 'reason': 'A late hybrid Armor that turns Focus and healing effects into practical durability. Prefer it when Eleanor needs to maintain pressure without losing safety.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Rings', 'order': 310, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Force Ring', 'category': 'Rings', 'rarity': 10, 'reason': 'A strong Arte Defense milestone that stays efficient well past its rarity. Keep one for magical encounters and for learning Ring skills.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Rings', 'order': 320, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Barrier Ring', 'category': 'Rings', 'rarity': 15, 'reason': 'The upgraded Arte Defense staple. It is the cleanest answer when incoming arte damage matters more than niche offensive ring bonuses.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'source_note_group': 'fluoric-boots', 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Early-mid game · Fens of Nog', 'item': 'Cast Heels', 'category': 'Women’s Shoes', 'rarity': 7, 'source_note_group': 'cast-heels', 'reason': 'A standout Women’s Shoes pickup: very high Focus plus BG gain and extra maximum BG. It is worth targeting even if later footwear has higher rarity.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Late game · Earthpulse', 'item': 'Shimmery Shoes', 'category': 'Women’s Shoes', 'rarity': 15, 'source_note_group': 'shimmery-shoes', 'reason': 'A higher-Focus alternative with SG economy. Use it when Cast Heels are unavailable or when weak-point combos make the SG return more useful.'},
)

SOURCE_NOTE_ITEM_GROUPS: dict[str, str] = {
    "Force Ring": "force-barrier-rings",
    "Barrier Ring": "force-barrier-rings",
    "Pure White Veil": "pure-white-quartz-garment",
    "Quartz Garment": "pure-white-quartz-garment",
    "Elder Garden": "elder-garden-survivors-garb",
    "Survivor's Garb": "elder-garden-survivors-garb",
    "Uprising Veil": "womens-armor-postgame",
    "Empress Shield": "womens-armor-postgame",
    "Unnamed Garment": "womens-armor-postgame",
    "Summertime Waistcoat": "summertime-topaz-waistcoat",
    "Topaz Waistcoat": "summertime-topaz-waistcoat",
    "Mythril Waistcoat": "mythril-reflex-waistcoat",
    "Reflex Waistcoat": "mythril-reflex-waistcoat",
    "Zero Impact Waistcoat": "mens-armor-postgame",
    "Mumbane": "mens-armor-postgame",
    "Unnamed Vestments": "mens-armor-postgame",
}

SOURCE_NOTE_TEXT: dict[str, str] = {
    "fluoric-boots": "Sono un po’ come le rotelle all’inizio del gioco, ma fanno benissimo il loro lavoro. Le statistiche sono esattamente dove devono essere e entrambe le abilità rendono più facile mantenere alto il BG per le Mystic Artes. Sostituiscile quando trovi qualcosa di meglio, ma non esitare a investirci durante le prime ore.",
    "quartz-boots": "I ragazzi sono un po’ carenti di Shoes che aumentano Attack, ma per fortuna questo paio di Boots li copre. Focus più abilità che migliorano i disturbi di stato è sempre una combinazione vincente, e questo tipo è la variante più estrema che incontrerai. Visto quanto è facile ottenere Quartz, non c’è motivo per non tenerne un paio di scorta. Dopotutto, cosa c’è che non va?",
    "unnamed-boots": "Sono l’unico paio di Shoes universali post-game. Sono anche una ricompensa del negozio, anche se probabilmente non li vedrai prima del post-game. La Master Skill e l’Enhancement Bonus non sono granché, ma il Focus è così alto che non ti importerà. Discreti, ma senza particolari qualità.",
    "protective-hops": "Se per qualche motivo non ti interessa Focus e dai priorità alla difesa (come una persona fuori di testa), buone notizie! C’è un paio di Shoes fatto apposta per te. Anche qui, più o meno sono stampelle sia come statistiche sia come abilità (tempo di utilizzo oggetti più rapido), ma non esisterebbero se non servissero a qualcuno. Detto questo, se ti servono Shoes più offensive nelle prime fasi, le Resistance Shoes sono una fantastica alternativa con una Master Skill follissima.",
    "hyper-velocity-boots": "Disgustose. Focus altissimo? Fatto. Una Master Skill che aumenta un disturbo di stato? Fatto. Enhancement Bonus con una probabilità del 2% di insta-kill? Ma stiamo scherzando?! Certo, le ottieni solo nel late game, ma restano comunque 3–4 dungeon da devastare. Goditi la follia.",
    "kaiser-road": "Puoi rinunciare del tutto a Focus anche per l’offesa. Non lo consiglierei a nessuno tranne che a Eizen. Tuttavia, su Eizen queste Shoes sono come una bomba subatomica nei suoi piedi. Kaiser Road è praticamente una seconda arma in termini di statistiche e, con una Master Skill e un Enhancement Bonus che incoraggiano ad attaccare come un berserker impazzito, Eizen può farsi strada a calci in qualunque cosa con immunità per 10 secondi.",
    "mens-shoes-postgame": "Le Gigant Shoes sono per tankare, mentre le Turbulent Shoes servono a decimare i nemici, attirarli su di sé e ascoltare le lamentazioni delle loro donne. Salta le prime e abusa delle seconde.",
    "cast-heels": "Ridicole. Focus pazzesco con due delle abilità più rotte del gioco… e sono disponibili più o meno dal traguardo delle 10 ore. Chi ha bilanciato questo gioco???",
    "shimmery-shoes": "Le Shimmery Shoes hanno ancora più Focus delle Cast Heels, ma la loro Master Skill non è altrettanto valida. Se ti mancano le Cast Heels, o non hai avuto voglia di farmarne tre, queste Shoes possono portarti fino all’endgame.",
    "pegasus-wings": "Cast Heels con Arte Defense e una disponibilità tremenda. No, davvero: sono esattamente questo. Le Pegasus Wings hanno leggermente meno Focus delle Cast Heels, molta più Arte Defense e sono disponibili solo nel dungeon finale; le Cast Heels sono COSÌ ridicole. Se in qualche modo hai resistito alla tentazione del potere assoluto, puoi assaggiarne un po’ poco prima di finire il gioco.",
    "womens-shoes-postgame": "Un paio di Shoes per Velvet ed Eleanor, l’altro per Magilou, o Eleanor, suppongo. Le Grounded Shoes rendono \"LOOK A SHOOTING STAR!\" assurdamente rotto con il Ventite di Guardbreaker. È praticamente tutto quello che hanno da offrire, ma serve davvero che facciano altro? Nel frattempo, le Queen Ellis Heels portano una quantità ridicola di Focus, con un contorno di Attack. Grazie al loro Enhancement Bonus, le Queen Ellis Heels superano perfino le Unnamed Boots in Focus: sulla carta sono quindi i tacchi definitivi, i tacchi della \"regina\", per così dire, per Velvet ed Eleanor. Prendi entrambi i tacchi e macina l’endgame sotto quegli… sensuali… ehm, sì.",
    "force-barrier-rings": "Consiglio vivamente di procurarti e tenere entrambi questi Rings, nell’eventualità in cui tu riesca a padroneggiare tutte le abilità disponibili della categoria. A livello di statistiche, offrono i migliori bonus ad Arte Defense rispetto a qualsiasi cosa fino a cinque livelli di rarità sopra di loro e, dato che le statistiche sono tutto ciò che conta, sono sempre i migliori Rings non appena diventano disponibili.",
    "offensive-rings": "Esistono soltanto quattro Rings con bonus offensivi consistenti: questi due e le rispettive varianti minori, Animalia Ring per Attack e Shell Ring per Arte Attack. Questi due sono stati messi in evidenza rispetto agli equivalenti disponibili prima perché hanno Master Skill più utili. I Golem sono tutti Armored e infliggono danni enormi, mentre tutti i Wraith sono Demi-humans e hanno potenti magie ad area: sono entrambi nemici più importanti da rendere banali rispetto a Beasts e Crustaceans, che sono perlopiù ridicolmente facili.",
    "postgame-rings": "Usa il Lindworm Ring per le sue statistiche utili oppure l’Unnamed Ring per la sua disgustosamente potente coppia di abilità. Ignora il Demon Ring: è completamente surclassato sia dal Barrier Ring sia dall’Unnamed Ring.",
    "garish-pink-shirt": "Nonostante l’assenza di una statistica Defense, la Garish Pink Shirt è davvero notevole e resta utilizzabile per tutto il gioco principale con Velvet ed Eleanor; nel post-game viene superata dalla Uprising Veil. I bonus ad Attack e Focus sono entrambi sostanziosi e tutte e due le sue abilità migliorano la solidità di chi la indossa, anche se in modo indiretto. Tieni pronto un set di combo che assorbe HP e non avrai problemi.",
    "pure-white-quartz-garment": "La Pure White Veil è un’ottima armatura generalista, con la Defense più alta tra tutte le armature femminili del gioco principale. Se preferisci qualcosa con un po’ più di mordente, e anche molto più facile da potenziare, puoi usare anche la Quartz Garment. Le sue abilità non sono impressionanti, ma le statistiche sono eccellenti per Magilou e utili per Eleanor e Velvet, che hanno entrambe bisogno di Arte Attack.",
    "elder-garden-survivors-garb": "Come avrai notato da tutte queste scelte degne di nota, le ragazze non hanno molte armature valide che migliorino davvero l’offesa. Queste due non risolvono molto il problema, purtroppo. Elder Garden è pura difesa, la migliore difesa mista tra tutte le armature femminili, mentre Survivor’s Garb è un ibrido con abilità difensive, ma anche Focus per migliorare indirettamente l’efficacia offensiva del personaggio. Entrambe sono valide, ma Survivor’s Garb è preferibile.",
    "womens-armor-postgame": "Eccola qui: la Uprising Veil, quell’armatura apparentemente mitica che aumenta sia attacco sia difesa, con anche ottime abilità al seguito. Non fa granché per Magilou, ma per gli dèi è eccezionale su Velvet. Eppure riesce comunque ad avere una concorrenza molto dura da parte di Empress Shield. Quell’indumento glorioso aumenta entrambe le difese con esattamente la distribuzione che si desidera davvero, meno Defense casuale e inutile e molta più resistenza alle magie ad area, e possiede due abilità che migliorano drasticamente la difesa contro tutti gli attacchi normali. Le Unnamed Garment semplicemente non possono competere a causa della loro Master Skill inaffidabile e della statistica singola poco rilevante. Due opzioni FANTASTICHE, una dimenticabile.",
    "jet-black-waistcoat": "Una buona armatura maschile universale. Dato che la maggior parte degli attacchi è non elementale, il suo incremento difensivo è più significativo di quanto i numeri facciano pensare. Non regge proprio fino alla fine del gioco, ma resta una grande risorsa per tutta la fase iniziale e centrale, quando le opzioni davvero buone scarseggiano.",
    "summertime-topaz-waistcoat": "Queste sono tutte armature valide fino all’endgame e diventano disponibili già più o meno all’inizio del late game. Summertime Waistcoat è fantastica per Eizen e Rokurou, ma inutile per Laphicet. Le sue abilità sono ottime e i bonus statistici sono a dir poco eccellenti, tanto da renderla una scelta di primo livello. Dall’altro lato della bilancia offensiva c’è Topaz Waistcoat, che è ottima per Laphicet ed Eizen, ma poco incisiva per Rokurou. Purtroppo la sua abilità è piuttosto mediocre, e questo la rende inferiore tra le due, anche se è molto più facile da potenziare perché richiede ingredienti comuni.",
    "mythril-reflex-waistcoat": "Entrambe queste Waistcoat da late game sono eccellenti per tutti e tre i ragazzi. Mythril Waistcoat è la più semplice da sfruttare, perché è di fatto una Jet Black Waistcoat migliorata ed è persino più facile da potenziare. Reflex Waistcoat, invece, è un po’ più difficile da usare: Eizen è già intoccabile con la sua Break Soul e Laphicet guadagna solo circa un secondo di invulnerabilità. Tuttavia, le sue statistiche sono molto migliori per Laphicet e il recupero del 100% dei danni riflessi è davvero ottimo per chiunque.",
    "mens-armor-postgame": "Qui non c’è nulla di particolarmente impressionante. Zero Impact Waistcoat è di gran lunga la più forte in termini di Defense pura, ma Unnamed Vestments fornisce una difesa effettiva superiore, sia fisica sia magica, grazie ad abilità molto più utili. Mumbane è la mia preferita del gruppo perché offre più Focus di tutte le altre armature che abbiano una statistica Defense; Kingly Waistcoat però le surclassa tutte. Prendile tutte e tre per le loro abilità, ma non sentirti obbligato a usarne una solo perché è esclusiva del post-game.",
}

SOURCE_NOTE_TEXT.update({
    "amphibole-blade": "L’Amphibole Blade è un’arma mono-stat che potenzia esattamente ciò di cui ha bisogno, possiede una Master Skill che rafforza molte delle arti di Velvet e un Enhancement Bonus che fornisce un aumento piatto al danno raramente resistito. Metti insieme tutto questo con la sua disponibilità precoce e con materiali di potenziamento facili da ottenere, e ti ritrovi una delle armi più utili del gioco.",
    "fonon-blade": "Dal punto di vista delle statistiche, la Fonon Blade è peggiore dell’Amphibole Blade in termini di Attack e danno complessivo, ma concede anche una buona quantità di Focus, rendendo facile mantenere alto il numero di Souls. L’arma si ottiene molto vicino alla fine del gioco, ma quasi tutti i nemici del dungeon finale, e anche molte aree immediatamente precedenti, sono Armored, il che rende la Fonon Blade l’arma anti-endgame ideale.",
    "adamantine-blade": "L’Adamantine Blade ha l’Attack più alto di tutte le armi da main game di Velvet, risultando l’arma principale più forte disponibile. Rafforza ulteriormente la propria supremazia grazie sia alla Master Skill sia all’Enhancement Bonus, che nel complesso sono abbastanza forti da renderla superiore persino alle sue prime due armi post-game. Il boost alla Defense è solo un piacevole extra. È l’arma da main game più forte per Velvet con una longevità che si estende a gran parte del post-game, rovinata solo dal fatto che arrivare a Katz Island durante il main game può essere una vera seccatura.",
    "blades-postgame": "Demon’s Bane è la miglior arma del kit di Velvet incentrata sulle Hidden Artes grazie al suo alto Arte Attack. Dragon Slayer è solo leggermente migliore dell’Adamantine Blade grazie alla sua Master Skill, ma l’Adamantine Blade finisce comunque per fare più Atk e per costare meno da potenziare. L’Unnamed Blade, invece, è di gran lunga la lama più forte, anzi proprio l’arma più forte dell’intero gioco, per potenza pura e abilità. Tieni Demon’s Bane, ignora Dragon Slayer e inchinati davanti all’Unnamed Blade in tutta la sua estetica banalità.",
    "feldspar-daggers": "Sono facilmente i pugnali più lineari e utili del gioco. Hanno un Attack molto alto, in competizione con i pugnali più forti del main game, sono disponibili all’incirca a metà campagna e sono facili da potenziare grazie al drop comune. Ancora più importante, il loro Enhancement Bonus può sfruttare in modo affidabile il Focus meraviglioso di Rokurou, grazie alle sue artes che infliggono Fatigue, Form 4 e Form 7. Se con Rokurou non ti interessa fare cose troppo sofisticate, queste sono le armi che fanno per te.",
    "kurogane-daggers": "L’Attack base di Rokurou è circa il 30% più alto del suo Arte Attack, quindi per le Hidden Artes 70 punti extra di Arte Attack valgono più di 70 punti di Attack. Il bonus al fuoco è piccolo, ma utilizzabile grazie al suo vasto arsenale di fire artes, mentre l’Enhancement Bonus è scandalosamente utile a prescindere da dove ti trovi nel gioco. Sono sorprendentemente solidi per essere un’arma gratuita.",
    "stygian-daggers": "Questa è l’arma da “pro”. Gli Stygian Daggers trasformano la più grande debolezza di Rokurou, il Focus, nella sua risorsa migliore, spalancando ogni sorta di porta a combo potenzialmente folli. La Master Skill è molto potente nell’alleviare la mancanza di un bonus ad Attack, mentre l’Enhancement Bonus sinergizza con l’alto Focus aggiungendo un’ulteriore possibilità di infliggere uno status ailment. Detto questo, l’arma è disponibile solo alla fine del gioco, quindi per via della sua natura specializzata la consiglierei come priorità solo se usi molto Rokurou.",
    "short-swords-postgame": "Ephemeral Wings è in realtà più forte di Lunar Tempests e supera persino gli Unnamed Daggers quando Rokurou raggiunge 866 Total Atk con il suo Enhancement Bonus attivo. Gli Unnamed Daggers, però, sono di gran lunga i più potenti skill-wise dell’intero gioco, assicurandosi così un posto tra le armi migliori del suo arsenale. In breve: Ephemeral Wings e Unnamed Daggers sono fantastici. Lunar Tempests è solo materiale da mastery fooder.",
    "secret-histories": "Considerando che quasi tutti i danni di Laphicet derivano dalle sue Malak Artes, il loro power boost da questo tipo di armi è ampiamente trascurabile. Tuttavia, il boost al Focus è graditissimo perché molte delle sue magie hanno tempi di lancio piuttosto lunghi. E proprio per questo Secret Histories brilla grazie alle sue abilità. Tutte le Malak Artes di Laphicet, tranne due, sono non-elementali, così come la fetta più grande delle sue Hidden Artes, quindi il potere d’attacco dell’arma influenza praticamente tutto il suo kit. Allo stesso modo, l’Enhancement Bonus accelera quasi tutte le sue magie, rendendolo un caster molto più efficiente. Anche se non usi Laphicet personalmente, quest’arma è eccellente con l’IA e dovrebbe essere una priorità.",
    "old-flyers": "Questa è una delle poche armi puramente difensive che risultino davvero degne di nota. È eccellente se vuoi che Laphicet funzioni come supporto più dedicato o che faccia maggior affidamento sulla sua Break Soul, anche se non è poi così utile se vuoi che faccia qualsiasi altra cosa.",
    "ember-paper": "Qui abbiamo l’arma orientata alle Malak Artes più forte disponibile per Laphicet durante la campagna. Anche se il Topaz Paper la supera di poco in Total Arte Attack, il Focus nettamente superiore compensa ampiamente la differenza su un personaggio che ne vuole il più possibile. Sfortunatamente, pur avendo un Enhancement Bonus fantastico, Laphicet non può davvero sfruttarlo perché non possiede neanche una singola arte che infligga Burn. A parte questo, è un’arma straordinaria e una scelta di prim’ordine per l’endgame.",
    "papers-postgame": "Lost Parlance è chiaramente l’arma più utile per Laphicet, perché aumenta il suo Arte Attack più di qualsiasi altra arma, accelerando anche il lancio delle magie e le cure. Vale comunque la pena notare che Unnamed Paper è l’arma ideale per ottimizzare le Hidden Artes di Laphicet, dato che colma completamente il divario tra Atk e A.Atk. Ragnarok, invece, è in gran parte dimenticabile a confronto con questi due colossi.",
    "armstrong": "Una delle mie armi preferite dell’intero gioco. Armstrong è una delle armi più facili da ottenere e l’unica che riesce a restare valida per tutta la campagna. È estremamente lineare: dà una montagna di Attack e praticamente nient’altro. Eizen ama Attack. Fine del discorso.",
    "perpetuity": "Se per qualche ragione pensi che il Focus di Eizen non sia già abbastanza ridicolo, esiste quest’arma. Concede una quantità considerevole di Focus insieme a una rispettabile dose di Attack, quindi puoi effettivamente far male ai nemici. Anche se il bonus al Focus non è alto quanto quello del Gattling Fist, entrambe le sue abilità sono molto più utili per dare senso all’idea di avere molto Focus, cioè usare la Break Soul, rendendola l’opzione più desiderabile.",
    "finger-of-god": "E, ultimo ma non meno importante, abbiamo un’arma che trasforma Eizen in un caster dedicato. Finger of God ha il più alto Arte Attack di tutti i Bracelets, persino di quelli post-game, aumenta leggermente Attack e possiede skill favorevoli a correre in giro ed evitare i nemici, cosa che probabilmente finirai per fare se dai priorità al casting. Io personalmente non la userei, ma Finger of God è senza dubbio un’arma potente che merita considerazione.",
    "bracelets-postgame": "Le scelte qui non sono troppo esaltanti. Tutte queste armi sono orientate all’Attack e due di esse sono mono-stat, il che le rende per lo più semplici upgrade lineari. Titan’s Knuckles supererà l’Unnamed Bracelet per danno; Eizen può arrivare a oltre 867 Attack senza l’Enhancement Bonus, anche se per farlo servono un po’ di Herbs e altri equipaggiamenti che aumentino l’Attack. Broken Shackle differenzia almeno un po’ il suo ruolo essendo sostanzialmente superiore a Perpetuity, ma le sue skill non sono nemmeno lontanamente altrettanto valide. Restano comunque senza dubbio le armi più forti di Eizen; è solo deludente che una sola di esse abbia davvero skill potenti per il combattimento.",
    "feldspar-doll": "Se per qualche motivo vuoi usare le Hidden Artes di Magilou come fonte di danno vero, la Feldspar Doll è una scelta giusta. Ha una statistica Attack rispettabile e possiede una Master Skill che la aumenta ulteriormente quando la salute scende. Nota però che la maggior parte di quanto ho detto vale per tutti i guardian comuni. Ho messo in evidenza la Feldspar Doll solo perché ha il Focus più alto, e il Focus è ciò che Magilou vuole davvero.",
    "secret-agent-doll": "La mia arma preferita del main game, non in piccola parte per via del suo modello. Secret Agent Doll ha statistiche fantastiche, una Master Skill incredibile e un Enhancement Bonus che accelera drasticamente la Malak Arte più devastante di Magilou. Il suo unico difetto è la disponibilità tardiva, anche se volendo puoi usare una versione inferiore, il Gradient Doll, per superare gran parte del mid game.",
    "twoside-doll": "Twoside Doll è una solida arma offensiva con un’enfasi marcata sulla sopravvivenza. L’elevato recupero HP mentre ci si muove, combinato con il suo forte bonus alla Defense, facilita uno stile di gioco “berserker” che potrebbe piacerti se non ti interessa pianificare con attenzione. Anche in questo caso, però, l’arma è disponibile solo verso la fine del gioco, quindi se vuoi qualcosa di simile prima, Witching Hour può fare da valido sostituto, oltre ad aiutarti a ottenere più equipaggiamento.",
    "guardians-postgame": "A differenza dei guardian del main game, tutti quelli del post-game sono piuttosto buoni. Corpore Sano è ideale per tankare, con skill che fanno una lieve concessione offensiva per mantenere il ruolo da arma. Doppelganger è, a livello statistico, il guardian definitivo per le Malak Artes. E l’Unnamed Guardian è il miglior guardian per le Hidden Artes, sotto ogni aspetto, e in più gode di due abilità estremamente utili. Insomma, stelle d’oro ovunque.",
    "mana-lance": "È facilmente l’arma iniziale più utile del gioco. Ha statistiche solide che reggono bene per gran parte della campagna, una Master Skill che aiuta Eleanor a raggiungere più in fretta il resto del gruppo e un Enhancement Bonus che rende molto più semplice ottenere oggetti. Non è niente meno che una grande arma.",
    "valkyrie": "Un’altra delle mie armi preferite. Valkyrie possiede la sempre utile capacità di potenziare la Break Soul, fornendo allo stesso tempo un buon incremento sia all’Attack sia all’Arte Attack di Eleanor. È l’unica Spear del main game che aumenti in modo sostanziale entrambe le statistiche offensive, e di conseguenza è l’unica arma che si sposi davvero con uno stile di gioco olistico.",
    "guandao": "In pratica è la paladina spear. Guandao ha una delle statistiche Attack più alte tra tutte le spears e, in più, concede un notevole incremento al Focus, garantendo più Souls, oltre a un costante recupero di HP. Il fatto che regga bene il confronto con le spears post-game, e che assomigli persino alla lancia di Guan Yu, è solo la ciliegina sulla torta. Davvero straordinaria.",
    "spears-postgame": "Hanno tutte un buon mix di statistiche, quindi non si oscurano a vicenda in modo netto. Final Scepter è per le Malak Artes, Gae Bolg per l’abuso degli status ailments e Nameless Spear per fare strage nelle armate e per il gioco standard. Le capacità sono MOLTO forti, il che le rende tutte eccellenti per gli status, anche se se quello è il tuo obiettivo principale conviene restare su Gae Bolg. In ogni caso, buone armi, grandi scelte.",
    "cassandra-sash": "Probabilmente è la miglior Belt dell’inizio gioco. Ha un Arte Attack molto alto che scala bene fino al late game, oltre a una master skill che rafforza in modo apprezzabile 4 delle 10 Hidden Artes di Velvet. Personalmente eviterei di usarla verso la fine del gioco, visto che viene superata dalla successiva Noteworthy Belt, ma è un’ottima scelta iniziale mentre stai ancora prendendo confidenza con tutto. Se, come me, non ti interessa rendere più forti le Hidden Artes di Velvet, puoi optare invece per la Duftwolke Sash che appare un po’ più tardi.",
    "gloire-des-mousseux-sash": "È la Belt del gioco principale che aumenta di più Arte Attack, e potenzialmente la più forte dell’intero gioco. Il fatto che arrivi così tardi ne rende discutibile il valore per il main game, ma la sua potenza è indiscutibile.",
    "helmut-schmidt-sash": "Questo oggetto è talmente forte che potresti persino giustificare di abusare delle spedizioni per Gald solo per raggiungere il livello negozio richiesto e prenderne una gratis. I bonus alle statistiche sono fantastici per Velvet che vuole tutto il Focus possibile senza azzoppare troppo il suo Arte Attack, e la Master Skill è probabilmente la più utile in assoluto per lei. Normalmente è disponibile solo nel dungeon finale, a meno che tu non alzi il livello negozio, ma essendo una ricompensa del negozio puoi iniziare una nuova partita con questa mostruosità. Semplicemente stellare.",
    "belts-postgame": "Per una ragazza dal Più Tragico dei Passati™ Velvet ha una fortuna assurda con l’equipaggiamento. L’Intrigue Sash porta il suo Atk a livelli ridicoli rendendola allo stesso tempo quasi immortale ogni volta che un nemico viene Stunned. La Jeanne d'Arc Sash aumenta parecchio entrambe le sue statistiche offensive e fornisce due abilità estremamente potenti. E l’Unnamed Belt dà il massimo incremento normale ad Arte Attack insieme a una skill che aiuta a sfondare i nemici che si mettono in guardia. Bottino d’oro su tutta la linea per la nostra vendicatrice.",
    "exquisite-charm": "Offre una quantità enorme di Arte Attack, più che sufficiente a portarti per tutta la seconda metà del gioco, ma non è questo il vero punto. Quello che ti interessa davvero è quel pazzesco incremento alla Defense dopo aver inflitto Slow. Rokurou ha due arti che infliggono Slow, Form 2 e Form 6, entrambe facili da inserire nelle combo. Quindi, combinato con l’elevato aumento della capacità di infliggere Slow e la naturalmente alta Defense di Rokurou, l’Exquisite Charm è un gingillo adorabile che trasforma Rangetsu Yaksha in puro acciaio Rangetsu.",
    "stoic-idol": "Rokurou ha la seconda Arte Defense più bassa del gioco, con Velvet che gli fa da regina assoluta in negativo, e non ha buone risposte ai caster nemici oltre alla sua Break Soul. Aumentare la sua A.Def e la sua capacità di infliggere Poison ne migliora sensibilmente la sopravvivenza. L’Arte Defense aumenta anche la quantità di HP ottenuti dalle healing artes, il che si combina bene con il suo stile più da tank. E senza contare che questa deliziosa torta di accessorio ha una Master Skill che colpisce due arti, Form 3 e Form 7, che funzionano comodamente contro i maghi grazie alla loro grande portata e alle proprietà perforanti, mentre il boost alla A.Def migliora anch’esso l’applicazione del Poison. È un pezzo fantastico che arriva proprio quando ti sposti nel late game.",
    "soothing-knife": "Questo è il vero Talisman offensivo. È disponibile solo alla fine del gioco, ma aumenta il suo Attack più di qualsiasi altro Talisman del gioco, incluso il trio post-game. Non userai spesso il suo Enhancement Bonus, dato che Moving Blade è l’unica arte di Rokurou che infligge Paralysis, ma se riesci a ottenerlo… diciamo solo che è meglio che i tuoi nemici scelgano un dio e preghino.",
    "talismans-postgame": "La distribuzione delle statistiche su questi accessori mi fa pensare che gli sviluppatori siano arrivati alle mie stesse conclusioni sugli accessori di Rokurou. Il Long Life Charm garantisce una quantità stupidamente alta di Defense, agendo di fatto come un secondo pezzo di armatura specializzato, ma ha abilità trascurabili perché il bonus ad Arte Attack è troppo basso per rendere utile quell’aumento di statistica. Il Perfect Bulwark è ancora più ridicolmente difensivo, nel senso che aumenta la Defense invece dell’Arte Attack, ma le sue abilità non hanno valore in combattimento. Infine c’è l’accessorio R21 mono-categoria obbligatorio, il meno utile dei tre, anche se possiede una Master Skill e un Enhancement Bonus estremamente validi che lo rendono un combattente più completo. Continuo comunque a preferire lo Stoic Idol a tutti e tre, anche se Perfect Bulwark e Long Life Charm restano solidi oggetti post-game.",
    "mars-satchel": "Uno degli oggetti più frustranti del gioco. Si ottiene prestissimo e ha statistiche fantastiche che lo mantengono competitivo per praticamente tutto il gioco, ma il suo Enhancement Bonus, che altrimenti sarebbe perfetto su un caster, è inutilizzabile per Laphicet a causa del fatto che non ha Hidden Artes che infliggano Burn. Perché ci fate questo, Bamco?",
    "topaz-bag": "Il Topaz Bag è sostanzialmente ciò che il Mars Satchel vorrebbe essere, solo disponibile molto più tardi. Ha più Arte Attack, rende Laphicet più resistente, è facile da potenziare e ci butta dentro anche un ulteriore bonus del 10% ad Arte Attack. Perché no? È fantastico, usalo.",
    "adamantine-bag": "È un potenziamento difficile da ottenere rispetto al Topaz Bag, con una disponibilità ancora peggiore. È solido nel post-game, anche se è improbabile che tu lo usi durante la storia dato che è molto simile al Topaz Bag ed è molto più difficile da potenziare.",
    "bags-postgame": "Sono diversi, ma non tutti validi. Il Solar Satchel è il miglior accessorio per le hidden artes, ma Laphicet ha una raccolta talmente terribile, e stranamente variabile, di hidden artes che è meglio lasciar perdere. Il Galactic Satchel invece è per i generalisti, combinando una coppia ben assortita di statistiche con abilità ideali, di nuovo, tutte e due a favore delle sue Malak Artes che sono non-elementali. L’Unnamed Bag prova a competere vantando il miglior boost ad A.Atk e una fantastica Break Soul, ma dato che i bonus alle arti non-elementali sono così significativi finiscono più o meno per equivalersi.",
    "feldspar-pendant": "Ottime statistiche con belle abilità: visto che Eizen ha tre arti che infliggono Fatigue (Last Throes, Wind Lance e Air Thrust), puoi attivare con costanza l’Enhancement Bonus e trasformarlo in un “vento di distruzione”. Devo aggiungere altro?",
    "pumper-upper": "La comodità definisce questo accessorio. Pumper-Upper ha un Arte Attack altissimo e una Master Skill utile, anche se senza valore in combattimento. Tuttavia, il fatto che tu possa semplicemente farmare gald e prenderlo quando vuoi lascia molto più spazio per sfruttarne le abilità. È fantastico.",
    "gnomes-force": "*Svenimento teatrale* L’accessorio perfetto. Sistema completamente l’unica vera debolezza di Eizen mentre allo stesso tempo potenzia il suo Arte Attack e metà delle sue arti offensive. È il massimo che si possa ottenere durante il gioco principale ed è disponibile proprio prima di entrare nell’ultimo dungeon.",
    "pendants-postgame": "Equipaggiamento solido come una roccia. Sylph’s Invitation è la controparte offensiva di Gnome’s Force. Entrambi coprono arti simili, ma uno aumenta Defense mentre l’altro aumenta Attack. Il boost ad Arte Attack di Sylph’s Invitation è molto più contenuto, bada bene, anche se non dovrebbe preoccuparti troppo quando Eizen sta lanciando i nemici fino a Giove. L’accessorio successivo, Undine’s Heart, è un po’ meno utile. L’Arte Defense di Eizen è già decente e, mentre il bonus ad Arte Attack è bello, viene completamente oscurato dall’Unnamed Pendant che in genere offre un rendimento migliore a fronte di un investimento minore. L’Unnamed Pendant possiede inoltre gli stessi vantaggi del Feldspar Pendant, potenziando potenzialmente anche il Focus di Eizen nello stesso tempo. In breve: il primo e l’ultimo accessorio post-game sono ottimi, il secondo è un po’ dimenticabile a meno che tu non abbia una passione per coltivare erbe.",
    "mana-earrings": "Potere puro per una strega fuori di testa? Dove si firma! Le Mana Earrings sono disponibili quando hai completato circa il 20% del gioco e restano il miglior incremento ad Arte Attack di Magilou fino a poco prima del dungeon finale. Sono un bel grosso affare e dovresti sempre tenerne un set a portata di mano.",
    "leviathan-satan-earrings": "Il gioco prova a nascondere questa conoscenza dietro tutte le sue Fire Malak Artes, ma Magilou ha una predisposizione per l’elemento Water. Di conseguenza, un accessorio che potenzia in maniera considerevole il suo principale attacco, incrementa di quasi la metà tutte le sue arti più forti, velocizza le sue cure più potenti e affronta la sua unica vera debolezza statistica, il Focus, è davvero fighissimo. Ovviamente non lo otterrai di nuovo nell’Empyrean’s Throne fino a poco prima della fine del gioco, ma è anche il momento in cui inizierai ad averne bisogno. Inoltre, se ti stai chiedendo perché le Satan’s Wrath Earrings non siano consigliate, è perché sono fastidiosamente difficili da ottenere, dato che il luogo è inaccessibile fino alla fine del gioco… dopo aver completato una lunga quest secondaria. Certo, sono un potenziamento netto delle Mana Earrings, ma avresti molta meno fatica prendendo le Leviathan Earrings proprio davanti all’ultimo dungeon.",
    "adamantine-earrings": "Le statistiche non mentono. È probabilmente il miglior accessorio del gioco principale per Magilou grazie alla sua Master Skill incredibile e alle statistiche ideali. Se hai avuto la fortuna di accedere a Katz Corner, prendilo assolutamente.",
    "earrings-postgame": "Lucifer’s Pride è il più forte, le Unnamed Earrings sono le migliori per “LOOK A SHOOTING STAR!”, e le Lucky Rabbit Earrings sono una stranezza statistica. Non c’è molto altro da dire. Prendi semplicemente l’oggetto del diavolo lungo la strada verso l’Ex-Dungeon e magari le Unnamed Earrings sulla via del ritorno.",
    "con-fuoco": "Con Fuoco è l’unico accessorio disponibile durante il gioco principale che aumenti Atk di una quantità ragionevole. Questo da solo basta a renderlo degno di nota per questa sezione. Inoltre, Con Fuoco offre un bonus significativo ad Arte Attack che può crescere fino a valori enormi dopo aver inflitto Burn, cosa con cui Eleanor dovrebbe avere poca difficoltà visto che tre delle sue arti basate sul fuoco lo applicano. Questo rende l’accessorio uno dei pochi che sostengono davvero tutto il suo lato offensivo. La rarità bassa lo rende anche relativamente facile da mantenere aggiornato, facendone uno dei migliori accessori del gioco principale.",
    "spiritoso": "Per quanto riguarda il fare davvero il suo lavoro, questo è facilmente il miglior Ribbon di tutta la campagna. È disponibile molto prima di quanto la sua rarità suggerisca perché si trova in un’area opzionale, e la sua statistica principale è ben oltre qualunque altro accessorio di Eleanor, escluso l’Unnamed Ribbon del post-game. Prendilo, potenzialo e ringraziami più tardi.",
    "brillante": "Brillante è più un accessorio di utilità. Porta l’Arte Attack di Eleanor a livelli appena “utilizzabili”, ma enfatizza soprattutto la sua Arte Defense per renderla più ricettiva alle cure e migliore contro i maghi. Inoltre fornisce un incremento incredibile alla velocità di apprendimento delle skill dell’equipaggiamento e al drop rate degli oggetti. È un’ottima manna per il post-game, anche se non è poi così determinante per il dungeon finale.",
    "ribbons-postgame": "Ancora una volta, gli sviluppatori confermano la mia analisi iniziale sui Ribbon concedendo a un personaggio tre oggetti end-game che altrimenti volerebbero in faccia allo scopo previsto della categoria. Perdendosi trasforma Eleanor in una raffica di status ailments, Grandioso la converte in un’attaccante più lenta ma di gran lunga più potente, e l’Unnamed Ribbon fa del suo meglio per renderla una Mixed Attacker competente. L’Unnamed Ribbon è il più forte, anche se sono tutti piuttosto validi, quindi scegli pure quello che si adatta meglio al tuo stile di gioco.",
})

PARTY_STAGES: tuple[tuple[str, int], ...] = (
    ("Velvet", 0),
    ("Rokurou", 1),
    ("Laphicet", 2),
    ("Eizen", 3),
    ("Magilou", 4),
    ("Eleanor", 5),
)

UNIVERSAL_SHOES_SOURCE_ENTRIES: tuple[dict[str, Any], ...] = tuple(
    {
        "character": character,
        "stage": stage,
        "slot": "Shoes",
        "order": 500,
        "checkpoint": "Post-game · Heavenly Steppes · 4th Chamber",
        "item": "Unnamed Boots",
        "category": "Shoes",
        "rarity": 21,
        "source_note_group": "unnamed-boots",
    }
    for character, stage in PARTY_STAGES
)

EIZEN_KAISER_ROAD_ENTRY: tuple[dict[str, Any], ...] = (
    {
        "character": "Eizen",
        "stage": 3,
        "slot": "Shoes",
        "order": 450,
        "checkpoint": "Final dungeon · Empyrean’s Throne",
        "item": "Kaiser Road",
        "category": "Men’s Shoes",
        "rarity": 17,
        "source_note_group": "kaiser-road",
    },
)

MENS_SHOES_SOURCE_ENTRIES: tuple[dict[str, Any], ...] = tuple(
    entry
    for character, stage in (("Rokurou", 1), ("Laphicet", 2), ("Eizen", 3))
    for entry in (
        {
            "character": character,
            "stage": stage,
            "slot": "Shoes",
            "order": 510,
            "checkpoint": "Post-game · Heavenly Steppes · Beginning",
            "item": "Gigant Shoes",
            "category": "Men’s Shoes",
            "rarity": 19,
            "source_note_group": "mens-shoes-postgame",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Shoes",
            "order": 520,
            "checkpoint": "Post-game · Heavenly Steppes · 2nd Chamber",
            "item": "Turbulent Shoes",
            "category": "Men’s Shoes",
            "rarity": 20,
            "source_note_group": "mens-shoes-postgame",
        },
    )
)

WOMENS_SHOES_SOURCE_ENTRIES: tuple[dict[str, Any], ...] = tuple(
    entry
    for character, stage in (("Velvet", 0), ("Magilou", 4), ("Eleanor", 5))
    for entry in (
        {
            "character": character,
            "stage": stage,
            "slot": "Shoes",
            "order": 440,
            "checkpoint": "Final dungeon · Innominat",
            "item": "Pegasus Wings",
            "category": "Women’s Shoes",
            "rarity": 17,
            "source_note_group": "pegasus-wings",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Shoes",
            "order": 510,
            "checkpoint": "Post-game · Heavenly Steppes · 2nd Chamber",
            "item": "Grounded Shoes",
            "category": "Women’s Shoes",
            "rarity": 19,
            "source_note_group": "womens-shoes-postgame",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Shoes",
            "order": 520,
            "checkpoint": "Post-game · Heavenly Steppes · 2nd Chamber",
            "item": "Queen Ellis Heels",
            "category": "Women’s Shoes",
            "rarity": 20,
            "source_note_group": "womens-shoes-postgame",
        },
    )
)


WEAPON_SOURCE_ENTRIES: tuple[dict[str, Any], ...] = (
    {"character": "Velvet", "stage": 0, "slot": "Weapon", "order": 10, "checkpoint": "Early game · Yseult shop", "item": "Amphibole Blade", "category": "Blades", "rarity": 8, "source_note_group": "amphibole-blade"},
    {"character": "Velvet", "stage": 0, "slot": "Weapon", "order": 20, "checkpoint": "Late game · Hexen Isle", "item": "Fonon Blade", "category": "Blades", "rarity": 15, "source_note_group": "fonon-blade"},
    {"character": "Velvet", "stage": 0, "slot": "Weapon", "order": 30, "checkpoint": "Optional late game · Katz Corner", "item": "Adamantine Blade", "category": "Blades", "rarity": 18, "source_note_group": "adamantine-blade"},
    {"character": "Velvet", "stage": 0, "slot": "Weapon", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st Chamber", "item": "Demon's Bane", "category": "Blades", "rarity": 19, "source_note_group": "blades-postgame"},
    {"character": "Velvet", "stage": 0, "slot": "Weapon", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 1st-4th Chamber", "item": "Dragon Slayer", "category": "Blades", "rarity": 20, "source_note_group": "blades-postgame"},
    {"character": "Velvet", "stage": 0, "slot": "Weapon", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 6th Chamber", "item": "Unnamed Blade", "category": "Blades", "rarity": 21, "source_note_group": "blades-postgame"},

    {"character": "Rokurou", "stage": 1, "slot": "Weapon", "order": 10, "checkpoint": "Mid game · Taliesin shop", "item": "Feldspar Daggers", "category": "Short Swords", "rarity": 10, "source_note_group": "feldspar-daggers"},
    {"character": "Rokurou", "stage": 1, "slot": "Weapon", "order": 20, "checkpoint": "Story reward", "item": "Kurogane Daggers", "category": "Short Swords", "rarity": 15, "source_note_group": "kurogane-daggers"},
    {"character": "Rokurou", "stage": 1, "slot": "Weapon", "order": 30, "checkpoint": "Final dungeon · Innominat", "item": "Stygian Daggers", "category": "Short Swords", "rarity": 17, "source_note_group": "stygian-daggers"},
    {"character": "Rokurou", "stage": 1, "slot": "Weapon", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st Chamber", "item": "Ephemeral Wings", "category": "Short Swords", "rarity": 19, "source_note_group": "short-swords-postgame"},
    {"character": "Rokurou", "stage": 1, "slot": "Weapon", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 3rd-6th Chamber", "item": "Lunar Tempests", "category": "Short Swords", "rarity": 20, "source_note_group": "short-swords-postgame"},
    {"character": "Rokurou", "stage": 1, "slot": "Weapon", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 6th Chamber", "item": "Unnamed Daggers", "category": "Short Swords", "rarity": 21, "source_note_group": "short-swords-postgame"},

    {"character": "Laphicet", "stage": 2, "slot": "Weapon", "order": 10, "checkpoint": "Mid game · Manann Reef", "item": "Secret Histories", "category": "Paper", "rarity": 9, "source_note_group": "secret-histories"},
    {"character": "Laphicet", "stage": 2, "slot": "Weapon", "order": 20, "checkpoint": "Late game · Baird Marsh", "item": "Old Flyers", "category": "Paper", "rarity": 13, "source_note_group": "old-flyers"},
    {"character": "Laphicet", "stage": 2, "slot": "Weapon", "order": 30, "checkpoint": "Final stretch · Zamahl Grotto", "item": "Ember Paper", "category": "Paper", "rarity": 17, "source_note_group": "ember-paper"},
    {"character": "Laphicet", "stage": 2, "slot": "Weapon", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st-4th Chamber", "item": "Ragnarok", "category": "Paper", "rarity": 19, "source_note_group": "papers-postgame"},
    {"character": "Laphicet", "stage": 2, "slot": "Weapon", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 3rd Chamber", "item": "Lost Parlance", "category": "Paper", "rarity": 20, "source_note_group": "papers-postgame"},
    {"character": "Laphicet", "stage": 2, "slot": "Weapon", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 6th Chamber", "item": "Unnamed Paper", "category": "Paper", "rarity": 21, "source_note_group": "papers-postgame"},

    {"character": "Eizen", "stage": 3, "slot": "Weapon", "order": 10, "checkpoint": "Early game · Barona Catacombs", "item": "Armstrong", "category": "Bracelets", "rarity": 5, "source_note_group": "armstrong"},
    {"character": "Eizen", "stage": 3, "slot": "Weapon", "order": 20, "checkpoint": "Late game · Baird Marsh", "item": "Perpetuity", "category": "Bracelets", "rarity": 13, "source_note_group": "perpetuity"},
    {"character": "Eizen", "stage": 3, "slot": "Weapon", "order": 30, "checkpoint": "Late game · Mount Killaraus", "item": "Finger of God", "category": "Bracelets", "rarity": 15, "source_note_group": "finger-of-god"},
    {"character": "Eizen", "stage": 3, "slot": "Weapon", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · Beginning / 1st Chamber", "item": "Titan's Knuckles", "category": "Bracelets", "rarity": 19, "source_note_group": "bracelets-postgame"},
    {"character": "Eizen", "stage": 3, "slot": "Weapon", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 1st-4th Chamber", "item": "Broken Shackle", "category": "Bracelets", "rarity": 20, "source_note_group": "bracelets-postgame"},
    {"character": "Eizen", "stage": 3, "slot": "Weapon", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 6th Chamber", "item": "Unnamed Bracelet", "category": "Bracelets", "rarity": 21, "source_note_group": "bracelets-postgame"},

    {"character": "Magilou", "stage": 4, "slot": "Weapon", "order": 10, "checkpoint": "Mid game · Taliesin shop", "item": "Feldspar Doll", "category": "Guardians", "rarity": 10, "source_note_group": "feldspar-doll"},
    {"character": "Magilou", "stage": 4, "slot": "Weapon", "order": 20, "checkpoint": "Late game · Mount Killaraus", "item": "Secret Agent Doll", "category": "Guardians", "rarity": 15, "source_note_group": "secret-agent-doll"},
    {"character": "Magilou", "stage": 4, "slot": "Weapon", "order": 30, "checkpoint": "Late game · Zamahl Grotto", "item": "Twoside Doll", "category": "Guardians", "rarity": 17, "source_note_group": "twoside-doll"},
    {"character": "Magilou", "stage": 4, "slot": "Weapon", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st-4th Chamber", "item": "Corpore Sano", "category": "Guardians", "rarity": 19, "source_note_group": "guardians-postgame"},
    {"character": "Magilou", "stage": 4, "slot": "Weapon", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 3rd Chamber", "item": "Doppelganger", "category": "Guardians", "rarity": 20, "source_note_group": "guardians-postgame"},
    {"character": "Magilou", "stage": 4, "slot": "Weapon", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 6th Chamber", "item": "Unnamed Guardian", "category": "Guardians", "rarity": 21, "source_note_group": "guardians-postgame"},

    {"character": "Eleanor", "stage": 5, "slot": "Weapon", "order": 10, "checkpoint": "Recruitment · East Laban Tunnel", "item": "Mana Lance", "category": "Spears", "rarity": 7, "source_note_group": "mana-lance"},
    {"character": "Eleanor", "stage": 5, "slot": "Weapon", "order": 20, "checkpoint": "Late game · Baird Marsh", "item": "Valkyrie", "category": "Spears", "rarity": 13, "source_note_group": "valkyrie"},
    {"character": "Eleanor", "stage": 5, "slot": "Weapon", "order": 30, "checkpoint": "Late game · Earthpulse", "item": "Guandao", "category": "Spears", "rarity": 15, "source_note_group": "guandao"},
    {"character": "Eleanor", "stage": 5, "slot": "Weapon", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st-4th Chamber", "item": "Final Scepter", "category": "Spears", "rarity": 19, "source_note_group": "spears-postgame"},
    {"character": "Eleanor", "stage": 5, "slot": "Weapon", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 3rd Chamber", "item": "Gae Bolg", "category": "Spears", "rarity": 20, "source_note_group": "spears-postgame"},
    {"character": "Eleanor", "stage": 5, "slot": "Weapon", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 6th Chamber", "item": "Nameless Spear", "category": "Spears", "rarity": 21, "source_note_group": "spears-postgame"},
)

ACCESSORY_SOURCE_ENTRIES: tuple[dict[str, Any], ...] = (
    {"character": "Velvet", "stage": 0, "slot": "Accessory", "order": 110, "checkpoint": "Early-mid game · Warg Forest", "item": "Cassandra Sash", "category": "Belts", "rarity": 7, "source_note_group": "cassandra-sash"},
    {"character": "Velvet", "stage": 0, "slot": "Accessory", "order": 120, "checkpoint": "Late game · Mount Killaraus / Meirchio", "item": "Gloire des Mousseux Sash", "category": "Belts", "rarity": 15, "source_note_group": "gloire-des-mousseux-sash"},
    {"character": "Velvet", "stage": 0, "slot": "Accessory", "order": 130, "checkpoint": "Final dungeon · Innominat / Katz Corner shop rank 10", "item": "Helmut Schmidt Sash", "category": "Belts", "rarity": 17, "source_note_group": "helmut-schmidt-sash"},
    {"character": "Velvet", "stage": 0, "slot": "Accessory", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st-4th Chamber", "item": "Intrigue Sash", "category": "Belts", "rarity": 19, "source_note_group": "belts-postgame"},
    {"character": "Velvet", "stage": 0, "slot": "Accessory", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 3rd Chamber", "item": "Jeanne d'Arc Sash", "category": "Belts", "rarity": 20, "source_note_group": "belts-postgame"},
    {"character": "Velvet", "stage": 0, "slot": "Accessory", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 5th Chamber", "item": "Unnamed Belt", "category": "Belts", "rarity": 21, "source_note_group": "belts-postgame"},
    {"character": "Rokurou", "stage": 1, "slot": "Accessory", "order": 110, "checkpoint": "Mid game · Titania · 2nd visit / Undead Quarter", "item": "Exquisite Charm", "category": "Talismans", "rarity": 9, "source_note_group": "exquisite-charm"},
    {"character": "Rokurou", "stage": 1, "slot": "Accessory", "order": 120, "checkpoint": "Late game · Titania · 3rd visit / Hexen Isle", "item": "Stoic Idol", "category": "Talismans", "rarity": 13, "source_note_group": "stoic-idol"},
    {"character": "Rokurou", "stage": 1, "slot": "Accessory", "order": 130, "checkpoint": "Final dungeon · Innominat", "item": "Soothing Knife", "category": "Talismans", "rarity": 17, "source_note_group": "soothing-knife"},
    {"character": "Rokurou", "stage": 1, "slot": "Accessory", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st Chamber", "item": "Long Life Charm", "category": "Talismans", "rarity": 19, "source_note_group": "talismans-postgame"},
    {"character": "Rokurou", "stage": 1, "slot": "Accessory", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 3rd-6th Chamber", "item": "Perfect Bulwark", "category": "Talismans", "rarity": 20, "source_note_group": "talismans-postgame"},
    {"character": "Rokurou", "stage": 1, "slot": "Accessory", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 5th Chamber", "item": "Unnamed Talisman", "category": "Talismans", "rarity": 21, "source_note_group": "talismans-postgame"},
    {"character": "Laphicet", "stage": 2, "slot": "Accessory", "order": 110, "checkpoint": "Early-mid game · Vester Tunnels", "item": "Mars Satchel", "category": "Bags", "rarity": 7, "source_note_group": "mars-satchel"},
    {"character": "Laphicet", "stage": 2, "slot": "Accessory", "order": 120, "checkpoint": "Late game · Port Zekson shop", "item": "Topaz Bag", "category": "Bags", "rarity": 14, "source_note_group": "topaz-bag"},
    {"character": "Laphicet", "stage": 2, "slot": "Accessory", "order": 130, "checkpoint": "Optional late game · Katz Corner", "item": "Adamantine Bag", "category": "Bags", "rarity": 18, "source_note_group": "adamantine-bag"},
    {"character": "Laphicet", "stage": 2, "slot": "Accessory", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st Chamber", "item": "Solar Satchel", "category": "Bags", "rarity": 19, "source_note_group": "bags-postgame"},
    {"character": "Laphicet", "stage": 2, "slot": "Accessory", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 3rd-6th Chamber", "item": "Galactic Satchel", "category": "Bags", "rarity": 20, "source_note_group": "bags-postgame"},
    {"character": "Laphicet", "stage": 2, "slot": "Accessory", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 5th Chamber", "item": "Unnamed Bag", "category": "Bags", "rarity": 21, "source_note_group": "bags-postgame"},
    {"character": "Eizen", "stage": 3, "slot": "Accessory", "order": 110, "checkpoint": "Mid game · Taliesin shop", "item": "Feldspar Pendant", "category": "Pendants", "rarity": 10, "source_note_group": "feldspar-pendant"},
    {"character": "Eizen", "stage": 3, "slot": "Accessory", "order": 120, "checkpoint": "Late game · Hexen Isle / shop level 8", "item": "Pumper-Upper", "category": "Pendants", "rarity": 13, "source_note_group": "pumper-upper"},
    {"character": "Eizen", "stage": 3, "slot": "Accessory", "order": 130, "checkpoint": "Late game · Mount Killaraus", "item": "Gnome's Force", "category": "Pendants", "rarity": 17, "source_note_group": "gnomes-force"},
    {"character": "Eizen", "stage": 3, "slot": "Accessory", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st-4th Chamber", "item": "Sylph's Invitation", "category": "Pendants", "rarity": 19, "source_note_group": "pendants-postgame"},
    {"character": "Eizen", "stage": 3, "slot": "Accessory", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 3rd Chamber", "item": "Undine's Heart", "category": "Pendants", "rarity": 20, "source_note_group": "pendants-postgame"},
    {"character": "Eizen", "stage": 3, "slot": "Accessory", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 5th Chamber", "item": "Unnamed Pendant", "category": "Pendants", "rarity": 21, "source_note_group": "pendants-postgame"},
    {"character": "Magilou", "stage": 4, "slot": "Accessory", "order": 110, "checkpoint": "Early-mid game · Brigid Ravine", "item": "Mana Earrings", "category": "Earrings", "rarity": 5, "source_note_group": "mana-earrings"},
    {"character": "Magilou", "stage": 4, "slot": "Accessory", "order": 120, "checkpoint": "Late game · Empyrean’s Throne · 2nd visit", "item": "Leviathan Earrings", "category": "Earrings", "rarity": 15, "source_note_group": "leviathan-satan-earrings"},
    {"character": "Magilou", "stage": 4, "slot": "Accessory", "order": 130, "checkpoint": "Late game · Hexen Isle / Meirchio", "item": "Satan's Wrath Earrings", "category": "Earrings", "rarity": 13, "source_note_group": "leviathan-satan-earrings"},
    {"character": "Magilou", "stage": 4, "slot": "Accessory", "order": 140, "checkpoint": "Optional late game · Katz Corner", "item": "Adamantine Earrings", "category": "Earrings", "rarity": 18, "source_note_group": "adamantine-earrings"},
    {"character": "Magilou", "stage": 4, "slot": "Accessory", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st-4th Chamber", "item": "Lucifer's Pride Earrings", "category": "Earrings", "rarity": 19, "source_note_group": "earrings-postgame"},
    {"character": "Magilou", "stage": 4, "slot": "Accessory", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 3rd Chamber", "item": "Lucky Rabbit Earrings", "category": "Earrings", "rarity": 20, "source_note_group": "earrings-postgame"},
    {"character": "Magilou", "stage": 4, "slot": "Accessory", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 5th Chamber", "item": "Unnamed Earrings", "category": "Earrings", "rarity": 21, "source_note_group": "earrings-postgame"},
    {"character": "Eleanor", "stage": 5, "slot": "Accessory", "order": 110, "checkpoint": "Mid game · Perniya Cliffside Path", "item": "Con Fuoco", "category": "Ribbons", "rarity": 11, "source_note_group": "con-fuoco"},
    {"character": "Eleanor", "stage": 5, "slot": "Accessory", "order": 120, "checkpoint": "Late game · Tranquil Woods", "item": "Spiritoso", "category": "Ribbons", "rarity": 13, "source_note_group": "spiritoso"},
    {"character": "Eleanor", "stage": 5, "slot": "Accessory", "order": 130, "checkpoint": "Final dungeon · Innominat", "item": "Brillante", "category": "Ribbons", "rarity": 17, "source_note_group": "brillante"},
    {"character": "Eleanor", "stage": 5, "slot": "Accessory", "order": 510, "checkpoint": "Post-game · Heavenly Steppes · 1st Chamber", "item": "Perdendosi", "category": "Ribbons", "rarity": 19, "source_note_group": "ribbons-postgame"},
    {"character": "Eleanor", "stage": 5, "slot": "Accessory", "order": 520, "checkpoint": "Post-game · Heavenly Steppes · 3rd Chamber", "item": "Grandioso", "category": "Ribbons", "rarity": 20, "source_note_group": "ribbons-postgame"},
    {"character": "Eleanor", "stage": 5, "slot": "Accessory", "order": 530, "checkpoint": "Post-game · Heavenly Steppes · 5th Chamber", "item": "Unnamed Ribbon", "category": "Ribbons", "rarity": 21, "source_note_group": "ribbons-postgame"},
)

RING_SOURCE_ENTRIES: tuple[dict[str, Any], ...] = tuple(
    entry
    for character, stage in PARTY_STAGES
    for entry in (
        {
            "character": character,
            "stage": stage,
            "slot": "Rings",
            "order": 330,
            "checkpoint": "Final dungeon · Innominat",
            "item": "Anthro Ring",
            "category": "Rings",
            "rarity": 16,
            "source_note_group": "offensive-rings",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Rings",
            "order": 340,
            "checkpoint": "Final dungeon · Innominat / Katz Corner",
            "item": "Plated Ring",
            "category": "Rings",
            "rarity": 17,
            "source_note_group": "offensive-rings",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Rings",
            "order": 510,
            "checkpoint": "Post-game · Heavenly Steppes · 3rd–6th Chamber",
            "item": "Lindworm Ring",
            "category": "Rings",
            "rarity": 20,
            "source_note_group": "postgame-rings",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Rings",
            "order": 520,
            "checkpoint": "Post-game · Heavenly Steppes · 4th Chamber",
            "item": "Unnamed Ring",
            "category": "Rings",
            "rarity": 21,
            "source_note_group": "postgame-rings",
        },
    )
)

MALE_ARMOR_SOURCE_ENTRIES: tuple[dict[str, Any], ...] = tuple(
    entry
    for character, stage in (("Rokurou", 1), ("Laphicet", 2), ("Eizen", 3))
    for entry in (
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 210,
            "checkpoint": "Early-mid game · Warg Forest",
            "item": "Jet Black Waistcoat",
            "category": "Men’s Armor",
            "rarity": 7,
            "source_note_group": "jet-black-waistcoat",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 220,
            "checkpoint": "Late game · Baird Marsh / Meirchio",
            "item": "Summertime Waistcoat",
            "category": "Men’s Armor",
            "rarity": 13,
            "source_note_group": "summertime-topaz-waistcoat",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 230,
            "checkpoint": "Late game · Port Zekson shop",
            "item": "Topaz Waistcoat",
            "category": "Men’s Armor",
            "rarity": 14,
            "source_note_group": "summertime-topaz-waistcoat",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 240,
            "checkpoint": "Late game · Meirchio shop",
            "item": "Mythril Waistcoat",
            "category": "Men’s Armor",
            "rarity": 16,
            "source_note_group": "mythril-reflex-waistcoat",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 250,
            "checkpoint": "Post-game · Heavenly Steppes · Beginning",
            "item": "Reflex Waistcoat",
            "category": "Men’s Armor",
            "rarity": 17,
            "source_note_group": "mythril-reflex-waistcoat",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 510,
            "checkpoint": "Post-game · Heavenly Steppes · Beginning",
            "item": "Zero Impact Waistcoat",
            "category": "Men’s Armor",
            "rarity": 19,
            "source_note_group": "mens-armor-postgame",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 520,
            "checkpoint": "Post-game · Heavenly Steppes · 2nd Chamber",
            "item": "Mumbane",
            "category": "Men’s Armor",
            "rarity": 20,
            "source_note_group": "mens-armor-postgame",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 530,
            "checkpoint": "Post-game · Heavenly Steppes · 4th Chamber",
            "item": "Unnamed Vestments",
            "category": "Men’s Armor",
            "rarity": 21,
            "source_note_group": "mens-armor-postgame",
        },
    )
)


WOMENS_ARMOR_SOURCE_ENTRIES: tuple[dict[str, Any], ...] = tuple(
    entry
    for character, stage in (("Velvet", 0), ("Magilou", 4), ("Eleanor", 5))
    for entry in (
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 210,
            "checkpoint": "Early-mid game · Burnack Plateau / Yseult",
            "item": "Garish Pink Shirt",
            "category": "Women’s Armor",
            "rarity": 7,
            "source_note_group": "garish-pink-shirt",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 220,
            "checkpoint": "Mid game · Aldina Plains",
            "item": "Pure White Veil",
            "category": "Women’s Armor",
            "rarity": 11,
            "source_note_group": "pure-white-quartz-garment",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 230,
            "checkpoint": "Late game · Hellawes shop return visit",
            "item": "Quartz Garment",
            "category": "Women’s Armor",
            "rarity": 12,
            "source_note_group": "pure-white-quartz-garment",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 240,
            "checkpoint": "Late game · Hexen Isle",
            "item": "Elder Garden",
            "category": "Women’s Armor",
            "rarity": 15,
            "source_note_group": "elder-garden-survivors-garb",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 250,
            "checkpoint": "Final dungeon · Innominat",
            "item": "Survivor's Garb",
            "category": "Women’s Armor",
            "rarity": 17,
            "source_note_group": "elder-garden-survivors-garb",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 510,
            "checkpoint": "Post-game · Heavenly Steppes · Beginning",
            "item": "Uprising Veil",
            "category": "Women’s Armor",
            "rarity": 19,
            "source_note_group": "womens-armor-postgame",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 520,
            "checkpoint": "Post-game · Heavenly Steppes · 2nd Chamber",
            "item": "Empress Shield",
            "category": "Women’s Armor",
            "rarity": 20,
            "source_note_group": "womens-armor-postgame",
        },
        {
            "character": character,
            "stage": stage,
            "slot": "Armor",
            "order": 530,
            "checkpoint": "Post-game · Heavenly Steppes · 4th Chamber",
            "item": "Unnamed Garment",
            "category": "Women’s Armor",
            "rarity": 21,
            "source_note_group": "womens-armor-postgame",
        },
    )
)



def recommendation_source_group(entry: dict[str, Any]) -> str:
    item = str(entry.get("item", ""))
    return str(SOURCE_NOTE_ITEM_GROUPS.get(item) or entry.get("source_note_group") or normalized(item)).replace(" ", "-")


def compiled_recommendations() -> list[dict[str, Any]]:
    """Publish only source-attributed recommendation text, never generated commentary."""
    rows = [
        *RECOMMENDED_EQUIPMENT,
        *WEAPON_SOURCE_ENTRIES,
        *UNIVERSAL_SHOES_SOURCE_ENTRIES,
        *EIZEN_KAISER_ROAD_ENTRY,
        *MENS_SHOES_SOURCE_ENTRIES,
        *WOMENS_SHOES_SOURCE_ENTRIES,
        *ACCESSORY_SOURCE_ENTRIES,
        *RING_SOURCE_ENTRIES,
        *MALE_ARMOR_SOURCE_ENTRIES,
        *WOMENS_ARMOR_SOURCE_ENTRIES,
    ]
    compiled: list[dict[str, Any]] = []
    index_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in rows:
        entry = {key: value for key, value in raw.items() if key != "reason"}
        key = (str(entry["character"]), normalized(str(entry["item"])))
        group = recommendation_source_group(entry)
        entry["source_note_group"] = group
        note = SOURCE_NOTE_TEXT.get(group)
        if note:
            entry["source_note"] = note
        existing = index_by_key.get(key)
        if existing is None:
            compiled.append(entry)
            index_by_key[key] = entry
            continue
        for field, value in entry.items():
            if value in (None, ""):
                continue
            existing[field] = value
    return compiled


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


def validate_recommendation_data(items: list[dict[str, Any]], recommendations: list[dict[str, Any]] | None = None) -> None:
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
    rows = recommendations if recommendations is not None else compiled_recommendations()
    for entry in rows:
        character = str(entry.get("character", ""))
        if character != "All" and character not in covered:
            raise RuntimeError(f"Unknown recommendation character: {character}")
        item = items_by_name.get(normalized(str(entry.get("item", ""))))
        if item is None:
            raise RuntimeError(f"Recommended item is absent from the catalogue: {entry.get('item')}")
        if entry.get("category") != item.get("category") or entry.get("rarity") != item.get("rarity"):
            raise RuntimeError(f"Recommended equipment metadata does not match the catalogue: {entry.get('item')}")
        for field in ("slot", "checkpoint", "category", "source_note_group"):
            if not str(entry.get(field, "")).strip():
                raise RuntimeError(f"Recommended equipment is missing {field}: {entry.get('item')}")
        if "reason" in entry:
            raise RuntimeError(f"Generated recommendation commentary must not be published: {entry.get('item')}")
        if character in covered:
            covered[character] += 1

    required_slots = {"Weapon", "Accessory", "Armor", "Rings", "Shoes"}
    for name in expected_names:
        personal = [entry for entry in rows if entry.get("character") == name]
        slots = {str(entry.get("slot", "")) for entry in personal}
        missing_slots = sorted(required_slots - slots)
        if missing_slots:
            raise RuntimeError(f"Recommended-equipment route is missing slot coverage for {name}: {', '.join(missing_slots)}")
        if len(personal) < 10:
            raise RuntimeError(f"Recommended-equipment route is too short for {name}")

    missing = [name for name, count in covered.items() if count < 10]
    if missing:
        raise RuntimeError(f"Every party member needs a full recommended-equipment route: {missing}")


def validate(categories: list[dict[str, str]], items: list[dict[str, Any]], cards: list[dict[str, Any]]) -> None:
    validate_recommendation_data(items, compiled_recommendations())
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
        "schema_version": 6,
        "complete": True,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "categories": categories,
        "items": items,
        "reference_cards": cards,
        "character_growth": list(CHARACTER_GROWTH),
        "recommended_equipment": compiled_recommendations(),
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
