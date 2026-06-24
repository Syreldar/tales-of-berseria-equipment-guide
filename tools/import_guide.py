#!/usr/bin/env python3
"""Archive the author-owned GameFAQs guide and generate the static reader inputs."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

DEFAULT_SOURCE_URL = "https://gamefaqs.gamespot.com/pc/184665-tales-of-berseria/faqs/74517?print=1"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def ensure_print_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    query = parse_qs(parsed.query)
    query["print"] = ["1"]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def clean_fragment(fragment_html: str) -> str:
    soup = BeautifulSoup(fragment_html, "html.parser")

    for unwanted in soup.find_all(["script", "style", "noscript", "iframe"]):
        unwanted.decompose()

    for element in soup.find_all(True):
        for attribute in list(element.attrs):
            if attribute.lower().startswith("on"):
                del element.attrs[attribute]

        if element.has_attr("href"):
            href = str(element["href"]).strip()

            if href and not (href.startswith("#") or href.startswith("/") or re.match(r"^https?://", href, re.IGNORECASE)):
                del element.attrs["href"]

    return str(soup).strip()


def fragment_to_text(fragment_html: str) -> str:
    soup = BeautifulSoup(fragment_html, "html.parser")
    text = soup.get_text("\n", strip=False)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def choose_guide_fragment(page) -> str:
    rich = page.locator(".faqtext").first

    if rich.count() > 0:
        tag_name = rich.evaluate("element => element.tagName.toLowerCase()")

        if tag_name == "pre":
            return f"<pre>{html.escape(rich.inner_text())}</pre>"

        return rich.inner_html()

    spans = page.locator('[id^="faqspan-"]')

    if spans.count() > 0:
        text = "\n".join(spans.nth(index).inner_text() for index in range(spans.count()))
        return f"<pre>{html.escape(text)}</pre>"

    pre_tags = page.locator("pre")

    if pre_tags.count() > 0:
        longest = max(
            (pre_tags.nth(index).inner_text() for index in range(pre_tags.count())),
            key=len,
        )
        return f"<pre>{html.escape(longest)}</pre>"

    raise RuntimeError("Could not locate the guide content in the printable page.")


def fetch_source(source_url: str) -> tuple[str, str]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1440, "height": 1800},
                locale="en-US",
            )
            page = context.new_page()

            try:
                page.goto(source_url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_selector(".faqtext, [id^='faqspan-'], pre", timeout=25_000)
            except PlaywrightTimeoutError as exc:
                raise RuntimeError(
                    "GameFAQs did not provide the printable guide content before the timeout. "
                    "Retry the workflow later."
                ) from exc

            full_page_html = page.content()
            guide_fragment = choose_guide_fragment(page)
            return full_page_html, guide_fragment
        finally:
            browser.close()


def write_if_changed(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False

    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    source_url = ensure_print_url(args.source_url)
    full_page_html, guide_fragment = fetch_source(source_url)
    clean_html = clean_fragment(guide_fragment)
    plain_text = fragment_to_text(clean_html)
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()

    manifest = {
        "author": "TheDarkn1ght",
        "source_url": source_url,
        "original_version": "1.5",
        "original_last_updated": "2018-12-12",
        "archived_at": generated_at,
        "notes": "The original printable page is preserved separately; the reader uses the extracted author content.",
    }

    files = {
        root / "archive" / "gamefaqs-print.html": full_page_html,
        root / "site" / "archive" / "gamefaqs-print.html": full_page_html,
        root / "site" / "content" / "guide.html": clean_html + "\n",
        root / "site" / "archive" / "guide-original.txt": plain_text,
        root / "site" / "content" / "manifest.json": json.dumps(manifest, indent=2) + "\n",
    }

    changed = []

    for path, content in files.items():
        if write_if_changed(path, content):
            changed.append(path.relative_to(root).as_posix())

    print("Updated files:" if changed else "No source changes detected.")

    for path in changed:
        print(f"- {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
