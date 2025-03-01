from typing import cast

from discord import Guild
from fastapi import APIRouter, HTTPException

from bot.cogs.board_cog import BoardCog
from bot.main import ActBot
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Default Router
# ----------------------------------------------------------------------------------------------------
class DefaultRouter(APIRouter):
    def __init__(self, bot: ActBot, *args, **kwargs):
        super().__init__(tags=["Default"], *args, **kwargs)

        @self.get("/")
        def get_root():
            return "Welcome to ACT API. For docs go to: ./docs"
