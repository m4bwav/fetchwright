# Gemini API facts for setup advice

Fetched from Google's pages on 2026-10-15 unless a line says otherwise. Each line names its source page and the "last updated" date that page showed. Prices, limits and model names move monthly: re-check before quoting (evergreen `verify_at_use`).

## Keys

Source: ai.google.dev/gemini-api/docs/api-key (updated 2026-10-06).

- Made at aistudio.google.com/apikey. Every key belongs to a Google Cloud project. A new user gets a default project; an existing Cloud user may need to import a project first.
- New keys are "auth keys": bound to a service account, restricted to the Gemini API by default, with fast leaked-key enforcement. "The Gemini API rejects requests from unrestricted standard keys." To fix an old key, choose Add restrictions, then "Restrict to Gemini API only".
- From 2026-05-07 the API blocks unrestricted keys that sat unused for a long time.
- Google's advice: treat the key like a password, never commit it, never put it in a web or mobile client, read it from an environment variable. The SDKs read `GEMINI_API_KEY` or `GOOGLE_API_KEY`; if both are set, `GOOGLE_API_KEY` wins. fetchwright prefers `GEMINI_API_KEY`.

## Tiers and billing

Sources: ai.google.dev/gemini-api/docs/rate-limits (updated 2026-10-15), ai.google.dev/gemini-api/docs/billing (updated 2026-09-28).

| tier | how you qualify | monthly cap | spend limit |
|---|---|---|---|
| Free | an active project | none | none |
| Tier 1 | a linked, active billing account | $250 | $10 per 10 minutes |
| Tier 2 | $100 paid and 3 days | $2,000 | $50 per 10 minutes |
| Tier 3 | $1,000 paid and 30 days | $20,000 to $100,000+ | $200 per 10 minutes |

- Upgrades happen on their own. Prepay starts at $5; an empty balance gives HTTP 402. The $300 Cloud free-trial credit does not apply. Unlinking billing returns the project to free.
- Limits are per project, not per key. Requests a day reset at midnight Pacific time. Preview models get tighter limits. Per-model free-tier numbers are not published on the page: "View your active rate limits in AI Studio". A forum post of 2026-09-03 (not Google staff) claimed 20 a day for 3.8 Flash and 500 a day for 3.5 Flash-Lite on the free tier: unverified.

## Prices per million tokens (paid tier)

Source: ai.google.dev/gemini-api/docs/pricing (updated 2026-10-15). Free tier: free of charge for both models.

| model | input | output (with thinking) |
|---|---|---|
| gemini-3.8-flash | $0.75 to 2026-12-31, then $1.50 | $3.75, then $7.50 from 2027-01-01 |
| gemini-3.5-flash-lite | $0.30 | $2.50 |

URL context: "Charged as input tokens per model pricing"; no per-tool charge. Example: a 7,700-token thread page plus 4,200 output tokens on flash-lite is about $0.013.

## Data use, age, regions

Source: ai.google.dev/gemini-api/terms ("Effective March 23, 2026", page updated 2026-04-28).

- Unpaid services: Google uses the content you submit and the responses it generates to provide and improve its products (the page's sentence begins "Google uses the content you submit to the Services and any generated responses to provide, improve"); "human reviewers may read, annotate, and process your API input and output"; "Do not submit sensitive, confidential, or personal information to the Unpaid Services."
- Paid services: Google does not use prompts or responses to improve products; it logs them for a limited time to detect abuse.
- "You must be 18 years of age or older to use the APIs."
- "You may use only Paid Services when making API Clients available to users in the European Economic Area", and the same for Switzerland and the UK. Those regions are on the supported list for using the API yourself.
- Interactions API (docs updated 2026-10-15): stored by default, 1 day on free and 55 days on paid; `store: false` turns it off. fetchwright sends `store: false`.

## Errors

Source: ai.google.dev/gemini-api/docs/api-errors (updated 2026-09-20). 429 codes: `rate_limit_exceeded` (per minute), `quota_exceeded` (daily), `too_many_requests`; spend limits also return 429. 503 `service_unavailable`: retry later. Do not retry 400, 402 or 403. 404 `model_not_found`: use another model.

## Models

Sources: ai.google.dev/gemini-api/docs/models (updated 2026-10-13), /deprecations (updated 2026-10-12). Stable: gemini-3.8-flash (2026-09-02), gemini-3.6-flash, gemini-3.5-flash-lite (2026-07-21), gemini-3.1-flash-lite (earliest shutdown 2027-05-07). `gemini-3.7-flash` routes to 3.8. The 2.5 models are open only to past users (404 for new keys, seen 2026-10-15). URL context works on 3.8 Flash, 3.6 Flash, 3.5 Flash-Lite, 3.1 Flash-Lite and others.

## Troubleshooting a new key

Seen 2026-10-15: right after a key was made, calls answered 403 `SERVICE_DISABLED` ("has not been used in project ... or it is disabled") or "The caller does not have permission", flipping between calls for some minutes, then worked. If it lasts: check in AI Studio which project the key belongs to, check the key is restricted to the Gemini API, or make a new key in a project AI Studio creates. A model answering 503 "high demand" on every call (gemini-3.8-flash most of that day) is Google's load, not the key.
