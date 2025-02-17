import discord
from colorama import Fore
from discord import Color, Embed, Guild, Interaction, Message, Status, app_commands
from discord.ext import commands
from discord.ext.commands import Bot, Cog, GroupCog
from pymongo.database import Database

from bot.main import ActBot
from bot.ui import EmbedX
from db.main import ActDbClient
from utils.log import logger
from utils.misc import import_classes, text_block


class Act(GroupCog, description="ACT control panel."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @app_commands.guild_only()
    class Act(app_commands.Group, description="Manage"):
        def __init__(self, bot: ActBot):
            self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(description="Say hi! 😀")
    async def hi(self, interaction: Interaction):
        await interaction.response.send_message("Hello 🙋‍♀️")

    @app_commands.command(description="Its cat wow!")
    async def cat(self, interaction: Interaction):
        await interaction.response.send_message("Meow! 🐱")
