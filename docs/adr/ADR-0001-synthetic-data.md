# ADR-0001: Use synthetic data only, with a fictional restaurant group

- **Status:** Accepted
- **Date:** 2026-07-23 (decision originally made in v1; re-affirmed and extended for v2)
- **Context:** Gästpuls v2 (FDE case)

## Context

Gästpuls needs realistic guest-review data to demonstrate an agentic
review-to-action flow. Real review data could be obtained by scraping public
platforms (TripAdvisor, Google Reviews), but scraping violates those
platforms' terms of service, produces brittle tooling that consumes project
time, and would undermine the professional signal the portfolio is meant to
send. The project is public and will be reviewed by Salesforce recruiters
and engineers.

## Decision

All review, guest, and restaurant data is synthetically generated. The
restaurant group and all restaurant names are fictional (v2 extension: v1
used real restaurant names for a private demo; a public portfolio must not
carry another company's brands).

Synthetic data must remain operationally credible: each restaurant has a
distinct profile (one struggling with a specific problem, one trending up),
rating distributions are realistic (averages 3.8–4.3 with occasional low
outliers), and review comments are specific and actionable, written in
Swedish with natural variation in tone and length.

## Alternatives considered

- **Scraping public review platforms** — ToS violation, brittle, wrong
  professional signal for a portfolio.
- **Public review datasets (e.g. Yelp academic dataset)** — English-language,
  US-centric, and licensing restricts redistribution; loses the Swedish
  restaurant-operations realism that anchors the demo narrative.
- **Real data via official APIs** — the right answer in production at a real
  customer (and a deliberate interview talking point), but requires
  partnerships and consent that are out of scope for a demo.

## Consequences

Easier: full control over data shape for demo scenarios and eval sets; no
legal or privacy exposure; the "how this connects to real data in
production" story becomes an explicit interview talking point rather than a
liability.

Harder: generator code must be maintained to keep data credible; findings
in the dashboard demonstrate the mechanism, not real-world insight.

Tracked follow-up: replace v1's real restaurant names in seed data and UI
with fictional ones (ROADMAP M6, "Dokumentationsstruktur" issue).
