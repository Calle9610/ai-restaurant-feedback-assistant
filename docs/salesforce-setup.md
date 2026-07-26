# Salesforce setup

Reproducible steps for standing up the Salesforce Developer Edition org this
project's agent backend (`agent/tools/create_case.py`,
`agent/salesforce_client.py`) integrates with. See `ADR-0003` for why the
integration is a direct REST call rather than an Agentforce action, and for
the dedup design this setup enables.

## 1. Get a Developer Edition org

Sign up for a free org at
[developer.salesforce.com/signup](https://developer.salesforce.com/signup) —
no credit card, no time limit.

**Domain gotcha:** once logged in, the address bar cycles through several
`*.salesforce.com` domains that look interchangeable but aren't:

- `*.lightning.force.com` — the Lightning UI you click around in. Not an API
  host.
- `*.my.salesforce-setup.com` — shown while inside Setup pages. Also not the
  API host.
- `*.my.salesforce.com` — the actual instance/API base URL. **This is the one
  that goes in `SF_INSTANCE_URL`.**

It's easy to copy whichever domain happens to be in the address bar at the
time — if OAuth or API calls fail with a generic connection/redirect error,
check this first before assuming a credentials problem.

## 2. Connected / External Client App (Client Credentials Flow)

Setup → App Manager (or External Client Apps, depending on org version —
Salesforce has been migrating "Connected Apps" to "External Client Apps";
either surface works) → New.

- **Enable OAuth Settings**: on.
- **Callback URL**: any dummy HTTPS value (e.g. `https://localhost/callback`)
  — required by the form even though the Client Credentials flow never
  redirects a browser here.
- **OAuth Scopes**: `api` only. No need for anything broader.
- **Enable Client Credentials Flow**: this has to be turned on in **two**
  separate places, not one:
  1. On the app's own OAuth policy.
  2. As part of that same policy, a **Run As** user must be assigned — the
     user whose permissions the flow authenticates as for every request.

  **This is the most common misstep.** Enabling the flow in only one of the
  two spots, or leaving Run As unset, produces an auth failure with an error
  that doesn't clearly say "you forgot Run As" — so if `SalesforceAuthError`
  comes back on a fresh setup, check both settings before anything else.

- **Client ID / Client Secret**: found afterward under the app's "Manage
  Consumer Details" — these map to `SF_CLIENT_ID` / `SF_CLIENT_SECRET`.

**Propagation delay:** changes to a Connected/External Client App (creating
it, editing scopes, toggling Client Credentials Flow) can take **up to ~10
minutes** to take effect. An auth failure immediately after setup or a
config change is often just this delay, not a misconfiguration — wait and
retry before digging further.

## 3. Custom field on Case: `Gastpuls_Review_Id__c`

Setup → Object Manager → Case → Fields & Relationships → New.

- **Data Type:** Text, length 50.
- **External ID:** checked.
- **Unique:** checked.

**Why:** this field holds the review's UUID and is what `create_case` upserts
against (`PATCH /sobjects/Case/Gastpuls_Review_Id__c/{review_id}`) instead of
querying for an existing Case by Subject first. The Subject-based approach
this replaced had a real bug — two different reviews for the same restaurant
and rating produced the same Subject and silently collapsed into one Case.
The external ID is the actual unique key. See `ADR-0003`'s amendments for the
full incident.

Creating the field is not enough on its own — two more steps are required,
or the upsert fails in a way that doesn't obviously point at permissions:

- **Field-Level Security:** the field must be visible (and, since
  `create_case` writes to it, editable) on:
  - the profile you use to inspect Cases in the UI (typically System
    Administrator), and
  - the profile assigned to the **Run As** user from step 2 — the identity
    the API calls actually authenticate as. If that profile can't edit the
    field, the upsert fails with a Salesforce error that does not name
    field-level security as the cause, which makes it look like a different
    problem entirely.
- **Page Layout:** add the field to the Case page layout used by those same
  profiles. Without this, the field is invisible in the UI (though still
  reachable via the API) — worth doing anyway so the field is visible for a
  demo walkthrough.

## 4. Environment variables

Set these in `.env.local` (never committed — see `.env.local.example`):

| Variable | Where it comes from |
|---|---|
| `SF_INSTANCE_URL` | The `*.my.salesforce.com` domain from step 1 — not the Lightning or Setup domain. |
| `SF_CLIENT_ID` | "Manage Consumer Details" on the app from step 2. |
| `SF_CLIENT_SECRET` | Same place as the Client ID. |

None of these are required in CI: `agent/salesforce_client.py` is fully
mocked in `tests/test_salesforce_client.py` and `tests/test_create_case.py`.
