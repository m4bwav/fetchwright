#!/usr/bin/env python3
"""yt.py: a YouTube video as a citable document: title, description links, chapters and a timestamped transcript.

Every transcript line carries a `URL&t=123s` link so a claim drawn from it can be checked at the second it was said.
Standard library only; captions and metadata come from yt-dlp run through `uvx yt-dlp` (or a yt-dlp on PATH), and
only the fields named below are kept (yt-dlp's info.json is ~15 MB, almost all of it the formats list).

    python yt.py read URL                     # markdown: title, chapters, links, transcript grouped by chapter
    python yt.py read URL --json              # the same as JSON
    python yt.py read URL --lang de           # caption language (default en)
    python yt.py clip URL 3:10-5:00 "what settings are on screen?"   # Gemini looks at that clip (reads the screen)

The yt-dlp route breaches YouTube's terms on automated access, so it is opt-in: set FETCHWRIGHT_YT_ROUTE=ytdlp or
pass --route ytdlp. The clip command uses Gemini's YouTube URL input (API terms, GEMINI_API_KEY, paid past the free
tier, ~90 tokens a second of video at low resolution) and never asks the model for chapter times, which it invents.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})")
URL_RE = re.compile(r"https?://[^\s)>\]]+")
GEMINI_MODEL = os.environ.get("FETCHWRIGHT_YT_MODEL", "gemini-3.8-flash")


def video_id(url):
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    m = ID_RE.search(url)
    if not m:
        sys.exit(f"yt.py: no video id in {url!r}")
    return m.group(1)


def ytdlp_cmd():
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    if shutil.which("uvx"):
        return ["uvx", "yt-dlp"]
    sys.exit("yt.py: needs yt-dlp on PATH or uv (uvx yt-dlp)")


def stamp(sec):
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def parse_time(t):
    sec = 0
    for part in t.split(":"):
        sec = sec * 60 + float(part)
    return int(sec)


def json3_lines(data):
    """json3 caption events to [(start_seconds, text)], dropping empty and repeated rolling-caption lines."""
    out, last = [], None
    for ev in data.get("events", []):
        segs = ev.get("segs")
        if not segs or "tStartMs" not in ev:
            continue
        text = " ".join("".join(s.get("utf8", "") for s in segs).split())
        if not text or text == last:
            continue
        out.append((ev["tStartMs"] / 1000, text))
        last = text
    return out


def fetch(url, lang):
    vid = video_id(url)
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ytdlp_cmd() + ["--skip-download", "--write-auto-subs", "--write-subs", "--sub-langs", f"{lang},{lang}-orig",
                             "--sub-format", "json3", "--write-info-json", "--no-warnings", "-o",
                             os.path.join(tmp, "v.%(ext)s"), f"https://www.youtube.com/watch?v={vid}"]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        info_path = os.path.join(tmp, "v.info.json")
        if "HTTP Error 429" in r.stderr:  # YouTube rate limit: stop, never retry in a loop
            sys.exit("yt.py: YouTube answered 429 (rate limit). Stop; try again in an hour, "
                     "or ask about one span with `yt.py clip` (Gemini reads the video itself).")
        if not os.path.exists(info_path):
            sys.exit(f"yt.py: yt-dlp failed ({r.returncode}): {r.stderr.strip()[-400:]}")
        with open(info_path, encoding="utf-8") as f:
            info = json.load(f)
        subs = sorted(n for n in os.listdir(tmp) if n.endswith(".json3"))
        # prefer a human track (v.en.json3) over auto (v.en-orig / auto names sort the same; manual has no suffix)
        lines, track = [], None
        if subs:
            track = min(subs, key=len)
            with open(os.path.join(tmp, track), encoding="utf-8") as f:
                lines = json3_lines(json.load(f))
    base = f"https://www.youtube.com/watch?v={vid}"
    desc = info.get("description") or ""
    chapters = [{"start": c["start_time"], "title": c["title"]} for c in info.get("chapters") or []]
    return {
        "id": vid, "url": base, "title": info.get("title"), "channel": info.get("channel"),
        "upload_date": info.get("upload_date"), "duration": info.get("duration"),
        "view_count": info.get("view_count"), "description": desc,
        "links": list(dict.fromkeys(URL_RE.findall(desc))), "chapters": chapters,
        "caption_track": track, "automatic_captions": bool(track) and track not in (f"v.{lang}.json3",),
        "transcript": [{"t": int(t), "at": stamp(t), "link": f"{base}&t={int(t)}s", "text": x} for t, x in lines],
    }


def to_markdown(d):
    out = [f"# {d['title']}", "", f"{d['channel']} · {d['upload_date']} · {stamp(d['duration'] or 0)} · {d['url']}", ""]
    if not d["transcript"]:
        out += ["No captions in this language. Options: another --lang, or `clip` with Gemini.", ""]
    if d["links"]:
        out += ["## Links in the description", ""] + [f"- {u}" for u in d["links"]] + [""]
    chapters = d["chapters"] or [{"start": 0, "title": "Transcript"}]
    starts = [c["start"] for c in chapters] + [float("inf")]
    for i, c in enumerate(chapters):
        out += [f"## [{stamp(c['start'])}]({d['url']}&t={int(c['start'])}s) {c['title']}", ""]
        para, pstart = [], None
        for ln in d["transcript"]:
            if starts[i] <= ln["t"] < starts[i + 1]:
                if pstart is None:
                    pstart = ln
                para.append(ln["text"])
                if len(para) >= 8:
                    out += [f"[{pstart['at']}]({pstart['link']}) " + " ".join(para), ""]
                    para, pstart = [], None
        if para:
            out += [f"[{pstart['at']}]({pstart['link']}) " + " ".join(para), ""]
    if d["automatic_captions"]:
        out += ["_Automatic captions: names and jargon may be misheard; check against the video before quoting._"]
    return "\n".join(out)


def clip(url, span, question):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("yt.py: clip needs GEMINI_API_KEY (see fetchwright-setup)")
    a, b = (parse_time(x) for x in span.split("-"))
    body = {"contents": [{"parts": [
        {"file_data": {"file_uri": f"https://www.youtube.com/watch?v={video_id(url)}"},
         "video_metadata": {"start_offset": f"{a}s", "end_offset": f"{b}s"}},
        {"text": question + " Answer only from what is seen and heard in this clip; say so when it is not shown."}]}],
        "generationConfig": {"mediaResolution": "MEDIA_RESOLUTION_LOW"}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:  # 429, 503 and the rest: report and stop, never retry in a loop
        sys.exit(f"yt.py: Gemini answered {e.code} {e.reason}; stopped")
    except TimeoutError:  # an 8-minute span went past 600 s on 2026-11-17; a 37 s span took 210 s
        sys.exit("yt.py: Gemini gave no answer in 600 s; stopped. Ask about a shorter span (2 minutes or less).")
    text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    usage = data.get("usageMetadata", {})
    print(text.strip())
    print(f"\n[{stamp(a)}-{stamp(b)}] {url} · {usage.get('totalTokenCount', '?')} tokens", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read")
    r.add_argument("url")
    r.add_argument("--lang", default="en")
    r.add_argument("--json", action="store_true")
    r.add_argument("--route", default=os.environ.get("FETCHWRIGHT_YT_ROUTE"))
    c = sub.add_parser("clip")
    c.add_argument("url")
    c.add_argument("span", help="START-END, e.g. 3:10-5:00")
    c.add_argument("question")
    a = ap.parse_args()
    if a.cmd == "clip":
        return clip(a.url, a.span, a.question)
    if a.route != "ytdlp":
        sys.exit("yt.py: transcripts use yt-dlp, which YouTube's terms do not allow; opt in with --route ytdlp "
                 "or FETCHWRIGHT_YT_ROUTE=ytdlp, or use `clip` (Gemini, API terms).")
    d = fetch(a.url, a.lang)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(d, ensure_ascii=False, indent=1) if a.json else to_markdown(d))


if __name__ == "__main__":
    main()
