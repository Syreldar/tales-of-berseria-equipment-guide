# Audit di copertura

## Obiettivo della revisione

Il sito è costruito come guida completa, non come selezione di consigli. Il testo didattico spiega l’ordine corretto con cui un nuovo giocatore incontra i sistemi; il catalogo generato contiene l’elenco integrale delle categorie di Equipment.

## Controlli bloccanti prima del deploy

Il workflow verifica che:

- siano presenti le 18 categorie di Equipment;
- il catalogo abbia almeno 300 Item;
- ogni Item abbia categoria, Rarity, statistiche base, Master Skill, Enhancement Bonus, materiale, indicazione di acquisizione e nome a `+10`;
- le 13 sezioni essenziali della guida esistano;
- le pagine pubblicate non contengano collegamenti esterni o riferimenti non consentiti.

Se uno di questi controlli fallisce, GitHub Pages non viene pubblicato.

## Copertura del testo

La guida include: statistiche e Rarity; limiti Smith’s Acerite; punti e costi di Enhancement; materiali di tutte le Rarity; Dismantle; ricette Common e Rare; Armory Acerite; difficoltà e drop; Ignicite; Equipment da farming; Common Target; catalogo; priorità per la prima run; Random Skills; Glacite; Sovereign Acerite; checklist finale.
