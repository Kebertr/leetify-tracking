import httpx
from fastapi import FastAPI, Path, Query
from typing import Literal

if __package__:
    from .history import match_history
else:
    from history import match_history
from fastapi.responses import JSONResponse

app = FastAPI()
LEETIFY_URL = "https://api-public.cs-prod.leetify.com/v3"


@app.exception_handler(httpx.HTTPError)
async def leetify_error(request, error):
    status = 502
    if isinstance(error, httpx.HTTPStatusError) and error.response.status_code in (404, 429):
        status = error.response.status_code
    return JSONResponse(status_code=status, content={"detail": "Could not fetch Leetify data"})


@app.get("/healthz")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Welcome to the Leetify API"}


@app.get("/players/{steam64_id}")
async def player_stats(steam64_id: str):
    params = {"steam64_id": steam64_id}

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(f"{LEETIFY_URL}/profile", params=params)
        response.raise_for_status()
        profile = response.json()


        response = await client.get(f"{LEETIFY_URL}/profile/matches", params=params)
        response.raise_for_status()
        matches = response.json()

    ranks_by_match = {}
    for recent_match in profile["recent_matches"]:
        ranks_by_match[recent_match["id"]] = recent_match

    results = []
    for match in matches:
        recent_match = ranks_by_match.get(match["id"], {})
        rank = None
        rank_type = None

        if match["data_source"] == "matchmaking" and recent_match.get("rank_type") == 11:
            rank = recent_match.get("rank")
            rank_type = "premier"
        elif match["data_source"] == "faceit":
            rank = recent_match.get("rank")
            rank_type = "faceit_level"
        elif match["data_source"] == "matchmaking_competitive":
            rank = recent_match.get("rank")
            rank_type = "competitive"

        for player in match["stats"]:
            if player["steam64_id"] != steam64_id:
                continue

            won = player["rounds_won"]
            lost = player["rounds_lost"]

            if won > lost:
                result = "win"
            elif won < lost:
                result = "loss"
            else:
                result = "draw"

            results.append({
                "match_id": match["id"],
                "finished_at": match["finished_at"],
                "map_name": match["map_name"],
                "mode": match["data_source"],
                "has_banned_player": match["has_banned_player"],
                "player_name": player["name"],
                "result": result,
                "kills": player["total_kills"],
                "deaths": player["total_deaths"],
                "leetify_rating": round(player["leetify_rating"] * 100, 2),
                "rank": rank,
                "rank_type": rank_type,
            })

    return results


@app.get("/players/{steam64_id}/history")
async def player_history(
    steam64_id: str = Path(pattern=r"^[0-9]+$"),
    search: str = Query(default="", max_length=200),
    limit: Literal["5", "10", "20", "50", "100", "all"] = "20",
):
    matches = await player_stats(steam64_id)
    count = None if limit == "all" else int(limit)
    return match_history(matches, search, count)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
