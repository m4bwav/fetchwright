# Changelog

Plugin versions, newest first. Skill-level changes are in each skill's `CHANGELOG.md`; the session log is `ai-docs/log.md`.

## 0.2.1 · 2026-10-31

- route.md: cache each page result by URL plus prompt hash with an expiry, so a same-day re-read costs no quota (guidance; the CLI is unchanged).

## 0.2.0 · 2026-10-16

- A 429 that names one model's own quota (the free tier gives `gemini-3.8-flash` 20 requests a day) moves to the next model, which is then used for the rest of the run; the run stops with exit 3 only when every model's quota is spent, or at any other 429. 39 offline tests.

## 0.1.0 · 2026-10-15

First release. Reads public web pages that refuse scripts, Reddit threads among them, through Gemini's URL context tool.

- `fetchwright.py check`: whether a Gemini API key is set and where it was found (never the key itself), and which models answer. `--no-call` sends nothing.
- `fetchwright.py read URL ...`: a Reddit or Hacker News thread comes back as its title, post and comments, word for word, with the poster's replies marked. Any other page comes back as a faithful section-by-section digest, because Gemini blocks long word-for-word copies as recitation. `--verbatim` asks for the exact text and falls back to a digest when blocked. `--json`, `--out`, `--max-comments`, `--max-chars`, `--save-raw`.
- Models: `gemini-3.8-flash`, then `gemini-3.5-flash-lite` on a 5xx, a 404 or a dropped connection. The run stops at a 429, and at 401, 402 or 403.
- Safeguards:
  - requests carry the URL context tool only, and the code refuses Google Search;
  - text without a successful retrieval is discarded;
  - removed-comment placeholders and lone usernames are dropped;
  - `store: false`, so the exchange is not kept;
  - the key comes from the environment and is never printed.
- Skills: `fetchwright` (when and how to read, how to read the result) and `fetchwright-setup` (the key, tiers, quotas, costs and free-tier privacy, with sources dated 2026-10-15).
- 37 offline tests, a live smoke test that skips without a key, a size budget checked in CI (all green), CI on Windows, macOS and Linux with Python 3.10 and 3.14.
