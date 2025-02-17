import asyncio
import csv
import os
import pathlib
import re
import tomllib
from io import StringIO
from types import SimpleNamespace

import google.generativeai as genai
import requests
from discord import Attachment, Guild, Member, Message, TextChannel
from discord.ext.commands import Cog
from google.ai import generativelanguage_v1beta as glm
from google.api_core.exceptions import ResourceExhausted

from bot.main import ActBot
from utils.log import logger

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * AI Cog
# ----------------------------------------------------------------------------------------------------
class AI(Cog, description="Integrated generative AI chat bot."):
    CONFIG_PATH = pathlib.Path(__file__).parent / "ai_cog.toml"

    def __init__(self, bot: ActBot):
        self.bot = bot
        with open(self.CONFIG_PATH, "rb") as file:
            self.config = tomllib.load(file)
            self.persona = self.create_persona("activa")
            log.info(
                f"{self.persona.name.title()} persona with {len(self.persona.desc)} characters description used."
            )
        genai.configure(api_key=bot.api_keys.get("gemini"))
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", system_instruction=self.persona.desc
        )
        self.chat_sessions = {}
        self.cooldowns = {}

    @Cog.listener()
    async def on_message(self, message: Message):
        # Ignore if bot own message or bot not mentioned
        if self.bot.user == message.author or self.bot.user not in message.mentions:
            return

        # Create default reply
        reply = "What? 😕"

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
        session_id = str(message.channel.id)

        # Check context
        if not session_id:
            reply = None
        if session_id in self.cooldowns:
            reply = "I'm taking a quick break! 🌙 Too many questions at once 😲. Try again in a moment."

        # Generate AI reply
        if prompt or image_url:
            # Load session
            if session_id not in self.chat_sessions:
                self.load_chat_session(message)

            # go
            try:
                async with message.channel.typing():
                    reply = await self.generate_content(
                        prompt=f"{message.author.display_name}: {prompt}",
                        image_url=image_url,
                        session_id=session_id,
                    )
            except ResourceExhausted as e:
                reply = "Oops! 😵‍💫 I'm out of energy for now. Give me a moment! 🙏"
                log.exception(e)
                # Set cooldown to prevent spamming API when quota is exceeded
                # asyncio.create_task(self.sleep_in_channel(session_id))
            except Exception as e:
                reply = "Sorry! 😵‍💫 There's something wrong with me right now 😭. Give me a moment plz! 🙏"
                log.exception(e)

        # Check one last time
        if not reply:
            reply = "...⁉"

        # Process mentions
        # mentions = re.findall(r"@(\w+)", reply)
        # for username in mentions:
        #     user_id = await message.guild.fetch_member()
        #     if user_id:
        #         text = text.replace(f"@{username}", f"<@!{user_id}>") # replace username mention with user id mention
        #     else:
        #         log.warning(f"User '{username}' not found in guild '{guild.name}'.")

        # Send reply
        await message.reply(reply)

        # Save chat session
        self.save_chat_session(message)
        self.save_member(message.author)

    # ----------------------------------------------------------------------------------------------------

    async def generate_content(self, prompt: str, image_url="", session_id=""):
        """Generate AI response while maintaining conversation history for each channel."""
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

    # @staticmethod
    # async def get_recent_messages(channel: TextChannel, limit=3) -> str:
    #     """Fetch recent messages from a text channel."""
    #     messages = [msg async for msg in channel.history(limit=limit)]
    #     return "\n".join(
    #         [
    #             f"User {msg.author.display_name} (name:{msg.author.name},id:{msg.author.id}) said: {msg.content}"
    #             for msg in reversed(messages)
    #         ]
    #     )

    def save_member(self, member: Member):
        ai_chat_users = self.bot.get_database(member.guild)["ai_chat_users"]
        return ai_chat_users.update_one(
            {"_id": member.id},
            {
                "$set": {
                    "_id": member.id,
                    "name": member.name,
                    "display_name": member.display_name,
                }
            },
            upsert=True,
        )

    def load_members_csv(self, guild: Guild):
        ai_chat_users = self.bot.get_database(guild)["ai_chat_users"]
        members = ai_chat_users.find()
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["_id", "name", "display_name"])
        writer.writeheader()
        for member in members:
            writer.writerow(member)
        return output.getvalue()

    # @staticmethod
    # async def get_recent_channel_users_csv(channel: TextChannel, limit=10) -> str:
    #     """Fetch recent unique message authors from a text channel in CSV format."""
    #     users = set()
    #     async for msg in channel.history(limit=limit):
    #         user_info = {  # Store in a dictionary for CSV writer
    #             "id": msg.author.id,
    #             "name": msg.author.name,
    #             "display_name": msg.author.display_name,
    #         }
    #         users.add(tuple(user_info.values()))  # Stringify the user object directly
    #     # Create CSV string in memory:
    #     output = StringIO()  # Use StringIO for in-memory file-like object
    #     writer = csv.DictWriter(output, fieldnames=user_info.keys())  # Use DictWriter
    #     writer.writeheader()  # Write the header row
    #     for user_data in users:
    #         writer.writerow(
    #             dict(zip(user_info.keys(), user_data))
    #         )  # Write each user as row
    #     return output.getvalue()

    def create_persona(self, name):
        persona = SimpleNamespace(**self.config.get("personas", {}).get(name, {}))
        persona.desc = " ".join(line.strip() for line in persona.desc.splitlines())
        return persona

    def load_chat_session(self, message: Message):
        try:
            guild_db = self.bot.get_database(message.guild)
            sessions = guild_db.get_collection("ai_chat_sessions").find(
                {}, {"history": {"$slice": -10}}
            )  # slice few last records
            for session in sessions:
                id = session["_id"]
                history = session["history"]
                history.append(
                    {
                        "role": "user",
                        "parts": [self.load_members_csv(message.guild)],
                    }
                )
                self.chat_sessions[id] = self.model.start_chat(history=history)
                log.info(
                    f"[{message.guild.name}][{message.channel.name}] Loaded chat session."
                )
        except Exception as e:
            log.exception(
                f"[{message.guild.name}][{message.channel.name}] Error loading chat session: {e}"
            )

    def save_chat_session(self, message: Message):
        try:
            session_id = str(message.channel.id)
            guild_db = self.bot.get_database(message.guild)
            guild_db.get_collection("ai_chat_sessions").replace_one(
                {"_id": session_id},
                {
                    "_id": session_id,
                    "history": [
                        genai.protos.Content.to_dict(content)
                        for content in self.chat_sessions[session_id].history
                    ],
                },
                upsert=True,
            )
            log.info(
                f"[{message.guild.name}][{message.channel.name}] Saved chat session."
            )
        except Exception as e:
            log.exception(
                f"[{message.guild.name}][{message.channel.name}] Error saving chat session: {e}"
            )

    async def sleep_in_channel(self, channel_id):
        self.cooldowns[channel_id] = True
        sleep_time = 60  # 1 minute
        log.loading(f"Sleeping for {sleep_time} seconds in channel {channel_id}...")
        await asyncio.sleep(60)
        log.info(f"Awake from sleep in channel {channel_id}.")
        self.cooldowns.pop(channel_id, None)
