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
        return value
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "");
    }

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function setTheme(theme) {
        document.documentElement.dataset.theme = theme;
        themeToggle.textContent = (theme === "dark") ? "Tema chiaro" : "Tema scuro";
        themeToggle.setAttribute(
            "aria-label",
            (theme === "dark") ? "Attiva il tema chiaro" : "Attiva il tema scuro"
        );
    }

    function initializeTheme() {
        const savedTheme = window.localStorage.getItem(storageKey);
        const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        setTheme(savedTheme || (systemPrefersDark ? "dark" : "light"));

        themeToggle.addEventListener("click", function() {
            const nextTheme = (document.documentElement.dataset.theme === "dark") ? "light" : "dark";
            window.localStorage.setItem(storageKey, nextTheme);
            setTheme(nextTheme);
        });
    }

    function buildTableOfContents() {
        const headings = Array.from(guide.querySelectorAll("h2, h3, h4"));
        const usedIds = new Map();
        const fragment = document.createDocumentFragment();

        headings.forEach(function(heading) {
            const base = heading.id || slugify(heading.textContent) || "sezione";
            const occurrence = usedIds.get(base) || 0;
            const id = (occurrence === 0) ? base : `${base}-${occurrence + 1}`;

            usedIds.set(base, occurrence + 1);

            if (!heading.id) {
                heading.id = id;
            }

            const link = document.createElement("a");
            link.href = `#${heading.id}`;
            link.textContent = heading.textContent;
            link.className = `toc-level-${heading.tagName.slice(1)}`;
            fragment.appendChild(link);
        });

        toc.replaceChildren(fragment);
    }

    function wrapTables(root) {
        root.querySelectorAll("table").forEach(function(table) {
            if (table.parentElement.classList.contains("table-wrap")) {
                return;
            }

            const wrapper = document.createElement("div");
            wrapper.className = "table-wrap";
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        });
    }

    function normalizeDetails() {
        guide.querySelectorAll("details").forEach(function(details) {
            const summary = details.querySelector("summary");

            if (!summary) {
                return;
            }

            summary.setAttribute("tabindex", "0");
        });
    }

    function formatStats(stats) {
        const parts = [];

        stats.forEach(function(value, index) {
            if (Number(value) > 0) {
                parts.push(`<span><b>${statLabels[index]}</b> ${Number(value)}</span>`);
            }
        });

        return parts.length ? parts.join("<br>") : "—";
    }

    function enhancedStats(stats) {
        const total = stats.reduce(function(sum, value) {
            return sum + Number(value || 0);
        }, 0);

        if (total <= 0) {
            return stats.slice();
        }

        return stats.map(function(value) {
            return Number(value) + Math.floor((100 * Number(value)) / total);
        });
    }

    function getDropText(item) {
        if (item.rare_drop && item.rare_drop !== "N/A") {
            return `Rare: ${item.rare_drop}`;
        }

        return item.availability || "Common / shop / chest / story";
    }

    function renderCatalogue(data) {
        const target = guide.querySelector("#catalogo-dinamico");

        if (!target) {
            return;
        }

        if (!data || !Array.isArray(data.items) || data.items.length === 0) {
            target.innerHTML = `
                <div class="callout warning">
                    <p><strong>Catalogo non ancora generato.</strong> Pubblica il repository tramite GitHub Actions: il workflow ricostruisce e convalida il database completo prima di caricare il sito.</p>
                </div>
            `;
            return;
        }

        const byCategory = new Map();
        const categories = Array.isArray(data.categories) ? data.categories : [];

        data.items.forEach(function(item) {
            const id = item.category_id || "altro";

            if (!byCategory.has(id)) {
                byCategory.set(id, []);
            }

            byCategory.get(id).push(item);
        });

        const controls = `
            <div class="catalog-toolbar">
                <label for="catalog-search">Filtra nel catalogo</label>
                <input id="catalog-search" type="search" placeholder="Es. Blood Blade, Rarity 10, Atk, Orc" autocomplete="off">
                <p id="catalog-status" class="catalog-status">${data.items.length} Item in ${categories.length} categorie.</p>
            </div>
        `;

        const sections = categories.map(function(category) {
            const items = byCategory.get(category.id) || [];
            const rows = items.map(function(item) {
                const base = Array.isArray(item.stats) ? item.stats : [0, 0, 0, 0, 0, 0];
                const plusTen = enhancedStats(base);

                return `
                    <tr data-catalog-row>
                        <td>${escapeHtml(item.rarity)}</td>
                        <td><strong>${escapeHtml(item.name)}</strong><br><small>${escapeHtml(item.max_name || "—")}</small></td>
                        <td>${formatStats(base)}</td>
                        <td>${formatStats(plusTen)}</td>
                        <td>${escapeHtml(item.master_skill || "—")}</td>
                        <td>${escapeHtml(item.enhancement_bonus || "—")}</td>
                        <td>${escapeHtml(item.main_ingredient || "—")}</td>
                        <td>${escapeHtml(getDropText(item))}</td>
                    </tr>
                `;
            }).join("");

            return `
                <details class="catalog-category" data-catalog-category open>
                    <summary>
                        <span>${escapeHtml(category.label)}</span>
                        <small>${escapeHtml(category.slot)} · ${escapeHtml(category.character)} · ${items.length} Item</small>
                    </summary>
                    <div class="table-wrap">
                        <table class="catalog-table">
                            <thead>
                                <tr>
                                    <th>Rarity</th>
                                    <th>Item<br><small>nome a +10</small></th>
                                    <th>Base</th>
                                    <th>+10</th>
                                    <th>Master Skill</th>
                                    <th>Enhancement Bonus</th>
                                    <th>Main Ingredient</th>
                                    <th>Acquisizione</th>
                                </tr>
                            </thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>
                </details>
            `;
        }).join("");

        target.innerHTML = `${controls}${sections}`;
        initializeCatalogueSearch();
    }

    function initializeCatalogueSearch() {
        const catalogSearch = guide.querySelector("#catalog-search");
        const catalogStatus = guide.querySelector("#catalog-status");

        if (!catalogSearch || !catalogStatus) {
            return;
        }

        catalogSearch.addEventListener("input", function() {
            const query = catalogSearch.value.trim().toLocaleLowerCase("it-IT");
            let visible = 0;

            guide.querySelectorAll("[data-catalog-category]").forEach(function(category) {
                let categoryVisible = 0;

                category.querySelectorAll("[data-catalog-row]").forEach(function(row) {
                    const matches = !query || row.textContent.toLocaleLowerCase("it-IT").includes(query);
                    row.hidden = !matches;

                    if (matches) {
                        categoryVisible += 1;
                        visible += 1;
                    }
                });

                category.hidden = (categoryVisible === 0);

                if (query && categoryVisible > 0) {
                    category.open = true;
                }
            });

            catalogStatus.textContent = query
                ? `${visible} Item corrispondenti nel catalogo.`
                : `${guide.querySelectorAll("[data-catalog-row]").length} Item nel catalogo.`;
        });
    }

    function filterGuide(query) {
        const normalizedQuery = query.trim().toLocaleLowerCase("it-IT");
        const blocks = Array.from(guide.querySelectorAll("section, details, table, .callout, .steps"));
        let visibleBlocks = 0;

        if (!normalizedQuery) {
            blocks.forEach(function(block) {
                block.classList.remove("is-filtered-out");
            });
            searchStatus.textContent = "";
            return;
        }

        blocks.forEach(function(block) {
            const matches = block.textContent.toLocaleLowerCase("it-IT").includes(normalizedQuery);
            block.classList.toggle("is-filtered-out", !matches);

            if (matches) {
                visibleBlocks += 1;

                if (block.tagName === "DETAILS") {
                    block.open = true;
                }
            }
        });

        searchStatus.textContent = `${visibleBlocks} blocchi pertinenti trovati.`;
    }

    function initializeSearch() {
        search.addEventListener("input", function() {
            filterGuide(search.value);
        });
    }

    function showLoadError() {
        guide.innerHTML = `
            <section class="callout warning">
                <h2>Impossibile aprire la guida locale</h2>
                <p>Apri il sito tramite GitHub Pages oppure avvialo con un server statico. Il file richiesto è <code>content/guide.html</code>.</p>
            </section>
        `;
    }

    function loadCatalogue() {
        return fetch("./content/catalogo.json", { cache: "no-store" })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error("Catalogo non disponibile");
                }

                return response.json();
            })
            .catch(function() {
                return null;
            });
    }

    function loadGuide() {
        fetch("./content/guide.html", { cache: "no-store" })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error("Contenuto non disponibile");
                }

                return response.text();
            })
            .then(function(html) {
                guide.innerHTML = html;
                return loadCatalogue();
            })
            .then(function(catalogue) {
                renderCatalogue(catalogue);
                wrapTables(guide);
                normalizeDetails();
                buildTableOfContents();
                initializeSearch();
            })
            .catch(showLoadError);
    }

    initializeTheme();
    loadGuide();
}());
