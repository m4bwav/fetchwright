"""Live smoke test: one real read through Gemini's URL context tool. Skips when no key is set, so CI without a
secret passes. Sends one request (two if the first model is overloaded) for a public Wikipedia article.
Run from the repository root: python tests/smoke_live.py"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "skills", "fetchwright", "scripts", "fetchwright.py")
sys.path.insert(0, os.path.dirname(CLI))
import fetchwright as fw  # noqa: E402

URL = "https://en.wikipedia.org/wiki/Reddit"


@unittest.skipUnless(fw.find_key()[0], "no GEMINI_API_KEY: live smoke test skipped")
class LiveSmoke(unittest.TestCase):
    def test_read_a_public_page(self):
        proc = subprocess.run([sys.executable, "-I", CLI, "read", URL, "--json", "--max-chars", "0"],
                              capture_output=True, text=True, encoding="utf-8", timeout=400)
        if proc.returncode == fw.EXIT_RATE:
            self.skipTest("rate limited: " + proc.stderr.strip())
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout[:2000])
        r = json.loads(proc.stdout)
        self.assertTrue(r["read_ok"], r["why_not"])
        self.assertTrue(any(s["status"].lower() in fw.SUCCESS_STATUSES for s in r["retrieval"]), r["retrieval"])
        self.assertIn("reddit", (r["title"] + r["text"]).lower())
        self.assertGreater(r["usage"]["page"] or 0, 0)
        print(f"\nlive: {r['model']} {r['style']}, tried {[t['http'] for t in r['models_tried']]}, "
              f"page tokens {r['usage']['page']}, text {len(r['text'])} characters", file=sys.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
