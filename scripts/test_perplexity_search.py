"""
Unit and Integration Tests for Perplexity Search API module.
"""

import os
import unittest
from perplexity_search import (
    PerplexitySearchClient,
    SearchResult,
    deduplicate_results,
    normalize_url,
    search_web
)


class TestPerplexitySearchUnit(unittest.TestCase):

    def test_normalize_url(self):
        self.assertEqual(normalize_url("https://EXAMPLE.com/page/"), "https://example.com/page")
        self.assertEqual(normalize_url("http://example.org/test#heading"), "http://example.org/test")
        self.assertEqual(normalize_url("https://site.com/item?id=123#ref"), "https://site.com/item?id=123")

    def test_deduplicate_results(self):
        items = [
            SearchResult(title="Doc 1", url="https://example.com/item", snippet="Snippet 1"),
            SearchResult(title="Doc 1 Duplicate", url="https://example.com/item/", snippet="Snippet 1 Dup"),
            SearchResult(title="Doc 2", url="https://example.com/other", snippet="Snippet 2"),
            SearchResult(title="Doc 2 Fragment", url="https://example.com/other#section", snippet="Snippet 2 Frag")
        ]
        deduped = deduplicate_results(items)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0].title, "Doc 1")
        self.assertEqual(deduped[1].title, "Doc 2")

    def test_query_validation(self):
        client = PerplexitySearchClient()
        with self.assertRaises(ValueError):
            client.search(query="")
        with self.assertRaises(ValueError):
            client.search(query=[])
        with self.assertRaises(ValueError):
            client.search(query=["1", "2", "3", "4", "5", "6"])


class TestPerplexitySearchLive(unittest.TestCase):

    def test_single_query_smoke(self):
        resp = search_web("CFPB Regulation Z", max_results=2, country="US")
        self.assertIsNotNone(resp)
        self.assertGreater(len(resp.results), 0)
        self.assertIsNotNone(resp.results[0].title)
        self.assertIsNotNone(resp.results[0].url)
        self.assertIsNotNone(resp.results[0].snippet)

    def test_domain_filter(self):
        resp = search_web(
            query="buy now pay later rules",
            max_results=3,
            search_domain_filter=["consumerfinance.gov"]
        )
        self.assertGreater(len(resp.results), 0)
        for r in resp.results:
            self.assertIn("consumerfinance.gov", r.url.lower())

    def test_multi_query_deduped(self):
        queries = [
            "Affirm CFPB dispute resolution",
            "CFPB Buy Now Pay Later interpretive rule"
        ]
        resp = search_web(query=queries, max_results=3)
        self.assertGreater(len(resp.results), 0)
        urls = [r.url for r in resp.results]
        self.assertEqual(len(urls), len(set(urls)), "Results must be unique by URL")


if __name__ == "__main__":
    unittest.main()
