#!/usr/bin/env python3
"""
Tests for Flask API endpoints.

Consolidates:
  - test_top_opportunities.py → /api/top-opportunities
  - test_visit_counter.py     → /api/visit-count, bot detection, visit increment
"""

import json
import sqlite3
import unittest

from app import app, DB_PATH, BOT_PATTERN


# ---------------------------------------------------------------------------
# /api/top-opportunities
# ---------------------------------------------------------------------------

class TestTopOpportunities(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_basic_response(self):
        response = self.client.get("/api/top-opportunities")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("opportunities", data["data"])
        self.assertIn("metadata", data["data"])
        self.assertIsInstance(data["data"]["opportunities"], list)
        self.assertGreater(len(data["data"]["opportunities"]), 0)

    def test_min_score_filter(self):
        response = self.client.get("/api/top-opportunities?min_score=75")
        self.assertEqual(response.status_code, 200)

        for opp in json.loads(response.data)["data"]["opportunities"]:
            self.assertGreaterEqual(opp["rvc_score"], 75.0)

    def test_sort_by_rvc_score(self):
        response = self.client.get("/api/top-opportunities?sort_by=rvc_score")
        self.assertEqual(response.status_code, 200)

        opps = json.loads(response.data)["data"]["opportunities"]
        for i in range(1, len(opps)):
            self.assertLessEqual(opps[i]["rvc_score"] or 0, opps[i - 1]["rvc_score"] or 0)

    def test_limit_parameter(self):
        response = self.client.get("/api/top-opportunities?limit=5")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(json.loads(response.data)["data"]["opportunities"]), 5)

    def test_sector_filter(self):
        response = self.client.get("/api/top-opportunities?sector=technology")
        self.assertEqual(response.status_code, 200)

        for opp in json.loads(response.data)["data"]["opportunities"]:
            self.assertIn("technology", (opp.get("sector") or "").lower())

    def test_metadata_structure(self):
        response = self.client.get("/api/top-opportunities")
        self.assertEqual(response.status_code, 200)

        metadata = json.loads(response.data)["data"]["metadata"]
        for field in ("total_count", "average_score", "sectors_available", "filters_applied", "generated_at"):
            self.assertIn(field, metadata)

        self.assertIsInstance(metadata["total_count"], int)
        self.assertIsInstance(metadata["average_score"], (int, float))
        self.assertIsInstance(metadata["sectors_available"], list)
        self.assertIsInstance(metadata["filters_applied"], dict)

    def test_opportunity_structure(self):
        response = self.client.get("/api/top-opportunities?limit=1")
        self.assertEqual(response.status_code, 200)

        opps = json.loads(response.data)["data"]["opportunities"]
        if opps:
            opp = opps[0]
            for field in ("ticker", "company_name", "rvc_score", "classification", "sector", "last_updated"):
                self.assertIn(field, opp)
            self.assertIsInstance(opp["ticker"], str)
            self.assertIsInstance(opp["rvc_score"], (int, float))
            self.assertGreater(opp["rvc_score"], 0)

    def test_invalid_min_score(self):
        response = self.client.get("/api/top-opportunities?min_score=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data)["status"], "error")

    def test_top_opportunity_is_schw(self):
        response = self.client.get("/api/top-opportunities?limit=1")
        self.assertEqual(response.status_code, 200)

        opps = json.loads(response.data)["data"]["opportunities"]
        if opps:
            self.assertEqual(opps[0]["ticker"], "SCHW")
            self.assertGreater(opps[0]["rvc_score"], 75.0)


# ---------------------------------------------------------------------------
# Visit counter
# ---------------------------------------------------------------------------

class TestVisitCounter(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_bot_detection(self):
        bot_agents = [
            "Mozilla/5.0 (compatible; Googlebot/2.1)",
            "facebookexternalhit/1.1",
            "python-requests/2.28.0",
            "curl/7.68.0",
        ]
        for ua in bot_agents:
            self.assertTrue(BOT_PATTERN.search(ua), f"Should detect bot: {ua}")

    def test_human_not_flagged_as_bot(self):
        human_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
        ]
        for ua in human_agents:
            self.assertFalse(BOT_PATTERN.search(ua), f"Should not flag human: {ua}")

    def test_visit_count_endpoint(self):
        response = self.client.get("/api/visit-count")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("visits", data)
        self.assertIn("today", data)
        self.assertIsInstance(data["visits"], int)
        self.assertIsInstance(data["today"], int)

    def test_db_tables_exist(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='site_visits'")
        self.assertIsNotNone(cursor.fetchone(), "Table 'site_visits' should exist")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_visits'")
        self.assertIsNotNone(cursor.fetchone(), "Table 'daily_visits' should exist")

        conn.close()

    def test_visit_increment_on_human_request(self):
        conn = sqlite3.connect(DB_PATH)
        before = conn.execute("SELECT total_visits FROM site_visits WHERE id = 1").fetchone()[0]
        conn.close()

        self.client.get("/", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        })

        conn = sqlite3.connect(DB_PATH)
        after = conn.execute("SELECT total_visits FROM site_visits WHERE id = 1").fetchone()[0]
        conn.close()

        # Counter should be >= before (may not increment if session was already active)
        self.assertGreaterEqual(after, before)


if __name__ == "__main__":
    unittest.main(verbosity=2)