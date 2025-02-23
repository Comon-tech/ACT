import pathlib
import tomllib
from datetime import UTC, datetime

from discord import Attachment, Guild, Member, Message, User
from discord.ext import tasks
from discord.ext.commands import Cog
from google.genai.errors import APIError

from bot.main import ActBot
from db.actor import Actor
from db.main import DbRef
from utils.ai import ActAi
from utils.file import ActFile
from utils.log import logger
from utils.misc import text_csv

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * AI Cog
# ----------------------------------------------------------------------------------------------------
class AI(Cog, description="Integrated generative AI chat bot."):
    CONFIG_PATH = pathlib.Path(__file__).parent / "ai_cog.toml"
    MAX_FILE_SIZE = 524288  # 512 KB (0.5 MB)
    COOLDOWN_SECONDS = 60

    def __init__(self, bot: ActBot):
        self.bot = bot
        with open(self.CONFIG_PATH, "rb") as file:
            config = tomllib.load(file)
        persona_name = "activa"
        persona_desc = config.get("personas", {}).get(persona_name)
        self.ai = ActAi(
            api_key=bot.api_keys.get("gemini", ""), instructions=persona_desc
        )
        log.info(
            f"AI persona @{persona_name} with {len(persona_desc)} characters instructions used."
        )
        self.guilds_remaining_cooldown_seconds: dict[int, int] = {}  # { id : seconds }

    def cog_unload(self):
        self.cooldown_guild.cancel()

    # ----------------------------------------------------------------------------------------------------

    @Cog.listener()
    async def on_message(self, message: Message):
        # Ignore if bot own message or bot not mentioned
        if self.bot.user == message.author or self.bot.user not in message.mentions:
            return

        # ⛔ TODO: Not from a guid? what to do ?
        # ⛔ TODO: Fix image attachement (maybe implement compression)
        if not message.guild:
            await message.reply(
                f"Wa are in DM right? 🤔\nChannel: {message.channel} (id#{message.channel.id})"
            )
            return

        remaining_cooldown_seconds = self.guilds_remaining_cooldown_seconds.get(
            message.guild.id
        )
        if remaining_cooldown_seconds:
            reply = (
                f"Please! 🙏 Give me about {remaining_cooldown_seconds} seconds... ⏳"
            )

        else:
            # Prepare prompts
            text_prompt = f"{message.author.name}:"
            file_prompt = None

            # Add message attachment
            if message.attachments:
                attachment = message.attachments[0]
                text_prompt += f"_sent file:{attachment.filename}_"
                if attachment.size <= self.MAX_FILE_SIZE:
                    async with message.channel.typing():
                        file_prompt = ActFile(
                            data=await attachment.read(),
                            mime_type=attachment.content_type,
                            name=attachment.filename,
                        )
                else:
                    text_prompt += f"(but u can't receive it cuz it's larger than ur allowed min size limit of {self.MAX_FILE_SIZE}byte)"
            elif message.embeds:
                embed_url = message.embeds[0].url
                embed_file = ActFile.load(embed_url) if embed_url else None
                if embed_file:
                    if embed_file.size <= self.MAX_FILE_SIZE:
                        file_prompt = embed_file
                    else:
                        text_prompt += f"_sent embed but u can't receive it cuz it's larger than ur allowed min size limit of {self.MAX_FILE_SIZE}byte_"

            # Add message content
            text_prompt += (
                f"{message.content.replace(self.bot.user.mention, "").strip()}"
            )

            # Add members who interacted before
            actors = self.load_actors(message.guild)
            if actors:
                text_prompt += f"\n{text_csv(actors, "|")}"

            # Prompt AI
            log.info(f"[Prompt] {text_prompt} <{file_prompt}>")
            try:
                self.ai.use_session(
                    message.guild.id, history=self.load_history(message.guild)
                )
                async with message.channel.typing():
                    reply = self.ai.prompt(
                        text=text_prompt,
                        file=file_prompt,
                    )
            except APIError as e:
                reply = "Oops! 😵‍💫 I'm out of energy for now. Give me a moment! 🙏"
                self.cooldown_guild.start(message.guild)
                log.exception(e)
            except Exception as e:
                reply = "Sorry! 😵‍💫 There's something wrong with me right now 😭. Give me a moment plz! 🙏"
                log.exception(e)

        # Send reply
        fallback_reply = "What? 😕"
        await message.reply(reply or fallback_reply)

        # Save current member who interacted to be remembered next time
        self.save_actor_interaction(message.guild, message.author)
        self.save_history(message.guild)

    # ----------------------------------------------------------------------------------------------------

    def load_actors(self, guild: Guild) -> list | None:
        db = self.bot.db_engine(guild)
        if not db:
            return
        actors = db.find(
            Actor,
            sort=Actor.ai_interacted_at,  # Sort by interaction time (most recent first)
            limit=5,
        )
        return [
            actor.model_dump(include={"id": True, "name": True, "display_name": True})
            for actor in actors
        ]

    def save_actor_interaction(self, guild: Guild, member: Member | User) -> None:
        db = self.bot.db_engine(guild)
        if not db:
            return
        actor = db.find_one(Actor, Actor.id == member.id)
        if not actor:
            actor = Actor(
                id=member.id, name=member.name, display_name=member.display_name
            )
        actor.ai_interacted_at = datetime.now(UTC)
        db.save(actor)

    # ----------------------------------------------------------------------------------------------------

    def load_history(self, guild: Guild) -> list | None:
        main_db = self.bot.db_engine()
        if not main_db:
            return
        db_ref = main_db.find_one(DbRef, DbRef.id == guild.id)
        if db_ref:
            return db_ref.ai_chat_history

    def save_history(self, guild: Guild) -> None:
        main_db = self.bot.db_engine()
        if not main_db:
            return
        db_ref = main_db.find_one(DbRef, DbRef.id == guild.id)
        if not db_ref:
            db_ref = DbRef(id=guild.id, name=guild.name)
        db_ref.ai_chat_history = self.ai.dump_history(guild.id)
        main_db.save(db_ref)

    # ----------------------------------------------------------------------------------------------------

    @tasks.loop(seconds=1)
    async def cooldown_guild(self, guild: Guild):
        """Cooldown to prevent spamming when needed."""
        remaining_seconds = self.guilds_remaining_cooldown_seconds.get(guild.id)
        if remaining_seconds is None:
            remaining_seconds = self.COOLDOWN_SECONDS + 1
            log.info(
                f"[{guild.name}] {self.COOLDOWN_SECONDS} seconds cooldown started."
            )
        remaining_seconds -= 1
        self.guilds_remaining_cooldown_seconds[guild.id] = remaining_seconds

        if remaining_seconds <= 0:
            self.guilds_remaining_cooldown_seconds.pop(guild.id, None)
            self.cooldown_guild.cancel()
            log.info(
                f"[{guild.name}] {self.COOLDOWN_SECONDS} seconds cooldown finished."
            )

    @cooldown_guild.before_loop
    async def before_sleep_in_guild(self):
        await self.bot.wait_until_ready()
