from discord import Interaction, app_commands
from discord.ext.commands import Cog

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Console Cog
# ----------------------------------------------------------------------------------------------------
class ConsoleCog(Cog, description="Provides control and management interface."):
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
                description=f"{count[0]}/{count[1]} commands synchronized.",
            ),
            ephemeral=True,
        )

    # @app_commands.guild_only()
    # @app_commands.checks.has_permissions(administrator=True)
    # @app_commands.command(description="Synchronize commands")
    # async def update_actors(self, interaction: Interaction):
    #     if not interaction.guild:
    #         return
    #     await interaction.response.defer(ephemeral=True)
    #     db = self.bot.get_db(interaction.guild)
    #     actors = db.find(Actor)
    #     members = interaction.guild.members
    #     for member in members:
    #         for actor in actors:
    #             if actor.id == member.id:

    #         if not actor:
    #             actor = self.bot.create_actor(member)
    #     db.save_all(actors)
    #     await interaction.followup.send(embed=EmbedX.success(title="", description=f"{len(members)}/{len(actors)} actors updated."))
