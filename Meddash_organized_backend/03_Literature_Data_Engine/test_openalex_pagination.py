"""Regression test: OpenAlex must request cursor pagination from page one."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("literature_engine.py")
spec = importlib.util.spec_from_file_location("literature_engine", MODULE_PATH)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class OpenAlexPaginationTest(unittest.TestCase):
    def test_fetches_all_pages_up_to_max_results(self):
        requests = []
        pages = {
            "*": ([1, 2], "next-a"),
            "next-a": ([3, 4], "next-b"),
            "next-b": ([5], None),
        }

        def fake_request(url, params):
            self.assertEqual(url, "https://api.openalex.org/works")
            cursor = params.get("cursor")
            requests.append(cursor)
            if cursor is None:
                # Mirrors OpenAlex: next_cursor is absent without cursor mode.
                return {"meta": {"count": 5}, "results": [
                    {"id": "https://openalex.org/W1", "title": "Paper 1"},
                    {"id": "https://openalex.org/W2", "title": "Paper 2"},
                ]}
            ids, next_cursor = pages[cursor]
            return {"meta": {"count": 5, "next_cursor": next_cursor},
                    "results": [{"id": f"https://openalex.org/W{i}", "title": f"Paper {i}"} for i in ids]}

        with patch.object(engine, "safe_request", side_effect=fake_request), \
             patch.object(engine.time, "sleep"):
            results, hits = engine.search_openalex("alopecia", max_results=5)

        self.assertEqual(hits, 5)
        self.assertEqual(len(results), min(hits, 5))
        self.assertEqual(requests, ["*", "next-a", "next-b"])


if __name__ == "__main__":
    unittest.main()
