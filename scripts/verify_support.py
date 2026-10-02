#!/usr/bin/env python3
"""Bounded source checks for the two static support pages, not release/device QA."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES = {ROOT / "support/index.html": "de", ROOT / "en/support/index.html": "en"}
CSS_PATH = ROOT / "assets/support.css"
MAILTO = "mailto:schenkei@hunchagent.io"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class SupportPage(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str]]] = []
        self.ids: set[str] = set()
        self.errors: list[str] = []
        self.stack: list[str] = []
        self.has_doctype = False
        self.text: list[str] = []

    def handle_decl(self, decl: str) -> None:
        self.has_doctype = decl.lower() == "doctype html"

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.elements.append((tag, values))
        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.errors.append(f"Duplicate ID: {element_id}")
            self.ids.add(element_id)
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"Unbalanced closing tag: {tag}")
        else:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def local_target(page: Path, ref: str) -> Path:
    parsed = urlsplit(ref)
    if parsed.scheme or parsed.netloc:
        raise ValueError(f"Non-local resource: {ref}")
    target = (page.parent / unquote(parsed.path)).resolve() if parsed.path else page
    if not target.is_relative_to(ROOT):
        raise ValueError(f"Reference leaves website: {ref}")
    if target.is_dir():
        target /= "index.html"
    return target


def validate_page(path: Path, language: str) -> list[str]:
    errors: list[str] = []
    source = path.read_text(encoding="utf-8")
    page = SupportPage()
    page.feed(source)
    page.close()
    errors.extend(page.errors)
    if page.stack:
        errors.append(f"Unclosed elements: {page.stack}")
    if not page.has_doctype:
        errors.append("Missing HTML doctype")
    if [(tag, attrs.get("lang")) for tag, attrs in page.elements if tag == "html"] != [("html", language)]:
        errors.append("Wrong document language")
    if sum(tag == "main" for tag, _ in page.elements) != 1 or sum(tag == "h1" for tag, _ in page.elements) != 1:
        errors.append("Require exactly one main and one h1")
    if not any(tag == "meta" and attrs.get("charset", "").lower() == "utf-8" for tag, attrs in page.elements):
        errors.append("Missing UTF-8 declaration")
    viewport = next((attrs.get("content", "") for tag, attrs in page.elements if tag == "meta" and attrs.get("name") == "viewport"), "")
    if "width=device-width" not in viewport or re.search(r"user-scalable\s*=\s*no|maximum-scale", viewport):
        errors.append("Missing responsive viewport or restricted zoom")
    if len(source.encode("utf-8")) > 12_000:
        errors.append("HTML payload exceeds 12 KB per language")

    stylesheet_count = 0
    mailto_count = 0
    language_targets: list[Path] = []
    for tag, attrs in page.elements:
        if tag in {"script", "iframe", "form", "input", "textarea", "video", "audio", "img", "object", "embed", "base"}:
            errors.append(f"Unexpected executable, data collection or media element: {tag}")
        if any(key.startswith("on") or key == "style" for key in attrs):
            errors.append("Unexpected inline handler or style")
        if tag == "nav" and not attrs.get("aria-label"):
            errors.append("Navigation needs an accessible name")
        for key in ("aria-labelledby", "aria-describedby", "aria-controls"):
            for element_id in attrs.get(key, "").split():
                if element_id not in page.ids:
                    errors.append(f"Missing ARIA target: {element_id}")
        if tag not in {"a", "link"}:
            continue
        ref = attrs.get("href", "")
        if not ref:
            errors.append(f"Missing href on {tag}")
            continue
        if ref.startswith("mailto:"):
            if tag != "a" or ref != MAILTO:
                errors.append("Unexpected contact target or prefilled private mail content")
            mailto_count += 1
            continue
        try:
            target = local_target(path, ref)
            if not target.is_file():
                errors.append(f"Missing local target: {ref}")
            if urlsplit(ref).fragment and target == path and unquote(urlsplit(ref).fragment) not in page.ids:
                errors.append(f"Missing anchor target: {ref}")
            if tag == "link":
                if attrs.get("rel") != "stylesheet" or target != CSS_PATH:
                    errors.append("Only the shared local stylesheet is allowed")
                stylesheet_count += 1
            if tag == "a" and attrs.get("hreflang") == ({"de": "en", "en": "de"}[language]) and target in PAGES:
                language_targets.append(target)
        except ValueError as exc:
            errors.append(str(exc))
    if stylesheet_count != 1 or mailto_count != 1:
        errors.append("Require one local stylesheet and one contact link")
    contacts = [attrs for tag, attrs in page.elements if tag == "a" and "contact" in attrs.get("class", "").split()]
    if len(contacts) != 1 or contacts[0].get("aria-label") != MAILTO.removeprefix("mailto:"):
        errors.append("Contact needs the complete accessible email address")
    if not re.search(r'<a\b[^>]*class="contact"[^>]*>\s*<span class="contact-value">schenkei@hunchagent\.io</span>\s*</a>', source):
        errors.append("Contact value needs its own shrinkable, single-line span")
    other_page = next(candidate for candidate, lang in PAGES.items() if lang != language)
    if language_targets != [other_page]:
        errors.append("Language switch does not reach the other support page")

    text = " ".join(page.text).lower()
    if any(term in text for term in ("hearth", "electron", "windows")):
        errors.append("Wrong product or paused platform claim")
    expected = {"de": ("keine passwörter", "gesundheitsdaten", "testflight", "app-store-version"), "en": ("do not send passwords", "health data", "testflight", "public app store version")}[language]
    if not all(term in text for term in expected):
        errors.append("Missing privacy guidance or beta/public version distinction")
    return errors


def validate_css() -> list[str]:
    css = CSS_PATH.read_text(encoding="utf-8")
    errors: list[str] = []
    if len(css.encode("utf-8")) > 8_000:
        errors.append("Shared CSS payload exceeds 8 KB")
    if re.search(r"@import|@font-face|url\s*\(|https?://", css, re.I):
        errors.append("External resource or embedded media in CSS")
    if css.count("{") != css.count("}"):
        errors.append("Unbalanced CSS braces")
    required = ("min-width: 44px", "min-height: 44px", "a:focus-visible", "prefers-reduced-motion: reduce", "max-width: 600px", "safe-area-inset-left", "safe-area-inset-bottom")
    for token in required:
        if token not in css:
            errors.append(f"Missing source invariant: {token}")
    for colour in ("#0d0d0b", "#39372f", "#f7f4eb", "#fffefa", "#5e584d", "#ddd5c2"):
        if colour not in css:
            errors.append(f"Missing Hunch palette token: {colour}")
    declarations = re.search(r"\.contact-value\s*\{([^}]*)\}", css)
    if not declarations or not all(token in declarations.group(1) for token in ("min-width: 0", "overflow: hidden", "text-overflow: ellipsis", "white-space: nowrap", "flex: 0 1 auto")):
        errors.append("Contact value must shrink and truncate without capping text size")
    if declarations and re.search(r"font-size|max-height|line-clamp", declarations.group(1)):
        errors.append("Contact value must not impose text-size or height caps")
    return errors


def main() -> int:
    errors: list[str] = []
    for page, language in PAGES.items():
        errors.extend(f"{page.relative_to(ROOT)}: {error}" for error in validate_page(page, language))
    errors.extend(f"assets/support.css: {error}" for error in validate_css())
    files = [*PAGES, CSS_PATH]
    print(json.dumps({
        "status": "source_checks_passed" if not errors else "failed",
        "errors": errors,
        "payload_bytes": {str(path.relative_to(ROOT)): path.stat().st_size for path in files},
        "limits": ["No browser layout, assistive-technology or mail-client test", "No live HTTP compression/cache headers checked", "No deployment or App Store change performed"],
    }, indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
