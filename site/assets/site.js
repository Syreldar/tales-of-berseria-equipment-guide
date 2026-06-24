(function() {
    "use strict";

    const guide = document.getElementById("guide");
    const toc = document.getElementById("toc");
    const search = document.getElementById("search");
    const searchStatus = document.getElementById("search-status");
    const themeToggle = document.getElementById("theme-toggle");
    const storageKey = "tob-equipment-guide-theme";

    function slugify(value) {
        return value
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "");
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
            const base = slugify(heading.textContent) || "sezione";
            const occurrence = usedIds.get(base) || 0;
            const id = (occurrence === 0) ? base : `${base}-${occurrence + 1}`;

            usedIds.set(base, occurrence + 1);
            heading.id = id;

            const link = document.createElement("a");
            link.href = `#${id}`;
            link.textContent = heading.textContent;
            link.className = `toc-level-${heading.tagName.slice(1)}`;
            fragment.appendChild(link);
        });

        toc.replaceChildren(fragment);
    }

    function wrapTables() {
        guide.querySelectorAll("table").forEach(function(table) {
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

    function filterGuide(query) {
        const normalizedQuery = query.trim().toLocaleLowerCase("it-IT");
        const blocks = Array.from(guide.querySelectorAll("section, details, table, .callout, .step-list"));
        let visibleBlocks = 0;

        guide.querySelectorAll("mark.search-hit").forEach(function(mark) {
            mark.replaceWith(document.createTextNode(mark.textContent));
        });

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
                wrapTables();
                normalizeDetails();
                buildTableOfContents();
                initializeSearch();
            })
            .catch(showLoadError);
    }

    initializeTheme();
    loadGuide();
}());
