import pathlib

from colorama import Fore
from discord import (
    Color,
    Embed,
    Guild,
    Interaction,
    Member,
    Message,
    Permissions,
    User,
    VoiceClient,
    app_commands,
)
from discord.ext.commands import Bot, Cog
from odmantic import SyncEngine

from bot.ui import EmbedX
from db.actor import Actor
from db.main import ActDb, DbRef
from utils.log import logger
from utils.misc import import_classes, text_block

log = logger(__name__)
VoiceClient.warn_nacl = False  # Hide "PyNaCl" warning


# ----------------------------------------------------------------------------------------------------
# * Act Bot
# ----------------------------------------------------------------------------------------------------
class ActBot(Bot):
    def __init__(
        self,
        *args,
        token="",
        db: ActDb | None = None,
        api_keys: dict[str, str] = {},
        title="",
        version="",
        description="",
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._token = token
        self._db = db
        self.api_keys = api_keys
        self.title = title
        self.version = version
        self.description = description
        self.tree.error(self.on_error)

    async def setup_hook(self):
        await self.load_cogs()
        log.loading("Bot client connecting...")

    # ----------------------------------------------------------------------------------------------------
    # * On Ready
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_ready(self):
        log.success(f"🎮 Bot client connected as {self.user}.")
        log.info("\n" + self.cogs_info_text)
        log.info("\n" + self.app_commands_info_text)
        log.info("\n" + await self.app_commands_remote_info_text)
        log.info("\n" + self.commands_info_text)
        # await self.sync_commands()

    # ----------------------------------------------------------------------------------------------------
    # * On Message
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_message(self, message: Message):
        self.log_message(message)
        await self.process_commands(message)

    # ----------------------------------------------------------------------------------------------------
    # * On Error
    # ----------------------------------------------------------------------------------------------------
    async def on_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        embed = EmbedX.error(f"{error}", "Unexpected Error")
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)
        log.exception(error)

    # ----------------------------------------------------------------------------------------------------

    async def load_cogs(self):
        cog_classes = import_classes(f"{pathlib.Path(__file__).parent}/cogs", Cog)
        log.loading("Loading cogs...")
        for cog_class in cog_classes:
            try:
                cog: Cog = cog_class(self)
                await self.add_cog(cog)
                log.info(
                    f"{cog.qualified_name} cog loaded from {cog.__module__} module."
                )
            except Exception as e:
                log.error(
                    f"Error loading {cog_class.qualified_name} cog from {cog_class.__module__} module:\t",
                    e,
                )
        log.success(f"{len(self.cogs)}/{len(cog_classes)} cogs loaded.")

    async def sync_commands(self) -> tuple[int, int]:
        """Sync commands and get (synced, all) commands count."""
        log.loading("Syncing commands...")
        all_cmds = self.tree.get_commands()
        synced_cmds = await self.tree.sync()
        for cmd in synced_cmds:
            log.info(f"{cmd} command synced.")
        count = (len(synced_cmds), len(all_cmds))
        log.success(f"{count[0]}/{count[1]} commands synced.")
        return count

    # ----------------------------------------------------------------------------------------------------

    @property
    def cogs_info_text(self):
        output = "Cogs:"
        for cog_name, cog in self.cogs.items():
            commands_str = ", ".join(
                f"{Fore.CYAN}{self.command_prefix}{cmd.qualified_name}{Fore.RESET}"
                for cmd in cog.walk_commands()
            )
            app_commands_str = ", ".join(
                f"{Fore.CYAN}/{cmd.qualified_name}{Fore.RESET}"
                for cmd in cog.walk_app_commands()
            )
            listeners_str = ", ".join(
                f"{Fore.CYAN}@{name}{Fore.RESET}" for name, func in cog.get_listeners()
            )

            output += f"\n• {cog_name}: {cog.description}"
            for s in (
                app_commands_str,
                commands_str,
                listeners_str,
            ):
                if s:
                    output += f"\n {s}"
        return text_block(output)

    @property
    def app_commands_info_text(self):
        output = "App Commands:"
        for cmd in self.tree.walk_commands():
            output += (
                f"\n• {Fore.CYAN}/{cmd.qualified_name}{Fore.RESET}: {cmd.description}"
            )
        return text_block(output)

    @property
    async def app_commands_remote_info_text(self):
        output = f"{Fore.GREEN}Remote{Fore.RESET} App Commands:"
        for cmd in await self.tree.fetch_commands():
            output += f"\n• {Fore.CYAN}/{cmd.name}{Fore.RESET}: {cmd.description}"
        return text_block(output)

    @property
    def commands_info_text(self):
        output = "Commands:"
        for cmd in self.walk_commands():
            output += f"\n• {Fore.CYAN}{self.command_prefix}{cmd.qualified_name}{Fore.RESET}: {cmd.description}"
        return text_block(output)

    # ----------------------------------------------------------------------------------------------------

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

    def get_db(self, guild: Guild | None = None) -> SyncEngine:
        """Get database engine with database of given guild. If no guild, get engine with main database. If nonexistent, create."""
        if self._db:
            db = (
                self._db.get_engine(guild.id, guild.name)
                if guild
                else self._db.get_engine()
            )
            if db:
                return db
        raise ValueError("Missing database.")

    def create_db_ref(self, guild: Guild) -> DbRef:
        """Get database reference of given guild. If nonexistent, create."""
        return DbRef(id=guild.id, name=guild.name)

    def create_actor(self, member: Member | User) -> Actor:
        """Create actor from given member."""
        return Actor(
            id=member.id,
            name=member.name,
            display_name=member.display_name,
            avatar_url=member.display_avatar.url if member.avatar else "",
        )

    # ----------------------------------------------------------------------------------------------------

    async def open(self):
        log.loading(f"Bot client opening...")
        await self.start(token=self._token)

    async def close(self):
        log.loading(f"Bot client closing...")
        await super().close()
        log.success(f"Bot client closed.")
