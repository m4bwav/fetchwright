# Learnings: fetchwright-setup

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); changes in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md.

## Active

### L-001 · 2026-10-15 · `setx-key-invisible-to-running-shell`: look in the user registry before saying there is no key
- Trigger: 2026-10-15, everscout Stage 0: a key set with `setx` was missing from the environment of an editor session started earlier, until the editor restarted.
- Hypothesis: Windows hands environment changes only to processes started afterwards.
- Rule: `fetchwright.py check` reads `HKCU\Environment` when the variable is missing and says so; tell the user a restart makes it visible everywhere.
- Evidence: C-20261015-1
- Scope: env:windows
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-15
