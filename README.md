# Tales of Berseria — Guida all'equipaggiamento

Guida italiana statica per GitHub Pages. Il contenuto è locale: la pubblicazione non scarica guide, archivi o dati da siti esterni.

## Contenuto della revisione

- spiegazione per principianti del ciclo `Equipment → Enhancement → Dismantle`;
- tabelle controllate per punti di Enhancement, costi, materiali e ricompense di smantellamento;
- strategie di farming, Ignicites e `Equipment drop rates +X`;
- tutte le 18 categorie di Equipment e una selezione ragionata di Item notevoli;
- sezione post-game su `Random Skills`, `Equipment Maximization` e `Sovereign Acerite`;
- controllo automatico che impedisce riferimenti a forum, URL esterni o dipendenze dal vecchio importatore.

I nomi di Monster, Item, Skill, Arte, Acerite, Stat e località rimangono in inglese per essere cercabili direttamente nel gioco.

## Pubblicazione su GitHub Pages

1. Crea un repository GitHub e carica questi file nel branch `main`.
2. Apri **Settings → Pages** e seleziona **GitHub Actions** come sorgente di pubblicazione.
3. Esegui un push su `main`, oppure avvia manualmente il workflow **Pubblica il sito su GitHub Pages** nella scheda **Actions**.
4. Al termine del workflow, GitHub mostra l'indirizzo pubblico del sito.

## Avvio locale

Non sono richieste dipendenze. Per evitare le restrizioni del browser sulle richieste locali, esegui dalla radice del progetto:

```bash
python -m http.server 8000 --directory site
```

Poi apri `http://localhost:8000`.

## Struttura

- `site/index.html` — pagina principale;
- `site/content/guide.html` — guida italiana;
- `site/assets/site.css` — stile responsive;
- `site/assets/site.js` — indice, ricerca e tema;
- `.github/workflows/deploy-pages.yml` — deploy automatico;
- `AUDIT.md` — controllo di copertura e correzioni;
- `tools/verify_site.py` — verifica locale del progetto.
