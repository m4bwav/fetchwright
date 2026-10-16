"""Offline tests for fetchwright.py. No network: responses are built here in the shape the Interactions API returned
on 2026-10-15 (steps url_context_call, url_context_result, thought, model_output), with invented text and handles.
Run from the repository root: python tests/test_fetchwright.py"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "fetchwright", "scripts"))
import fetchwright as fw  # noqa: E402

THREAD = "https://www.reddit.com/r/examplesub/comments/1abc234/"
SLUG = "https://www.reddit.com/r/examplesub/comments/1abc234/a_made_up_title/"
PAGE = "https://example.org/article"


def interaction(answer, retrieval=(("success", SLUG), ("error", THREAD)), page_tokens=4000):
    """A response shaped like the real ones. `answer` is a dict (sent as JSON text) or a raw string."""
    text = answer if isinstance(answer, str) else json.dumps(answer)
    return {
        "id": "v1_synthetic", "status": "completed", "object": "interaction", "model": "gemini-test",
        "usage": {"total_tokens": 100 + page_tokens + 500, "total_input_tokens": 100, "total_output_tokens": 500,
                  "total_tool_use_tokens": page_tokens, "total_thought_tokens": 0},
        "steps": [
            {"id": "call_1", "signature": "x", "type": "url_context_call", "arguments": {"urls": [THREAD]}},
            {"call_id": "call_1", "signature": "x", "type": "url_context_result", "is_error": False,
             "result": [{"url": u, "status": s} for s, u in retrieval]},
            {"signature": "x", "type": "thought"},
            {"type": "model_output", "content": [{"type": "text", "text": text}]},
        ],
    }


GOOD_THREAD = {
    "read_ok": True, "why_not": "", "title": "Invented title about a tool",
    "body": "I made a small tool.\n\nIt does one thing.",
    "comments": [
        {"text": "This works well on my machine.", "author_is_op": False},
        {"text": "Thanks, glad it helps.", "author_is_op": True},
        {"text": "Invented_Handle_1234", "author_is_op": False},
        {"text": "Comment removed by moderator", "author_is_op": False},
        {"text": "Comment deleted by user", "author_is_op": False},
        {"text": "Comment removed by moderator Does it run on Linux too?", "author_is_op": False},
        {"text": "   ", "author_is_op": False},
        {"text": "Great work!", "author_is_op": False},
    ],
}


class FakePost:
    """Stands in for http_post: returns queued (status, data) pairs and records the bodies sent."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.bodies = []

    def __call__(self, url, body, key, timeout):
        self.bodies.append(body)
        status, data = self.responses.pop(0)
        return status, data, 0.1


def run_cli(argv, post, env=None):
    out, err = io.StringIO(), io.StringIO()
    env = {"GEMINI_API_KEY": "test-key-not-real"} if env is None else env
    with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(fw, "http_post", post), \
            mock.patch.object(fw, "_registry_key", lambda name: ""), mock.patch.object(fw.time, "sleep", lambda s: None), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fw.main(argv)
    return code, out.getvalue(), err.getvalue()


class RequestTests(unittest.TestCase):
    def test_body_has_url_context_and_store_false(self):
        body = fw.build_body("m", "read it")
        self.assertEqual(body["tools"], [{"type": "url_context"}])
        self.assertIs(body["store"], False)

    def test_google_search_is_refused_in_any_spelling(self):
        for tool in ({"type": "google_search"}, {"google_search": {}}, {"googleSearch": {}},
                     {"type": "google-search"}, {"google_search_retrieval": {}}):
            with self.assertRaises(ValueError):
                fw.build_body("m", "x", tools=[{"type": "url_context"}, tool])

    def test_no_request_sent_by_read_carries_search(self):
        post = FakePost((200, interaction(GOOD_THREAD)))
        run_cli(["read", THREAD, "--json"], post)
        for body in post.bodies:
            self.assertNotIn("google_search", json.dumps(body).lower())
            self.assertNotIn("googlesearch", json.dumps(body).lower())

    def test_key_is_never_printed(self):
        key = "fake-SECRET-test-value-123"
        post = FakePost((200, interaction(GOOD_THREAD)))
        code, out, err = run_cli(["read", THREAD, "--json"], post, env={"GEMINI_API_KEY": key})
        self.assertEqual(code, 0)
        self.assertNotIn(key, out + err)
        post = FakePost((200, {"steps": []}), (200, {"steps": []}))
        code, out, err = run_cli(["check"], post, env={"GEMINI_API_KEY": key})
        self.assertNotIn(key, out + err)
        self.assertIn("GEMINI_API_KEY", out)

    def test_gemini_key_is_preferred_over_google_key(self):
        with mock.patch.dict(os.environ, {"GOOGLE_API_KEY": "g", "GEMINI_API_KEY": "m"}, clear=True):
            self.assertEqual(fw.find_key()[0], "m")
        with mock.patch.dict(os.environ, {"GOOGLE_API_KEY": "g"}, clear=True), \
                mock.patch.object(fw, "_registry_key", lambda name: ""):
            self.assertEqual(fw.find_key(), ("g", "environment variable GOOGLE_API_KEY"))

    def test_registry_fallback_names_the_source(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(fw, "_registry_key", lambda name: "r" if name == "GEMINI_API_KEY" else ""):
            key, where = fw.find_key()
        self.assertEqual(key, "r")
        self.assertIn("after this shell started", where)

    def test_no_key_exits_4_without_sending(self):
        post = FakePost()
        code, out, err = run_cli(["read", THREAD], post, env={})
        self.assertEqual(code, fw.EXIT_KEY)
        self.assertEqual(post.bodies, [])
        self.assertIn("GEMINI_API_KEY", err)

    def test_non_http_url_is_refused(self):
        code, _, err = run_cli(["read", "file:///etc/passwd"], FakePost())
        self.assertEqual(code, fw.EXIT_USAGE)


class FallbackTests(unittest.TestCase):
    def test_503_then_success_uses_second_model(self):
        post = FakePost((503, {"error": {"code": 503, "message": "high demand"}}), (200, interaction(GOOD_THREAD)))
        code, out, _ = run_cli(["read", THREAD, "--json", "--models", "a,b"], post)
        r = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(r["model"], "b")
        self.assertEqual([t["outcome"] for t in r["models_tried"]], ["next", "ok"])
        self.assertEqual([b["model"] for b in post.bodies], ["a", "b"])

    def test_dropped_connection_moves_on(self):
        post = FakePost(("net", {"error": {"message": "RemoteDisconnected: closed"}}), (200, interaction(GOOD_THREAD)))
        code, out, _ = run_cli(["read", THREAD, "--json", "--models", "a,b"], post)
        self.assertEqual(json.loads(out)["model"], "b")

    def test_404_model_gone_moves_on(self):
        post = FakePost((404, {"error": {"message": "no longer available to new users"}}), (200, interaction(GOOD_THREAD)))
        code, out, _ = run_cli(["read", THREAD, "--json", "--models", "a,b"], post)
        self.assertEqual(code, 0)

    def test_every_model_down_exits_5(self):
        post = FakePost((503, {"error": {"message": "x"}}), ("net", {"error": {"message": "y"}}))
        code, out, _ = run_cli(["read", THREAD, "--json", "--models", "a,b"], post)
        self.assertEqual(code, fw.EXIT_DOWN)
        self.assertFalse(json.loads(out)["read_ok"])

    def test_429_stops_the_whole_run(self):
        post = FakePost((429, {"error": {"code": "rate_limit_exceeded", "message": "slow down"}}))
        code, out, err = run_cli(["read", THREAD, PAGE, "--json", "--models", "a,b"], post)
        self.assertEqual(code, fw.EXIT_RATE)
        self.assertEqual(len(post.bodies), 1)
        self.assertIn("429", err)

    def test_403_and_bad_key_stop(self):
        for status, msg in ((403, "The caller does not have permission"), (400, "API key not valid"),
                            (402, "Payment Required")):
            post = FakePost((status, {"error": {"message": msg}}))
            code, _, _ = run_cli(["read", THREAD, "--models", "a,b"], post)
            self.assertEqual(code, fw.EXIT_KEY, status)
            self.assertEqual(len(post.bodies), 1)

    def test_recitation_block_retries_as_digest(self):
        page = {"read_ok": True, "why_not": "", "title": "An article", "text": "It covers three sections."}
        post = FakePost((400, {"error": {"message": "Request blocked due to copyright/recitation content."}}),
                        (200, interaction(page, retrieval=(("success", PAGE),))))
        code, out, _ = run_cli(["read", PAGE, "--verbatim", "--json", "--models", "a"], post)
        r = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(r["style"], "digest")
        self.assertIn("word for word", post.bodies[0]["input"])
        self.assertIn("faithful", post.bodies[1]["input"])


class ResultTests(unittest.TestCase):
    def test_thread_cleaning(self):
        r = fw.build_result(THREAD, "thread", "m", interaction(GOOD_THREAD), [])
        self.assertTrue(r["read_ok"])
        texts = [c["text"] for c in r["comments"]]
        self.assertEqual(texts, ["This works well on my machine.", "Thanks, glad it helps.",
                                 "Does it run on Linux too?", "Great work!"])
        self.assertEqual(r["dropped"], {"placeholder": 2, "lone_token": 1, "empty": 1})
        self.assertTrue(r["comments"][1]["author_is_op"])
        self.assertNotIn("Invented_Handle_1234", json.dumps(r))

    def test_lone_token_shapes(self):
        # A lone word ("lol") cannot be told from a handle, so it goes too; one word gives a note nothing to use.
        for handle in ("Invented_Handle_1234", "Some-Name-99", "lowercasename", "u/somebody", "CamelCaseName", "lol"):
            self.assertTrue(fw.LONE_TOKEN.fullmatch(handle), handle)
        for text in ("Great work!", "ok", "🤣", "Two words", "This?"):
            self.assertFalse(fw.LONE_TOKEN.fullmatch(text), text)

    def test_removed_post_body(self):
        answer = dict(GOOD_THREAD, body="[removed]")
        r = fw.build_result(THREAD, "thread", "m", interaction(answer), [])
        self.assertEqual(r["body"], "")
        self.assertTrue(r["body_removed"])

    def test_statuses_are_recorded(self):
        r = fw.build_result(THREAD, "thread", "m", interaction(GOOD_THREAD), [])
        self.assertEqual(r["retrieval"], [{"url": SLUG, "status": "success"}, {"url": THREAD, "status": "error"}])
        self.assertEqual(r["new_statuses"], [])
        self.assertEqual(r["usage"]["page"], 4000)

    def test_unknown_status_is_flagged(self):
        r = fw.build_result(THREAD, "thread", "m", interaction(GOOD_THREAD, retrieval=(("success", SLUG), ("blocked_x", THREAD))), [])
        self.assertEqual(r["new_statuses"], ["blocked_x"])

    def test_text_without_successful_retrieval_is_discarded(self):
        r = fw.build_result(THREAD, "thread", "m", interaction(GOOD_THREAD, retrieval=(("error", THREAD),)), [])
        self.assertFalse(r["read_ok"])
        self.assertEqual(r["comments"], [])
        self.assertIn("discarded", r["why_not"])

    def test_no_retrieval_step_at_all_is_discarded(self):
        data = interaction(GOOD_THREAD)
        data["steps"] = [s for s in data["steps"] if s["type"] != "url_context_result"]
        self.assertFalse(fw.build_result(THREAD, "thread", "m", data, [])["read_ok"])

    def test_model_says_not_read(self):
        answer = {"read_ok": False, "why_not": "Not able to browse the provided URL.", "title": "", "body": "", "comments": []}
        r = fw.build_result(THREAD, "thread", "m", interaction(answer, retrieval=(("error", THREAD),)), [])
        self.assertFalse(r["read_ok"])
        self.assertIn("Not able to browse", r["why_not"])

    def test_json_in_code_fences_and_prose(self):
        fenced = "```json\n" + json.dumps(GOOD_THREAD) + "\n```"
        self.assertEqual(fw.extract_json(fenced)["title"], GOOD_THREAD["title"])
        self.assertEqual(fw.extract_json("Here it is: " + json.dumps(GOOD_THREAD) + " done")["title"], GOOD_THREAD["title"])
        self.assertIsNone(fw.extract_json("no json here"))
        self.assertIsNone(fw.extract_json("[1, 2]"))

    def test_unparsed_answer(self):
        r = fw.build_result(THREAD, "thread", "m", interaction("I could not format that."), [])
        self.assertFalse(r["read_ok"])
        self.assertIn("unparsed", r)

    def test_page_mode(self):
        page = {"read_ok": True, "why_not": "", "title": "An article", "text": "First section.\n\nSecond section."}
        r = fw.build_result(PAGE, "page", "m", interaction(page, retrieval=(("success", PAGE),)), [], "digest")
        self.assertEqual(r["text"], "First section.\n\nSecond section.")
        self.assertNotIn("comments", r)

    def test_thread_url_detection(self):
        self.assertTrue(fw.is_thread_url(THREAD))
        self.assertTrue(fw.is_thread_url("https://old.reddit.com/r/x/comments/abc/"))
        self.assertTrue(fw.is_thread_url("https://news.ycombinator.com/item?id=1"))
        self.assertFalse(fw.is_thread_url("https://www.reddit.com/r/x/"))
        self.assertFalse(fw.is_thread_url(PAGE))


class OutputTests(unittest.TestCase):
    def test_text_output(self):
        post = FakePost((200, interaction(GOOD_THREAD)))
        code, out, _ = run_cli(["read", THREAD], post)
        self.assertIn("# Invented title about a tool", out)
        self.assertIn("[OP] Thanks, glad it helps.", out)
        self.assertIn("dropped 2 placeholders, 1 lone usernames or words, 1 empty", out)
        self.assertIn("retrieval: success " + SLUG, out)

    def test_digest_is_labelled(self):
        page = {"read_ok": True, "why_not": "", "title": "An article", "text": "Account."}
        post = FakePost((200, interaction(page, retrieval=(("success", PAGE),))))
        _, out, _ = run_cli(["read", PAGE], post)
        self.assertIn("style: digest", out)
        self.assertIn("not quotes", out)

    def test_max_chars_cuts_and_out_writes_whole(self):
        long = dict(GOOD_THREAD, comments=[{"text": "A comment of some length number %d." % i} for i in range(400)])
        post = FakePost((200, interaction(long)))
        _, out, _ = run_cli(["read", THREAD, "--max-chars", "2000"], post)
        self.assertIn("[cut at 2000 characters", out)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "o.json")
            post = FakePost((200, interaction(long)))
            run_cli(["read", THREAD, "--json", "--out", path, "--max-chars", "2000"], post)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)["comments"]), 400)

    def test_several_urls_give_a_list(self):
        page = {"read_ok": True, "why_not": "", "title": "An article", "text": "Account."}
        post = FakePost((200, interaction(GOOD_THREAD)), (200, interaction(page, retrieval=(("success", PAGE),))))
        code, out, _ = run_cli(["read", THREAD, PAGE, "--json"], post)
        data = json.loads(out)
        self.assertEqual([r["mode"] for r in data], ["thread", "page"])

    def test_one_unread_page_exits_1(self):
        answer = {"read_ok": False, "why_not": "blocked", "title": "", "body": "", "comments": []}
        post = FakePost((200, interaction(GOOD_THREAD)), (200, interaction(answer, retrieval=(("error", PAGE),))))
        code, _, _ = run_cli(["read", THREAD, PAGE, "--thread"], post)
        self.assertEqual(code, fw.EXIT_UNREAD)

    def test_max_comments_reaches_the_instruction(self):
        post = FakePost((200, interaction(GOOD_THREAD)))
        run_cli(["read", THREAD, "--max-comments", "30"], post)
        self.assertIn("at most 30 comments", post.bodies[0]["input"])

    def test_save_raw(self):
        with tempfile.TemporaryDirectory() as d:
            post = FakePost((200, interaction(GOOD_THREAD)))
            run_cli(["read", THREAD, "--save-raw", d], post)
            files = os.listdir(d)
            self.assertEqual(len(files), 1)
            with open(os.path.join(d, files[0]), encoding="utf-8") as f:
                saved = f.read()
            self.assertNotIn("test-key-not-real", saved)

    def test_check_reports_models(self):
        post = FakePost((200, {"steps": []}), (503, {"error": {"message": "busy"}}))
        code, out, _ = run_cli(["check", "--models", "a,b", "--json"], post)
        report = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual([m["answers"] for m in report["models"]], [True, False])
        self.assertNotIn("tools", post.bodies[0])

    def test_check_no_call_sends_nothing(self):
        post = FakePost()
        code, out, _ = run_cli(["check", "--no-call"], post)
        self.assertEqual(code, 0)
        self.assertEqual(post.bodies, [])

    def test_models_from_environment(self):
        with mock.patch.dict(os.environ, {"FETCHWRIGHT_MODELS": "x, y"}, clear=True):
            self.assertEqual(fw.model_list(None), ["x", "y"])
        self.assertEqual(fw.model_list("p,q"), ["p", "q"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
