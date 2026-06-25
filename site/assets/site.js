(function() {
    "use strict";

    const guide = document.getElementById("guide");
    const toc = document.getElementById("toc");
    const search = document.getElementById("search");
    const searchStatus = document.getElementById("search-status");
    const themeToggle = document.getElementById("theme-toggle");
    const storageKey = "tob-equipment-guide-theme";
    const spoilerModeKey = "tob-equipment-guide-spoiler-mode";
    const spoilerProgressKey = "tob-equipment-guide-spoiler-progress";
    const statLabels = ["Atk", "A.Atk", "Def", "A.Def", "Focus"];

    const partyMembers = Object.freeze([
        {
            id: "velvet",
            name: "Velvet",
            stage: 0,
            tone: "velvet",
            role: "Attaccante in prima linea · combo, Stun e Therion Form",
            battleAdvice: "Se la affidi al controllo automatico, falla puntare un nemico resistente: la sua combo ha il tempo di finire e può entrare in Therion Form. Questa scelta non elimina gli spostamenti: se il bersaglio è lontano, Velvet dovrà comunque raggiungerlo.",
            equipmentAdvice: "Blades privilegiano Atk; Belts, il suo Accessory, possono aggiungere Focus per lo Stun. Su Armor, Rings e Footwear conserva prima le Master Skills che non hai ancora appreso.",
            categories: ["Blades", "Belts", "Women’s Armor", "Rings", "Shoes", "Women’s Shoes"],
            tip: "AI: Target Strong Enemies · Be Aggressive",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Velvet_Cut-in_%28ToB%29.png"
        },
        {
            id: "rokurou",
            name: "Rokurou",
            stage: 1,
            tone: "rokurou",
            role: "Duellante in prima linea · Souls, counter e colpi mirati",
            battleAdvice: "Target Enemy with Most Souls fa scegliere all’AI il bersaglio con più Souls. Non garantisce che resti sempre lontano da Velvet, ma evita una priorità casuale. Defense Only privilegia schivate e sicurezza quando il gruppo è sotto pressione.",
            equipmentAdvice: "Cerca Atk su Short Swords e Talismans; Armor e Footwear servono a non farlo cadere mentre resta vicino al nemico. Impara prima ogni Master Skill nuova.",
            categories: ["Short Swords", "Talismans", "Men’s Armor", "Rings", "Shoes", "Men’s Shoes"],
            tip: "AI: Most Souls · Defense Only",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Rokurou_Cut-in_%28ToB%29.png"
        },
        {
            id: "laphicet",
            name: "Laphicet",
            stage: 2,
            tone: "laphicet",
            role: "Caster di supporto · magie rapide, cure e controllo",
            battleAdvice: "Lascialo a distanza con poche Malak Artes affidabili: Kaleidos Ray, Blessed Drops, Void Mire e Dark Fangs. Una lista corta riduce i cast lunghi e le occasioni in cui l’AI viene interrotta.",
            equipmentAdvice: "Paper e Bags favoriscono A.Atk. A.Def e Focus sono utili quando viene preso di mira; prima di sostituire un pezzo, impara la sua Master Skill.",
            categories: ["Paper", "Bags", "Men’s Armor", "Rings", "Shoes", "Men’s Shoes"],
            tip: "AI: Range · 4 Malak Artes",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Laphicet_Cut-in_%28ToB%29.png"
        },
        {
            id: "eizen",
            name: "Eizen",
            stage: 3,
            tone: "eizen",
            role: "Combattente flessibile · pugni durante la storia, magia del vento più tardi",
            battleAdvice: "Usa Fist Bruiser durante la storia. Passa a Wind Master solo dopo avere Coercion, Last Throes, Stone Lance e Hell Gate: prima di allora la rotazione a distanza non è ancora completa.",
            equipmentAdvice: "Nel set Fist Bruiser cerca Atk e Focus. Nel set Wind Master conta di più A.Atk, ma mantieni Def e A.Def: Eizen può comunque ricevere pressione.",
            categories: ["Bracelets", "Pendants", "Men’s Armor", "Rings", "Shoes", "Men’s Shoes"],
            tip: "AI: Fist prima · Wind Master dopo",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Eizen_Cut-in_%28ToB%29.png"
        },
        {
            id: "magilou",
            name: "Magilou",
            stage: 4,
            tone: "magilou",
            role: "Caster offensiva · magie rapide da lontano",
            battleAdvice: "L’AI è più affidabile con Aqua Split e Blood Moon; Crown Fire è opzionale. Tenere poche Malak Artes abbrevia i cast e riduce le aperture in cui può essere interrotta.",
            equipmentAdvice: "Guardians ed Earrings favoriscono A.Atk. A.Def è utile perché un personaggio che lancia magie colpito durante un cast perde più valore di pochi punti aggiuntivi di danno.",
            categories: ["Guardians", "Earrings", "Women’s Armor", "Rings", "Shoes", "Women’s Shoes"],
            tip: "AI: Range · Aqua Split / Blood Moon",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Magilou_Cut-in_%28ToB%29.png"
        },
        {
            id: "eleanor",
            name: "Eleanor",
            stage: 5,
            tone: "eleanor",
            role: "Combattente ibrida · lancia a distanza ravvicinata e Malak Artes",
            battleAdvice: "L’AI lavora meglio vicino al bersaglio con una rotazione corta. Flame Beast e Maelstrom restano le Malak Artes principali; le Artes che spingono troppo lontano il nemico restano fuori.",
            equipmentAdvice: "Scegli una priorità per volta: Atk per le Martial Artes, A.Atk per Flame Beast e Maelstrom. Non distribuire le statistiche senza uno scopo.",
            categories: ["Spears", "Ribbons", "Women’s Armor", "Rings", "Shoes", "Women’s Shoes"],
            tip: "AI: Close Combat · Flame Beast",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Eleanor_Cut-in_%28ToB%29.png"
        }
    ]);

    const categorySlots = Object.freeze({
        "Blades": "Weapon",
        "Short Swords": "Weapon",
        "Paper": "Weapon",
        "Bracelets": "Weapon",
        "Guardians": "Weapon",
        "Spears": "Weapon",
        "Belts": "Accessory",
        "Talismans": "Accessory",
        "Bags": "Accessory",
        "Pendants": "Accessory",
        "Earrings": "Accessory",
        "Ribbons": "Accessory",
        "Men’s Armor": "Armor",
        "Women’s Armor": "Armor",
        "Rings": "Ring",
        "Shoes": "Footwear universale",
        "Men’s Shoes": "Footwear",
        "Women’s Shoes": "Footwear"
    });

    let spoilerFilterEnabled = true;
    let unlockedStage = 0;
    let catalogueData = null;
    let cataloguePendingCharacter = "";
    let cataloguePendingCategory = "";
    let catalogueHashHandlerBound = false;

    function slugify(value) {
        return String(value || "")
            .toLocaleLowerCase("it-IT")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "");
    }

    function escapeHtml(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function normalizeText(value) {
        return String(value || "")
            .toLocaleLowerCase("it-IT")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/\s+/g, " ")
            .trim();
    }

    function setTheme(theme) {
        document.documentElement.dataset.theme = theme;
        themeToggle.textContent = (theme === "dark") ? "Tema chiaro" : "Tema scuro";
        themeToggle.setAttribute("aria-label", (theme === "dark") ? "Attiva il tema chiaro" : "Attiva il tema scuro");
    }

    function initializeTheme() {
        const saved = window.localStorage.getItem(storageKey);
        const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        setTheme(saved || (dark ? "dark" : "light"));

        themeToggle.addEventListener("click", function() {
            const next = (document.documentElement.dataset.theme === "dark") ? "light" : "dark";
            window.localStorage.setItem(storageKey, next);
            setTheme(next);
        });
    }

    function initializeSpoilerState() {
        const savedMode = window.localStorage.getItem(spoilerModeKey);
        const savedProgress = Number(window.localStorage.getItem(spoilerProgressKey));
        spoilerFilterEnabled = savedMode !== "off";
        unlockedStage = Number.isInteger(savedProgress) ? Math.max(0, Math.min(partyMembers.length - 1, savedProgress)) : 0;
    }

    function initializeCatalogueDeepLink() {
        const params = new URLSearchParams(window.location.search);
        cataloguePendingCharacter = params.get("character") || "";
        cataloguePendingCategory = params.get("category") || "";
    }

    function catalogueLink(member, category) {
        const params = new URLSearchParams();
        if (member && member.name) {
            params.set("character", member.name);
        }
        if (category) {
            params.set("category", slugify(category));
        }
        const query = params.toString();
        return `./index.html${query ? `?${query}` : ""}#catalogo`;
    }

    function scrollToGuideAnchor() {
        const rawHash = window.location.hash.slice(1);
        const id = rawHash ? decodeURIComponent(rawHash) : "";

        if (!id || id.startsWith("item-")) {
            return;
        }

        const target = document.getElementById(id);
        if (!target) {
            return;
        }

        window.requestAnimationFrame(function() {
            target.scrollIntoView({ block: "start", behavior: "auto" });
        });
    }

    function saveSpoilerState() {
        window.localStorage.setItem(spoilerModeKey, spoilerFilterEnabled ? "on" : "off");
        window.localStorage.setItem(spoilerProgressKey, String(unlockedStage));
    }

    function getMemberByName(name) {
        const key = normalizeText(name);
        return partyMembers.find(function(member) {
            return normalizeText(member.name) === key;
        }) || null;
    }

    function memberIsVisible(member) {
        return !spoilerFilterEnabled || member.stage <= unlockedStage;
    }

    function visibleMembers() {
        return partyMembers.filter(memberIsVisible);
    }

    function splitCharacterList(value) {
        return String(value || "")
            .split(/[·/;,]/)
            .map(function(entry) { return entry.trim(); })
            .filter(Boolean);
    }

    function isNamedCharacterVisible(name) {
        const member = getMemberByName(name);
        return !member || memberIsVisible(member);
    }

    function itemIsVisible(item) {
        if (!spoilerFilterEnabled) {
            return true;
        }

        const users = splitCharacterList(item.character);
        if (!users.length || users.includes("All")) {
            return true;
        }

        return users.some(isNamedCharacterVisible);
    }

    function categoryIsVisible(category) {
        if (!spoilerFilterEnabled) {
            return true;
        }

        const users = splitCharacterList(category.character);
        if (!users.length || users.includes("All")) {
            return true;
        }

        return users.some(isNamedCharacterVisible);
    }

    function applySpoilerMask() {
        guide.querySelectorAll("[data-spoiler-stage]").forEach(function(node) {
            const stage = Number(node.dataset.spoilerStage);
            node.hidden = spoilerFilterEnabled && Number.isFinite(stage) && stage > unlockedStage;
        });
    }

    function wrapTables(root) {
        root.querySelectorAll("table").forEach(function(table) {
            if (table.parentElement && table.parentElement.classList.contains("table-wrap")) {
                return;
            }

            const wrapper = document.createElement("div");
            wrapper.className = "table-wrap";
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        });
    }

    function buildTableOfContents() {
        const headings = Array.from(guide.querySelectorAll("h2, h3, h4"));
        const used = new Map();
        const fragment = document.createDocumentFragment();

        headings.forEach(function(heading) {
            const base = heading.id || slugify(heading.textContent) || "sezione";
            const count = used.get(base) || 0;
            const id = count ? `${base}-${count + 1}` : base;
            used.set(base, count + 1);
            heading.id = heading.id || id;

            const link = document.createElement("a");
            link.href = `#${heading.id}`;
            link.textContent = heading.textContent;
            link.className = `toc-level-${heading.tagName.slice(1)}`;
            fragment.appendChild(link);
        });

        toc.replaceChildren(fragment);
    }

    function enhancedStats(stats) {
        const values = Array.isArray(stats) ? stats.map(function(value) {
            return Number(value) || 0;
        }) : [0, 0, 0, 0, 0];
        const total = values.reduce(function(sum, value) { return sum + value; }, 0);

        if (total <= 0) {
            return values;
        }

        return values.map(function(value) {
            return value + Math.floor((100 * value) / total);
        });
    }

    function formatStats(stats) {
        const values = Array.isArray(stats) ? stats : [0, 0, 0, 0, 0];
        const fragments = values.map(function(value, index) {
            const n = Number(value) || 0;
            return n > 0 ? `${statLabels[index]} ${n}` : "";
        }).filter(Boolean);
        return fragments.length ? fragments.join(" · ") : "—";
    }

    function itemId(item) {
        return `item-${slugify(item.category_id)}-${item.rarity}-${slugify(item.name)}`;
    }

    function allText(item) {
        return normalizeText([
            item.name,
            item.max_name,
            item.category,
            item.character,
            item.phase,
            item.rarity,
            item.master_skill,
            item.enhancement_bonus,
            item.main_ingredient,
            item.rare_drop,
            item.acquisition,
            formatStats(item.stats),
            formatStats(item.stats_plus10)
        ].join(" "));
    }

    function getAcquisition(item) {
        const source = String(item.acquisition || "").trim();
        const rare = String(item.rare_drop || "").trim();

        if (source && source !== "—") {
            return source;
        }

        if (rare && rare !== "—" && rare !== "N/A") {
            return `Rare drop: ${rare}`;
        }

        return "Fonte non registrata";
    }

    function sourceBadge(item) {
        const kind = String(item.source_kind || "").trim();

        if (kind === "rare_drop") {
            return "Rare drop";
        }
        if (kind === "common_drop") {
            return "Common drop";
        }
        if (kind === "postgame_enemy_drop") {
            return "Enemy drop post-game";
        }
        if (kind === "postgame_chest_or_drop") {
            return "Post-game";
        }
        if (kind === "chest_or_story") {
            return "Chest / storia";
        }
        return "Indicazione";
    }

    function renderCharacterCards() {
        const target = guide.querySelector("#character-cards-dynamic");
        if (!target) {
            return;
        }

        const unlocked = visibleMembers();
        const hasHiddenMembers = spoilerFilterEnabled && unlocked.length < partyMembers.length;

        function renderMember(member) {
            const chips = member.categories.map(function(category) {
                const href = catalogueLink(member, category);
                const slot = categorySlots[category] || "Categoria Equipment";
                return `<a href="${escapeHtml(href)}" data-catalogue-link title="Apri ${escapeHtml(category)} (${escapeHtml(slot)}) nel catalogo filtrato per ${escapeHtml(member.name)}" aria-label="Apri ${escapeHtml(category)}, ${escapeHtml(slot)}, nel catalogo filtrato per ${escapeHtml(member.name)}">${escapeHtml(category)}</a>`;
            }).join("");
            const catalogHref = catalogueLink(member, "");
            const aiHref = `./ai.html#ai-${escapeHtml(member.id)}`;

            return `
                <article class="character-card tone-${escapeHtml(member.tone)}">
                    <img class="character-art" src="${escapeHtml(member.image)}" alt="" loading="lazy" referrerpolicy="no-referrer" aria-hidden="true">
                    <div class="character-card-content">
                        <div class="character-card-header">
                            <div class="character-portrait">
                                <img src="${escapeHtml(member.image)}" alt="Ritratto di ${escapeHtml(member.name)}" loading="lazy" referrerpolicy="no-referrer">
                            </div>
                            <div>
                                <p class="character-kicker">Equipment e comportamento automatico</p>
                                <h3>${escapeHtml(member.name)}</h3>
                                <p class="character-role">${escapeHtml(member.role)}</p>
                            </div>
                        </div>
                        <p class="character-summary"><strong>In battaglia:</strong> ${escapeHtml(member.battleAdvice)}</p>
                        <p class="character-equipment-focus"><strong>Equipment:</strong> ${escapeHtml(member.equipmentAdvice)}</p>
                        <div class="character-category-list" aria-label="Categorie utilizzabili da ${escapeHtml(member.name)}">${chips}</div>
                        <div class="character-card-footer">
                            <span class="character-card-tip">★ ${escapeHtml(member.tip)}</span>
                            <div class="character-card-actions">
                                <a class="character-card-action" href="${escapeHtml(catalogHref)}">Vedi tutti gli Item <span aria-hidden="true">→</span></a>
                                <a class="character-card-action" href="${aiHref}">Preset AI <span aria-hidden="true">→</span></a>
                            </div>
                        </div>
                    </div>
                </article>
            `;
        }

        const cards = unlocked.map(renderMember);
        if (hasHiddenMembers) {
            cards.push(`
                <article class="character-card locked-character-card" aria-label="Personaggio non ancora sbloccato">
                    <div class="locked-character-content">
                        <div class="locked-silhouette" aria-hidden="true"><span>🔒</span></div>
                        <p class="character-kicker">Filtro anti-spoiler attivo</p>
                        <h3>???</h3>
                        <p>Questa scheda non mostra nome, avatar, ruolo né categorie finché non scegli di aggiornare il tuo progresso.</p>
                        <button class="character-card-action" type="button" data-advance-party>Ho sbloccato un nuovo alleato <span aria-hidden="true">→</span></button>
                    </div>
                </article>
            `);
        }

        target.innerHTML = `
            <div class="character-toolbar">
                <label class="spoiler-toggle" for="spoiler-filter">
                    <input id="spoiler-filter" type="checkbox" ${spoilerFilterEnabled ? "checked" : ""}>
                    <span class="spoiler-toggle-control" aria-hidden="true"></span>
                    <span class="spoiler-copy"><strong>Filtro anti-spoiler</strong><small>Nasconde automaticamente i personaggi e i dati che non hai ancora incontrato.</small></span>
                </label>
                <div class="character-progress" aria-label="Gestione del progresso senza spoiler">
                    <span class="character-progress-count">Progresso salvato nel browser</span>
                    <button class="character-action" type="button" data-advance-party ${unlocked.length >= partyMembers.length ? "disabled" : ""}>Ho sbloccato un alleato</button>
                    <button class="character-action" type="button" data-reset-party>Ripristina</button>
                </div>
            </div>
            <div class="character-grid">${cards.join("")}</div>
            <div class="character-help">
                <div><strong>Ruolo spiegato</strong>Ogni scheda dice che cosa fa l’alleato, perché il preset automatico usa quelle scelte e quali statistiche cercare per prime.</div>
                <div><strong>Collegamenti diretti</strong>Ogni chip apre la categoria esatta già filtrata. <strong>Vedi tutti gli Item</strong> mostra tutte le categorie utilizzabili; Shoes e la variante maschile o femminile sono alternative dello stesso slot Footwear.</div>
                <div><strong>Nessuno spoiler</strong>Finché il filtro è attivo, personaggi, categorie, preset automatici e Item futuri restano esclusi da schede, ricerca e catalogo.</div>
            </div>
        `;

        if (target.dataset.eventsBound === "true") {
            return;
        }
        target.dataset.eventsBound = "true";

        target.addEventListener("error", function(event) {
            if (event.target && event.target.matches(".character-portrait img")) {
                event.target.classList.add("portrait-unavailable");
                event.target.setAttribute("aria-hidden", "true");
            }
        }, true);

        target.addEventListener("change", function(event) {
            if (event.target && event.target.id === "spoiler-filter") {
                spoilerFilterEnabled = event.target.checked;
                saveSpoilerState();
                refreshSpoilerSensitiveViews();
            }
        });

        target.addEventListener("click", function(event) {
            const advance = event.target.closest("[data-advance-party]");
            const reset = event.target.closest("[data-reset-party]");

            if (advance) {
                unlockedStage = Math.min(partyMembers.length - 1, unlockedStage + 1);
                saveSpoilerState();
                refreshSpoilerSensitiveViews();
                return;
            }

            if (reset) {
                unlockedStage = 0;
                spoilerFilterEnabled = true;
                saveSpoilerState();
                refreshSpoilerSensitiveViews();
            }
        });
    }

    function refreshSpoilerSensitiveViews() {
        applySpoilerMask();
        renderCharacterCards();
        if (catalogueData) {
            renderCatalogue(catalogueData);
            renderReferenceCards(catalogueData);
        }
    }

    function resolveItemLinks(data) {
        const lookup = new Map();

        data.items.forEach(function(item) {
            const key = normalizeText(item.name);
            if (!lookup.has(key)) {
                lookup.set(key, item);
            }
        });

        guide.querySelectorAll("[data-item-ref]").forEach(function(link) {
            const item = lookup.get(normalizeText(link.dataset.itemRef));

            if (!item || !itemIsVisible(item)) {
                link.classList.add("item-link-missing");
                link.title = item ? "Nascosto dal filtro anti-spoiler" : "Scheda non trovata nel catalogo";
                link.removeAttribute("href");
                return;
            }

            link.href = `#${itemId(item)}`;
            link.dataset.catalogItem = itemId(item);
            link.classList.remove("item-link-missing");
            link.removeAttribute("title");
        });
    }

    function renderReferenceCards(data) {
        const target = guide.querySelector("#reference-cards-dynamic");
        if (!target) {
            return;
        }

        if (!data || data.complete !== true || !Array.isArray(data.items)) {
            target.innerHTML = "<p class=\"muted\">Le schede rapide saranno disponibili dopo la creazione del catalogo locale completo.</p>";
            return;
        }

        const entries = (Array.isArray(data.reference_cards) ? data.reference_cards : []).filter(function(entry) {
            return !spoilerFilterEnabled || splitCharacterList(entry.character).some(isNamedCharacterVisible) || !entry.character || String(entry.character).includes("All");
        });
        const itemByKey = new Map(data.items.map(function(item) {
            return [`${item.category_id}|${item.rarity}|${normalizeText(item.name)}`, item];
        }));

        if (!entries.length) {
            target.innerHTML = "<p class=\"muted\">Le schede rapide degli alleati non ancora sbloccati sono nascoste dal filtro anti-spoiler.</p>";
            return;
        }

        target.innerHTML = entries.map(function(entry) {
            const item = itemByKey.get(`${entry.category_id}|${entry.rarity}|${normalizeText(entry.name)}`);
            const href = item ? `#${itemId(item)}` : "#catalogo";
            const title = item ? item.name : entry.name;
            const phase = entry.phase || (item && item.phase) || "Progressione";
            const category = entry.category || (item && item.category) || "Equipment";
            const character = entry.character || (item && item.character) || "";

            return `
                <article class="noteworthy-card">
                    <p class="noteworthy-meta">${escapeHtml(category)}${character ? ` · ${escapeHtml(character)}` : ""} · ${escapeHtml(phase)} · Rarity ${escapeHtml(entry.rarity || "—")}</p>
                    <h4><a href="${escapeHtml(href)}">${escapeHtml(title)}</a></h4>
                    <p>${escapeHtml(entry.reason || "Scheda di confronto: verifica statistiche, Master Skill e Enhancement Bonus.")}</p>
                </article>
            `;
        }).join("");
    }

    function renderCatalogue(data) {
        const target = guide.querySelector("#catalogo-dinamico");
        if (!target) {
            return;
        }

        if (!data || data.complete !== true || !Array.isArray(data.items) || !data.items.length) {
            target.innerHTML = `
                <div class="callout warning">
                    <h3>Catalogo non ancora materializzato</h3>
                    <p>Questa copia locale non contiene ancora il catalogo completo. Al primo deploy, GitHub Actions lo materializza, lo valida e lo salva nel repository prima di pubblicare il sito.</p>
                </div>
            `;
            return;
        }

        const categories = (Array.isArray(data.categories) ? data.categories : []).filter(categoryIsVisible);
        const categoryOptions = categories.map(function(category) {
            return `<option value="${escapeHtml(category.id)}">${escapeHtml(category.label)}</option>`;
        }).join("");
        const characters = visibleMembers().map(function(member) { return member.name; });
        const characterOptions = characters.map(function(character) {
            return `<option value="${escapeHtml(character)}">${escapeHtml(character)}</option>`;
        }).join("") + "<option value=\"All\">Solo universali (Rings/Shoes)</option>";

        target.innerHTML = `
            <div class="catalog-toolbar">
                <label for="catalog-search">Cerca nel catalogo</label>
                <input id="catalog-search" type="search" placeholder="Es. Brillante, Orc Kong, Atk, Adamantine" autocomplete="off">
                <label for="catalog-character">Personaggio</label>
                <select id="catalog-character"><option value="">Tutti visibili</option>${characterOptions}</select>
                <label for="catalog-category">Categoria</label>
                <select id="catalog-category"><option value="">Tutte le categorie visibili</option>${categoryOptions}</select>
                <label for="catalog-phase">Periodo</label>
                <select id="catalog-phase"><option value="">Main game e post-game</option><option value="Main game">Main game</option><option value="Post-game">Post-game</option></select>
                <label for="catalog-rarity">Rarity</label>
                <select id="catalog-rarity"><option value="">Tutte</option>${Array.from({ length: 21 }, function(_, i) { return `<option value="${i + 1}">${i + 1}</option>`; }).join("")}</select>
                <p id="catalog-status" class="catalog-status">${data.items.length} Item · ${categories.length} categorie visibili · dati locali.</p>
            </div>
            <div id="catalog-results"></div>
        `;

        const results = target.querySelector("#catalog-results");
        const query = target.querySelector("#catalog-search");
        const character = target.querySelector("#catalog-character");
        const category = target.querySelector("#catalog-category");
        const phase = target.querySelector("#catalog-phase");
        const rarity = target.querySelector("#catalog-rarity");
        const status = target.querySelector("#catalog-status");

        if (cataloguePendingCharacter && characters.includes(cataloguePendingCharacter)) {
            character.value = cataloguePendingCharacter;
        }
        if (cataloguePendingCategory && categories.some(function(entry) { return entry.id === cataloguePendingCategory; })) {
            category.value = cataloguePendingCategory;
        }
        cataloguePendingCharacter = "";
        cataloguePendingCategory = "";

        function renderRows() {
            const queryText = normalizeText(query.value);
            const filters = {
                character: character.value,
                category: category.value,
                phase: phase.value,
                rarity: rarity.value
            };

            const matching = data.items.filter(function(item) {
                if (!itemIsVisible(item)) {
                    return false;
                }
                if (filters.character) {
                    const users = splitCharacterList(item.character);
                    const universal = users.includes("All");
                    if (filters.character === "All") {
                        if (!universal) {
                            return false;
                        }
                    } else if (!universal && !users.includes(filters.character)) {
                        return false;
                    }
                }
                if (filters.category && item.category_id !== filters.category) {
                    return false;
                }
                if (filters.phase && item.phase !== filters.phase) {
                    return false;
                }
                if (filters.rarity && String(item.rarity) !== filters.rarity) {
                    return false;
                }
                return !queryText || allText(item).includes(queryText);
            });

            const byCategory = new Map();
            matching.forEach(function(item) {
                if (!byCategory.has(item.category_id)) {
                    byCategory.set(item.category_id, []);
                }
                byCategory.get(item.category_id).push(item);
            });

            results.innerHTML = categories.map(function(cat) {
                const rows = byCategory.get(cat.id) || [];
                if (!rows.length) {
                    return "";
                }
                const body = rows.map(function(item) {
                    const base = Array.isArray(item.stats) ? item.stats : [0, 0, 0, 0, 0];
                    const plusTen = Array.isArray(item.stats_plus10) && item.stats_plus10.length === 5
                        ? item.stats_plus10 : enhancedStats(base);
                    const itemAnchor = itemId(item);
                    const acquisition = getAcquisition(item);
                    return `
                        <tr id="${escapeHtml(itemAnchor)}" data-catalog-row>
                            <td>R${escapeHtml(item.rarity)}</td>
                            <td><strong>${escapeHtml(item.name)}</strong><br><small>${escapeHtml(item.max_name || "—")}</small></td>
                            <td><span class="phase-badge">${escapeHtml(item.phase || "—")}</span></td>
                            <td>${escapeHtml(formatStats(base))}</td>
                            <td>${escapeHtml(formatStats(plusTen))}</td>
                            <td>${escapeHtml(item.master_skill || "—")}</td>
                            <td>${escapeHtml(item.enhancement_bonus || "—")}</td>
                            <td>${escapeHtml(item.main_ingredient || "—")}</td>
                            <td><span class="source-badge">${escapeHtml(sourceBadge(item))}</span><br><small>${escapeHtml(acquisition)}</small></td>
                        </tr>
                    `;
                }).join("");

                return `
                    <details class="catalog-category" open>
                        <summary><span>${escapeHtml(cat.label)}</span><small>${escapeHtml(cat.slot)} · ${escapeHtml(cat.character)} · ${rows.length} Item</small></summary>
                        <div class="table-wrap"><table class="catalog-table"><thead><tr><th>Rarity</th><th>Item<br><small>nome a +10</small></th><th>Periodo</th><th>Base</th><th>+10</th><th>Master Skill</th><th>Enhancement Bonus</th><th>Main Ingredient</th><th>Provenienza</th></tr></thead><tbody>${body}</tbody></table></div>
                    </details>
                `;
            }).join("") || "<p class=\"muted\">Nessun Item visibile soddisfa questi filtri.</p>";

            status.textContent = `${matching.length} Item trovati · ${categories.length} categorie visibili.${spoilerFilterEnabled ? " Filtro anti-spoiler attivo." : ""}`;
            wrapTables(results);
            revealHashTarget();
        }

        function revealHashTarget() {
            const id = window.location.hash.slice(1);
            if (!id || !id.startsWith("item-")) {
                return;
            }

            const targetNode = document.getElementById(id);
            if (!targetNode) {
                const hasActiveFilter = Boolean(query.value || character.value || category.value || phase.value || rarity.value);
                if (hasActiveFilter) {
                    query.value = "";
                    character.value = "";
                    category.value = "";
                    phase.value = "";
                    rarity.value = "";
                    renderRows();
                }
                return;
            }

            const parent = targetNode.closest("details");
            if (parent) {
                parent.open = true;
            }
            window.setTimeout(function() {
                targetNode.scrollIntoView({ block: "center" });
            }, 0);
        }

        [query, character, category, phase, rarity].forEach(function(control) {
            control.addEventListener("input", renderRows);
            control.addEventListener("change", renderRows);
        });

        renderRows();
        resolveItemLinks(data);

        if (!catalogueHashHandlerBound) {
            catalogueHashHandlerBound = true;
            window.addEventListener("hashchange", function() {
                if (catalogueData) {
                    renderCatalogue(catalogueData);
                }
                scrollToGuideAnchor();
            });
        }
    }

    function filterGuide(queryText) {
        const term = normalizeText(queryText);
        const blocks = Array.from(guide.querySelectorAll("section"));

        if (!term) {
            blocks.forEach(function(block) { block.classList.remove("is-filtered-out"); });
            searchStatus.textContent = "";
            return;
        }

        let count = 0;
        blocks.forEach(function(block) {
            const visible = normalizeText(block.textContent).includes(term);
            block.classList.toggle("is-filtered-out", !visible);
            if (visible) {
                count += 1;
            }
        });
        searchStatus.textContent = `${count} sezioni pertinenti.`;
    }

    function showError() {
        guide.innerHTML = `
            <section class="callout warning">
                <h2>Impossibile aprire il contenuto locale</h2>
                <p>Apri il sito tramite GitHub Pages oppure avvialo con un server statico. Il file richiesto è <code>content/guide.html</code>.</p>
            </section>
        `;
    }

    function loadJson() {
        return fetch("./content/catalogo.json", { cache: "no-store" })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error("Catalogo non disponibile");
                }
                return response.json();
            })
            .catch(function() { return null; });
    }

    function loadGuide() {
        fetch("./content/guide.html", { cache: "no-store" })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error("Guida non disponibile");
                }
                return response.text();
            })
            .then(function(html) {
                guide.innerHTML = html;
                wrapTables(guide);
                buildTableOfContents();
                applySpoilerMask();
                renderCharacterCards();
                search.addEventListener("input", function() { filterGuide(search.value); });
                return loadJson();
            })
            .then(function(data) {
                catalogueData = data;
                renderCatalogue(data);
                renderReferenceCards(data);
                scrollToGuideAnchor();
            })
            .catch(showError);
    }

    initializeTheme();
    initializeSpoilerState();
    initializeCatalogueDeepLink();
    loadGuide();
}());
