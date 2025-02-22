from enum import Enum
from typing import Optional

from google.genai import Client
from google.genai.chats import Chat
from google.genai.types import Content, GenerateContentConfig, Part
from pydantic import BaseModel, Field, StringConstraints, field_validator
from typing_extensions import Annotated

from utils.file import ActFile
from utils.log import logger

log = logger(__name__)
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]


# ----------------------------------------------------------------------------------------------------
# * Act AI
# ----------------------------------------------------------------------------------------------------
class ActAi(BaseModel):
    """Multi-session AI chat bot interface."""

    # ----------------------------------------------------------------------------------------------------

    api_key: NonEmptyStr
    instructions: NonEmptyStr | list[NonEmptyStr] | None = None
    model_name: str = Field(alias="model", default="gemini-1.5-flash")

    _client: Client | None = None
    _config: GenerateContentConfig | None = None
    _chats: dict[int | str, Chat | None] = {}
    _current_chat_id: int = 0

    def model_post_init(self, __context):
        self._client = Client(api_key=self.api_key)
        self._config = GenerateContentConfig(system_instruction=self.instructions)
        return super().model_post_init(__context)

    # ----------------------------------------------------------------------------------------------------

    @classmethod
    @field_validator("instructions")
    def process_instructions(cls, instructions) -> list[NonEmptyStr]:
        return (
            instructions.splitlines() if isinstance(instructions, str) else instructions
        )

    # ----------------------------------------------------------------------------------------------------

    def prompt(self, text: str, file: ActFile | None = None) -> str | None:
        chat = self.use_session(self._current_chat_id)
        message = [Part(text=text)]
        if file and file.major_type == "image":
            message.append(
                Part.from_bytes(data=file.data, mime_type=file.mime_type or "")
            )
        response = chat.send_message(message, self._config)
        return response.text if response else None

    # ----------------------------------------------------------------------------------------------------

    def use_session(self, id: int, history: list[Content] | None = None) -> Chat:
        """Use chat session with given id. If nonexistent, create and initialize with given history."""
        chat = self._chats.get(id)
        if not chat:
            if history:
                history = [
                    Content(**content) if not isinstance(content, Content) else content
                    for content in history
                ]  # Sanitize history to ensure correct dumping in dump_history()
            chat = self._client.chats.create(model=self.model_name, history=history)  # type: ignore
            self._chats[id] = chat
            self._current_chat_id = id
        return chat

    def dump_history(self, id: int | None = None, history_max_items=20) -> list[dict]:
        """Dump chat session history of given id. If no id, dump current."""
        id = id or self._current_chat_id
        chat = self.use_session(id)
        return [
            content.model_dump(exclude_unset=True)
            for content in chat._curated_history[-history_max_items:]
        ]

    # ----------------------------------------------------------------------------------------------------
