# Tales of Berseria — Guida completa all’Equipment

Sito GitHub Pages in italiano dedicato all’Equipment di *Tales of Berseria*. I nomi di Item, Monster, Skill, Arte, Acerite e località rimangono in inglese per coincidere con il gioco.

## Cosa contiene

- Percorso guidato per chi inizia, con decisioni pratiche e collegamenti tra i concetti.
- Spiegazione completa di statistiche, Rarity, Master Skills, Enhancement, Dismantle, Powder, Fluid, Armory Acerite, farming, Ignicite, Random Skills, Glacite e Sovereign Acerite.
- Catalogo locale di 18 categorie di Equipment, ricercabile e filtrabile per personaggio, categoria, periodo e Rarity.
- Valori a `+10`, Main Ingredient, Master Skill, Enhancement Bonus e Rare Drop per ogni Item disponibile nel catalogo.
- Schede di riferimento collegate direttamente al catalogo per confrontare rapidamente gli Item nelle fasi avanzate della storia e nel post-game.

## Pubblicazione

1. Estrai l’archivio e carica il contenuto in un repository GitHub.
2. Pubblica nel branch `main`.
3. In **Settings → Pages**, seleziona **GitHub Actions** come sorgente.
4. Il workflow crea `site/content/catalogo.json`, convalida il sito e poi pubblica l’artifact.

Il browser carica esclusivamente file locali pubblicati con il sito. Il catalogo non viene interrogato né costruito lato client.

## Controlli della build

La pubblicazione viene bloccata quando:

- non sono presenti tutte le 18 categorie;
- il catalogo contiene meno di 350 Item;
- una scheda non ha i campi essenziali;
- i valori `+10` non coincidono con la formula di distribuzione dei 100 punti di Enhancement;
- una pagina pubblicata contiene collegamenti esterni;
- mancano gli anchor essenziali o i collegamenti interni della guida.

## Anteprima locale

Per vedere la parte statica della guida:

```bash
python -m http.server 8000 --directory site
```

Apri `http://localhost:8000/`. Il catalogo completo viene creato dal workflow di build e incluso nell’artifact pubblicato.
