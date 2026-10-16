---
name: fetchwright-setup
description: "Set up and advise on the Gemini API key that fetchwright needs. Covers creating a key in AI Studio, storing it as GEMINI_API_KEY (setx on Windows, a shell profile on macOS and Linux) without pasting it into chat or a repository, and checking it with fetchwright check. Explains the free and paid tiers, rate limits and 429s, what a read costs, what Google may do with free-tier prompts (used to improve products, read by human reviewers), the 18+ rule, and the EEA, Swiss and UK rule for serving others. Use when the user asks 'set up fetchwright', 'get a gemini api key', 'fetchwright says no key', 'is the gemini free tier private', 'why does gemini give me 429', 'what does fetchwright cost', 'should I pay for gemini', or when fetchwright check exits 4. Also for 'refresh fetchwright-setup'. Not for other Google APIs, Vertex AI, or reading pages (that is fetchwright)."
metadata:
  version: "0.1.0"
---

# fetchwright-setup

Gets the user a working Gemini API key for fetchwright and answers the questions that come before using one: what it costs, what the limits are, and who sees what is sent. The facts, with sources and dates, are in [references/gemini-api.md](references/gemini-api.md). They move often, so check Step 0 first.

`FW` below means `python "<the fetchwright skill folder>/scripts/fetchwright.py"`.

## Step 0: freshness

Read [evergreen.json](evergreen.json). This unit is `verify_at_use`: before quoting a price, a limit or a terms line to the user, re-check the due `volatile_claims` (one search or fetch each, primary sources only), update [references/gemini-api.md](references/gemini-api.md) if one moved, and stamp it ([MAINTENANCE.md](MAINTENANCE.md)). If a check fails, say the figure is from the reference's date.

## Step 1: is a key already there

Run `FW check --no-call`. It says whether `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is set and where it was found, never the key. On Windows it also finds a key set with `setx` after the shell started. If one is found, run `FW check`, which sends one tiny request per model. A model that answers means setup is done; go to Step 4 only if the user asked about cost or privacy.

## Step 2: what to tell the user before they make a key

Say these four things in plain words, briefly:

1. The free tier costs nothing, but Google may use what fetchwright sends and gets back to improve its products, and human reviewers may read it. fetchwright sends public page URLs and gets their text back, which is fine for public pages. Nothing private should go through it.
2. Users must be 18 or older.
3. Someone building a tool for users in the EEA, Switzerland or the UK may serve them only through a paid project.
4. Limits are per project and shown in AI Studio after signing in. Google does not publish fixed free-tier numbers on its rate-limits page.

## Step 3: make and store the key (the user's hands)

The user does this; never run a browser login for them, and never ask for the key in the chat.

1. Open https://aistudio.google.com/apikey and choose **Create API key**. A new user gets a project made for them. Someone with an existing Google Cloud account may need to import a project first. New keys come restricted to the Gemini API; an older key marked "Unrestricted" needs **Add restrictions**, then "Restrict to Gemini API only", or the API rejects it.
2. Store it as an environment variable, typed by the user in their own terminal:
   - Windows: `setx GEMINI_API_KEY "<key>"`, then restart the editor or terminal (a running shell does not see it; `FW check` still finds it through the registry).
   - macOS or Linux: add `export GEMINI_API_KEY="<key>"` to `~/.zshrc` or `~/.bashrc`, then open a new terminal.
3. Never put the key in a repository, a `.env` file that is committed, a script, a log, or a chat. If it leaks, delete it in AI Studio and make a new one.
4. Run `FW check`. A 403 "has not been used in project ... or it is disabled" can last some minutes after a new project; wait and retry. If it persists, make a fresh key in a project AI Studio creates ([references/gemini-api.md](references/gemini-api.md), troubleshooting).

If both `GEMINI_API_KEY` and `GOOGLE_API_KEY` are set, fetchwright uses `GEMINI_API_KEY`. Google's own SDKs prefer `GOOGLE_API_KEY`. Say so if the user has both.

## Step 4: tiers, cost and quotas

- Free tier: no billing, limits shown in AI Studio, prompts used to improve products.
- Paid: link a billing account to the project (prepay from $5). Prompts are then not used to improve products, and limits rise with spending (Tier 1, 2, 3). Unlinking billing returns the project to free.
- What a read costs: the fetched page counts as input tokens; URL context has no separate charge. A Reddit thread was 3,000 to 15,000 page tokens and 600 to 10,000 output tokens in a test. Prices per model are in the reference with their date; work the cost out from them, never from memory.
- A 429 means the minute rate or the daily quota ran out: wait (daily quotas reset at midnight Pacific time) or move to paid. A 429 on one model's own quota moves fetchwright to the next model; it stops when every model is out, or at any other 429. On 2026-10-16 the free tier allowed `gemini-3.8-flash` 20 requests a day. A 402 means a prepaid balance ran out.

## Step 5: hand back

Say in one line that the key works and which models answered, then return to the fetchwright skill for the read. Record nothing about the key except that it works.

## Maintenance

This skill is evergreen: [evergreen.json](evergreen.json) (state), [RESEARCH.md](RESEARCH.md) (findings and search plan), [CHANGELOG.md](CHANGELOG.md) (every change with its reason), [LEARNINGS.md](LEARNINGS.md) (lessons from use), [TESTS.md](TESTS.md) and `evals/evals.json` (the cases that prove it). Protocol: [MAINTENANCE.md](MAINTENANCE.md).
