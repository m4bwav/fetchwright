---
title: fetchwright as a standalone public plugin with a stdlib CLI
kind: decision
status: active
date: 2026-10-15
verified: 2026-10-15
stale_after: 2027-04-13
tags: [design, gemini, url-context, reddit, everscout]
summary: read before adding a command, a model rule, a request field, or wiring fetchwright into everscout
---

# fetchwright as a standalone public plugin with a stdlib CLI

## Context

everscout reads Reddit through the Arctic Shift archive, which collects through Reddit's Data API and is expected to stop when that API closes in March 2027. The backup route found on 2026-10-15: have Gemini read each thread with its URL context tool. A Stage 1 test passed ([everscout research note](https://github.com/m4bwav/everscout/blob/main/ai-docs/research/2026-10-15-gemini-url-context-reddit-test.md)).

## Decision

The owner chose on 2026-10-15 a standalone public plugin, named fetchwright the same day, over a reader inside everscout:

- Two skills: `fetchwright` (when and how to read, how to read the result) and `fetchwright-setup` (key, tiers, quotas, privacy).
- One standard-library CLI, `skills/fetchwright/scripts/fetchwright.py`, with `check` and `read`.
- everscout stays keyless by default and may call the CLI later as a subprocess.

## Reasons

Design choices in 0.1.0, each with its reason:

- One URL a request (the API takes 20) so each page has its own retrieval status and failure.
- Text with no `success` retrieval is discarded: the model could otherwise answer from memory.
- Google Search is refused in `build_body`, because the Gemini API terms forbid passing grounded results on and using them to find pages to crawl.
- `store: false`, because Interactions keeps exchanges 1 day free and 55 days paid by default.
- Pages default to a digest, because a long word-for-word copy drew a recitation block. Threads stay word for word, since that worked.
- Fallback models on 5xx, 404 and dropped connections. Stop on 429 (no retry loop) and on 401, 402 and 403.
- Placeholders and lone username-shaped tokens are dropped, because handles must not reach notes.
- `GEMINI_API_KEY` is preferred over `GOOGLE_API_KEY`, the reverse of Google's SDKs, because `GOOGLE_API_KEY` is often a key for another Google API.

## Rejected options

- A reader inside everscout (config `reddit.thread_reader: gemini`): it would give a keyless plugin a key, and it would serve Reddit only.
- Both at once: more code to keep for no gain until everscout needs it.
- Gemini's Google Search tool for discovery: ruled out by its terms ([everscout research note](https://github.com/m4bwav/everscout/blob/main/ai-docs/research/2026-10-15-reddit-through-gemini.md)).

Related: see also [Word-for-word page copies are blocked as recitation](../solutions/2026-10-15-word-for-word-page-copies-are-blocked-as-recitation-ask-for-.md)
