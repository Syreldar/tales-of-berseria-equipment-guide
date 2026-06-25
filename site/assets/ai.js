(function() {
    "use strict";

    const storageKey = "tob-equipment-guide-theme";
    const spoilerModeKey = "tob-equipment-guide-spoiler-mode";
    const spoilerProgressKey = "tob-equipment-guide-spoiler-progress";
    const root = document.documentElement;
    const guide = document.getElementById("ai-guide");
    const toc = document.getElementById("ai-toc");
    const search = document.getElementById("ai-search");
    const searchStatus = document.getElementById("ai-search-status");
    const themeToggle = document.getElementById("theme-toggle");
    const spoilerToggle = document.getElementById("ai-spoiler-filter");

    const partyMembers = Object.freeze([
        { id: "velvet", name: "Velvet", stage: 0, tone: "velvet", image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Velvet_Cut-in_%28ToB%29.png" },
        { id: "rokurou", name: "Rokurou", stage: 1, tone: "rokurou", image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Rokurou_Cut-in_%28ToB%29.png" },
        { id: "laphicet", name: "Laphicet", stage: 2, tone: "laphicet", image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Laphicet_Cut-in_%28ToB%29.png" },
        { id: "eizen", name: "Eizen", stage: 3, tone: "eizen", image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Eizen_Cut-in_%28ToB%29.png" },
        { id: "magilou", name: "Magilou", stage: 4, tone: "magilou", image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Magilou_Cut-in_%28ToB%29.png" },
        { id: "eleanor", name: "Eleanor", stage: 5, tone: "eleanor", image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Eleanor_Cut-in_%28ToB%29.png" }
    ]);

    let spoilerFilterEnabled = true;
    let unlockedStage = 0;

    function slugify(value) {
        return String(value || "")
            .toLocaleLowerCase("it-IT")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "");
    }

    function setTheme(theme) {
        root.dataset.theme = theme;
        themeToggle.textContent = (theme === "dark") ? "Tema chiaro" : "Tema scuro";
        themeToggle.setAttribute("aria-label", (theme === "dark") ? "Attiva il tema chiaro" : "Attiva il tema scuro");
    }

    function initializeTheme() {
        const saved = window.localStorage.getItem(storageKey);
        const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        setTheme(saved || (dark ? "dark" : "light"));

        themeToggle.addEventListener("click", function() {
            const next = (root.dataset.theme === "dark") ? "light" : "dark";
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

    function saveSpoilerState() {
        window.localStorage.setItem(spoilerModeKey, spoilerFilterEnabled ? "on" : "off");
        window.localStorage.setItem(spoilerProgressKey, String(unlockedStage));
    }

    function memberById(id) {
        return partyMembers.find(function(member) {
            return member.id === id;
        }) || null;
    }

    function nodeIsVisible(node) {
        return !node.hidden && !node.classList.contains("ai-search-hidden");
    }

    function injectVisiblePortraits() {
        guide.querySelectorAll(".ai-character-identity[data-member-id]").forEach(function(identity) {
            const preset = identity.closest("[data-spoiler-stage]");
            const portrait = identity.querySelector(".ai-character-portrait");
            const member = memberById(identity.dataset.memberId || "");
            if (!portrait || !member || !nodeIsVisible(preset)) {
                if (portrait) {
                    portrait.replaceChildren();
                }
                return;
            }

            if (portrait.dataset.rendered === member.id) {
                return;
            }

            const image = document.createElement("img");
            image.src = member.image;
            image.alt = "";
            image.loading = "lazy";
            image.referrerPolicy = "no-referrer";
            image.addEventListener("error", function() {
                portrait.classList.add("portrait-unavailable");
                image.remove();
            }, { once: true });
            portrait.replaceChildren(image);
            portrait.dataset.rendered = member.id;
        });
    }

    function applySpoilerMask() {
        root.dataset.aiSpoiler = spoilerFilterEnabled ? "on" : "off";
        root.dataset.aiSpoilerStage = String(unlockedStage);
        guide.querySelectorAll("[data-spoiler-stage]").forEach(function(node) {
            const stage = Number(node.dataset.spoilerStage);
            node.hidden = spoilerFilterEnabled && Number.isFinite(stage) && stage > unlockedStage;
        });
        spoilerToggle.checked = spoilerFilterEnabled;
        injectVisiblePortraits();
    }

    function buildTableOfContents() {
        const headings = Array.from(guide.querySelectorAll("h2, h3, h4"));
        const fragment = document.createDocumentFragment();
        const used = new Map();

        headings.forEach(function(heading) {
            if (heading.closest("[hidden]") || heading.closest(".ai-search-hidden")) {
                return;
            }

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

    function applySearch() {
        const query = search.value.trim().toLocaleLowerCase("it-IT");
        const nodes = Array.from(guide.querySelectorAll("[data-ai-searchable]"));
        let shown = 0;

        nodes.forEach(function(node) {
            if (node.hidden) {
                node.classList.remove("ai-search-hidden");
                return;
            }

            const matches = !query || node.textContent.toLocaleLowerCase("it-IT").includes(query);
            node.classList.toggle("ai-search-hidden", !matches);
            if (matches) {
                shown += 1;
            }
        });

        searchStatus.textContent = query ? `${shown} sezioni visibili corrispondono alla ricerca.` : "";
        injectVisiblePortraits();
        buildTableOfContents();
    }

    function refresh() {
        applySpoilerMask();
        applySearch();
        buildTableOfContents();
    }

    function bindControls() {
        spoilerToggle.addEventListener("change", function() {
            spoilerFilterEnabled = spoilerToggle.checked;
            saveSpoilerState();
            refresh();
        });

        document.addEventListener("click", function(event) {
            const advance = event.target.closest("[data-ai-advance-party]");
            const reset = event.target.closest("[data-ai-reset-party]");

            if (advance) {
                unlockedStage = Math.min(partyMembers.length - 1, unlockedStage + 1);
                saveSpoilerState();
                refresh();
            }

            if (reset) {
                unlockedStage = 0;
                spoilerFilterEnabled = true;
                saveSpoilerState();
                refresh();
            }
        });

        search.addEventListener("input", applySearch);
    }

    try {
        initializeTheme();
        initializeSpoilerState();
        bindControls();
        refresh();
    } catch (error) {
        console.error("Impossibile inizializzare i preset AI.", error);
    }
}());
