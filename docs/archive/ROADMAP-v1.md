> ARKIVERAD 2026-07-23 — gällde v1 (Tech Lead-caset). Aktuell version: /PROJECT_BRIEF.md

# Gästpuls – Reviderad roadmap & backlog

> Ersätter den gamla 7-fasplanen (Foundation, Dashboard MVP, Database Layer, AI Analysis, Automation & n8n, Deployment, Knowledge Assistant/RAG, Portfolio Quality). Den planen var en kvartalsplan – detta är en **veckoplan för en demo**.
>
> **Så här använder du den:** skapa milstolparna nedan som *Milestones* i GitHub och varje punkt som ett *Issue*. Stäng eller arkivera de gamla issues som inte längre är aktuella. Kryssrutorna under varje issue är förslag på acceptanskriterier.

---

## M0 – Setup & live-skelett (Dag 1, högsta prio)

**Issue: Scaffolda Next.js + TypeScript-projekt**
- [ ] `npx create-next-app` med TypeScript + App Router
- [ ] Tailwind + shadcn/ui installerat och fungerar
- [ ] En enkel landningssida renderar

**Issue: Deploya tom app live till Vercel**
- [ ] Repo kopplat till Vercel
- [ ] Publik URL fungerar (t.ex. `gastpuls.vercel.app`)
- [ ] Auto-deploy vid push till main

**Issue: Sätt upp Supabase-projekt**
- [ ] Projekt skapat, connection string sparad i `.env.local` (ej committad)
- [ ] Supabase-klient initierad i appen
- [ ] En testtabell läses från appen

## M1 – Datalager (Dag 1–2)

**Issue: Skapa databasschema**
- [ ] Tabeller: `restaurants`, `reviews`, `review_analysis`, `weekly_summaries`
- [ ] Relationer + lämpliga index

**Issue: Bygg generator för syntetisk data**
- [ ] Riktiga krognamn (Tennstopet, Kommendören, Tako m.fl.)
- [ ] Trovärdiga svenska omdömen, realistisk betygsfördelning
- [ ] Tidsstämplar spridda över ~8 veckor (för trender)
- [ ] Seed-script som fyller databasen

## M2 – AI-analyspipeline (Dag 2)

**Issue: Analysera omdömen med Claude (förberäknat)**
- [ ] Funktion som per omdöme returnerar sentiment, category, summary, suggested_action
- [ ] Strukturerad output (JSON), robust parsing
- [ ] Batch-script som analyserar all seed-data och sparar i `review_analysis`

**Issue: En live AI-endpoint för demon**
- [ ] Endpoint "analysera nytt omdöme" som kör i realtid
- [ ] Anropas från UI:t med en knapp (bevisar att det är riktig AI)

## M3 – Dashboard (Dag 2–3)

**Issue: Översiktsvy (koncern)**
- [ ] Kort per restaurang: snittbetyg, antal omdömen, trendpil
- [ ] Sortering/enkel filtrering

**Issue: Per-restaurang-vy**
- [ ] Omdömeslista med AI-taggar (sentiment, tema, åtgärd)
- [ ] Filtrera på sentiment/tema

## M4 – Insikter & veckorapport (Dag 3)

**Issue: Insiktsvy**
- [ ] Topp-klagomål och topp-beröm
- [ ] Sentiment över tid (enkel graf)
- [ ] Jämförelse mellan krogar

**Issue: AI-genererad veckorapport**
- [ ] Knapp som genererar ledningssammanfattning (per krog + koncern)
- [ ] Sparas i `weekly_summaries` och visas i UI

## M5 – Polish & demoförberedelse (Dag 3–4)

**Issue: Visuell polish med deras varumärken**
- [ ] Konsekvent, ren design; krognamn/områden känns äkta
- [ ] Mobilvänlig nog att visa på skärm

**Issue: Demo-manus & talking points**
- [ ] Vad är mockat vs. riktigt
- [ ] Koppling till Maîtres-data + officiella API:er i produktion
- [ ] Kostnad, GDPR, och "första 2–3 interna processerna jag AI-stöttar"
- [ ] Repetera flödet 2–3 gånger

## Stretch – om tid finns (Dag 4)

**Issue: "Fråga datan"-ruta**
- [ ] Fritextfråga → skicka aggregerad data till Claude → svar
- [ ] Ingen vektor-DB; håll det enkelt

**Issue: n8n veckoautomation**
- [ ] Flöde som triggar måndagar, hämtar färsk data, genererar rapport
- [ ] Skickar via mail eller Slack/Teams
