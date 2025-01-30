from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color
from services.db import get_user_data, save_user_data
import re
import time
import random
from datetime import datetime, timedelta
from math import ceil
from collections import Counter, defaultdict

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Get help with the commands")
    async def help(self, interaction: Interaction):
        embed = Embed(
            title="📚 TACT Bot Help",
            description=(
                "Welcome to the TACT Bot! Here are some of the available commands:\n"
                "**/balance**: Check your balance\n"
                "**/leaderboard**: View the top users\n"
                "**/level**: Check your level\n"
                "**/steal**: Attempt to steal from another user\n"
                "**/shoot**: Shoot another user for a chance to win XPs\n"
                "**/rob_bank**: Attempt to rob a bank\n"
                "**/store**: View items available for purchase\n"
                "**/buy**: Buy items from the store\n"
                "**/gift**: Gift an item to another user\n"
                "**/inventory**: Check your inventory\n"
                "**/give_xp**: Give XP to another user\n"
                "**/heist**: Team up to pull off an epic heist\n"
                "**/join_heist**: Join the heist\n"
                "**/open_box**: Open a mystery box for surprises\n"
                "**/claim_daily**: Claim your daily reward\n"
                "**/claim_hourly**: Claim your hourly reward\n"
                "**/help**: Get help with the commands"
                "\n\nUse these commands to explore the TACT Bot features!"

            ),
            color=Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)