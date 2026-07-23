# Gästpuls v2 – Roadmap (FDE-caset)

> Ersätter v1-roadmapen (M0–M5, Tech Lead-demon) som är **klar och arkiverad**
> i `docs/archive/ROADMAP-v1.md`.
> Skapa milstolparna nedan som *Milestones* i GitHub och varje rubrik som ett *Issue*.
> Kryssrutorna är acceptanskriterier. Varje issue = egen branch = egen PR (squash merge).

---

## M6 – Setup & kvalitetsgrund (Pass 0, ~halv dag)

**Issue: Repo-hygien och CI**
- [ ] Stäng inaktuella v1-issues (#44 n8n, #43 Fråga datan, #41 Visuell polish, #35 Analysera omdömen, m.fl.) med kommentar som pekar på PROJECT_BRIEF.md
- [ ] Verifiera att dark mode-backlog-issuet finns; skapa annars
- [ ] Lös eller nedgradera legacy-lint i `lib/data.ts` (#45) **INNAN** lint blir CI-gate — sannolik fix: `supabase gen types typescript` istället för handskrivna interfaces
- [ ] CI via GitHub Actions: lint + typecheck (+ test när ramverk finns) på varje PR
- [ ] Branch-skydd på `main` (PR krävs)
- [ ] Repo Settings → Pull Requests: avaktivera "Allow merge commits" så squash är enda merge-vägen
- [ ] `.env.example` komplett och dokumenterad; inga secrets i repo

**Issue: Dokumentationsstruktur**
- [x] Nya CLAUDE.md / PROJECT_BRIEF.md / ROADMAP.md incheckade (denna PR)
- [x] Gamla BRIEF + ROADMAP arkiverade i `docs/archive/` med arkiveringsnotis (denna PR)
- [ ] `docs/adr/` skapad med mall + ADR-0001 (synthetic data, från v1)
- [ ] Fiktiva krognamn ersätter riktiga i seed-data och UI

**Issue: Python-agentpaketet scaffoldat**
- [ ] `agent/`-paket med pytest uppsatt och ett trivialt test som går grönt i CI
- [ ] Kan läsa/skriva mot Supabase från Python

## M7 – Agent-kärnan (Pass 1–2)

**Issue: Tool-calling-loop**
- [ ] Loop byggd från grunden (Anthropic SDK): prompt → tool-val → exekvering → resultat tillbaka → tills klar
- [ ] Tool-register med JSON-scheman, en fil per tool
- [ ] ADR-0002: varför from scratch istället för ramverk

**Issue: `get_context` + `draft_response`**
- [ ] `get_context(review_id)` returnerar strukturerad kontext från Supabase
- [ ] `draft_response(...)` genererar svarsutkast + severity-klassning (strukturerad JSON, robust parsing)
- [ ] Enhetstester för båda tools (LLM-anrop mockade)
- [ ] Körbart CLI: `python -m agent.run --review-id X` ger klassning + utkast

## M8 – Salesforce-integrationen (Pass 3) ⭐ casets kärna

**Issue: Developer Edition-org + auth**
- [ ] Org skapad, connected app konfigurerad, OAuth-flöde fungerar från Python
- [ ] Credentials endast via env; dokumenterat i `.env.example`

**Issue: `create_case`-toolet**
- [ ] Skapar Case via REST API med mappade fält (text → description, severity → priority)
- [ ] Anropas endast vid negativ recension över tröskel; varje anrop loggas med beslutsunderlag
- [ ] End-to-end-test: ny recension → Case syns i Salesforce-UI:t
- [ ] ADR-0003: REST API nu, Agentforce custom action som nästa steg

## M9 – Observability & evals (Pass 4)

**Issue: Langfuse-tracing**
- [ ] Varje agent-körning ger trace: tools, latens per steg, tokenkostnad, utfall
- [ ] ADR-0004: observability-val

**Issue: Eval-set**
- [ ] 10–15 recensioner märkta med facit (severity + Case ja/nej)
- [ ] Eval-körning rapporterar success rate; körbar via pytest
- [ ] Minst ett prompt-failure dokumenterat: trace → rotorsak → fix → ny mätning

**Issue: Metrics i dashboarden**
- [ ] Ny vy/sektion: behandlade recensioner, andel Cases, snittlatens, kostnad, eval-score
- [ ] Följer design-systemet (MASTER.md)

## M10 – Story & leverans

**Issue: README + demovideo**
- [ ] README (engelska): problem, arkitekturdiagram, flödet, metrics, "next steps at a real customer"
- [ ] 3-min video: recension in → agentbeslut → Case dyker upp i Salesforce → trace i Langfuse
- [ ] Repetera demo-berättelsen mot talking points i PROJECT_BRIEF.md §6

## Out of scope (nämns i README, byggs ej)
Bemanning/leverantörsflöden, multi-agent, RAG, Snowflake-migrering, n8n-automation, dark mode (låst till light, se backlog-issue).
