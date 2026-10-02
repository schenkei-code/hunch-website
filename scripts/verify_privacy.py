#!/usr/bin/env python3
"""Read-only, bounded static checks for the two public Hunch privacy pages.

This is not a legal audit, browser/device test, deployment check or proof of
server cache/compression headers. It never follows network links or executes HTML.
"""

from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import stat
from urllib.parse import unquote, urlsplit


MAX_HTML_BYTES = 24 * 1024
MAX_CSS_BYTES = 16 * 1024
MAX_AGGREGATE_BYTES = 56 * 1024
MAX_ELEMENTS = 512
MAX_LINKS = 24
MAX_INLINE_STYLE_BYTES = 256
TOPICS = (
    "controller", "local", "ai", "computer", "voice", "keyboard",
    "health-calendar", "retention-rights", "website",
)
MAIL = "mailto:schenkei@hunchagent.io"
RIGHTS_URL = "https://commission.europa.eu/law/law-topic/data-protection/information-individuals_en"
PAGES = {
    "de": ("privacy/index.html", "../assets/support.css", "../en/privacy/", "inhalt", "Datenschutz"),
    "en": ("en/privacy/index.html", "../../assets/support.css", "../../privacy/", "content", "Privacy"),
}
FORBIDDEN = (
    r"\btindle\b", r"\bhearth\b", r"\bworld\s*id\b",
    r"(?:erfasst|sammelt|speichert)\s+(?:gar\s+)?keine\s+(?:personenbezogenen\s+)?daten",
    r"(?:collects?|stores?|processes?)\s+no\s+(?:personal\s+)?data",
    r"(?:hundert|100)\s*(?:prozent|%)\s*(?:sicher|secure|safe)",
    r"(?:perfect|absolute|complete)\s+(?:security|privacy)",
    r"(?:vollständige|absolute|perfekte)\s+sicherheit",
    r"(?:gdpr|dsgvo)[-\s]*(?:certified|zertifiziert|konform|compliant)",
    r"(?:alle|all)\s+(?:deine\s+|your\s+)?daten\s+bleiben\s+(?:immer\s+)?lokal",
    r"all\s+(?:your\s+)?data\s+(?:always\s+)?stays?\s+local",
    r"(?:always\s+listens|hört\s+immer\s+zu|24/7|rund\s+um\s+die\s+uhr)",
)
REQUIRED = {
    "de": {
        "controller": ("Verantwortlich für Hunch und diese Website: Dominik Schenkel",),
        "local": ("Identitätsprofil", "Kennungen", "Chatverläufe", "Keychain", "Backups"),
        "ai": ("OpenAI", "Anthropic", "Google", "Kontext", "Empfänger", "außerhalb der EU", "Apple On-Device"),
        "computer": ("Gedächtnis-Abgleich", "kein getrenntes privates Profil", "Betreiber"),
        "voice": ("Mikrofon-Audio", "Transkripte", "Cloud-Dienst", "Telefonate", "Bilder", "Bildschirmkontext", "gesondert und bewusst", "gibt diesen Bildweg nicht automatisch frei", "hängt von Version"),
        "keyboard": ("Normales Tippen löst nicht automatisch", "Vollen Zugriff erlauben", "ganze Text", "bewusst"),
        "health-calendar": ("freiwillig", "getrennt", "sieben Tage", "keine gesicherte medizinische Diagnose", "Falls auf deinem verbundenen Computer bereits", "Ultrahuman", "Ringdaten", "Abrufzeitraum", "Konto-E-Mail", "Partner-API", "aus der Keychain geholt"),
        "retention-rights": ("Identität & Memory", "es löscht keine", "Einwilligungen", "Datenschutzaufsichtsbehörde"),
        "website": ("IP-Adresse", "Anfragedaten", "keine Analytics", "öffentliche"),
    },
    "en": {
        "controller": ("Responsible for Hunch and this website: Dominik Schenkel",),
        "local": ("identity profile", "identifiers", "chat history", "Keychain", "backups"),
        "ai": ("OpenAI", "Anthropic", "Google", "context", "recipient", "outside the EU", "Apple On-Device"),
        "computer": ("memory sync", "does not create a separate private profile", "operator"),
        "voice": ("microphone audio", "Transcripts", "cloud service", "phone calls", "images", "screen context", "separately and deliberately", "does not automatically permit this image route", "depends on the version"),
        "keyboard": ("Ordinary typing does not automatically", "Allow Full Access", "entire text", "deliberately"),
        "health-calendar": ("optional", "separate", "seven days", "not an established medical diagnosis", "If an Ultrahuman integration is already configured on your connected computer", "Ultrahuman", "ring data", "time range", "account email", "partner API", "retrieved from the computer’s Keychain"),
        "retention-rights": ("Identität & Memory", "does not delete copies", "withdraw consent", "data protection authority"),
        "website": ("IP address", "request data", "no analytics", "public HTML"),
    },
}


class InvalidPrivacy(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidPrivacy(message)


def read_public(root: Path, relative: str, maximum: int) -> tuple[str, bytes]:
    path = root / relative
    require(not path.is_symlink(), f"Symlink is not an accepted public input: {relative}")
    require(path.resolve().is_relative_to(root), f"Input escapes website: {relative}")
    info = path.stat()
    require(stat.S_ISREG(info.st_mode), f"Input is not a regular file: {relative}")
    require(0 < info.st_size <= maximum, f"Payload outside bounds: {relative}")
    with path.open("rb") as source:
        payload = source.read(maximum + 1)
    require(len(payload) == info.st_size and len(payload) <= maximum, f"Input changed or exceeds bounds: {relative}")
    return payload.decode("utf-8", errors="strict"), payload


class PublicPage(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.ids: set[str] = set()
        self.sections: list[str] = []
        self.section_labels: list[str] = []
        self.heading_ids: set[str] = set()
        self.section_text: dict[str, list[str]] = {}
        self.active_topic: str | None = None
        self.links: list[dict[str, str]] = []
        self.stylesheets: list[str] = []
        self.text: list[str] = []
        self.h1: list[str] = []
        self.in_h1 = False
        self.inline_styles: list[str] = []
        self.in_style = False
        self.main: dict[str, str] = {}
        self.viewport = ""
        self.elements = 0

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        self.elements += 1
        require(self.elements <= MAX_ELEMENTS, "Too many HTML elements")
        keys = [key for key, _ in attributes]
        require(len(keys) == len(set(keys)), f"Duplicate attributes on {tag}")
        attrs = {key: value or "" for key, value in attributes}
        require(tag not in {"script", "iframe", "object", "embed", "form", "input", "button", "video", "audio", "img", "svg", "base"}, f"Unexpected active/resource element: {tag}")
        require(not any(key.startswith("on") for key in attrs), "Inline event handler is forbidden")
        require(not any(key in attrs for key in ("src", "srcset", "ping", "nonce", "style")), "Unexpected resource/inline attribute")
        if "id" in attrs:
            require(attrs["id"] not in self.ids, f"Duplicate id: {attrs['id']}")
            self.ids.add(attrs["id"])
        if tag == "html":
            require(not self.lang, "Multiple html roots")
            self.lang = attrs.get("lang", "")
        elif tag == "meta":
            require("http-equiv" not in attrs, "HTTP-equivalent redirect or directive forbidden")
            if attrs.get("name") == "viewport":
                self.viewport = attrs.get("content", "")
        elif tag == "link":
            require(attrs.get("rel") == "stylesheet", "Only the local support stylesheet may be linked")
            self.stylesheets.append(attrs.get("href", ""))
        elif tag == "a":
            require("href" in attrs, "Link has no href")
            self.links.append(attrs)
            require(len(self.links) <= MAX_LINKS, "Too many links")
        elif tag == "main":
            require(not self.main, "Multiple main elements")
            self.main = attrs
        elif tag == "section":
            topic = attrs.get("data-topic", "")
            require(topic in TOPICS and topic not in self.sections, "Unknown or repeated privacy section")
            require(self.active_topic is None, "Nested content sections forbidden")
            self.sections.append(topic)
            self.section_labels.append(attrs.get("aria-labelledby", ""))
            self.section_text[topic] = []
            self.active_topic = topic
            require(bool(attrs.get("aria-labelledby")), "Section needs a named heading")
        elif tag == "h1":
            self.h1.append("")
            self.in_h1 = True
        elif tag == "h2":
            require(bool(attrs.get("id")), "Privacy heading needs an id")
            self.heading_ids.add(attrs["id"])
        elif tag == "style":
            self.in_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "section":
            self.active_topic = None
        elif tag == "h1":
            self.in_h1 = False
        elif tag == "style":
            self.in_style = False

    def handle_data(self, value: str) -> None:
        if self.in_style:
            self.inline_styles.append(value)
            return
        self.text.append(value)
        if self.active_topic:
            self.section_text[self.active_topic].append(value)
        if self.in_h1:
            self.h1[-1] += value


def local_target(root: Path, page: Path, href: str) -> Path:
    parts = urlsplit(href)
    require(not parts.scheme and not parts.netloc and not parts.query, "Local link contains network origin or query")
    decoded = unquote(parts.path)
    require("\\" not in decoded and "\x00" not in decoded and not decoded.startswith("/"), "Unsafe relative link")
    target = (page.parent / decoded).resolve()
    require(target.is_relative_to(root), "Local link leaves website")
    if target.is_dir():
        target = target / "index.html"
    require(target.is_file() and not target.is_symlink(), f"Missing local link target: {href}")
    return target


def verify(root: Path) -> dict[str, object]:
    root = root.resolve(strict=True)
    results = {}
    total = 0
    stylesheet, css_bytes = read_public(root, "assets/support.css", MAX_CSS_BYTES)
    total += len(css_bytes)
    require("min-width: 44px" in stylesheet and "min-height: 44px" in stylesheet, "Support stylesheet lacks minimum touch bounds")
    require("prefers-reduced-motion: reduce" in stylesheet, "Reduced Motion support missing")
    require(not re.search(r"@import|url\s*\(|@font-face", stylesheet, flags=re.I), "External CSS dependency forbidden")
    for locale, (relative, css, alternate, main_id, heading) in PAGES.items():
        source, payload = read_public(root, relative, MAX_HTML_BYTES)
        total += len(payload)
        require(total <= MAX_AGGREGATE_BYTES, "Combined privacy payload exceeds bound")
        require("<!doctype html>" in source.casefold(), "HTML doctype missing")
        require(not re.search(r"\{\{|\{%|<\?php|document\.cookie|localStorage|sessionStorage|fetch\s*\(", source, flags=re.I), "Dynamic or private-client state marker forbidden")
        page = PublicPage()
        page.feed(source)
        page.close()
        require(page.lang == locale, f"Wrong language on {relative}")
        require(page.h1 == [heading], f"Wrong or multiple title on {relative}")
        require(page.stylesheets == [css], f"Wrong stylesheet on {relative}")
        require(page.sections == list(TOPICS), f"Missing, reordered or unequal data-route sections on {relative}")
        require(set(page.section_labels) == page.heading_ids, "Section labels must name their actual headings")
        require(page.main.get("id") == main_id and page.main.get("tabindex") == "-1", "Missing keyboard-accessible main target")
        require("width=device-width" in page.viewport and "initial-scale=1" in page.viewport, "Viewport definition missing")
        require(not re.search(r"maximum-scale|user-scalable\s*=\s*(?:no|0)", page.viewport, flags=re.I), "Text/browser zoom is capped")
        inline_style = "".join(page.inline_styles)
        require(len(inline_style.encode()) <= MAX_INLINE_STYLE_BYTES, "Unexpected inline style payload")
        require(inline_style.strip() == "h1 { font-size: 1.5rem; } p { overflow-wrap: anywhere; }", "Inline stylesheet must only keep long privacy title/text readable")
        text = " ".join(" ".join(page.text).split())
        for expression in FORBIDDEN:
            require(not re.search(expression, text, flags=re.I), f"Foreign brand or unsupported blanket claim: {expression}")
        for topic, needles in REQUIRED[locale].items():
            section = " ".join(" ".join(page.section_text[topic]).split())
            for needle in needles:
                require(needle.casefold() in section.casefold(), f"Required disclosure absent: {locale}/{topic}/{needle}")
        hrefs = [link["href"] for link in page.links]
        require(MAIL in hrefs and RIGHTS_URL in hrefs and alternate in hrefs, "Contact, rights or alternate-language route absent")
        alternate_link = next(link for link in page.links if link["href"] == alternate)
        other_locale = "en" if locale == "de" else "de"
        require(alternate_link.get("lang") == other_locale and alternate_link.get("hreflang") == other_locale, "Language switch is incorrectly identified")
        for link in page.links:
            href = link["href"]
            if href.startswith("#"):
                require(href[1:] in page.ids, "Missing in-page anchor target")
            elif href in {MAIL, RIGHTS_URL}:
                continue
            else:
                local_target(root, root / relative, href)
        local_target(root, root / relative, css)
        results[locale] = {"route": "/" + relative.removesuffix("index.html"), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "topics": len(page.sections), "links": len(page.links)}
    return {
        "status": "STATIC_CHECKS_PASS",
        "pages": results,
        "stylesheet": {"bytes": len(css_bytes), "sha256": hashlib.sha256(css_bytes).hexdigest()},
        "aggregate_bytes": total,
        "limits": {"html_bytes": MAX_HTML_BYTES, "aggregate_bytes": MAX_AGGREGATE_BYTES, "links_per_page": MAX_LINKS, "elements_per_page": MAX_ELEMENTS},
        "not_proven": ["legal_compliance", "installed_app_behavior", "browser_rendering", "physical_device", "publication", "http_cache_or_compression_headers"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--website-root", type=Path, default=Path(__file__).resolve().parents[1])
    arguments = parser.parse_args()
    try:
        result = verify(arguments.website_root)
    except (InvalidPrivacy, OSError, UnicodeError, ValueError) as failure:
        print(json.dumps({"status": "STATIC_CHECKS_FAIL", "error": str(failure)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
