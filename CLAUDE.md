# Gästpuls – Projektbrief (källa till sanning)

> Detta dokument är projektets "source of truth". Det används på två ställen:
> 1. Som **instruktioner i ett Claude Project** (klistras in i projektets instruktionsfält).
> 2. Som **CLAUDE.md i repot** så att Claude Code alltid har rätt kontext.
> Uppdatera detta dokument när beslut ändras – inte enskilda chattar.

---

## 1. Varför detta projekt finns

Carl intervjuar för en **Tech Lead-roll på Stockholm Krogbolag** (restaurangkoncern bakom bl.a. Tennstopet, Tennstopet Grill, Kommendören, Tako, Kapten Jack och boknings-/betalappen **Maîtres**). Rekryteraren har indikerat att bolaget **inte har någon in-house** som driver tech/AI idag, att appen underhålls av en **extern konsultbyrå**, och att fokus ligger på att **få den interna organisationen att jobba smartare med AI och automation**.

Syftet med detta projekt är **inte** att bygga en färdig produkt. Det är att, på några dagar och med små resurser, producera en **liten, körbar demo** som bevisar:

- att Carl går från **affärsproblem → teknisk lösning → deployad produkt** snabbt och pragmatiskt,
- att han förstår **deras** verksamhet (krog + Maîtres), inte ett generiskt portfolio-case,
- att han tänker som en **Tech Lead**: omdöme kring data, kostnad, GDPR, och nästa steg.

**Demon är ~50 % produkt, 50 % berättelse.** Koden ska fungera live, men poängen är hur Carl ramar in värdet i intervjun.

## 2. Vad vi bygger: "Gästpuls"

Ett **internt chefsverktyg** som tar gästfeedback och gör om den till **konkret handling per restaurang**. Vinkeln som gör det vasst: Maîtres samlar **redan** in betyg och gästsignaler – det bolaget saknar är ett sätt att omvandla den datan till veckovisa, prioriterade åtgärder för krogcheferna. Det är där Gästpuls kommer in.

**Kärnflöde:** omdömen in → AI kategoriserar (sentiment, tema, kort summering, **föreslagen åtgärd**) → dashboard visar läget per krog → AI genererar en veckorapport till ledningen.

## 3. Hårda avgränsningar (läs detta innan du föreslår något)

- **Endast syntetisk data.** Vi scrapar INTE TripAdvisor/Google. Skäl: (1) bryter mot deras användarvillkor, (2) tekniskt sköra scrapers äter upp veckan, (3) viktigast: man söker en ledarroll och ska sätta standarden – en demo byggd på villkorsbrott skickar fel signal. Vi genererar realistisk svensk data med riktiga restaurangnamn. "Så här kopplar vi mot Maîtres riktiga betygsdata och officiella API:er i produktion" är en **talking point**, inte något vi bygger nu.
- **En tunn vertikal skiva, inte 7 faser.** Hellre något litet som är helt klart och snyggt än mycket som är halvfärdigt.
- **Ingen auth, ingen multi-tenant, ingen RAG-infra** i grundscopet. Single-purpose demo.
- **Undvik överengineering.** Inga köer, ingen microservice-arkitektur, ingen egen VPS. Vercel + Supabase räcker.
- AI-analysen **förberäknas** på seed-datan och sparas i databasen, så demon är blixtsnabb. Vi lämnar **en** live-knapp (analysera nytt omdöme / generera veckorapport) så de ser att det är riktig AI, inte attrapp.

## 3b. Datakvalitetsprinciper

Den syntetiska datan ska kännas operativt trovärdig för någon som arbetar med dessa restauranger dagligen. Det innebär:

- **Varje restaurang har en distinkt profil.** En kämpar med ett specifikt problem (t.ex. väntetider, pris), en annan visar tydlig uppåtgång. Ingen restaurang är "genomsnittlig på allt".
- **Realistisk betygsfördelning.** Enstaka 2:or och 3:or mitt i perioder av höga betyg – inte en jämn kurva. Snittbetyg på 3.8–4.3 beroende på restaurang.
- **Specifika, agerbara kommentarer.** Inte "maten var god" utan "Pulled pork-burgaren på Captain Jack var torr och brödet smulade sönder – tre gäster V23 nämner samma rätt". Det är den nivån som gör att krogchefen kan agera direkt.
- **Svenska kommentarer** med naturlig variation i ton och längd.

## 4. Teknikstack

| Lager | Val | Varför |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript | Modernt, snabbt, deployar till Vercel direkt |
| UI | Tailwind + shadcn/ui | Snabb, snygg, konsekvent design utan egen designtid |
| Databas | Supabase (Postgres) | Hostad Postgres + enkel klient, noll infra-strul |
| AI | Anthropic API (Claude) | Sentiment/tema/åtgärd + veckorapport. Bonus: bolaget är AI-fokuserat och Carl visar att han bygger med Claude/Claude Code |
| Hosting | Vercel (live URL) | Publik domän de kan surfa in på under intervjun |
| Automation (stretch) | n8n Cloud | Ett veckoflöde som skickar rapporten – visar automationsförmågan |

Carls egen styrka ligger i **Python, data, integrationer och pipelines** – inte frontend. Det är okej att frontend är Claude Code-assisterad; var ärlig med det och led samtalet mot den riktiga edgen (data, integration, drift) i intervjun.

## 5. Scope för veckan

**Grund (måste finnas):**
1. **Översikt** – alla krogar: snittbetyg, antal omdömen, trendpil.
2. **Per restaurang** – omdömeslista där varje omdöme redan är AI-kategoriserat (sentiment, tema, summering, föreslagen åtgärd).
3. **Insikter** – topp-klagomål, topp-beröm, sentiment över tid, jämförelse mellan krogar.
4. **AI-veckorapport** – knapp som genererar en ledningssammanfattning per krog/koncern.

**Stretch (om tid finns):**
5. "Fråga datan"-ruta (enkel, ingen vektor-DB – skicka aggregerad data till Claude).
6. n8n-flöde som skickar veckorapporten via mail/Slack varje måndag.

## 6. Dataschema (Supabase)

- `restaurants` – id, namn, område, ev. logotyp/färg.
- `reviews` – id, restaurant_id, betyg (1–5), text, källa, datum.
- `review_analysis` – review_id, sentiment (positive/neutral/negative), category (service/food/waiting_time/atmosphere/price/booking/other), summary, suggested_action.
- `weekly_summaries` – id, restaurant_id (nullable för koncern), vecka, sammanfattning, skapad.

## 7. Demo-dagens talking points (förbered dessa)

- Vad som är mockat vs. riktigt, och **varför** vi valde syntetisk data (omdömessvaret ovan).
- Hur det kopplas till **Maîtres riktiga betygsdata** och officiella API:er i produktion.
- **Kostnad** per AI-anrop och hur man håller den nere (förberäkning, batching, billigare modell för triage).
- **GDPR/dataintegritet** vid gästdata mot LLM – vad som kan köras lokalt/anonymiseras.
- **Nästa steg om de anställde dig imorgon**: vilka 2–3 interna processer du skulle AI-stötta först.

## 8. Hur Claude Code ska jobba (arbetssätt)

Claude Code agerar som en **senior men pedagogisk** kodpartner. För varje steg:
1. Förklara målet.
2. Förklara den tekniska approachen kort.
3. Gör **små** ändringar.
4. Säg vilka filer som ändrats.
5. Hjälp Carl köra och testa resultatet.
6. Undvik stora rewrites; bygg inkrementellt.
7. Hjälp Carl **förstå** koden, inte bara generera den.

## 9. Status och plan

- **Dag 1–3: klart och presenterat.** Grundfunktionaliteten (översikt, per-restaurang-vy, insikter, AI-veckorapport) är byggd, deployad och demad.
- **Fas 2 (nu): UI-polish enligt sektion 10** – design system + inkrementell komponent-refaktorering för att höja den visuella kvaliteten till "färdig produkt"-nivå.
- **Borttaget ur scopet:** de ursprungliga dag 4-stretchpunkterna (fråga datan, n8n) är inte längre aktuella.

## 10. UI-arbetssätt och skills (Fas 2: polish)

Funktionaliteten (dag 1–3) är klar och demad. Målet framåt är att höja den visuella kvaliteten till "färdig produkt"-nivå. Två design-skills används med **OLIKA roller** – de ska inte konkurrera:

- **ui-ux-pro-max** (`.claude/skills/ui-ux-pro-max/`): körs **EN gång** för att generera ett design system anpassat för en intern B2B analytics-dashboard. Resultatet persisteras till `design-system/gästpuls/MASTER.md` = källa till sanning för alla visuella beslut (färg, typografi, stil).
- **frontend-design** (inbyggd): används **löpande** vid varje komponentändring för hantverket – spacing, hierarki, states, tillgänglighet.

**Ordning:** läs `design-system/gästpuls/MASTER.md` först (tokens vinner), läs sedan frontend-design för utförandet. Generera **ALDRIG** om design-systemet mitt i arbetet – justera `MASTER.md` medvetet om något ska ändras.

**Stack-tvång:** all UI är Next.js (App Router) + TypeScript + 
Tailwind v4 + shadcn/ui. Skillens default till HTML+Tailwind 
gäller **INTE** här.

**Visuell riktning:** operativt chefsverktyg, inte konsument-landing. Lugnt, datatätt, förtroendeingivande (tänk Linear / Vercel-dashboard). Undvik: AI-lila/rosa gradienter, neon, tunga animationer, emojis som ikoner.

**Arbetssätt:** applicera design-systemet som en **INKREMENTELL refaktorering** av befintliga komponenter – inga stora rewrites (se sektion 8). En vy/komponent åt gången, visa planen innan ändring.

**Engångskommando för att generera design-systemet:**

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py \
  "internal B2B analytics dashboard for a restaurant group, guest feedback and operations" \
  --design-system --persist -p "Gästpuls"
```
