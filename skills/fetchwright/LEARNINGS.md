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
