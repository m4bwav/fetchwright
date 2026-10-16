---
title: GitHub wiki written and published for 0.1.0
kind: note
date: 2026-10-15
verified: 2026-10-15
stale_after: 2027-04-15
tags: [wiki, docs, 0.1.0, github]
summary: "the wiki's pages, where their git working copy is, how every example was verified against the released v0.1.0 tag, the facts found on the way, the inaccuracies in the shipped docs, and how to update the wiki; read before touching the wiki or the README sentences listed under inaccuracies"
---

# GitHub wiki for 0.1.0

## Summary

The owner asked for the wiki after releasing 0.1.0 on 2026-10-15; he created the first page. The run wrote 9 pages and a sidebar and footer from the repository, the release, and a verification program run against the v0.1.0 tag. Wiki commit 8287e8f. `live`: 9 pages, 0 failures. The prose checker found 0 strong and 4 weak (judged fine).

Pages: Home, Getting-Started, Commands, How-Pages-Are-Read, Terms-and-Privacy, Recipes, FAQ, Versions-and-Upgrading, Development, plus `_Sidebar.md` and `_Footer.md`.

## Where the pages are

`D:\m4bwa\Claude\Projects\Ai\fetchwright.wiki` (a sibling of this clone, outside this repository), branch `master`, remote `origin` = `https://github.com/m4bwav/fetchwright.wiki.git`. Plain markdown links between pages (`[Recipes](Recipes)`), no wikilinks, LF line endings.

## How it was published

Preflight state: `placeholder` (the owner's first page, "Welcome to the fetchwright wiki!"). The pages were committed on top of it with a plain push. `wikiwright.py live m4bwav/fetchwright`: root 200, footer and sidebar render, 8 anchor links fine, 9 pages, 0 failures.

## Updating the wiki later

1. `git -C <wiki dir> pull --ff-only`, then edit the pages.
2. Re-verify from a scratch folder: `git clone --depth 1 --branch vX.Y.Z https://github.com/m4bwav/fetchwright <scratch>/fw`, then `python -I 2026-10-15-wiki-verify.py <scratch>/fw > new.out.txt` (the program beside this note).
   - The program runs the plain CLI for help, version and argument errors.
   - It runs a stand-in for Google's API for every `check` and `read` (the same file started with `FW_STANDIN=<scenario>`; it replaces `http_post` and hides the Windows registry key). Nothing calls Google.
   - `python <wikiwright>/scripts/wikiwright.py diffout 2026-10-15-wiki-verify.out.txt new.out.txt` lists every changed section; each difference is a page to fix. If the stand-in's canned responses no longer match the CLI (a changed response shape), update them from a real response saved with `--save-raw`, with the text replaced.
3. `wikiwright.py outputs <wiki dir> new.out.txt --address ''`, `wikiwright.py snippets <wiki dir> <the program>`, `wikiwright.py check <wiki dir> --version <new>`, and the everwrite checker.
4. Commit, `git push`, `wikiwright.py live m4bwav/fetchwright <wiki dir>`. Pages that name the version: Home (intro), Commands (`--version` output and every output's header line), How-Pages-Are-Read (JSON `"fetchwright": "0.1.0"`), Getting-Started (`check` output), Versions-and-Upgrading, Development (budget table), `_Footer.md`.

## How the examples were verified

- The program is `2026-10-15-wiki-verify.py` and its saved output is `2026-10-15-wiki-verify.out.txt`, with the scratch path masked.
- It ran fetchwright 0.1.0 from a depth-1 clone of tag v0.1.0, with Python 3.14.6 on Windows 11.
- Every command and Python block on the pages is run as written, 25 sections in all.
- Sample content is invented (the thread `r/examplesub/comments/1abc234`, `example.org/article`). Home says so.
- The stand-in answers in the Interactions API's shape of 2026-10-15.
- Not run: the install commands, `setx` and `export` with a real key, and `tests/smoke_live.py` (a live call). They are marked skip on the pages. The PowerShell variant of `FETCHWRIGHT_MODELS` is marked "not tested".
- `outputs`: 21 checked, 0 missing, 1 skipped (an elided JSON block). `snippets`: 3 checked, 0 missing, 4 skipped, 21 commands.
- The repository's tests in the tag clone: 37 run, OK. The budget is green.

## Facts verified while writing (not in the README)

- `read --json` to stdout is cut at `--max-chars` (25,000 by default), so a long record prints broken JSON. Programs must use `--out` or `--max-chars 0`.
- A 429 stops the run and still prints the records already read (stderr carries the message).
- `check` without `--no-call` sends "Reply with the word OK." with no tool, and stops early on a refused key or a 429. Its timeout defaults to 90 s (read's is 120 s).
- An unread page's text header still names the requested style ("style: digest (the model's account, not quotes)").
- Placeholder handling is a prefix strip: a comment that starts with "Comment removed by moderator" and continues keeps the rest. "Comment removed by Reddit" and "Comment Image" are in the list too.
- With one model in the list there is no fallback: an overloaded model gives exit 5 (seen in the first verification run, when the case used the busy scenario).

## Inaccuracies found in the shipped docs

1. README size-budget table said "under 300" KB for the tracked repository; with the icon added it is 489 KB. It also gave SKILL.md 1,430 tokens (now 1,519, after the Maintenance section) and the skills folder 86 KB (now 88). Fixed in the README on 2026-10-15; the README is read from GitHub, so no release is needed.
2. README does not warn that `--json` on stdout can be cut. The wiki says so (Commands, FAQ, Recipes). Candidate fix for 0.1.1: leave `--json` uncut, or cut it only with a valid JSON wrapper.

## Gotchas

- `wikiwright.py snippets` matches whole lines. A Python snippet held in a triple-quoted string must start and end on lines of its own (`'''` then a newline), or its first and last lines are "in no program".
- On Windows, `find_key` reads the registry when the environment has no key, so a "no key" example run on the owner's machine finds the real key. The stand-in hides it (`_registry_key` returns ""). Without that, the page would show "found in user environment".

Related: see also [../HANDOFF.md](../HANDOFF.md), [../log.md](../log.md).
