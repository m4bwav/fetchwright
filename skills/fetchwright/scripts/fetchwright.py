#!/usr/bin/env python3
"""fetchwright: read a public web page that ordinary fetchers cannot reach, through Gemini's URL context tool.

The model is handed the URL and asked to copy the page's text back as JSON. Google reads the page from its own
index or a live fetch, so pages that refuse scripts and plain HTTP clients (Reddit threads, for one) can still be
read. Standard library only, Python 3.10 or newer, Windows, macOS and Linux.

    python fetchwright.py check                      # is a key set, which models answer
    python fetchwright.py read URL [URL ...]         # page text, or a thread's post and comments
    python fetchwright.py read URL --json            # the same as JSON

Rules the code enforces: the key comes from the environment and is never printed or written anywhere; requests
carry the url_context tool only and never Google Search (build_body refuses it); a page whose retrieval did not
succeed gives no text, whatever the model wrote; placeholders for removed or deleted comments and comments that
are a lone username are dropped before anything is printed.
"""
import argparse
import http.client
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

VERSION = "0.1.0"
API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODELS = ("gemini-3.8-flash", "gemini-3.5-flash-lite")
KEY_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")
USER_AGENT = f"fetchwright/{VERSION} (+https://github.com/m4bwav/fetchwright)"
DEFAULT_MAX_CHARS = 25000
SEARCH_TOOLS = ("google_search", "googlesearch", "google_search_retrieval", "googlesearchretrieval")
SUCCESS_STATUSES = ("success", "url_retrieval_status_success")
KNOWN_STATUSES = SUCCESS_STATUSES + ("error", "unsafe", "paywall", "url_retrieval_status_error", "url_retrieval_status_unsafe",
                                     "url_retrieval_status_paywall", "url_retrieval_status_unspecified")

# Text Reddit and other forums put where a removed or deleted comment was. Seen in Gemini's copies on 2026-10-15.
PLACEHOLDERS = ("comment removed by moderator", "comment deleted by user", "comment removed by reddit",
                "removed by moderator", "deleted by user", "[deleted]", "[removed]", "comment image")
# One token of the shape usernames take. Gemini sometimes returns a commenter's handle as a comment's text.
LONE_TOKEN = re.compile(r"(?:u/)?[A-Za-z0-9_-]{3,24}")

EXIT_OK, EXIT_UNREAD, EXIT_USAGE, EXIT_RATE, EXIT_KEY, EXIT_DOWN = 0, 1, 2, 3, 4, 5

_HEAD = """Read this {what} with the URL context tool: {url}

Return ONLY a JSON object, no prose, no code fences:
{{"read_ok": true or false, "why_not": "<if the page could not be read, what you saw instead>",
"""
_TAIL = """
If you could not read the page, set read_ok false and do not invent content."""

# Gemini blocks long word-for-word copies ("Request blocked due to copyright/recitation content", HTTP 400, seen
# 2026-10-15 on a Wikipedia article), so pages default to a digest. Thread comments are short and copy fine.
INSTRUCTIONS = {
    ("page", "verbatim"): """ "title": "<the page title, word for word>",
 "text": "<the page's main content as plain text, word for word, paragraphs separated by blank lines>"}}
Copy the main content from the first paragraph to the last. Leave out navigation, menus, ads, cookie notices and
footers. Copy the text exactly; do not summarise or paraphrase.""",
    ("page", "digest"): """ "title": "<the page title, word for word>",
 "text": "<a faithful, detailed account of the page's main content, section by section in the page's order>"}}
Cover every section from the first to the last, not only the opening. Keep names, numbers, dates, versions and
links exactly as the page gives them. Quote at most one sentence at a time, and only where the exact wording
matters. Leave out navigation, menus, ads, cookie notices and footers. Add nothing the page does not say.""",
    ("thread", "verbatim"): """ "title": "<post title, word for word>", "body": "<post body text, word for word, empty if none>",
 "comments": [{{"text": "<comment text word for word>", "author_is_op": true or false}}]}}
Include {how_many} comments as the page shows, in page order, copied exactly. Put only what each person wrote in
"text": never a username, a score or a timestamp. Do not summarise or paraphrase.""",
    ("thread", "digest"): """ "title": "<post title, word for word>", "body": "<what the post says, faithfully, in brief>",
 "comments": [{{"text": "<what the comment says, faithfully, in brief>", "author_is_op": true or false}}]}}
Include {how_many} comments as the page shows, in page order. Keep names, numbers and links exactly. Never put a
username, a score or a timestamp in "text". Add nothing the page does not say.""",
}


def instruction(mode, style, url, max_comments=0):
    how_many = f"at most {max_comments}" if max_comments else "as many"
    what = "discussion thread" if mode == "thread" else "page"
    return (_HEAD.format(what=what, url=url) + INSTRUCTIONS[(mode, style)].format(how_many=how_many) + _TAIL)


class Stop(Exception):
    """Ends the whole run: the key was refused or the API is rate limiting."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------- key

def _registry_key(name):
    """A user-level variable set with setx after this shell started (Windows only)."""
    if os.name != "nt":
        return ""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            value, _ = winreg.QueryValueEx(k, name)
            return str(value or "")
    except OSError:
        return ""


def find_key():
    """(key, where it came from). The key itself is never printed."""
    for name in KEY_VARS:
        if os.environ.get(name):
            return os.environ[name], f"environment variable {name}"
    for name in KEY_VARS:
        value = _registry_key(name)
        if value:
            return value, f"user environment {name} (set after this shell started)"
    return "", ""


# ---------------------------------------------------------------- request

def build_body(model, instruction, tools=None):
    """The Interactions request. Refuses any Google Search tool: its terms forbid handing results to another model."""
    tools = [{"type": "url_context"}] if tools is None else tools
    for tool in tools:
        names = [str(tool.get("type", ""))] + [str(k) for k in tool]
        if any(n.lower().replace("-", "_") in SEARCH_TOOLS for n in names):
            raise ValueError("fetchwright never sends Google Search: its terms forbid passing grounded results on")
    # store false: the Interactions API otherwise keeps every exchange (1 day free, 55 days paid; docs 2026-10-15).
    body = {"model": model, "input": instruction, "store": False}
    if tools:
        body["tools"] = tools
    return body


def http_post(url, body, key, timeout):
    """POST JSON. Returns (http status or "net", parsed body or error dict, seconds). Tests replace this."""
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST", headers={
        "x-goog-api-key": key, "Content-Type": "application/json", "User-Agent": USER_AGENT})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8")), time.time() - t0
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")
        try:
            data = json.loads(text)
        except ValueError:
            data = {"error": {"message": text[:500]}}
        return e.code, data, time.time() - t0
    except (urllib.error.URLError, http.client.HTTPException, socket.timeout, ConnectionError, OSError) as e:
        return "net", {"error": {"message": f"{type(e).__name__}: {e}"}}, time.time() - t0


def classify(status, data):
    """What a response means for the run: ok, next (try the next model), stop-rate, stop-key, or fail (this URL)."""
    message = str(((data or {}).get("error") or {}).get("message", ""))
    if status == 200:
        return "ok", ""
    if status == "net":
        return "next", "dropped: " + message
    if status in (500, 502, 503, 504):
        return "next", f"overloaded ({status}): {message}"
    if status == 404:
        return "next", f"model not available (404): {message}"
    if status == 429 and re.search(r"\bfor model\b|per day|perday", message.lower()):
        # one model's own quota (the free tier gives each model its own daily limit): the next model may still answer
        return "quota", f"model quota used up (429): {message}"
    if status == 429:
        return "stop-rate", f"rate limited (429): {message}"
    if status == 402:
        return "stop-key", f"payment required (402, the prepaid balance is empty): {message}"
    if status in (401, 403) or (status == 400 and "api key" in message.lower()):
        return "stop-key", f"key refused ({status}): {message}"
    if status == 400 and "recitation" in message.lower():
        return "recitation", f"blocked as recitation (400): {message}"
    if status == 400:
        return "next", f"request refused (400): {message}"
    return "fail", f"HTTP {status}: {message}"


def call_models(models, instruction, key, timeout, post=None, spent=None):
    """Try each model in turn. Returns (model, data, tried) for the first 200, or (None, None, tried).
    spent: models whose quota ran out earlier in this run; they are skipped and new ones are added. When every
    model's quota is spent, the run stops with EXIT_RATE like any other 429."""
    post = post or http_post
    spent = set() if spent is None else spent
    tried = []
    for model in [m for m in models if m not in spent]:
        status, data, secs = post(f"{API_BASE}/interactions", build_body(model, instruction), key, timeout)
        verdict, why = classify(status, data)
        tried.append({"model": model, "http": status, "seconds": round(secs, 1), "outcome": verdict, "why": why[:300]})
        if verdict == "ok":
            return model, data, tried
        if verdict == "quota":
            spent.add(model)
            if all(m in spent for m in models):
                raise Stop(EXIT_RATE, why + " Every model's quota is used up. Stopped: wait before trying again.")
            continue
        if verdict == "stop-rate":
            raise Stop(EXIT_RATE, why + " Stopped: wait before trying again, and check the quota in AI Studio.")
        if verdict == "stop-key":
            raise Stop(EXIT_KEY, why + " Stopped: check the key (run `check`, or the fetchwright-setup skill).")
        if verdict in ("fail", "recitation"):
            return None, None, tried
    return None, None, tried


# ---------------------------------------------------------------- response

def parse_interaction(data):
    """(model text, retrieval statuses, usage) from an Interactions response."""
    texts, retrieval = [], []
    for step in (data or {}).get("steps") or []:
        kind = step.get("type")
        if kind == "url_context_result":
            for r in step.get("result") or []:
                retrieval.append({"url": r.get("url", ""), "status": str(r.get("status", ""))})
        elif kind == "model_output":
            for c in step.get("content") or []:
                if c.get("type") == "text":
                    texts.append(c.get("text") or "")
    u = (data or {}).get("usage") or {}
    usage = {"input": u.get("total_input_tokens"), "page": u.get("total_tool_use_tokens"),
             "output": u.get("total_output_tokens"), "total": u.get("total_tokens")}
    return "".join(texts), retrieval, usage


def extract_json(text):
    """The JSON object in the model's text, allowing for code fences or prose around it. None if there is none."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    try:
        value = json.loads(t)
        return value if isinstance(value, dict) else None
    except ValueError:
        pass
    start, end = t.find("{"), t.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(t[start:end + 1])
        return value if isinstance(value, dict) else None
    except ValueError:
        return None


def strip_placeholders(text):
    """(text without leading placeholders, whether any was removed)."""
    t = (text or "").strip()
    removed = False
    again = True
    while again and t:
        again = False
        low = t.lower()
        for p in PLACEHOLDERS:
            if low.startswith(p):
                t = t[len(p):].lstrip(" \t\r\n:.-")
                removed = again = True
                break
    return t, removed


def clean_comments(comments):
    """Kept comments and counts of what was dropped (placeholders, lone tokens that look like usernames)."""
    kept, dropped = [], {"placeholder": 0, "lone_token": 0, "empty": 0}
    for c in comments or []:
        if isinstance(c, str):
            c = {"text": c}
        if not isinstance(c, dict):
            continue
        text, had_placeholder = strip_placeholders(str(c.get("text") or ""))
        if not text:
            dropped["placeholder" if had_placeholder else "empty"] += 1
            continue
        if LONE_TOKEN.fullmatch(text):
            dropped["lone_token"] += 1
            continue
        kept.append({"text": text, "author_is_op": bool(c.get("author_is_op"))})
    return kept, dropped


def is_thread_url(url):
    p = urllib.parse.urlsplit(url)
    host = p.netloc.lower()
    if host.endswith("reddit.com") and "/comments/" in p.path:
        return True
    return host == "news.ycombinator.com" and p.path == "/item"


def build_result(url, mode, model, data, tried, style="verbatim"):
    """The record printed for one URL."""
    result = {"fetchwright": VERSION, "url": url, "mode": mode, "style": style, "model": model, "models_tried": tried,
              "read_ok": False, "why_not": "", "retrieval": [], "new_statuses": [], "title": "", "usage": {}}
    if mode == "thread":
        result.update({"body": "", "body_removed": False, "comments": [],
                       "dropped": {"placeholder": 0, "lone_token": 0, "empty": 0}})
    else:
        result["text"] = ""
    if data is None:
        last = tried[-1]["why"] if tried else "no model tried"
        result["why_not"] = "no model answered: " + last
        return result
    text, retrieval, usage = parse_interaction(data)
    result["retrieval"], result["usage"] = retrieval, usage
    result["new_statuses"] = sorted({r["status"] for r in retrieval if r["status"].lower() not in KNOWN_STATUSES})
    retrieved = any(r["status"].lower() in SUCCESS_STATUSES for r in retrieval)
    parsed = extract_json(text)
    if parsed is None:
        result["why_not"] = "the model's answer was not the JSON asked for"
        result["unparsed"] = text[:2000]
        return result
    if not parsed.get("read_ok"):
        result["why_not"] = str(parsed.get("why_not") or "the model could not read the page")
        return result
    if not retrieved:
        result["why_not"] = ("the model answered but no page was retrieved (statuses: "
                             + (", ".join(r["status"] for r in retrieval) or "none") + "); its text was discarded")
        return result
    result["read_ok"] = True
    result["title"] = str(parsed.get("title") or "").strip()
    if mode == "thread":
        body, removed = strip_placeholders(str(parsed.get("body") or ""))
        result["body"], result["body_removed"] = body, removed and not body
        result["comments"], result["dropped"] = clean_comments(parsed.get("comments"))
    else:
        result["text"] = str(parsed.get("text") or "").strip()
    return result


# ---------------------------------------------------------------- output

def render_text(result):
    lines = [f"# {result['title'] or result['url']}", f"url: {result['url']}"]
    lines.append(f"model: {result['model'] or 'none'}  mode: {result['mode']}  style: {result['style']}"
                 + ("  (the model's account, not quotes)" if result["style"] == "digest" else ""))
    if result["retrieval"]:
        lines.append("retrieval: " + "; ".join(f"{r['status']} {r['url']}" for r in result["retrieval"]))
    u = result.get("usage") or {}
    if u.get("total"):
        lines.append(f"tokens: page {u.get('page')}, output {u.get('output')}, total {u.get('total')}")
    if result["new_statuses"]:
        lines.append("new retrieval status seen: " + ", ".join(result["new_statuses"]))
    if not result["read_ok"]:
        lines.append(f"NOT READ: {result['why_not']}")
        return "\n".join(lines) + "\n"
    lines.append("")
    if result["mode"] == "thread":
        if result["body_removed"]:
            lines.append("(post body removed or deleted)")
        elif result["body"]:
            lines.append(result["body"])
        d = result["dropped"]
        lines += ["", f"## Comments ({len(result['comments'])} kept; dropped {d['placeholder']} placeholders, "
                      f"{d['lone_token']} lone usernames or words, {d['empty']} empty)"]
        for i, c in enumerate(result["comments"], 1):
            lines.append(f"{i}. {'[OP] ' if c['author_is_op'] else ''}{c['text']}")
    else:
        lines.append(result["text"])
    return "\n".join(lines) + "\n"


def clip(text, max_chars):
    if max_chars and len(text) > max_chars:
        return text[:max_chars] + f"\n[cut at {max_chars} characters of {len(text)}; use --max-chars 0 or --json --out FILE]\n"
    return text


def write_out(text, out):
    if out:
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {out} ({len(text)} characters)")
    else:
        sys.stdout.write(text)
        sys.stdout.flush()


# ---------------------------------------------------------------- commands

def model_list(arg):
    raw = arg or os.environ.get("FETCHWRIGHT_MODELS") or ",".join(DEFAULT_MODELS)
    return [m.strip() for m in raw.split(",") if m.strip()]


def cmd_read(args):
    key, _ = find_key()
    if not key:
        print("No Gemini API key: set GEMINI_API_KEY (the fetchwright-setup skill walks through it).", file=sys.stderr)
        return EXIT_KEY
    for url in args.urls:
        if urllib.parse.urlsplit(url).scheme not in ("http", "https"):
            print(f"not an http(s) URL: {url}", file=sys.stderr)
            return EXIT_USAGE
    models = model_list(args.models)
    results, code, spent = [], EXIT_OK, set()
    for i, url in enumerate(args.urls):
        if i:
            time.sleep(args.gap)
        mode = "thread" if args.thread or (not args.page and is_thread_url(url)) else "page"
        style = "digest" if args.digest else "verbatim" if (args.verbatim or mode == "thread") else "digest"
        try:
            model, data, tried = call_models(models, instruction(mode, style, url, args.max_comments), key, args.timeout,
                                              spent=spent)
            if data is None and style == "verbatim" and tried and tried[-1]["outcome"] == "recitation":
                style = "digest"
                model, data, more = call_models(models, instruction(mode, style, url, args.max_comments), key, args.timeout,
                                                spent=spent)
                tried += more
        except Stop as stop:
            print(str(stop), file=sys.stderr)
            if results:
                emit(results, args)
            return stop.code
        if args.save_raw and data is not None:
            os.makedirs(args.save_raw, exist_ok=True)
            name = re.sub(r"[^A-Za-z0-9]+", "_", url.split("://", 1)[-1]).strip("_")[:80] + ".json"
            with open(os.path.join(args.save_raw, name), "w", encoding="utf-8", newline="\n") as f:
                json.dump({"url": url, "model": model, "tried": tried, "response": data}, f, indent=1, ensure_ascii=False)
        result = build_result(url, mode, model, data, tried, style)
        if model is None and all(t["outcome"] in ("next", "quota") for t in tried):
            code = max(code, EXIT_DOWN)
        elif not result["read_ok"]:
            code = max(code, EXIT_UNREAD)
        results.append(result)
    emit(results, args)
    return code


def emit(results, args):
    if args.json:
        payload = results[0] if len(results) == 1 else results
        text = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
        write_out(text if args.out else clip(text, args.max_chars), args.out)
    else:
        text = "\n".join(render_text(r) for r in results)
        write_out(text if args.out else clip(text, args.max_chars), args.out)


def cmd_check(args):
    key, where = find_key()
    report = {"fetchwright": VERSION, "key": bool(key), "key_from": where, "models": []}
    if key and not args.no_call:
        for model in model_list(args.models):
            status, data, secs = http_post(f"{API_BASE}/interactions", build_body(model, "Reply with the word OK.", tools=[]),
                                           key, args.timeout)
            verdict, why = classify(status, data)
            report["models"].append({"model": model, "http": status, "seconds": round(secs, 1),
                                     "answers": verdict == "ok", "why": why[:300]})
            if verdict in ("stop-key", "stop-rate"):
                break
    if args.json:
        print(json.dumps(report, indent=1))
    else:
        print(f"fetchwright {VERSION}")
        print(f"key: {'found in ' + where if key else 'not set (GEMINI_API_KEY)'}")
        for m in report["models"]:
            print(f"  {m['model']}: {'answers' if m['answers'] else 'no'} (HTTP {m['http']}, {m['seconds']} s)"
                  + (f" {m['why']}" if m["why"] else ""))
    if not key:
        return EXIT_KEY
    if report["models"] and not any(m["answers"] for m in report["models"]):
        return EXIT_KEY if any(m["http"] in (400, 401, 403) for m in report["models"]) else EXIT_DOWN
    return EXIT_OK


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", newline="\n")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(prog="fetchwright", description="Read pages other fetchers cannot, through Gemini's URL context tool.")
    p.add_argument("--version", action="version", version=f"fetchwright {VERSION}")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("check", help="is a key set, and which models answer (one tiny request per model)")
    c.add_argument("--models", help=f"comma-separated, first is tried first (default {','.join(DEFAULT_MODELS)} or FETCHWRIGHT_MODELS)")
    c.add_argument("--no-call", action="store_true", help="only look for the key; send nothing")
    c.add_argument("--timeout", type=float, default=90)
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_check)

    r = sub.add_parser("read", help="read one or more public pages")
    r.add_argument("urls", nargs="+", metavar="URL")
    kind = r.add_mutually_exclusive_group()
    kind.add_argument("--thread", action="store_true", help="read as a discussion thread: title, post, comments")
    kind.add_argument("--page", action="store_true", help="read as a page: title and main text")
    style = r.add_mutually_exclusive_group()
    style.add_argument("--verbatim", action="store_true", help="ask for the text word for word (threads do by default; "
                       "long pages are often blocked as recitation, then fetchwright retries as a digest)")
    style.add_argument("--digest", action="store_true", help="ask for a faithful account instead of quotes (pages do by default)")
    r.add_argument("--max-comments", type=int, default=0, help="ask for at most N comments (cuts output tokens)")
    r.add_argument("--models", help="comma-separated model list; the next is tried on 5xx, 404 or a dropped connection")
    r.add_argument("--timeout", type=float, default=120, help="seconds per request (default 120)")
    r.add_argument("--gap", type=float, default=5, help="seconds between URLs (default 5)")
    r.add_argument("--json", action="store_true")
    r.add_argument("--out", help="write the output to this file instead of stdout")
    r.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="cut stdout here (0 for no limit)")
    r.add_argument("--save-raw", metavar="DIR", help="keep each raw response here (page text: keep it out of repositories)")
    r.set_defaults(func=cmd_read)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
