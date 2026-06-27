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
    const sourceCalloutByItem = Object.freeze({
        "Force Ring": { key: "best-early", label: "Best early", icon: "🌱" },
        "Barrier Ring": { key: "best-early", label: "Best early", icon: "🌱" },
        "Anthro Ring": { key: "mastery", label: "Good Master Skill material", icon: "📘" },
        "Plated Ring": { key: "mastery", label: "Good Master Skill material", icon: "📘" },
        "Unnamed Ring": { key: "bis", label: "Best in slot", icon: "👑" },

        "Stoic Idol": { key: "bis", label: "Best in slot", icon: "👑" },
        "Unnamed Ribbon": { key: "bis", label: "Best in slot", icon: "👑" },
        "Unnamed Blade": { key: "bis", label: "Best in slot", icon: "👑" },
        "Unnamed Daggers": { key: "bis", label: "Best in slot", icon: "👑" },
        "Lost Parlance": { key: "bis", label: "Best in slot", icon: "👑" }
    });

    function sourceCallout(member, entry) {
        return sourceCalloutByItem[entry.item] || null;
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
                const callout = sourceCallout(member, entry);
                return callout && callout.key === "bis";
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
                const calloutMarkup = callout ? `<p class="dossier-item-callout dossier-item-callout-${escapeHtml(callout.key)}">${escapeHtml(callout.icon)} ${escapeHtml(callout.label)}</p>` : "";
                const calloutClass = callout ? ` dossier-pick-item-${escapeHtml(callout.key)}` : "";
                return `
                    <li class="dossier-pick-item dossier-pick-item-${escapeHtml(progression.key)}${calloutClass}">
                        <p class="dossier-progression-badge">${escapeHtml(progression.icon)} ${escapeHtml(progression.label)}</p>
                        ${calloutMarkup}
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
                    <p>Ogni pezzo è mostrato come un <strong>passo della progressione</strong>, ordinato per checkpoint della storia: non è più una classifica generica. I badge speciali compaiono soltanto quando il commento della guida esprime un motivo preciso, come <strong>Best early</strong> o <strong>Good Master Skill material</strong>. <strong>Best in slot</strong> resta riservato a un solo pezzo della categoria per questo personaggio, e solo quando la fonte lo giudica in modo inequivocabile. Le note restano espandibili e collegate agli oggetti.</p>
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
