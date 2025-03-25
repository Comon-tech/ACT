from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import tomllib
from utils.ai import ActAi, ActPersona
from pathlib import Path

# ----------------------------------------------------------------------------------------------------
# * Actva AI route
# ----------------------------------------------------------------------------------------------------

CONFIG_PATH = "/home/comon/dev/comon/TACT/bot/cogs/chat_cogs/ai_cog.toml" #use right path

with open(CONFIG_PATH, "rb") as file:
            config = tomllib.load(file)

persona = ActPersona(**config.get("personas", {}).get("activa"))

bot = ActAi(api_key="????????", 
            instructions=persona.description,
)

class ChatRequest(BaseModel):
    text: str
    session_id: int | None = None

class ActivaRouter(APIRouter):
    def __init__(self, activa: ActAi, *args, **kwargs):
        super().__init__(tags=["Activa"], *args, **kwargs)
        
        @self.post("/activa/chat")
        async def chat(request: ChatRequest):
            try:
                response = await bot.prompt(request.text)
                return {"response": response}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))