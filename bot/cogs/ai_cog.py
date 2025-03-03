import asyncio
import pathlib
import tomllib
from datetime import UTC, datetime, timedelta
from random import choice, randint

from discord import (
    Attachment,
    Embed,
    Guild,
    Interaction,
    Member,
    Message,
    User,
    app_commands,
)
from discord.abc import Messageable
from discord.ext import tasks
from discord.ext.commands import Cog
from google.genai.errors import APIError
from humanize import naturaldelta
from odmantic import query

from bot.main import ActBot
from bot.ui import EmbedX
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
class AiCog(Cog, description="Integrated generative AI chat bot."):
    CONFIG_PATH = pathlib.Path(__file__).parent / "ai_cog.toml"
    MAX_ACTORS = 10
    MAX_FILE_SIZE = 524288  # 524,288 B == 512 KB == 0.5 MB
    COOLDOWN_TIME = 60  # 60 sec == 1 min
    INCENTIVE_WAIT_TIME_RANGE = (3600, 43200)  # (3600, 43200) sec == (1, 12) hr

    def __init__(self, bot: ActBot):
        self.bot = bot
        with open(self.CONFIG_PATH, "rb") as file:
            config = tomllib.load(file)
        persona_name = "activa"
        persona_desc = config.get("personas", {}).get(persona_name)
        self.ai = ActAi(
            api_key=bot.api_keys.get("gemini", ""), instructions=persona_desc
        )
        log.info(f"AI persona @{persona_name} used.")
        self.guilds_cooldown_time_left: dict[int, int] = {}  #  { guild_id: seconds }
        self.guilds_incentive_tasks = {}  # { guild_id: task }
        self.guild_incentive_startup_task.start()

    def cog_unload(self):
        self.guild_cooldown_task.cancel()
        self.guild_incentive_startup_task.cancel()
        for task in self.guilds_incentive_tasks.values():
            task.cancel()

    # ----------------------------------------------------------------------------------------------------
    # * Incite
    # ----------------------------------------------------------------------------------------------------
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.command(description="Incite AI chat bot to interact on its own")
    async def incite(
        self,
        interaction: Interaction,
        prompt: str | None = None,
        member: Member | None = None,
    ):
        # Deny bot-self & DM & non-messageable channel
        if (
            self.bot.user == member
            or not interaction.guild
            or not isinstance(interaction.channel, Messageable)
        ):
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Prepare prompt
        text_prompt = (
            f"Begin natural talk{f" w/ {member.mention} " if member else " "}that feels like ur own initiative."
            f"Absolutely avoid references to instructions, prompts, or being told to message them."
            f"{ f'follow this prompt:"{prompt.strip()}".' if prompt else "" }"
        )

        # Defer response to prevent timeout
        await interaction.response.defer(ephemeral=True)

        # Remember current member & Add previous members to prompt
        if member:
            self.save_actor(interaction.guild, member)
        text_prompt += self.load_actors_csv(interaction.guild)

        # Perform prompt & send reply
        async with interaction.channel.typing():
            try:
                await interaction.followup.send(
                    embed=EmbedX.success(
                        title="Incentive",
                        description=f"{self.bot.user} has been incited to talk {f"with {member.mention}" if member else ""}."
                        f"\n\n**Prompt:**```{text_prompt}```",
                    ),
                    ephemeral=True,
                )
                await interaction.channel.send(
                    self.ai.prompt(text=text_prompt)
                    or f"👋 {member.mention if member else ""}"
                )
            except Exception as e:
                await interaction.followup.send(
                    embed=EmbedX.error(str(e)), ephemeral=True
                )
                log.exception(e)
                return

        # Save history
        self.save_history(interaction.guild)

    # ----------------------------------------------------------------------------------------------------
    # * On Guild Join
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_guild_join(self, guild):
        self.start_incentive_task(guild)

    # ----------------------------------------------------------------------------------------------------
    # * On Message
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_message(self, message: Message):
        # Ignore if bot own message or bot not mentioned
        if self.bot.user == message.author or self.bot.user not in message.mentions:
            return

        # TODO: ⛔ Should we support Direct messages ?
        if not message.guild:
            # await message.reply(f"Wa are in DM right? 🤔")
            return

        # Check cooldown
        cooldown_time_left = self.guilds_cooldown_time_left.get(message.guild.id)
        if cooldown_time_left:
            await message.reply(
                f"Please! 🙏 Give me about {cooldown_time_left} seconds... ⏳"
            )
            return

        # Prepare prompts
        text_prompt = f"{message.author.name}:"
        file_prompt = None

        # Add message content to prompt
        text_prompt += f"{message.content.replace(self.bot.user.mention, "").strip()}"

        # Add message attachment or embed to prompt
        if message.attachments:
            attachment = message.attachments[0]
            text_prompt += f"_sent file:{attachment.filename}_"
            file_prompt = await self.get_file(attachment)
            if not file_prompt:
                text_prompt += f"(but u can't receive it cuz it's larger than ur allowed min size limit of {self.MAX_FILE_SIZE}byte)"
        elif message.embeds:
            text_prompt += f"_sent embed_"
            file_prompt = await self.get_file(message.embeds[0])
            if not file_prompt:
                text_prompt += f"(but u can't receive it cuz it's larger than ur allowed min size limit of {self.MAX_FILE_SIZE}byte)"

        # Remember current member & Add previous members to prompt
        self.save_actor(message.guild, message.author)
        text_prompt += self.load_actors_csv(message.guild)

        # Perform prompt & send reply
        async with message.channel.typing():
            try:
                await message.reply(
                    self.get_reply(message.guild, text_prompt, file_prompt)
                    or "What? 😕"
                )
            except APIError as e:
                await message.reply(
                    "Oops! 😵‍💫 I'm out of energy for now. Give me a moment! 🙏"
                )
                self.guild_cooldown_task.start(message.guild)
                log.exception(e)
                return
            except Exception as e:
                await message.reply(
                    "Sorry! 😵‍💫 There's something wrong with me right now 😭. Give me a moment plz! 🙏"
                )
                log.exception(e)
                return

        # Remember chat session
        self.save_history(message.guild)

    # ----------------------------------------------------------------------------------------------------
    # * Guild Cooldown
    # ----------------------------------------------------------------------------------------------------
    @tasks.loop(seconds=1)
    async def guild_cooldown_task(self, guild: Guild):
        """Cooldown to prevent spamming when needed."""
        time_left = self.guilds_cooldown_time_left.get(guild.id)
        if time_left is None:
            time_left = self.COOLDOWN_TIME + 1
            log.info(f"[{guild.name}] {self.COOLDOWN_TIME} seconds cooldown started.")
        time_left -= 1
        self.guilds_cooldown_time_left[guild.id] = time_left
        if time_left <= 0:
            self.guilds_cooldown_time_left.pop(guild.id, None)
            self.guild_cooldown_task.cancel()
            log.info(f"[{guild.name}] {self.COOLDOWN_TIME} seconds cooldown finished.")

    @guild_cooldown_task.before_loop
    async def before_sleep_in_guild(self):
        await self.bot.wait_until_ready()

    # ----------------------------------------------------------------------------------------------------
    # * Guild Incentive
    # ----------------------------------------------------------------------------------------------------
    @tasks.loop(count=1)
    async def guild_incentive_startup_task(self):
        """Incite bot to send random message to random member. Start separate incentive task for each guild."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            self.start_incentive_task(guild)

    def start_incentive_task(self, guild: Guild):
        """Start incentive task for given guild."""
        # Cancel existing task if there is one
        if (
            guild.id in self.guilds_incentive_tasks
            and not self.guilds_incentive_tasks[guild.id].done()
        ):
            self.guilds_incentive_tasks[guild.id].cancel()

        # Create a new task for this guild
        self.guilds_incentive_tasks[guild.id] = asyncio.create_task(
            self.guild_incentive_loop(guild), name=f"incentive_task_{guild.id}"
        )

    async def guild_incentive_loop(self, guild: Guild):
        """Incentive background looping task coroutine to send messages to random members of a specific guild."""
        try:
            while True:
                # Sleep a random period
                wait_time = randint(
                    self.INCENTIVE_WAIT_TIME_RANGE[0], self.INCENTIVE_WAIT_TIME_RANGE[1]
                )
                log.loading(
                    f"[{guild.name}] Waiting {naturaldelta(timedelta(seconds=wait_time))} for next incentive..."
                )
                await asyncio.sleep(wait_time)

                # Make sure the guild still exists and we're still in it
                if guild not in self.bot.guilds:
                    log.warning(
                        f"[{guild.name}] Bot is no longer in guild, stopping task."
                    )
                    break

                # Get all text channels the bot can send messages in & Choose a random text channel
                text_channels = [
                    channel
                    for channel in guild.text_channels
                    if channel.permissions_for(guild.me).send_messages
                    and channel.permissions_for(guild.me).read_message_history
                ]
                if not text_channels:
                    log.warning(
                        f"[{guild.name}] No accessible text channels found in guild, skipping incentive."
                    )
                    continue
                channel = choice(text_channels)

                #  Get the last messages in the channel
                messages: list[Message] = []
                async for message in channel.history(limit=20):
                    if not message.author.bot:  # Filter out bot messages
                        messages.append(message)
                if not messages:
                    log.warning(
                        f"[{guild.name}][{channel.name}] No recent user messages found in guild channel, skipping incentive."
                    )
                    continue

                # Choose a random message & its author as target member
                message = choice(messages)
                member = message.author

                # Prepare prompt
                text_prompt = (
                    f"Begin natural talk{f" w/ {member.mention} " if member else " "}that feels like ur own initiative."
                    f"Absolutely avoid references to instructions, prompts, or being told to message them."
                )

                # Remember current member & Add previous members to prompt
                self.save_actor(guild, member)
                text_prompt += self.load_actors_csv(guild)

                # Perform prompt & send reply
                async with channel.typing():
                    try:
                        await message.reply(
                            self.ai.prompt(text=text_prompt)
                            or f"👋 {member.mention if member else ""}"
                        )
                    except Exception as e:
                        await channel.send("👋")
                        log.exception(e)
                        return

                # Save history
                self.save_history(guild)
        except asyncio.CancelledError:
            log.warning(f"[{guild.name}] Incentive task was cancelled.")
        except Exception as e:
            log.error(f"[{guild.name}] Incentive task error: {str(e)}")

    @guild_incentive_startup_task.before_loop
    async def before_start_guild_tasks(self):
        await self.bot.wait_until_ready()

    # ----------------------------------------------------------------------------------------------------

    def get_reply(self, guild: Guild, text: str, file: ActFile | None = None):
        log.info(f"[Prompt] {text} <{file}>")
        self.ai.use_session(guild.id, history=self.load_history(guild))
        return self.ai.prompt(text=text, file=file)

    # ----------------------------------------------------------------------------------------------------

    async def get_file(self, attachment_or_embed: Attachment | Embed):
        """Get file from attachment or embed. If file size limit exceeded, get None."""
        if isinstance(attachment_or_embed, Attachment):
            attachment = attachment_or_embed
            if attachment.size <= self.MAX_FILE_SIZE:
                return ActFile(
                    data=await attachment.read(),
                    mime_type=attachment.content_type,
                    name=attachment.filename,
                )
        if isinstance(attachment_or_embed, Embed):
            embed_url = attachment_or_embed.url
            embed_file = ActFile.load(embed_url) if embed_url else None
            if embed_file and embed_file.size <= self.MAX_FILE_SIZE:
                return embed_file

    # ----------------------------------------------------------------------------------------------------

    def save_actor(self, guild: Guild, member: Member | User):
        db = self.bot.get_db(guild)
        if not db:
            return
        actor = db.find_one(Actor, Actor.id == member.id)
        if not actor:
            actor = self.bot.create_actor(member)
        actor.ai_interacted_at = datetime.now(UTC)
        db.save(actor)

    def load_actors(self, guild: Guild):
        db = self.bot.get_db(guild)
        if not db:
            return
        actors = db.find(
            Actor, sort=query.desc(Actor.ai_interacted_at), limit=self.MAX_ACTORS
        )
        return [
            actor.model_dump(include={"id": True, "name": True, "display_name": True})
            for actor in actors
        ]

    def load_actors_csv(self, guild: Guild):
        actors = self.load_actors(guild)
        return f"\n{text_csv(actors, "|")}" if actors else ""

    # ----------------------------------------------------------------------------------------------------

    def save_history(self, guild: Guild):
        main_db = self.bot.get_db()
        if not main_db:
            return
        db_ref = main_db.find_one(DbRef, DbRef.id == guild.id)
        if not db_ref:
            db_ref = self.bot.create_db_ref(guild)
        db_ref.ai_chat_history = self.ai.dump_history(guild.id)
        main_db.save(db_ref)

    def load_history(self, guild: Guild) -> list | None:
        main_db = self.bot.get_db()
        if not main_db:
            return
        db_ref = main_db.find_one(DbRef, DbRef.id == guild.id)
        if db_ref:
            return db_ref.ai_chat_history

    # ----------------------------------------------------------------------------------------------------
