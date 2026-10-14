# Match history

A React + Vite match history frontend backed by FastAPI and Leetify's public API.
Cards show the map, player, mode, result, kills/deaths, and per-game Leetify rating.
Search by map, player, mode or result and choose how many recent matches to show.
Search runs across the available history before the count limit is applied.
FastAPI owns sorting, searching, count limits, display labels and summary
calculations in `backend/history.py`. React sends query parameters and renders
the response; it does not calculate match statistics.

The UI uses `/players/{steam64_id}/history?search=mirage&limit=20` (through the
`/api` proxy). Its response contains `matches`, `summary`, `available_count`,
and `matching_count`. Allowed limits are 5, 10, 20, 50, 100, or `all`.
The original `/players/{steam64_id}` endpoint still returns the raw match list.
Each history request fetches fresh data from Leetify; there is no database or
server cache yet. Search requests are debounced in the browser.

Run backend checks with `.venv/bin/python -m unittest backend.test_history`.

## Run locally

Use Node 22.12+ (or Node 24) and Python 3.10+.
From the project root, start the backend:

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/main.py
```

If you have no virtual environment yet, create it with `python -m venv .venv` first.
In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Enter a Steam64 ID and click **Load matches**.
Vite forwards `/api` requests to FastAPI on port 8000, so CORS configuration
isn't required. The lookup initially contains the ID used during development;
no player data is fetched until you submit it.

Frontend source is in `frontend/src/App.jsx` and `frontend/src/styles.css`.
Run `npm run build` inside `frontend` to produce `dist/`.
`npm run preview` previews that build and also proxies to the local backend.

## Docker Compose

From the project root, build and start both services:

```bash
docker compose up --build -d
```

Open http://localhost:8080. No local Python or Node installation is needed
when running with Docker Compose.

The frontend serves the production Vite build through Nginx and forwards
`/api` requests to the backend over Compose's internal network. Only port
8080 is published. Both services have health checks; the frontend waits
for the backend to become healthy before starting.

View logs or stop the app:

```bash
docker compose logs -f
docker compose down
```

After changing code, run `docker compose up --build -d` again to rebuild.
To use another host port, change `8080:8080` in `compose.yaml` (for example,
`3000:8080` serves the app at http://localhost:3000).

## Data notes

- FACEIT historical rank is a **level**, not Elo. Competitive ranks are numeric.
- Missing or zero ranks display as unavailable; current rank is not used as a fallback.
- Match Leetify ratings are multiplied by 100 for display (0.0625 → +6.25).
- Win rate, total kills divided by total deaths, and average match rating use only displayed matches.
- Match counts are limited to the history returned by Leetify; choosing 100 cannot fetch missing matches.
- Match history and rank availability depend on Leetify's response and profile privacy.

This is an independent project using Leetify data, not an official Leetify app.

## CI and GHCR images

Pushing to `main` or `dev` runs `.github/workflows/ci.yml` and builds both
Dockerfiles. The backend tests run before publishing the backend image;
the frontend Docker build installs dependencies and builds the Vite app.

The workflow publishes exactly two image packages:

- `ghcr.io/kebertr/leetify-tracking-frontend`
- `ghcr.io/kebertr/leetify-tracking-backend`

A `main` push tags each image with `prod-<short-commit-sha>` and `latest`.
A `dev` push tags each image with `dev-<short-commit-sha>` and `dev`.
Both services are rebuilt on every push to those branches.

Authentication uses the automatic `GITHUB_TOKEN` with `packages: write`;
no personal access token is needed for the workflow. Image names follow the
repository name automatically and are converted to lowercase for GHCR.
The workflow publishes images only; it does not deploy or restart your app.
Local Docker Compose still builds from source.
