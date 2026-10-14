# Player stats backend

Run from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Request `GET /players/76561198833875502`, or use http://127.0.0.1:8000/docs.
The ID must be a Steam64 ID, not a match UUID.

The response is a list of matches, each containing only `map_name`,
`player_name`, `mode`, `result` (`win`, `loss`, or `draw`), `kills`, and `deaths`.
`mode` is the API's `data_source` value, such as `matchmaking`.
`leetify_rating` is the player's per-game performance rating, multiplied
by 100 and rounded to two decimals for display (for example, 0.0625 becomes 6.25).
Matches without the requested player's stats are omitted.

`rank` and `rank_type` describe historical ranks matched by game ID
from the profile's `recent_matches`: Premier rating (`premier`), FACEIT
level (`faceit_level`), or the numeric competitive rank (`competitive`).
Ranks are null for matches missing from the profile's recent history or
unsupported modes. Current profile ranks are never substituted for
historical values. Each result also includes `has_banned_player`.

Upstream requests use `/v3/profile` and `/v3/profile/matches` with `steam64_id`.
Official API reference: https://api-public-docs.cs-prod.leetify.com/
