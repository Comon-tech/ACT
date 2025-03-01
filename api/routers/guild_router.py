from typing import cast

from discord import Guild
from fastapi import APIRouter, HTTPException

from bot.cogs.board_cog import BoardCog
from bot.main import ActBot
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Guild Router
# ----------------------------------------------------------------------------------------------------
class GuildRouter(APIRouter):
    def __init__(self, bot: ActBot, *args, **kwargs):
        super().__init__(prefix="/guilds", tags=["Guilds"], *args, **kwargs)

        def guild_dict(guild: Guild):
            return {
                "id": guild.id,
                "name": guild.name,
                "description": guild.description,
                "icon": guild.icon.url if guild.icon else None,
                "banner": guild.banner.url if guild.banner else None,
                "created_at": guild.created_at,
            }

        # ----------------------------------------------------------------------------------------------------

        @self.get("/", response_model=list[dict])
        async def get_guilds():
            try:
                return [guild_dict(guild) for guild in bot.guilds]
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        # ----------------------------------------------------------------------------------------------------

        @self.get("/{guild_id}", response_model=dict)
        async def get_guild(guild_id: int):
            try:
                for guild in bot.guilds:
                    if guild.id == guild_id:
                        return guild_dict(guild)
                raise HTTPException(
                    status_code=404,
                    detail=f"No guild with id '{guild_id}' found among the guilds the discord bot is member of.",
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
