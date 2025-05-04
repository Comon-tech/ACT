from io import BytesIO
from typing import Any

from google.genai import Client
from google.genai.chats import AsyncChat
from google.genai.types import Content, GenerateContentConfig, Part
from PIL import Image
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
    model_name: str = Field(alias="model", default="gemini-2.0-flash")
    response_char_limit: int = 2000  # Used to be 4000 hmm

    _client: Client | None = None
    _config: GenerateContentConfig | None = None
    _chats: dict[int | str, AsyncChat | None] = {}
    _current_chat_id: int = 0

    def model_post_init(self, context: Any):
        self._client = Client(api_key=self.api_key)
        self._config = GenerateContentConfig(
            system_instruction=self.instructions, response_modalities=["TEXT"]  # type: ignore
        )
        return super().model_post_init(context)

    # ----------------------------------------------------------------------------------------------------

    @classmethod
    @field_validator("instructions")
    def process_instructions(cls, instructions) -> list[NonEmptyStr]:
        return (
            instructions.splitlines() if isinstance(instructions, str) else instructions
        )

    # ----------------------------------------------------------------------------------------------------

    async def prompt(self, text: str, file: ActFile | None = None) -> str | None:
        chat = self.use_session(self._current_chat_id)
        message = [Part(text=text)]
        if file and file.major_type == "image":
            message.append(
                Part.from_bytes(data=file.data, mime_type=file.mime_type or "")
            )
        response = await chat.send_message(message, self._config)  # type: ignore
        response_text = response.text if response else None
        if response_text and len(response_text) > self.response_char_limit:
            response_text = response_text[: (self.response_char_limit - 3)] + "..."
        return response_text

    # async def prompt_image(self, text: str) -> BytesIO | None:
    #     candiates = response.candidates[0] if response and response.candidates else None
    #     parts =  candiates.content.parts if candiates and candiates.content else None

    #     if not parts:
    #         return ""

    #     for part in parts:
    #         if part.text is not None:
    #             print(part.text)
    #         elif part.inline_data is not None:
    #             image = Image.open(BytesIO((part.inline_data.data)))
    #             image.save('gemini-native-image.png')
    #             image.show()

    # ----------------------------------------------------------------------------------------------------

    def use_session(self, id: int, history: list[Content] | None = None) -> AsyncChat:
        """Use and get chat session with given id. If nonexistent, create and initialize with given history."""
        chat = self._chats.get(id)
        if not chat:
            if history:
                history = [
                    Content(**content) if not isinstance(content, Content) else content
                    for content in history
                ]  # Sanitize history to ensure correct dumping in dump_history()
            chat = self._client.aio.chats.create(model=self.model_name, history=history)  # type: ignore
            self._chats[id] = chat
        self._current_chat_id = id
        return chat

    def clear_session(self, id: int):
        """Clear chat session with given id. If nonexistent, get False."""
        chat = self._chats.get(id)
        if chat:
            del self._chats[id]
            return True
        return False

    def dump_history(self, id: int | None = None, history_max_items=20) -> list[dict]:
        """Dump chat session history of given id. If no id, dump current."""
        id = id or self._current_chat_id
        chat = self.use_session(id)
        return [
            content.model_dump(exclude_unset=True)
            for content in chat._curated_history[-history_max_items:]
        ]

    # ----------------------------------------------------------------------------------------------------
