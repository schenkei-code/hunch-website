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

### Pattern-of-Life / Wissensgraph — EXPERIMENTELL / ALS NÄCHSTES
Kein Graph im Code. Vorhanden sind Stundenprofil + Markov-Übergangstabellen (als `notes`
gecacht). Das ist statistische Mustererkennung, kein Wissensgraph. Nicht als fertig zeigen.

### Werkzeuge — HEUTE (vier Herkünfte, ein Verzeichnis)
- **Eingebaut:** `search_memory`, `remember`, `list_tasks`, `add_task`, `run_command`,
  `http_get` (+ bedingte Bündel: Chat-, Reach-, Browser-Tools). `tools/builtin.py`
- **Skills:** `SKILL.md` (Prosa fürs Modell) + Python `run(arguments)`. `tools/skills.py`
- **MCP:** fremde Server aus `mcp_config.json`, dynamisch. `tools/mcp_client.py`
- **REST:** Connectoren aus `connectors.json`, ohne Code. `register_rest_connector`
- **Externe Agent-Harnesses:** eingebaut **codex, claude, gemini, aider**; eigene via
  `~/.hunch/harnesses.json`. Ein Tool `run_agent`, immer kritisch. `harness.py`

### Gelernte Skills — HEUTE (mit Grenze)
Nach ≥3 identischen Erfolgen schreibt die Runtime `auto_<tool>.SKILL.md` (sichtbar/editierbar).
Kein autonomes Training, keine Selbstumprogrammierung. `executive._maybe_learn_skill`.

### Provider — HEUTE (Observer und Executive unabhängig wählbar)
Cloud: `claude, openai, gemini, kimi, deepseek, qwen, mistral, grok, groq`.
Gerät: `appleLocal` (nur On-Device). Lokal: `ollama, lmstudio, llamacpp`.
CLI: `claude-cli, codex-cli, gemini-cli`. Fallbacks: `cli:<cmd>`, `custom:<name>` +
`HUNCH_*_BASE_URL` (jeder OpenAI-kompatible Endpoint). `providers.py`, `test_providers.py`.
Breitere Harness-/Adapter-Provider (OpenRouter, Together, Fireworks, Cerebras, Perplexity,
Bedrock …): nur zeigen, was die eingesetzte Runtime/Surface tatsächlich lädt — sonst ALS NÄCHSTES.

### Gedächtnis / Brain — HEUTE
Schema identisch zur App (`memories`, `action_items`). `POST /brain/sync` beidseitig, Cursor
aus Zeitstempel+ID; Erinnerungen wachsen nur, Aufgaben jüngster Stand. FTS5-Suche.
MCP-Server-Modus bietet `search_memory, remember, list_tasks, add_task, recent_context`
(bewusst kein `run_command`/`run_agent`). `memory.py`, `mcp_server.py`, `test_brain_shared.py`.

### Memory-Scopes (global / projekt / faden) — ALS NÄCHSTES / VISION
**Nicht implementiert.** Erinnerungen tragen `category` und `conversation_id`, keinen Scope.
Die strukturierte global/projekt/faden-Architektur ist Zielbild — auf der Website als
Roadmap/Zielbild kennzeichnen, nicht als ausgeliefert.

### Autorität / Sicherheit — HEUTE (Kette, kein Einzelschalter)
- Secure-Enclave-Besitzeridentität: Runtime hält nur den P-256-Public-Key, Challenge/Verify
  (ECDSA), 24h-Session. `ausweis.py`
- Risikoklassen, Governor, Budgets, Circuit-Breaker, Prüfer/Zweitprüfung
- Freigabe mit Vorschau (Werkzeug/Argumente/Ziel/Risiko/Begründung), persistent
- Audit (append-only), Gastisolation (`besitzer`/`frei`/`gast`), Einlass-Codes (Einmal, 15 min)
- **Weniger strenger Modus vor der Einrichtung:** ohne enrollten Besitzer gibt `darf_alles()`
  True zurück — bewusst (`ausweis.py:216`). Die kryptografische Sperre ist NICHT automatisch
  aktiv, bevor die Besitzeridentität eingerichtet ist. Ehrlich so dokumentieren.
- Noch nicht vollständig (ALS NÄCHSTES): fein abgestuftes Vertrauen pro Gerät/Aktion,
  vollständiges Undo, universell sichtbare Begründung vor JEDER Aktion, geräteübergreifende
  Authority-Oberfläche.

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
status: `/status`, `/v1/web/login|profile`
stream/ws: `WS /ws`, `WS /v1/ws`, `GET /v1/stream` (SSE-Fallback)
web: `GET /`, `GET /chat`
MCP: kein HTTP — nur stdio (`python -m hunch_runtime.mcp_server`).
Keine erfundenen Endpoints auf der Website oder in der Doku.

---

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
