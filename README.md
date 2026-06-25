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
- 36 schede rapide di confronto: una per ogni combinazione categoria/fase della guida;
- link interni da consigli, ricette e farming alle sezioni e agli Item corrispondenti;
- schede personaggi con avatar online, sfondi tematici e collegamento diretto ai filtri del catalogo;
- filtro anti-spoiler attivo per impostazione predefinita: nasconde nome, avatar, ruolo, categorie e Item degli alleati non ancora sbloccati.

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
- tutte le 36 combinazioni categoria/fase realmente presenti nelle tabelle sorgente;
- statistiche base e valori `+10` coerenti;
- Master Skill, Enhancement Bonus, Main Ingredient, Rare Drop, tipo di provenienza e testo di provenienza;
- tutte le schede rapide categoria/fase;
- un hash di integrità corrispondente alle righe committate;
- tutti i riferimenti della guida a Item realmente presenti;
- anchor e collegamenti interni validi;
- nessun URL o riferimento a GameFAQs/GameSpot nei file pubblicati;
- solo URL immagine approvati per le sei schede personaggi, senza immagini generate con IA.

## Filtro anti-spoiler

Il filtro è attivo al primo accesso e salva localmente la scelta. Il pulsante **Ho sbloccato un nuovo alleato** aumenta la progressione senza mostrare in anticipo il prossimo nome. Finché il filtro resta attivo, la pagina non mostra nemmeno quanti alleati mancano: compare una sola scheda `???` generica. Anche il catalogo nasconde categorie, filtri, Item, schede rapide e righe della guida legati a personaggi non ancora sbloccati. `Rings` e `Shoes` restano disponibili perché universali.

Le immagini delle schede sono online, non generate: il browser carica i cut-in da Aselia Wiki / Fandom. I dettagli e le pagine media sono in [`ASSET_SOURCES.md`](ASSET_SOURCES.md).

## Provenienza nel catalogo

La colonna **Provenienza** distingue tra `Rare drop` con Monster registrato, `Common drop`, chest/storia e fonti post-game. Se non esiste un Monster registrato, la guida dichiara la regola di acquisizione invece di inventare area o chest.

## Anteprima locale

Per vedere la guida prima della prima snapshot:

```bash
python -m http.server 8000 --directory site
```

Apri `http://localhost:8000/`. Prima del primo deploy, il catalogo mostra un messaggio esplicito. Il primo deploy materializza e committa automaticamente il file locale completo.

### Cross-reference validation

The validation step intentionally fails if an Equipment link in the written guide does not match an Item name in the local catalogue. This protects in-page navigation from silently pointing to a missing row. The current guide uses the canonical Item name `Amphibole Belt`.

## Schede personaggi e filtro anti-spoiler

Le schede personaggi usano **illustrazioni online** caricate dal browser tramite URL esterni e non includono immagini generate con IA. Le fonti delle immagini sono documentate in `ASSET_SOURCES.md`.

Il filtro anti-spoiler è attivo per impostazione predefinita. Nasconde nome, immagine, ruolo, categorie, righe della guida e Item del catalogo relativi agli alleati non ancora indicati come sbloccati. Il pulsante `Ho sbloccato un alleato` avanza di una sola scheda senza mostrare in anticipo chi arriverà dopo. La preferenza e il progresso restano solo nel browser dell’utente tramite `localStorage`.
