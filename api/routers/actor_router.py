from typing import cast

from fastapi import APIRouter, HTTPException

from bot.cogs.board_cog import BoardCog
from bot.main import ActBot
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Actor Router
# ----------------------------------------------------------------------------------------------------
class ActorRouter(APIRouter):
    def __init__(self, bot: ActBot, *args, **kwargs):
        super().__init__(prefix="/actors", tags=["Actors"], *args, **kwargs)

        # ----------------------------------------------------------------------------------------------------

        @self.get("/{guild_id}/", response_model=list[Actor])
        async def get_actors(guild_id: int, limit: int = 10):
            try:
                for guild in bot.guilds:
                    if guild.id == guild_id:
                        return bot.get_db(guild).find(Actor, limit=limit)

                    raise HTTPException(
                        status_code=404,
                        detail=f"No guild with id '{guild_id}' found among the guilds the discord bot is member of.",
                    )
                raise HTTPException(
                    status_code=404,
                    detail="No guilds found. The discord bot is not member of any guild",
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        # ----------------------------------------------------------------------------------------------------

        @self.get("/{guild_id}/top/", response_model=list[Actor])
        async def get_top_actors(guild_id: int, limit: int = 10):  # Leaderboard
            try:
                for guild in bot.guilds:
                    if guild.id == guild_id:
                        return cast(
                            BoardCog, bot.get_cog(BoardCog.__cog_name__)
                        ).get_top_actors(guild, limit)

                    raise HTTPException(
                        status_code=404,
                        detail=f"No guild with id '{guild_id}' found among the guilds the discord bot is member of.",
                    )
                raise HTTPException(
                    status_code=404,
                    detail="No guilds found. The discord bot is not member of any guild",
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
