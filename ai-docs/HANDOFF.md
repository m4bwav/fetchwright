# Handoff

<!-- Keep under 50 lines. Replace, never append. Written at the end of a work session so the next one starts without re-deriving state. -->

## Current state
- 0.1.0 built on 2026-10-15 and pushed to the public repo github.com/m4bwav/fetchwright (main). Not tagged or released: releases need the owner's go-ahead.
- Two skills: `skills/fetchwright` (reader, CLI `scripts/fetchwright.py` with `check` and `read`) and `skills/fetchwright-setup` (key, tiers, quotas, privacy; `verify_at_use`). Both are registered with evergreen, and `evergreen.py lint` is OK on both.
- Tests: `python tests/test_fetchwright.py` (37 offline, pass), `python tests/smoke_live.py` (live, passed 2026-10-15), `python scripts/budget.py` (all green). CI runs the suite on three operating systems with Python 3.10 and 3.14, plus the budget job.
- Live on 2026-10-15:
  - `gemini-3.8-flash` answers `check` but gives 503 or drops on URL context reads; `gemini-3.5-flash-lite` read every page.
  - A settled Reddit thread gave 47 comments.
  - Wikipedia read as a digest.
- everscout (separate repo) has conduct rule 17 and a kb/platforms.md keyed-sources row for this route, PR on branch `kb/fetchwright-route`.

## In progress
- Eval cases in `evals/` (6 trigger and decoy, 2 action) have never run. They need a fresh session with the plugin installed; the action cases need `GEMINI_API_KEY` in the eval environment.
- The wiki is enabled, but its repository does not exist until the owner creates the first page in the browser.

## Decisions made this session
- Standalone plugin, named fetchwright; pages default to a digest; `store: false`; one URL a request. Reasons in [decisions/2026-10-15-fetchwright-as-a-standalone-public-plugin-with-a-stdlib-cli.md](decisions/2026-10-15-fetchwright-as-a-standalone-public-plugin-with-a-stdlib-cli.md).

## Dead ends hit
- Word-for-word copies of long pages: blocked as recitation (HTTP 400). See [solutions/2026-10-15-word-for-word-page-copies-are-blocked-as-recitation-ask-for-.md](solutions/2026-10-15-word-for-word-page-copies-are-blocked-as-recitation-ask-for-.md).

## Next single action
Read [next-session-prompt.md](next-session-prompt.md) and follow it.
