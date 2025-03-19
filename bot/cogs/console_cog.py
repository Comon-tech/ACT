from discord import ClientException, Interaction, VoiceChannel, app_commands
from discord.ext.commands import Cog

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Console Cog
# ----------------------------------------------------------------------------------------------------
class ConsoleCog(Cog, description="Provide control and management interface"):
    def __init__(self, bot: ActBot):
        self.bot = bot

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
