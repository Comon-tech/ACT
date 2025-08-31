from discord import (
    Attachment,
    Interaction,
    Member,
    TextChannel,
    Thread,
    User,
    VoiceChannel,
    app_commands,
)
from discord.ext.commands import Cog
from discord.utils import MISSING

from bot.main import ActBot
from bot.ui.embed import EmbedX
from bot.ui.modal import TextParagraphModal
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
    @app_commands.command(
        description="Patch database records", extras={"category": "Console"}
    )
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
    @app_commands.command(
        description="Synchronize commands", extras={"category": "Console"}
    )
    async def sync(self, interaction: Interaction, global_sync: bool = True):
        await interaction.response.defer(ephemeral=True)
        count = await self.bot.sync_commands(None if global_sync else interaction.guild)
        await interaction.followup.send(
            embed=EmbedX.success(
                title="Commands Synchronization",
                description=f"{count[0]}/{count[1]} command(s) synchronized{" globally" if global_sync else f" to guild: {interaction.guild}"}.",
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
        extras={"category": "Console"},
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
    @app_commands.command(
        description="Connect, disconnect, or switch voice channel",
        extras={"category": "Console"},
    )
    async def join(self, interaction: Interaction, channel: VoiceChannel | None = None):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if not guild:
            return

        voice_client = guild.voice_client

        try:
            if channel:
                if voice_client:
                    if voice_client.channel.id == channel.id:
                        return await interaction.followup.send(
                            embed=EmbedX.info(f"Already in {channel.mention}."),
                            ephemeral=True,
                        )
                    await voice_client.move_to(channel)
                    await interaction.followup.send(
                        embed=EmbedX.info(f"Switched to {channel.mention}."),
                        ephemeral=True,
                    )
                else:
                    await channel.connect()
                    await interaction.followup.send(
                        embed=EmbedX.info(f"Joined {channel.mention}."), ephemeral=True
                    )
            else:
                if voice_client:
                    await voice_client.disconnect()
                    await interaction.followup.send(
                        embed=EmbedX.info("Disconnected from voice channel."),
                        ephemeral=True,
                    )
                else:
                    await interaction.followup.send(
                        embed=EmbedX.warning(
                            "Not in a voice channel. Provide a channel to join."
                        ),
                        ephemeral=True,
                    )
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedX.error(f"An error occurred: {e}"),
                ephemeral=True,
            )

    # ----------------------------------------------------------------------------------------------------
    # * Proxy
    # ----------------------------------------------------------------------------------------------------
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        description="Send a message on your behalf", extras={"category": "Console"}
    )
    @app_commands.describe(
        attachment="File to send along with text",
    )
    async def proxy(
        self,
        interaction: Interaction,
        attachment: Attachment | None = None,
    ):
        await interaction.response.send_modal(TextParagraphModal(attachment=attachment))

    # ----------------------------------------------------------------------------------------------------
    # * Purge
    # ----------------------------------------------------------------------------------------------------
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        description="Purge messages in current channel", extras={"category": "Console"}
    )
    @app_commands.describe(
        limit="Maximum number of messages to purge (default: 1)",
        member="Only purge messages from this member (optional)",
        before="Purge messages before this message ID (optional)",
        after="Purge messages after this message ID (optional)",
    )
    async def purge(
        self,
        interaction: Interaction,
        limit: int = 1,
        member: Member | User | None = None,
        before: str | None = None,
        after: str | None = None,
    ):
        """
        Purge messages in the current channel with better handling of before/after fields.
        """
        try:
            await interaction.response.defer(ephemeral=True)
            channel = interaction.channel
            if not channel:
                return await interaction.followup.send(
                    embed=EmbedX.error("No channel to purge messages from."),
                    ephemeral=True,
                )
            if not (isinstance(channel, TextChannel) or isinstance(channel, Thread)):
                return await interaction.followup.send(
                    embed=EmbedX.error(
                        "This command can only be used in text channels."
                    ),
                    ephemeral=True,
                )

            # Convert before and after to discord.Message objects if provided
            before_msg = None
            after_msg = None
            try:
                if before:
                    before_msg = await channel.fetch_message(int(before))
                if after:
                    after_msg = await channel.fetch_message(int(after))
            except Exception as e:
                return await interaction.followup.send(
                    embed=EmbedX.error(f"Invalid message ID provided: {e}"),
                    ephemeral=True,
                )

            # Purge messages
            deleted = await channel.purge(
                limit=limit,
                check=(lambda msg: msg.author == member) if member else MISSING,
                before=before_msg,
                after=after_msg,
            )
            await interaction.followup.send(
                embed=EmbedX.success(
                    f"Purged {len(deleted)} message(s){f" by {member.mention}" if member else ""}."
                ),
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(
                embed=EmbedX.error(f"Failed to purge messages: {e}"), ephemeral=True
            )
