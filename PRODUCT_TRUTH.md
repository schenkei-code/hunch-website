# PRODUCT_TRUTH.md

Die einzige Quelle der Wahrheit für die öffentlichen Aussagen auf hunchagent.io.
Jede Website-Behauptung muss hier mit **Quelle** und **Status** belegt sein. Bei
Widerspruch zwischen Roadmap und Code **gewinnt der Code**.

Status-Legende:
- **HEUTE** — im aktuellen Code vorhanden und getestet; runtime-abhängige Aussagen zusätzlich
  gegen die laufende Runtime nachgewiesen
- **EXPERIMENTELL** — teilweise, nur auf einer Surface, oder Prototyp
- **ALS NÄCHSTES** — in Arbeit / nahe Roadmap
- **VISION** — 2.0-Zielbild, nicht ausgeliefert

Repos geprüft (Grundabgleich 2026-09-03; App-Menü-/Auslieferungsnachtrag 2026-09-06):
- `hunch-runtime` @ `init-runtime` — Python-Runtime, FastAPI, CLI, MCP-Server
- `hunch-app-repo` (hunch-app) @ `health-sync` — iOS-App (Pocket), aktueller geprüfter Branch
- `hunch-windows-repo` @ `windows-app` — Desktop-App (Electron)
- `hunch-harness`, `hunch` (Brain-Forschung), `website`

Bei iOS gilt: aktueller Swift-Code > HANDOFF.md > PLAN-INTENTIONAL.md > MEILENSTEINE-2.0.md.
Ältere Roadmaps sind nur historisch. Beispiel: `MONETIZATION.md` behauptet StoreKit/Paywall
„gebaut und getestet" — im Pocket-Target gibt es **null** StoreKit-Referenzen (HANDOFF.md §0).
Daher: **kein Kauf-/Paywall-Feature auf der Website.**

---

## Runtime — verifizierte Fähigkeiten

### Observer / Executive — HEUTE
Zwei-Modell-Architektur. Observer liest, antwortet nie, bündelt Ereignisse, schätzt Absicht
und Konfidenz; Executive wird ab Konfidenz-Schwelle **0.85** geweckt, prüft Autorität, ruft
Werkzeuge, meldet. Ohne Observer-Modell läuft ein ehrlicher Regelmodus.
Quelle: `observer.py`, `executive.py`, `config.py:103`; `test_e2e.py`.

### Guardrails / Governor — HEUTE (7 im README-Table + 2 weitere im Code = ~9)
Die Website zeigt **7 Karten** (Website behauptete 7, zeigte aber nur 6 — behoben):
1. Kosten/Tagesbudget (500k Token, persistent) — `governor.may_spend`
2. Modellwahl (klein dauerhaft, groß ab 0.85) — `autopick.py`
3. Risiko, 3 Klassen: read_only / write_low_risk / critical_action — `models.py:16`
4. Freigabe mit Vorschau (Werkzeug/Argumente/Ziel/Risiko/Begründung) — `executive.py:192`
5. Impuls-Bremse (Cooldown 900s + Tagescap; Unterdrücktes abgelegt) — `governor.may_nudge`
6. Kaputte Werkzeuge (3 Fehler → 5 min Pause) — `governor.record_tool_failure`
7. Protokoll (append-only Audit mit Begründung); verschachtelte Geheimnisfelder werden
   rekursiv geschwärzt, Modell-/Werkzeugausgaben nur als Länge + SHA-256 nachgewiesen — `audit.py`
Zusätzlich im Code, nicht als Karte gezählt: **Prüfer** (Zweitprüfmodell, exakt `HARMLOS`
oder fragen; nie Auto-Freigabe für kritisch) `pruefer.py`; **Ausweis-Tor** (kein verifizierter
Besitzer ⇒ kein Werkzeug in Executive/Fäden) `executive.py:107`, `faeden.py:424`.

### Fäden (parallele persistente Arbeitsstränge) — HEUTE
Eigener Auftrag, eigener Kontext, eigene Tool-Runden, persistent über Runtime-Neustart.
Cap MAX_PARALLEL=3. Zustände: `offen`, `laeuft`, `wartet` (auf Freigabe), `pausiert`,
`fertig`, `gescheitert`, `abgebrochen`. „Fortgesetzt" ist ein Historienereignis; der
persistierte Zustand geht dabei zurück auf `offen`. Hinter Ausweis (Gäste bekommen Antwort,
nie einen Agenten).
Quelle: `faeden.py`, `test_faeden.py`.

### Antizipation / Vorhersage — HEUTE (4 Arten, reine Statistik, kein LLM, keine Kosten)
- **routine** — Stundenhistogramm: was diese Tageszeit meist betrifft
- **folgt_auf (follow-on)** — Ein-Schritt-Markov über aufeinanderfolgende Ereignisse
- **faellig (recurring)** — Themen mit erkennbarer Kadenz, jetzt fällig
- **momentum** — Begriff, der zuletzt stark ansteigt
Untrusted/synthetische (heartbeat) Ereignisse ausgeschlossen. Hinter Ausweis (Verhaltensprofil).
Quelle: `vorhersage.py`, `test_vorhersage.py`; `GET /vorhersage`.

### Pattern-of-Life / Wissensgraph — HEUTE (2026-08-22, G7)
`graph.py`: Tabellen `graph_nodes`/`graph_edges` (thema, person, ort, datei, vorhaben, faden; Kanten
erwaehnt/gehoert_zu/folgt_auf/gleichzeitig), regelbasierte Extraktion (kein LLM), inkrementell über
`graph.cursor`, Dauerlauf „graph" alle 30 min mit Nulllauf-Protokoll; `GET /graph`, `GET /muster`
(Stundenprofil + Übergänge aus `vorhersage.py` + Kadenzen + Graph-Kennzahlen), beide hinter Ausweis.
Live 2026-08-22: 106 Knoten/625 Kanten aus 26 Erinnerungen + 416 Ereignissen. App: Brain → Graph
(Canvas, Kraft-Layout einmal gerechnet, Tippen zeigt Name · Art) + Karte „Muster" (Build 105).
`tests/test_graph.py`.

### Sensoren / Rewind / Import — HEUTE (2026-08-22, G11; macOS)
`sensoren.py`: Vordergrund-App, Fenstertitel (Bedienungshilfen-Recht), Browser-URL (Safari/Chrome via
osascript), Dateiänderungen (Ordner aus `HUNCH_SENSOREN_ORDNER`), Screen-OCR nur mit Bildschirmaufnahme-
Recht, über macOS Vision (`sidecar/ocr/hunch-ocr.swift`, einmalig mit swiftc gebaut; Rückfall tesseract; sonst ehrlich gemeldet); Ruhezeiten 23–7, Dedupe, Schleife 15 s,
ein/aus über `HUNCH_SENSOREN`, `hunch sensoren an|aus|status`, `GET/POST /sensoren`; Ereignisse
`source=sensor`. Standardmäßig nur ins Gedächtnis, `HUNCH_SENSOREN_OBSERVER=1` reicht an den Observer.
MCP `search_screen`/`get_screen_activity` echt. `chat_import.py` + `hunch import <datei>` (txt/md,
ChatGPT-`conversations.json`, Claude-Export) → Ereignisse `source=import` mit Originalzeit.
`tests/test_sensoren.py` (15). Live: Sensoren 2026-08-22 eingeschaltet; Vision-OCR las den Sperrbildschirm-Text in 0,3 s.

### Auslöser + Wiederaufnahme — HEUTE (2026-08-22, G8)
`ausloeser.py`: Arten zeit (`taeglich 07:30`, `alle 30 min`, `mo,mi 09:00`, `werktags …`), datei
(mtime-Polling), build (Kommando mit Exit≠0), kanal (Quelle+Muster, Hook in `Runtime.submit`) → Auftrag
oder Faden; Wiederaufnahme: lange gescheiterte/wartende Fäden → `pausiert`, `POST /faeden/{id}/fortsetzen`.
`GET/POST/DELETE /ausloeser`, `hunch ausloeser list|add|rm`, Schleife 60 s. Live: Zeitauslöser
„Tagesstart 07:30" angelegt. `tests/test_ausloeser.py` (8).

### Globale Konversation + Presence — HEUTE (G9; App-Chat seit Build 106)
`memory.py`: `conversations`/`messages` im Schema und im Brain-Sync (Schema 4); Konsole, Telegram-Chat
und Web-Chat spiegeln in denselben Verlauf, die Konsole liest eine Sitzung nach Neustart zurück;
`GET /v1/conversations`, `GET /v1/conversations/{id}/messages`. `presence.py`: `POST/GET /v1/presence`,
`app_state`-Ereignisse zählen; Impulse/Freigaben zuerst an die aktive Oberfläche (offene Verbindung), sonst
alle offenen, sonst Push — Audit `zustellung`. App meldet Presence (Build 105). App-Chat (Build 106):
`AgentSession.archiveToBrain` spiegelt jede Chat-Sitzung als Brain-Gespräch (`surface: app`), BrainSync trägt
conversations/messages (Schema V4, append-only, jüngerer Stand am Gespräch), fremde Gespräche (cli/web/telegram)
erscheinen im Brain mit Surface-Mono-Label und lassen sich „Hier fortsetzen" (letzte 30 Zeilen in die
Session, Antwort wandert zurück). `tests/test_konversation.py`, `PocketTests/KonversationSyncTests` (7).

### Vorhaben auf Desktop-Surfaces — HEUTE (2026-08-22, G10)
`hunch vorhaben list|add|stand`, Weboberfläche (Abschnitt Vorhaben, `GET /vorhaben/ansicht`), Cockpit-Block.
`tests/test_vorhaben_surfaces.py` (6).

### Vorhaben-Ausführer (2.0) — HEUTE (2026-08-22, G12)
`planer.py`: Plan (3–8 Schritte) aus dem Executive-Modell in `vorhaben_plaene`, Schritte als Fäden unter
`vorhaben:<id>`, rückt nach fertigen Fäden vor, schreibt `stand`/`next_step`; Fehlschlag → einmal neu planen,
dann `pausiert` + Impuls; Schleife „planer" 60 s setzt nach Neustart fort; Modellwechsel ändert den Zustand
nicht (liegt in der DB). `POST /vorhaben/{id}/ausfuehren`, `GET /vorhaben/{id}/plan`,
`POST /vorhaben/{id}/pausieren`; App: „Ausführen lassen"/Plan/„Pausieren" unter jedem aktiven Vorhaben
(Build 105). `tests/test_planer.py` (6). Rückfragen nur für Besitzer-Entscheidungen: sichere/reversible
Schritte ohne Nachfrage (Governor), kritische durchs Gate.

### Agenten-Tresor — HEUTE (2026-08-22, G5)
`agent_tresor.py`: `tresor_eintraege` (login/payment/passkey), Geheimnis nur mit dem Tresor-Schlüssel
verschlüsselt (Anlegen nur bei offenem Tresor). `vault_use` ist immer kritisch und fest auf „immer
fragen"; es bestätigt Zweck und bei Zahlungsmitteln Betrag, entschlüsselt das Geheimnis aber nicht und
gibt es nie als Werkzeugergebnis aus. Eine echte Übergabe braucht einen zielgebundenen lokalen Adapter.
Eine Aufsperrung läuft nach spätestens 24 Stunden ab; der Wartungstakt verlängert sie nicht.
Audit schwärzt auch verschachtelte Geheimnisfelder und dupliziert keine Klartextausgabe,
`GET/POST/DELETE /v1/vault/items`, `POST …/reveal`, `hunch tresor list|add`. App: Wallet → „An Maschine
geben" + Abschnitt „Auf der Maschine" (Build 105). `tests/test_agent_tresor.py`,
`tests/test_tresor_ablauf.py`.

### Apple Watch — EXPERIMENTELL (Target gebaut; physischer Gerätetest offen)
Der aktuelle Source enthält das watchOS-Target `HunchWatch`: Freigaben über WatchConnectivity ↔ iPhone,
Arbeitsschritt der Work-Live-Activity als Zeile, HUNCH_APPROVAL-Aktionen, Diktat → Maschine → vorgelesene
Antwort sowie die WidgetKit-Complication (accessoryCircular/Rectangular/Inline, App Group
`group.com.hunchagent.hunch`). Target und Build sind belegt. Ob Freigabe, Sprache und Complication auf
Dominiks echter Uhr Ende zu Ende funktionieren, ist noch nicht bestätigt; deshalb kein vollständiges HEUTE.

### Werkzeuge — HEUTE (fünf Herkünfte, ein Verzeichnis)
- **Eingebaut, u. a.:** `search_memory`, `remember`, `list_tasks`, `add_task`, `list_goals`,
  `add_goal`, `update_goal`, `run_command`, `http_get`, `vault_use` (+ bedingte Bündel:
  Chat-, Reach-, Browser-Tools). `tools/builtin.py`, `agent_tresor.py`
- **Skills:** `SKILL.md` wird nur mit einem getrennten Manifest für exakten
  Pfad, Namen, Byteumfang und SHA-256 geladen. Fremde GitHub-/Import-Referenzen
  bleiben in Quarantäne. Python `run(arguments)` braucht zusätzlich die
  ausdrückliche Startfreigabe. Kein Erweiterungsloader darf einen vorhandenen
  Werkzeugnamen ersetzen; die Herkunft enthält den Inhalts-Hash.
  `tools/skills.py`, `tools/registry.py`, `tests/test_skill_loader_security.py`.
- **MCP:** fremde Server aus `mcp_config.json`, dynamisch. `tools/mcp_client.py`
- **REST:** Connectoren aus `connectors.json`, ohne Code. `register_rest_connector`
- **Externe Agent-Harnesses:** eingebaut **codex, claude, gemini, aider**; eigene via
  `~/.hunch/harnesses.json`. Ein Tool `run_agent`, immer kritisch. `harness.py`

### Automatische Verdichtung — HEUTE (Nachweis 2026-08-22)
`verdichter.py`, Schleife „verdichtung" alle 6 h (Ruhezeit beachtet); Audit `actor=verdichter` — auf der
laufenden Runtime 16 Einträge, Nulllauf wird protokolliert („nichts zu verdichten"). `test_verdichter`.
Seit 2026-09-02 gelangen nur vertrauenswürdig markierte Ereignisse in die Verdichtung; externe/untrusted
Inhalte und daraus abgeleitete Observer-Signale werden nicht als Erinnerung zurückgeschrieben.

### Gelernte Skills — HEUTE (mit Grenze)
Nach ≥3 identischen Erfolgen kann die Runtime `auto_<tool>.SKILL.md` schreiben (sichtbar/editierbar).
Die Datei enthält nur wertfreie Platzhalter aus dem Werkzeugschema, nie frühere Argumente oder
Begründungen. Das v2-Format wird beim Schreiben im privaten Vertrauensmanifest an seinen Hash
gebunden; eine Änderung nimmt ihm bis zur erneuten Prüfung die Aktivierung. Alte Auto-Dateien ohne
dieses Format bleiben inaktiv und werden nie still überschrieben. Der Rückweg prüft Datei und
Manifestfreigabe gegen Name und Inhalts-Hash; nur im passenden Stand entzieht er die Freigabe und
entfernt anschließend die Datei. Einen bearbeiteten oder neueren Nachfolger lässt er unangetastet.
Werkzeugnamen, die nicht verlustfrei aus Buchstaben, Ziffern und `_` bestehen, werden nicht
automatisch als Skill gelernt.
Gelernte Skills lernen nicht rekursiv weiter;
`run_agent`, `run_command`, `vault_use`
und Datei-/Sprachnachrichten-Versand sind ausgeschlossen. Kein autonomes Training, keine
Selbstumprogrammierung. `executive._maybe_learn_skill`, `tests/test_skill_lernen.py`,
`tests/test_fahrtenbuch.py`.

### Provider — HEUTE (Observer und Executive unabhängig wählbar)
Cloud: `claude, openai, gemini, kimi, deepseek, qwen, mistral, grok, groq`.
Gerät: `appleLocal` (nur On-Device). Lokal: `ollama, lmstudio, llamacpp`.
CLI: `claude-cli, codex-cli, gemini-cli`. Fallbacks: `cli:<cmd>`, `custom:<name>` +
`HUNCH_*_BASE_URL` (jeder OpenAI-kompatible Endpoint). `providers.py`, `test_providers.py`.
Breitere Provider — HEUTE (2026-08-22, G6): `openrouter`, `together`, `fireworks`, `cerebras`,
`perplexity`, `bedrock` (OpenAI-kompatibler Bedrock-Endpunkt, Bearer-API-Key, Region via
`HUNCH_*_BASE_URL`) in `providers.py` **und** `ProviderRegistry.swift` (Build 103); `test_providers`
prüft Wire-Format + Swift-Abgleich (17 Zeilen deckungsgleich).
Provider-, APNs- und World-ID-Diagnosen geben nur feste Fehlerklassen, HTTP-Status und bekannte
Reason-Codes aus; weder Antwortkörper noch Token, Proof, Nonce oder Nullifier landen im Betriebslog.
CLI und Cockpit entfernen Terminal-, Zwischenablage- und Bidi-Steuerfolgen vor Anzeige und Kürzung.
`ausgabesicherheit.py`, `push.py`, `world_id.py`, `tests/test_ausgabesicherheit.py`.

### Gedächtnis / Brain — HEUTE
Sync-Cursor zeigt nie in die laufende Millisekunde (2026-08-22): vorher konnte ein Eintrag derselben
Millisekunde mit kleinerer ID für immer übersprungen werden (59 von 60 im Test) — jetzt doppelt statt
fehlend, `merge` verwirft Dubletten.
Runtime und App führen getrennte lokale Datenbanken. Ihre gemeinsamen Sync-Formen umfassen
`memories`, `action_items`, `goals`, `conversations` und `messages`. `POST /brain/sync` gleicht
beidseitig ab, Cursor aus Zeitstempel+ID; Erinnerungen wachsen nur, bei veränderlichen Einträgen
gewinnt der jüngere Stand. FTS5-Suche.
MCP-Server-Modus bietet `search_memory`, `remember`, `list_tasks`, `add_task`, `recent_context`,
`search_screen` und `get_screen_activity` (bewusst kein `run_command`/`run_agent`).
`memory.py`, `mcp_server.py`, `test_brain_shared.py`, App `BrainSync.swift`.

### Memory-Scopes (global / projekt / faden) — HEUTE (2026-08-22, G2)
`memories.scope` (`global` | `projekt:<goal_id>` | `faden:<id>`) in Runtime (`memory.py`, Migration +
Index) und App (`BrainMemory.scope`, Schema v3). Ablage/Suche/Kontext je Ebene, Dublette nur innerhalb
einer Ebene, Verschieben (`set_memory_scope` / `moveMemory`) wandert über `/brain/sync` (jüngerer Stand
gewinnt; Antwort trägt `schema: 3`), Vorhaben fließen jetzt auch App→Runtime. Fäden legen automatisch in
`faden:<id>` ab und lesen global+Faden; Werkzeuge `remember`/`search_memory`, MCP (`scope`, `HUNCH_SCOPE`),
CLI `--scope`, Endpunkte `/brain/scopes`, `/brain/memories`, `POST /brain/memories/{id}/scope`,
`DELETE /brain/memories/{id}` (Ausweis). App: Brain → Ebenen-Filter, Ebene an der Zeile, Kontextmenü
„Verschieben nach"/„Löschen" (Build 103). Tests: `tests/test_scopes.py`, `test_brain_shared.py`.
**Präferenzen** bleiben flach (`UserIdentity.preferences`); strukturierte Präferenzen = Erinnerungen mit
Ebene (Kategorie „Präferenz") — kein eigener Speicher.

### Autorität / Sicherheit — HEUTE (Kette, kein Einzelschalter)
**Prüfgrenze, 06.09.2026:** Die folgenden gebauten Mechanismen sind keine vollständige
Sicherheitsfreigabe. Der Nachweis für Berechtigungswechsel bei laufenden Verbindungen
ist noch offen; lokale Korrekturen werden geprüft und sind noch nicht live eingespielt.
Das öffentliche Update bleibt davon getrennt und ist nicht freigegeben.

- Secure-Enclave-Besitzeridentität: Runtime hält nur den P-256-Public-Key, Challenge/Verify
  (ECDSA), 24h-Session. `ausweis.py`
- Risikoklassen, Governor, Budgets, Circuit-Breaker, Prüfer/Zweitprüfung
- Freigabe mit Vorschau (Werkzeug/Argumente/Ziel/Risiko/Begründung), persistent
- Audit (append-only, verschachtelte Geheimnisfelder geschwärzt, Inhaltsausgaben als Länge + SHA-256),
  Gastisolation (`besitzer`/`frei`/`gast`), Einlass-Codes (Einmal, 15 min)
- **Weniger strenger Modus vor der Einrichtung:** ohne enrollten Besitzer gibt `darf_alles()`
  True zurück — bewusst (`ausweis.py:216`). Die kryptografische Sperre ist NICHT automatisch
  aktiv, bevor die Besitzeridentität eingerichtet ist. Ehrlich so dokumentieren.
- **Master-Token nach der Einrichtung:** bleibt Zugang für unpersönliche Betriebsdaten, ist aber
  kein Besitzer-Ausweis. Brain, privater Chat, Graph, Muster, Sensoren, Voice und kritische Aktionen
  verlangen danach einen widerrufbaren Geräte-Token mit passender Risikogrenze.
- **Rückweg (Undo) — HEUTE (2026-08-21):** `rueckweg.py`, remember/add_task hinterlassen Rückweg,
  `GET/POST /rueckweg`; App: Einstellungen → Agent-Runtime → Rückweg. Erinnerungen/Aufgaben/Vorhaben.
- **Wallet (Logins, Zahlungsmethoden, Passkeys) — HEUTE, Menschen-Seite (2026-08-22, Build 99):** App → Profil → Wallet:
  Einträge lokal, Geheimnisse im Schlüsselbund (SecretStore), Aufdecken nur mit Face ID/Code. Agenten-Seite (Runtime-Tresor,
  Werkzeug hinter Authority Gate, Audit/Rückweg) — HEUTE seit Build 105 (Ausführung `agent_tresor.py` auf `tresor.py`, `vault_use`).
- **Mitteilungen als Authority-Gate-Anfrage beim Öffnen — HEUTE (Build 102):** `MitteilungenGateView` (Ink-Karte,
  Erlauben/Später), erst „Erlauben" ruft den System-Dialog; Gerätezeichen geht an jede verbundene Maschine (`pushEinrichten`).
- **Freigaben aus der Mitteilung — EXPERIMENTELL (Code + APNs belegt; Aktion E2E offen):** Push-Kategorie
  HUNCH_APPROVAL mit Freigeben (Face ID)/Ablehnen ist im App-Code vorhanden; APNs nahm den Server-Push
  mit 200 an. Der Action-Handler wurde ab Build 118 korrigiert, aber ein echter Button-Tipp auf Build ≥118
  wurde noch nicht bestätigt. Spiegelung und Aktion auf einer echten Apple Watch sind ebenfalls offen.
- **Profil = Credential-Hub — HEUTE (Build 99):** Ausweis, Nachweise (HID/Secure Enclave, World ID, vertrauende Maschinen), Wallet, Profile.
- **World ID Human in the Loop — HEUTE (2026-08-22):** Runtime `world_id.py` + Sidecar (offizielles IDKit): `GET /world`,
  `POST/GET /approvals/{id}/world`; Proof an Action `authority-approve` + RP-signierte Nonce gebunden, Verify gegen
  `developer.world.org/api/v4/verify/{rp_id}`, Replay-Schutz, Audit mit bestätigtem Credential-Typ,
  aber ohne Proof-/Nonce-/Nullifier-Rohdaten. Live bestätigt 2026-08-22 13:06 (proof_of_human).
  App: Button „Mit World ID bestätigen" seit Build 98 in TestFlight (Freigaben-Kachel). World ist optional — Ausweis/App bleiben Standard.
- **Vorhaben (1.8) — HEUTE (2026-08-21):** Runtime `goals` mit `stand`/`next_step`, Tools list_goals/add_goal/update_goal,
  `add_task(goal=…)` verknüpft Schritt ↔ Vorhaben, `/vorhaben` (Ausweis-gated), Abgleich über `/brain/sync`
  (jüngerer Stand gewinnt); App: BrainGoal.stand/nextStep (Schema v2), Bearbeiten in der Zielzeile, MCP get_goals.
- **Grenze einsehbar — HEUTE (2026-08-21):** `GET /grenze`; App: „Die Grenze“.
- **Fahrtenbuch (Action-Log) — HEUTE (2026-08-22, G3):** jeder Audit-Eintrag trägt Begründung (`reasoning`, vor der
  Ausführung gesetzt), `rueckweg_id` und `umkehrbar` (True/False/None); `GET /audit` liefert `rueckweg_offen`.
  App: Einstellungen → Agent-Runtime → **Fahrtenbuch** mit Zurück-Knopf (Build 104). `tests/test_fahrtenbuch.py`.
- **Umfassendes Undo — HEUTE (2026-08-22, G3):** Rückweg-Typen `memory`, `task`, `goal`, `goal_update` (alter
  Stand/nächster Schritt/Fortschritt/aktiv), `memory_scope`, `skill` (gelernte SKILL.md + Registrierung), `file`
  (Schnappschuss in `~/.hunch/rueckweg/`, oder Datei wieder entfernen). `run_command`, `run_agent`, `web_ansehen` sind
  ausdrücklich **nicht umkehrbar** (`UNUMKEHRBAR`) und so protokolliert — kein stilles Schweigen.
- **Geräte- & Aktionsgrenzen — HEUTE (2026-08-22, gehärtet 2026-09-01, G4):** Freigabe je
  Gerät/Kanal mit `max_risk` (`read_only` | `write_low_risk` | `critical_action`). Die Runtime
  leitet die Autorität serverseitig aus Token/Kanal ab, trennt Observer-Bündel je Principal und
  persistiert sie an Signal, Faden und wartender Freigabe. Vor Ausführung wird die aktuelle Grenze
  erneut geprüft; Entzug oder Senkung schließt offene WS-, SSE- und Voice-Drähte, auch nach einem
  lokalen `hunch geraete`-Befehl. Einlass beginnt mit `write_low_risk`; Verwaltung über
  `GET/POST /v1/identity/geraete`, `hunch geraete`; App: Profil → Nachweise → Maschinen →
  **Vertrauen**. `ausweis.py`, `observer.py`, `faeden.py`, `executive.py`,
  `tests/test_geraete.py`, `tests/test_risikogrenze.py`, `tests/test_voice.py`.
- Geräteübergreifende Authority-Oberfläche — EXPERIMENTELL (G9/G13): Presence-Routing und Zustellung an
  die aktive Oberfläche, sonst Push, sind im Code vorhanden. CLI und Web sind belegt; der korrigierte
  Notification-Action-Pfad auf iPhone Build ≥118 und die Aktion auf einer echten Uhr warten noch auf E2E-Nachweis.
- **Lokale Geheimnis- und Dateigrenze — HEUTE (gehärtet 2026-09-03):** Kanal-Tokens liegen außerhalb
  von `channels.json`, der Web-Token nur im flüchtigen Tab-Speicher, externe Kindprozesse bekommen eine
  Positivliste statt der gesamten Runtime-Umgebung, Wallet-Kennwörter gehen über stdin statt Prozessargumente.
  Runtime-Datenordner/Sicherungen sind 0700, Datenbanken, Push-Zustand und Logs 0600; Nachrichtenanfänge
  stehen nicht im Betriebslog. `tests/test_channel_secrets.py`, `tests/test_subprocess_sicherheit.py`,
  `tests/test_wallet.py`, `tests/test_dateisicherheit.py`.

### Endpoints — HEUTE (Source/lokal verifiziert; kein aktuelles Live-Inventar)
Lokale Introspektion des aktuellen Source ergibt 127 HTTP-Methoden/Pfad-Kombinationen auf 115
eindeutigen HTTP-Pfaden: 108 stehen im lokal erfolgreich erzeugten OpenAPI-Schema; sieben sind bewusst
nicht darin (OpenAPI-/Doku-Flächen sowie `/`, `/chat`, `/vorhaben/ansicht`). Dazu kommen drei WebSockets.
Die laufende Runtime antwortete bei der Prüfung auf `/status` und `/doctor` mit 200, auf
`/openapi.json` aber mit 500. Die folgende Auswahl ist daher ein Source-Nachweis, kein vollständiges
Live-Inventar:
identity: `/v1/identity`, `/v1/identity/enroll|challenge|verify|grant`, `/v1/einlass[/erzeugen]`
fäden: `/faeden` (GET/POST), `/faeden/{id}` (GET/DELETE), `/faeden/{id}/fortsetzen` (POST)
approvals: `/approvals`, `/approvals/{id}`, `/proposals`, `/approve`, `/deny`
console: `/v1/konsole[/{id}|/freigabe]`, `/v1/exec`
channels: `/v1/channels[...]`, telegram/whatsapp
memory: `/brain/sync`, `/brain/search`, `/brain/memories[...]`, `/brain/scopes`, `/v1/intents`
tasks/session/goals: `/sitzung`, `/vorhersage`, `/vorhaben[...]`
tools/audit: `/tools`, `/audit`
vault: `/v1/vault[...]`
providers: `/providers`, `/runtimes`, `/v1/machine`
wallet: `/v1/wallet`, `/v1/wallet-pass`
events/nudges/push: `/events`, `/v1/events`, `/nudges`, `/v1/push[-token]`
rechenschaft: `/rueckweg` (GET), `/rueckweg/{id}` (POST) — Undo; `/grenze` (GET) — einsehbare Grenze (beide hinter Ausweis, 2026-08-21)
status: `/status`, `/doctor`, `/v1/web/login|profile`
stream/ws: `WS /ws`, `WS /v1/ws`, `WS /v1/voice/ws`, `GET /v1/stream` (SSE-Fallback)
web: `GET /`, `GET /chat`, `GET /vorhaben/ansicht`
MCP: kein HTTP — nur stdio (`python -m hunch_runtime.mcp_server`).
Keine erfundenen Endpoints auf der Website oder in der Doku.

---

### Relay (1.6) — NICHT GEPLANT (Entscheidung Dominik 2026-08-21: kein Hosting)
Kein gehosteter Relay-Dienst. Erreichbarkeit von unterwegs = Tailscale-Adresse + TLS + Token
(siehe Loslegen). Auf der Website nicht als „Als Nächstes" führen.

## App / iOS — verifiziert (branch health-sync)

### Öffentlicher App-Store-Stand — Update vorbereitet, noch nicht veröffentlicht (06.09.2026)
**Aktueller Nachtrag R72:** Der öffentliche Entwurf ist jetzt **1.6 mit Build 147**,
`PREPARE_FOR_SUBMISSION` und `AFTER_APPROVAL`. Apple hat 147 als `VALID` verarbeitet;
intern ist er in beiden TestFlight-Gruppen verfügbar. Noch kein Produktions-Submit
und keine öffentliche Veröffentlichung. Aktuelle anonyme Storebilder und gemeinsame
Endabnahme bleiben offen. Der folgende 1.5.1/146-Stand ist der vorherige Nachweis.

App Store Connect bestätigt iOS 1.5 als `READY_FOR_SALE`. Der bestehende Update-Entwurf
1.5.1 verwendet jetzt Build 146 statt Build 125; sein Status wechselte von
`INVALID_BINARY` zu `PREPARE_FOR_SUBMISSION`. Aktuelle DE/EN-Versionshinweise,
Beschreibungen und Review-Anleitung sind gespeichert und nachgelesen. Der Apple-Verlauf
zeigt die sofortige Zurückweisung des alten Builds 125 als ungültige Binärdatei am
24.08.; ein weiterer Begründungstext ist nicht sichtbar. Die alte Einreichung ist noch
nicht erneut übermittelt. Die englischen Store-Bilder sind leer bzw. zeigen die alte
deutsche Oberfläche; frische anonyme Original-Captures fehlen. Der vorhandene gemeinsame
Authority-Nachweis bleibt separat offen. Keine öffentliche Veröffentlichung von 1.5.1
behaupten. TestFlight ist separat.

Die Store-Copy trennt lokale Apple-Verarbeitung (iOS 26+, Systemmodell tatsächlich
verfügbar) von gewählten Cloudmodellen und Voice-Diensten. Die optionale Voice-Brücke
kann beim Verbindungsfehler auf Gemini mit vorhandenem Nutzer-Key zurückfallen; direkte
Voice fordert derzeit deutsche Antworten an. Deshalb kein pauschales Local-only-
Versprechen. Quelle: `AppleLocalProvider.swift:35–43`, `VoiceEngine.swift:285–310,362–370,403–413`,
`VoiceScreen.swift:417`; Review-Anleitung ohne die entfernte Vier-Seiten-Tour.

### Menüordnung — TestFlight 146 intern/extern, Mac-Installation offen (06.09.2026)
iOS `bab3029`: Modelle und eigene Anbieter stehen zusammen; der unverändert wirkende
Schalter für nichtkritische Werkzeugfreigaben steht unter „Sicherheit & Freigaben“.
Die Suche berücksichtigt die tatsächlich sichtbaren Plattform-/Debug-Bereiche.
Desktop `cf82737`: Erinnerungen sind eine eigene Inhaltsroute, Wallet liegt im Profil;
Agent-Konfiguration ist von allgemeinen Einstellungen getrennt. Aufnahmen erklärt den
Unterschied zwischen fortlaufender Transkription und Voice-Chat. Der lokale Desktop-Tresor
benennt ausdrücklich seine fehlende Verbindung zum Runtime-Tresor/Authority Gate.
Quelle: `SettingsView.swift`, `SettingsSearchIndex.swift`, Desktop `Sidebar.tsx`,
`Settings.tsx`, `AgentTab.tsx`, `RewindTab.tsx`, `Profil.tsx`, `Wallet.tsx`.
Nachweis: 89 iOS-Tests, 866 Desktop-Tests bestanden; drei Desktop-Tests übersprungen.
Gezielte Sichtprüfung, kein vollständiger Geräte-/Live-Nachweis. TestFlight Build 146
ist seit 06.09. `VALID` / `IN_BETA_TESTING`, mit geprüfter produktiver Push-Berechtigung,
DE/EN-Versionshinweisen und bestätigter Zuordnung zu beiden internen Gruppen. Apple hat
inzwischen auch die externe Beta genehmigt (`APPROVED`, extern `IN_BETA_TESTING`). Das
ist keine App-Store-Veröffentlichung. Die neue Desktop-Installation wartet
auf reguläres Beenden der bisher laufenden App; Paket und wiederherstellbare Sicherung
sind vorbereitet. **Kein neues öffentliches HEUTE-Versprechen** und kein Website-Deploy.

### Berechtigungszwecke — Source und Mac-Paket geprüft, Auslieferung offen (06.09.2026)
Desktop `8112d4c` korrigiert die bisher falsch verschachtelten macOS-Zwecktexte.
Das tatsächliche neue Bundle enthält Mikrofon-, Systemaudio- und Bildschirmzweck
sowie passende deutsche und englische Systemressourcen; ungenutzte generische
Kamera-/Bluetooth-Texte sind entfernt. Audio ist nicht pauschal lokal: die Zwecke
benennen den eingerichteten Dienst bzw. die Runtime. Die native Mikrofon-Copy in
`2dd4cc1` umfasst Voice und gestartete Gesprächsaufnahmen sowie mögliche Verarbeitung
auf dem Gerät, durch Apple oder den eingerichteten Anbieter/Server.

Nachweis: 873 Desktop-Tests bestanden, drei übersprungen, Produktionsbuild und
Kontrolle des erzeugten Mac-Pakets grün; beide Sprachressourcen durch Foundation
gelesen. Ein isolierter nativer Quellvertrag bestanden, kein vollständiger neuer
App-Testlauf. Das Mac-Paket bleibt lokal, unsigniert und nicht installiert; echte
Systemdialoge und Hardwareaufnahme sind offen. Die native Änderung ist **nicht in
TestFlight/App-Store-Kandidat 146 enthalten** und benötigt ein neues signiertes Archiv.
Keine neue öffentliche Verfügbarkeitszusage und keine Änderung des Grunddesigns.
Quelle: Desktop `electron-builder.yml`, `scripts/mac-usage-descriptions.cjs`,
`packaging/mac-privacy/`; nativ `Info.plist`, `InfoPlist.xcstrings`, `project.yml`.

### Aufnahme-Freigaben — geprüftes Desktop-Paket, noch nicht ausgeliefert (06.09.2026)
Desktop `4fd05c2` ersetzt den simulierten Bildschirm-Erfolg durch eine echte
Berechtigungsprüfung und bestätigtes Speichern. Auf macOS zählt der aktuelle
Systemstatus; Windows/Linux prüfen bei der ausdrücklichen Aktivierung einen
nutzbaren Videostream und geben ihn sofort wieder frei. Mikrofonfehler sind kein
Erfolg. Überspringen während der Abfrage verhindert eine spätere Aktivierung;
ab dem tatsächlichen Speicherauftrag ist Überspringen gesperrt.

Bildschirmverlauf und automatische Insight-Analyse sind bei neuen Installationen
ausgeschaltet. Vorhandene gültige Einstellungen bleiben unverändert; ein alter
gespeicherter Einschaltwert beweist keine frühere bewusste Einwilligung. Automatischer
Chat-Bildschirmtext benötigt eingeschalteten Verlauf und auf macOS zusätzlich die
aktuelle Systemfreigabe. Die Oberfläche unterscheidet lokale Bilder von Bildschirmtext,
der als Chat-Kontext oder bei separat eingeschalteter Analyse an Anbieter gehen kann.
Einstellungen und Sidebar verwenden dieselbe Aktivierungsprüfung. Einzelaufnahmen
bleiben ein eigener, ausdrücklich gestarteter Weg. Der ungenutzte simulierte
Dateizugriff-Schritt ist entfernt; kein aktiver Menüweg entfällt.

Nachweis: 993 Desktop-Tests bestanden, drei übersprungen; 23 gerenderte Fälle mit
echten Komponenten und gemockten System-/Speicherantworten unter React.StrictMode
bei 1024×640 und 375×812, einschließlich Reduced Motion. Keine Konsolenfehler,
Warnungen oder externen Requests im isolierten Prüflauf. Produktionsbuild und
tatsächliches Mac-Paket geprüft. Kein echter OS-Dialog, Hardware-, Vollsecurity-
oder Installationsnachweis; kein neues öffentliches HEUTE-Versprechen. iOS/Watch
lesen den Bildschirmverlauf der Maschine, besitzen aber keine entsprechende lokale
Aufnahme. Das Grunddesign bleibt unverändert.
Quelle: Desktop `screenCapturePermission.ts` (Main/Renderer), `PermissionStep.tsx`,
`ScreenPermissionStep.tsx`, `MicPermissionStep.tsx`, `useScreenHistoryToggle.ts`,
`rewindSettings.ts`, `insight/state.ts`, `ipc/screen.ts`, `ipc/rewind.ts`.

### Datei-Discovery — Source geprüft, Auslieferung und Mac-Quellen offen (06.09.2026)
Desktop `6f71bb9`: Der Einstieg liest erst nach „Dateien einlesen“ ein. Kein
simulierter Erfolg oder automatischer Scan beim Öffnen. Vollständig, leer,
teilweise lesbar, nicht unterstützt und fehlgeschlagen sind getrennte Zustände.
Nur ein vollständiger Lauf ersetzt den Index atomar; bei Fehlern bleiben die
alten gespeicherten Einträge erhalten. Gefundene und gespeicherte Anzahl sind
nicht dasselbe. Hintergrundläufe bleiben nach Menüwechsel sichtbar; spätere
Statusabfragen starten weder Scan noch Analyse.

Dateinamen, Metadaten und App-Verknüpfungen werden lokal indexiert, keine Inhalte
gelesen. „Neu scannen“ in Einstellungen startet keine Modellgraph-Analyse mehr.
Ein späterer Chat oder die separate Wissensgraph-Analyse kann Indexdaten an den
eingerichteten Anbieter schicken; deshalb kein pauschales „nie hochgeladen“.
Der Scanner unterstützt tatsächlich nur Windows-Standardordner. Mac/Linux
melden fehlende unterstützte Quellen; ein Mac-Dateiscanner ist damit nicht gebaut.
iOS/Watch besitzen diesen lokalen Desktop-Indexer nicht. Installierte Apps im
Onboarding-Graphen sind außerdem noch kein nachgewiesenes Nutzungsverhalten.

Nachweis des Funktionsstands: 1.059 Tests bestanden, drei übersprungen;
Produktionsbuild, beide Typechecks und 57 isolierte gerenderte Fälle grün.
Echte Komponenten, synthetische Daten, StrictMode, 1024×640/375×812,
normal/Reduced Motion. Kein echter Dateiscan, Geräte- oder Installationsnachweis.
Grunddesign unverändert; kein neues HEUTE-Label. Quelle: Desktop
`fileIndex/indexer.ts`, `ipc/fileIndex.ts`, `ipc/db.ts`, `useFileIndex.ts`,
`fileIndexStatus.ts`, `BuildProfileStep.tsx`, `AdvancedTab.tsx`.

**Paketstand `130c0cc`:** Explizites Laufzeit-Inventar verhindert das Mitpacken
alter Builds und eigener Entwicklungsdateien auch bei anderem Ausgabeordner.
Tatsächliches bereinigtes Mac-Paket geprüft; sieben Runtime-Dateien bytegleich,
DE/EN-Zwecktexte korrekt. Vollständige Desktop-Suite danach 1.102 bestanden,
drei übersprungen; 43 zusätzliche Paketprüfungen. Kein gültiges Distributions-
Signing, keine Installation und keine öffentliche Auslieferung. Frühere lokale
Prüfpakete mit zusätzlichem Entwicklungsinhalt nicht als Release verwenden.

### Kennenlernen und Graph-Herkunft — Source geprüft, nicht ausgeliefert (06.09.2026)
Desktop `08ee271`, Runde 57: Neue App-Verknüpfungen heißen „im Datei-Index
gefunden“, nicht „genutzt“. Zielvorschläge erhalten nur ausdrücklich indexbezogene
App-Namen und werden weiterhin vor dem Speichern bearbeitet/bestätigt. Der
Synthese-Prompt verlangt belegte Memory-Aussagen für Nutzungsbeziehungen; dies ist
keine deterministische Prüfung der Modellantwort. Alte, möglicherweise unbelegte
`uses`-Beziehungen bleiben unangetastet und sind keine nachträglich bestätigte Nutzung.

Erneutes Öffnen des Desktop-Einstiegs lädt den gemeinsamen Graphen, statt ihn zu
löschen. Laden und ausdrückliche Graph-Schreibvorgänge laufen geordnet; ein Fehler
verwirft nicht den vorherigen sichtbaren Stand und sperrt keine Folgeanfragen.
Keine Migration und kein Zugriff auf private Bestandsdaten im Prüflauf.

Nativ `184f686`: macOS überspringt den wirkungslosen Berechtigungsschritt; iOS
fragt weiterhin erst nach „Erlauben“ Mitteilungen und Mikrofon an. DE/EN versprechen
keine garantierte Zahl von Systemdialogen. Der Abschluss unterscheidet lokale
Speicherung von möglicher Kontextweitergabe an Anbieter/verbundene Maschinen.
Keine Änderung der View-Geometrie, keine neue Aufnahmefähigkeit für den Mac.

Nachweis: 1.116 Desktop-Tests bestanden, drei übersprungen; Produktionsbuild,
beide Typechecks, Preload-Vertrag und gezieltes Lint grün. Nativ 34 isolierte
Prüfungen des tatsächlichen Kennenlern-Scripts und iOS-SDK-Typecheck bestanden.
20 isolierte gerenderte Desktop-Fälle bestanden: Discovery/Ziel bei 1024×640
und 375×812, normal/Reduced Motion; echte Einstiegseite mit gestubbtem WebGL-Graph
und unbetroffenen Diensten bei 1024×640. Keine Konsolenfehler oder Außenrequests.
Das sind keine vollständige native App-/Geräteprüfung oder Release-Nachweise.
Noch kein neues Paket/Archiv dieser Änderungen; Build 146 enthält sie nicht.
Keine Watch-/CLI-/Web-Quelle für lokale Desktop-App-Shortcuts erfunden, keine
Änderung des Grunddesigns und kein neues öffentliches HEUTE-Label.

### Daten, Quellen und Wartung — Source geprüft, nicht ausgeliefert (06.09.2026)
Desktop `403ea8f`, Runde 58: „Daten & Quellen“ enthält Import/Export, Integrationen
und Datei-Index; „Wartung“ enthält Auto-Bereinigung, Erinnerungs-Wartung,
Graph-Neuaufbau und erneute Einrichtung. Die bestehende Auto-Bereinigung entfernt
technische Reste, nicht nach einer Zeitregel. Ihr gespeicherter Modus bleibt
unverändert. Löschen steht im Aktionsmenü und verlangt weiter eine Bestätigung.
Der frühere Erweitert-Link öffnet Daten & Quellen; alte Erinnerungs-Links behalten
ihr Inhaltsziel. Suche und Bereichswechsel erhalten Entwürfe. Ein gewählter Bereich
beginnt am sichtbaren Titel; bei schmaler Breite sind Navigation und Inhalt gestapelt.
Normale Desktop-Maße, Palette, Schrift, Material und Ausweis-/Voice-Design bleiben.

Die Import- und Kurznotiztexte erklären nun, dass Text und vorhandene Erinnerungen
zur Extraktion an den gewählten Anbieter gehen können. Das frühere „Notizen werden
nie hochgeladen“ war falsch. Der Graph-Neuaufbau erklärt Modellanalyse getrennt
vom Dateiscan. Keine Änderung an Integrationskonten, Quellen, Freigaben oder Sync.

Nativ `e716560`: Quellen/Kalender/Aufbewahrung/Bereinigung finden die bestehenden
Memory-Einstellungen; App-Stand sichern/wiederherstellen findet Agent-Runtime.
Keine neue native Gruppe, keine Änderung der Geometrie; Plattform-/Debug-Filter
bleiben. Watch/CLI/Web besitzen diese lokalen Desktop-/nativen Einstellungswege
nicht und erhalten keine erfundenen Ersatzflächen.

Nachweis: 1.125 Desktop-Tests bestanden, drei übersprungen; Produktionsbuild,
Typechecks und Preload-Prüfung grün. Fünf isolierte native XCTest-Fälle sowie
iOS-SDK-Typecheck bestanden. 17 gerenderte Desktop-Fälle bei 1024×640/375×812,
normal/Reduced Motion bestanden, inklusive bestätigtem Löschabbruch ohne Schreib-
aufruf; synthetische Quellen und externe Dienste gestubbt.
Keine vollständige native App-/Geräteabnahme, Installation oder neue Auslieferung;
Build 146 enthält diese Änderungen nicht. Kein neues öffentliches HEUTE-Label.
Quelle: Desktop `Settings.tsx`, `DataTab.tsx`, `MaintenanceTab.tsx`,
`settingsNavigation.ts`; nativ `SettingsSearchIndex.swift`, `SettingsView.swift`.

### Ziele, Aufgaben und Fäden — QUELLSTAND, NOCH NICHT AUSGELIEFERT (06.09.)

Desktop `8fb0de0`: Ziele und Aufgaben bleiben lokale Daten; Fäden gehören zur verbundenen
Hunch-Runtime. Die vorhandenen Flächen erklären jetzt den Unterschied und
verlinken einander. Zielvorschläge sind Entwürfe mit getrennt geprüftem Messwert:
Ein Datum im Titel bestimmt nicht den Fortschrittsmaßstab. Der Einstieg geht
erst nach bestätigtem Speichern weiter; Fehler behalten den Entwurf. Die
abschließende Aufgabenliste ist ausdrücklich eine ungespeicherte Beispielvorschau.

Nativ `00f5a29`: Fehler beim Brain-INSERT erzeugen kein scheinbar gespeichertes
Ziel; im Kennenlernen bleiben Eingabe und Schritt erhalten. KI-Vorschläge werden
vor dem Speichern bearbeitet. DE/EN unterscheiden Speichern von einem Auftrag an
die Runtime und erklären mögliche Brain-Synchronisierung statt „bleibt auf diesem
Gerät“. Die bestehende native Zielwertgrenze ist 1; Desktop akzeptiert positive
Dezimalwerte. Keine neue allgemeine Synchronisierung oder automatische Ausführung.

Der Abgleich fand außerdem einen falschen Desktop-Claim: Zum Stand dieser Runde
fehlte der Fortsetzen-Client, pausierte Fäden standen unter Beendet. Runde 62
korrigiert dies im Quellstand; Auslieferung und Live-Nachweis bleiben offen.
Prüfungen und Belege: PROGRESS/MENUE_AUDIT Runde 60. Grunddesign, Ausweis und Voice
unverändert; kein neues HEUTE-Label, Gerätetest, signiertes Archiv oder Release.
Build 146 enthält diese Änderungen nicht.

### Hub — HEUTE
Der aktuelle Hub hält dieselben **11 Routen** in vier ruhigen Gruppen: **Jetzt** —
Freigaben, Fäden, Intention; **Verstehen** — Brain, Bildschirm; **Verbinden** —
Maschinen, Kanäle, Nodes; **Werkzeuge** — Skills & MCPs, Apps, GitHub. `.sitzung`
bleibt nur der interne Schlüssel für die sichtbare Fläche „Intention“.
Quelle: `AppModel.swift:24-29`, `HunchHubView.swift:81-136`;
`IntentionalClientRenderSafetyTests.swift:404-434`.

### Dynamic Island / Work Live Activity — HEUTE
`WorkActivityAttributes.swift` Phase-Enum: **denkt, arbeitet, wartet, fertig, gescheitert**.
`.wartet` = „Freigabe erforderlich" (einzige nutzergerichtete, farbig hervorgehoben; kein
separater freigabe-Case). Zeigt Fortschrittsbalken, selbstlaufende Laufzeituhr (`Text timerInterval`),
Deep-Link `pocket://chat`. Zweite (Voice) Live Activity existiert ebenfalls.
Quelle: `HunchWidgets/WorkLiveActivity.swift`, `AI/WorkLiveActivityController.swift`.

### Voice — HEUTE (ehrlich)
Voice nimmt Audio auf dem Gerät auf; die Gesprächsverarbeitung läuft wahlweise
über Gemini Live mit Nutzer-Key oder über die verbundene Runtime-/S2S-Brücke.
`UIBackgroundModes` enthält `audio`; die Audio-Session unterstützt Bluetooth,
A2DP und AirPlay. Siri/CarPlay kann die App über „Sprich mit Hunch“ öffnen und
Voice sofort starten. Hunch startet weiterhin kein Gespräch autonom aus dem
Hintergrund; proaktive Signale kommen per APNs.
Quelle: `VoiceSettingsView.swift`, `VoiceEngine.swift`, `VoiceIntents.swift`, `Info.plist`.

### Identität / Secure Enclave — HEUTE
EC-P-256-Schlüssel in der Secure Enclave (`kSecAttrTokenIDSecureEnclave`), biometrisch
geschützt, nicht exportierbar, kein Backup. Nur Public-Key exportiert. **HID** = SHA-256-
Fingerprint des Public-Keys als „HID 0000 0000 0000 0000". Challenge/Signatur beim Handshake.
Vor Schlüsselerzeugung meldet `OwnerIdentity` ehrlich „HID — — — —"; nur die sichtbare Karte
markiert ihren kurzlebigen, namensbasierten Rückfall mit „HID ·“. Der Simulator nutzt eine
Ersatz-Identität statt eine Secure Enclave vorzutäuschen.
Quelle: `AI/OwnerIdentity.swift`, `Views/IdentityCardView.swift`,
`Connection/IntentionalAgentClient.swift`.
**Alte Fallback-HID „6699 3937" nicht mehr verwenden** — die neue Karte leitet aus dem Namen ab.

### Lokale Werkzeug-Autorität / Codex — HEUTE
„Nicht-kritisches automatisch erlauben“ gilt ausschließlich für begrenzte,
umkehrbare Hunch-Werkzeuge. Kritisches fragt immer. Codex besitzt eine eigene
Ausführungsschleife und deshalb keine Einzelrückfragen: Standard ist `read-only`;
`workspace-write` muss bewusst gewählt werden und gibt Schreibrecht im gewählten
Arbeitsordner. `danger-full-access` wird in Hunch nicht angeboten.
Quelle: `AI/Runtime/ToolRegistry.swift:8-25`, `AgentSession.swift:570-575,841-859`,
`SettingsView.swift:186-197`, `CodexProvider.swift:144-191,497-511`,
`RuntimeSettingsViews.swift:1091-1116,1185-1191`;
`IntentionalClientRenderSafetyTests.swift:337-434`.

### App-Fähigkeiten — Status
HEUTE (lokal, ohne Runtime seedbar): Brain (Erinnerungen/Aufgaben/Ziele/Gespräche, SQLite+FTS5),
deterministische Predictions+Topics+Momentum (`BrainEngine`), lokale Nudges, Audit-Trail,
Token-Budget (CostGovernor), Secure-Enclave-Identität, Work-Live-Activity,
Voice und Hunch-Memory-Export/-Import als JSON.
HEUTE, aber runtime-abhängig (holen live vom `IntentionalAgentClient`): Fäden, Nodes/Maschinen,
Skills & MCPs mit Risiko, Intention/Vorhersage, Kanäle, Freigaben, Apps,
GitHub, Wissensgraph/Pattern-of-Life, Bildschirm-Fernansicht und App-Nudges.
Memory-Scopes `global`, `projekt:<id>` und `faden:<id>` sind in App, Runtime
und Brain-Sync vorhanden. `UserIdentity.preferences` bleibt flach; strukturierte
Präferenzen werden als Erinnerungen der Kategorie „Präferenz“ in einem Scope abgelegt.
Externe Transkripte importiert heute die Runtime-CLI (txt/md, ChatGPT, Claude);
die native iOS-Dateiauswahl akzeptiert derzeit nur Hunch-Memory-JSON.
Grenze: Das iPhone selbst sendet als Szenensensor weiterhin nur `app_state`
und den aktuellen App-Screen; Bildschirm-OCR entsteht auf der Maschine.

### StoreKit / Paywall — EXISTIERT NICHT
Kein StoreKit/Paywall/IAP im aktuellen Branch. „Subscription"-Treffer betreffen OAuth-Login
gegen ein bestehendes ChatGPT/Claude-Abo als Alternative zum API-Key, keine App-Store-Monetarisierung.

### Screenshot-Fixtures — HEUTE
`-uitest-marketing-fixtures` seedet lokal reproduzierbare, anonymisierte Demo-Daten (Brain,
Identität, Audit, Budget). Runtime-abhängige Screens (Fäden/Nodes/Skills/Sitzung/Kanäle) brauchen
einen Fixture-Pfad im `IntentionalAgentClient` — siehe Delivery, welche Screens echt gefüllt sind
und welche als gekennzeichnetes Konzept dargestellt werden.

### Aufgaben- und Zieländerungen — QUELLSTAND, NOCH NICHT AUSGELIEFERT (06.09.)

Native Source `712469b`: Anlegen, Ändern und Löschen lokaler Aufgaben sowie
Ändern/Löschen von Zielen bestätigen den Datenbankeintrag. Fehler erhalten
Entwürfe und zeigen keine falsche Erledigung; dasselbe gilt für die native
MCP-Aufgabenerledigung. Kalender merkt bestätigte Teilimporte. Fehlgeschlagene
Aufgaben aus Aufnahmen waren in Runde 61 nur während der geöffneten Brain-
Ansicht erneut speicherbar. Runde 63 erweitert dies auf die laufende App,
weiterhin nicht dauerhaft über Neustarts gepuffert.

Desktop `17589b3`: Tasks/Goals zeigen bestätigte Einzeländerungen statt optimistischer
Listen. Fehler bei einem Eintrag rollen keine bereits gespeicherte andere
Änderung zurück; ältere Ladeantworten überschreiben keine neuen Bestätigungen.
Eingaben bleiben bei Fehlern erhalten. Keine zusätzliche Maschinenarbeit,
allgemeine bidirektionale Brain-Synchronisierung oder neue Fäden-Fähigkeit.

Isolierte Fehler-/Retry-/Importprüfungen und vollständige Builds: PROGRESS und
MENUE_AUDIT Runde 61. Native Gesprächs-/Memory-Speicherung und Sync-Upserts
wurden anschließend in Runde 63 getrennt geprüft. Kein Geräte-/Live-Nachweis oder neues HEUTE-Label;
diese Änderungen sind nicht im App-Store-/TestFlight-Kandidaten 146 enthalten.

### Fäden-Zustände und Aktionen — QUELLSTAND, NOCH NICHT AUSGELIEFERT (06.09., Runde 62)

Desktop `07e2074`: Aktive, unterbrochene, beendete und unbekannte Fäden sind
getrennt. Pausierte, gescheiterte und abgebrochene Fäden lassen sich ausdrücklich
fortsetzen; wartende Freigaben führen ins Authority Gate. Ladefehler sind keine
leere Liste. Aktionen bleiben an die gelesene Runtime-Verbindung gebunden und
zeigen nur geprüfte Bestätigungen. Rückmeldungen stehen am betroffenen Faden;
spätere Hintergrundabgleiche verändern die Scrollposition nicht.

Nativ `06225bb` behalten Detail, Abbruch, Fortsetzen und neuer Auftrag ihre Maschine und
Verbindung. Ladefehler erhalten den letzten bestätigten Stand. Fehler verlieren
keinen Auftragsentwurf; unklare Antworten lösen keinen automatischen Schreib-
Retry aus. Ein neuer Auftrag schließt erst nach einer gültigen Bestätigung mit
Kennung und Titel. Die bestehende Grenze von 2000 Zeichen wird erklärt statt
still gekürzt. DE/EN nachgeführt. Abbruch ist kein Undo bereits erfolgter Arbeit.

Nachweise: 1256 Desktop-Tests bestanden / 3 übersprungen, 25 native Zustands-
und Modelltests plus 25 injizierte HTTP-Prüfungen, vollständiger Pocket-Compile-
only-Build und Desktop-Produktionsbuild. Gerendert: 56 Hauptfälle bei 375/1024 px,
normal/reduzierter Bewegung; zusätzlich 8 Rückmeldungsfälle. Details, Commit
und Grenzen: PROGRESS/MENUE_AUDIT Runde 62. Diese UI-Prüfungen verwenden
synthetische Daten, keine echte Runtime oder installierte App. Kein neues
HEUTE-Label, Gerätetest, Store-Submit, Archiv, Runtime- oder Website-Deploy.
Build 146 enthält diese Änderungen nicht; das gemeinsame Authority-/Security-
und Live-Gate bleibt offen. Watch/Web/CLI erhalten keine erfundenen Fäden-Editoren.

### Erinnerungen und Gespräche — QUELLSTAND, NOCH NICHT AUSGELIEFERT (06.09., Runde 63)

Native Source `c239d3d` / `c643ec6`: Memory- und Gesprächsänderungen bestätigen
den lokalen Schreibvorgang, bevor Entwürfe verschwinden, Spiegel aktualisiert
oder Erfolge gemeldet werden. Sync bestätigt alle angenommenen Schreibvorgänge,
bevor Cursor, Zeitstempel oder Bereinigung fortschreiten; bestätigte Teile
bleiben bei einem späteren Fehler erhalten. Unbrauchbare Antworten sind kein
erfolgreicher leerer Abgleich. MCP und der lokale Remember-Weg unterscheiden
bestehende Erinnerungen von fehlgeschlagenem Speichern. Ein Chatwechsel verliert
bei Archivfehlern nicht den aktuellen Verlauf.

Aufnahme-Transkripte bleiben bei Speicherfehlern auf beiden App-Surfaces während
der laufenden App erhalten. Ausdrückliches Wiederholen speichert den vorhandenen
Text, ohne Mikrofon oder Modell neu zu starten. Diese Zwischenablage überlebt
keinen App-Neustart. Nativ gilt dies auch für noch ungespeicherte extrahierte
Erinnerungen und Aufgaben. Späte Berechtigungs- oder Zielvorschlagsantworten
starten nach Verlassen keine versteckte Aufnahme bzw. überschreiben keinen
neuen Entwurf. Kurze erkannte Notizen sind nicht mehr allein wegen ihrer
Wortzahl Löschkandidaten; automatische Audio-Segmentierung bleibt unverändert.

Desktop Source `5ee3e18` / `c19a075` bestätigt neue Erinnerungen unabhängig von einem späteren Ladefehler.
Teilimporte behalten unbestätigte Vorschläge und warnen vor unklaren Antworten;
vor erneutem Import soll die Liste geprüft werden. Titelentwürfe bleiben bei
Fehlern offen, verspätete automatische Titel überschreiben keine manuelle
Umbenennung. Mehrfachlöschen zeigt bestätigte Löschungen und Fehler getrennt;
Undo gilt nur während der Wartefrist, nicht nach ausgeführter Löschung.

Grunddesign, Materialien und normale Schriftgrößen unverändert. Neue
Rückmeldungen DE/EN; dies ist noch keine vollständige Desktop-Lokalisierung.
Quell-, isolierte Speicher-/Sync-, Build- und anonymisierte Renderer-Nachweise:
PROGRESS/MENUE_AUDIT Runde 63. Keine echte Aufnahme-, Runtime- oder Geräteprüfung,
keine allgemeine neue Brain-Synchronisierung, kein Release/Deploy oder HEUTE-
Upgrade. Watch/Web/CLI besitzen diese lokalen Editorwege nicht. Native Profil-
Autosaves/Session-Merge, Nudge-Bestätigungen und Desktop-Chat-Archivierung bleiben
separate Anschlussprüfungen. Build 146 enthält diese Source nicht; StoreKit/IAP
bleibt ungebaut und das gemeinsame Authority-/Security-/Live-Gate offen.

### 06.09.2026 — Ergebnisbelege nach Freigaben · Runde 64

**QUELLSTAND, NOCH NICHT AUSGELIEFERT.** Nach einer Freigabe unterscheidet
hunch die angenommene Entscheidung von der tatsächlichen Ausführung. Der neue
Beleg nennt Entscheidung, Ausführungszustand, Zeitpunkt, Audit-Kennung und
einen Rückweg nur dann, wenn er wirklich verfügbar ist. Eine unklare Antwort
ist kein Erfolg: Die Apps lesen den Beleg nach, ohne die Handlung erneut
auszulösen. Die Runtime hält bereits beanspruchte Entscheidungen dauerhaft
fest; ein unterbrochener Versuch ist keine neue Ausführungserlaubnis.

iPhone/native App und Desktop zeigen den aktuellen Beleg getrennt vom
eingeklappten Verlauf. Alte Ergebnisse verdrängen keine offenen Entscheidungen.
Watch, Runtime-Web und CLI verwenden denselben Ergebnisvertrag; die Watch
verweist für das Zurücknehmen auf das iPhone. Lokale Werkzeugprotokolle bleiben
von Runtime-Belegen getrennt. Neue Rückmeldungen sind Deutsch/Englisch; dies
ist keine vollständige Übersetzung aller bestehenden Desktop-/Web-Texte.
Grunddesign, Materialien und normale Schrift-/Symbolgrößen bleiben erhalten.

Die Source-, isolierten Test-, Build- und anonymisierten Renderer-Nachweise
stehen in PROGRESS/PARITAET/MENUE_AUDIT Runde 64. Keine neue Auslieferung,
echte Geräte-/Push-/Watch-/Runtime-Endabnahme oder allgemeine Sicherheitsfreigabe.
Build 146 enthält diese Änderungen nicht. Öffentlicher Release, neuer signierter
Kandidat und passende Storebilder bleiben getrennte Gates; StoreKit/IAP bleibt
ungebaut. Kein HEUTE-Label wird durch diese Quellarbeit angehoben.

## Nachweisgrenze, 06.09.2026 — Runde 65

Die Runtime-Gesamtsuite besteht im vorhandenen Arbeitsstand 453 von 453 Fällen
unter einem versionierten anonymen Testläufer. Kein Fall abgewählt, keine
Verletzung der Test-I/O-Grenzen. Eigene lokale Protokollpartner ersetzen echte
Anbieter und Besitzerprofile; die Prüfung ist kein Live-, Hardware- oder
allgemeiner Sicherheitsnachweis. Ablauf und Grenzen: PROGRESS/PARITAET R65.
Keine neue App-Funktion, Auslieferung oder öffentliche Store-Einreichung in
dieser Runde. Aktuelle Storebilder, neuer signierter Kandidat und gemeinsame
Endabnahme bleiben offen. Grunddesign unverändert; kein HEUTE-Upgrade.

## Browser-Menüs — QUELLSTAND, NICHT AUSGELIEFERT (06.09.2026, Runde 66)

Runtime `b412c93`: feste Kopfaktionen mit mindestens 44px Trefferfläche,
einzeilige Namen, Ink/Ivory und lowercase hunch. Auf schmalen Displays bekommen
die bestehenden Aktionen eine eigene Zeile. Vorhaben, Geräteverbindung und
Nachweise teilen einen Zusatzbereich; Chat und bearbeitete Vorhabenfelder
bleiben beim Menüwechsel erhalten. Fokus und Verbindung sind benannt. Zugang,
Browser-Chrome und Vorhaben-Feldnamen sind Deutsch/Englisch; eigene Inhalte
werden nicht übersetzt. Der Token bleibt nur im Arbeitsspeicher des Tabs.

460 isolierte Runtime-Tests und 64 anonyme Browserfälle bestanden. Dies belegt
die genannten Rahmen-/Navigationsänderungen und die Receipt-Regressionsfälle,
keine echte Authentifizierung, Geräteverbindung oder Speicherung von Vorhaben.
Details und Grenzen: PROGRESS/PARITAET/MENUE_AUDIT R66. Siegel-/Motion- und
vollständige Materialabnahme, Vorhaben-Schreibfehler und allgemeine Live-/
Geräte-/Release-Gates bleiben offen. Native/Mac/Watch-Grunddesign unverändert;
keine neue App-Store-Einreichung, Auslieferung oder HEUTE-Anhebung.

## Browser-Vorhaben — QUELLSTAND, NICHT AUSGELIEFERT (06.09.2026, Runde 67)

Runtime `bee1f12`: Abgelehnte oder unbestätigte Änderungen verlieren keine
Eingabe mehr. Nur passende positive Antworten bestätigen das Speichern oder
Anlegen. Bei einer unklaren Antwort erst nachlesen; kein automatischer zweiter
Schreibversuch. Nachgelesene Übereinstimmung bestätigt den Stand, nicht die
Ausführung einer bestimmten Anfrage. Lokales Abbrechen ist kein behaupteter
Server-Rollback. Alte Antworten ersetzen keine neuen Entwürfe; Rückmeldung,
Handlungen und Fokus bleiben verständlich zusammen. Grunddesign unverändert.

463 isolierte Runtime-Tests einschließlich echter eigener API-/SQLite-
Schreibfälle und 328 anonyme Browserfälle bestanden. Deutsch/Englisch,
schmale/breite Ansicht und reduzierte Bewegung geprüft. Dies ist kein Nachweis
gegen die laufende Runtime, keine neue gemeinsame Synchronisierung und kein
Geräte-/Sicherheits-/Release-PASS. Native/Mac/Watch unverändert; Storebilder,
neuer signierter Kandidat und gemeinsame Endabnahme bleiben erforderlich.
Details und Grenzen: PROGRESS/PARITAET/MENUE_AUDIT R67. Keine Auslieferung,
neue Store-Einreichung oder HEUTE-Anhebung; StoreKit/IAP weiterhin ungebaut.

## Startoptimierung — IN ARBEIT, NICHT AUSGELIEFERT (06.09.2026, Runde 70)

Der Desktop-Arbeitsstand lädt besuchte Bereiche bei Bedarf und trennt deren
Sichtbarkeit von bereits erlaubten Hintergrunddiensten. Entwürfe sollen beim
Bereichswechsel bestehen bleiben. Finale Interaktions-/Performanceprüfung und
Produktionsbuild fehlen noch; kein neues HEUTE-Label oder fertiger Leistungsclaim.
Grunddesign unverändert. Der aktuelle Apple-Abgleich bestätigt weiterhin
iOS 1.5.1 mit Build 146 in Vorbereitung, keine neue öffentliche Einreichung.
Die neueren Quelländerungen sind nicht in diesem Build enthalten. Passender
signierter Kandidat, Storebilder und Endabnahme bleiben erforderlich.

## Nächster iOS-Kandidat — GEPLANT: 1.6 (147) (06.09.2026, Runde 71)

Dominik hat Version 1.6, Build 147 als öffentliches Release-Ziel festgelegt.
Die nativen Versionsangaben für iPhone, Watch und Widgets sind gesetzt und
gegen Xcode geprüft. 147 ist noch nicht archiviert, hochgeladen oder eingereicht;
dies ist keine Veröffentlichung oder neue Funktionszusage. Letzter belegter
Apple-Stand bleibt R70. Grunddesign und offene Endabnahmen unverändert.

## iOS 1.6 (147) — INTERN VERFÜGBAR, ÖFFENTLICH VORBEREITET (06.09., Runde 72)

Der tatsächliche signierte Store-Build enthält 1.6/147 auf iPhone, Widgets,
Watch und Complication; produktive iPhone-Push-Berechtigung geprüft. Apple
bestätigt `VALID` und interne TestFlight-Verfügbarkeit in beiden Gruppen.
Der öffentliche Entwurf verwendet jetzt 1.6/147, bleibt in Vorbereitung;
für 147 keine externe Beta-Review oder Produktionseinreichung ausgelöst.

92 native XCTest-Fälle und 105 weitere isolierte Prüfungen bestanden. Das
belegt den Quell-/Buildstand, nicht neue Hardware-, gemeinsame Runtime- oder
vollständige UI-Abnahme. Grunddesign unverändert. Aktuelle vollständige anonyme
Storebilder nach Brand, gemeinsame Endabnahme und alte Apple-Review-Probleme
bleiben offen. Kein öffentliches HEUTE-Upgrade oder Runtime-/Website-Deploy;
der unfertige Desktop-Startstand bleibt außerhalb der Auslieferung. PROGRESS R72.

## Geführte Einführung — LOKAL GEPRÜFT, NICHT AUSGELIEFERT (06.09., Runde 73)

Native Quelle `bbb8961` und Desktop `d24deff` enthalten eine DE/EN-Einführung:
ein Anliegen formulieren, eine Beispielhandlung annehmen oder ablehnen, den
Unterschied zwischen Entscheidung und Ergebnis verstehen und die passenden
App-Bereiche finden. Überspringbar, in den Einstellungen wiederholbar;
persönliche Einrichtung getrennt. Die Übung versendet keine Nachrichten,
zeichnet nicht auf und erteilt keine echten Freigaben. Watch mit Kurzhilfe.

Beide Apps bündeln einen lokal erzeugten 24-Sekunden-Kurzfilm in DE/EN, mit
Textfassung und manueller Wiedergabe ohne Schleife. Ein kurzer Startübergang
und zentral abschaltbare iOS-Haptik ergänzen das unveränderte Grunddesign.
1472 Tests der eigenständigen Desktop-Version sowie Typechecks/Build bestanden;
native Übungslogik und Compilerlauf grün. Anonyme gerenderte Fälle bei schmaler
und breiter Ansicht geprüft. Das belegt keine physische Haptik, vollständige
native Bedienbarkeit oder allgemeine Verständlichkeit für neue Nutzer.

Diese Änderungen sind nicht Teil des bereits hochgeladenen iOS 1.6 (147).
Keine neue Buildnummer, kein Upload, keine Store-Einreichung und kein
öffentlicher Funktionsstatus geändert. Bestehende Geräte-/Release-Gates und
StoreKit/IAP-Status bleiben unverändert. Nachweise und Grenzen: PROGRESS R73.

## Desktop-Start und Eingaben — LOKAL GEPRÜFT, NICHT AUSGELIEFERT (06.09., Runde 74)

Desktop-Quellen `bf05d27`/`3048966`: Bereiche werden erst beim Besuch aufgebaut;
Entwürfe bleiben bei Rückwegen erhalten. Reine Anzeigeabfragen pausieren in
den geprüften verborgenen Bereichen, erlaubte Hintergrunddienste besitzen
einen getrennten Lebenszyklus. Die schmale Gesprächssuche bleibt nutzbar,
Eingaben verschieben nicht mehr den gesamten Einstellungsrahmen. Grunddesign
unverändert. Ersetzt den offenen Quellstatus des Startpakets aus Runde 70.

1562 Tests und 88 anonyme gerenderte Prüfungen bestanden, Produktionsbundle
grün. Weniger vorzeitige Arbeit im 60-s-Vergleich belegt; kein Nachweis eines
schnelleren ersten Bildes, echter Geräte-Bildrate oder allgemeiner Fehlerfreiheit.
Kein Live-/Geräte-/Security-Gesamt-PASS und keine Installation oder Auslieferung.
Native Einführung/Haptik aus Runde 73 weiterhin nicht Teil von iOS 1.6 (147).
Keine neue Buildnummer, kein Upload, Submit, Deploy oder HEUTE-Upgrade;
StoreKit/IAP und gemeinsame Abnahme bleiben unverändert. PROGRESS R74.
