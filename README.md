# Tales of Berseria — Guida all'equipaggiamento

Versione italiana statica, pronta per GitHub Pages.

Il progetto non scarica contenuti durante la pubblicazione: guida, tabelle, ricerca e indice sono tutti inclusi nella cartella `site/`.

## Pubblicazione su GitHub Pages

1. Crea un repository GitHub e carica questi file nel branch `main`.
2. Apri **Settings → Pages** e seleziona **GitHub Actions** come sorgente di pubblicazione.
3. Effettua un push su `main`, oppure avvia manualmente il workflow **Pubblica il sito su GitHub Pages** dalla scheda **Actions**.
4. Al termine del workflow, GitHub mostrerà l'indirizzo pubblico del sito.

## Avvio locale

Non servono dipendenze. Apri `site/index.html` in un browser oppure avvia un server statico dalla radice del progetto:

```bash
python -m http.server 8000 --directory site
```

Poi visita `http://localhost:8000`.

## Struttura

- `site/index.html` — shell della pagina.
- `site/content/guide.html` — testo della guida in italiano.
- `site/assets/site.css` — stile responsive.
- `site/assets/site.js` — indice automatico, ricerca nel testo e tema chiaro/scuro.
- `.github/workflows/deploy-pages.yml` — pubblicazione automatica su GitHub Pages.

## Nota sui nomi

I nomi di Monster, Item, Skill, Arte, Acerite, stat e località del gioco restano in inglese per permettere una ricerca immediata in gioco.
