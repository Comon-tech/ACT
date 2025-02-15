import asyncio
import os
import tomllib
from argparse import ArgumentParser
from types import SimpleNamespace

import dotenv
from discord import Intents

from api.main import ActApi
from bot.main import ActBot
from db.main import ActDbClient
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
        bot, api = get_components(TOOL_ACT_COMPONENTS)

        # Prepare list of components to run
        coroutines = []

        # Create & add database
        db_client = ActDbClient(host=db_uri, name=name)

        # Create & add bot component
        if bot:
            intents = Intents.default()
            intents.message_content = True
            bot = ActBot(
                token=bot_token,
                db_client=db_client,
                title=name,
                version=version,
                api_keys={"gemini": ai_api_key},
                command_prefix="!",
                intents=intents,
            )
            coroutines.append(bot.enter())

        # Create & add api component
        if api:
            api = ActApi(
                bot=bot,
                url=server_url,
                title=name,
                version=version,
                description=description,
            )
            coroutines.append(api.enter())

        # Run all components asynchronously
        await asyncio.gather(*coroutines)

    except (asyncio.CancelledError, KeyboardInterrupt, Exception) as e:
        if isinstance(e, KeyboardInterrupt):
            log.info("Keyboard interrupt received.")
        elif not isinstance(e, asyncio.CancelledError):
            log.exception(e)
        if bot:
            await bot.exit()
        if api:
            await api.exit()
        db_client.close()

    finally:
        print("❤  Bye!\n")


# ----------------------------------------------------------------------------------------------------
# * Title
# ----------------------------------------------------------------------------------------------------
def get_components(config: dict[str, bool]):
    parser = ArgumentParser(description="run app components")
    parser.add_argument("-b", "--bot", action="store_true", help="run bot component")
    parser.add_argument("-a", "--api", action="store_true", help="run api component")
    args = parser.parse_args()
    bot = args.bot if args.bot else config.get("bot", False)
    api = args.api if args.api else config.get("api", False)
    if not (bot or api):
        log.warning(
            f"No app component specified in command options or project settings.\n\n{parser.format_help()}"
        )
        raise SystemExit(1)
    return (bot, api)


# ----------------------------------------------------------------------------------------------------
# * Run Application
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
