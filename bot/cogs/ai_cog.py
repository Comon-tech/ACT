import asyncio
import csv
import pathlib
import re
import tomllib
from datetime import UTC, datetime
from io import BytesIO, StringIO
from types import SimpleNamespace

import google.generativeai as genai
import requests
from discord import Attachment, File, Guild, HTTPException, Member, Message
from discord.ext.commands import Cog
from google.api_core.exceptions import ResourceExhausted

from bot.main import ActBot
from db.actor import Actor
from utils.ai import AiChat, AiPersona
from utils.log import logger
from utils.misc import text_csv

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * AI Cog
# ----------------------------------------------------------------------------------------------------
class AI(Cog, description="Integrated generative AI chat bot."):
    CONFIG_PATH = pathlib.Path(__file__).parent / "ai_cog.toml"

    def __init__(self, bot: ActBot):
        self.bot = bot
        with open(self.CONFIG_PATH, "rb") as file:
            config = tomllib.load(file)
        persona = AiPersona(**config.get("personas").get("activa"))
        self.ai_chat = AiChat(api_key=bot.api_keys.get("gemini"), persona=persona)
        log.info(
            f"AI persona with {len(persona.instructions_text)} characters instructions used."
        )

    @Cog.listener()
    async def on_message(self, message: Message):
        # Ignore if bot own message or bot not mentioned
        if self.bot.user == message.author or self.bot.user not in message.mentions:
            return

        # Prepare prompts
        text_prompt = f"{message.author.name}: {message.content.replace(self.bot.user.mention, "").strip()}"
        image_prompt: bytes = bytes(0)

        # Load all members who interacted before
        actors = self.load_actors(message.guild)
        text_prompt += f"\n{text_csv(actors, "|")}"

        # Add attachment
        if message.attachments:
            attachment = message.attachments[0]
            content_type, content = await self.process_attachment(attachment)
            match content_type:
                case "text":
                    text_prompt += content
                case "image":
                    image_prompt = content
                case "video":
                    text_prompt += f"_sent video:{attachment.filename}_"
                case _:
                    text_prompt += f"_sent file:{attachment.filename}_"

        # Prompt AI
        log.info(f"[Prompt] {text_prompt} <image:{len(image_prompt)}bytes>")
        try:
            chat = self.ai_chat
            chat.use_session(message.guild.id, history=[])
            reply = await chat.prompt(text=text_prompt, image=image_prompt)
        except ResourceExhausted as e:
            reply = "Oops! 😵‍💫 I'm out of energy for now. Give me a moment! 🙏"
            log.exception(e)
            # Set cooldown to prevent spamming API when quota is exceeded
            # asyncio.create_task(self.sleep_in_channel(session_id))
        except Exception as e:
            reply = "Sorry! 😵‍💫 There's something wrong with me right now 😭. Give me a moment plz! 🙏"
            log.exception(e)

        # Send reply
        fallback_reply = "What? 😕"
        await message.reply(reply or fallback_reply)

        # Save current member who interacted to be remembered next time
        self.save_actor(message.guild, message.author)

    # ----------------------------------------------------------------------------------------------------

    @staticmethod
    async def process_attachment(attachment: Attachment) -> tuple[str, str | bytes]:
        file_type = attachment.content_type.strip()
        content_type = file_type.split("/")[0]
        if content_type == "text":
            content = (await attachment.read()).decode("utf-8")
        elif content_type in ("image", "audio", "video"):
            content = await attachment.read()
        else:
            content = file_type
        return (content_type, content)

    def load_actors(self, guild: Guild):
        db = self.bot.db_engine(guild)
        actors = db.find(
            Actor,
            sort=Actor.ai_interacted_at,  # Sort by interaction time (most recent first)
            limit=5,
        )
        return [
            actor.model_dump(include={"id": True, "name": True, "display_name": True})
            for actor in actors
        ]

    def save_actor(self, guild: Guild, member: Member):
        db = self.bot.db_engine(guild)
        actor = db.find_one(Actor, Actor.id == member.id)
        if not actor:
            user = member
            actor = Actor(
                id=user.id,
                name=user.name,
                display_name=user.display_name,
                ai_interacted_at=datetime.now(UTC),
            )
        db.save(actor)

    # ----------------------------------------------------------------------------------------------------

    # def load_chat_session(self, guild: Guild):
    #     try:
    #         session_id = guild.id
    #         if session_id not in self.chat_sessions:
    #             db = self.bot.db_engine(guild)
    #             sessions = db.get_collection("ai_chat_sessions").find(
    #                 {}, {"history": {"$slice": -10}}
    #             )  # slice few last records

    #             sessions = db.find(ChatSessionModel)

    #             for session in sessions:
    #                 history.append(
    #                     {
    #                         "role": "user",
    #                         "parts": [self.load_members_csv(message.guild)],
    #                     }
    #                 )
    #                 self.chat_sessions[id] = self.model.start_chat(
    #                     history=session.history
    #                 )
    #                 log.info(f"[{guild.name}] Loaded chat session.")
    #         if session_id not in self.chat_sessions:
    #             self.chat_sessions[session_id] = self.model.start_chat(
    #                 history=[
    #                     {
    #                         "role": "user",
    #                         "parts": [self.load_members_csv(message.guild)],
    #                     }
    #                 ]
    #             )
    #     except Exception as e:
    #         log.exception(
    #             f"[{message.guild.name}][{message.channel.name}] Error loading chat session: {e}"
    #         )

    # def save_chat_session(self, message: Message):
    #     try:
    #         session_id = message.channel.id
    #         guild_db = self.bot.db_engine(message.guild)
    #         guild_db.get_collection("ai_chat_sessions").replace_one(
    #             {"_id": session_id},
    #             {
    #                 "_id": session_id,
    #                 "history": [
    #                     genai.protos.Content.to_dict(content)
    #                     for content in self.chat_sessions[session_id].history
    #                 ],
    #             },
    #             upsert=True,
    #         )
    #         log.info(
    #             f"[{message.guild.name}][{message.channel.name}] Saved chat session."
    #         )
    #     except Exception as e:
    #         log.exception(
    #             f"[{message.guild.name}][{message.channel.name}] Error saving chat session: {e}"
    #         )

    # async def sleep_in_channel(self, channel_id):
    #     self.cooldowns[channel_id] = True
    #     sleep_time = 60  # 1 minute
    #     log.loading(f"Sleeping for {sleep_time} seconds in channel {channel_id}...")
    #     await asyncio.sleep(60)
    #     log.info(f"Awake from sleep in channel {channel_id}.")
    #     self.cooldowns.pop(channel_id, None)
