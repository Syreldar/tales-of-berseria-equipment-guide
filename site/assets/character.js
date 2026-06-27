(function() {
    "use strict";

    const target = document.getElementById("character-dossier");
    const themeToggle = document.getElementById("theme-toggle");
    const storageKey = "tob-equipment-guide-theme";
    const spoilerModeKey = "tob-equipment-guide-spoiler-mode";
    const spoilerProgressKey = "tob-equipment-guide-spoiler-progress";
    const slotOrder = ["Weapon", "Accessory", "Armor", "Rings", "Shoes"];
    const slotLabels = Object.freeze({
        "Weapon": "Weapon · Arma",
        "Accessory": "Accessory · Accessorio",
        "Armor": "Armor · Armatura",
        "Rings": "Rings · Anello",
        "Shoes": "Shoes · Calzature"
    });
    const slotIcons = Object.freeze({
        "Weapon": "⚔",
        "Accessory": "✦",
        "Armor": "⛨",
        "Rings": "◈",
        "Shoes": "⌁"
    });
    const categoryIcons = Object.freeze({
        "Blades": "🗡️",
        "Short Swords": "🗡️",
        "Paper": "📜",
        "Bracelets": "🥊",
        "Guardians": "🧸",
        "Spears": "🔱",
        "Belts": "🎗️",
        "Talismans": "🪬",
        "Bags": "👜",
        "Pendants": "📿",
        "Earrings": "💎",
        "Ribbons": "🎀",
        "Men’s Armor": "🛡️",
        "Women’s Armor": "🛡️",
        "Rings": "💍",
        "Shoes": "👞",
        "Men’s Shoes": "👞",
        "Women’s Shoes": "👠"
    });
    const categoryIds = Object.freeze({
        "Blades": "blades",
        "Short Swords": "short-swords",
        "Paper": "paper",
        "Bracelets": "bracelets",
        "Guardians": "guardians",
        "Spears": "spears",
        "Belts": "belts",
        "Talismans": "talismans",
        "Bags": "bags",
        "Pendants": "pendants",
        "Earrings": "earrings",
        "Ribbons": "ribbons",
        "Men’s Armor": "mens-armor",
        "Women’s Armor": "womens-armor",
        "Rings": "rings",
        "Shoes": "shoes",
        "Men’s Shoes": "mens-shoes",
        "Women’s Shoes": "womens-shoes"
    });

    const members = Object.freeze([
        {
            id: "velvet",
            name: "Velvet",
            stage: 0,
            tone: "velvet",
            role: "Attaccante in prima linea · combo, Stun e Therion Form",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Velvet_Cut-in_%28ToB%29.png",
            equipmentFocus: "Blades privilegiano Atk; Belts possono aggiungere Focus per lo Stun. Su Armor, Rings, Shoes e Women’s Shoes conserva prima le Master Skills che non hai ancora appreso.",
            titleAdvice: "Incapacitator finché i Rings sono a +8 o meno. Dopo quel punto puoi tornare a un Title offensivo se vuoi più danno o utilità, ma il preset prudente parte sempre dalla protezione contro Stun.",
            ai: {
                summary: "Preset aggressivo ma affidabile: scegli un nemico robusto, lascia che Velvet completi la catena ed entri in Therion Form senza sprecare mosse che l'AI tende a mancare.",
                strategy: ["Target Strong Enemies", "Aim for Weaknesses", "Be Aggressive", "Change Out", "You Decide"],
                mode: "Artes OFF",
                skills: ["Harsh Rebuttal", "Avalanche Fang", "Moonlight Cyclone", "Rising Moon", "Rising Falcon", "Soaring Dragon", "Slag Assault", "Grounding Strike", "Banishing Thunder", "Binding Frost"],
                footnote: "Lascia ON le altre Artes, incluso Scale Crusher."
            }
        },
        {
            id: "rokurou",
            name: "Rokurou",
            stage: 1,
            tone: "rokurou",
            role: "Duellante in prima linea · Souls, counter e colpi mirati",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Rokurou_Cut-in_%28ToB%29.png",
            equipmentFocus: "Cerca Atk su Short Swords e Talismans; Armor, Shoes e Men’s Shoes servono a non farlo cadere mentre resta vicino al nemico. Impara prima ogni Master Skill nuova.",
            titleAdvice: "Incapacitator fino a Rings +8. Superata quella soglia puoi tornare su un Title più offensivo, ma per l'AI il guadagno maggiore resta evitare Stun letali mentre duella in prima linea.",
            ai: {
                summary: "Preset difensivo e lineare: Rokurou deve colpire le debolezze senza perdere tempo in riposizionamenti o in Forms che l'AI concatena male.",
                strategy: ["Target Enemy with Most Souls", "Aim for Weaknesses", "Defense Only", "Change Out", "You Decide"],
                mode: "Artes OFF",
                skills: ["Crimson Flash", "Jade Wave", "Armor Crusher", "Double Haze", "Orochi’s Fury", "Form 1: Fire Burst", "Form 2: Imbue Earth", "Form 5: Scatterburst", "Form 6: Dark Vortex", "Form 7: Rapid Bolt"],
                footnote: "Lascia ON tutte le altre Artes non elencate."
            }
        },
        {
            id: "laphicet",
            name: "Laphicet",
            stage: 2,
            tone: "laphicet",
            role: "Incantatore di supporto · magie rapide, cure e controllo",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Laphicet_Cut-in_%28ToB%29.png",
            equipmentFocus: "Paper e Bags favoriscono Arte Attack. Arte Defense e Focus sono utili quando viene preso di mira; prima di sostituire un pezzo, impara la sua Master Skill.",
            titleAdvice: "Scelta sicura: Incapacitator finché i Rings sono a +8 o meno. Eccezione legittima: Sorcerer se vuoi aumentare la pressione offensiva e i Void cast, accettando un preset meno prudente.",
            ai: {
                summary: "Laphicet funziona meglio con poche Malak Artes affidabili. Ridurre la lista abbassa i cast lunghi, gli errori di priorità e le interruzioni mentre resta a distanza.",
                strategy: ["Target Multiple Enemies", "Engage at Range", "Defense Only", "Change Out", "For Attacking"],
                mode: "Malak Artes ON",
                skills: ["Kaleidos Ray", "Blessed Drops", "Void Mire", "Dark Fangs"],
                footnote: "Metti OFF tutte le altre Malak Artes."
            }
        },
        {
            id: "eizen",
            name: "Eizen",
            stage: 3,
            tone: "eizen",
            role: "Combattente flessibile · pugni durante la storia, magia del vento più tardi",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Eizen_Cut-in_%28ToB%29.png",
            equipmentFocus: "Nel set Fist Bruiser cerca Atk e Focus. Nel set Wind Master conta di più Arte Attack, ma mantieni Def e Arte Defense: Eizen può comunque ricevere pressione.",
            titleAdvice: "Incapacitator resta il punto di partenza fino a Rings +8. In seguito scegli in base al ruolo: più sicurezza se lo usi in mischia, più danno/cast se lo usi come Wind Master.",
            ai: {
                summary: "Eizen ha due preset distinti. Non mescolare le due configurazioni: scegline una completa e usala finché non hai davvero sbloccato il set successivo.",
                variants: [
                    {
                        name: "Fist Bruiser",
                        availability: "Durante la storia",
                        strategy: ["Target Nearby Enemies", "Balanced", "Defense Only", "Change Out", "For Attacking"],
                        mode: "Artes OFF",
                        skills: ["Verdict", "Tempo", "Eleventh Hour", "Clear Path", "Lighthouse", "Deceiving Pummel", "Tutte le Malak Artes tranne Flash Step e Stone Lance"],
                        footnote: "È la configurazione più semplice e consistente finché non hai il set completo da Wind Master."
                    },
                    {
                        name: "Wind Master",
                        availability: "Endgame / set completo",
                        strategy: ["Target Multiple Enemies", "Fast Attacks", "Defense Only", "Change Out", "For Attacking"],
                        mode: "Lascia ON solo",
                        skills: ["Martial Artes: Coercion, Last Throes", "Malak Artes: Stone Lance, Hell Gate"],
                        footnote: "Passa qui solo dopo aver sbloccato tutte e quattro le mosse chiave."
                    }
                ]
            }
        },
        {
            id: "magilou",
            name: "Magilou",
            stage: 4,
            tone: "magilou",
            role: "Incantatrice offensiva · magie rapide da lontano",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Magilou_Cut-in_%28ToB%29.png",
            equipmentFocus: "Guardians e Earrings favoriscono Arte Attack. Arte Defense è utile perché un personaggio che lancia magie colpito durante un cast perde più valore di pochi punti aggiuntivi di danno.",
            titleAdvice: "Incapacitator resta la scelta standard fino a Rings +8. Se poi vuoi più pressione magica puoi rivalutare un Title da caster, ma il preset base premia prima la sopravvivenza.",
            ai: {
                summary: "Magilou rende meglio con una rotazione molto corta: poche magie, cast più sicuri e meno aperture in cui l'AI si fa interrompere.",
                strategy: ["Target Multiple Enemies", "Engage at Range", "Defense Only", "Change Out", "For Attacking"],
                mode: "Malak Artes ON",
                skills: ["Aqua Split", "Blood Moon", "Opzionale: Crown Fire"],
                footnote: "Metti OFF tutte le altre Malak Artes."
            }
        },
        {
            id: "eleanor",
            name: "Eleanor",
            stage: 5,
            tone: "eleanor",
            role: "Combattente ibrida · lancia e magie a distanza ravvicinata",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Eleanor_Cut-in_%28ToB%29.png",
            equipmentFocus: "Scegli una priorità per volta: Atk per le Martial Artes, Arte Attack per Flame Beast e Maelstrom. Non distribuire le statistiche senza uno scopo.",
            titleAdvice: "Incapacitator fino a Rings +8. Dopo puoi cercare più danno, ma per un personaggio ibrido che combatte vicino al bersaglio il controllo dello Stun resta uno dei bonus difensivi più apprezzabili.",
            ai: {
                summary: "Eleanor vuole stare vicina al bersaglio e usare una rotazione corta. Le mosse che respingono troppo o rompono il seguito della combo rendono l'AI molto meno affidabile.",
                strategy: ["Target Nearby Enemies", "Close Combat", "Defense Only", "Change Out", "For Attacking"],
                mode: "Artes OFF",
                skills: ["Martial Artes: Vanguard, Double Rush, Skewering Spear, Cleansing Lance", "Malak Artes: tutte tranne Flame Beast e Maelstrom"],
                footnote: "Mantieni la rotazione corta: è qui che l'AI di Eleanor lavora meglio."
            }
        }
    ]);

    function escapeHtml(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function normalize(value) {
        return String(value || "").trim().toLocaleLowerCase("it");
    }

    function slugify(value) {
        return normalize(value)
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "");
    }

    function getTheme() {
        try {
            return window.localStorage.getItem(storageKey) || "light";
        } catch (error) {
            return "light";
        }
    }

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme;
        themeToggle.textContent = theme === "dark" ? "Tema chiaro" : "Tema scuro";
        themeToggle.setAttribute("aria-label", theme === "dark" ? "Attiva il tema chiaro" : "Attiva il tema scuro");
    }

    function initializeTheme() {
        applyTheme(getTheme());
        themeToggle.addEventListener("click", function() {
            const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
            try {
                window.localStorage.setItem(storageKey, next);
            } catch (error) {
                /* Theme still works for this page load. */
            }
            applyTheme(next);
        });
    }

    function spoilerState() {
        try {
            const mode = window.localStorage.getItem(spoilerModeKey);
            const progress = Number(window.localStorage.getItem(spoilerProgressKey));
            return {
                enabled: mode !== "off",
                stage: Number.isInteger(progress) ? Math.max(0, Math.min(5, progress)) : 0
            };
        } catch (error) {
            return { enabled: true, stage: 0 };
        }
    }

    function phaseFromRarity(rarity) {
        return Number(rarity) >= 19 ? "Post-game" : "Story";
    }

    function phaseLabel(rarity) {
        return phaseFromRarity(rarity) === "Post-game" ? "👑 Post-game" : "🧭 Storia principale";
    }

    function memberFromQuery() {
        const params = new URLSearchParams(window.location.search);
        const requested = normalize(params.get("character"));
        return members.find(function(member) {
            return normalize(member.name) === requested || member.id === requested;
        }) || members[0];
    }

    function itemId(item) {
        return `item-${slugify(item.category_id)}-${item.rarity}-${slugify(item.name)}`;
    }

    function itemHref(member, item, entry) {
        const categoryId = item ? item.category_id : categoryIds[String(entry.category || "")] || "";
        const params = new URLSearchParams();
        params.set("character", member.name);
        if (categoryId) {
            params.set("category", categoryId);
        }
        const hash = item ? `#${itemId(item)}` : "#catalogo";
        return `./index.html?${params.toString()}${hash}`;
    }

    /*
     * The roadmap is chronological by default.  Badges are reserved for source-backed
     * callouts, not for a generic quality ladder.
     *
     * Best in slot is deliberately rare: one item at most per character/category and
     * only when the translated source makes a genuinely unambiguous claim.
     */
    /*
     * Every item in the roadmap gets a concise, source-led purpose label.
     * These are not quality tiers: they explain why the piece belongs in the
     * route.  Only the explicitly confirmed standouts use Best in slot.
     */
    const sourceCalloutByItem = Object.freeze({
        /* Velvet · Blades */
        "Amphibole Blade": { key: "early", label: "Early-game carry", icon: "⚡" },
        "Fonon Blade": { key: "build", label: "Anti-Armored route", icon: "🛡️" },
        "Adamantine Blade": { key: "offense", label: "Best main-game damage", icon: "🔥" },
        "Demon's Bane": { key: "build", label: "Hidden Arte route", icon: "✦" },
        "Dragon Slayer": { key: "postgame", label: "Post-game comparison", icon: "↗" },
        "Unnamed Blade": { key: "final", label: "Post-game power route", icon: "★" },

        /* Rokurou · Short Swords */
        "Feldspar Daggers": { key: "early", label: "Main-game carry", icon: "⚡" },
        "Kurogane Daggers": { key: "story", label: "Story reward upgrade", icon: "◆" },
        "Stygian Daggers": { key: "focus", label: "Focus specialist", icon: "◈" },
        "Ephemeral Wings": { key: "offense", label: "Attack-cap route", icon: "🔥" },
        "Lunar Tempests": { key: "mastery", label: "Mastery material", icon: "📘" },
        "Unnamed Daggers": { key: "final", label: "Post-game skill powerhouse", icon: "★" },

        /* Laphicet · Paper */
        "Secret Histories": { key: "build", label: "AI caster priority", icon: "✦" },
        "Old Flyers": { key: "defense", label: "Support route", icon: "🛡️" },
        "Ember Paper": { key: "offense", label: "Endgame Malak route", icon: "🔥" },
        "Ragnarok": { key: "postgame", label: "Post-game alternative", icon: "↗" },
        "Lost Parlance": { key: "final", label: "Post-game caster powerhouse", icon: "★" },
        "Unnamed Paper": { key: "build", label: "Hidden Arte route", icon: "✦" },

        /* Eizen · Bracelets */
        "Armstrong": { key: "early", label: "Early-game mainstay", icon: "⚡" },
        "Perpetuity": { key: "focus", label: "Focus + Break Soul route", icon: "◈" },
        "Finger of God": { key: "build", label: "Caster route", icon: "✦" },
        "Titan's Knuckles": { key: "offense", label: "Raw Attack route", icon: "🔥" },
        "Broken Shackle": { key: "postgame", label: "Versatile post-game", icon: "↗" },
        "Unnamed Bracelet": { key: "final", label: "Post-game all-rounder", icon: "★" },

        /* Magilou · Guardians */
        "Feldspar Doll": { key: "build", label: "Hidden Arte alternative", icon: "✦" },
        "Secret Agent Doll": { key: "offense", label: "Late-game caster spike", icon: "🔥" },
        "Twoside Doll": { key: "defense", label: "Offense + survival", icon: "🛡️" },
        "Corpore Sano": { key: "defense", label: "Tanking route", icon: "🛡️" },
        "Doppelganger": { key: "build", label: "Malak Arte route", icon: "✦" },
        "Unnamed Guardian": { key: "build", label: "Hidden Arte route", icon: "✦" },

        /* Eleanor · Spears */
        "Mana Lance": { key: "early", label: "Early-game carry", icon: "⚡" },
        "Valkyrie": { key: "build", label: "Hybrid build", icon: "✦" },
        "Guandao": { key: "offense", label: "Paladin-style main-game route", icon: "🔥" },
        "Final Scepter": { key: "build", label: "Malak Arte route", icon: "✦" },
        "Gae Bolg": { key: "build", label: "Status-abuse route", icon: "☄" },
        "Nameless Spear": { key: "offense", label: "Standard damage route", icon: "🔥" },

        /* Velvet · Belts */
        "Cassandra Sash": { key: "best-early", label: "Best early", icon: "🌱" },
        "Gloire des Mousseux Sash": { key: "offense", label: "Maximum Arte Attack", icon: "🔥" },
        "Helmut Schmidt Sash": { key: "final", label: "Final-dungeon powerhouse", icon: "★" },
        "Intrigue Sash": { key: "build", label: "Stun-sustain route", icon: "✦" },
        "Jeanne d'Arc Sash": { key: "offense", label: "Dual-offense route", icon: "🔥" },
        "Unnamed Belt": { key: "build", label: "Guard-break route", icon: "✦" },

        /* Rokurou · Talismans */
        "Exquisite Charm": { key: "defense", label: "Slow tanking route", icon: "🛡️" },
        "Stoic Idol": { key: "bis", label: "Best in slot", icon: "👑" },
        "Soothing Knife": { key: "offense", label: "Attack finisher", icon: "🔥" },
        "Long Life Charm": { key: "defense", label: "Pure-defense option", icon: "🛡️" },
        "Perfect Bulwark": { key: "defense", label: "Defense-wall option", icon: "🛡️" },
        "Unnamed Talisman": { key: "mastery", label: "Skill-utility option", icon: "📘" },

        /* Laphicet · Bags */
        "Mars Satchel": { key: "early", label: "Early-game caster route", icon: "⚡" },
        "Topaz Bag": { key: "offense", label: "Main-game upgrade", icon: "🔥" },
        "Adamantine Bag": { key: "postgame", label: "Difficult sidegrade", icon: "↗" },
        "Solar Satchel": { key: "build", label: "Hidden Arte route", icon: "✦" },
        "Galactic Satchel": { key: "build", label: "Generalist Malak route", icon: "✦" },
        "Unnamed Bag": { key: "build", label: "Break Soul route", icon: "✦" },

        /* Eizen · Pendants */
        "Feldspar Pendant": { key: "build", label: "Fatigue synergy", icon: "☄" },
        "Pumper-Upper": { key: "mastery", label: "Farmable utility", icon: "📘" },
        "Gnome's Force": { key: "final", label: "Best main-game pendant", icon: "★" },
        "Sylph's Invitation": { key: "offense", label: "Offensive pendant route", icon: "🔥" },
        "Undine's Heart": { key: "caution", label: "Lower-priority post-game", icon: "◌" },
        "Unnamed Pendant": { key: "postgame", label: "Efficient post-game route", icon: "↗" },

        /* Magilou · Earrings */
        "Mana Earrings": { key: "early", label: "Early-game core", icon: "⚡" },
        "Satan's Wrath Earrings": { key: "caution", label: "Hard-to-get upgrade", icon: "◌" },
        "Leviathan Earrings": { key: "build", label: "Water-caster route", icon: "✦" },
        "Adamantine Earrings": { key: "final", label: "Best main-game earrings", icon: "★" },
        "Lucifer's Pride Earrings": { key: "offense", label: "Highest raw power", icon: "🔥" },
        "Lucky Rabbit Earrings": { key: "postgame", label: "Stat-anomaly option", icon: "↗" },
        "Unnamed Earrings": { key: "build", label: "Shooting Star route", icon: "✦" },

        /* Eleanor · Ribbons */
        "Con Fuoco": { key: "offense", label: "Main-game Atk core", icon: "🔥" },
        "Spiritoso": { key: "final", label: "Best campaign Ribbon", icon: "★" },
        "Brillante": { key: "mastery", label: "Utility + mastery route", icon: "📘" },
        "Perdendosi": { key: "build", label: "Status route", icon: "☄" },
        "Grandioso": { key: "offense", label: "Slow power route", icon: "🔥" },
        "Unnamed Ribbon": { key: "final", label: "Post-game strongest route", icon: "★" },

        /* Armor shared by the relevant characters */
        "Garish Pink Shirt": { key: "early", label: "Story offense bridge", icon: "⚡" },
        "Pure White Veil": { key: "defense", label: "Generalist defense", icon: "🛡️" },
        "Quartz Garment": { key: "offense", label: "Offensive generalist", icon: "🔥" },
        "Elder Garden": { key: "defense", label: "Pure-defense option", icon: "🛡️" },
        "Survivor's Garb": { key: "build", label: "Preferred hybrid", icon: "✦" },
        "Uprising Veil": { key: "postgame", label: "Offense-defense post-game", icon: "↗" },
        "Empress Shield": { key: "defense", label: "Magic-defense specialist", icon: "🛡️" },
        "Unnamed Garment": { key: "caution", label: "Lower-priority option", icon: "◌" },
        "Jet Black Waistcoat": { key: "early", label: "Early-story universal", icon: "⚡" },
        "Summertime Waistcoat": { key: "offense", label: "Late-game martial route", icon: "🔥" },
        "Topaz Waistcoat": { key: "mastery", label: "Easy-enhancement route", icon: "📘" },
        "Mythril Waistcoat": { key: "build", label: "Simple universal upgrade", icon: "✦" },
        "Reflex Waistcoat": { key: "defense", label: "Reflection route", icon: "🛡️" },
        "Zero Impact Waistcoat": { key: "defense", label: "Raw-defense option", icon: "🛡️" },
        "Mumbane": { key: "focus", label: "Focus post-game option", icon: "◈" },
        "Unnamed Vestments": { key: "defense", label: "Effective-defense option", icon: "🛡️" },

        /* Rings */
        "Force Ring": { key: "best-early", label: "Best early", icon: "🌱" },
        "Barrier Ring": { key: "best-early", label: "Best early", icon: "🌱" },
        "Anthro Ring": { key: "mastery", label: "Good Master Skill material", icon: "📘" },
        "Plated Ring": { key: "mastery", label: "Good Master Skill material", icon: "📘" },
        "Lindworm Ring": { key: "postgame", label: "Useful-stat option", icon: "↗" },
        "Unnamed Ring": { key: "final", label: "Post-game skill powerhouse", icon: "★" },

        /* Shoes shared by the relevant characters */
        "Fluoric Boots": { key: "early", label: "Early-game training wheels", icon: "⚡" },
        "Cast Heels": { key: "best-early", label: "Best early", icon: "🌱" },
        "Shimmery Shoes": { key: "build", label: "Cast Heels fallback", icon: "✦" },
        "Quartz Boots": { key: "build", label: "Atk + status route", icon: "☄" },
        "Protective Hops": { key: "defense", label: "Defensive fallback", icon: "🛡️" },
        "Hyper Velocity Boots": { key: "offense", label: "Late-game Focus spike", icon: "🔥" },
        "Unnamed Boots": { key: "postgame", label: "Post-game fallback", icon: "↗" },
        "Kaiser Road": { key: "build", label: "Eizen berserker route", icon: "✦" },
        "Gigant Shoes": { key: "defense", label: "Tanking route", icon: "🛡️" },
        "Turbulent Shoes": { key: "offense", label: "Post-game damage route", icon: "🔥" },
        "Pegasus Wings": { key: "defense", label: "Defensive Cast Heels", icon: "🛡️" },
        "Grounded Shoes": { key: "build", label: "Ventite-combo route", icon: "✦" },
        "Queen Ellis Heels": { key: "focus", label: "Focus crown route", icon: "◈" }
    });

    /*
     * Every character/category route has one source-led primary recommendation.
     * A primary recommendation is not automatically Best in slot: the latter is
     * reserved only for comments that make an unambiguous overall claim. Where
     * the source presents competing build paths, the page marks one general
     * recommendation and keeps the alternatives visible with their own roles.
     */
    const recommendedByCharacterCategory = Object.freeze({
        "velvet::Blades": "Unnamed Blade",
        "velvet::Belts": "Helmut Schmidt Sash",
        "velvet::Women’s Armor": "Uprising Veil",
        "velvet::Rings": "Unnamed Ring",
        "velvet::Shoes": "Fluoric Boots",
        "velvet::Women’s Shoes": "Queen Ellis Heels",

        "rokurou::Short Swords": "Unnamed Daggers",
        "rokurou::Talismans": "Stoic Idol",
        "rokurou::Men’s Armor": "Summertime Waistcoat",
        "rokurou::Rings": "Unnamed Ring",
        "rokurou::Shoes": "Quartz Boots",
        "rokurou::Men’s Shoes": "Turbulent Shoes",

        "laphicet::Paper": "Lost Parlance",
        "laphicet::Bags": "Galactic Satchel",
        "laphicet::Men’s Armor": "Reflex Waistcoat",
        "laphicet::Rings": "Unnamed Ring",
        "laphicet::Shoes": "Quartz Boots",
        "laphicet::Men’s Shoes": "Turbulent Shoes",

        "eizen::Bracelets": "Unnamed Bracelet",
        "eizen::Pendants": "Gnome's Force",
        "eizen::Men’s Armor": "Summertime Waistcoat",
        "eizen::Rings": "Unnamed Ring",
        "eizen::Shoes": "Quartz Boots",
        "eizen::Men’s Shoes": "Kaiser Road",

        "magilou::Guardians": "Doppelganger",
        "magilou::Earrings": "Lucifer's Pride Earrings",
        "magilou::Women’s Armor": "Empress Shield",
        "magilou::Rings": "Unnamed Ring",
        "magilou::Shoes": "Fluoric Boots",
        "magilou::Women’s Shoes": "Grounded Shoes",

        "eleanor::Spears": "Guandao",
        "eleanor::Ribbons": "Unnamed Ribbon",
        "eleanor::Women’s Armor": "Uprising Veil",
        "eleanor::Rings": "Unnamed Ring",
        "eleanor::Shoes": "Fluoric Boots",
        "eleanor::Women’s Shoes": "Queen Ellis Heels"
    });

    const recommendedReasonByCharacterCategory = Object.freeze({
        "velvet::Blades": "La lama più forte dell'intero gioco per potenza pura e abilità.",
        "velvet::Belts": "Focus, statistiche e Master Skill eccezionali specificamente per Velvet.",
        "velvet::Women’s Armor": "Su Velvet combina in modo straordinario attacco, difesa e abilità; Empress Shield resta una valida alternativa difensiva.",
        "velvet::Rings": "La coppia di abilità è descritta come disgustosamente potente.",
        "velvet::Shoes": "Primo investimento universale affidabile: statistiche corrette e BG più facile da mantenere.",
        "velvet::Women’s Shoes": "Focus, Attack e Enhancement Bonus la rendono la scelta conclusiva per Velvet.",

        "rokurou::Short Swords": "È tra le armi più forti del suo arsenale per le abilità; Ephemeral Wings resta l'alternativa da danno puro.",
        "rokurou::Talismans": "L'autore la preferisce esplicitamente a tutte le opzioni post-game.",
        "rokurou::Men’s Armor": "Statistiche e abilità eccellenti la rendono la scelta prioritaria per Rokurou nel late game.",
        "rokurou::Rings": "La coppia di abilità è descritta come disgustosamente potente.",
        "rokurou::Shoes": "Attack, Focus e status: un pacchetto pratico che vale sempre la pena tenere di scorta.",
        "rokurou::Men’s Shoes": "La guida invita esplicitamente a saltare Gigant Shoes e abusare di queste.",

        "laphicet::Paper": "È chiaramente definita l'arma più utile: massimizza Arte Attack e accelera cast e cure.",
        "laphicet::Bags": "È la scelta generalista per Malak Artes con statistiche e abilità ben assortite.",
        "laphicet::Men’s Armor": "Le statistiche sono molto migliori su Laphicet e il recupero dei danni riflessi è eccellente.",
        "laphicet::Rings": "La coppia di abilità è descritta come disgustosamente potente.",
        "laphicet::Shoes": "Attack, Focus e status: il miglior percorso pratico da tenere pronto.",
        "laphicet::Men’s Shoes": "La guida invita esplicitamente a saltare Gigant Shoes e abusare di queste.",

        "eizen::Bracelets": "La scelta post-game più completa: il commento indica che una sola ha skill davvero potenti, oltre a un ottimo rendimento generale.",
        "eizen::Pendants": "Accessorio definito perfetto: copre la debolezza chiave di Eizen e potenzia Arte Attack e arti offensive.",
        "eizen::Men’s Armor": "Statistiche e abilità eccellenti la rendono una scelta di primo livello per Eizen.",
        "eizen::Rings": "La coppia di abilità è descritta come disgustosamente potente.",
        "eizen::Shoes": "Attack, Focus e status: percorso universale efficiente prima delle opzioni specifiche.",
        "eizen::Men’s Shoes": "Su Eizen è descritta come una bomba subatomica: una seconda arma in termini di statistiche.",

        "magilou::Guardians": "È il guardian definitivo per le Malak Artes, cioè il nucleo del danno di Magilou.",
        "magilou::Earrings": "Il commento la identifica come l'opzione più forte del gruppo post-game.",
        "magilou::Women’s Armor": "Uprising Veil fa poco per Magilou; questa offre la distribuzione difensiva e le abilità più adatte al suo ruolo.",
        "magilou::Rings": "La coppia di abilità è descritta come disgustosamente potente.",
        "magilou::Shoes": "Investimento iniziale affidabile per BG e Master Skills, prima delle opzioni più situazionali.",
        "magilou::Women’s Shoes": "La scelta specifica per Magilou: rende LOOK A SHOOTING STAR! eccezionale con Guardbreaker.",

        "eleanor::Spears": "Attack molto alto, Focus, recupero HP e resa comparabile alle Spears post-game.",
        "eleanor::Ribbons": "Il commento la definisce la più forte tra le opzioni post-game.",
        "eleanor::Women’s Armor": "È il miglior upgrade naturale della Garish Pink Shirt nel post-game; Empress Shield resta una concorrenza difensiva molto forte.",
        "eleanor::Rings": "La coppia di abilità è descritta come disgustosamente potente.",
        "eleanor::Shoes": "Investimento iniziale affidabile per BG e Master Skills, prima delle opzioni più situazionali.",
        "eleanor::Women’s Shoes": "Focus, Attack e Enhancement Bonus la rendono la scelta conclusiva per Eleanor."
    });

    /*
     * Only entries supported by unequivocal wording keep the crown.  Everything
     * else above remains Recommended, so competing builds are not mislabeled.
     */
    const bestInSlotByCharacterCategory = Object.freeze({
        "velvet::Blades": "Unnamed Blade",
        "velvet::Rings": "Unnamed Ring",
        "velvet::Women’s Shoes": "Queen Ellis Heels",

        "rokurou::Talismans": "Stoic Idol",
        "rokurou::Rings": "Unnamed Ring",
        "rokurou::Men’s Shoes": "Turbulent Shoes",

        "laphicet::Paper": "Lost Parlance",
        "laphicet::Rings": "Unnamed Ring",
        "laphicet::Men’s Shoes": "Turbulent Shoes",

        "eizen::Bracelets": "Unnamed Bracelet",
        "eizen::Rings": "Unnamed Ring",

        "magilou::Guardians": "Doppelganger",
        "magilou::Earrings": "Lucifer's Pride Earrings",
        "magilou::Rings": "Unnamed Ring",

        "eleanor::Ribbons": "Unnamed Ribbon",
        "eleanor::Rings": "Unnamed Ring",
        "eleanor::Women’s Shoes": "Queen Ellis Heels"
    });

    /* Character-specific source judgements override the shared baseline when needed. */
    const sourceCalloutByCharacterItem = Object.freeze({
        "velvet::Uprising Veil": { key: "build", label: "Velvet post-game carry", icon: "✦" },
        "magilou::Uprising Veil": { key: "caution", label: "Low priority for Magilou", icon: "◌" },
        "rokurou::Summertime Waistcoat": { key: "final", label: "Late-game standout", icon: "★" },
        "eizen::Summertime Waistcoat": { key: "final", label: "Late-game standout", icon: "★" },
        "laphicet::Summertime Waistcoat": { key: "caution", label: "Low priority for Laphicet", icon: "◌" },
        "laphicet::Topaz Waistcoat": { key: "offense", label: "Late-game offensive route", icon: "🔥" },
        "eizen::Topaz Waistcoat": { key: "offense", label: "Late-game offensive route", icon: "🔥" },
        "rokurou::Topaz Waistcoat": { key: "caution", label: "Easy but secondary option", icon: "◌" },
        "laphicet::Reflex Waistcoat": { key: "final", label: "High-stat reflection route", icon: "★" },
        "eizen::Reflex Waistcoat": { key: "build", label: "Situational reflection", icon: "✦" },
        "rokurou::Reflex Waistcoat": { key: "defense", label: "Defensive reflection", icon: "🛡️" },
        "velvet::Queen Ellis Heels": { key: "bis", label: "Best in slot", icon: "👑" },
        "eleanor::Queen Ellis Heels": { key: "bis", label: "Best in slot", icon: "👑" },
        "magilou::Grounded Shoes": { key: "build", label: "Ventite specialist", icon: "✦" },
        "velvet::Grounded Shoes": { key: "build", label: "Ventite specialist", icon: "✦" },
        "eleanor::Grounded Shoes": { key: "build", label: "Ventite specialist", icon: "✦" },
        "magilou::Queen Ellis Heels": { key: "focus", label: "Focus crown route", icon: "◈" }
    });


    function sourceCallout(member, entry) {
        const categoryKey = `${member.id}::${String(entry.category || "")}`;
        const itemName = String(entry.item || "");
        const memberKey = `${member.id}::${itemName}`;
        const routeCallout = sourceCalloutByCharacterItem[memberKey] || sourceCalloutByItem[itemName] || {
            key: "story",
            label: "Story progression step",
            icon: "◆"
        };
        const recommendedItem = recommendedByCharacterCategory[categoryKey];
        const bestItem = bestInSlotByCharacterCategory[categoryKey];

        if (recommendedItem === itemName) {
            const badges = [{ key: "recommended", label: "Recommended", icon: "✓" }];
            if (bestItem === itemName) {
                badges.push({ key: "bis", label: "Best in slot", icon: "👑" });
            }
            return {
                key: bestItem === itemName ? "bis" : "recommended",
                label: bestItem === itemName ? "Recommended · Best in slot" : "Recommended",
                icon: bestItem === itemName ? "👑" : "✓",
                badges: badges,
                detail: `${routeCallout.label} — ${recommendedReasonByCharacterCategory[categoryKey] || "Scelta principale della roadmap."}`
            };
        }

        return {
            key: routeCallout.key,
            label: routeCallout.label,
            icon: routeCallout.icon,
            badges: [routeCallout],
            detail: ""
        };
    }

    function hasCalloutBadge(callout, key) {
        return Boolean(callout && Array.isArray(callout.badges) && callout.badges.some(function(badge) {
            return badge.key === key;
        }));
    }

    function progressionPhase(entry) {
        const checkpoint = String(entry.checkpoint || "").toLowerCase();
        if (phaseFromRarity(entry.rarity) === "Post-game") {
            return { key: "postgame", label: "Post-game route", icon: "👑" };
        }
        if (checkpoint.includes("early game") || checkpoint.includes("starting") || checkpoint.includes("recruitment")) {
            return { key: "early", label: "Early-game route", icon: "①" };
        }
        if (checkpoint.includes("mid game")) {
            return { key: "mid", label: "Mid-game route", icon: "②" };
        }
        if (checkpoint.includes("late game") || checkpoint.includes("optional late")) {
            return { key: "late", label: "Late-game route", icon: "③" };
        }
        if (checkpoint.includes("final")) {
            return { key: "final", label: "Final-route step", icon: "④" };
        }
        if (checkpoint.includes("story reward")) {
            return { key: "story", label: "Story reward", icon: "◆" };
        }
        return { key: "story", label: "Story progression", icon: "◆" };
    }

    function progressionLabel(entry, index, total) {
        const phase = progressionPhase(entry);
        const position = String(index + 1).padStart(2, "0");
        return {
            key: phase.key,
            label: `Step ${position}/${String(total).padStart(2, "0")} · ${phase.label}`,
            icon: phase.icon
        };
    }

    function titleForGroup(group, slotName) {
        const first = group.entries[0] || {};
        if (group.entries.length === 1) {
            return `Noteworthy ${first.category || slotName} · ${first.item || "Oggetto"}`;
        }
        const allPostgame = group.entries.every(function(entry) {
            return phaseFromRarity(entry.rarity) === "Post-game";
        });
        return allPostgame ? `${first.category || slotName} (Post-Game)` : `Noteworthy ${first.category || slotName}`;
    }

    function growthMarkup(data, member) {
        const growth = (data.character_growth || []).find(function(entry) {
            return entry.name === member.name;
        });
        if (!growth || !Array.isArray(growth.level_200)) {
            return "";
        }

        const labels = ["Atk", "Arte Attack", "Def", "Arte Defense", "Focus"];
        const values = growth.level_200.slice(1, 6).map(function(value) { return Number(value) || 0; });
        const ranking = labels.map(function(label, index) { return { label: label, value: values[index] }; }).sort(function(a, b) { return b.value - a.value; });
        const strongest = ranking.slice(0, 2).map(function(entry) {
            return `<span><strong>${escapeHtml(entry.label)}</strong><small>${escapeHtml(entry.value.toFixed(1))} · Lv 200</small></span>`;
        }).join("");
        const weakest = ranking[ranking.length - 1];

        return `
            <div class="dossier-growth-pills">${strongest}</div>
            <p class="dossier-mini-note">Da compensare con l'equip: <strong>${escapeHtml(weakest.label)}</strong> (${escapeHtml(weakest.value.toFixed(1))} a Lv 200).</p>
        `;
    }

    function aiMarkup(member) {
        const ai = member.ai;
        if (Array.isArray(ai.variants)) {
            return `
                <p>${escapeHtml(ai.summary)}</p>
                <div class="dossier-ai-variants">${ai.variants.map(function(variant) {
                    return `
                        <article>
                            <div class="dossier-ai-variant-heading"><h4>${escapeHtml(variant.name)}</h4><span>${escapeHtml(variant.availability)}</span></div>
                            <div class="dossier-strategy">${variant.strategy.map(function(step) { return `<span>${escapeHtml(step)}</span>`; }).join("")}</div>
                            <p><strong>${escapeHtml(variant.mode)}:</strong> ${escapeHtml(variant.skills.join(" · "))}</p>
                            <p class="dossier-mini-note">${escapeHtml(variant.footnote)}</p>
                        </article>
                    `;
                }).join("")}</div>
            `;
        }

        return `
            <p>${escapeHtml(ai.summary)}</p>
            <div class="dossier-strategy">${ai.strategy.map(function(step) { return `<span>${escapeHtml(step)}</span>`; }).join("")}</div>
            <p><strong>${escapeHtml(ai.mode)}:</strong> ${escapeHtml(ai.skills.join(" · "))}</p>
            <p class="dossier-mini-note">${escapeHtml(ai.footnote)}</p>
        `;
    }

    function renderSlot(member, slotName, entries, itemByName) {
        const groups = [];
        const byGroup = new Map();
        entries.forEach(function(entry) {
            const key = String(entry.source_note_group || normalize(entry.item));
            let group = byGroup.get(key);
            if (!group) {
                group = { entries: [], note: "" };
                byGroup.set(key, group);
                groups.push(group);
            }
            group.entries.push(entry);
            if (!group.note && String(entry.source_note || "").trim()) {
                group.note = String(entry.source_note).trim();
            }
        });

        const progressionByEntry = new Map(entries.map(function(entry, index) {
            return [entry, index];
        }));
        const cards = groups.map(function(group) {
            const groupHasBest = group.entries.some(function(entry) {
                return hasCalloutBadge(sourceCallout(member, entry), "bis");
            });
            const groupHasCallout = group.entries.some(function(entry) {
                return Boolean(sourceCallout(member, entry));
            });
            const items = group.entries.map(function(entry) {
                const item = itemByName.get(normalize(entry.item));
                const category = entry.category || (item && item.category) || "Categoria";
                const rarity = entry.rarity || (item && item.rarity) || "—";
                const href = itemHref(member, item, entry);
                const progression = progressionLabel(entry, progressionByEntry.get(entry) || 0, entries.length);
                const callout = sourceCallout(member, entry);
                const calloutBadges = callout && Array.isArray(callout.badges) ? callout.badges : [];
                const calloutMarkup = calloutBadges.length ? `<div class="dossier-item-callout-row">${calloutBadges.map(function(badge) {
                    return `<p class="dossier-item-callout dossier-item-callout-${escapeHtml(badge.key)}">${escapeHtml(badge.icon)} ${escapeHtml(badge.label)}</p>`;
                }).join("")}</div>` : "";
                const calloutDetailMarkup = callout && callout.detail ? `<p class="dossier-item-callout-detail">${escapeHtml(callout.detail)}</p>` : "";
                const calloutClass = calloutBadges.map(function(badge) {
                    return ` dossier-pick-item-${escapeHtml(badge.key)}`;
                }).join("");
                return `
                    <li class="dossier-pick-item dossier-pick-item-${escapeHtml(progression.key)}${calloutClass}">
                        <p class="dossier-progression-badge">${escapeHtml(progression.icon)} ${escapeHtml(progression.label)}</p>
                        ${calloutMarkup}
                        ${calloutDetailMarkup}
                        <p class="dossier-pick-checkpoint">${escapeHtml(entry.checkpoint)}</p>
                        <h4><a href="${escapeHtml(href)}">${escapeHtml(entry.item)}</a></h4>
                        <p class="dossier-pick-meta"><span>${escapeHtml(categoryIcons[category] || "✦")} ${escapeHtml(category)}</span><span>Rarità ${escapeHtml(rarity)}</span><span>${escapeHtml(phaseLabel(rarity))}</span></p>
                    </li>
                `;
            }).join("");
            const note = group.note ? `
                <details class="dossier-source-note" ${groupHasBest ? "open" : ""}>
                    <summary>Perché la guida lo consiglia</summary>
                    <div>
                        <p class="dossier-source-kicker">Nota della guida</p>
                        <h5>${escapeHtml(titleForGroup(group, slotName))}</h5>
                        <p>${escapeHtml(group.note)}</p>
                    </div>
                </details>
            ` : "";
            const groupState = groupHasBest ? "has-best" : (groupHasCallout ? "has-callout" : "");
            return `
                <article class="dossier-pick dossier-pick-group ${escapeHtml(groupState)}">
                    <ul>${items}</ul>
                    ${note}
                </article>
            `;
        }).join("");

        return `
            <section id="slot-${escapeHtml(slugify(slotName))}" class="dossier-slot-panel">
                <header>
                    <div>
                        <p class="dossier-slot-kicker">${escapeHtml(slotIcons[slotName] || "✦")} ${escapeHtml(slotLabels[slotName] || slotName)}</p>
                        <h3>${escapeHtml(slotName === "Shoes" ? "Calzature consigliate" : `${slotName} consigliati`)}</h3>
                    </div>
                    <p>${escapeHtml(slotName === "Weapon" ? "Dove si concentra la statistica offensiva principale del personaggio." : slotName === "Accessory" ? "Lo slot che completa le statistiche o abilita la specializzazione del personaggio." : slotName === "Armor" ? "Protezione, stabilità e statistiche secondarie senza perdere di vista l'offensiva." : slotName === "Rings" ? "Arte Defense, Master Skills e protezione dallo Stun alle difficoltà più alte." : "Focus, Souls e Master Skills: spesso più importanti di quanto il nome dello slot faccia pensare.")}</p>
                </header>
                <div class="dossier-pick-grid">${cards}</div>
            </section>
        `;
    }

    function renderDossier(data, member) {
        const state = spoilerState();
        if (state.enabled && member.stage > state.stage) {
            target.innerHTML = `
                <section class="dossier-locked">
                    <p class="eyebrow">Filtro anti-spoiler attivo</p>
                    <h2>????</h2>
                    <p>Questa scheda appartiene a un alleato non ancora segnato come sbloccato nel tuo progresso locale.</p>
                    <a class="character-dossier-header-link" href="./index.html">Torna alla guida</a>
                </section>
            `;
            return;
        }

        const itemByName = new Map((data.items || []).map(function(item) { return [normalize(item.name), item]; }));
        const entries = (data.recommended_equipment || []).filter(function(entry) { return entry.character === member.name; }).sort(function(a, b) { return (Number(a.order) || 0) - (Number(b.order) || 0); });
        const bySlot = new Map();
        entries.forEach(function(entry) {
            const slotName = String(entry.slot || "Other");
            if (!bySlot.has(slotName)) {
                bySlot.set(slotName, []);
            }
            bySlot.get(slotName).push(entry);
        });
        const slotLinks = slotOrder.filter(function(slotName) { return bySlot.has(slotName); }).map(function(slotName) {
            return `<a href="#slot-${escapeHtml(slugify(slotName))}">${escapeHtml(slotIcons[slotName] || "✦")} ${escapeHtml(slotLabels[slotName] || slotName)}</a>`;
        }).join("");
        const slots = slotOrder.filter(function(slotName) { return bySlot.has(slotName); }).map(function(slotName) {
            return renderSlot(member, slotName, bySlot.get(slotName), itemByName);
        }).join("");
        const otherMembers = members.filter(function(entry) { return !state.enabled || entry.stage <= state.stage; }).map(function(entry) {
            const active = entry.id === member.id ? " is-active" : "";
            return `<a class="dossier-member-switch${active}" href="./character.html?character=${encodeURIComponent(entry.name)}">${escapeHtml(entry.name)}</a>`;
        }).join("");

        document.title = `Tales of Berseria — ${member.name}`;
        target.innerHTML = `
            <nav class="dossier-member-switcher" aria-label="Schede personaggio">${otherMembers}</nav>
            <section class="dossier-hero tone-${escapeHtml(member.tone)}">
                <div class="dossier-hero-copy">
                    <p class="eyebrow">Character dossier</p>
                    <h2>${escapeHtml(member.name)}</h2>
                    <p>${escapeHtml(member.role)}</p>
                    <div class="dossier-hero-actions">
                        <a href="./index.html?character=${encodeURIComponent(member.name)}#catalogo">Apri il catalogo filtrato</a>
                        <a href="./ai.html#ai-${escapeHtml(member.id)}">Preset AI completo</a>
                    </div>
                </div>
                <div class="dossier-hero-portrait"><img src="${escapeHtml(member.image)}" alt="Ritratto di ${escapeHtml(member.name)}" referrerpolicy="no-referrer"></div>
            </section>
            <nav class="dossier-slot-nav" aria-label="Sezioni della scheda">
                <a href="#overview">Panoramica</a>
                <a href="#ai">AI</a>
                <a href="#title">Title</a>
                <a href="#growth">Statistiche</a>
                ${slotLinks}
            </nav>
            <section id="overview" class="dossier-overview-grid">
                <article>
                    <p class="dossier-section-kicker">Focus equip</p>
                    <h3>Che cosa cercare</h3>
                    <p>${escapeHtml(member.equipmentFocus)}</p>
                </article>
                <article id="title">
                    <p class="dossier-section-kicker">Title consigliato</p>
                    <h3>Scelta sicura</h3>
                    <p>${escapeHtml(member.titleAdvice)}</p>
                </article>
                <article id="growth">
                    <p class="dossier-section-kicker">Curva statistiche</p>
                    <h3>Talento naturale</h3>
                    ${growthMarkup(data, member)}
                </article>
            </section>
            <section id="ai" class="dossier-ai-panel">
                <div class="dossier-ai-heading">
                    <div><p class="dossier-section-kicker">Preset AI</p><h3>Configurazione pratica</h3></div>
                    <a href="./ai.html#ai-${escapeHtml(member.id)}">Vedi spiegazione completa →</a>
                </div>
                ${aiMarkup(member)}
            </section>
            <section class="dossier-gear-section">
                <div class="dossier-gear-heading">
                    <p class="dossier-section-kicker">Equipment roadmap</p>
                    <h3>Roadmap lineare dell'equipaggiamento</h3>
                    <p>Ogni pezzo ha un <strong>passo cronologico</strong> e una <strong>funzione pratica estratta dal commento della guida</strong>: early-game carry, route da Focus, opzione difensiva, materiale per Master Skill, specializzazione da endgame e così via. Non sono voti di qualità. Ogni categoria del personaggio ha però <strong>un solo Best in slot generale</strong>, scelto confrontando le frasi più forti della fonte: “più forte”, “preferibile”, “ideale”, “perfetto”, “ultimo” o equivalenti. Le alternative restano visibili quando servono a una build diversa, al farming o a una Master Skill specifica. Le note restano espandibili e collegate agli oggetti.</p>
                </div>
                <div class="dossier-slot-list">${slots}</div>
            </section>
        `;
    }

    function showError() {
        target.innerHTML = `
            <section class="dossier-locked">
                <p class="eyebrow">Errore di caricamento</p>
                <h2>Catalogo non disponibile</h2>
                <p>La scheda personaggio richiede il file locale <code>content/catalogo.json</code>.</p>
                <a class="character-dossier-header-link" href="./index.html">Torna alla guida</a>
            </section>
        `;
    }

    async function init() {
        initializeTheme();
        const member = memberFromQuery();
        try {
            const response = await fetch("./content/catalogo.json", { cache: "no-store" });
            if (!response.ok) {
                throw new Error("Catalogo non disponibile");
            }
            const data = await response.json();
            renderDossier(data, member);
        } catch (error) {
            showError();
        }
    }

    init();
})();
