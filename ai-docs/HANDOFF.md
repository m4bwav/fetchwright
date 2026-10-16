# Handoff

<!-- Keep under 50 lines. Replace, never append. Written at the end of a work session so the next one starts without re-deriving state. -->

## Current state
- 0.2.0 released on 2026-10-16 (tag v0.2.0, GitHub Release; the quota fall-through) on the owner's go-ahead; 0.1.0 on 2026-10-15. Wiki live and updated for 0.2.0 (9 pages; [notes/2026-10-15-github-wiki.md](notes/2026-10-15-github-wiki.md) says how to update it).
- Two skills: `skills/fetchwright` (reader, CLI `scripts/fetchwright.py` with `check` and `read`) and `skills/fetchwright-setup` (key, tiers, quotas, privacy; `verify_at_use`). Both are registered with evergreen, and `evergreen.py lint` is OK on both. Installed locally as fetchwright@mark-local 0.2.0 (user scope); everscout finds it there (the owner's everscout config no longer sets `fetchwright.cli`).
- Tests: `python tests/test_fetchwright.py` (39 offline, pass), `python tests/smoke_live.py` (live, passed 2026-10-15), `python scripts/budget.py` (all green). CI runs the suite on three operating systems with Python 3.10 and 3.14, plus the budget job.
- Live on 2026-10-15:
  - `gemini-3.8-flash` answers `check` but gives 503 or drops on URL context reads; `gemini-3.5-flash-lite` read every page.
  - A settled Reddit thread gave 47 comments.
  - Wikipedia read as a digest.
- everscout (separate repo) has conduct rule 17 and a kb/platforms.md keyed-sources row for this route, merged as everscout PR #18.

## In progress
- Eval cases in `evals/` (6 trigger and decoy, 2 action) have never run. They need a fresh session with the plugin installed; the action cases need `GEMINI_API_KEY` in the eval environment.
- 0.1.1 candidate: `read --json` on stdout is cut at `--max-chars`, giving broken JSON for long threads (wiki note, inaccuracy 2). Leave JSON uncut, or say so in the README.
- everscout 0.5.0 calls this CLI (`--max-chars 0`, `--max-comments 100`) as its opt-in Reddit thread reader. Its discovery plan (everscout `ai-docs/plans/2026-10-16-reddit-discovery-after-arctic-shift.md`) caps reads at 10 a scan.

## Decisions made this session
- Standalone plugin, named fetchwright; pages default to a digest; `store: false`; one URL a request. Reasons in [decisions/2026-10-15-fetchwright-as-a-standalone-public-plugin-with-a-stdlib-cli.md](decisions/2026-10-15-fetchwright-as-a-standalone-public-plugin-with-a-stdlib-cli.md).

## Dead ends hit
- Word-for-word copies of long pages: blocked as recitation (HTTP 400). See [solutions/2026-10-15-word-for-word-page-copies-are-blocked-as-recitation-ask-for-.md](solutions/2026-10-15-word-for-word-page-copies-are-blocked-as-recitation-ask-for-.md).

## Next single action
Read [next-session-prompt.md](next-session-prompt.md) and follow it.
