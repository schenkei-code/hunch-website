#!/usr/bin/env python3
"""Static release checks for the dependency-free Hunch website."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [ROOT / "index.html", ROOT / "en" / "index.html", *sorted((ROOT / "docs").glob("*.html"))]
SKIP_SCHEMES = {"data", "http", "https", "mailto", "tel"}
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}
ALLOWED_RADIUS_VALUES = {"0", "9px", "12px", "16px", "18px", "24px", "28px", "50%", "inherit"}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.id_text: dict[str, list[str]] = {}
        self.local_refs: list[tuple[str, str]] = []
        self.menu_controls: list[dict[str, str]] = []
        self.mobile_menus: list[dict[str, str | bool | int]] = []
        self.landmarks: list[dict[str, str | int]] = []
        self.mains: list[int] = []
        self.current_pages: list[int] = []
        self.aria_idrefs: list[tuple[int, str, list[str]]] = []
        self.scripts: list[str] = []
        self.images: list[dict[str, str | int | bool]] = []
        self.videos: list[dict[str, str | int | bool]] = []
        self.stack: list[tuple[str, str, int]] = []
        self.structure_errors: list[str] = []

    def _record_element(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        line = self.getpos()[0]
        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
            self.id_text.setdefault(element_id, [])

        for name in ("aria-controls", "aria-describedby", "aria-labelledby"):
            raw_idrefs = values.get(name, "")
            if raw_idrefs:
                self.aria_idrefs.append((line, name, idrefs(raw_idrefs)))

        for name in ("href", "src", "poster"):
            value = values.get(name)
            if value:
                self.local_refs.append((name, value))

        if "data-mobile-menu-toggle" in values:
            self.menu_controls.append({"tag": tag, "line": str(line), **values})
        if element_id == "mobile-menu":
            self.mobile_menus.append({
                "line": line,
                "role": values.get("role", ""),
                "label": values.get("aria-label", ""),
                "hidden": "hidden" in values,
                "inside_nav": any(open_tag == "nav" for open_tag, _, _ in self.stack),
            })
        if tag == "nav" or values.get("role") == "navigation":
            self.landmarks.append({
                "line": line,
                "label": values.get("aria-label", "") or values.get("aria-labelledby", ""),
            })
        if tag == "main":
            self.mains.append(line)
        if values.get("aria-current") == "page":
            self.current_pages.append(line)
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"])
        if tag == "img":
            self.images.append({
                "line": line,
                "has_alt": any(name == "alt" for name, _ in attrs),
                "src": values.get("src", ""),
            })
        if tag == "video":
            self.videos.append({
                "line": line,
                "controls": "controls" in values,
                "autoplay": "autoplay" in values,
                "loop": "loop" in values,
                "label": values.get("aria-label", ""),
                "labelledby": values.get("aria-labelledby", ""),
                "describedby": values.get("aria-describedby", ""),
            })

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record_element(tag, attrs)
        if tag not in VOID_ELEMENTS:
            values = {key: value or "" for key, value in attrs}
            self.stack.append((tag, values.get("id", ""), self.getpos()[0]))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record_element(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_ELEMENTS:
            self.structure_errors.append(f"Zeile {self.getpos()[0]}: unerwartetes </{tag}>")
            return
        if not self.stack:
            self.structure_errors.append(f"Zeile {self.getpos()[0]}: schließendes </{tag}> ohne Starttag")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        matching = next((index for index in range(len(self.stack) - 1, -1, -1) if self.stack[index][0] == tag), None)
        if matching is None:
            self.structure_errors.append(f"Zeile {self.getpos()[0]}: schließendes </{tag}> ohne Starttag")
            return
        crossed = ", ".join(f"<{name}> aus Zeile {line}" for name, _, line in self.stack[matching + 1:])
        self.structure_errors.append(f"Zeile {self.getpos()[0]}: </{tag}> kreuzt {crossed}")
        del self.stack[matching:]

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        for _, element_id, _ in self.stack:
            if element_id:
                self.id_text.setdefault(element_id, []).append(data.strip())

    def finish(self) -> None:
        self.close()
        if self.stack:
            unclosed = ", ".join(f"<{tag}> aus Zeile {line}" for tag, _, line in self.stack)
            self.structure_errors.append(f"nicht geschlossen: {unclosed}")


def local_target(page: Path, raw: str) -> Path | None:
    split = urlsplit(raw)
    if split.scheme in SKIP_SCHEMES or split.netloc:
        return None
    path = unquote(split.path)
    if not path:
        target = page
    else:
        target = (ROOT / path.lstrip("/")) if path.startswith("/") else (page.parent / path)
    target = target.resolve()
    if ROOT not in target.parents and target != ROOT:
        return None
    if target.is_dir():
        target /= "index.html"
    return target


def idrefs(raw: str) -> list[str]:
    """Split an ARIA IDREF(S) attribute into referenced element IDs."""
    return [part for part in raw.split() if part]


def compact_css(css: str) -> str:
    return re.sub(r"\s+", "", css)


def css_rule(css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", css)
    return compact_css(match.group(1)) if match else ""


def require_css(css: str, source: str, selector: str, declarations: tuple[str, ...], errors: list[str]) -> None:
    body = css_rule(css, selector)
    if not body:
        errors.append(f"{source}: CSS-Regel fehlt: {selector}")
        return
    for declaration in declarations:
        if compact_css(declaration) not in body:
            errors.append(f"{source}: {selector} braucht {declaration}")


def check_radii(css: str, source: str, errors: list[str]) -> None:
    for match in re.finditer(r"border-radius\s*:\s*([^;}\n]+)", css):
        value = match.group(1).strip()
        if value.startswith("var("):
            continue
        tokens = value.replace("/", " ").split()
        invalid = [token for token in tokens if token not in ALLOWED_RADIUS_VALUES]
        if invalid:
            errors.append(f"{source}: Radius außerhalb der Brand-Registry: {value}")


def main() -> int:
    errors: list[str] = []
    pages: dict[Path, Page] = {}
    texts: dict[Path, str] = {}

    for path in HTML_FILES:
        parser = Page()
        text = path.read_text(encoding="utf-8")
        parser.feed(text)
        parser.finish()
        resolved = path.resolve()
        pages[resolved] = parser
        texts[resolved] = text
        rel = path.relative_to(ROOT)

        for error in parser.structure_errors:
            errors.append(f"{rel}: HTML-Struktur: {error}")
        if parser.duplicate_ids:
            errors.append(f"{rel}: doppelte IDs {sorted(parser.duplicate_ids)}")
        for line, attribute, targets in parser.aria_idrefs:
            missing = [target for target in targets if target not in parser.ids]
            if missing:
                errors.append(f"{rel}:{line}: {attribute} verweist auf fehlende IDs {missing}")
        if len(parser.menu_controls) != 1:
            errors.append(f"{rel}: genau ein mobiler Menüknopf erwartet")
        else:
            control = parser.menu_controls[0]
            target = control.get("aria-controls", "")
            if not target or target not in parser.ids:
                errors.append(f"{rel}: aria-controls verweist nicht auf ein vorhandenes Menü")
            if control.get("tag") != "button" or control.get("type") != "button":
                errors.append(f"{rel}: mobiler Menüknopf muss button[type=button] sein")
            if control.get("aria-expanded") != "false":
                errors.append(f"{rel}: mobiler Menüknopf muss geschlossen mit aria-expanded=false starten")
        if len(parser.mobile_menus) != 1:
            errors.append(f"{rel}: genau ein mobiles Menü erwartet")
        else:
            menu = parser.mobile_menus[0]
            if menu["inside_nav"]:
                errors.append(f"{rel}: mobiles Fixed-Menü darf nicht im gefilterten Header-nav liegen")
            if menu["role"] != "navigation" or not menu["label"]:
                errors.append(f"{rel}: mobiles Menü braucht einen benannten Navigation-Landmark")
            if not menu["hidden"]:
                errors.append(f"{rel}: mobiles Menü muss initial hidden sein")

        landmark_labels: list[str] = []
        for landmark in parser.landmarks:
            label = str(landmark["label"]).strip()
            if not label:
                errors.append(f"{rel}: Navigation-Landmark in Zeile {landmark['line']} ist nicht benannt")
            else:
                landmark_labels.append(label.casefold())
        if len(landmark_labels) != len(set(landmark_labels)):
            errors.append(f"{rel}: Navigation-Landmarks brauchen eindeutige Namen")
        if len(parser.mains) != 1:
            errors.append(f"{rel}: genau ein main-Landmark erwartet")
        if rel.parts and rel.parts[0] == "docs" and len(parser.current_pages) != 1:
            errors.append(f"{rel}: genau ein Doku-Link mit aria-current=page erwartet")

        if not any(src.endswith("site-nav.js") for src in parser.scripts):
            errors.append(f"{rel}: site-nav.js fehlt")
        for image in parser.images:
            if not image["has_alt"]:
                errors.append(f"{rel}:{image['line']}: Bild ohne alt-Attribut: {image['src']}")
        if rel.as_posix() in {"index.html", "en/index.html"} and len(parser.videos) != 1:
            errors.append(f"{rel}: genau ein benanntes Produktvideo erwartet")
        for video in parser.videos:
            line = video["line"]
            forbidden = [name for name in ("autoplay", "loop") if video[name]]
            if forbidden:
                errors.append(f"{rel}:{line}: Video enthält {', '.join(forbidden)}")
            if not video["controls"]:
                errors.append(f"{rel}:{line}: Video braucht controls")
            labelledby = idrefs(str(video["labelledby"]))
            has_labelled_name = bool(labelledby) and all(
                target in parser.ids and bool(" ".join(parser.id_text.get(target, [])).strip())
                for target in labelledby
            )
            if not str(video["label"]).strip() and not has_labelled_name:
                errors.append(f"{rel}:{line}: Video braucht aria-label oder ein benanntes aria-labelledby-Ziel")
            describedby = idrefs(str(video["describedby"]))
            if not describedby or not all(
                target in parser.ids and bool(" ".join(parser.id_text.get(target, [])).strip())
                for target in describedby
            ):
                errors.append(f"{rel}:{line}: Video braucht eine nichtleere Textalternative über aria-describedby")

    for path, parser in pages.items():
        rel = path.relative_to(ROOT)
        for attribute, raw in parser.local_refs:
            target = local_target(path, raw)
            if target is None:
                continue
            if not target.exists():
                errors.append(f"{rel}: lokales Ziel fehlt: {raw}")
                continue
            fragment = urlsplit(raw).fragment
            target_page = pages.get(target.resolve())
            if attribute == "href" and fragment and target_page is not None:
                fragment_id = unquote(fragment)
                if fragment_id not in target_page.ids:
                    errors.append(f"{rel}: Fragmentziel fehlt: {raw}")

    landing = texts[(ROOT / "index.html").resolve()]
    landing_en = texts[(ROOT / "en" / "index.html").resolve()]
    docs_session = texts[(ROOT / "docs" / "session.html").resolve()]
    docs_status = texts[(ROOT / "docs" / "status.html").resolve()]
    docs_tools = texts[(ROOT / "docs" / "werkzeuge.html").resolve()]
    docs_security = texts[(ROOT / "docs" / "sicherheit.html").resolve()]
    joined = landing + landing_en
    public_copy = "\n".join(texts.values())
    truth = (ROOT / "PRODUCT_TRUTH.md").read_text(encoding="utf-8")
    truth_flat = re.sub(r"\s+", " ", truth)
    truth_contract = "### Globale Konversation + Presence — HEUTE"
    if truth_contract not in truth:
        errors.append(f"PRODUCT_TRUTH.md: erwarteter Wahrheitsvertrag fehlt: {truth_contract}")
    truth_today_contract = (
        "**HEUTE** — im aktuellen Code vorhanden und getestet; runtime-abhängige Aussagen zusätzlich "
        "gegen die laufende Runtime nachgewiesen"
    )
    if truth_today_contract not in truth_flat:
        errors.append("PRODUCT_TRUTH.md: HEUTE braucht bei Runtime-Claims einen Live-Nachweis")
    forbidden_claims = (
        "HID · 6699",
        "Live-Konversation überall",
        "Live conversation everywhere",
        "globale Live-Session",
        "global live session",
        "globale Live-Konversation",
        "global live conversation",
        "globale Session",
        "global session",
        "haupt-Session",
        "offene Verbindungen erhalten neue Zeilen live",
    )
    for stale in forbidden_claims:
        if stale.casefold() in public_copy.casefold():
            errors.append(f"Website enthält unbelegten/veralteten Claim: {stale}")
    for pattern, label in (
        (r"\bglobal(?:e|er|en)?\s+(?:live[\s-]*)?(?:session|konversation)\b", "deutscher Global-Live-Claim"),
        (r"\bglobal\s+(?:live[\s-]*)?(?:session|conversation)\b", "englischer Global-Live-Claim"),
    ):
        if re.search(pattern, public_copy, flags=re.I):
            errors.append(f"Website enthält unbelegten/veralteten Claim: {label}")
    required_claims = (
        (landing, "Verlauf + Presence", "deutscher Verlauf-/Presence-Claim"),
        (landing, "App, Runtime, CLI, Web und Telegram", "deutscher belegter Surface-Scope"),
        (landing, "letzten 30 Zeilen", "deutsche Fortsetzungsgrenze"),
        (landing_en, "History + presence", "englischer Verlauf-/Presence-Claim"),
        (landing_en, "app, runtime, CLI, web and Telegram", "englischer belegter Surface-Scope"),
        (landing_en, "last 30 lines", "englische Fortsetzungsgrenze"),
        (
            landing,
            "Im aktuellen Code vorhanden und getestet; runtime-abhängige Aussagen sind zusätzlich "
            "gegen die laufende Runtime nachgewiesen.",
            "deutscher HEUTE-Nachweisvertrag",
        ),
        (
            landing_en,
            "Present and tested in current code; runtime-dependent claims are additionally proven "
            "against the running runtime.",
            "englischer HEUTE-Nachweisvertrag",
        ),
        (landing, "Kritische Hunch-Werkzeuge werden nie automatisch freigegeben.", "deutsche Hunch-Grenze"),
        (landing, "Codex ist getrennt: Standard ist nur lesen", "deutsche Codex-Grenze"),
        (landing_en, "Critical Hunch tools are never approved automatically.", "englische Hunch-Grenze"),
        (landing_en, "Codex is separate: read-only is the default", "englische Codex-Grenze"),
        (docs_session, "Konsole, Telegram-Chat und Web-Chat", "Doku-Verlauf-Scope"),
        (docs_session, "letzten 30 Zeilen", "Doku-Fortsetzungsgrenze"),
        (docs_session, "App, Runtime, CLI, Web und Telegram", "Doku-belegter Surface-Scope"),
        (docs_session, "Stand 2026-09-03, gegen PRODUCT_TRUTH geprüft", "Doku-Session-Prüfstand"),
        (docs_status, "Stand 2026-09-03, gegen PRODUCT_TRUTH geprüft", "Doku-Status-Prüfstand"),
        (
            docs_status,
            "Fenstertitel nur mit Bedienungshilfen-Recht",
            "Sensor-Bedienungshilfen-Grenze im HEUTE-Stand",
        ),
        (
            docs_status,
            "Bildschirm-OCR nur mit Bildschirmaufnahme-Recht",
            "Sensor-Bildschirmaufnahme-Grenze im HEUTE-Stand",
        ),
        (
            docs_tools,
            '<h2>Kompatibilität — aktuelle Grenze <span class="tag heute">Heute</span></h2>',
            "HEUTE-Status der aktuellen Kompatibilitätsgrenze",
        ),
        (docs_security, "Kritische Hunch-Werkzeuge werden nie automatisch", "Doku-Hunch-Grenze"),
        (docs_security, "Codex ist getrennt: Standard ist nur lesen", "Doku-Codex-Grenze"),
    )
    for source, claim, label in required_claims:
        if claim not in source:
            errors.append(f"Website: {label} fehlt: {claim}")

    for source, language in ((landing, "de"), (landing_en, "en")):
        section = re.search(
            r'<section\b(?=[^>]*\bid=["\']session["\'])[^>]*>.*?</section>',
            source,
            flags=re.I | re.S,
        )
        if not section:
            errors.append(f"Landingpage {language}: Verlauf-/Presence-Abschnitt fehlt")
            continue
        for unsupported_surface in ("WhatsApp", "Voice", "MCP / HTTP"):
            if unsupported_surface.casefold() in section.group(0).casefold():
                errors.append(
                    f"Landingpage {language}: unbelegte Surface im Verlauf-/Presence-Abschnitt: "
                    f"{unsupported_surface}"
                )

    hub_groups = ["jetzt", "verstehen", "verbinden", "werkzeuge"]
    hub_routes = [
        "freigaben", "faeden", "sitzung", "brain", "bildschirm", "maschinen",
        "kanaele", "nodes", "skills", "apps", "github",
    ]
    hub_contracts = (
        (
            landing,
            "de",
            ["Jetzt", "Verstehen", "Verbinden", "Werkzeuge"],
            [
                "Freigaben", "Fäden", "Intention", "Brain", "Bildschirm", "Maschinen",
                "Kanäle", "Nodes", "Skills &amp; MCPs", "Apps", "GitHub",
            ],
            "Vier ruhige Gruppen, dieselben 11 Wege",
        ),
        (
            landing_en,
            "en",
            ["Now", "Understand", "Connect", "Tools"],
            [
                "Approvals", "Threads", "Intention", "Brain", "Screen", "Machines",
                "Channels", "Nodes", "Skills &amp; MCPs", "Apps", "GitHub",
            ],
            "Four quiet groups, the same 11 routes",
        ),
    )
    for source, language, expected_group_labels, expected_route_labels, caption in hub_contracts:
        actual_groups = re.findall(r'data-hub-group="([^"]+)"', source)
        actual_routes = re.findall(r'data-hub-route="([^"]+)"', source)
        actual_group_labels = re.findall(
            r'data-hub-group="[^"]+"[^>]*>\s*<h3 class="hub-group-title">([^<]+)</h3>',
            source,
        )
        actual_route_labels = re.findall(
            r'data-hub-route="[^"]+"[^>]*>\s*<div>\s*<strong>([^<]+)</strong>',
            source,
        )
        if actual_groups != hub_groups:
            errors.append(f"Landingpage {language}: Hub-Gruppen oder Reihenfolge falsch: {actual_groups}")
        if actual_routes != hub_routes:
            errors.append(f"Landingpage {language}: Hub braucht dieselben 11 Routen: {actual_routes}")
        if actual_group_labels != expected_group_labels:
            errors.append(f"Landingpage {language}: sichtbare Hub-Gruppen falsch: {actual_group_labels}")
        if actual_route_labels != expected_route_labels:
            errors.append(f"Landingpage {language}: sichtbare Hub-Routen falsch: {actual_route_labels}")
        if caption not in source:
            errors.append(f"Landingpage {language}: Hub-Caption nennt die vier Gruppen nicht")

    experimental_blocks = (
        (
            re.search(
                r'<div class="col reveal"><h3><span class="tag exp">Experimentell</span>.*?</div>',
                landing,
                flags=re.S,
            ),
            ("Fenstertitel", "Bedienungshilfen-Recht", "Screen-OCR", "Bildschirmaufnahme-Recht"),
            "deutsche Statusmatrix",
        ),
        (
            re.search(
                r'<div class="col reveal"><h3><span class="tag exp">Experimental</span>.*?</div>',
                landing_en,
                flags=re.S,
            ),
            ("Window titles", "accessibility permission", "screen OCR", "screen-recording permission"),
            "englische Statusmatrix",
        ),
        (
            re.search(
                r'<h2><span class="tag exp">Experimentell</span>.*?(?=<h2>)',
                docs_status,
                flags=re.S,
            ),
            ("Fenstertitel", "Bedienungshilfen-Recht", "Bildschirm-OCR", "Bildschirmaufnahme-Recht"),
            "Status-Doku",
        ),
    )
    for match, stale_sensor_terms, label in experimental_blocks:
        if match is None:
            errors.append(f"{label}: Experimentell-Abschnitt fehlt")
            continue
        block = match.group(0).casefold()
        for stale in stale_sensor_terms:
            if stale.casefold() in block:
                errors.append(f"{label}: Sensor-Berechtigung ist eine HEUTE-Grenze, kein Experiment: {stale}")

    for source, label in ((docs_session, "Session-Doku"), (docs_status, "Status-Doku")):
        if "Stand 2026-09-01" in source:
            errors.append(f"{label}: veralteter Prüfstand 2026-09-01")

    if " infinite" in joined or "autoplay" in joined:
        errors.append("Landingpage enthält verbotene Dauerbewegung")
    for stale_ui in (
        'class="steps"',
        'class="pill"',
        'class="chain reveal"',
        '.island .pill',
        '.concept-badge',
        'content:"✓"',
        'content:"◌',
        'content:"▼"',
        'content:"›"',
        '>→<',
        '>›<',
    ):
        if stale_ui in joined:
            errors.append(f"Landingpage enthält veraltetes Slop-/Glyph-Muster: {stale_ui}")

    dead_patterns = (".session-map li.target{", ".flow,", ".chain,")
    compact_joined = compact_css(joined)
    for dead in dead_patterns:
        if compact_css(dead) in compact_joined:
            errors.append(f"Landingpage enthält toten Selektor: {dead}")

    landing_css_sources = {
        "index.html": "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", landing, flags=re.I | re.S)),
        "en/index.html": "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", landing_en, flags=re.I | re.S)),
    }
    for source, css in landing_css_sources.items():
        if css.count("{") != css.count("}") or css.count("(") != css.count(")"):
            errors.append(f"{source}: CSS-Klammern sind nicht ausgeglichen")
        check_radii(css, source, errors)
        for contract in (
            "--card:var(--ivory-50)",
            "--on-gold:#4a3410",
            "--btn-ink:var(--on-gold)",
        ):
            if compact_css(contract) not in compact_css(css):
                errors.append(f"{source}: Brand-Farbvertrag fehlt: {contract}")
        for selector in (".nav-cta", ".btn-primary", ".mobile-menu .mobile-menu-cta", ".gate-btn.primary"):
            require_css(css, source, selector, ("color:var(--on-gold)",), errors)
        require_css(css, source, ".menu-toggle", ("min-width:58px", "min-height:44px"), errors)
        require_css(css, source, ".mobile-menu", ("position:fixed", "overscroll-behavior:contain"), errors)
        require_css(css, source, ".mobile-menu a", ("min-height:44px", "white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis"), errors)
        require_css(css, source, "html.mobile-menu-open,body.mobile-menu-open", ("overflow:hidden",), errors)
        require_css(css, source, ".card h3", ("flex-wrap:nowrap", "white-space:nowrap"), errors)
        require_css(css, source, ".scope h3", ("flex-wrap:nowrap", "white-space:nowrap"), errors)
        require_css(css, source, ".island .activity-row", ("min-width:0", "border-bottom:1px solid var(--security-line-dark)"), errors)
        if "backdrop-filter" in css_rule(css, ".mobile-menu"):
            errors.append(f"{source}: mobiles Overlay darf keinen eigenen Backdrop-Filter erzeugen")
        require_css(css, source, ".lane header b", ("min-width:0", "white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis"), errors)
        require_css(css, source, ".lane header span", ("min-width:0", "white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis"), errors)
        require_css(css, source, ".lane-ledger span", ("min-height:2.35rem", "min-width:0", "white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis"), errors)
        require_css(css, source, ".authority-ledger div", ("min-height:3.35rem", "min-width:0"), errors)
        require_css(css, source, ".authority-ledger strong", ("min-width:0", "white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis"), errors)
        require_css(css, source, ".authority-ledger span", ("min-width:0", "white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis"), errors)
        require_css(css, source, ".hub-group", ("display:grid",), errors)
        require_css(css, source, ".hub-group-title", ("white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis", "font:650 .56rem/1 var(--mono)"), errors)
        require_css(css, source, ".hub-row", ("min-height:4.5rem", "grid-template-columns:minmax(0,1fr) auto"), errors)
        require_css(css, source, ".hub-row > div", ("min-width:0",), errors)
        require_css(css, source, ".hub-row strong", ("min-width:0", "white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis"), errors)
        require_css(css, source, ".hub-row span", ("min-width:0", "white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis"), errors)
        compact = compact_css(css)
        for contract in (
            ".lane-ledger{grid-template-columns:repeat(2,minmax(0,1fr))}",
            ".authority-ledgerdiv{grid-template-columns:minmax(0,1fr)minmax(0,1fr)}",
        ):
            if compact_css(contract) not in compact:
                errors.append(f"{source}: mobiler 375-pt-Vertrag fehlt: {contract}")

    nav_source = (ROOT / "site-nav.js").read_text(encoding="utf-8")
    for contract in (
        "Escape",
        "aria-expanded",
        "setAttribute('inert'",
        "removeAttribute('inert'",
        "focusHashTarget",
        "history.pushState",
        "scrollIntoView",
        "document.documentElement.classList",
        "setBackgroundInert(true)",
        "setBackgroundInert(false)",
        "close(true)",
        "desktopFocusTarget",
    ):
        if contract not in nav_source:
            errors.append(f"site-nav.js: Accessibility-Vertrag fehlt: {contract}")
    if "event.target.closest('a')" in nav_source and "close(false)" in nav_source:
        errors.append("site-nav.js: pauschales Schließen darf den Fokus nicht in einem versteckten Link lassen")

    docs_css = (ROOT / "docs" / "docs.css").read_text(encoding="utf-8")
    if docs_css.count("{") != docs_css.count("}") or docs_css.count("(") != docs_css.count(")"):
        errors.append("docs/docs.css: CSS-Klammern sind nicht ausgeglichen")
    check_radii(docs_css, "docs/docs.css", errors)
    for contract in (
        "--card:var(--ivory-50)",
        "--on-gold:#4a3410",
        "--btn-ink:var(--on-gold)",
    ):
        if compact_css(contract) not in compact_css(docs_css):
            errors.append(f"docs/docs.css: Brand-Farbvertrag fehlt: {contract}")
    for selector in (".nav-cta", ".mobile-menu .mobile-menu-cta"):
        require_css(
            docs_css,
            "docs/docs.css",
            selector,
            (
                "background:linear-gradient(135deg,#efcf6f,#c79a3a)",
                "color:var(--on-gold)",
            ),
            errors,
        )
    require_css(docs_css, "docs/docs.css", ".menu-toggle", ("min-width:58px", "min-height:44px"), errors)
    require_css(docs_css, "docs/docs.css", ".mobile-menu", ("position:fixed", "overscroll-behavior:contain"), errors)
    require_css(docs_css, "docs/docs.css", ".mobile-menu a", ("min-height:44px", "white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis"), errors)
    require_css(docs_css, "docs/docs.css", "html.mobile-menu-open,body.mobile-menu-open", ("overflow:hidden",), errors)
    if "backdrop-filter" in css_rule(docs_css, ".mobile-menu"):
        errors.append("docs/docs.css: mobiles Overlay darf keinen eigenen Backdrop-Filter erzeugen")
    require_css(docs_css, "docs/docs.css", ".side-nav a", ("min-height:44px",), errors)
    for contract in ("prefers-reduced-motion", "prefers-reduced-transparency", "--r-action:9px"):
        if contract not in docs_css:
            errors.append(f"docs.css: Designvertrag fehlt: {contract}")
    for foreign_status_color in ("#2e6b47", "#9a5d08", "#9fd3b0"):
        if foreign_status_color in (joined + docs_css).casefold():
            errors.append(f"Website enthält Statusfarbe außerhalb der Brand-Palette: {foreign_status_color}")

    if errors:
        print("Website-Verifikation fehlgeschlagen:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"Website-Verifikation: {len(HTML_FILES)} HTML-Seiten; Struktur, Landmarks, Fragmente, "
        "Navigation, A11y, CSS, Motion und Produktwahrheit grün."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
