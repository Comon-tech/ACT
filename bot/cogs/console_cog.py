import argparse
import shlex

from discord import Color, Embed, Interaction, Member, Message, app_commands
from discord.ext import commands
from discord.ext.commands import Cog, GroupCog
from tabulate import tabulate

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Console Cog
# ----------------------------------------------------------------------------------------------------
class Console(Cog, description="Provides control and management interface."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(description="Synchronize commands")
    async def sync(self, interaction: Interaction):
        count = await self.bot.sync_commands()
        await interaction.response.send_message(
            embed=EmbedX.success(
                title="Commands Synchronization",
                description=f"{count[0]}/{count[1]} commands synchronized.",
            ),
            ephemeral=True,
        )
