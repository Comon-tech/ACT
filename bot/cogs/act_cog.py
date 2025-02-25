import discord
from colorama import Fore
from discord import (
    Color,
    Embed,
    Guild,
    Interaction,
    Message,
    Permissions,
    Status,
    app_commands,
)
from discord.ext import commands
from discord.ext.commands import Bot, Cog, GroupCog
from humanize import naturaltime
from pymongo.database import Database

from bot.main import ActBot
from db.main import ActDb
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

    @app_commands.guild_only
    @app_commands.command(description="Show all roles")
    async def roles(self, interaction: Interaction):
        await interaction.response.defer()
        guild = interaction.guild
        roles = (
            sorted(guild.roles, key=lambda role: role.position, reverse=True)
            if guild
            else []
        )
        embed = Embed(title="🎭 Roles", color=Color.blue())
        embed.add_field(name="", value="", inline=False)
        for role in roles:
            embed.add_field(name="", value="", inline=False)
            embed.add_field(name=role.name, value="")
            embed.add_field(name=f"👥 {len(role.members)}", value="")
        if not len(embed.fields):
            embed.description = "_No roles found in this server._"
        await interaction.followup.send(embed=embed)
