# Next session: fetchwright after 0.2.0 (evals, 0.2.1)

Written 2026-10-15 (night), updated 2026-10-16 after the 0.2.0 release. Run from `D:\m4bwa\Claude\Projects\Ai`. The repository is `Ai\fetchwright` (public, m4bwav/fetchwright, branch main). everscout is `Ai\everscout`; its main clone holds another session's uncommitted edits, so work there in a worktree off origin/main (`Ai\everscout-wt-urlctx` exists).

## Where things stand

- fetchwright 0.2.0 is released (tag v0.2.0, 2026-10-16: a 429 on one model's quota moves to the next model) and its wiki is live and updated for 0.2.0 (ai-docs/notes/2026-10-15-github-wiki.md). It holds two skills (the reader and a setup advisor), the stdlib CLI `skills/fetchwright/scripts/fetchwright.py`, 39 offline tests, a live smoke test, a size budget (all green) and CI.
- Installed as fetchwright@mark-local 0.2.0 (user scope) from `Ai\.claude-plugin\marketplace.json`; CI green on all seven jobs for 0.2.0.
- `GEMINI_API_KEY` is set at user level and works. On 2026-10-15 `gemini-3.8-flash` answered plain calls but 503'd or dropped on URL context; `gemini-3.5-flash-lite` read everything.
- everscout 0.5.0 uses this CLI as its opt-in Reddit thread reader and finds the installed plugin (Mark's config no longer sets `fetchwright.cli`). Free tier: `gemini-3.8-flash` 20 requests a day; Mark's config runs `gemini-3.5-flash-lite` first.

## Read first

1. `fetchwright/ai-docs/HANDOFF.md`, then the decision and solution entries it links.
2. `fetchwright/skills/fetchwright/SKILL.md` and `references/route.md`.
3. `fetchwright/AGENTS.md`, the repository rules: never Google Search; the key never printed; no real responses in tests.

## The next steps and their limits

1. Run the eval suite: `claude plugin eval . --tag trigger` (native Windows), and the `live` action cases where `GEMINI_API_KEY` reaches the harness. Earlier runs of this harness used WSL2 for Bash cases (readwright's LEARNINGS L-002, and its solution on running the suite on Windows). Record each run as `T-` in each skill's TESTS.md and update `evergreen.json` `tests`. A failure goes to evergreen-tune.
2. 0.2.1: stop cutting `--json` output at `--max-chars` (a long thread prints broken JSON today), with a test; update the wiki in wikiwright's Update mode (the note lists the pages that name the version). A release needs Mark's go-ahead.
3. everscout's own work (its discovery plan) has its own prompt: everscout's `ai-docs/next-session-prompt.md`. Take any CLI change it asks of fetchwright here.
4. Re-test `gemini-3.8-flash` on URL context once Google's load settles. Note the result in RESEARCH.md as an `R-` finding.

## Rules

- Commit with `156112+m4bwav@users.noreply.github.com`. No AI attribution anywhere.
- Document as you go: the ai-docs log and HANDOFF, each skill's CHANGELOG, LEARNINGS and TESTS. Kill processes by PID only.
- No README or doc may call the route "legal". State what the terms say, with the date read, and what is untested.
- Merge your own PRs once checks pass, unless the change is a release or publish workflow or a public API. Tagging, releases and publishing need Mark's go-ahead. Batch what needs his hands into one message.

## When to stop and ask

- When the key stops working.
- If Gemini starts returning text from deleted or removed posts.
- If requests fail with refusals or 429s: record it and stop.
- Before any release or tag.

When you stop, rewrite this file for the session after you: what to read first, the next step and its limits, the rules, when to stop and ask. Its last paragraph must give that session this same instruction.
