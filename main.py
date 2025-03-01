import asyncio
import os
import tomllib
from argparse import ArgumentParser
from types import SimpleNamespace

import dotenv
from discord import Intents

from api.main import ActApi
from bot.main import ActBot
from db.main import ActDb
from utils.log import logger

log = logger(__name__)

# ----------------------------------------------------------------------------------------------------
# * PyProject
# ----------------------------------------------------------------------------------------------------
# Load and parse pyproject.toml file
with open("pyproject.toml", "rb") as file:
    PYPROJECT = tomllib.load(file)
    PROJECT = PYPROJECT.get("project", {})
    TOOL_ACT_COMPONENTS = PYPROJECT.get("tool", {}).get("act", {}).get("components", {})


# ----------------------------------------------------------------------------------------------------
# * Main
# ----------------------------------------------------------------------------------------------------
async def main():
    """Application main entry point."""

    try:
        # Retrieve meta-data
        name = PROJECT.get("name", "")
        version = PROJECT.get("version", "")
        description = PROJECT.get("description", "")

        # Retrieve environment variables
        dotenv.load_dotenv()
        db_uri = os.getenv("MONGO_DB_URI")
        bot_token = os.getenv("DISCORD_BOT_TOKEN")
        server_url = os.getenv("APP_SERVER_URL")
        ai_api_key = os.getenv("GEMINI_AI_API_KEY")

        # Clear console & set title (Based on OS)
        os.system(
            f"cls && title ✈ {name}"  # For Windows
            if os.name == "nt"
            else f'clear && printf "\033]0;🚀 {name}\007"'  # For Unix-based systems
        )

        # Get components to enable
        db_enabled, bot_enabled, api_enabled = get_components(TOOL_ACT_COMPONENTS)

        # Prepare list of components to run
        coroutines = []

        # Create & add database component
        db = None
        if db_enabled:
            db = ActDb(host=db_uri, name=name)
        else:
            log.warning("Database component is turned off.")

        # Create & add bot component
        bot = None
        if bot_enabled:
            intents = Intents.default()
            intents.members = True
            intents.message_content = True
            bot = ActBot(
                token=bot_token or "",
                command_prefix="!",
                intents=intents,
                db=db,
                api_keys={"gemini": ai_api_key or ""},
                title=name,
                version=version,
                description=description,
            )
            coroutines.append(bot.open())
        else:
            log.warning("Bot component is turned off.")

        # Create & add api component
        api = None
        if api_enabled:
            api = ActApi(
                bot=bot,
                url=server_url or "",
                title=name,
                version=version,
                description=description,
            )
            coroutines.append(api.open())
        else:
            log.warning("API component is turned off.")

        # Run all components asynchronously
        await asyncio.gather(*coroutines)

    except (asyncio.CancelledError, KeyboardInterrupt, Exception) as e:
        if isinstance(e, KeyboardInterrupt):
            log.info("Keyboard interrupt received.")
        elif not isinstance(e, asyncio.CancelledError):
            log.exception(e)
        if db:
            db.close()
        if bot:
            await bot.close()
        if api:
            await api.close()

    finally:
        print("\n❤  Bye!\n")


# ----------------------------------------------------------------------------------------------------
# * Title
# ----------------------------------------------------------------------------------------------------
def get_components(config: dict[str, bool]):
    parser = ArgumentParser(description="run app components")
    parser.add_argument(
        "-d", "--db", action="store_true", help="enable db client component"
    )
    parser.add_argument(
        "-b", "--bot", action="store_true", help="enable bot client component"
    )
    parser.add_argument(
        "-a", "--api", action="store_true", help="enable api server component"
    )
    args = parser.parse_args()
    db_enabled = args.db if args.db else config.get("db", False)
    bot_enabled = args.bot if args.bot else config.get("bot", False)
    api_enabled = args.api if args.api else config.get("api", False)
    if not (bot_enabled or api_enabled):
        log.warning(
            f"No app component specified in command options or project settings.\n\n{parser.format_help()}"
        )
        raise SystemExit(1)
    return (db_enabled, bot_enabled, api_enabled)


# ----------------------------------------------------------------------------------------------------
# * Run Application
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
