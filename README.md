# Tales of Berseria — Guida completa all’Equipment

Sito GitHub Pages in italiano dedicato all’Equipment di *Tales of Berseria*. I nomi di Item, Monster, Skill, Arte, Acerite e località restano in inglese per coincidere con il gioco.

## Per chi è la guida

La lettura parte da una domanda pratica: cosa indossare adesso. Poi collega, nell’ordine, statistiche, Master Skills, Enhancement, materiali, Dismantle, farming e post-game. Il catalogo serve soltanto quando hai una domanda precisa su un Item o un Monster.

## Cosa contiene

- percorso iniziale con decisioni sicure per una prima run;
- spiegazione separata di Rarity, livello `+N` e Rank delle Random Skills;
- limiti degli Smith, costi, ricette `Common` e `Rare` fino a `+10`;
- Dismantle, Main Ingredient, Powder, Fluid, Armory e Alchemist’s Acerite;
- farming, Mystic Artes, Common Target, shop reset, Ignicite e Equipment da farming;
- Random Skills, Glacite e Sovereign Acerite;
- catalogo locale filtrabile con 18 categorie e 350 Item;
- 34 schede rapide di confronto: una per ogni combinazione categoria/fase realmente presente;
- link interni da consigli, ricette e farming alle sezioni e agli Item corrispondenti.

## Pubblicazione

1. Estrai l’archivio e sostituisci il contenuto del repository.
2. In **Settings → Pages**, seleziona **GitHub Actions** come sorgente.
3. In **Settings → Actions → General → Workflow permissions**, seleziona **Read and write permissions**: il primo deploy salva nel repository il catalogo locale verificato.
4. Fai commit e push su `main`.

Non devi eseguire workflow manuali. Se `catalogo.json` è il segnaposto iniziale, **Deploy GitHub Pages** materializza il catalogo, lo valida, lo committa e poi pubblica l’artefatto già completo. Dai push successivi viene controllato e pubblicato soltanto il JSON locale già committato.

Per aggiornare volontariamente la snapshot in futuro, puoi usare **Actions → Refresh catalog snapshot → Run workflow**.

## Garanzie bloccanti

Il deploy non parte se il catalogo locale non contiene:

- esattamente 18 categorie;
- esattamente 350 Item;
- tutte le 34 combinazioni categoria/fase realmente presenti nelle tabelle sorgente;
- statistiche base e valori `+10` coerenti;
- Master Skill, Enhancement Bonus, Main Ingredient, Rare Drop, tipo di provenienza e testo di provenienza;
- tutte le schede rapide categoria/fase;
- un hash di integrità corrispondente alle righe committate;
- tutti i riferimenti della guida a Item realmente presenti;
- anchor e collegamenti interni validi;
- nessun URL o riferimento esterno nei file pubblicati.

## Provenienza nel catalogo

La colonna **Provenienza** distingue tra `Rare drop` con Monster registrato, `Common drop`, chest/storia e fonti post-game. Se non esiste un Monster registrato, la guida dichiara la regola di acquisizione invece di inventare area o chest.

## Anteprima locale

Per vedere la guida prima della prima snapshot:

```bash
python -m http.server 8000 --directory site
```

Apri `http://localhost:8000/`. Prima del primo deploy, il catalogo mostra un messaggio esplicito. Il primo deploy materializza e committa automaticamente il file locale completo.
