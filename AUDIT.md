# Audit di completezza

## Contenuto pubblicato

La guida pubblicata è priva di link e riferimenti esterni alla fonte di lavoro. Tutti i dati mostrati dal browser sono contenuti nei file del sito pubblicato.

## Catalogo

La build genera un JSON locale che deve contenere:

- 18 categorie: 6 Weapons, 6 Accessories, 2 Armor, Rings e 3 Footwear;
- almeno 350 schede Equipment;
- Rarity, periodo Main game/Post-game, statistiche base, statistiche esatte a `+10`, Master Skill, Enhancement Bonus, Main Ingredient e acquisizione;
- selezione delle schede notevoli per la progressione.

Il validatore interrompe il deploy se una di queste condizioni non è rispettata.

## Revisione per novizi

Le spiegazioni collegano esplicitamente:

- Rarity → Main Ingredient → donor Matching → ricette di Enhancement;
- Random Skill Rank → Fluid → costo dei Rare;
- Monster/Chest/Shop → catalogo → Common Target;
- Item da farming → singole schede del catalogo;
- soglie Smith’s Acerite → obiettivi `+3`, `+6`, `+9` e `+10`.

## Garanzie di pubblicazione

Il file `catalogo.json` incluso nel repository è intenzionalmente un segnaposto non pubblicabile. La build deve sostituirlo con il catalogo statico completo; in caso contrario, la validazione fallisce e GitHub Pages non riceve alcun artifact. Questo evita di esporre una copia parziale o di eseguire importazioni nel browser.
