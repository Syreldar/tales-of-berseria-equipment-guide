(function() {
    "use strict";

    const guide = document.getElementById("guide");
    const tableOfContents = document.getElementById("table-of-contents");
    const searchInput = document.getElementById("guide-search");
    const searchStatus = document.getElementById("search-status");
    const themeToggle = document.getElementById("theme-toggle");
    const storageKey = "tob-equipment-guide-theme";

    function slugify(value) {
        return value
            .toLowerCase()
            .trim()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "") || "section";
    }

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme;
        localStorage.setItem(storageKey, theme);
    }

    function initialiseTheme() {
        const savedTheme = localStorage.getItem(storageKey);

        if (savedTheme === "light" || savedTheme === "dark") {
            applyTheme(savedTheme);
            return;
        }

        if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
            applyTheme("dark");
        }
    }

    function wrapTables() {
        guide.querySelectorAll("table").forEach(function(table) {
            if (table.parentElement.classList.contains("table-scroll")) {
                return;
            }

            const wrapper = document.createElement("div");
            wrapper.className = "table-scroll";
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        });
    }

    function prepareLinks() {
        guide.querySelectorAll("a[href]").forEach(function(link) {
            const href = link.getAttribute("href");

            if (href && /^https?:\/\//i.test(href)) {
                link.target = "_blank";
                link.rel = "noreferrer";
            }
        });
    }

    function buildTableOfContents() {
        const headings = Array.from(guide.querySelectorAll("h2, h3, h4"));
        const rootList = document.createElement("ul");
        let currentH2List = rootList;
        let currentH3List = null;
        let headingCount = 0;

        headings.forEach(function(heading) {
            const title = heading.textContent.trim();

            if (!title) {
                return;
            }

            let id = slugify(title);
            let duplicate = 2;

            while (document.getElementById(id) && document.getElementById(id) !== heading) {
                id = `${slugify(title)}-${duplicate}`;
                duplicate += 1;
            }

            heading.id = id;

            const item = document.createElement("li");
            const link = document.createElement("a");
            link.href = `#${id}`;
            link.textContent = title;
            item.appendChild(link);

            if (heading.tagName === "H2") {
                rootList.appendChild(item);
                currentH2List = document.createElement("ul");
                item.appendChild(currentH2List);
                currentH3List = null;
            } else if (heading.tagName === "H3") {
                currentH2List.appendChild(item);
                currentH3List = document.createElement("ul");
                item.appendChild(currentH3List);
            } else if (currentH3List) {
                currentH3List.appendChild(item);
            } else {
                currentH2List.appendChild(item);
            }

            headingCount += 1;
        });

        tableOfContents.replaceChildren(rootList);

        if (headingCount === 0) {
            tableOfContents.innerHTML = "<p>No headings were found in this archive.</p>";
        }
    }

    function clearSearch() {
        guide.querySelectorAll(".search-match, .is-hidden-by-search").forEach(function(element) {
            element.classList.remove("search-match", "is-hidden-by-search");
        });
    }

    function searchGuide() {
        const query = searchInput.value.trim().toLowerCase();
        const sections = Array.from(guide.querySelectorAll("h2, h3, h4, p, li, table, pre"));

        clearSearch();

        if (!query) {
            searchStatus.textContent = "";
            return;
        }

        let matches = 0;

        sections.forEach(function(section) {
            const text = section.textContent.toLowerCase();

            if (text.includes(query)) {
                section.classList.add("search-match");
                matches += 1;
            } else {
                section.classList.add("is-hidden-by-search");
            }
        });

        searchStatus.textContent = `${matches} matching block${matches === 1 ? "" : "s"}`;
    }

    async function loadGuide() {
        try {
            const response = await fetch("./content/guide.html", { cache: "no-store" });

            if (!response.ok) {
                throw new Error(`Guide archive returned HTTP ${response.status}`);
            }

            const content = await response.text();

            if (!content.trim()) {
                throw new Error("The guide archive is empty.");
            }

            guide.innerHTML = content;
            wrapTables();
            prepareLinks();
            buildTableOfContents();
        } catch (error) {
            guide.innerHTML = `
                <section class="loading-card">
                    <h2>Source archive not imported</h2>
                    <p>Run the <strong>Archive GameFAQs guide and deploy</strong> workflow from the repository's Actions tab. It saves the complete printable source page and builds this reader automatically.</p>
                    <p><a href="https://gamefaqs.gamespot.com/pc/184665-tales-of-berseria/faqs/74517?print=1" target="_blank" rel="noreferrer">Open the original GameFAQs printable version</a></p>
                    <p class="error-detail">${error.message}</p>
                </section>
            `;
            tableOfContents.innerHTML = "<p>Import the source archive to generate navigation.</p>";
        }
    }

    themeToggle.addEventListener("click", function() {
        const currentTheme = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
        applyTheme(currentTheme === "dark" ? "light" : "dark");
    });

    searchInput.addEventListener("input", searchGuide);

    initialiseTheme();
    loadGuide();
}());
