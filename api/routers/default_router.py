from fastapi import APIRouter

from bot.main import ActBot


# ----------------------------------------------------------------------------------------------------
# * Default Router
# ----------------------------------------------------------------------------------------------------
class DefaultRouter(APIRouter):
    def __init__(self, bot: ActBot, *args, **kwargs):
        super().__init__(tags=["Default"], *args, **kwargs)

        @self.get("/")
        def get_root():
            return "Welcome to ACT API. For docs go to: ./docs"
