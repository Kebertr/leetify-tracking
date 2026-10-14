import { useEffect, useState } from "react";

function MatchCard({ match }) {
  return (
    <article className="match-card">
      <div className="card-heading">
        <h3>{match.map_label}</h3>
        <span className={`result ${match.result}`}>{match.result}</span>
      </div>
      <p className="match-meta">
        {match.player_name} · {match.mode_label}
      </p>
      <dl className="match-stats">
        <div>
          <dt>Kills</dt>
          <dd>{match.kills}</dd>
        </div>
        <div>
          <dt>Deaths</dt>
          <dd>{match.deaths}</dd>
        </div>
        <div>
          <dt>Match rating</dt>
          <dd>{match.rating_label}</dd>
        </div>
      </dl>
      {match.finished_at && (
        <time dateTime={match.finished_at}>
          {new Date(match.finished_at).toLocaleString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </time>
      )}
    </article>
  );
}

export default function App() {
  const [playerId, setPlayerId] = useState("76561198833875502");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [limit, setLimit] = useState("20");
  const [activePlayer, setActivePlayer] = useState("");
  const [refresh, setRefresh] = useState(0);

  function loadPlayer(event) {
    event.preventDefault();
    setActivePlayer(playerId.trim());
    setRefresh((value) => value + 1);
  }

  useEffect(() => {
    if (!activePlayer) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setData(null);

    // Debounce typing; the backend performs the search and calculations.
    const timer = setTimeout(async () => {
      try {
        const params = new URLSearchParams({ search, limit });
        const response = await fetch(
          `/api/players/${activePlayer}/history?${params}`,
          {
            signal: controller.signal,
          },
        );
        if (!response.ok) {
          if (response.status === 429)
            throw new Error("Too many requests. Try again shortly.");
          if (response.status === 404)
            throw new Error("No public match history found for this player.");
          throw new Error(
            "Could not load matches. Check your player ID and try again.",
          );
        }
        const result = await response.json();
        if (!controller.signal.aborted) setData(result);
      } catch (err) {
        if (!controller.signal.aborted) setError(err.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 300);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [activePlayer, search, limit, refresh]);

  return (
    <main>
      <div className="page-title">
        <h1>Recent matches</h1>
        <p>Player performance, one match at a time.</p>
      </div>
      <form className="lookup" onSubmit={loadPlayer}>
        <label htmlFor="player-id">Steam64 ID</label>
        <div className="lookup-controls">
          <input
            id="player-id"
            value={playerId}
            onChange={(event) => setPlayerId(event.target.value)}
            pattern="[0-9]+"
            inputMode="numeric"
            title="Enter a numeric Steam ID"
            required
          />
          <button disabled={loading} type="submit">
            {loading ? "Loading…" : "Load matches"}
          </button>
        </div>
      </form>

      <div className="filters">
        <label className="search">
          Search matches
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Map, player, mode or result"
          />
        </label>
        <label>
          Show matches
          <select
            value={limit}
            onChange={(event) => setLimit(event.target.value)}
          >
            <option value="5">Latest 5</option>
            <option value="10">Latest 10</option>
            <option value="20">Latest 20</option>
            <option value="50">Latest 50</option>
            <option value="100">Latest 100</option>
            <option value="all">All available</option>
          </select>
        </label>
      </div>

      <section
        className="summary"
        aria-label="Statistics for displayed matches"
      >
        <div>
          <span>Matches shown</span>
          <strong>{data?.summary.match_count ?? "—"}</strong>
        </div>
        <div>
          <span>Win rate</span>
          <strong>{data?.summary.win_rate_label ?? "—"}</strong>
        </div>
        <div>
          <span>Kill / death ratio</span>
          <strong>{data?.summary.kd_ratio_label ?? "—"}</strong>
        </div>
        <div>
          <span>Avg. match rating</span>
          <strong>{data?.summary.average_rating_label ?? "—"}</strong>
        </div>
      </section>
      <p className="summary-note">
        Statistics use only the matches shown below.
        {data && ` ${data.available_count} matches available from Leetify.`}
      </p>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <section
        aria-label="Recent match results"
        aria-live="polite"
        aria-busy={loading}
      >
        {loading ? (
          <p className="empty-state">Loading match history…</p>
        ) : data?.matches.length ? (
          <div className="match-grid">
            {data.matches.map((match, index) => (
              <MatchCard key={match.match_id || index} match={match} />
            ))}
          </div>
        ) : (
          <p className="empty-state">
            {data
              ? "No matches found. Try another search."
              : "Load a player to view their recent matches."}
          </p>
        )}
      </section>
      <footer>
        Match data from{" "}
        <a href="https://leetify.com" target="_blank" rel="noreferrer">
          Leetify
        </a>
      </footer>
    </main>
  );
}
