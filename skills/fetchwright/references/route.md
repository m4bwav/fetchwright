# How the route works, what it costs, what the terms say

Checked 2026-10-15 against Google's docs and a live test. Sources and later checks: [../RESEARCH.md](../RESEARCH.md).

## The request

```
POST https://generativelanguage.googleapis.com/v1beta/interactions
x-goog-api-key: <key from the environment>
{"model": "gemini-3.8-flash", "input": "<instruction naming the URL>", "tools": [{"type": "url_context"}], "store": false}
```

- `store: false` because the Interactions API otherwise keeps each exchange (1 day on the free tier, 55 days on paid).
- The response's `steps` hold a `url_context_call`, a `url_context_result` (each URL with a `status`), a `thought` and a `model_output` with the text. `usage.total_tool_use_tokens` is the fetched page.
- URL context tries Google's index first, then a live fetch. Up to 20 URLs a request and 34 MB a URL; fetchwright sends one URL a request so each gets its own status.
- Not readable: pages behind a login or paywall, YouTube, Google Docs and Sheets, video and audio, localhost and private networks. Readable: HTML, JSON, plain text, PDF, PNG, JPEG, BMP, WebP.
- Cache each page result by URL plus a hash of the prompt, with an expiry (a day suits most pages; skip time-sensitive ones such as live threads or prices), so a same-day re-read costs no Gemini quota. `--out` or `--save-raw` gives the file to cache.

## Statuses

Seen on 2026-10-15: `success` and `error`. Documented: success, error, paywall, unsafe (`URL_RETRIEVAL_STATUS_*` in generateContent). A Reddit thread returns two entries: the thread's slug URL `success` (from the index) and the bare URL `error` (Reddit refuses the live fetch). A GitHub page and a missing Wikipedia page came back `error`; the model then said it could not read the page and invented nothing.

## Errors

| HTTP | meaning | fetchwright |
|---|---|---|
| 503, 500, 502, 504, a dropped connection | overloaded (`gemini-3.8-flash` was, most of 2026-10-15) | next model |
| 404 | model gone or closed to new users (`gemini-2.5-flash`) | next model |
| 400 "copyright/recitation" | the model may not copy that much text | retry once as a digest |
| 429 naming one model ("for model X", "per day") | that model's quota, for example 20 a day for `gemini-3.8-flash` on the free tier (2026-10-16) | next model, skipped for the rest of the run; stop when every model's quota is used up |
| 429, other | rate limit | stop the run |
| 400 "API key not valid", 401, 403 | key | stop the run |
| 402 | prepaid balance empty | stop the run |

## What a test measured (Stage 1, 2026-10-15, gemini-3.5-flash-lite)

Six Reddit threads were compared with two independent copies (an archive and Reddit's feeds). Six of six titles and bodies were right. Comments returned: 20 of 21, 47 of 51, 12 of 13, 151 of 185, 62 of 174 and 89 of 251. No comment was shown to be invented. Deleted comments came back as placeholders, not their old text, and a deleted post came back empty. Usernames came back as comment text 20 times in 381 comments. Each thread cost 3,000 to 15,000 page tokens plus 600 to 10,000 output tokens. Asking for a whole Wikipedia article word for word was blocked as recitation; the digest read every section.

## The terms, as of 2026-10-15

- The Gemini API Additional Terms (effective 2026-03-23) restrict "Grounded Results", answers made with Grounding with Google Search: no caching, analysis or mixing by others. They forbid using that search "to identify destination pages for crawling or scraping". No clause names URL context, and the URL context docs list technical limits only. Whether its output counts as a grounded result is not stated anywhere.
- "You're responsible for your use of generated content, and for the use of that content by anyone you share it with."
- Free tier: Google may use what you send and get back to improve its products, and human reviewers may read it. Paid: prompts are not used that way and are logged for a limited time for abuse checks.
- 18 or older. Only paid services may serve users in the EEA, Switzerland or the UK.
- The site's side is untested: for Reddit, Google reads its own copy and hands back its reading. No clause was found that forbids this, and nothing that permits it either. This page does not call the route legal.
