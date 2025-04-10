from discord import (
    Attachment,
    ClientException,
    Interaction,
    TextInput,
    TextStyle,
    VoiceChannel,
    app_commands,
)
from discord.abc import Messageable
from discord.ext.commands import Cog
from discord.ui import Modal
from ui import TextParagraphModal

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor
from db.main import DbRef
from utils.log import logger

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * Console Cog
# ----------------------------------------------------------------------------------------------------
class ConsoleCog(Cog, description="Provide control and management interface"):
    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------
    # * Patch
    # ----------------------------------------------------------------------------------------------------
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(description="Patch database records")
    async def migrate_data(self, interaction: Interaction):
        return await interaction.response.send_message(
            embed=EmbedX.info("No patch currently.")
        )
        db_api = self.bot._db
        if not db_api:
            log.error("No database api available")
        main_db_engine = db_api.get_engine()
        db_refs = main_db_engine.find(DbRef)
        for db_ref in db_refs:
            db_engine = db_api.get_engine(db_ref.id)
            if not db_engine:
                continue
            raw_actors = db_engine.database[Actor.__collection__].find()
            unset_fields = {"equipment": 1, "equipped_items": 1, "item_stacks": 1}
            for raw_actor in raw_actors:
                actor_id = raw_actor.get("_id")
                db_engine.database[Actor.__collection__].update_one(
                    {"_id": actor_id}, {"$unset": unset_fields}
                )
                log.info(
                    f"Removed {', '.join(unset_fields.keys())} for Actor record: {actor_id} in {db_ref.name}"
                )

    # ----------------------------------------------------------------------------------------------------
    # * Sync
    # ----------------------------------------------------------------------------------------------------
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(description="Synchronize commands")
    async def sync(self, interaction: Interaction, global_sync: bool = True):
        await interaction.response.defer(ephemeral=True)
        count = await self.bot.sync_commands(None if global_sync else interaction.guild)
        await interaction.followup.send(
            embed=EmbedX.success(
                title="Commands Synchronization",
                description=f"{count[0]}/{count[1]} command(s) synchronized.",
            ),
            ephemeral=True,
        )

    # ----------------------------------------------------------------------------------------------------
    # * Sync Actors
    # ----------------------------------------------------------------------------------------------------
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        description="Update actors with fresh data from associated guild members",
    )
    async def sync_actors(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if not guild:
            return
        db = self.bot.get_db(guild)
        actors = list(db.find(Actor))
        removed_members_count = 0
        for actor in actors:
            member = None
            try:
                member = guild.get_member(actor.id) or await guild.fetch_member(
                    actor.id
                )
            except:
                pass
            if member:
                actor.is_member = True
                actor.name = member.name
                actor.display_name = member.display_name
            else:
                actor.is_member = False
                removed_members_count += 1
        db.save_all(actors)
        await interaction.followup.send(
            embed=EmbedX.success(
                title="Actors Synchronization",
                description=f"{len(actors)} actor(s) synchronized.\n{removed_members_count} actor(s) no longer members.",
            ),
            ephemeral=True,
        )

    # ----------------------------------------------------------------------------------------------------
    # * Join
    # ----------------------------------------------------------------------------------------------------
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(description="Add bot to a voice channel")
    async def join(self, interaction: Interaction, channel: VoiceChannel):
        try:
            await channel.connect()
            await interaction.response.send_message(
                embed=EmbedX.info(f"Joined {channel.name}."), ephemeral=True
            )
        except ClientException:
            await interaction.response.send_message(
                embed=EmbedX.warning("Already in a voice channel."), ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=EmbedX.error(f"Could not join the voice channel: {e}"),
                ephemeral=True,
            )

    # ----------------------------------------------------------------------------------------------------
    # * Proxy
    # ----------------------------------------------------------------------------------------------------
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(description="Send a message on your behalf")
    @app_commands.describe(attachment="File to send along with text")
    async def proxy(
        self,
        interaction: Interaction,
        attachment: Attachment | None = None,
    ):
        await interaction.response.send_modal(TextParagraphModal(attachment=attachment))
