# Changelog: fetchwright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261117-2 · 2026-11-17 · clip stops cleanly on a Gemini timeout
- because: an 8-minute clip span got no answer in 600 s and yt.py printed a bare traceback (youtube-mining everscout test)
- files: scripts/yt.py (clip); tests/test_yt.py; SKILL.md (YouTube videos)
- A timeout now stops with advice to ask about a span of 2 minutes or less, and the skill says so.

### C-20261117-1 · 2026-11-17 · YouTube videos through yt.py (transcript, chapters, clip)
- because: user request (YouTube mining chain); viability tests in plugin-backlog youtube-mining tests.md (research, harvest, clip all KEEP)
- files: SKILL.md (description, Step 1, YouTube videos); scripts/yt.py; tests/test_yt.py; evals trigger-5
- The description no longer rules YouTube out. yt.py reads captions, chapters and links with `&t=` citations (yt-dlp route opt-in until the owner rules), and `clip` asks Gemini about one span's screen. A 429 stops the run with advice.

### C-20261115-1 · 2026-11-15 · --json output stays valid under --max-chars (0.2.2)
- because: user request (2026-11-15): --json cut at --max-chars printed broken JSON
- files: scripts/fetchwright.py (emit, fit_json); tests/test_fetchwright.py
- With --json, the page text fields (text, body, comment text) are shortened until the object fits, and each shortened result carries "truncated": true and "chars_before_truncation". The serialized string is never cut. VERSION in the script was still 0.2.0 and now matches the plugin.

### C-20261102-1 · 2026-11-02 · point Discord to everscout's invited-bot reader
- because: user request (2026-11-02): a legal way to read Discord
- files: SKILL.md (when not to use it)
- Discord is login-walled, so URL context cannot read it; the skill now names everscout's es_discord.py route. Unreleased.

### C-20261031-1 · 2026-10-31 · cache page results by URL and prompt hash (0.2.1)
- because: R-20261031-1 (book-learnings pass)
- files: references/route.md (The request)
- A same-day re-read of one page with one prompt should come from a cache with an expiry, not a new Gemini call.

### C-20261016-1 · 2026-10-16 · a 429 on one model's quota moves to the next model
- because: L-004 (`free-tier-20-a-day-on-flash`); the owner agreed on 2026-10-16 that a quota 429 on one model may fall through to the next
- files: scripts/fetchwright.py (classify, call_models, cmd_read), SKILL.md (Rules), references/route.md (Errors), ../fetchwright-setup/SKILL.md, ../../tests/test_fetchwright.py
- A 429 whose message names a model or a daily limit is a `quota` outcome: the next model is tried and the spent one is skipped for later URLs in the run. Exit 3 when every model's quota is spent; any other 429 still stops at once.

### C-20261015-1 · 2026-10-15 · Created: the URL context reader and its CLI
- because: user request (a standalone public plugin that reads pages other fetchers cannot, 2026-10-15), R-20261015-1, R-20261015-2, R-20261015-3, L-001, L-002
- files: SKILL.md, references/route.md, scripts/fetchwright.py, ../../tests/test_fetchwright.py, ../../tests/smoke_live.py
- `check` and `read`; model fallback on 5xx, 404 and dropped connections; stop on 429, 401, 403, 402 and bad keys; Google Search refused in any request; `store: false`; text discarded when no retrieval succeeded; placeholders and lone handles dropped; pages as a digest by default with a retry as digest after a recitation block; the key from the environment (and the Windows user registry), never printed.
