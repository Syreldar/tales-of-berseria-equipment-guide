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
- 36 schede rapide di confronto: una per ogni combinazione categoria/fase;
- link interni da consigli, ricette e farming alle sezioni e agli Item corrispondenti.

## Pubblicazione corretta

Il progetto usa due workflow diversi per evitare che un deploy normale dipenda dalla rete o rigeneri dati non revisionati.

1. Estrai l’archivio e sostituisci il contenuto del repository.
2. Fai commit e push su `main`.
3. In **Settings → Pages**, seleziona **GitHub Actions** come sorgente.
4. In **Settings → Actions → General → Workflow permissions**, seleziona **Read and write permissions**: `Snapshot catalog` deve poter committare il JSON verificato.
5. Apri **Actions → Snapshot catalog → Run workflow** sul branch `main`.
6. Il workflow genera il catalogo locale, lo controlla, lo committa e pubblica il sito.
7. Da quel momento, ogni push esegue soltanto **Deploy GitHub Pages**: convalida il JSON già committato e pubblica file statici.

Il primo push può far fallire il deploy normale perché `catalogo.json` è volutamente un segnaposto. È previsto: non pubblica mai un catalogo parziale. Esegui `Snapshot catalog` una volta; il workflow effettua anche il deploy finale.

## Garanzie bloccanti

Il deploy non parte se il catalogo locale non contiene:

- esattamente 18 categorie;
- esattamente 350 Item;
- entrambe le fasi per ogni categoria, per un totale di 36 combinazioni;
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

Apri `http://localhost:8000/`. Prima della snapshot, la guida funziona ma il catalogo mostra un messaggio esplicito. Dopo `Snapshot catalog`, il file locale completo è incluso nel repository e nella pagina pubblicata.
