# Research: fetchwright

Findings that back [SKILL.md](SKILL.md), [references/route.md](references/route.md) and `scripts/fetchwright.py`. Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Protocol: [MAINTENANCE.md](MAINTENANCE.md).

Topic: reading public web pages that refuse ordinary fetchers through Gemini's URL context tool: the Interactions API's request and response shape, retrieval statuses, which models support the tool, recitation blocks, the Gemini API terms on URL context and Google Search grounding, and other tools agents use for hard-to-fetch pages. Tier `fast`. Last refresh 2026-10-15; next due 2026-10-29.

## Current understanding

- **URL context reads pages scripts cannot.** Reddit refuses a plain client, but URL context returns its threads from Google's index under the slug URL (`success`), while its live fetch of the bare URL gives `error`. Six of six test threads read right on 2026-10-15. A thread must be in Google's index; an 8.6 hour old one was. Confident for Reddit on that date (R-20261015-1).
- **Request shape.** `POST /v1beta/interactions` with `tools: [{"type": "url_context"}]`; the response's `steps` hold `url_context_call`, `url_context_result` (per-URL `status`), `thought` and `model_output`. The fetched page shows as `usage.total_tool_use_tokens`. The Interactions API is generally available and `generateContent` is legacy; it stores exchanges by default (1 day free, 55 days paid) and takes `store: false`. Confident (R-20261015-1, R-20261015-2).
- **Statuses.** Seen: `success`, `error`. Documented: success, error, paywall, unsafe; the lowercase Interactions strings beyond `unsafe` are not in a REST page. The CLI flags anything else (R-20261015-2).
- **Long verbatim copies are blocked.** Asking for a whole Wikipedia article word for word drew HTTP 400 "Request blocked due to copyright/recitation content"; a section-by-section digest read the whole article. Thread comments copy word for word without a block (R-20261015-3).
- **Models.** `gemini-3.8-flash` answers plain calls but was overloaded (503, or a drop at 60 s) on most URL context calls on 2026-10-15; `gemini-3.5-flash-lite` answered every time. `gemini-2.5-flash` is closed to new keys (404). Volatile (R-20261015-1, R-20261015-2).
- **Terms.** The Additional Terms (effective 2026-03-23) restrict results of Grounding with Google Search and forbid using it to find pages to crawl; no clause names URL context, and whether its output is a "Grounded Result" is not stated. The free tier lets Google use prompts and answers and lets reviewers read them. Fairly confident as of 2026-10-15; re-read each refresh (R-20261015-2).
- **Tooling.** Small URL context wrappers exist (`@taiyokimura/url-context-mcp` on npm, `dnvriend/gemini-url-context-tool`), maintenance and installs unchecked. None found checks retrieval statuses, drops handles and placeholders, or refuses Google Search (R-20261015-2).

## Open questions

- Does `gemini-3.8-flash` read URL context reliably once its load settles, and do its copies differ from flash-lite's?
- Free-tier rate limits per model: only visible in AI Studio; no 429 seen in about 25 requests over two sessions.
- Does a 429 body carry RetryInfo with a wait time?
- How fast does Google's index pick up a new Reddit thread (under an hour old: untested)?
- Do other hard sites (X, LinkedIn public posts, Cloudflare-walled pages, Discourse forums) read, and under what status?

## Search plan

Four tracks; every refresh runs at least one query on each, scoped to the time since the last refresh.

Subject:
- Re-fetch ai.google.dev/gemini-api/docs/url-context, /interactions, /api-errors and /models; compare their "Last updated" dates with RESEARCH entries.
- `"url context" OR url_context site:discuss.ai.google.dev` sorted by date; the forum's Announcements category.
- ai.google.dev/gemini-api/terms: any section naming URL context, or a change to the Grounded Results section.

Tooling:
- `registry.modelcontextprotocol.io/v0/servers?search=url-context`; GitHub `"url_context" interactions path:*.py` sorted by recent; npm `url-context`.
- Other routes for pages that refuse scripts: Jina Reader, Firecrawl, browser MCP servers. Note their terms beside their features.

Practice:
- `"url context" gemini "claude code" OR agent 2026`; simonwillison.net "url context"; hn.algolia.com "url context gemini".

Testing:
- Re-run `tests/smoke_live.py`; read one fresh Reddit thread and check every `url_context_result` is recorded; compare the answer with the live page for staleness.
- `"url_context" eval OR test site:github.com 2026`.

## Findings

### R-20261015-1 · 2026-10-15 · Stage 1: six Reddit threads read right on gemini-3.5-flash-lite
- Track: subject, testing
- Sources: live test, results in the everscout repository (`ai-docs/research/2026-10-15-gemini-url-context-reddit-test.md`, github.com/m4bwav/everscout)
- Six threads (fresh, settled, long, a year old, video, deleted post) against two independent copies: titles and bodies six of six; comments 20/21, 47/51, 89/251, 151/185, 62/174, 12/13; no comment shown invented; placeholders instead of removed text; 20 handles returned as comment text in 381 comments; 3,000 to 15,000 page tokens and 600 to 10,000 output tokens a thread. gemini-3.8-flash overloaded all session.
- Magnitude: 1.0 (the route exists) · applied: C-20261015-1

### R-20261015-2 · 2026-10-15 · Docs and terms for keys, tiers, limits, statuses, storage and models
- Track: subject, tooling
- Sources: ai.google.dev/gemini-api/docs/url-context (updated 2026-10-13), /interactions (2026-10-15), /api-errors (2026-09-20), /models (2026-10-13), /deprecations (2026-10-12), /pricing (2026-10-15), /gemini-api/terms (effective 2026-03-23, updated 2026-04-28)
- One research pass (5 searches, 18 fetches). URL context: 20 URLs and 34 MB a URL, public pages only; not paywalls, YouTube, Workspace files, video or audio, localhost; index first, then live fetch; billed as input tokens. Interactions stores by default; `store: false`. Errors: 429 codes `rate_limit_exceeded`, `quota_exceeded`, `too_many_requests`; 402 empty prepaid balance; 404 `model_not_found`. Terms as in Current understanding. Tooling baseline as above.
- Magnitude: 0.4 (store false, 402, paywall status added) · applied: C-20261015-1

### R-20261015-3 · 2026-10-15 · Word-for-word page copies are blocked as recitation
- Track: testing
- Sources: live run of `fetchwright.py read https://en.wikipedia.org/wiki/Reddit` with a word-for-word page instruction
- The first instruction got a 1,864-character excerpt of a long article; asking for every paragraph drew HTTP 400 "Request blocked due to copyright/recitation content". The digest instruction read every section (2,839 characters from 7,479 page tokens).
- Magnitude: 0.5 · applied: C-20261015-1
