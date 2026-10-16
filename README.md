# fetchwright

![A brass robot reaching through a lit library window for a single glowing page, past a locked iron gate](https://raw.githubusercontent.com/m4bwav/fetchwright/main/.github/images/banner.jpg)

An agent plugin for reading public web pages that refuse scripts. A Reddit thread answers a plain HTTP client with a block page, and some sites want a browser. fetchwright hands the URL to Gemini's URL context tool. Google reads the page from its own index or with a live fetch, and the model gives the page back as JSON. A small command-line tool checks that Google retrieved the page, drops what a note should not keep, and prints the result for the agent.

Two skills and one standard-library Python script:

- `fetchwright`: when to use the route, how to read a page or a thread, and how to read the result.
- `fetchwright-setup`: getting a Gemini API key without pasting it anywhere, and what the free and paid tiers mean for cost, limits and privacy.
- `skills/fetchwright/scripts/fetchwright.py`: the CLI. Python 3.10 or newer on Windows, macOS or Linux; nothing to install.

## Commands

```
python skills/fetchwright/scripts/fetchwright.py check
python skills/fetchwright/scripts/fetchwright.py read https://www.reddit.com/r/<sub>/comments/<id>/
python skills/fetchwright/scripts/fetchwright.py read URL --json --out thread.json
python skills/fetchwright/scripts/fetchwright.py read URL --max-comments 30
```

- `check`: is a key set, and where it was found (never the key itself), then one tiny request per model to show which answer. `--no-call` sends nothing.
- `read`: a Reddit or Hacker News thread comes back as its title, post and comments, copied word for word, with the poster's replies marked `[OP]`. Any other page comes back as a faithful section-by-section account (`style: digest`), because Gemini blocks long word-for-word copies as recitation. `--verbatim` asks for the exact text and falls back to a digest when blocked; `--thread` and `--page` override the guess. Output stops at 25,000 characters unless `--out` is given.
- Models: `gemini-3.8-flash` first, then `gemini-3.5-flash-lite` when the first is overloaded (5xx or a dropped connection) or gone (404). `--models` or `FETCHWRIGHT_MODELS` sets the list.
- Exit codes: 0 all read, 1 a page not read, 2 bad arguments, 3 rate limited (the run stops), 4 no key, a refused key or an empty prepaid balance, 5 every model unavailable.

## What the CLI enforces

- **Retrieval is checked.** Every URL's retrieval status from Google is printed. If no URL shows `success`, whatever the model wrote is discarded and the page is reported as not read.
- **No Google Search.** Requests carry the URL context tool only, and the code refuses to build one with Google Search in it. Google's terms forbid passing Search grounding results on to another model and using that search to find pages to crawl.
- **Placeholders and handles are dropped.** "Comment removed by moderator", "Comment deleted by user", `[deleted]` and `[removed]` are dropped, and so is any comment that is a lone username or word, because Gemini sometimes returns a commenter's handle as the comment. A removed post body is reported as removed.
- **Nothing is stored.** Requests send `store: false`, so the Interactions API does not keep the exchange (it keeps them 1 day on the free tier and 55 days on paid by default).
- **The key stays secret.** It is read from `GEMINI_API_KEY` (or `GOOGLE_API_KEY`), and on Windows from the user environment when it was set with `setx` after the shell started. It is never printed, logged or written to a file.

## What it measured

On 2026-10-15, six Reddit threads read through the route on `gemini-3.5-flash-lite` were compared with two independent copies of the same threads. Six of six titles and post bodies were right, and no comment was shown to be invented. Comments returned: 20 of 21, 47 of 51, 12 of 13, 151 of 185, 62 of 174 and 89 of 251, so long threads come back in part. Deleted comments came back as placeholders, not their old text. Strikethrough is lost, so a struck-out claim reads as asserted. A thread must already be in Google's index to read; one 8.6 hours old was. Each thread cost 3,000 to 15,000 tokens of page plus 600 to 10,000 output tokens. Details: [skills/fetchwright/references/route.md](skills/fetchwright/references/route.md).

## Terms and privacy

What the terms say, as read on 2026-10-15, and what is untested:

- The Gemini API Additional Terms (effective 2026-03-23) restrict the results of Grounding with Google Search. No clause names URL context, and the URL context docs list technical limits only. Whether URL context output counts as a "Grounded Result" is not stated anywhere. fetchwright never sends Google Search.
- The site's side is untested. For Reddit, Google reads its own copy and hands back its reading of the page. No clause was found that forbids this, and none that permits it. This README does not call the route legal.
- On the free tier, Google may use what fetchwright sends and receives to improve its products, and human reviewers may read it. fetchwright sends a public URL and an instruction, and receives the page's text. Do not send anything private through it. On a paid project, prompts are not used that way.
- Gemini API users must be 18 or older. Tools that serve users in the EEA, Switzerland or the UK may use only paid Gemini services.
- fetchwright itself sends nothing anywhere except to Google's Gemini API, with your key, for the URLs you name. It keeps no logs. `--save-raw DIR` writes raw responses only when asked; they hold page text, so keep them out of repositories.

## Install

Claude Code, from a clone:

```
git clone https://github.com/m4bwav/fetchwright
claude plugin marketplace add ./fetchwright
claude plugin install fetchwright@fetchwright
```

The [wiki](https://github.com/m4bwav/fetchwright/wiki) has every command with its output, the JSON record, recipes and an FAQ.

Other agents that read Agent Skills (`SKILL.md`): link or copy the two folders under `skills/` into the agent's skills folder. The CLI alone needs only Python and a key: `python skills/fetchwright/scripts/fetchwright.py --help`. The `fetchwright-setup` skill walks through getting the key.

## Tests

- `python tests/test_fetchwright.py`: 37 offline tests on responses built in the shape the API returns, with invented text. No network and no key.
- `python tests/smoke_live.py`: one live read of a Wikipedia article. It skips when no key is set, which is how it runs in CI.
- `python scripts/budget.py`: the size budget below.
- The trigger and decoy cases in `evals/` run with `claude plugin eval`. Results go in each skill's TESTS.md.

## Size budget

fetchwright should stay small enough that nobody thinks twice about installing it. `scripts/budget.py` measures each row, and CI fails at red.

| measure | green up to | yellow up to | now (0.1.0) |
|---|---:|---:|---:|
| longest skill description, characters (loaded in every session) | 1,000 | 1,300 | 873 |
| both descriptions, characters | 1,800 | 2,400 | 1,734 |
| largest SKILL.md, tokens | 2,500 | 3,500 | 1,519 |
| largest reference file, tokens | 2,000 | 3,000 | 1,292 |
| fetchwright.py, lines | 600 | 900 | 497 |
| installed skills folder, KB | 150 | 400 | 88 |
| tracked repository, KB | 1,024 | 3,072 | 489 |

## Evergreen

Both skills keep their research current on a schedule (tier fast). `fetchwright-setup` re-checks prices, limits and terms lines before quoting them, because those change monthly. Plugin versions are in [CHANGELOG.md](CHANGELOG.md); every skill change is logged with its reason in that skill's CHANGELOG.md, findings in RESEARCH.md and lessons from real use in LEARNINGS.md.

## Licence

MIT, see [LICENSE](LICENSE). Semantic versions; tags `vX.Y.Z`.
