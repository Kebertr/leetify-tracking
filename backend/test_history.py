import unittest
from unittest.mock import AsyncMock, patch

import httpx

from backend.history import match_history
from backend.main import app


def sample_matches():
    return [
        {
            "match_id": str(index),
            "finished_at": f"2026-10-{20-index:02}T12:00:00Z",
            "map_name": "de_mirage" if index < 6 else "de_nuke",
            "mode": "faceit",
            "rank_type": "faceit_level",
            "player_name": "Test player",
            "result": "win" if index < 6 else "loss",
            "kills": 20 if index < 6 else 10,
            "deaths": 10,
            "leetify_rating": 4 if index < 6 else -2,
        }
        for index in range(12)
    ]


class HistoryTests(unittest.TestCase):
    def test_limit_and_sort_determine_summary(self):
        result = match_history(list(reversed(sample_matches())), limit=5)
        self.assertEqual(result["matches"][0]["match_id"], "0")
        self.assertEqual(result["summary"]["match_count"], 5)
        self.assertEqual(result["summary"]["win_rate"], 100)
        self.assertEqual(result["summary"]["kd_ratio"], 2)
        self.assertEqual(result["summary"]["average_rating"], 4)

    def test_search_before_limit(self):
        result = match_history(sample_matches(), "NUKE faceit loss", 5)
        self.assertEqual(result["matching_count"], 6)
        self.assertEqual(result["available_count"], 12)
        self.assertEqual(result["summary"]["match_count"], 5)
        self.assertEqual(result["summary"]["win_rate"], 0)
        self.assertEqual(result["summary"]["average_rating"], -2)

    def test_all_and_empty(self):
        result = match_history(sample_matches(), limit=None)
        self.assertEqual(result["summary"]["kd_ratio"], 1.5)
        self.assertEqual(result["summary"]["win_rate"], 50)
        empty = match_history(sample_matches(), "missing")
        self.assertEqual(empty["matches"], [])
        self.assertIsNone(empty["summary"]["average_rating"])
        self.assertEqual(empty["summary"]["kd_ratio_label"], "—")

    def test_no_deaths_is_json_safe(self):
        matches = sample_matches()[:1]
        matches[0]["deaths"] = 0
        result = match_history(matches)
        self.assertIsNone(result["summary"]["kd_ratio"])
        self.assertEqual(result["summary"]["kd_ratio_label"], "∞")


class EndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_numeric_ids_have_no_fixed_length(self):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            with patch("backend.main.player_stats", new=AsyncMock(return_value=[])) as fetch:
                for player_id in ("12345678", "76561198833875502", "123456789012345678"):
                    response = await client.get(f"/players/{player_id}/history")
                    self.assertEqual(response.status_code, 200)
                    fetch.assert_awaited_with(player_id)

    async def test_request_and_validation(self):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            with patch("backend.main.player_stats", new=AsyncMock(return_value=sample_matches())) as fetch:
                response = await client.get("/players/76561198833875502/history?search=nuke&limit=5")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["summary"]["match_count"], 5)
                self.assertEqual(response.json()["summary"]["win_rate_label"], "0%")
                fetch.reset_mock()
                for url in ("/players/invalid/history", "/players/76561198833875502/history?limit=-1"):
                    self.assertEqual((await client.get(url)).status_code, 422)
                fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
