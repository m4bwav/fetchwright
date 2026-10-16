# Research: fetchwright-setup

Findings that back [SKILL.md](SKILL.md) and [references/gemini-api.md](references/gemini-api.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); lessons in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Protocol: [MAINTENANCE.md](MAINTENANCE.md).

Topic: setting up a Gemini API key for a command-line tool: AI Studio keys and their restrictions, environment variables, free and paid tiers, prices, rate limits and error codes, data use on the free tier, age and regional rules, model lifecycle. Tier `fast` with `verify_at_use` (prices, limits and terms are quoted to users). Last refresh 2026-10-15.

## Current understanding

- Keys: made in AI Studio, restricted to the Gemini API by default since the auth-key change; unrestricted standard keys are rejected. `GOOGLE_API_KEY` beats `GEMINI_API_KEY` in Google's SDKs; fetchwright prefers `GEMINI_API_KEY` (R-20261015-1).
- Tiers: free, then Tier 1 to 3 by billing and spend; prepay from $5; 402 on an empty balance. Free-tier per-model limits are shown only in AI Studio (R-20261015-1).
- Cost: URL context page tokens are billed as input; prices in the reference, with gemini-3.8-flash doubling on 2027-01-01 (R-20261015-1).
- Data: free-tier prompts and responses improve Google products and may be read by human reviewers; paid ones are not used that way. 18+. Only paid services may serve users in the EEA, Switzerland or the UK (R-20261015-1).
- A new project's key can answer 403 `SERVICE_DISABLED` for some minutes before working (R-20261015-2).

## Open questions

- Actual free-tier RPM and RPD for gemini-3.8-flash and gemini-3.5-flash-lite (a forum post claims 20 and 500 a day: unverified).
- Whether a 429 body carries RetryInfo.
- What `gemini-flash-latest` points to now.

## Search plan

Four tracks; every refresh runs at least one query on each, scoped to the time since the last refresh.

Subject:
- Re-fetch ai.google.dev/gemini-api/docs/api-key, /rate-limits, /billing, /pricing, /api-errors, /models, /deprecations and /gemini-api/terms; compare their "Last updated" dates.

Tooling:
- How other CLIs and MCP servers that wrap Gemini store and check keys (`GEMINI_API_KEY` setup guides, current year).

Practice:
- discuss.ai.google.dev threads on free-tier limits and 429s, newest first.

Testing:
- Run `fetchwright.py check` on a fresh key; confirm whether the 403-then-works pattern still happens.

## Findings

### R-20261015-1 · 2026-10-15 · Keys, tiers, prices, limits, errors, data use, regions, models
- Track: subject
- Sources: ai.google.dev/gemini-api/docs/api-key (updated 2026-10-06), /rate-limits (2026-10-15), /billing (2026-09-28), /pricing (2026-10-15), /api-errors (2026-09-20), /interactions (2026-10-15), /models (2026-10-13), /deprecations (2026-10-12), /gemini-api/terms (effective 2026-03-23, updated 2026-04-28); discuss.ai.google.dev/t/180609 (forum, unverified)
- One subagent pass, 5 searches and 18 fetches. Details as in references/gemini-api.md.
- Magnitude: 1.0 (created) · applied: C-20261015-1

### R-20261015-2 · 2026-10-15 · A new key's first minutes
- Track: testing
- Sources: the everscout Stage 1 probe note (`ai-docs/notes/2026-10-15-gemini-url-context-probe.md`, github.com/m4bwav/everscout)
- 403 `SERVICE_DISABLED` or "The caller does not have permission", flipping, for some minutes after the API was switched on; then 200. gemini-3.8-flash then answered 503 for hours: load, not the key.
- Magnitude: 0.3 · applied: C-20261015-1
