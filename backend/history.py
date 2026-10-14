"""Prepare match history and statistics for display."""

MODE_NAMES = {
    "faceit": "FACEIT",
    "matchmaking": "Matchmaking",
    "matchmaking_competitive": "Competitive",
    "matchmaking_wingman": "Wingman",
}


def rating_text(value):
    if value is None:
        return "—"
    return f"{value:+.2f}" if value > 0 else f"{value:.2f}"


def match_history(matches, search="", limit=20):
    terms = search.lower().split()
    filtered = []

    for match in sorted(matches, key=lambda row: row.get("finished_at") or "", reverse=True):
        row = dict(match)
        map_name = row["map_name"]
        if map_name.startswith(("de_", "cs_")):
            map_name = map_name[3:]
        row["map_label"] = map_name.replace("_", " ").title()
        row["mode_label"] = "Premier" if row["rank_type"] == "premier" else MODE_NAMES.get(row["mode"], row["mode"])
        row["rating_label"] = rating_text(row["leetify_rating"])
        searchable = " ".join([
            row["map_name"], row["map_label"], row["player_name"],
            row["mode_label"], row["result"],
        ]).lower()
        if all(term in searchable for term in terms):
            filtered.append(row)

    shown = filtered if limit is None else filtered[:limit]
    count = len(shown)
    wins = sum(row["result"] == "win" for row in shown)
    kills = sum(row["kills"] for row in shown)
    deaths = sum(row["deaths"] for row in shown)
    ratings = [row["leetify_rating"] for row in shown if row["leetify_rating"] is not None]
    win_rate = round(wins / count * 100) if count else None
    kd_ratio = round(kills / deaths, 2) if deaths else None
    average_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
    kd_label = f"{kd_ratio:.2f}" if deaths else "∞" if kills else "—"

    return {
        "matches": shown,
        "available_count": len(matches),
        "matching_count": len(filtered),
        "summary": {
            "match_count": count,
            "win_rate": win_rate,
            "kd_ratio": kd_ratio,
            "average_rating": average_rating,
            "win_rate_label": f"{win_rate}%" if count else "—",
            "kd_ratio_label": kd_label,
            "average_rating_label": rating_text(average_rating),
        },
    }
