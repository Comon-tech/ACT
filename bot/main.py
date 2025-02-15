from colorama import Fore
from discord import Guild, Message
from discord.ext.commands import Bot, Cog
from pymongo.database import Database

from db.main import ActDbClient
from utils.log import logger
from utils.misc import import_classes

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * Act Bot
# ----------------------------------------------------------------------------------------------------
class ActBot(Bot):
    def __init__(
        self,
        *args,
        token="",
        db_client: ActDbClient = None,
        api_keys: dict[str, str] = {},
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.token = token
        self.db_client = db_client
        self.api_keys = api_keys

    async def setup_hook(self):
        await self.load_cogs()
        log.loading("Starting bot...")

    @Cog.listener()
    async def on_ready(self):
        log.success(f"🎮 Bot client connected as {self.user}.")

    @Cog.listener()
    async def on_message(self, message: Message):
        self.log_message(message)

    # ----------------------------------------------------------------------------------------------------

    async def load_cogs(self):
        cog_classes = import_classes("./bot/", Cog)
        log.loading("Loading cogs...")
        for cog_class in cog_classes:
            try:
                cog: Cog = cog_class(self)
                await self.add_cog(cog)
                log.info(f"{cog.qualified_name} cog loaded from {cog.__module__}.")
            except Exception as e:
                log.error(
                    f"Error loading {cog_class.qualified_name} cog from {cog_class.__module__}:\t",
                    e,
                )
        log.success(f"{len(self.cogs)}/{len(cog_classes)} cogs loaded.")

    async def sync_commands(self):
        log.loading("Syncing commands...")
        all_cmds = self.bot.tree.get_commands()
        synced_cmds = await self.bot.tree.sync()
        for cmd in synced_cmds:
            log.info(f"{cmd} command synced.")
        log.success(f"{len(synced_cmds)}/{len(all_cmds)} commands synced.")

    def log_cogs(self):
        log.info("⚙  Cogs:")
        for cog_name in self.bot.cogs:
            cog = self.bot.get_cog(cog_name)
            log.info("\t• ", cog_name, ":", cog.description)
            app_commands_str = ", ".join(
                [f"/{cmd.qualified_name}" for cmd in cog.walk_app_commands()]
            )
            event_listeners_str = ", ".join(
                [f"⚡{name}" for name, func in cog.get_listeners()]
            )
            if app_commands_str:
                log.info("\t\t", app_commands_str)
            if event_listeners_str:
                log.info("\t\t", event_listeners_str)
        log.info()

    def log_app_commands(self):
        log.info("🔘 App Commands (Local):")
        for cmd in self.bot.tree.get_commands():
            log.info("\t/", cmd.name, ":", cmd.description)
        log.info()

    async def log_app_commands_remote(self):
        log.info("🟢 App Commands (Remote):")
        for cmd in await self.bot.tree.fetch_commands():
            log.info("\t/", cmd.name, ":", cmd.description)
        log.info()

    def log_commands(self):
        log.info("⚫ Commands (Local):")
        for cmd in self.bot.commands:
            log.info("\t!", cmd.name, ":", cmd.description)
        log.info()

    def log_message(self, message: Message):
        source = f"[{message.guild}][{message.channel}]"
        author = f"👤{message.author.name}"
        time = message.created_at.strftime("%Y-%m-%d %X")
        full_content = ""
        if message.poll:
            poll = message.poll.question or ""
            full_content = f"<poll:{Fore.CYAN}{poll}{Fore.RESET}>"
        else:
            content = message.content or ""
            attachments = (
                ", ".join([attachment.filename for attachment in message.attachments])
                or ""
            )
            full_content = (
                f'"{Fore.CYAN}{content}{Fore.RESET}" <{Fore.CYAN}{attachments}{Fore.RESET}>'
                if content or attachments
                else ""
            )
        log.info(f"✉  {source} {author}: {full_content} ({time})")

    # ----------------------------------------------------------------------------------------------------

    def get_database(self, guild: Guild) -> Database:
        """Retrieve database by guild. Create if nonexistent."""
        return self.db_client.get_database_by_id(guild.id, guild.name)

    async def enter(self):
        log.loading(f"Bot running...")
        await self.start(token=self.token)

    async def exit(self):
        log.loading(f"Bot exiting...")
        await self.close()
        log.success(f"Bot exited.")
