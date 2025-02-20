import google.generativeai as genai
import requests
from google.generativeai.generative_models import ChatSession
from pydantic import BaseModel, StringConstraints, field_validator
from typing_extensions import Annotated

from utils.log import logger
from utils.misc import text_csv

log = logger(__name__)
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]


# ----------------------------------------------------------------------------------------------------
# * AI Persona
# ----------------------------------------------------------------------------------------------------
class AiPersona(BaseModel):
    instructions: NonEmptyStr | list[NonEmptyStr] = None

    @classmethod
    @field_validator("instructions")
    def process_instructions(cls, instructions) -> list[NonEmptyStr]:
        return (
            instructions.splitlines() if isinstance(instructions, str) else instructions
        )

    @property
    def instructions_text(self) -> str:
        return ";".join(self.instructions)


# ----------------------------------------------------------------------------------------------------
# * AI Chat
# ----------------------------------------------------------------------------------------------------
class AiChat(BaseModel):
    api_key: NonEmptyStr
    persona: AiPersona
    _model: genai.GenerativeModel
    _sessions: dict[int | str, ChatSession | None] = {}
    _current_session_id: int = 0

    def model_post_init(self, __context):
        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=self.persona.instructions_text,
        )
        return super().model_post_init(__context)

    # ----------------------------------------------------------------------------------------------------

    async def prompt(self, text: str, image: bytes = None) -> str | None:
        session = self.use_session(self._current_session_id)
        content = self._create_content(text, image)
        response = session.send_message(content)
        return response.text if response else None

    # ----------------------------------------------------------------------------------------------------

    def use_session(self, id: int, history: list[dict | str] = []) -> ChatSession:
        """Use session with given id. If nonexistent, create and initialize with given history."""
        session = self._sessions.get(id)
        if not session:
            session = self._model.start_chat(history=history)
            self._sessions[id] = session
            self._current_session_id = id
        return session

    def dump_session(self, id: int = None):
        """Dump session with given id or current sesssion if no given id."""
        id = id or self._current_session_id
        session = self.use_session(id)
        history = [
            genai.protos.Content.to_dict(content)
            for content in self._sessions[id].history
        ]
        return {"id": id, "history": history}

    # ----------------------------------------------------------------------------------------------------

    @staticmethod
    def _create_content(text: str, image: bytes = None, role="user") -> str:
        parts = [text]
        if image:
            parts.append({"mime_type": "image/png", "data": image})
        content = {
            "role": role,
            "parts": parts,
        }
        return content
