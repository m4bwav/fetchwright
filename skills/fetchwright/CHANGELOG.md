# Changelog: fetchwright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261015-1 · 2026-10-15 · Created: the URL context reader and its CLI
- because: user request (a standalone public plugin that reads pages other fetchers cannot, 2026-10-15), R-20261015-1, R-20261015-2, R-20261015-3, L-001, L-002
- files: SKILL.md, references/route.md, scripts/fetchwright.py, ../../tests/test_fetchwright.py, ../../tests/smoke_live.py
- `check` and `read`; model fallback on 5xx, 404 and dropped connections; stop on 429, 401, 403, 402 and bad keys; Google Search refused in any request; `store: false`; text discarded when no retrieval succeeded; placeholders and lone handles dropped; pages as a digest by default with a retry as digest after a recitation block; the key from the environment (and the Windows user registry), never printed.
