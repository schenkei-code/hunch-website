# AGENTS.md — Hunch Website (hunchagent.io)

Gilt für jeden Agenten, der hier arbeitet oder reviewt (Codex-Review-Gate,
Claude, Dominik). Quelle der Wahrheit fürs Design ist die interne Brand Bible
`~/Projekte/hunch/brand/hunch-brand-system.html` (Brand System 2026.03) —
die Regeln unten sind daraus **hart** abgeleitet. Ein Review, das eine davon
verletzt sieht, antwortet mit **BLOCK** und nennt die Regel.

## Design-Regeln (hart, für Reviews)

### Layout & Proportionen
1. **Nichts bricht um, was ein Titel, ein Name oder ein Wert ist.** Screen-Titel
   („Chat", „Hunch", „Profil", „Einstellungen") sind `fixedSize` — niemals
   „Ch/at". Werte (Modellname, Maschinenname, Token) haben `lineLimit(1)` +
   `truncationMode(.tail)`. Mehrzeilig ist nur Fließtext.
2. **Gleiche Proportionen für gleiche Dinge.** Eine Kapsel/Zeile/Kachel, die
   je nach Inhalt (Modell, Anbieter, Maschine) anders breit oder hoch wird,
   ist ein Fehler. Feste Wunschbreite + Truncation, nicht Inhalt bestimmt
   Größe. Referenz: Modell-Kapsel im Chat-Kopf (148 × 38).
3. **Jeder Kopf muss auf 375 pt Breite passen** (iPhone mini/SE/16e) ohne
   Umbruch und ohne Überlappung: Titel + Kapsel + Aktions-Knöpfe. Prüfen bei
   jeder Änderung an Headern.
4. **Keine Überlappungen** von Karten/Elementen (z. B. Identity Card über
   „Nachweise"). Abstände aus der Registry: Spacing 4/8/12/16/20/24/32.
5. **Radien** nur 9/12/16/18/24/28; Springs .24/.38/.55; Motion micro 140 ms,
   shift 220 ms, reveal 420 ms; `prefers-reduced-motion` respektieren.
6. **Touchziele ≥ 44 × 44 pt.** Knöpfe ohne Trefffläche sind ein Fehler.

### Typografie & Farbe
7. **SF Pro / Systemschrift** (Display für Headlines, Text für Fließtext),
   **SF Mono** für HID, Herkunft, Scope, Confidence, Serien, technische Werte
   (Modell-IDs, Adressen, Tokens). Keine anderen Fonts. Wortmarke immer
   lowercase „hunch".
8. **Palette:** Ink `#0d0d0b/#171713/#25241f/#39372f`, Ivory
   `#fffefa/#f7f4eb/#eee9dc/#ddd5c2`, Stone `#716b5e/#5e584d`, Signal Gold
   `#e7cf82/#d5ad4d/#bd8d24/#8a6412/#624508`. Flächen: 70 % Ink+Ivory, 20 %
   Stone, **≤ 10 % Gold**. Gold/Folie nur für Eigentümerschaft, Auswahl,
   Signatur, Freigabe — nie Primärtext. Kein Rot als Markenfarbe (Rot nur als
   Fehler/Risiko-Signal, immer mit Wort oder Symbol).
9. **Zustand ist signiert, nicht gefärbt:** Risiko, Status, Ergebnis bekommen
   Wort oder Symbol, nie nur Farbe.

### Kein AI-Slop
10. **Keine Kästen-in-Kästen, keine Chips, keine Ringmuster-Badges, keine
    gerahmten Labels.** Status = kleines Mono-Wort (+ Punkt), ohne Rahmen und
    ohne Hintergrund. Lieber Hairline und Typografie als Box.
11. **Keine nummerierten Schritt-Listen/Stepper** in der Oberfläche. Abläufe
    als Receipt/Ledger erzählen.
12. **Keine Emoji/Unicode-Glyphen als Icons** — nur SF Symbols oder das
    offizielle flache Signet (`SignetFlach`). Die 3D-Bronze-Eule ist
    Kampagnenmotiv, nie Master-Logo, nie Emoji-Kachel.
13. **Liquid Glass / Material** nur für Navigation und Overlays (Tab-Bar,
    Sheets), nie als Identität einer Inhaltskarte; bei Reduce Transparency
    opak.

### Credential-Material (Design-DNA)
14. Jede Fläche zeigt **Provenienz**: wem sie gehört, in welchem Scope sie
    handelt, was sie signiert (Kopf, Serienfeld, Receipt, Audit-Metadatum).
15. Inhalte auf **Perlmutt-Papier** mit Hairline, leisem Bevel, drei leisen
    Schatten (`0 1px 1.5px .08 / 0 5px 12px .06 / 0 18px 32px .055`) — keine
    harten Schlagschatten, kein Glow.
16. **Authority Gate:** Handlung in einem Satz, Konsequenz statt Prozess,
    Risiko mit Wort+Form+Farbe, Ablehnen und Freigeben gleichwertig, Undo wo
    möglich, jede Entscheidung auditierbar. Drei Entscheidungen: Ablehnen ·
    Annehmen (Ausweis) · Immer annehmen; optional Proof of Human (World ID).
17. **Identity Card:** 1.586:1, max 340 pt, Radius 28, Tilt max 7°, Finger
    drückt die Karte weg (kein Magnet), lässt man los → Standardposition.
    Reduced Motion blendet statt kippt.

### Sprache in der UI
18. Deutsch, ruhig, direkt, aktiv. Keine AI-Floskeln. Fachbegriffe als
    Denglisch: „intentional agent", Authority Gate, Observer/Executive, Brain,
    Fäden (deutsch), Session, Surface, Skill. Keine Feature-Listen ohne die
    Beziehung Mensch ↔ Hunch ↔ Handlung.
19. **Claim-Architektur:** jede Aussage trägt Status (heute / experimentell /
    als nächstes / vision); Gegenwart nie mit Zukunft verwechseln.
    Quelle: `website/PRODUCT_TRUTH.md`.

### Parität & Technik
20. **Jede Änderung in allen Oberflächen**: iOS-App, Mac-Desktop-App
    (`hunch-windows-repo`, Electron), Watch, Web/CLI — nicht „später".
    Siehe `hunch-runtime/PARITAET.md`.
21. **Modelle pro Anbieter sind eine Auswahl** (Picker aus bekannten
    Modellen), nie Freitext als Standard.
22. **Geheimnisse nur Keychain** (`SecretStore`), nie UserDefaults, nie Log.
    Maschinen heißen in der UI kurz („Lokal · MacBook"), nie mit voller
    Tailscale-Adresse.
23. Release: signierte Archive (manuelles Release-Signing je Target), Push
    braucht `aps-environment`; `UNUserNotificationCenterDelegate` nutzt die
    Completion-Handler-Variante (die `async`-Form stürzt beim Tipp ab).

## Review-Protokoll (Codex-Gate)
- Erst Layout-Invarianten prüfen (Regeln 1–6) — ein Titel, der umbricht, oder
  eine Kapsel, die mit dem Inhalt wächst, ist **BLOCK**.
- Dann Slop-Regeln (10–13) und Palette/Typo (7–9).
- Dann Parität (20): fehlt die Desktop-Seite, **BLOCK** mit dem Hinweis, was
  dort nachzuziehen ist — außer die Änderung ist plattformspezifisch
  (Watch, Live Activity, Keychain).
- Bei Unsicherheit: Brand Bible lesen, nicht raten.
