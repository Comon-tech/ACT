from typing import Union

from discord.ext.commands import Bot
from fastapi import FastAPI, HTTPException


# ----------------------------------------------------------------------------------------------------
# * Routes
# ----------------------------------------------------------------------------------------------------
def add_routes(app: FastAPI, bot: Bot):
    @app.get("/")
    def get_root():
        return "Welcome to ACT API. For docs go to: ./docs"

    @app.get("/users/{id}")
    async def get_users(id: int, q: Union[str, None] = None):
        if not bot:
            return {"error": "No Bot"}
        else:
            if not id:
                members = [member.display_name for member in bot.get_all_members()]
                return members
            try:
                user = await bot.fetch_user(id)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            return {
                # "id": user.id,
                "name": user.name,
                "display_name": user.display_name,
                "avatar": user.avatar.url,
            }
