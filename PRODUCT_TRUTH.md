# PRODUCT_TRUTH.md

Die einzige Quelle der Wahrheit für die öffentlichen Aussagen auf hunchagent.io.
Jede Website-Behauptung muss hier mit **Quelle** und **Status** belegt sein. Bei
Widerspruch zwischen Roadmap und Code **gewinnt der Code**.

Status-Legende:
- **HEUTE** — im aktuellen Code vorhanden und getestet
- **EXPERIMENTELL** — teilweise, nur auf einer Surface, oder Prototyp
- **ALS NÄCHSTES** — in Arbeit / nahe Roadmap
- **VISION** — 2.0-Zielbild, nicht ausgeliefert

Repos geprüft (Stand 2026-08-21):
- `hunch-runtime` @ `init-runtime` — Python-Runtime, FastAPI, CLI, MCP-Server
- `hunch-app-repo` (hunch-app) @ `feat/english-localization` — iOS-App (Pocket)
- `hunch-harness`, `hunch-windows`, `hunch` (Brain-Forschung), `hunch-website`

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
7. Protokoll (append-only Audit mit Begründung) — `audit.py`
Zusätzlich im Code, nicht als Karte gezählt: **Prüfer** (Zweitprüfmodell, exakt `HARMLOS`
oder fragen; nie Auto-Freigabe für kritisch) `pruefer.py`; **Ausweis-Tor** (kein verifizierter
Besitzer ⇒ kein Werkzeug in Executive/Fäden) `executive.py:107`, `faeden.py:424`.

### Fäden (parallele persistente Arbeitsstränge) — HEUTE
Eigener Auftrag, eigener Kontext, eigene Tool-Runden, persistent über Runtime-Neustart.
Cap MAX_PARALLEL=3. Zustände: `offen`, `laeuft`, `wartet` (auf Freigabe), `fertig`,
`gescheitert`, `abgebrochen`. Hinter Ausweis (Gäste bekommen Antwort, nie einen Agenten).
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
Recht **und** installiertem tesseract (sonst ehrlich gemeldet); Ruhezeiten 23–7, Dedupe, Schleife 15 s,
ein/aus über `HUNCH_SENSOREN`, `hunch sensoren an|aus|status`, `GET/POST /sensoren`; Ereignisse
`source=sensor`. Standardmäßig nur ins Gedächtnis, `HUNCH_SENSOREN_OBSERVER=1` reicht an den Observer.
MCP `search_screen`/`get_screen_activity` echt. `chat_import.py` + `hunch import <datei>` (txt/md,
ChatGPT-`conversations.json`, Claude-Export) → Ereignisse `source=import` mit Originalzeit.
`tests/test_sensoren.py` (15). Live: Sensoren 2026-08-22 eingeschaltet (OCR: tesseract fehlt).

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
verschlüsselt (Anlegen nur bei offenem Tresor), Werkzeug `vault_use` (immer critical, `HART_IMMER_FRAGEN` —
kein „immer annehmen"; Zahlungsmittel nur mit Zweck + Betrag), Audit schwärzt Geheimnisse,
`GET/POST/DELETE /v1/vault/items`, `POST …/reveal`, `hunch tresor list|add`. App: Wallet → „An Maschine
geben" + Abschnitt „Auf der Maschine" (Build 105). `tests/test_agent_tresor.py` (7).

### Apple Watch — HEUTE (Build 105, G13)
watchOS-Target `HunchWatch`: Freigaben (WatchConnectivity ↔ iPhone, Freigeben/Ablehnen), Arbeitsschritt der
Work-Live-Activity als Zeile, HUNCH_APPROVAL-Aktionen auf der Uhr, Sprechen (Diktat → Maschine → Antwort
vorgelesen). Offen: Complication, Gerätetest durch Dominik.

### Werkzeuge — HEUTE (vier Herkünfte, ein Verzeichnis)
- **Eingebaut:** `search_memory`, `remember`, `list_tasks`, `add_task`, `run_command`,
  `http_get` (+ bedingte Bündel: Chat-, Reach-, Browser-Tools). `tools/builtin.py`
- **Skills:** `SKILL.md` (Prosa fürs Modell) + Python `run(arguments)`. `tools/skills.py`
- **MCP:** fremde Server aus `mcp_config.json`, dynamisch. `tools/mcp_client.py`
- **REST:** Connectoren aus `connectors.json`, ohne Code. `register_rest_connector`
- **Externe Agent-Harnesses:** eingebaut **codex, claude, gemini, aider**; eigene via
  `~/.hunch/harnesses.json`. Ein Tool `run_agent`, immer kritisch. `harness.py`

### Automatische Verdichtung — HEUTE (Nachweis 2026-08-22)
`verdichter.py`, Schleife „verdichtung" alle 6 h (Ruhezeit beachtet); Audit `actor=verdichter` — auf der
laufenden Runtime 16 Einträge, Nulllauf wird protokolliert („nichts zu verdichten"). `test_verdichter`.

### Gelernte Skills — HEUTE (mit Grenze)
Nach ≥3 identischen Erfolgen schreibt die Runtime `auto_<tool>.SKILL.md` (sichtbar/editierbar).
Kein autonomes Training, keine Selbstumprogrammierung. `executive._maybe_learn_skill`.

### Provider — HEUTE (Observer und Executive unabhängig wählbar)
Cloud: `claude, openai, gemini, kimi, deepseek, qwen, mistral, grok, groq`.
Gerät: `appleLocal` (nur On-Device). Lokal: `ollama, lmstudio, llamacpp`.
CLI: `claude-cli, codex-cli, gemini-cli`. Fallbacks: `cli:<cmd>`, `custom:<name>` +
`HUNCH_*_BASE_URL` (jeder OpenAI-kompatible Endpoint). `providers.py`, `test_providers.py`.
Breitere Provider — HEUTE (2026-08-22, G6): `openrouter`, `together`, `fireworks`, `cerebras`,
`perplexity`, `bedrock` (OpenAI-kompatibler Bedrock-Endpunkt, Bearer-API-Key, Region via
`HUNCH_*_BASE_URL`) in `providers.py` **und** `ProviderRegistry.swift` (Build 103); `test_providers`
prüft Wire-Format + Swift-Abgleich (17 Zeilen deckungsgleich).

### Gedächtnis / Brain — HEUTE
Sync-Cursor zeigt nie in die laufende Millisekunde (2026-08-22): vorher konnte ein Eintrag derselben
Millisekunde mit kleinerer ID für immer übersprungen werden (59 von 60 im Test) — jetzt doppelt statt
fehlend, `merge` verwirft Dubletten.
Schema identisch zur App (`memories`, `action_items`). `POST /brain/sync` beidseitig, Cursor
aus Zeitstempel+ID; Erinnerungen wachsen nur, Aufgaben jüngster Stand. FTS5-Suche.
MCP-Server-Modus bietet `search_memory, remember, list_tasks, add_task, recent_context`
(bewusst kein `run_command`/`run_agent`). `memory.py`, `mcp_server.py`, `test_brain_shared.py`.

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
- Secure-Enclave-Besitzeridentität: Runtime hält nur den P-256-Public-Key, Challenge/Verify
  (ECDSA), 24h-Session. `ausweis.py`
- Risikoklassen, Governor, Budgets, Circuit-Breaker, Prüfer/Zweitprüfung
- Freigabe mit Vorschau (Werkzeug/Argumente/Ziel/Risiko/Begründung), persistent
- Audit (append-only), Gastisolation (`besitzer`/`frei`/`gast`), Einlass-Codes (Einmal, 15 min)
- **Weniger strenger Modus vor der Einrichtung:** ohne enrollten Besitzer gibt `darf_alles()`
  True zurück — bewusst (`ausweis.py:216`). Die kryptografische Sperre ist NICHT automatisch
  aktiv, bevor die Besitzeridentität eingerichtet ist. Ehrlich so dokumentieren.
- **Rückweg (Undo) — HEUTE (2026-08-21):** `rueckweg.py`, remember/add_task hinterlassen Rückweg,
  `GET/POST /rueckweg`; App: Einstellungen → Agent-Runtime → Rückweg. Erinnerungen/Aufgaben/Vorhaben.
- **Wallet (Logins, Zahlungsmethoden, Passkeys) — HEUTE, Menschen-Seite (2026-08-22, Build 99):** App → Profil → Wallet:
  Einträge lokal, Geheimnisse im Schlüsselbund (SecretStore), Aufdecken nur mit Face ID/Code. Agenten-Seite (Runtime-Tresor,
  Werkzeug hinter Authority Gate, Audit/Rückweg) — ALS NÄCHSTES.
- **Mitteilungen als Authority-Gate-Anfrage beim Öffnen — HEUTE (Build 102):** `MitteilungenGateView` (Ink-Karte,
  Erlauben/Später), erst „Erlauben" ruft den System-Dialog; Gerätezeichen geht an jede verbundene Maschine (`pushEinrichten`).
- **Freigaben aus der Mitteilung — HEUTE (Build 98):** Push-Kategorie HUNCH_APPROVAL mit Freigeben (Face ID)/Ablehnen; erscheint auf
  iPhone und gespiegelt auf der Apple Watch. Eigene Watch-App (Voice über verbundene Maschinen) — ALS NÄCHSTES.
- **Profil = Credential-Hub — HEUTE (Build 99):** Ausweis, Nachweise (HID/Secure Enclave, World ID, vertrauende Maschinen), Wallet, Profile.
- **World ID Human in the Loop — EXPERIMENTELL (2026-08-22):** Runtime `world_id.py` + Sidecar (offizielles IDKit): `GET /world`,
  `POST/GET /approvals/{id}/world`; Proof an Action `authority-approve` + RP-signierte Nonce gebunden, Verify gegen
  `developer.world.org/api/v4/verify/{rp_id}`, Replay-Schutz, Audit mit Nullifier/Credential. Live bestätigt 2026-08-22 13:06 (proof_of_human).
  App: Button „Mit World ID bestätigen" seit Build 98 in TestFlight (Freigaben-Kachel). World ist optional — Ausweis/App bleiben Standard. → HEUTE (Runtime & App).
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
- **Geräte- & Aktionsgrenzen — HEUTE (2026-08-22, G4):** Freigabe je Gerät/Kanal mit `max_risk`
  (`read_only` | `write_low_risk` | `critical_action`), `Ausweis.darf(quelle, risk)`; Einlass-Code beginnt mit
  `write_low_risk`; Fäden prüfen die Grenze ihrer Quelle; `GET/POST /v1/identity/geraete`, `hunch geraete`; App: Profil →
  Nachweise → Maschinen → **Vertrauen** (Grenze setzen/entziehen, Build 104). `tests/test_geraete.py`.
- Geräteübergreifende Authority-Oberfläche — HEUTE (G9/G13): Freigaben an die aktive Oberfläche, sonst Push; Uhr, iPhone, CLI, Web.

### Endpoints — HEUTE (39 HTTP + 2 WebSocket, code-verifiziert)
identity: `/v1/identity`, `/v1/identity/enroll|challenge|verify|grant`, `/v1/einlass[/erzeugen]`
fäden: `/faeden`, `/faeden/{id}` (GET/POST/DELETE)
approvals: `/approvals`, `/approvals/{id}`, `/proposals`, `/approve`, `/deny`
console: `/v1/konsole[/{id}|/freigabe]`, `/v1/exec`
channels: `/v1/channels[...]`, telegram/whatsapp
memory: `/brain/sync`, `/brain/search`, `/v1/intents`
tasks/session: `/sitzung`, `/vorhersage`
tools/audit: `/tools`, `/audit`
vault: `/v1/vault[...]`
providers: `/providers`, `/runtimes`, `/v1/machine`
wallet: `/v1/wallet`, `/v1/wallet-pass`
events/nudges/push: `/events`, `/v1/events`, `/nudges`, `/v1/push[-token]`
rechenschaft: `/rueckweg` (GET), `/rueckweg/{id}` (POST) — Undo; `/grenze` (GET) — einsehbare Grenze (beide hinter Ausweis, 2026-08-21)
status: `/status`, `/v1/web/login|profile`
stream/ws: `WS /ws`, `WS /v1/ws`, `GET /v1/stream` (SSE-Fallback)
web: `GET /`, `GET /chat`
MCP: kein HTTP — nur stdio (`python -m hunch_runtime.mcp_server`).
Keine erfundenen Endpoints auf der Website oder in der Doku.

---

### Relay (1.6) — NICHT GEPLANT (Entscheidung Dominik 2026-08-21: kein Hosting)
Kein gehosteter Relay-Dienst. Erreichbarkeit von unterwegs = Tailscale-Adresse + TLS + Token
(siehe Loslegen). Auf der Website nicht als „Als Nächstes" führen.

## App / iOS — verifiziert (branch feat/english-localization)

### Hub — HEUTE
Aktueller Code (`AppModel.swift:27`, `HunchHubView.swift`) hat **7 Kacheln**: brain, maschinen,
kanaele, skills, faeden, **sitzung**, nodes.
**Diskrepanz/Blocker:** Die Produktvorgabe sagt, „Sitzung" soll NICHT mehr als aktueller Hub
gezeigt werden — der Code auf diesem Branch enthält die Kachel aber noch. Auf der Website wird
der Hub mit den **6** vom Besitzer bestimmten Punkten beschrieben (brain, maschinen, kanäle,
skills & mcps, fäden, nodes). Wenn Sitzung wirklich raus soll, muss der App-Code angepasst
werden — offener Punkt, im Delivery gemeldet.

### Dynamic Island / Work Live Activity — HEUTE
`WorkActivityAttributes.swift` Phase-Enum: **denkt, arbeitet, wartet, fertig, gescheitert**.
`.wartet` = „Freigabe erforderlich" (einzige nutzergerichtete, farbig hervorgehoben; kein
separater freigabe-Case). Zeigt Fortschrittsbalken, selbstlaufende Laufzeituhr (`Text timerInterval`),
Deep-Link `pocket://chat`. Zweite (Voice) Live Activity existiert ebenfalls.
Quelle: `HunchWidgets/WorkLiveActivity.swift`, `AI/WorkLiveActivityController.swift`.

### Voice — HEUTE (ehrlich)
On-Device-Sprache (`VoiceEngine.swift`, `AVAudioSession .playAndRecord/.voiceChat`), Vordergrund-
Modus im Chat. **Kein `UIBackgroundModes` in Info.plist** → die App kann NICHT spontan im
Hintergrund eine Unterhaltung starten. Hintergrund-Signale kommen per APNs-Push, nicht per Audio.
So auf der Website darstellen. Quelle: `Info.plist`, `VoiceEngine.swift`, `PushRegistrar`.

### Identität / Secure Enclave — HEUTE
EC-P-256-Schlüssel in der Secure Enclave (`kSecAttrTokenIDSecureEnclave`), biometrisch
geschützt, nicht exportierbar, kein Backup. Nur Public-Key exportiert. **HID** = SHA-256-
Fingerprint des Public-Keys als „HID 0000 0000 0000 0000". Challenge/Signatur beim Handshake.
Vor Einrichtung: Platzhalter „HID · XXXX XXXX", Simulator nutzt Ersatz-Identität (ehrlicher Fake).
Quelle: `AI/OwnerIdentity.swift`, `Connection/IntentionalAgentClient.swift:610`.
**Alte Fallback-HID „6699 3937" nicht mehr verwenden** — die neue Karte leitet aus dem Namen ab.

### App-Fähigkeiten — Status
HEUTE (lokal, ohne Runtime seedbar): Brain (Erinnerungen/Aufgaben/Ziele/Gespräche, SQLite+FTS5),
deterministische Predictions+Topics+Momentum (`BrainEngine`), lokale Nudges, Audit-Trail,
Token-Budget (CostGovernor), Secure-Enclave-Identität, Work-Live-Activity, Voice (Vordergrund).
HEUTE, aber runtime-abhängig (holen live vom `IntentionalAgentClient`): Fäden, Nodes/Maschinen,
Skills & MCPs mit Risiko, Sitzung/Vorhersage, Kanäle-Status, App-Nudge-Banner.
EXPERIMENTELL/PLANNED: Pattern-of-Life, Wissensgraph, Rewind/Screen-Kontext-Sensoren
(MCP-Tool-Definitionen `search_screen`/`get_screen_activity` existieren, aber „noch ohne Erfassung"),
Transcript-Import extern, **strukturierte Arbeitspräferenzen mit Scopes** (heute nur flaches
`UserIdentity.preferences: [String]`, kein Scope-Konzept — global/projekt/faden = Zielbild).
Szene-Sensoren minimal: app_state + aktueller Screen (bewusst kleiner erster Umfang).

### StoreKit / Paywall — EXISTIERT NICHT
Kein StoreKit/Paywall/IAP im aktuellen Branch. „Subscription"-Treffer betreffen OAuth-Login
gegen ein bestehendes ChatGPT/Claude-Abo als Alternative zum API-Key, keine App-Store-Monetarisierung.

### Screenshot-Fixtures — NEU implementiert
`-uitest-marketing-fixtures` seedet lokal reproduzierbare, anonymisierte Demo-Daten (Brain,
Identität, Audit, Budget). Runtime-abhängige Screens (Fäden/Nodes/Skills/Sitzung/Kanäle) brauchen
einen Fixture-Pfad im `IntentionalAgentClient` — siehe Delivery, welche Screens echt gefüllt sind
und welche als gekennzeichnetes Konzept dargestellt werden.
