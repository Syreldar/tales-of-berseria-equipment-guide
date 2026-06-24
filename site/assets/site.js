(function() {
    "use strict";

    const guide = document.getElementById("guide");
    const toc = document.getElementById("toc");
    const search = document.getElementById("search");
    const searchStatus = document.getElementById("search-status");
    const themeToggle = document.getElementById("theme-toggle");
    const storageKey = "tob-equipment-guide-theme";
    const statLabels = ["Atk", "A.Atk", "Def", "A.Def", "Focus"];

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

    function normalizeText(value) {
        return String(value || "")
            .toLocaleLowerCase("it-IT")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/\s+/g, " ")
            .trim();
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
        const text = normalizeText(getAcquisition(item));

        if (text.includes("chest")) {
            return "Chest";
        }

        if (text.includes("shop")) {
            return "Shop";
        }

        if (text.includes("common drop")) {
            return "Common drop";
        }

        if (item.rare_drop && item.rare_drop !== "—" && item.rare_drop !== "N/A") {
            return "Rare drop";
        }

        return "Story / altro";
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

            if (!item) {
                link.classList.add("item-link-missing");
                link.title = "Scheda non trovata nel catalogo";
                return;
            }

            link.href = `#${itemId(item)}`;
            link.dataset.catalogItem = itemId(item);
        });
    }

    function renderNoteworthy(data) {
        const target = guide.querySelector("#noteworthy-dynamic");
        if (!target) {
            return;
        }

        const entries = Array.isArray(data.noteworthy) ? data.noteworthy : [];
        const itemByKey = new Map(data.items.map(function(item) {
            return [`${item.category_id}|${item.rarity}|${normalizeText(item.name)}`, item];
        }));

        if (!entries.length) {
            target.innerHTML = "<p class=\"muted\">Le note di progressione sono incluse nelle schede disponibili nel catalogo. Usa il filtro <strong>Main game</strong> per seguire l’ordine di acquisizione.</p>";
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
                    <p>${escapeHtml(entry.reason || "Item notevole per statistiche, Master Skill o Enhancement Bonus.")}</p>
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
                    <h3>Catalogo non disponibile in questa copia</h3>
                    <p>Il repository genera il catalogo locale durante la pubblicazione e blocca il deploy se mancano categorie, Item o fonti essenziali. Apri la versione pubblicata dopo che il workflow ha terminato.</p>
                </div>
            `;
            return;
        }

        const categories = Array.isArray(data.categories) ? data.categories : [];
        const categoryItems = new Map();
        data.items.forEach(function(item) {
            const key = item.category_id || "other";
            if (!categoryItems.has(key)) {
                categoryItems.set(key, []);
            }
            categoryItems.get(key).push(item);
        });

        const categoryOptions = categories.map(function(category) {
            return `<option value="${escapeHtml(category.id)}">${escapeHtml(category.label)}</option>`;
        }).join("");
        const characters = ["Velvet", "Rokurou", "Laphicet", "Eizen", "Magilou", "Eleanor", "All"];
        const characterOptions = characters.map(function(character) {
            return `<option value="${escapeHtml(character)}">${escapeHtml(character)}</option>`;
        }).join("");

        target.innerHTML = `
            <div class="catalog-toolbar">
                <label for="catalog-search">Cerca nel catalogo</label>
                <input id="catalog-search" type="search" placeholder="Es. Brillante, Orc Kong, Atk, Adamantine" autocomplete="off">
                <label for="catalog-character">Personaggio</label>
                <select id="catalog-character"><option value="">Tutti</option>${characterOptions}</select>
                <label for="catalog-category">Categoria</label>
                <select id="catalog-category"><option value="">Tutte le categorie</option>${categoryOptions}</select>
                <label for="catalog-phase">Periodo</label>
                <select id="catalog-phase"><option value="">Main game e post-game</option><option value="Main game">Main game</option><option value="Post-game">Post-game</option></select>
                <label for="catalog-rarity">Rarity</label>
                <select id="catalog-rarity"><option value="">Tutte</option>${Array.from({ length: 21 }, function(_, i) { return `<option value="${i + 1}">${i + 1}</option>`; }).join("")}</select>
                <p id="catalog-status" class="catalog-status">${data.items.length} Item · ${categories.length} categorie · dati locali.</p>
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

        function renderRows() {
            const queryText = normalizeText(query.value);
            const filters = {
                character: character.value,
                category: category.value,
                phase: phase.value,
                rarity: rarity.value
            };

            const matching = data.items.filter(function(item) {
                if (filters.character && !String(item.character || "").split("·").map(function(value) { return value.trim(); }).includes(filters.character)) {
                    return false;
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
                        <div class="table-wrap"><table class="catalog-table"><thead><tr><th>Rarity</th><th>Item<br><small>nome a +10</small></th><th>Periodo</th><th>Base</th><th>+10</th><th>Master Skill</th><th>Enhancement Bonus</th><th>Main Ingredient</th><th>Acquisizione</th></tr></thead><tbody>${body}</tbody></table></div>
                    </details>
                `;
            }).join("") || "<p class=\"muted\">Nessun Item soddisfa questi filtri.</p>";

            status.textContent = `${matching.length} Item trovati · ${categories.length} categorie disponibili.`;
            wrapTables(results);

            if (window.location.hash) {
                const targetNode = document.getElementById(window.location.hash.slice(1));
                if (targetNode) {
                    const parent = targetNode.closest("details");
                    if (parent) {
                        parent.open = true;
                    }
                    window.setTimeout(function() {
                        targetNode.scrollIntoView({ block: "center" });
                    }, 0);
                }
            }
        }

        [query, character, category, phase, rarity].forEach(function(control) {
            control.addEventListener("input", renderRows);
            control.addEventListener("change", renderRows);
        });

        renderRows();
        resolveItemLinks(data);
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
                search.addEventListener("input", function() { filterGuide(search.value); });
                return loadJson();
            })
            .then(function(data) {
                if (data) {
                    renderCatalogue(data);
                    renderNoteworthy(data);
                }
            })
            .catch(showError);
    }

    initializeTheme();
    loadGuide();
}());
