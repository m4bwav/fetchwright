# Next session: fetchwright after 0.1.0 (evals, wiki, everscout wiring)

Written 2026-10-15 (night). Run from `D:\m4bwa\Claude\Projects\Ai`. The repository is `Ai\fetchwright` (public, m4bwav/fetchwright, branch main). everscout is `Ai\everscout`; its main clone holds another session's uncommitted edits, so work there in a worktree off origin/main (`Ai\everscout-wt-urlctx` exists).

## Where things stand

- fetchwright 0.1.0 is on main, not tagged or released. It holds two skills (the reader and a setup advisor), the stdlib CLI `skills/fetchwright/scripts/fetchwright.py`, 37 offline tests, a live smoke test, a size budget (all green) and CI.
- Installed as fetchwright@mark-local from `Ai\.claude-plugin\marketplace.json`, if the install step went through; check with `claude plugin list`.
- `GEMINI_API_KEY` is set at user level and works. On 2026-10-15 `gemini-3.8-flash` answered plain calls but 503'd or dropped on URL context; `gemini-3.5-flash-lite` read everything.
- everscout: conduct rule 17 and a kb/platforms.md keyed-sources row for the route (merged or open: check `gh pr list -R m4bwav/everscout`).

## Read first

1. `fetchwright/ai-docs/HANDOFF.md`, then the decision and solution entries it links.
2. `fetchwright/skills/fetchwright/SKILL.md` and `references/route.md`.
3. `fetchwright/AGENTS.md`, the repository rules: never Google Search; the key never printed; no real responses in tests.

## The next steps and their limits

1. Run the eval suite: `claude plugin eval . --tag trigger` (native Windows), and the `live` action cases where `GEMINI_API_KEY` reaches the harness. Earlier runs of this harness used WSL2 for Bash cases (readwright's LEARNINGS L-002, and its solution on running the suite on Windows). Record each run as `T-` in each skill's TESTS.md and update `evergreen.json` `tests`. A failure goes to evergreen-tune.
2. Wiki: once Mark has created the first page (check with `git ls-remote https://github.com/m4bwav/fetchwright.wiki.git`), write it with the wikiwright skill. Until then it stays on his list.
3. everscout wiring (optional, ask Mark first): `everscout.py thread` could call `fetchwright.py read --json` as a subprocess when the user opts in (config `reddit.thread_reader: fetchwright`) and Arctic Shift has stopped. That would be a CLI change with tests, a decision record, and a minor version.
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
- Before wiring everscout to fetchwright.

When you stop, rewrite this file for the session after you: what to read first, the next step and its limits, the rules, when to stop and ask. Its last paragraph must give that session this same instruction.
