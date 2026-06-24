# Tales of Berseria — Equipment Guide

A self-hosted, responsive edition of **TheDarkn1ght's Tales of Berseria Equipment Guide**.

The source guide is preserved in two forms when the import workflow runs:

- `archive/gamefaqs-print.html`: complete printable-page archive;
- `site/content/guide.html`: extracted guide content used by the reader;
- `site/archive/guide-original.txt`: plain-text archive for long-term access.

The reader provides a searchable table of contents, keyboard-friendly navigation, responsive tables, a light/dark theme toggle, and a direct link to the preserved original text. No guide content is intentionally rewritten or discarded during import.

## Publish it with GitHub Pages

1. Create an empty **public** GitHub repository named `tales-of-berseria-equipment-guide`.
2. Extract this archive, then publish the folder with GitHub Desktop.
3. In the repository, open **Settings → Pages** and set **Build and deployment → Source** to **GitHub Actions**.
4. Open **Actions → Archive GameFAQs guide and deploy → Run workflow**.
5. After the workflow succeeds, open **Settings → Pages → Visit site**.

The workflow retrieves the guide from its printable GameFAQs view, saves the complete page archive, extracts the author content, commits the files, and deploys the static site in the same run.

If GitHub refuses the archive workflow's commit, open **Settings → Actions → General → Workflow permissions** and allow read/write workflow permissions, then run it again.

## Updating the source archive

Run **Archive GameFAQs guide and deploy** again. It replaces the preserved source files only when the page changes, commits the result, and deploys the refreshed site.

## Ownership and attribution

Guide text © 2018–2026 **TheDarkn1ght**. All rights reserved.

This repository deliberately preserves the original byline, version history, acknowledgement text, and a link to the GameFAQs publication. *Tales of Berseria* and related names are trademarks of their respective owners.
