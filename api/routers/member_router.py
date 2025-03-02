from typing import cast

from discord import Guild, Member
from fastapi import APIRouter, HTTPException

from bot.cogs.board_cog import BoardCog
from bot.main import ActBot
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Member Router
# ----------------------------------------------------------------------------------------------------
class MemberRouter(APIRouter):
    def __init__(self, bot: ActBot, *args, **kwargs):
        super().__init__(prefix="/members", tags=["Members"], *args, **kwargs)

        def member_dict(member: Member):
            return (
                {
                    "id": member.id,
                    "name": member.name,
                    "display_name": member.display_name,
                    "diplay_avatar_url": member.display_avatar.url,
                    "display_icon_url": member.display_icon,
                    "banner_url": member.banner.url if member.banner else None,
                    "created_at": member.created_at,
                    "joined_at": member.joined_at,
                }
                if member
                else {}
            )

        # ----------------------------------------------------------------------------------------------------

        @self.get("/{guild_id}/top", response_model=list[dict])
        async def get_top_members(guild_id: int, limit: int = 10):
            try:
                for guild in bot.guilds:
                    if guild.id == guild_id:
                        top_actors = cast(
                            BoardCog, bot.get_cog(BoardCog.__cog_name__)
                        ).get_top_actors(guild, limit)

                        return [
                            member_dict(
                                guild.get_member(actor.id)
                                or await guild.fetch_member(actor.id)
                            )
                            for actor in top_actors
                        ]
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
