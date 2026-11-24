# Session Log

## 2026-09-20

**Changed**
- Wired `AiCog` to the dashboard's `guild_settings` collection: new read-only `db/guild_settings.py` model; `ai_cog.py` gets `get_guild_settings()` (60s cache) and per-guild auto-reply enabled/chance and initiative-enabled checks, falling back to the class constants on any missing/invalid/failed lookup. Initiative is now always scheduled and checked per guild at run time.
- Updated stale "bot doesn't read guild_settings" text in `ACT/CLAUDE.md`, `act-dashboard/AGENTS.md`, and the comment in `act-dashboard/src/models/GuildSettings.ts`.

**Verified**
- Settings lookup tested against a throwaway `mongo:7` container (saved settings, no doc, invalid chance, DM, DB failure, cache expiry, dashboard's extra fields intact).
- Dashboard: `tsc --noEmit` passes; `pnpm build` passes with dummy env vars.

**Still broken / unverified**
- `pnpm build` in `act-dashboard` fails without `MONGODB_URI` (`src/lib/mongodb.ts` throws at import). May also fail on Cloudflare if the var isn't present at build time; making the check lazy in `dbConnect()` would fix it.
- `on_message` / `perform_initiative` not exercised end to end (running the bot uses the live token).
- Black not installed in `.venv`; formatting unchecked.
- No dashboard route loaded in a browser; nothing tested against a deployed URL.
- All ACT changes are uncommitted (`ai_cog.py`, new `db/guild_settings.py`, `CLAUDE.md`). `act-dashboard` is uncommitted too and has no git remote.

**Next steps**
1. Review the diff, commit. Pushing to `main` auto-deploys to the live bot.
2. Save a setting in the dashboard and watch the bot log in the real server.
3. Make the `MONGODB_URI` check lazy so builds don't need it.
4. Add a remote for `act-dashboard` and commit its work.

## 2026-11-24

**Changed**
- Rebuilt `.venv` (`rm -rf .venv && uv sync`). The old venv's script shebangs pointed to the repo's previous location (`~/dev/comon/ACT`), so `uv run task db` failed with "Failed to spawn: `task`". `uv run task --list` works now.

**Still broken / unverified**
- `uv run task db` itself was not started (it would leave a mongod running). The `.mongodb` dbpath may need to exist first.
- Everything listed under 2026-09-20 is still open.
- Added `db-bg` (forked mongod on 1717, log at `.mongodb/mongod.log`) and `db-stop` taskipy tasks in `pyproject.toml`. Tested start → ping → stop.
- Found a system `mongod` service (enabled, port 27017, `/var/lib/mongo`) already running. Pointing `.env` at 27017 would remove the need for `task db` entirely. Not changed yet.
- Gemini 503 "model is experiencing high demand" (gemma-4-31b-it): `ActAi` built its `Client` without retry options, so google-genai 2.8.0 made one attempt only, and any `APIError` led to the "out of energy" reply plus a 60s per-guild cooldown. Added `RETRY_OPTIONS` in `utils/ai.py` (4 attempts, exponential backoff, retries 408/5xx, not 429). Tested against a fake local endpoint: two 503s then success → reply returned after 3 attempts; 429 → 1 attempt.
- Not done: AiCog still applies the 60s cooldown to every `APIError` (including 5xx that outlast the retries); there's no fallback model. Change not running live; it ships when committed and pushed to `main`.
- Benchmarked chat models on the bot's key (2 calls each, no retries, short persona prompt). Current gemma-4-31b-it: 503 / 22.0s. gemini-3.5-flash-lite 2.6/1.8s, gemini-2.5-flash 3.2/1.7s, gemini-flash-lite-latest 2.4/3.8s, gemma-4-26b-a4b-it 6.6/5.9s, gemini-3.1-flash-lite 10.5/2.2s. gemini-3.5-flash and 3.8-flash returned 503 on both calls; gemini-2.5-flash-lite returned 404 (retired). Free-tier daily limits per model not checked (not exposed by the API). Model not changed yet.
- Second benchmark (3 prompts each): both Gemma models and gemini-3.8-flash got 503 on all three calls; gemini-3.5-flash 13-53s; gemini-3.1-flash-lite 5-10s; gemini-2.5-flash 1.8-3.8s; gemini-3.5-flash-lite 0.9-3.8s; gemini-flash-lite-latest 1.1-1.7s (alias, Google can repoint it).
- Switched the `ActAi` default model `gemma-4-31b-it` → `gemini-3.5-flash-lite` (`utils/ai.py`). Tested through `ActAi` with the real Activa persona: stayed in character, remembered the user's name across turns, and read an attached image correctly; 6.5s and 7.3s per reply with the full persona prompt.
- Not verified: free-tier daily quota for gemini-3.5-flash-lite (check AI Studio); behavior in the live bot with channel history in the prompt. Uncommitted; pushing to `main` deploys.
