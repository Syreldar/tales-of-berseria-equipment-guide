# Tales of Berseria — Guida completa all’Equipment

Sito GitHub Pages in italiano dedicato all’Equipment di *Tales of Berseria*. I nomi di Item, Monster, Skill, Arte, Acerite e località rimangono in inglese per coincidere con il gioco.

## Cosa contiene

- Percorso guidato per chi inizia, con decisioni pratiche e collegamenti tra i concetti.
- Spiegazione completa di statistiche, Rarity, Master Skills, Enhancement, Dismantle, Powder, Fluid, Armory Acerite, farming, Ignicite, Random Skills, Glacite e Sovereign Acerite.
- Catalogo locale completo delle 18 categorie di Equipment, ricercabile e filtrabile per personaggio, categoria, periodo e Rarity.
- Valori esatti a `+10`, Main Ingredient, Master Skill, Enhancement Bonus e fonte di acquisizione per ogni Item.
- Selezione degli Item notevoli collegata direttamente alle rispettive schede.

## Pubblicazione

1. Estrai l’archivio e carica il contenuto in un repository GitHub.
2. Pubblica nel branch `main`.
3. In **Settings → Pages**, seleziona **GitHub Actions** come sorgente.
4. Il workflow genera il catalogo statico prima del deploy e interrompe la pubblicazione se la copertura non è completa.

Il browser carica esclusivamente file locali pubblicati con il sito. Il catalogo non viene interrogato né costruito lato client; il workflow lo genera prima dell’upload e pubblica solo l’output convalidato.

## Controlli della build

La pubblicazione viene bloccata quando:

- non sono presenti tutte le 18 categorie;
- il catalogo contiene meno di 350 Item;
- una scheda non ha i campi essenziali;
- i valori `+10` non coincidono con la formula di distribuzione dei 100 punti di Enhancement;
- una pagina pubblicata contiene collegamenti esterni o riferimenti alla fonte di lavoro;
- mancano gli anchor essenziali o i collegamenti interni della guida.

## Anteprima locale

```bash
python -m http.server 8000 --directory site
```

Apri `http://localhost:8000/`. La copia del repository mostra il testo della guida; il catalogo completo appare dopo la build del workflow, che materializza `site/content/catalogo.json` prima della pubblicazione.
