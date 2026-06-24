# Audit di pubblicazione

## Regola fondamentale

Il deploy non contatta né dipende da GameFAQs. Il catalogo viene trasformato in `site/content/catalogo.json` prima della pubblicazione e il browser legge soltanto questo file locale.

## Controlli bloccanti

Il workflow rifiuta l’artifact quando non trova:

- 18 categorie di Equipment;
- almeno 350 Item;
- valori base e `+10` coerenti;
- Master Skill, Enhancement Bonus, Main Ingredient e acquisizione per ogni scheda;
- almeno due schede di riferimento per ciascuna categoria;
- anchor interni validi e tutte le sezioni didattiche richieste.

## Limite dichiarato dei dati di acquisizione

Il catalogo conserva sempre il `Rare Drop` quando presente nella tabella strutturata. Per gli Item senza una fonte puntuale disponibile nel dato strutturato, l’interfaccia dichiara esplicitamente che l’acquisizione va verificata in-game; non inventa Monster, chest, shop o località.
