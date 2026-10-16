---
title: Word-for-word page copies are blocked as recitation; ask for a digest
kind: solution
status: active
date: 2026-10-15
verified: 2026-10-15
stale_after: 2027-01-13
tags: [gemini, url-context, recitation, pages]
evidence: [python tests/smoke_live.py]
proof_count: 1
summary: read before changing the page instruction or the verbatim and digest styles
---

# Word-for-word page copies are blocked as recitation; ask for a digest

## Problem

`fetchwright.py read https://en.wikipedia.org/wiki/Reddit` with an instruction asking for the page's main content word for word:

- The first wording returned only the opening paragraphs: 1,864 characters from 7,427 page tokens.
- A wording asking for "every paragraph from the first to the last" got HTTP 400 with "Request blocked due to copyright/recitation content. Please modify your input and retry."

## Fix

Pages default to a digest: a faithful, section-by-section account that keeps names, numbers, dates and links exactly and quotes at most a sentence at a time. That read every section of the article (2,839 characters from 7,479 page tokens). `--verbatim` still asks for the exact text, and on a recitation block the CLI retries once as a digest. The output marks `style: digest` and says it is the model's account, not quotes.

Thread comments are short and copy word for word without a block (47 comments of a settled Reddit thread, twice on 2026-10-15).

## Verified by

`python tests/smoke_live.py` (live, needs a key) and `python tests/test_fetchwright.py` (`test_recitation_block_retries_as_digest`).
