# Tales of Berseria — Guida completa all’Equipment

Sito statico italiano per GitHub Pages. Spiega l’Equipment da zero e include un catalogo completo filtrabile per Item, categoria, Rarity, statistiche, Master Skill, Enhancement Bonus, Main Ingredient e Rare drop.

## Pubblicazione

1. Crea un repository GitHub vuoto e carica il contenuto di questa cartella nel branch `main`.
2. In **Settings → Pages**, seleziona **GitHub Actions** come sorgente.
3. Apri la scheda **Actions** e avvia oppure attendi `Build and deploy GitHub Pages`.
4. Il workflow genera `site/content/catalogo.json`, verifica che siano presenti tutte le 18 categorie e almeno 300 Item, poi pubblica il sito.

Il deploy si interrompe intenzionalmente quando il catalogo non è completo: non viene mai pubblicata una versione parziale.

## Sviluppo locale

Il file principale è `site/index.html`. Per testarlo con il catalogo completo:

```bash
python -m pip install requests beautifulsoup4
python tools/build_catalog.py --output site/content/catalogo.json
python tools/verify_site.py
python -m http.server --directory site 8000
```

Poi apri `http://localhost:8000` nel browser. Il server locale è necessario perché il sito carica guida e catalogo tramite `fetch`.

## Struttura

- `site/content/guide.html` — testo completo della guida in italiano.
- `site/content/catalogo.json` — database locale generato durante build/deploy.
- `site/assets/site.js` — ricerca, indice, tema e rendering del catalogo.
- `tools/build_catalog.py` — generatore del catalogo.
- `tools/verify_site.py` — controlli contro cataloghi incompleti, link esterni pubblicati e riferimenti non consentiti.
- `.github/workflows/deploy-pages.yml` — build, validazione e deploy.

## Note editoriali

I nomi di Monster, Item, Skill, Arte, Acerite e località restano in inglese per essere riconoscibili nel gioco. Il testo, le istruzioni e le spiegazioni sono in italiano.
