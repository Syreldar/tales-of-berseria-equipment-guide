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
    const statLabels = ["Atk", "Arte Attack", "Def", "Arte Defense", "Focus"];

    const partyMembers = Object.freeze([
        {
            id: "velvet",
            name: "Velvet",
            stage: 0,
            tone: "velvet",
            role: "Attaccante in prima linea · combo, Stun e Therion Form",
            battleAdvice: "Se la affidi al controllo automatico, falla puntare un nemico resistente: la sua combo ha il tempo di finire e può entrare in Therion Form. Questa scelta non elimina gli spostamenti: se il bersaglio è lontano, Velvet dovrà comunque raggiungerlo.",
            equipmentAdvice: "Blades privilegiano Atk; Belts, il suo Accessory, possono aggiungere Focus per lo Stun. Su Armor, Rings, Shoes e Women’s Shoes conserva prima le Master Skills che non hai ancora appreso.",
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
            equipmentAdvice: "Cerca Atk su Short Swords e Talismans; Armor, Shoes e Men’s Shoes servono a non farlo cadere mentre resta vicino al nemico. Impara prima ogni Master Skill nuova.",
            categories: ["Short Swords", "Talismans", "Men’s Armor", "Rings", "Shoes", "Men’s Shoes"],
            tip: "AI: Most Souls · Defense Only",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Rokurou_Cut-in_%28ToB%29.png"
        },
        {
            id: "laphicet",
            name: "Laphicet",
            stage: 2,
            tone: "laphicet",
            role: "Incantatore di supporto · magie rapide, cure e controllo",
            battleAdvice: "Lascialo a distanza con poche Malak Artes affidabili: Kaleidos Ray, Blessed Drops, Void Mire e Dark Fangs. Una lista corta riduce i cast lunghi e le occasioni in cui l’AI viene interrotta.",
            equipmentAdvice: "Paper e Bags favoriscono Arte Attack. Arte Defense e Focus sono utili quando viene preso di mira; prima di sostituire un pezzo, impara la sua Master Skill.",
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
            equipmentAdvice: "Nel set Fist Bruiser cerca Atk e Focus. Nel set Wind Master conta di più Arte Attack, ma mantieni Def e Arte Defense: Eizen può comunque ricevere pressione.",
            categories: ["Bracelets", "Pendants", "Men’s Armor", "Rings", "Shoes", "Men’s Shoes"],
            tip: "AI: Fist prima · Wind Master dopo",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Eizen_Cut-in_%28ToB%29.png"
        },
        {
            id: "magilou",
            name: "Magilou",
            stage: 4,
            tone: "magilou",
            role: "Incantatrice offensiva · magie rapide da lontano",
            battleAdvice: "L’AI è più affidabile con Aqua Split e Blood Moon; Crown Fire è opzionale. Tenere poche Malak Artes abbrevia i cast e riduce le aperture in cui può essere interrotta.",
            equipmentAdvice: "Guardians e Earrings favoriscono Arte Attack. Arte Defense è utile perché un personaggio che lancia magie colpito durante un cast perde più valore di pochi punti aggiuntivi di danno.",
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
            equipmentAdvice: "Scegli una priorità per volta: Atk per le Martial Artes, Arte Attack per Flame Beast e Maelstrom. Non distribuire le statistiche senza uno scopo.",
            categories: ["Spears", "Ribbons", "Women’s Armor", "Rings", "Shoes", "Women’s Shoes"],
            tip: "AI: Close Combat · Flame Beast",
            image: "https://aselia.fandom.com/wiki/Special:Redirect/file/Eleanor_Cut-in_%28ToB%29.png"
        }
    ]);

    const characterGuideDetails = Object.freeze({
        velvet: {
            titleAdvice: "Incapacitator finché i Rings sono a +8 o meno. Dopo quel punto puoi tornare a un Title offensivo se vuoi più danno o utilità, ma il preset prudente parte sempre dalla protezione contro Stun.",
            ai: {
                summary: "Preset aggressivo ma affidabile: scegli un nemico robusto, lascia che Velvet completi la catena ed entri in Therion Form senza sprecare mosse che l'AI tende a mancare.",
                strategy: ["Target Strong Enemies", "Aim for Weaknesses", "Be Aggressive", "Change Out", "You Decide"],
                mode: "Artes OFF",
                skills: ["Harsh Rebuttal", "Avalanche Fang", "Moonlight Cyclone", "Rising Moon", "Rising Falcon", "Soaring Dragon", "Slag Assault", "Grounding Strike", "Banishing Thunder", "Binding Frost"],
                footnote: "Lascia ON le altre Artes, incluso Scale Crusher."
            }
        },
        rokurou: {
            titleAdvice: "Incapacitator fino a Rings +8. Superata quella soglia puoi tornare su un Title più offensivo, ma per l'AI il guadagno maggiore resta evitare Stun letali mentre duella in prima linea.",
            ai: {
                summary: "Preset difensivo e lineare: Rokurou deve colpire le debolezze senza perdere tempo in riposizionamenti o in Forms che l'AI concatena male.",
                strategy: ["Target Enemy with Most Souls", "Aim for Weaknesses", "Defense Only", "Change Out", "You Decide"],
                mode: "Artes OFF",
                skills: ["Crimson Flash", "Jade Wave", "Armor Crusher", "Double Haze", "Orochi’s Fury", "Form 1: Fire Burst", "Form 2: Imbue Earth", "Form 5: Scatterburst", "Form 6: Dark Vortex", "Form 7: Rapid Bolt"],
                footnote: "Lascia ON tutte le altre Artes non elencate."
            }
        },
        laphicet: {
            titleAdvice: "Scelta sicura: Incapacitator finché i Rings sono a +8 o meno. Eccezione legittima: Sorcerer se vuoi aumentare la pressione offensiva e i Void cast, accettando un preset meno prudente.",
            ai: {
                summary: "Laphicet funziona meglio con poche Malak Artes affidabili. Ridurre la lista abbassa i cast lunghi, gli errori di priorità e le interruzioni mentre resta a distanza.",
                strategy: ["Target Multiple Enemies", "Engage at Range", "Defense Only", "Change Out", "For Attacking"],
                mode: "Malak Artes ON",
                skills: ["Kaleidos Ray", "Blessed Drops", "Void Mire", "Dark Fangs"],
                footnote: "Metti OFF tutte le altre Malak Artes."
            }
        },
        eizen: {
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
        magilou: {
            titleAdvice: "Incapacitator resta la scelta standard fino a Rings +8. Se poi vuoi più pressione magica puoi rivalutare un Title da caster, ma il preset base premia prima la sopravvivenza.",
            ai: {
                summary: "Magilou rende meglio con una rotazione molto corta: poche magie, cast più sicuri e meno aperture in cui l'AI si fa interrompere.",
                strategy: ["Target Multiple Enemies", "Engage at Range", "Defense Only", "Change Out", "For Attacking"],
                mode: "Malak Artes ON",
                skills: ["Aqua Split", "Blood Moon", "Opzionale: Crown Fire"],
                footnote: "Metti OFF tutte le altre Malak Artes."
            }
        },
        eleanor: {
            titleAdvice: "Incapacitator fino a Rings +8. Dopo puoi cercare più danno, ma per un personaggio ibrido che combatte vicino al bersaglio il controllo dello Stun resta uno dei bonus difensivi più apprezzabili.",
            ai: {
                summary: "Eleanor vuole stare vicina al bersaglio e usare una rotazione corta. Le mosse che respingono troppo o rompono il seguito della combo rendono l'AI molto meno affidabile.",
                strategy: ["Target Nearby Enemies", "Close Combat", "Defense Only", "Change Out", "For Attacking"],
                mode: "Artes OFF",
                skills: ["Martial Artes: Vanguard, Double Rush, Skewering Spear, Cleansing Lance", "Malak Artes: tutte tranne Flame Beast e Maelstrom"],
                footnote: "Mantieni la rotazione corta: è qui che l'AI di Eleanor lavora meglio."
            }
        }
    });

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
        "Shoes": "Shoes",
        "Men’s Shoes": "Men’s Shoes",
        "Women’s Shoes": "Women’s Shoes"
    });

    const categoryLabels = Object.freeze({
        "Blades": "Blades",
        "Short Swords": "Short Swords",
        "Paper": "Paper",
        "Bracelets": "Bracelets",
        "Guardians": "Guardians",
        "Spears": "Spears",
        "Belts": "Belts",
        "Talismans": "Talismans",
        "Bags": "Bags",
        "Pendants": "Pendants",
        "Earrings": "Earrings",
        "Ribbons": "Ribbons",
        "Men’s Armor": "Men’s Armor",
        "Women’s Armor": "Women’s Armor",
        "Rings": "Rings",
        "Shoes": "Shoes",
        "Men’s Shoes": "Men’s Shoes",
        "Women’s Shoes": "Women’s Shoes"
    });

    const slotLabels = Object.freeze({
        "Weapon": "Weapon",
        "Accessory": "Accessory",
        "Armor": "Armor",
        "Ring": "Ring",
        "Shoes": "Shoes",
        "Men’s Shoes": "Men’s Shoes",
        "Women’s Shoes": "Women’s Shoes"
    });

    const phaseLabels = Object.freeze({
        "Main game": "Storia principale",
        "Post-game": "Post-game"
    });

    const slotDisplayLabels = Object.freeze({
        "Weapon": "Weapon · Arma",
        "Accessory": "Accessory · Accessorio",
        "Armor": "Armor · Armatura",
        "Rings": "Rings · Anelli",
        "Shoes": "Shoes · Calzature"
    });

    const slotGuideCopy = Object.freeze({
        "Weapon": "Qui conta soprattutto la statistica offensiva principale del personaggio.",
        "Accessory": "È lo slot in cui specializzi davvero Atk oppure Arte Attack.",
        "Armor": "Serve a stabilizzare il personaggio: difese, Focus e sopravvivenza prima del nome.",
        "Rings": "Sono soprattutto un contenitore di Arte Defense e Master Skills, più che di danno.",
        "Shoes": "Focus e utilità: spesso sono gli oggetti con le abilità più immediate da sentire in battaglia."
    });

    const recommendationPhaseIcons = Object.freeze({
        "Main game": "🧭",
        "Post-game": "👑"
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

    const categorySourceGuide = Object.freeze({
        families: [
            {
                id: "weapons",
                title: "Weapons",
                icon: "⚔",
                lead: "Le Weapons sono la fonte principale di Attack. Martial Artes e Hidden Artes scalano entrambe con Attack, quindi per quasi tutti — soprattutto per Velvet e Rokurou — sono il primo slot da controllare. Fanno in parte eccezione Laphicet e, in misura minore, Magilou. Anche gli Enhancement Bonus aumentano il danno in percentuale su avversari storditi; per questo una Weapon ben potenziata può diventare una vera centrale offensiva.",
                categories: [
                    { name: "Blades", owners: "Velvet", note: "Le Blades puntano soprattutto su capability e bonus elementali: effetti che Velvet può reperire anche tramite Random Skills, quindi la priorità resta la statistica. Poiché Attack e Arte Attack crescono in modo simile, le Blades che spingono Attack restano in genere le più interessanti." },
                    { name: "Short Swords", owners: "Rokurou", note: "Le Short Swords sono spesso costruite attorno ad ailment e elementi, quindi il loro valore dipende molto dal tuo stile di gioco. Rokurou apprezza sia Arte Attack sia Focus, ma usa molte Hidden Artes: conviene quindi cercare armi che alzino una di queste due statistiche oltre ad Attack, senza mai sacrificare troppo quest’ultimo." },
                    { name: "Paper", owners: "Laphicet", note: "Laphicet è prima di tutto un caster. Gran parte del suo danno passa dalle Malak Artes, quindi le Paper migliori sono quelle che alzano Arte Attack oppure riducono i tempi di cast. Per fortuna è anche la direzione seguita da gran parte delle sue armi." },
                    { name: "Bracelets", owners: "Eizen", note: "Eizen è estremamente flessibile: con Break Soul e set di Artes può sfruttare bene sia Attack sia Arte Attack. Poiché i suoi orientamenti cambiano molto, conviene cercare Bracelets che potenzino con decisione una sola statistica invece di disperdere il valore su troppe direzioni." },
                    { name: "Guardians", owners: "Magilou", note: "Le Guardians sono un assortimento molto eterogeneo: alcune sono utili, molte meno. Magilou usa quasi solo Malak Artes, ha Attack basso e trae poco vantaggio dalle Hidden Artes offensive; di conseguenza conviene scegliere soprattutto in base alle statistiche, con un occhio di riguardo ad Arte Attack." },
                    { name: "Spears", owners: "Eleanor", note: "Le Spears ricordano le Short Swords: tante capability da status e contro specifici mostri, con una distribuzione statisticamente però più coerente. Molte spingono Attack più di Arte Attack e questo si adatta bene a Eleanor, che tende naturalmente a valorizzare l’offensiva fisica pur avendo anche Malak Artes." }
                ]
            },
            {
                id: "accessories",
                title: "Accessories",
                icon: "✦",
                lead: "Gli Accessories sono la fonte primaria di Arte Attack: utili per tutti, ma davvero cruciali per Magilou, Laphicet ed Eizen. Velvet e Rokurou trovano spesso ottime sinergie negli effetti, mentre Eleanor ottiene soprattutto un miglioramento prestazionale più lineare.",
                categories: [
                    { name: "Belts", owners: "Velvet", note: "Scegli le Belts in base alle Skills e alle statistiche secondarie. Velvet ha buone Hidden Artes, ma spesso le usa più per le proprietà di controllo che per il puro danno; per questo conviene guardare prima gli Accessory che le danno Arte Attack e utilità davvero impattanti." },
                    { name: "Talismans", owners: "Rokurou", note: "Velvet può trascurare parte dell’Arte Attack, Rokurou no. Con soltanto otto Hidden Artes, peraltro, i Talismans sono spesso più utili quando offrono capacità da ailment o bonus elementali che interagiscono bene con il suo set difensivo." },
                    { name: "Bags", owners: "Laphicet", note: "Laphicet è un caster difensivo e la sua Break Soul ne riflette il ruolo. Molte Bags migliorano la capacità di infliggere status o di restare stabile; con poche eccezioni, per lui conviene scegliere l’Accessory in base alle statistiche più che agli effetti di potenziamento situazionale." },
                    { name: "Pendants", owners: "Eizen", note: "Qui si vede come dovrebbe funzionare il design: quasi ogni Pendant offre statistiche utili, bonus elementali o capability contro nemici “problematici”. Siccome tutti gli Accessories di Eizen alzano Arte Attack — cosa che lui vuole se lo usi da caster — è difficile sbagliare davvero scelta." },
                    { name: "Earrings", owners: "Magilou", note: "Gli Earrings sono il cuore dell’equipaggiamento di Magilou. Aumentano Arte Attack e quasi sempre questo basta per renderli lo slot più importante; le capability contro specifici nemici contano poco, ma alcune gemme eccellono nettamente anche solo da un punto di vista statistico." },
                    { name: "Ribbons", owners: "Eleanor", note: "Eleanor non ha Malak Artes come Eizen, ma quasi la stessa fame di statistiche, perché per lei sono basse sia Arte Attack sia capacità di teletrasportarsi in mezzo al caos. Una metà dei suoi Ribbons punta a capability contro mostri specifici, l’altra a status ailment: in genere conviene privilegiare i numeri e la praticità." }
                ]
            },
            {
                id: "armor",
                title: "Armor",
                icon: "🛡️",
                lead: "L’Armor serve ad aumentare Defense. La maggior parte lo fa in modo diretto, alcuni pezzi lo fanno indirettamente, altri “sbagliano messaggio” e spingono Attack o Focus. Defense è la statistica meno importante del gioco finché non stai usando attacchi rapidi o guardia per mitigare un colpo, ma resta utile se temi molto una categoria di danno o hai problemi a negoziare il lieve ritardo introdotto dal movimento difensivo. Per questo è consigliabile cercare Armor che, oltre a Defense, alzi anche una statistica offensiva. Inoltre la categoria ha un Enhancement Bonus potentissimo — la riduzione della durata dello Stagger — ma si sente davvero solo da +5 in poi, quindi non serve inseguirlo subito.",
                categories: [
                    { name: "Men’s Armor", owners: "Rokurou; Laphicet; Eizen", note: "Le Men’s Armor offrono una distribuzione piuttosto ampia: alcune sono puramente difensive, altre molto più interessanti perché combinano tenuta e spinta offensiva. In pratica sono più utili quando non ti limiti a guardare la sola Defense." },
                    { name: "Women’s Armor", owners: "Velvet; Magilou; Eleanor", note: "Le Women’s Armor seguono la stessa logica: statistiche difensive come base, ma alcuni pezzi emergono perché aiutano davvero l’output o la stabilità di Velvet, Magilou ed Eleanor. Le scelte migliori non sono quasi mai quelle da puro “muro”." }
                ]
            },
            {
                id: "shoes-family",
                title: "Shoes, Men’s Shoes e Women’s Shoes",
                icon: "👣",
                lead: "Le categorie Shoes governano Focus, quindi hanno tutte un impatto di gameplay molto più grande di quanto sembri. La buona notizia è che, in tutte e tre le categorie, gran parte delle Shoes possiede abilità eccellenti che le rendono desiderabili quasi indipendentemente dai numeri. Inoltre, a differenza dell’Armor, uomini e donne hanno sia le Shoes universali sia i rispettivi modelli specifici, e di norma si trovano tutti nelle stesse aree: se hai poche risorse, potenzia le Shoes universali e falle girare nel party.",
                categories: [
                    { name: "Shoes", owners: "All", note: "Le Shoes universali funzionano da infrastruttura comune del gruppo. Spesso bastano loro per tenere alto Focus e raccogliere Master Skills eccellenti senza dover investire subito nei modelli specifici di genere." },
                    { name: "Men’s Shoes", owners: "Rokurou; Laphicet; Eizen", note: "Le Men’s Shoes alternano opzioni molto difensive ad altre sorprendentemente aggressive. Proprio perché Focus resta centrale, quasi ogni buon paio può accompagnare a lungo il trio maschile se ne attiva bene le Skills." },
                    { name: "Women’s Shoes", owners: "Velvet; Magilou; Eleanor", note: "Le Women’s Shoes sono una delle categorie con i picchi qualitativi più evidenti: Focus molto alto, Skills spesso fortissime e parecchi pezzi che restano utili fino a tardi. Vale quasi sempre la pena tenerle d’occhio." }
                ]
            },
            {
                id: "rings",
                title: "Rings",
                icon: "💍",
                lead: "Detto brutalmente, i singoli Rings sono spesso poco importanti. Sono però la fonte principale di Arte Defense e questa statistica è davvero utile; il problema è che, fino agli ultimissimi, quasi tutti i Rings hanno coppie di Skills poco incisive e facilmente replicabili via Random Skills. L’Enhancement Bonus della categoria — ridurre lo Stun dal 9% fino al 90% — è invece assurdo e rende equipaggiare un Ring quasi obbligatorio alle difficoltà alte. Conviene raccoglierli tutti per le Master Skills e per completare il party, ricordando però che è più importante indossare un Ring che inseguirne uno specifico.",
                categories: [
                    { name: "Rings", owners: "All", note: "I Rings vanno letti più come slot funzionale che come caccia al pezzo perfetto: i migliori si distinguono soprattutto per quando diventano disponibili, per il picco di Arte Defense e per l’enorme valore del loro Enhancement Bonus." }
                ]
            }
        ]
    });

    let spoilerFilterEnabled = true;
    let unlockedStage = 0;
    let catalogueData = null;
    let cataloguePendingCharacter = "";
    let cataloguePendingCategory = "";
    let catalogueHashHandlerBound = false;
    const originalCharacterReferenceText = new WeakMap();
    const originalCharacterReferenceAttributes = new WeakMap();

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

    function displayCategory(value) {
        return categoryLabels[String(value || "")] || String(value || "Categoria");
    }

    function displaySlot(value) {
        return slotLabels[String(value || "")] || String(value || "Slot");
    }

    function displayPhase(value) {
        return phaseLabels[String(value || "")] || String(value || "Progressione");
    }

    function displayReferenceReason(value) {
        return String(value || "Scheda di confronto: verifica statistiche, Master Skill e Enhancement Bonus.")
            .replace(/\bRarity\b/g, "rarità")
            .replace(/\bMain game\b/g, "storia principale");
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

    function visibleCharacterNames(value) {
        const users = splitCharacterList(value);

        if (!users.length) {
            return "";
        }
        if (users.includes("All")) {
            return "Tutti";
        }

        return users.map(function(user) {
            return isNamedCharacterVisible(user) ? user : "????";
        }).join(" · ");
    }

    function escapeRegex(value) {
        return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function lockedMemberNamePattern() {
        if (!spoilerFilterEnabled) {
            return null;
        }

        const names = partyMembers
            .filter(function(member) {
                return !memberIsVisible(member);
            })
            .map(function(member) {
                return escapeRegex(member.name);
            });

        if (!names.length) {
            return null;
        }

        return new RegExp(`\\b(?:${names.join("|")})\\b`, "gi");
    }

    function maskLockedCharacterName(value, pattern) {
        return pattern ? String(value || "").replace(pattern, "????") : String(value || "");
    }

    function originalAttributeValue(element, attribute) {
        let attributes = originalCharacterReferenceAttributes.get(element);

        if (!attributes) {
            attributes = new Map();
            originalCharacterReferenceAttributes.set(element, attributes);
        }
        if (!attributes.has(attribute)) {
            attributes.set(attribute, element.getAttribute(attribute) || "");
        }

        return attributes.get(attribute);
    }

    function maskLockedCharacterReferences(root) {
        const pattern = lockedMemberNamePattern();
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let node = walker.nextNode();

        while (node) {
            const parent = node.parentElement;
            const skip = parent && (parent.tagName === "SCRIPT" || parent.tagName === "STYLE");

            if (!skip) {
                if (!originalCharacterReferenceText.has(node)) {
                    originalCharacterReferenceText.set(node, node.nodeValue || "");
                }
                node.nodeValue = maskLockedCharacterName(originalCharacterReferenceText.get(node), pattern);
            }

            node = walker.nextNode();
        }

        [root].concat(Array.from(root.querySelectorAll("[alt], [aria-label], [title]"))).forEach(function(element) {
            ["alt", "aria-label", "title"].forEach(function(attribute) {
                if (!element.hasAttribute(attribute)) {
                    return;
                }
                element.setAttribute(attribute, maskLockedCharacterName(originalAttributeValue(element, attribute), pattern));
            });
        });
    }

    function visibleText(node) {
        const copy = node.cloneNode(true);
        copy.querySelectorAll("[hidden], .is-filtered-out").forEach(function(hiddenNode) {
            hiddenNode.remove();
        });
        return copy.textContent || "";
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
        guide.querySelectorAll("[data-spoiler-stage], [data-spoiler-members]").forEach(function(node) {
            const stage = Number(node.dataset.spoilerStage);
            const members = splitCharacterList(node.dataset.spoilerMembers || "");
            const stageIsVisible = !spoilerFilterEnabled || !Number.isFinite(stage) || stage <= unlockedStage;
            const membersAreVisible = !spoilerFilterEnabled || members.every(isNamedCharacterVisible);

            node.hidden = !stageIsVisible || !membersAreVisible;
        });
        maskLockedCharacterReferences(guide);
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
            if (heading.closest("[hidden]") || heading.closest(".is-filtered-out")) {
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
            displayCategory(item.category),
            visibleCharacterNames(item.character),
            displayPhase(item.phase),
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
        const recorded = String(item.acquisition || "").trim();
        const needsLocalizedFallback = /^(rare drop|common drop|post-game enemy drop)/i.test(recorded);
        if (recorded && !needsLocalizedFallback && !/provenienza .*verificare|fonte non registrata/i.test(recorded)) {
            return recorded;
        }

        const kind = String(item.source_kind || "").trim();
        const rare = String(item.rare_drop || "").trim();
        if (kind === "rare_drop" && rare && rare !== "—" && rare !== "N/A") {
            return `Drop raro — ${rare}`;
        }
        if (kind === "common_drop") {
            return "Drop comune — rarità equivalente; usa la regola Common Target nella sezione dedicata al farming.";
        }
        if (kind === "postgame_enemy_drop") {
            return "Drop dei nemici nel post-game — fonte specifica non registrata nella tabella strutturata.";
        }
        if (rare && rare !== "—" && rare !== "N/A") {
            return `Drop raro — ${rare}`;
        }
        return "Fonte non registrata";
    }

    function sourceBadge(item) {
        const kind = String(item.source_kind || "").trim();
        const labels = {
            rare_drop: "Drop raro",
            common_drop: "Drop comune",
            shop_and_common_drop: "Negozio / drop comune",
            chest: "Forziere",
            chest_or_shop: "Forziere / negozio",
            chest_or_shop_rank: "Forziere / grado negozio",
            shop: "Negozio",
            story: "Storia",
            starting_equipment: "Equipaggiamento iniziale",
            postgame_chest: "Forziere post-game",
            postgame_enemy_drop: "Drop nemici post-game",
            chest_or_story: "Forziere / storia",
            postgame_chest_or_drop: "Post-game"
        };
        return labels[kind] || "Indicazione";
    }

    function recommendationSlotLabel(slotName) {
        return slotDisplayLabels[String(slotName || "")] || String(slotName || "Slot");
    }

    function recommendationSlotCopy(slotName) {
        return slotGuideCopy[String(slotName || "")] || "";
    }

    function categoryIcon(categoryName) {
        return categoryIcons[String(categoryName || "")] || "✦";
    }

    function slotIcon(slotName) {
        return slotIcons[String(slotName || "")] || "✦";
    }

    function recommendationGroupTitle(sourceGroup, slotName) {
        const entries = Array.isArray(sourceGroup && sourceGroup.entries) ? sourceGroup.entries : [];
        const first = entries[0] || {};
        const itemCount = entries.length;
        const firstCategory = displayCategory(first.category || "");
        const firstPhaseKey = phaseFromRarity(first.rarity);
        const firstPhase = displayPhase(firstPhaseKey);
        const hasOnlyPostgame = entries.length > 1 && entries.every(function(entry) {
            return phaseFromRarity(entry.rarity) === "Post-game";
        });

        if (itemCount <= 1) {
            return `Noteworthy ${firstCategory} · ${String(first.item || "Nota oggetto")}`;
        }
        if (hasOnlyPostgame) {
            return `${firstCategory} (Post-Game)`;
        }
        if (slotName === "Shoes") {
            return `Noteworthy ${firstCategory}`;
        }
        return `${firstCategory} · ${firstPhase}`;
    }

    function renderCategoryGuide() {
        const target = guide.querySelector("#category-guide-dynamic");
        if (!target) {
            return;
        }

        const families = categorySourceGuide.families.map(function(family) {
            const categories = family.categories.filter(function(category) {
                return !spoilerFilterEnabled || splitCharacterList(category.owners).some(function(owner) {
                    return owner === "All" || isNamedCharacterVisible(owner);
                });
            }).map(function(category) {
                const owners = visibleCharacterNames(category.owners);
                return `
                    <article class="category-guide-card" data-spoiler-members="${escapeHtml(category.owners)}">
                        <div class="category-guide-card-header">
                            <p class="category-guide-card-icon" aria-hidden="true">${escapeHtml(categoryIcon(category.name))}</p>
                            <div>
                                <h5>${escapeHtml(category.name)}</h5>
                                <p class="category-guide-card-meta">${owners ? `Utilizzatori · ${escapeHtml(owners)}` : "Utilizzatori · Tutti"}</p>
                            </div>
                        </div>
                        <p>${escapeHtml(category.note)}</p>
                    </article>
                `;
            });

            if (!categories.length) {
                return "";
            }

            return `
                <section class="category-family-panel">
                    <div class="category-family-header">
                        <p class="category-family-kicker">${escapeHtml(family.icon)} Sezione base</p>
                        <h4>${escapeHtml(family.title)}</h4>
                        <p class="category-family-lead">${escapeHtml(family.lead)}</p>
                    </div>
                    <div class="category-guide-grid">${categories.join("")}</div>
                </section>
            `;
        }).filter(Boolean);

        target.innerHTML = families.join("");
    }

    function phaseFromRarity(rarity) {
        return Number(rarity) >= 19 ? "Post-game" : "Main game";
    }

    function phaseIcon(phase) {
        return recommendationPhaseIcons[String(phase || "")] || "✦";
    }

    function memberTone(member) {
        return member && member.tone ? ` tone-${member.tone}` : "";
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
                const slot = categorySlots[category] || "Categoria di equipaggiamento";
                const descriptor = (slot === category) ? `${slot} category` : slot;
                return `<a href="${escapeHtml(href)}" data-catalogue-link title="Apri ${escapeHtml(displayCategory(category))} (${escapeHtml(descriptor)}) nel catalogo filtrato per ${escapeHtml(member.name)}" aria-label="Apri ${escapeHtml(displayCategory(category))}, ${escapeHtml(descriptor)}, nel catalogo filtrato per ${escapeHtml(member.name)}">${escapeHtml(displayCategory(category))}</a>`;
            }).join("");
            const catalogHref = catalogueLink(member, "");
            const aiHref = `./ai.html#ai-${escapeHtml(member.id)}`;
            const dossierHref = `./character.html?character=${encodeURIComponent(member.name)}`;

            return `
                <article class="character-card tone-${escapeHtml(member.tone)}">
                    <img class="character-art" src="${escapeHtml(member.image)}" alt="" loading="lazy" referrerpolicy="no-referrer" aria-hidden="true">
                    <div class="character-card-content">
                        <div class="character-card-header">
                            <div class="character-portrait">
                                <img src="${escapeHtml(member.image)}" alt="Ritratto di ${escapeHtml(member.name)}" loading="lazy" referrerpolicy="no-referrer">
                            </div>
                            <div>
                                <p class="character-kicker">Equipaggiamento e comportamento automatico</p>
                                <h3>${escapeHtml(member.name)}</h3>
                                <p class="character-role">${escapeHtml(member.role)}</p>
                            </div>
                        </div>
                        <p class="character-summary"><strong>In battaglia:</strong> ${escapeHtml(member.battleAdvice)}</p>
                        <p class="character-equipment-focus"><strong>Equipaggiamento:</strong> ${escapeHtml(member.equipmentAdvice)}</p>
                        <div class="character-category-list" aria-label="Categorie utilizzabili da ${escapeHtml(member.name)}">${chips}</div>
                        <div class="character-card-footer">
                            <span class="character-card-tip">★ ${escapeHtml(member.tip)}</span>
                            <div class="character-card-actions">
                                <a class="character-card-action" href="${escapeHtml(dossierHref)}">Pagina personaggio <span aria-hidden="true">→</span></a>
                                <a class="character-card-action" href="${escapeHtml(catalogHref)}">Vedi tutti gli oggetti <span aria-hidden="true">→</span></a>
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
                        <h3>????</h3>
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
                <div><strong>Collegamenti diretti</strong>Ogni chip apre la categoria esatta già filtrata. <strong>Vedi tutti gli oggetti</strong> mostra tutte le categorie utilizzabili; Shoes, Men’s Shoes e Women’s Shoes sono categorie alternative dello stesso shoe slot.</div>
                <div><strong>Nessuno spoiler</strong>Finché il filtro è attivo, personaggi, categorie, preset automatici e oggetti futuri restano esclusi da schede, ricerca e catalogo.</div>
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
        buildTableOfContents();
        renderCharacterCards();
        if (catalogueData) {
            renderGrowthTable(catalogueData);
            renderCatalogue(catalogueData);
            renderReferenceCards(catalogueData);
            renderRecommendedEquipment(catalogueData);
        }
        maskLockedCharacterReferences(guide);
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
            const visible = Boolean(item && itemIsVisible(item));
            link.hidden = Boolean(item) && !visible;

            if (!visible) {
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

        guide.querySelectorAll(".item-link-list").forEach(function(list) {
            const links = Array.from(list.querySelectorAll("[data-item-ref]"));
            list.hidden = links.length > 0 && links.every(function(link) { return link.hidden; });
        });
    }

    function growthNumber(value) {
        const number = Number(value) || 0;
        return Number.isInteger(number) ? String(number) : number.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
    }

    function growthCell(value, index, values) {
        if (index === 0) {
            return `<td>${escapeHtml(growthNumber(value))}</td>`;
        }

        const combatValues = values.slice(1);
        const numericValue = Number(value) || 0;
        const highest = Math.max.apply(null, combatValues.map(function(entry) { return Number(entry) || 0; }));
        const lowest = Math.min.apply(null, combatValues.map(function(entry) { return Number(entry) || 0; }));
        let className = "";

        if (numericValue === highest) {
            className = " growth-cell-high";
        } else if (numericValue === lowest) {
            className = " growth-cell-low";
        }

        return `<td class="${className.trim()}">${escapeHtml(growthNumber(value))}</td>`;
    }

    function renderGrowthTable(data) {
        const target = guide.querySelector("#growth-table-dynamic");
        if (!target) {
            return;
        }

        const entries = (Array.isArray(data && data.character_growth) ? data.character_growth : []).filter(function(entry) {
            const member = getMemberByName(entry.name);
            return member && memberIsVisible(member) && Array.isArray(entry.base) && Array.isArray(entry.level_200);
        });
        const header = "<tr><th>Personaggio</th><th>HP</th><th>Atk</th><th>Arte Attack</th><th>Def</th><th>Arte Defense</th><th>Focus</th></tr>";

        if (!entries.length) {
            target.innerHTML = '<p class="muted">I dati di crescita diventano disponibili insieme alla scheda del personaggio.</p>';
            return;
        }

        function rows(field) {
            return entries.map(function(entry) {
                const values = entry[field];
                return `<tr data-spoiler-stage="${escapeHtml(entry.stage)}"><th scope="row">${escapeHtml(entry.name)}</th>${values.map(function(value, index) { return growthCell(value, index, values); }).join("")}</tr>`;
            }).join("");
        }

        target.innerHTML = `
            <p class="growth-legend"><span class="growth-key growth-key-high">Verde</span> crescita combattiva più alta per quel personaggio. <span class="growth-key growth-key-low">Rosso</span> crescita combattiva più bassa. HP non è colorato perché usa una scala separata.</p>
            <h4>Guadagno per livello</h4>
            <div class="table-wrap"><table class="compact-table growth-table"><thead>${header}</thead><tbody>${rows("base")}</tbody></table></div>
            <h4>Guadagno totale stimato al livello 200</h4>
            <p class="muted">Stima del solo guadagno dai livelli: il ritmo si dimezza oltre il livello 60 e si dimezza di nuovo oltre il livello 100.</p>
            <div class="table-wrap"><table class="compact-table growth-table"><thead>${header}</thead><tbody>${rows("level_200")}</tbody></table></div>
        `;
    }

    function renderRecommendedEquipment(data) {
        const target = guide.querySelector("#recommended-equipment-dynamic");
        if (!target) {
            return;
        }

        if (!data || data.complete !== true || !Array.isArray(data.recommended_equipment)) {
            target.innerHTML = '<p class="muted">Le schede personaggio saranno disponibili dopo il caricamento del catalogo locale.</p>';
            return;
        }

        const cards = visibleMembers().map(function(member) {
            const entries = data.recommended_equipment.filter(function(entry) {
                return entry.character === member.name;
            });
            const categories = Array.from(new Set(entries.map(function(entry) {
                return displayCategory(entry.category || "");
            }).filter(Boolean))).slice(0, 6);
            const sourceNotes = new Set(entries.map(function(entry) {
                return String(entry.source_note_group || "");
            }).filter(Boolean)).size;
            const href = `./character.html?character=${encodeURIComponent(member.name)}`;

            return `
                <article class="dossier-directory-card tone-${escapeHtml(member.tone)}">
                    <div class="dossier-directory-card-head">
                        <img src="${escapeHtml(member.image)}" alt="" loading="lazy" referrerpolicy="no-referrer" aria-hidden="true">
                        <div>
                            <p class="dossier-directory-kicker">Character dossier</p>
                            <h4>${escapeHtml(member.name)}</h4>
                            <p>${escapeHtml(member.role)}</p>
                        </div>
                    </div>
                    <p class="dossier-directory-copy">AI, Title, curva statistiche, suggerimenti per ogni slot e ${escapeHtml(sourceNotes)} note della guida tradotte.</p>
                    <div class="dossier-directory-chips">${categories.map(function(category) {
                        return `<span>${escapeHtml(categoryIcon(category))} ${escapeHtml(category)}</span>`;
                    }).join("")}</div>
                    <a class="dossier-directory-action" href="${escapeHtml(href)}">Apri la scheda di ${escapeHtml(member.name)} <span aria-hidden="true">→</span></a>
                </article>
            `;
        });

        target.innerHTML = `
            <div class="dossier-directory-intro">
                <p class="dossier-directory-kicker">Una pagina per alleato</p>
                <h4>Apri una scheda dedicata invece di leggere tutte le raccomandazioni insieme.</h4>
                <p>La scheda conserva i commenti importanti, ma li organizza per personaggio e per slot. Le note restano disponibili accanto agli oggetti a cui si riferiscono.</p>
            </div>
            <div class="dossier-directory-grid">${cards.join("")}</div>
        `;
    }

    function renderReferenceCards(data) {
        const target = guide.querySelector("#reference-cards-dynamic");
        if (!target) {
            return;
        }

        if (!data || data.complete !== true || !Array.isArray(data.items)) {
            target.innerHTML = '<p class="muted">Le schede rapide saranno disponibili dopo la creazione del catalogo locale completo.</p>';
            return;
        }

        const entries = (Array.isArray(data.reference_cards) ? data.reference_cards : []).filter(function(entry) {
            return !spoilerFilterEnabled || splitCharacterList(entry.character).some(isNamedCharacterVisible) || !entry.character || String(entry.character).includes("All");
        });
        const itemByKey = new Map(data.items.map(function(item) {
            return [`${item.category_id}|${item.rarity}|${normalizeText(item.name)}`, item];
        }));

        if (!entries.length) {
            target.innerHTML = '<p class="muted">Le schede rapide degli alleati non ancora sbloccati sono nascoste dal filtro anti-spoiler.</p>';
            return;
        }

        const phaseOrder = ["Main game", "Post-game"];
        target.innerHTML = phaseOrder.map(function(phase) {
            const phaseEntries = entries.filter(function(entry) {
                return entry.phase === phase;
            });

            if (!phaseEntries.length) {
                return "";
            }

            const cards = phaseEntries.map(function(entry) {
                const item = itemByKey.get(`${entry.category_id}|${entry.rarity}|${normalizeText(entry.name)}`);
                const href = item ? `#${itemId(item)}` : "#catalogo";
                const title = item ? item.name : entry.name;
                const category = displayCategory(entry.category || (item && item.category) || "Categoria");
                const character = visibleCharacterNames(entry.character || (item && item.character) || "");

                return `
                    <article class="noteworthy-card">
                        <p class="noteworthy-kicker">${escapeHtml(categoryIcon(category))} Noteworthy ${escapeHtml(category)}</p>
                        <h4><a href="${escapeHtml(href)}">${escapeHtml(title)}</a></h4>
                        <p class="noteworthy-meta">${character ? `${escapeHtml(character)} · ` : ""}Rarità ${escapeHtml(entry.rarity || "—")}</p>
                        <p>${escapeHtml(displayReferenceReason(entry.reason))}</p>
                    </article>
                `;
            }).join("");

            return `
                <section class="reference-phase-group">
                    <div class="reference-phase-heading">
                        <p class="reference-phase-kicker">${escapeHtml(phaseIcon(phase))} Fase della guida</p>
                        <h4>${escapeHtml(displayPhase(phase))}</h4>
                    </div>
                    <div class="noteworthy-list">${cards}</div>
                </section>
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
            return `<option value="${escapeHtml(category.id)}">${escapeHtml(displayCategory(category.label))}</option>`;
        }).join("");
        const characters = visibleMembers().map(function(member) { return member.name; });
        const characterOptions = characters.map(function(character) {
            return `<option value="${escapeHtml(character)}">${escapeHtml(character)}</option>`;
        }).join("") + "<option value=\"All\">Solo categorie universali (Rings/Shoes)</option>";

        target.innerHTML = `
            <div class="catalog-toolbar">
                <label for="catalog-search">Cerca nel catalogo</label>
                <input id="catalog-search" type="search" placeholder="Es. Brillante, Orc Kong, Atk, Adamantine" autocomplete="off">
                <label for="catalog-character">Personaggio</label>
                <select id="catalog-character"><option value="">Tutti visibili</option>${characterOptions}</select>
                <label for="catalog-category">Categoria</label>
                <select id="catalog-category"><option value="">Tutte le categorie visibili</option>${categoryOptions}</select>
                <label for="catalog-phase">Periodo</label>
                <select id="catalog-phase"><option value="">Storia principale e post-game</option><option value="Main game">Storia principale</option><option value="Post-game">Post-game</option></select>
                <label for="catalog-rarity">Rarità</label>
                <select id="catalog-rarity"><option value="">Tutte</option>${Array.from({ length: 21 }, function(_, i) { return `<option value="${i + 1}">${i + 1}</option>`; }).join("")}</select>
                <p id="catalog-status" class="catalog-status">${data.items.length} oggetti · ${categories.length} categorie visibili · dati locali.</p>
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
                            <td><span class="phase-badge">${escapeHtml(displayPhase(item.phase || "—"))}</span></td>
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
                        <summary><span>${escapeHtml(displayCategory(cat.label))}</span><small>${escapeHtml(displaySlot(cat.slot))} · ${escapeHtml(visibleCharacterNames(cat.character) || "Tutti")} · ${rows.length} oggetti</small></summary>
                        <div class="table-wrap"><table class="catalog-table"><thead><tr><th>Rarità</th><th>Oggetto<br><small>nome a +10</small></th><th>Periodo</th><th>Base</th><th>+10</th><th>Master Skill</th><th>Enhancement Bonus</th><th>Materiale principale</th><th>Provenienza</th></tr></thead><tbody>${body}</tbody></table></div>
                    </details>
                `;
            }).join("") || "<p class=\"muted\">Nessun oggetto visibile soddisfa questi filtri.</p>";

            status.textContent = `${matching.length} oggetti trovati · ${categories.length} categorie visibili.${spoilerFilterEnabled ? " Filtro anti-spoiler attivo." : ""}`;
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
            buildTableOfContents();
            return;
        }

        let count = 0;
        blocks.forEach(function(block) {
            const visible = normalizeText(visibleText(block)).includes(term);
            block.classList.toggle("is-filtered-out", !visible);
            if (visible) {
                count += 1;
            }
        });
        searchStatus.textContent = `${count} sezioni pertinenti.`;
        buildTableOfContents();
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
                applySpoilerMask();
                buildTableOfContents();
                renderCharacterCards();
                search.addEventListener("input", function() { filterGuide(search.value); });
                return loadJson();
            })
            .then(function(data) {
                catalogueData = data;
                renderGrowthTable(data);
                renderCategoryGuide();
                renderCatalogue(data);
                renderReferenceCards(data);
                renderRecommendedEquipment(data);
                maskLockedCharacterReferences(guide);
                scrollToGuideAnchor();
            })
            .catch(showError);
    }

    initializeTheme();
    initializeSpoilerState();
    initializeCatalogueDeepLink();
    loadGuide();
}());
