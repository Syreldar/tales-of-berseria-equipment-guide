#!/usr/bin/env python3
"""Run lightweight integrity checks for the static guide."""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
TEXT_FILES = [
    path
    for path in ROOT.rglob("*")
    if path.is_file()
    and path != Path(__file__).resolve()
    and path.suffix.lower() in {".html", ".md", ".js", ".css", ".yml", ".yaml", ".py"}
]

FORBIDDEN_PATTERNS = [
    re.compile(r"gamefaqs", re.IGNORECASE),
    re.compile(r"gamespot\.com", re.IGNORECASE),
    re.compile(r'<a\b[^>]*\bhref=[\"\'][a-z][a-z0-9+.-]*://', re.IGNORECASE),
    re.compile(r"import_guide", re.IGNORECASE),
]

REQUIRED_GUIDE_TEXT = [
    "Enhancement: cosa aumenta davvero",
    "Smantellamento: cosa ricevi e perché +1 conviene",
    "Come mirare un Common drop preciso",
    "Random Skills: cosa sono e quando diventano importanti",
    "Sovereign Acerite",
]


def main() -> int:
    failures: list[str] = []

    for path in TEXT_FILES:
        relative = path.relative_to(ROOT)
        content = path.read_text(encoding="utf-8")

        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(content):
                failures.append(f"{relative}: pattern non consentito: {pattern.pattern}")

    guide = ROOT / "site" / "content" / "guide.html"

    if not guide.exists():
        failures.append("site/content/guide.html non trovato")
    else:
        guide_text = guide.read_text(encoding="utf-8")

        for required_text in REQUIRED_GUIDE_TEXT:
            if required_text not in guide_text:
                failures.append(f"guida: sezione mancante: {required_text}")

        section_count = guide_text.count("<section>")

        if section_count < 12:
            failures.append(f"guida: sezioni insufficienti ({section_count}, attese almeno 12)")

        table_count = guide_text.count("<table>")

        if table_count < 15:
            failures.append(f"guida: tabelle insufficienti ({table_count}, attese almeno 15)")

    if failures:
        print("Verifica non superata:", file=sys.stderr)

        for failure in failures:
            print(f"- {failure}", file=sys.stderr)

        return 1

    print("Verifica superata.")
    print(f"- File controllati: {len(TEXT_FILES)}")
    print(f"- Sezioni guida: {section_count}")
    print(f"- Tabelle guida: {table_count}")
    print("- Nessun riferimento esterno o importatore rilevato.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
