# CLAUDE.md – Arbetsinstruktioner för Claude Code

> Detta är **operativa instruktioner** för Claude Code i detta repo.
> För projektets *varför*, scope och arkitektur: läs `PROJECT_BRIEF.md`.
> För aktuell plan och milstolpar: läs `ROADMAP.md`.
> Vid konflikt gäller: PROJECT_BRIEF.md (scope) > ROADMAP.md (ordning) > denna fil (arbetssätt).

---

## Projektet i en mening

Gästpuls är en portfolio-demo för en Forward Deployed Engineer-ansökan: en agentisk AI-lösning som tar restaurangrecensioner → bedömer allvar → draftar svar → skapar Case i en riktig Salesforce-org, med full observability (Langfuse) och en analytics-dashboard ovanpå.

## Arbetssätt (obligatoriskt)

1. **Föreslå alltid en plan innan du ändrar kod.** Vänta på godkännande vid ändringar som rör mer än en fil.
2. **Små, inkrementella ändringar.** Inga stora rewrites. En vy/modul/tool åt gången.
3. Efter varje ändring: lista vilka filer som ändrats och hur Carl testar resultatet.
4. **Förklara resonemanget**, inte bara koden. Carl ska kunna försvara varje beslut i intervju.
5. Jobba alltid på en feature-branch, aldrig direkt mot `main`. Varje task = branch = PR. PRs mergas med **squash and merge**.
6. Kör `npm run lint` och `npm run typecheck` innan du föreslår commit.
7. Stora arkitekturbeslut dokumenteras som ADR i `docs/adr/` (kort markdown, mall finns där).

## Vad du INTE får göra

- Ändra Supabase-migrations eller databasschema utan explicit godkänd plan.
- Committa secrets. Alla nycklar går via `.env.local`; `.env.example` hålls uppdaterad.
- **Aldrig credentials i remote-URLs eller config-filer** — gh/keychain för GitHub, env-variabler för allt annat. Flagga omedelbart om du upptäcker inbäddade credentials.
- Utöka scope utöver `PROJECT_BRIEF.md` sektion "Avgränsningar". Föreslå gärna – men bygg inte oombedd.
- Generera om design-systemet (`design-system/gästpuls/MASTER.md`). Justera det medvetet vid behov.
- Använda riktiga restaurangers eller personers namn i data eller UI.
- Läsa `docs/archive/` som gällande instruktioner — det är historik från v1.

## Stack & konventioner

- **Frontend/app:** Next.js (App Router) + TypeScript + Tailwind v4 + shadcn/ui. Läs `AGENTS.md` – denna Next.js-version har breaking changes mot din träningsdata.
- **Agent-backend:** Python. Agent-loop och tools ligger i `agent/` (eget paket, testbart utan UI).
  - Tools är rena funktioner med typade signaturer + JSON-schema. En fil per tool i `agent/tools/`.
  - Affärslogik separerad från LLM-anrop – allt runt modellen ska vara deterministiskt testbart.
- **Data:** Supabase (Postgres). Endast syntetisk data.
- **Salesforce:** Developer Edition-org. Integration via REST API i `agent/tools/create_case.py`. OAuth-credentials endast via env.
- **Observability:** Langfuse wrappar agent-loopen. Evals ligger i `agent/evals/` med märkt facit-data.
- **Tester:** Vitest för TypeScript, pytest för Python. Nya tools kräver test.

## UI-arbete

- Läs `design-system/gästpuls/MASTER.md` först – tokens vinner alltid.
- Använd frontend-design-skillen för utförandet (spacing, hierarki, states, a11y).
- Visuell riktning: operativt chefsverktyg, lugnt och datatätt (Linear/Vercel-känsla). Inga AI-gradienter, neon eller emojis som ikoner.
- UI-ändringar är inkrementell refaktorering av befintliga komponenter.
- Appen är **låst till light mode** tills brand-tokens finns för dark (se issue "Dark mode"). Introducera inga dark:-varianter.

## Språk

- Kod, kommentarer, commits, ADRs: **engelska** (repot ska läsas av Salesforce-rekryterare).
- Syntetisk recensionsdata: **svenska** (realism) – men UI-copy på engelska.
