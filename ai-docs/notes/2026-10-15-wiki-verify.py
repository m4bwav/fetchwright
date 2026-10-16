"""Wiki verification for fetchwright: runs every command and code block the wiki shows, against the released tag.

    python wiki-verify.py <clone of the tag>           # prints every case, ## headers between them

Commands that reach Google's API run through a stand-in: this same file, started with FW_STANDIN=<scenario>, imports
the released fetchwright.py, replaces its http_post with canned responses in the shape the Interactions API returned
on 2026-10-15 (invented sample text), hides the Windows user-registry key, and runs its main(). Nothing here calls
Google. Standard library only.
"""
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile

THREAD_URL = "https://www.reddit.com/r/examplesub/comments/1abc234/"
SLUG_URL = "https://www.reddit.com/r/examplesub/comments/1abc234/a_small_upscaler_node/"
PAGE_URL = "https://example.org/article"

SAMPLE_THREAD = {
    "read_ok": True, "why_not": "", "title": "I made a small upscaler node",
    "body": "It upscales video in tiles so it fits in 8 GB.\n\nLink in the comments.",
    "comments": [
        {"text": "Works on my 3060, about 2 fps at 1080p.", "author_is_op": False},
        {"text": "Thanks for testing. Tiles of 512 are the default.", "author_is_op": True},
        {"text": "Example_User_1234", "author_is_op": False},
        {"text": "Comment removed by moderator", "author_is_op": False},
        {"text": "Does it keep the audio track?", "author_is_op": False},
    ],
}
SAMPLE_PAGE = {"read_ok": True, "why_not": "", "title": "An example article",
               "text": "The article opens with what the project is for.\n\nIts second section lists three releases, in 2024, 2025 and 2026."}
NOT_READ = {"read_ok": False, "why_not": "Not able to browse the provided URL.", "title": "", "body": "", "comments": []}


def interaction(answer, retrieval, page_tokens):
    return {"status": "completed", "object": "interaction",
            "usage": {"total_input_tokens": 190, "total_tool_use_tokens": page_tokens, "total_output_tokens": 410,
                      "total_tokens": 190 + page_tokens + 410},
            "steps": [{"type": "url_context_call", "arguments": {"urls": [retrieval[-1][1]]}},
                      {"type": "url_context_result", "result": [{"url": u, "status": s} for s, u in retrieval]},
                      {"type": "thought"},
                      {"type": "model_output", "content": [{"type": "text", "text": json.dumps(answer)}]}]}


THREAD_OK = (200, interaction(SAMPLE_THREAD, (("success", SLUG_URL), ("error", THREAD_URL)), 4210))
PAGE_OK = (200, interaction(SAMPLE_PAGE, (("success", PAGE_URL),), 3120))
SCENARIOS = {
    "thread": [THREAD_OK],
    "page": [PAGE_OK],
    "both": [THREAD_OK, PAGE_OK],
    "busy": [(503, {"error": {"code": 503, "message": "This model is currently experiencing high demand."}}), THREAD_OK],
    "recite": [(400, {"error": {"code": 400, "message": "Request blocked due to copyright/recitation content."}}), PAGE_OK],
    "rate": [(429, {"error": {"code": "rate_limit_exceeded", "message": "Resource has been exhausted."}})],
    "unread": [(200, interaction(NOT_READ, (("error", PAGE_URL),), 300))],
    "check": [(200, {"steps": []}), (200, {"steps": []})],
    "nokey": [],
}


def standin():
    """Run the released CLI with canned API answers. FW_CLI_DIR names its scripts folder."""
    sys.path.insert(0, os.environ["FW_CLI_DIR"])
    import fetchwright as fw
    queue = list(SCENARIOS[os.environ["FW_STANDIN"]])

    def fake_post(url, body, key, timeout):
        status, data = queue.pop(0)
        return status, data, 0.1

    fw.http_post = fake_post
    fw._registry_key = lambda name: ""
    fw.time.sleep = lambda s: None
    sys.exit(fw.main(sys.argv[1:]))


# Every code block the wiki shows, as the page shows it.
SNIPPETS = {
    "home-read": "python fetchwright.py read https://www.reddit.com/r/examplesub/comments/1abc234/",
    "check-no-call": "python fetchwright.py check --no-call",
    "check": "python fetchwright.py check",
    "help": "python fetchwright.py --help",
    "read-help": "python fetchwright.py read --help",
    "check-help": "python fetchwright.py check --help",
    "version": "python fetchwright.py --version",
    "read-json": "python fetchwright.py read https://www.reddit.com/r/examplesub/comments/1abc234/ --json",
    "read-page": "python fetchwright.py read https://example.org/article",
    "read-verbatim": "python fetchwright.py read https://example.org/article --verbatim --json",
    "read-unread": "python fetchwright.py read https://example.org/article",
    "read-busy": "python fetchwright.py read https://www.reddit.com/r/examplesub/comments/1abc234/ --json --max-chars 900",
    "read-rate": "python fetchwright.py read https://www.reddit.com/r/examplesub/comments/1abc234/",
    "read-nokey": "python fetchwright.py read https://www.reddit.com/r/examplesub/comments/1abc234/",
    "check-nokey": "python fetchwright.py check --no-call",
    "read-badurl": "python fetchwright.py read file:///etc/hosts",
    "recipe-out": "python fetchwright.py read https://www.reddit.com/r/examplesub/comments/1abc234/ --json --out thread.json",
    "recipe-load": '''
import json

with open("thread.json", encoding="utf-8") as f:
    thread = json.load(f)
print(thread["title"])
print(len(thread["comments"]), "comments kept, dropped:", thread["dropped"])
''',
    "recipe-subprocess": '''
import json
import os
import subprocess
import sys

CLI = os.environ.get("FETCHWRIGHT_CLI", "skills/fetchwright/scripts/fetchwright.py")
url = "https://www.reddit.com/r/examplesub/comments/1abc234/"
proc = subprocess.run([sys.executable, CLI, "read", url, "--json", "--max-chars", "0"],
                      capture_output=True, text=True, encoding="utf-8")
if proc.returncode == 3:
    raise SystemExit("rate limited: stop for now")
if proc.returncode == 4:
    raise SystemExit("no key, or the key was refused")
result = json.loads(proc.stdout)
print(result["read_ok"], result["model"], len(result["comments"]))
''',
    "recipe-several": "python fetchwright.py read https://www.reddit.com/r/examplesub/comments/1abc234/ https://example.org/article --gap 6",
    "recipe-fewer": "python fetchwright.py read https://www.reddit.com/r/examplesub/comments/1abc234/ --max-comments 30",
    "recipe-models": '''
FETCHWRIGHT_MODELS=gemini-3.5-flash-lite python fetchwright.py read https://www.reddit.com/r/examplesub/comments/1abc234/
''',
    "dev-tests": "python tests/test_fetchwright.py",
    "dev-budget": "python scripts/budget.py",
}

# case -> (snippet, stand-in scenario or None for the plain CLI, key in the environment?)
CASES = [
    ("home-read", "thread", True), ("check-no-call", "nokey", True), ("check", "check", True),
    ("help", None, False), ("read-help", None, False), ("check-help", None, False), ("version", None, False),
    ("read-json", "thread", True), ("read-page", "page", True), ("read-verbatim", "recite", True),
    ("read-unread", "unread", True), ("read-busy", "busy", True), ("read-rate", "rate", True),
    ("read-nokey", "nokey", False), ("check-nokey", "nokey", False), ("read-badurl", "nokey", True),
    ("recipe-several", "both", True), ("recipe-fewer", "thread", True), ("recipe-models", "thread", True),
]


def env_for(scenario, key, cli_dir):
    env = {k: v for k, v in os.environ.items() if k not in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "FETCHWRIGHT_MODELS")}
    env["PYTHONIOENCODING"] = "utf-8"
    if key:
        env["GEMINI_API_KEY"] = "stand-in-key"
    if scenario:
        env["FW_STANDIN"], env["FW_CLI_DIR"] = scenario, cli_dir
    return env


def run_command(text, scenario, key, cli_dir, cwd):
    """Run a page command: 'python fetchwright.py ...' runs the released CLI, or the stand-in when one is named."""
    words = shlex.split(text.strip())
    env = env_for(scenario, key, cli_dir)
    while words and re.fullmatch(r"[A-Z_]+=.*", words[0]):
        name, value = words.pop(0).split("=", 1)
        env[name] = value
    assert words[:2] == ["python", "fetchwright.py"], text
    target = os.path.abspath(__file__) if scenario else os.path.join(cli_dir, "fetchwright.py")
    proc = subprocess.run([sys.executable, target] + words[2:], capture_output=True, text=True, encoding="utf-8",
                          env=env, cwd=cwd)
    return proc.stdout + proc.stderr, proc.returncode


def section(name, text, code=None):
    print(f"## {name}" + (f" (exit {code})" if code is not None else ""))
    print(text.rstrip("\n"))
    print()


def main():
    clone = os.path.abspath(sys.argv[1])
    cli_dir = os.path.join(clone, "skills", "fetchwright", "scripts")
    with open(os.path.join(cli_dir, "fetchwright.py"), encoding="utf-8") as f:
        version = re.search(r'VERSION = "([^"]+)"', f.read()).group(1)
    section("installed", f"fetchwright {version} from {os.path.basename(clone)}; Python {sys.version.split()[0]}")
    work = tempfile.mkdtemp(prefix="fw-wiki-")
    for name, scenario, key in CASES:
        out, code = run_command(SNIPPETS[name], scenario, key, cli_dir, work)
        section(name, out, code)

    out, code = run_command(SNIPPETS["recipe-out"], "thread", True, cli_dir, work)
    section("recipe-out", out, code)
    proc = subprocess.run([sys.executable, "-c", SNIPPETS["recipe-load"].strip()], capture_output=True, text=True,
                          encoding="utf-8", cwd=work)
    section("recipe-load", proc.stdout + proc.stderr, proc.returncode)
    env = env_for("thread", True, cli_dir)
    env["FETCHWRIGHT_CLI"] = os.path.abspath(__file__)
    proc = subprocess.run([sys.executable, "-c", SNIPPETS["recipe-subprocess"].strip()], capture_output=True, text=True,
                          encoding="utf-8", cwd=work, env=env)
    section("recipe-subprocess", proc.stdout + proc.stderr, proc.returncode)

    for name in ("dev-tests", "dev-budget"):
        proc = subprocess.run([sys.executable] + shlex.split(SNIPPETS[name])[1:], capture_output=True, text=True,
                              encoding="utf-8", cwd=clone)
        text = re.sub(r"Ran (\d+) tests in [0-9.]+s", r"Ran \1 tests in <seconds>s", proc.stdout + proc.stderr)
        section(name, text, proc.returncode)


if __name__ == "__main__":
    if os.environ.get("FW_STANDIN"):
        standin()
    else:
        main()
