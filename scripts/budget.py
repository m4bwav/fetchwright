"""Size budget for fetchwright. Run from the repository root: python scripts/budget.py [--json]

What every session loads (the two skill descriptions), what a use loads (SKILL.md, a reference), the CLI and the
installed size must stay small enough that nobody thinks twice about installing the plugin. Exit 2 at red,
0 otherwise; a yellow is printed so the maintainer can be told before the next feature. Tokens are bytes / 4.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())

# measure, green <=, yellow <= (above yellow is red)
BUDGETS = [
    ("longest skill description, characters (always loaded; cut at 1,536)", 1000, 1300),
    ("both skill descriptions, characters", 1800, 2400),
    ("largest SKILL.md, tokens (loaded on every use)", 2500, 3500),
    ("largest reference file, tokens (loaded on demand)", 2000, 3000),
    ("fetchwright.py, lines", 600, 900),
    ("installed skills folder, KB", 150, 400),
    ("tracked repository, KB", 1024, 3072),
]


def measure():
    descs, skill_md, refs, files = [], [], [], []
    for skill in SKILLS:
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        m = re.search(r'^description:\s*"(.*)"\s*$', text, re.M)
        descs.append((len(m.group(1)) if m else 0, skill.name))
        skill_md.append((len(text.encode("utf-8")) // 4, skill.name))
        refs += [(p.stat().st_size // 4, f"{skill.name}/{p.name}") for p in (skill / "references").glob("*.md")]
        files += [p for p in skill.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    cli = ROOT / "skills" / "fetchwright" / "scripts" / "fetchwright.py"
    cli_lines = len(cli.read_text(encoding="utf-8").splitlines())
    folder_kb = sum(p.stat().st_size for p in files) // 1024
    try:
        tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.split(b"\0")
        repo_kb = sum((ROOT / t.decode()).stat().st_size for t in tracked if t and (ROOT / t.decode()).exists()) // 1024
    except (OSError, subprocess.CalledProcessError):
        repo_kb = folder_kb
    return [max(descs), (sum(d for d, _ in descs), ""), max(skill_md), max(refs or [(0, "")]),
            (cli_lines, ""), (folder_kb, ""), (repo_kb, "")]


def main():
    rows = []
    for (label, g, y), (v, where) in zip(BUDGETS, measure()):
        status = "green" if v <= g else ("yellow" if v <= y else "red")
        rows.append({"measure": label, "value": v, "green": g, "yellow": y, "status": status, "worst": where})
    overall = "red" if any(r["status"] == "red" for r in rows) else ("yellow" if any(r["status"] == "yellow" for r in rows) else "green")
    if "--json" in sys.argv:
        print(json.dumps({"overall": overall, "rows": rows}, indent=2))
    else:
        for r in rows:
            print("%-70s %6s  green<=%-5s yellow<=%-5s %-6s %s" % (r["measure"], r["value"], r["green"], r["yellow"], r["status"], r["worst"]))
        print("budget: %s" % overall.upper())
    return 2 if overall == "red" else 0


if __name__ == "__main__":
    sys.exit(main())
