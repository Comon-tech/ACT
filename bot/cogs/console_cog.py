from discord import ClientException, Interaction, VoiceChannel, app_commands
from discord.ext.commands import Cog

from bot.main import ActBot
from bot.ui import EmbedX


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
