# Gästpuls – Projektbrief (källa till sanning för SCOPE)

> Detta dokument äger projektets **varför, vad och avgränsningar**.
> Arbetssätt och konventioner: `CLAUDE.md`. Plan och ordning: `ROADMAP.md`.
> Uppdatera detta dokument när beslut ändras – inte enskilda chattar.
>
> **Historik:** Gästpuls v1 byggdes för ett annat case (Tech Lead-demo) och är
> levererad. Den briefen är arkiverad i `docs/archive/PROJECT_BRIEF-v1.md` och
> gäller inte längre. Detta dokument definierar v2.

---

## 1. Varför detta projekt finns

Carl söker rollen **Forward Deployed Engineer på Salesforce Stockholm** (JR349196). Annonsen efterfrågar ett uppvisbart AI-case och betonar: agentiska lösningar i produktion, tool calls mot riktiga system, datapipelines, förmågan att förklara varför en prompt failade, och att utvärdera AI-output med engineering rigor.

Gästpuls v1 (analytics-dashboard med AI-kategoriserade recensioner, deployad på Vercel med applicerat design system) finns redan. **Detta projekt är v2: vi bygger den agentiska ryggraden** som gör Gästpuls till ett komplett FDE-case.

Demon ska bevisa fyra saker:

1. **Agent som agerar, inte bara svarar** – tool-calling-loop byggd från grunden, med kontrollerad action-taking mot ett externt system.
2. **Riktig Salesforce-integration** – agenten skapar Cases i en riktig Developer Edition-org. Detta är casets kärnbevis.
3. **Engineering rigor kring icke-determinism** – tracing (Langfuse), eval-set med facit, mätbar success rate, och minst ett dokumenterat prompt-failure med rotorsak och fix.
4. **End-to-end-tänk** – data in → pipeline → agentbeslut → action → observability → dashboard. Smalt men komplett.

**Demon är ~50 % produkt, 50 % berättelse.** README, ADRs och en kort demovideo är del av leveransen.

## 2. Kärnflödet (enda flödet i scope)

**Recension-till-action:**

1. En ny recension "landar" (simulerad inmatning i Supabase).
2. Agenten hämtar kontext (`get_context`): restaurang, historik, tidigare mönster.
3. Agenten bedömer sentiment + allvarsgrad och draftar ett svar (`draft_response`).
4. Vid negativ recension över tröskelvärde: agenten skapar ett Case i Salesforce (`create_case`) med recension, utkast och prioritet.
5. Hela körningen tracas i Langfuse; metrics visas i Gästpuls-dashboarden.

## 3. Hårda avgränsningar

- **Endast syntetisk data.** Ingen scraping (villkorsbrott, skört, fel signal). Datakvalitetsprinciperna från v1 gäller fortsatt: distinkta restaurangprofiler, realistisk betygsfördelning, specifika agerbara svenska kommentarer.
- **Fiktiv restaurangkoncern.** Inga riktiga restaurangers namn eller varumärken – detta är en publik portfolio. Hitta på trovärdiga svenska krognamn.
- **Ett flöde, end-to-end.** Bemanning, leverantörsbeställningar, multi-agent, RAG: uttryckligen out of scope. De nämns som "nästa steg" i README – de byggs inte.
- **Kontrollerad action-taking.** `create_case` är det enda toolet som skriver till ett externt system. Varje anrop loggas med beslutsunderlag.
- **Ingen auth, ingen multi-tenant.** Single-purpose demo.
- **Undvik överengineering.** Inga köer, inga microservices. Vercel + Supabase + ett Python-agentpaket räcker.
- **Snowflake är en talking point, inte ett krav.** Pipelinen byggs mot Supabase; i README/intervju förklaras hur samma modell flyttar till Snowflake/Databricks hos en kund. (Omprövas bara om tid finns i slutet.)
- **Dark mode är låst till light** tills brand-tokens finns (backlog-issue). Inget dark-arbete i detta scope.

## 4. Teknikstack

| Lager | Val | Varför (intervjuargument) |
|---|---|---|
| Dashboard | Next.js + TS + Tailwind + shadcn/ui (befintlig v1) | Återanvänd, redan deployad på Vercel |
| Data | Supabase (Postgres) | Enkel hostad Postgres; datamodellen är poängen, inte plattformen |
| Agent | Python, tool-calling-loop byggd från grunden (Anthropic SDK) | Visar förståelse för mekaniken – kan förklara varje steg och varje failure |
| Integration | Salesforce Developer Edition, REST API (Case-objekt) | Riktig action i riktig Salesforce-miljö = casets kärna |
| Observability | Langfuse (self-serve) | Trace per körning: tools, latens, kostnad, utfall |
| Evals | Eget eval-set (10–15 märkta recensioner) + pytest | "Engineering rigor" – mätbar träffsäkerhet, regressionsskydd |

Carls edge är **Python, data, integrationer, pipelines**. Frontend är Claude Code-assisterad – var öppen med det och styr samtalet mot agent/data/integration.

## 5. Definition of done

- [ ] Flödet körbart end-to-end: ny recension → (vid negativ) ett Case syns i Salesforce-UI:t.
- [ ] Langfuse-trace för varje körning; metrics i dashboarden (behandlade recensioner, andel Cases, latens, kostnad, eval-score).
- [ ] Eval-set kört med rapporterad success rate.
- [ ] Minst ett dokumenterat prompt-failure: trace → rotorsak → fix → förbättrad mätning.
- [ ] README på engelska med arkitekturdiagram + 3-min demovideo.
- [ ] 3–4 ADRs (synthetic data, tool-loop from scratch, Salesforce via REST, Langfuse).

## 6. Intervju-talking points (förbered)

- Varför tool-loopen är byggd från grunden och hur den fungerar steg för steg.
- Prompt-failure-berättelsen: vad hände, vad visade tracet, vad ändrades.
- Hur lösningen flyttar till en riktig kund: Snowflake/Databricks som datalager, Agentforce custom actions istället för rå REST, credentials-hantering (inkl. lärdomen från token-saneringen i detta repo).
- Kostnad per körning och hur den hålls nere (modellval för triage, batching).
- GDPR: gästdata mot LLM, anonymisering, vad som kan hållas lokalt.
- Scoping-filosofin: ett flöde production-ready > fem prototyper ("sketch to deployable in days").
- Arbetsprocessen i sig: PR-flöde, CI, ADRs, medveten skuld-hantering (issues #45, dark mode) – "så här inför man kvalitetsgrindar i ett levande repo".
