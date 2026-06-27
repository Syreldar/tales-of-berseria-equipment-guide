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
    {'character': 'Velvet', 'stage': 0, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Early-mid game · Fens of Nog', 'item': 'Cast Heels', 'category': 'Women’s Shoes', 'rarity': 7, 'reason': 'A standout Women’s Shoes pickup: very high Focus plus BG gain and extra maximum BG. It is worth targeting even if later footwear has higher rarity.'},
    {'character': 'Velvet', 'stage': 0, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Late game · Earthpulse', 'item': 'Shimmery Shoes', 'category': 'Women’s Shoes', 'rarity': 15, 'reason': 'A higher-Focus alternative with SG economy. Use it when Cast Heels are unavailable or when weak-point combos make the SG return more useful.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Weapon', 'order': 10, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Feldspar Daggers', 'category': 'Short Swords', 'rarity': 10, 'reason': 'High Attack, accessible Common materials, and a Fatigue trigger that repairs Rokurou’s weak Focus. The default straightforward damage choice.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Weapon', 'order': 20, 'checkpoint': 'Story reward', 'item': 'Kurogane Daggers', 'category': 'Short Swords', 'rarity': 15, 'reason': 'A balanced story weapon with useful fire coverage and excellent Break Soul recovery. Its extra Arte Attack helps Hidden Artes more than the stat line first suggests.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Weapon', 'order': 30, 'checkpoint': 'Final dungeon · Innominat', 'item': 'Stygian Daggers', 'category': 'Short Swords', 'rarity': 17, 'reason': 'A specialist Focus weapon for deep combo play. It turns Rokurou’s usual weakness into a resource, but is only worth prioritizing for an active Rokurou build.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Accessory', 'order': 110, 'checkpoint': 'Mid game · Titania', 'item': 'Exquisite Charm', 'category': 'Talismans', 'rarity': 9, 'reason': 'Pairs a large Arte Attack boost with a huge Defense payoff after Slow. Rokurou can trigger it naturally through Slow-inflicting combo resets.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Accessory', 'order': 120, 'checkpoint': 'Late game · Hexen Isle', 'item': 'Stoic Idol', 'category': 'Talismans', 'rarity': 13, 'reason': 'A defensive accessory for caster-heavy areas. The large Arte Defense gain and healing synergy give Rokurou a safer answer to enemy artes.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Armor', 'order': 210, 'checkpoint': 'Early-mid game · Warg Forest', 'item': 'Jet Black Waistcoat', 'category': 'Men’s Armor', 'rarity': 7, 'reason': 'A universal Men’s Armor pick against the predominantly non-elemental damage of the early and middle game. Strong before the later specialized choices arrive.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Armor', 'order': 220, 'checkpoint': 'Late game · Baird Marsh', 'item': 'Summertime Waistcoat', 'category': 'Men’s Armor', 'rarity': 13, 'reason': 'An endgame-viable Armor with a meaningful Attack component. It is especially well suited to Rokurou’s physical pressure.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Rings', 'order': 310, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Force Ring', 'category': 'Rings', 'rarity': 10, 'reason': 'A strong Arte Defense milestone that stays efficient well past its rarity. Keep one for magical encounters and for learning Ring skills.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Rings', 'order': 320, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Barrier Ring', 'category': 'Rings', 'rarity': 15, 'reason': 'The upgraded Arte Defense staple. It is the cleanest answer when incoming arte damage matters more than niche offensive ring bonuses.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Mid game · Hellawes return', 'item': 'Quartz Boots', 'category': 'Shoes', 'rarity': 12, 'reason': 'A universal Focus pair with stun-oriented effects. Easy Common materials make it a practical backup for male physical builds.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Mid game · Faldies Ruins', 'item': 'Protective Hops', 'category': 'Men’s Shoes', 'rarity': 11, 'reason': 'Choose this defensive Men’s Shoes option when survival and faster item use matter more than Focus. It is a deliberate utility alternative, not a damage upgrade.'},
    {'character': 'Rokurou', 'stage': 1, 'slot': 'Shoes', 'order': 440, 'checkpoint': 'Late game · Gaiburk Icefield', 'item': 'Hyper Velocity Boots', 'category': 'Men’s Shoes', 'rarity': 15, 'reason': 'A late Focus spike with stronger status pressure and a stun-finishing bonus. Excellent when the party can repeatedly create Stunned targets.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Weapon', 'order': 10, 'checkpoint': 'Mid game · Manann Reef', 'item': 'Secret Histories', 'category': 'Paper', 'rarity': 9, 'reason': 'The key offensive Paper for a caster route: it raises Focus, boosts almost all of Laphicet’s non-elemental damage, and shortens most of his casts.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Weapon', 'order': 20, 'checkpoint': 'Late game · Baird Marsh', 'item': 'Old Flyers', 'category': 'Paper', 'rarity': 13, 'reason': 'A defensive Paper for support-focused play. Select it for survivability and Break Soul support rather than for direct spell damage.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Weapon', 'order': 30, 'checkpoint': 'Final stretch · Zamahl Grotto', 'item': 'Ember Paper', 'category': 'Paper', 'rarity': 17, 'reason': 'The strongest campaign Paper for Malak Arte damage. Its Focus lead makes it preferable for endgame casting even though Laphicet cannot exploit its Burn enhancement bonus.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Accessory', 'order': 110, 'checkpoint': 'Early-mid game · Vester Tunnels', 'item': 'Mars Satchel', 'category': 'Bags', 'rarity': 7, 'reason': 'An unusually early Arte Attack Bag with stats that remain useful for a long time. Its Burn payoff is unavailable to Laphicet, so treat it as raw caster value.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Accessory', 'order': 120, 'checkpoint': 'Late game · Port Zekson shop', 'item': 'Topaz Bag', 'category': 'Bags', 'rarity': 14, 'reason': 'A cleaner late-game replacement: more Arte Attack, extra toughness, Common materials, and an additional percentage boost to his core stat.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Armor', 'order': 210, 'checkpoint': 'Early-mid game · Warg Forest', 'item': 'Jet Black Waistcoat', 'category': 'Men’s Armor', 'rarity': 7, 'reason': 'A universal Men’s Armor pick against the predominantly non-elemental damage of the early and middle game. Strong before the later specialized choices arrive.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Armor', 'order': 220, 'checkpoint': 'Late game · Hellawes return', 'item': 'Topaz Waistcoat', 'category': 'Men’s Armor', 'rarity': 14, 'reason': 'A common-material Armor that gives Laphicet useful Arte Attack alongside Defense. Its combat skill is modest, but the stat split fits a caster better than the physical option.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Rings', 'order': 310, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Force Ring', 'category': 'Rings', 'rarity': 10, 'reason': 'A strong Arte Defense milestone that stays efficient well past its rarity. Keep one for magical encounters and for learning Ring skills.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Rings', 'order': 320, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Barrier Ring', 'category': 'Rings', 'rarity': 15, 'reason': 'The upgraded Arte Defense staple. It is the cleanest answer when incoming arte damage matters more than niche offensive ring bonuses.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Mid game · Hellawes return', 'item': 'Quartz Boots', 'category': 'Shoes', 'rarity': 12, 'reason': 'A universal Focus pair with stun-oriented effects. Easy Common materials make it a practical backup for male physical builds.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Mid game · Faldies Ruins', 'item': 'Protective Hops', 'category': 'Men’s Shoes', 'rarity': 11, 'reason': 'Choose this defensive Men’s Shoes option when survival and faster item use matter more than Focus. It is a deliberate utility alternative, not a damage upgrade.'},
    {'character': 'Laphicet', 'stage': 2, 'slot': 'Shoes', 'order': 440, 'checkpoint': 'Late game · Gaiburk Icefield', 'item': 'Hyper Velocity Boots', 'category': 'Men’s Shoes', 'rarity': 15, 'reason': 'A late Focus spike with stronger status pressure and a stun-finishing bonus. Excellent when the party can repeatedly create Stunned targets.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Weapon', 'order': 10, 'checkpoint': 'Early game · Barona Catacombs', 'item': 'Armstrong', 'category': 'Bracelets', 'rarity': 5, 'reason': 'An early Attack-focused Bracelet that stays useful through the whole campaign. Its purpose is simple and exactly matches Eizen’s preferred physical stat.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Weapon', 'order': 20, 'checkpoint': 'Late game · Baird Marsh', 'item': 'Perpetuity', 'category': 'Bracelets', 'rarity': 13, 'reason': 'A Focus-heavy alternative that still retains workable Attack. Its Break Soul effects give the extra Focus a concrete payoff instead of making it a passive stat pile.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Accessory', 'order': 110, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Feldspar Pendant', 'category': 'Pendants', 'rarity': 10, 'reason': 'A dependable Arte Attack and Focus Pendant whose Fatigue bonus is easy for Eizen to trigger with several of his artes.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Accessory', 'order': 120, 'checkpoint': 'Late game · Hexen Isle / shop level 8', 'item': 'Pumper-Upper', 'category': 'Pendants', 'rarity': 13, 'reason': 'A convenience-focused Pendant with very high Arte Attack and faster equipment learning. It is easy to obtain when its skill still has time to matter.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Armor', 'order': 210, 'checkpoint': 'Early-mid game · Warg Forest', 'item': 'Jet Black Waistcoat', 'category': 'Men’s Armor', 'rarity': 7, 'reason': 'A universal Men’s Armor pick against the predominantly non-elemental damage of the early and middle game. Strong before the later specialized choices arrive.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Armor', 'order': 220, 'checkpoint': 'Late game · Baird Marsh', 'item': 'Summertime Waistcoat', 'category': 'Men’s Armor', 'rarity': 13, 'reason': 'A top physical Armor choice for Eizen: it combines Defense with Attack and remains worthwhile through the end of the main campaign.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Armor', 'order': 230, 'checkpoint': 'Late game · Hellawes return', 'item': 'Topaz Waistcoat', 'category': 'Men’s Armor', 'rarity': 14, 'reason': 'A second late-game Armor route for a more mixed offensive setup. It trades physical emphasis for Arte Attack and is easier to enhance as a Common piece.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Rings', 'order': 310, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Force Ring', 'category': 'Rings', 'rarity': 10, 'reason': 'A strong Arte Defense milestone that stays efficient well past its rarity. Keep one for magical encounters and for learning Ring skills.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Rings', 'order': 320, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Barrier Ring', 'category': 'Rings', 'rarity': 15, 'reason': 'The upgraded Arte Defense staple. It is the cleanest answer when incoming arte damage matters more than niche offensive ring bonuses.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Mid game · Hellawes return', 'item': 'Quartz Boots', 'category': 'Shoes', 'rarity': 12, 'reason': 'A universal Focus pair with stun-oriented effects. Easy Common materials make it a practical backup for male physical builds.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Mid game · Faldies Ruins', 'item': 'Protective Hops', 'category': 'Men’s Shoes', 'rarity': 11, 'reason': 'Choose this defensive Men’s Shoes option when survival and faster item use matter more than Focus. It is a deliberate utility alternative, not a damage upgrade.'},
    {'character': 'Eizen', 'stage': 3, 'slot': 'Shoes', 'order': 440, 'checkpoint': 'Late game · Gaiburk Icefield', 'item': 'Hyper Velocity Boots', 'category': 'Men’s Shoes', 'rarity': 15, 'reason': 'A late Focus spike with stronger status pressure and a stun-finishing bonus. Excellent when the party can repeatedly create Stunned targets.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Weapon', 'order': 10, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Feldspar Doll', 'category': 'Guardians', 'rarity': 10, 'reason': 'A Common Guardian for a Hidden Arte-oriented Magilou. It has the highest Focus among the common options while retaining useful Attack.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Weapon', 'order': 20, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Secret Agent Doll', 'category': 'Guardians', 'rarity': 15, 'reason': 'A high-end Guardian with strong mixed stats, fire power, and faster fire casting. Its only real drawback is arriving near the end of the campaign.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Accessory', 'order': 110, 'checkpoint': 'Early-mid game · Brigid Ravine', 'item': 'Mana Earrings', 'category': 'Earrings', 'rarity': 5, 'reason': 'A long-lasting Arte Attack staple. It appears early and remains Magilou’s strongest pure Arte Attack accessory until very late in the story.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Accessory', 'order': 120, 'checkpoint': 'Late game · Hexen Isle', 'item': "Satan's Wrath Earrings", 'category': 'Earrings', 'rarity': 13, 'reason': 'A large direct Arte Attack upgrade with a percentage multiplier. Pick it when raw spell power matters more than elemental specialization.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Accessory', 'order': 130, 'checkpoint': 'Late game · Empyrean’s Throne return', 'item': 'Leviathan Earrings', 'category': 'Earrings', 'rarity': 15, 'reason': 'A Water-focused caster option with extra Focus and faster Water casting. It matches Magilou’s Water bias and improves an important healing arte.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Armor', 'order': 210, 'checkpoint': 'Mid game · Hellawes return', 'item': 'Quartz Garment', 'category': 'Women’s Armor', 'rarity': 12, 'reason': 'An easier-to-enhance Women’s Armor that adds useful Arte Attack while still improving Defense. It is the offensive alternative to a pure-defense set.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Armor', 'order': 220, 'checkpoint': 'Final dungeon · Innominat', 'item': "Survivor's Garb", 'category': 'Women’s Armor', 'rarity': 17, 'reason': 'A late hybrid Armor that turns Focus and healing effects into practical durability. Prefer it when Magilou needs to keep casting under pressure.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Rings', 'order': 310, 'checkpoint': 'Mid game · Taliesin shop', 'item': 'Force Ring', 'category': 'Rings', 'rarity': 10, 'reason': 'A strong Arte Defense milestone that stays efficient well past its rarity. Keep one for magical encounters and for learning Ring skills.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Rings', 'order': 320, 'checkpoint': 'Late game · Mount Killaraus', 'item': 'Barrier Ring', 'category': 'Rings', 'rarity': 15, 'reason': 'The upgraded Arte Defense staple. It is the cleanest answer when incoming arte damage matters more than niche offensive ring bonuses.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Early-mid game · Fens of Nog', 'item': 'Cast Heels', 'category': 'Women’s Shoes', 'rarity': 7, 'reason': 'A standout Women’s Shoes pickup: very high Focus plus BG gain and extra maximum BG. It is worth targeting even if later footwear has higher rarity.'},
    {'character': 'Magilou', 'stage': 4, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Late game · Earthpulse', 'item': 'Shimmery Shoes', 'category': 'Women’s Shoes', 'rarity': 15, 'reason': 'A higher-Focus alternative with SG economy. Use it when Cast Heels are unavailable or when weak-point combos make the SG return more useful.'},
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
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Shoes', 'order': 410, 'checkpoint': 'Early game · Reneed shop', 'item': 'Fluoric Boots', 'category': 'Shoes', 'rarity': 6, 'reason': 'A temporary universal Shoes option that makes Break Soul BG generation easier. Safe to enhance early, then replace once a character-specific pair arrives.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Shoes', 'order': 420, 'checkpoint': 'Early-mid game · Fens of Nog', 'item': 'Cast Heels', 'category': 'Women’s Shoes', 'rarity': 7, 'reason': 'A standout Women’s Shoes pickup: very high Focus plus BG gain and extra maximum BG. It is worth targeting even if later footwear has higher rarity.'},
    {'character': 'Eleanor', 'stage': 5, 'slot': 'Shoes', 'order': 430, 'checkpoint': 'Late game · Earthpulse', 'item': 'Shimmery Shoes', 'category': 'Women’s Shoes', 'rarity': 15, 'reason': 'A higher-Focus alternative with SG economy. Use it when Cast Heels are unavailable or when weak-point combos make the SG return more useful.'},
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
        for field in ("slot", "checkpoint", "category", "reason"):
            if not str(entry.get(field, "")).strip():
                raise RuntimeError(f"Recommended equipment is missing {field}: {entry.get('item')}")
        if character in covered:
            covered[character] += 1

    required_slots = {"Weapon", "Accessory", "Armor", "Rings", "Shoes"}
    for name in expected_names:
        personal = [entry for entry in RECOMMENDED_EQUIPMENT if entry.get("character") == name]
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
