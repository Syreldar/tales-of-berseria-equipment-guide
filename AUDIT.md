# Audit di pubblicazione e contenuto

## Architettura

| Workflow | Rete durante il job | Output | Scopo |
|---|---:|---|---|
| `Snapshot catalog` | Solo per creare una nuova snapshot | Commit di `site/content/catalogo.json` + deploy | Aggiornare intenzionalmente i dati locali. |
| `Deploy GitHub Pages` | Nessuna acquisizione del catalogo | Artifact statico | Pubblicare esclusivamente il JSON già revisionato e committato. |

Il browser riceve soltanto file locali. Nessuna pagina pubblicata contiene URL esterni o riferimenti alla fonte di consultazione.

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

## Limite dichiarato della provenienza

La snapshot conserva sempre il Monster quando la tabella strutturata registra un `Rare drop`. Per tutte le righe senza Monster non dichiara una località fittizia: mostra invece `Common drop`, `Chest / storia` o una regola post-game. Questo evita di trasformare dati mancanti in istruzioni sbagliate per un nuovo giocatore.
