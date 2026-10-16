# Tests: fetchwright

Test runs for [SKILL.md](SKILL.md). Cases live in `evals/evals.json` (runnable copies in the repository's root `evals/`). A failure that taught something is a lesson in [LEARNINGS.md](LEARNINGS.md); a fix it caused is logged in [CHANGELOG.md](CHANGELOG.md) with `because: T-...`; research it triggered is in [RESEARCH.md](RESEARCH.md); counts and the failing list are in `evergreen.json` under `tests`. Rules: MAINTENANCE.md (Tests).

A test passes on evidence (a tool call in the trace, a file, a marker, a log line), never on the transcript's claim that something was done.

Entry shape: `### T-YYYYMMDD-n · date · harness · env · passed/total`, then one line per failing case, then `led to:`. Newest first. Budget 150 lines.

## Runs

### T-20261015-1 · 2026-10-15 · unittest and a live run · Windows 11, Python 3.14 · 38/38
- `python tests/test_fetchwright.py`: 37 offline tests on synthetic responses in the shape the API returned that day (fallback, stops, Google Search refusal, key never printed, retrieval check, placeholder and handle drops, digest retry, output limits).
- `python tests/smoke_live.py`: one live read of a Wikipedia article, passed.
- Live by hand: `read` on a settled Reddit thread gave 47 comments with retrieval `success` for the slug URL and `error` for the bare URL, the same as Stage 1; gemini-3.8-flash answered 503 or dropped, flash-lite read it. The eval cases in `evals/` have not been run yet (they need a fresh session with the plugin installed).
- led to: L-001, L-003, C-20261015-1
