import asyncio
import tomllib

import google.generativeai as genai
import requests
from discord import Attachment, Message, TextChannel
from discord.ext.commands import Cog
from google.api_core.exceptions import ResourceExhausted

from bot.main import ActBot
from utils.log import logger

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * AI Cog
# ----------------------------------------------------------------------------------------------------
class AI(Cog, description="Integrated generative AI chat bot."):
    def __init__(self, bot: ActBot):
        self.bot = bot
        genai.configure(api_key=bot.api_keys.get("gemini"))
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.chat_sessions = {}
        self.cooldowns = {}
        with open("./bot/ai.toml", "rb") as file:
            config = tomllib.load(file)
            persona = config.get("personas", {}).get("activa", {})
            persona_name: str = persona.get("name", "")
            persona_desc: str = persona.get("desc", "")
            self.persona_desc = " ".join(
                line.strip() for line in persona_desc.split("\n")
            )
            log.info(f"{self.__cog_name__} cog: using {persona_name.title()} persona.")

    @Cog.listener()
    async def on_message(self, message: Message):
        # Ignore if bot own message or bot not mentioned
        if self.bot.user == message.author or self.bot.user not in message.mentions:
            return

        # Create default reply
        reply = "What? 😕"
        await message.reply(reply)
        return

        # Create text prompt
        prompt = message.content.replace(self.bot.user.mention, "").strip()

        # Create image prompt
        file: Attachment = None
        image_url: str = None
        if message.attachments:
            file = message.attachments[0]
            file_type = file.content_type
            if file_type.startswith("text/"):
                reply = "Is this a 📄text file? 🤔"
            if file_type.startswith("image/"):
                image_url = file.url
                # reply = "Is this an 🖼image file? 🤔"
            elif file_type.startswith("audio/"):
                reply = "Is this an 🔊audio file? 🤔"
            elif file_type.startswith("video/"):
                reply = "Is this a 🎬video file? 🤔"
            else:
                reply = f"What type of file is this? 😮\nAfter inspecting, it says `{file_type}`\nhmm...🤔"

        # Create context
        persona_desc = self.persona_desc
        context = await self.get_recent_messages(message.channel)
        session_id = str(message.channel.id)

        # Check context
        if not session_id:
            reply = None
        if session_id in self.cooldowns:
            reply = "I'm taking a quick break! 🌙 Too many questions at once 😲. Try again in a moment."

        # Generate AI reply
        if prompt or image_url:
            try:
                reply = await self.generate_content(
                    prompt=prompt,
                    image_url=image_url,
                    personality=persona_desc,
                    context=context,
                    session_id=session_id,
                )
            except ResourceExhausted as e:
                reply = "Oops! 😵‍💫 I'm out of energy for now. Give me a moment! 🙏"
                log.error(e)
                # Set cooldown to prevent spamming API when quota is exceeded
                # asyncio.create_task(self.sleep_in_channel(session_id))
            except Exception as e:
                reply = "Sorry! 😵‍💫 There's something wrong with me right now 😭. Give me a moment plz! 🙏"
                log.error(e)

        # Check one last time
        if not reply:
            reply = "...⁉"

        # Send reply
        await message.reply(reply)

    # ----------------------------------------------------------------------------------------------------

    async def generate_content(
        self, prompt: str, image_url="", personality="", context="", session_id=""
    ):
        """Generate AI response while maintaining conversation history for each channel."""
        # Create a new chat session for the channel if it doesn't exist
        if session_id not in self.chat_sessions:
            # Add personality and context
            self.chat_sessions[session_id] = self.model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [
                            personality,
                            f"Context of conversation:\n{context}",
                        ],
                    }
                ]
            )
        # Continue conversation in the existing chat session
        response = self.chat_sessions[session_id].send_message(
            {
                "role": "user",
                "parts": [
                    prompt,
                    (
                        {
                            "mime_type": "image/png",
                            "data": requests.get(image_url).content,
                        }
                        if image_url
                        else ""
                    ),
                ],
            }
        )
        return response.text if response else None

    async def get_recent_messages(self, channel: TextChannel, limit=3) -> str:
        """Fetch recent messages from a text channel."""
        messages = [msg async for msg in channel.history(limit=limit)]
        return "\n".join(
            [
                f"User {msg.author.display_name} (name:{msg.author.name},id:{msg.author.id}) said: {msg.content}"
                for msg in reversed(messages)
            ]
        )

    async def sleep_in_channel(self, channel_id):
        self.cooldowns[channel_id] = True
        sleep_time = 60  # 1 minute
        log.loading(f"Sleeping for {sleep_time} seconds in channel {channel_id}...")
        await asyncio.sleep(60)
        log.info(f"Awake from sleep in channel {channel_id}.")
        self.cooldowns.pop(channel_id, None)
