# Learnings: fetchwright

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md. Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first, by meaning: add / update / retire / none. Trigger and Hypothesis are required. Promote after three confirmations; retire when harmful > helpful.

## Active

### L-001 · 2026-10-15 · `recitation-block-on-verbatim-pages`: ask pages for a digest, not a copy
- Trigger: live run, 2026-10-15: "copy every paragraph word for word" of a Wikipedia article drew HTTP 400 "Request blocked due to copyright/recitation content"; the softer first wording returned only the opening paragraphs.
- Hypothesis: Gemini's recitation filter stops long verbatim output of indexed text; short comments pass.
- Rule: pages default to a digest; `--verbatim` retries as a digest when blocked; never present a digest as quotes.
- Evidence: R-20261015-3, C-20261015-1, confirmed 2026-10-15
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-15

### L-002 · 2026-10-15 · `handles-leak-as-comment-text`: drop lone tokens before anything reaches a note
- Trigger: Stage 1, 2026-10-15: 20 of 381 comments Gemini returned were a commenter's username, mostly in a video post's thread.
- Hypothesis: the page parse sometimes takes the author line for the comment body.
- Rule: drop any comment that is one token of username shape (`[A-Za-z0-9_-]{3,24}`, optional `u/`); a lone word goes too, which costs nothing a note could use.
- Evidence: R-20261015-1, C-20261015-1
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-15

### L-003 · 2026-10-15 · `flash-overloaded-plain-calls-fine`: a model can answer `check` and still 503 on URL context
- Trigger: 2026-10-15 evening: `check` showed gemini-3.8-flash answering in 5.3 s, then three URL context reads got 503 or a dropped connection from it within minutes.
- Hypothesis: Google sheds load per request kind; tool calls are heavier.
- Rule: keep a fallback model in every read; a passing `check` does not prove reads will go through the first model.
- Evidence: T-20261015-1
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-15

### L-004 · 2026-10-16 · `free-tier-20-a-day-on-flash`: the first model's daily quota stops the whole route
- Trigger: everscout's first live run through fetchwright, 2026-10-16 01:56 UTC: HTTP 429 "Rate limit exceeded for model gemini-3.8-flash (limit: 20 requests per day on Free Tier). Please retry in 22h3m56s", after about 25 calls that day (Stage 1, tests, smoke runs, four everscout reads).
- Hypothesis: free-tier quotas are per model and per day; gemini-3.5-flash-lite has its own, larger bucket (a forum says 500, unverified). Because every read tries gemini-3.8-flash first and a 429 stops the run, its 20 a day caps the whole route.
- Rule: count calls against 20 a day while gemini-3.8-flash is first; honour the "retry in" time; whether a quota 429 on one model may move to the next model is the owner's decision (open), so until then stop as now.
- Evidence: everscout `ai-docs/research/2026-10-15-fetchwright-thread-reader-live.md`
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-16

### L-005 · 2026-10-16 · `long-thread-breaks-json`: a 183-comment thread came back unparseable
- Trigger: same run: a Reddit thread with 183 comments (plus 18 collapsed) took 79 s and returned "the model's answer was not the JSON asked for".
- Hypothesis: the answer was cut off at the output limit; unverified, since the caller kept no `unparsed` text.
- Rule: for threads over about 100 comments pass `--max-comments 100` and see if it reads; record the outcome here.
- Evidence: everscout `ai-docs/research/2026-10-15-fetchwright-thread-reader-live.md`
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-16
