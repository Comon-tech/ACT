# ACT (Assistant of Comon Tech)

AI-powered Discord bot combining conversational AI with RPG features. Python 3.13, managed with `uv`.

## Architecture

Single `main.py` entrypoint wires up three independent components, each toggled on/off:

- `bot/` — Discord bot (`discord.py`). `bot/main.py` is the `ActBot` class; `bot/cogs/` holds feature cogs (`chat_cogs/` for AI chat, `game_cogs/` for RPG mechanics), `bot/ui/` holds embeds/modals/views.
- `api/` — FastAPI server (`api/main.py` + `api/routers/`).
- `db/` — MongoDB access via ODMantic (`db/main.py` is `ActDb`; other files are ODMantic models). Static game data (items, personas, ranks, stats) lives in `db/data/*.toml`.
- `utils/` — shared helpers: `log.py` (custom emoji-tagged logger, see below), `ai.py` (Gemini wrapper), `task.py` (`ActTaskManager` for scheduled/delayed async tasks), `audio.py`, `file.py`, `misc.py`, `xp.py`.

Which components run is controlled by `[tool.act.components]` in `pyproject.toml` (currently `bot`, `api`, `db` all `true`), with CLI flags `-b`/`-a`/`-d` in `main.py`. **The flags are additive only** — `get_components()` does `args.db if args.db else config.get(...)`, so passing a flag can enable a component but there's no flag to force one *off* if it's already `true` in `pyproject.toml`; edit the toml to disable one.

## Running locally

```bash
uv run task app       # dev, hot reload via pymon
uv run task app-prod  # prod-style, no reload — prefer this when tailing logs for errors
uv run task db         # local mongod on port 1717 (mismatches .env's default 27017 — see below)
```

MongoDB is required whenever the `db` component is enabled (it is, by default) — `ActDb.__init__` calls `self._engine.client.address`, which blocks on server selection and will hang/fail startup if nothing is listening on the configured URI. If no local `mongod` is available, run one in Docker instead, matching whatever `MONGO_DB_URI` your `.env` has:

```bash
docker run -d --name act-mongo -p 27017:27017 -v act-mongo-data:/data/db mongo:7
```

## ⚠️ There is no separate dev bot token

`.env` holds the **real, live** `DISCORD_BOT_TOKEN` and `GEMINI_AI_API_KEY` — not test credentials. Running the bot locally connects the actual production Discord bot and serves real users in the real server; there's no sandbox/staging bot to point at instead. Treat starting/stopping/restarting it locally as a live-production action, not a harmless local test.

## ⚠️ Pushing to `main` auto-deploys to production

`.github/workflows/deploy.yml` ("Deploy to Homelab") SSHes into the homelab (`act-bot.comonhq.com`, via Cloudflare Tunnel) on every push to `main`, pulls, `uv sync`s, and restarts the live bot service — no manual approval step. `deploy-pi.yml` ("Deploy to Raspberry Pi") is a legacy workflow from before the move to the homelab; the homelab is the current production target. Be deliberate about pushing/merging to `main`.

## Error tracking

`utils/log.py` defines a custom `ActLogger` with emoji-tagged levels (❌ error, 💀 critical, ✅ success, ⏳ loading, ⚠️ warning). Most cog-level failures are caught and logged with `log.exception`/`log.error` rather than crashing the process — when hunting for runtime errors, grep console/log output for `❌|💀|Traceback` rather than expecting the process to exit.

Known trouble spots found while debugging:
- `bot/cogs/chat_cogs/ai_cog.py`'s `MAX_CHANNEL_HISTORY` controls how many full channel messages get embedded as CSV into *every* AI prompt (`create_prompt`) — keep it small, it directly drives Gemini input-token usage and free-tier `429 RESOURCE_EXHAUSTED` errors.
- `ActTaskManager.schedule()` (`utils/task.py`) silently returns `False` and just logs an error if a task ID is already scheduled — it does not queue or replace. Any code scheduling tasks under a shared/reused ID (e.g. per-guild instead of per-message) can silently drop work when two triggers race.

## Conventions

- PEP 8, Black formatter.
- No test suite currently — `z_test/` holds exploratory Jupyter notebooks (`_ai.ipynb`, `_bot.ipynb`, `_db.ipynb`, `_rpg.ipynb`, `_utils.ipynb`), not automated tests.
