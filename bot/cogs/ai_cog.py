import pathlib
import tomllib
from datetime import UTC, datetime

from discord import Attachment, Guild, Member, Message, User
from discord.ext.commands import Cog
from google.genai.errors import APIError

from bot.main import ActBot
from db.actor import Actor
from db.main import DbRef
from utils.ai import ActAi
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
        persona_name = "activa"
        persona_desc = config.get("personas", {}).get(persona_name)
        self.ai = ActAi(
            api_key=bot.api_keys.get("gemini", ""), instructions=persona_desc
        )
        log.info(
            f"AI persona @{persona_name} with {len(persona_desc)} characters instructions used."
        )

    @Cog.listener()
    async def on_message(self, message: Message):
        # Ignore if bot own message or bot not mentioned
        if self.bot.user == message.author or self.bot.user not in message.mentions:
            return

        # ⛔ TODO: Not from a guid? what to do ?
        # ⛔ TODO: Fix image attachement (maybe implement compression)
        if not message.guild:
            await message.reply("Wa are in DM right? 🤔")
            return

        # Prepare prompts
        text_prompt = f"{message.author.name}: {message.content.replace(self.bot.user.mention, "").strip()}"
        image_prompt: bytes = bytes(0)

        # Load all members who interacted before
        actors = self.load_actors(message.guild)
        if actors:
            text_prompt += f"\n{text_csv(actors, "|")}"

        # Add attachment
        if message.attachments:
            attachment = message.attachments[0]
            content_type, content = await self.process_attachment(attachment)
            match content_type:
                case "text":
                    text_prompt += f"_sent text file:{attachment.filename}_"
                    text_prompt += content  # type: ignore
                case "image":
                    text_prompt += f"_sent image:{attachment.filename}_"
                    image_prompt = content  # type: ignore
                case "video":
                    text_prompt += f"_sent video:{attachment.filename}_"
                case _:
                    text_prompt += f"_sent file:{attachment.filename}_"

        # Prompt AI
        log.info(f"[Prompt] {text_prompt} <image:{len(image_prompt)}bytes>")
        try:
            self.ai.use_session(
                message.guild.id, history=self.load_history(message.guild)
            )
            async with message.channel.typing():
                reply = self.ai.prompt(text=text_prompt, data=image_prompt)
        except APIError as e:
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
        self.save_actor_interaction(message.guild, message.author)
        self.save_history(message.guild)

    # ----------------------------------------------------------------------------------------------------

    @staticmethod
    async def process_attachment(attachment: Attachment) -> tuple[str, str | bytes]:
        file_type = attachment.content_type.strip() if attachment.content_type else ""
        content_type = file_type.split("/")[0]
        if content_type == "text":
            content = (await attachment.read()).decode("utf-8")
        elif content_type in ("image", "audio", "video"):
            content = await attachment.read()
        else:
            content = file_type
        return (content_type, content)

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

    # async def sleep_in_channel(self, channel_id):
    #     self.cooldowns[channel_id] = True
    #     sleep_time = 60  # 1 minute
    #     log.loading(f"Sleeping for {sleep_time} seconds in channel {channel_id}...")
    #     await asyncio.sleep(60)
    #     log.info(f"Awake from sleep in channel {channel_id}.")
    #     self.cooldowns.pop(channel_id, None)
