# Audit di pubblicazione e contenuto

## Architettura

| Workflow | Rete durante il job | Output | Scopo |
|---|---:|---|---|
| `Refresh catalog snapshot` | Sì, per creare una nuova snapshot | Commit di `site/content/catalogo.json` + deploy | Aggiornare intenzionalmente i dati locali. |
| `Deploy GitHub Pages` | Solo al primo bootstrap, quando il JSON è un segnaposto | Snapshot validata + artifact statico | Materializzare una volta il catalogo locale, poi pubblicare il JSON già committato ai push successivi. |

Il browser riceve il testo e il catalogo come file locali. Le sole richieste esterne ammesse nel client sono sei URL immagine approvati dell’Aselia Wiki / Fandom, usati per gli avatar delle schede personaggi; non sono immagini generate con IA. Nessuna pagina pubblicata contiene riferimenti a GameFAQs/GameSpot.

## Contratto del catalogo

La snapshot viene rifiutata se non soddisfa tutti questi vincoli:

| Vincolo | Valore richiesto |
|---|---:|
| Categorie | 18 |
| Item | 350 esatti |
| Fasi per categoria | Main game e Post-game |
| Coppie categoria/fase | 36 esatte |
| Schede rapide | 36 esatte, senza duplicati |
| Tier post-game | R19, R20, R21 |
| Vettore statistiche | 5 valori base e 5 valori `+10` |
| Integrità | SHA-256 delle righe normalizzate |

## Correzioni concettuali bloccate dal codice o esplicitate nella guida

- `+N` aggiunge punti statistica; non è una percentuale.
- I valori `+10` usano il troncamento per singola statistica e possono quindi mostrare 99 punti aggiunti totali.
- `Rarity`, livello `+N` e Random Skill Rank sono tre concetti indipendenti.
- Per R1–R18, la regola Common/Rare è collegata alla parità; R19–R21 non usano questa scorciatoia.
- `Matching` significa stessa Rarity, non stesso Main Ingredient.
- Dismantle separa il rendimento da `+N` dal Fluid determinato dal Rank delle Random Skills.
- Il filtro di un personaggio include le categorie universali `All`.
- Sovereign richiede un tipo di Item già registrato a `+10`; gli esemplari idonei successivi devono essere Monster drop, non acquisti da shop.
- Il filtro anti-spoiler è attivo per default, usa una progressione senza nomi o conteggi futuri e nasconde schede, righe della guida, categorie, Item e filtri non ancora rilevanti.
- Le uniche immagini remote sono i sei cut-in delle schede; ogni altro URL esterno nel client causa errore di validazione.

## Limite dichiarato della provenienza

La snapshot conserva sempre il Monster quando la tabella strutturata registra un `Rare drop`. Per tutte le righe senza Monster non dichiara una località fittizia: mostra invece `Common drop`, `Chest / storia` o una regola post-game. Questo evita di trasformare dati mancanti in istruzioni sbagliate per un nuovo giocatore.

## Cross-reference hotfix

- Corrected the farming-link target from `Velvet Amphibole Belt` to the canonical catalogue name `Amphibole Belt`.
- The validator remains strict: every `data-item-ref` in the guide must resolve to a committed Equipment row after the catalogue snapshot is built.
