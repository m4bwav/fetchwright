"""Offline tests for yt.py. No network: caption events and video data are invented here in yt-dlp's json3 shape.
Run from the repository root: python tests/test_yt.py"""
import contextlib
import io
import os
import sys
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "fetchwright", "scripts"))
import yt  # noqa: E402

VID = "abcDEF123_-"


class VideoId(unittest.TestCase):
    def test_forms(self):
        for u in (VID, f"https://www.youtube.com/watch?v={VID}&t=5s", f"https://youtu.be/{VID}",
                  f"https://www.youtube.com/shorts/{VID}", f"https://www.youtube.com/live/{VID}"):
            self.assertEqual(yt.video_id(u), VID)

    def test_bad(self):
        with self.assertRaises(SystemExit):
            yt.video_id("https://example.org/page")


class Times(unittest.TestCase):
    def test_stamp_and_parse(self):
        self.assertEqual(yt.stamp(65), "1:05")
        self.assertEqual(yt.stamp(3725), "1:02:05")
        self.assertEqual(yt.parse_time("1:02:05"), 3725)
        self.assertEqual(yt.parse_time("90"), 90)


class Json3(unittest.TestCase):
    def test_drops_empty_and_repeats(self):
        data = {"events": [
            {"tStartMs": 0, "segs": [{"utf8": "hello "}, {"utf8": "there"}]},
            {"tStartMs": 900, "segs": [{"utf8": "\n"}]},
            {"tStartMs": 1000, "segs": [{"utf8": "hello there"}]},
            {"tStartMs": 2500, "segs": [{"utf8": "next  line"}]},
            {"segs": [{"utf8": "no start"}]},
            {"tStartMs": 3000}]}
        self.assertEqual(yt.json3_lines(data), [(0.0, "hello there"), (2.5, "next line")])


def doc(chapters, auto=False):
    base = f"https://www.youtube.com/watch?v={VID}"
    lines = [(0, "intro words"), (61, "setup words"), (125, "result words")]
    return {"id": VID, "url": base, "title": "A made-up tutorial", "channel": "Example Channel",
            "upload_date": "20260101", "duration": 200, "links": ["https://example.org/x"], "chapters": chapters,
            "automatic_captions": auto,
            "transcript": [{"t": t, "at": yt.stamp(t), "link": f"{base}&t={t}s", "text": x} for t, x in lines]}


class Markdown(unittest.TestCase):
    def test_chapters_group_lines_with_links(self):
        md = yt.to_markdown(doc([{"start": 0, "title": "Intro"}, {"start": 60, "title": "Setup"},
                                 {"start": 120, "title": "Result"}]))
        self.assertIn(f"## [1:00](https://www.youtube.com/watch?v={VID}&t=60s) Setup", md)
        self.assertIn(f"[2:05](https://www.youtube.com/watch?v={VID}&t=125s) result words", md)
        setup = md.split("Setup")[1].split("## ")[0]
        self.assertIn("setup words", setup)
        self.assertNotIn("result words", setup)

    def test_no_chapters_and_auto_note(self):
        md = yt.to_markdown(doc([], auto=True))
        self.assertIn("Transcript", md)
        self.assertIn("Automatic captions", md)


class Route(unittest.TestCase):
    def test_read_needs_opt_in(self):
        env = {k: v for k, v in os.environ.items() if k != "FETCHWRIGHT_YT_ROUTE"}
        with unittest.mock.patch.dict(os.environ, env, clear=True), \
                unittest.mock.patch.object(sys, "argv", ["yt.py", "read", VID]), \
                unittest.mock.patch.object(yt, "fetch") as fetch, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                yt.main()
            fetch.assert_not_called()


class RateLimit(unittest.TestCase):
    def test_429_stops_with_advice(self):
        done = unittest.mock.Mock(returncode=1, stderr="ERROR: Unable to download video subtitles: HTTP Error 429: Too Many Requests")
        with unittest.mock.patch.object(yt.subprocess, "run", return_value=done) as run:
            with self.assertRaises(SystemExit) as cm:
                yt.fetch(VID, "en")
        self.assertEqual(run.call_count, 1)
        self.assertIn("429", str(cm.exception))
        self.assertIn("clip", str(cm.exception))

    def test_clip_timeout_stops_with_advice(self):
        env = unittest.mock.patch.dict(yt.os.environ, {"GEMINI_API_KEY": "test"})
        slow = unittest.mock.patch.object(yt.urllib.request, "urlopen", side_effect=TimeoutError)
        with env, slow as op:
            with self.assertRaises(SystemExit) as cm:
                yt.clip(f"https://www.youtube.com/watch?v={VID}", "0-480", "q")
        self.assertEqual(op.call_count, 1)
        self.assertIn("shorter span", str(cm.exception))


if __name__ == "__main__":
    import unittest.mock  # noqa: F401
    unittest.main()
