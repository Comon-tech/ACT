from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color
from services.db import get_user_data, save_user_data
import re
import time
import random
from datetime import datetime, timedelta
from math import ceil
from collections import Counter, defaultdict

class ClaimDaily(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_daily_claim = {} # Track last claim times in a database or dictionary

    @app_commands.command(name="claim_daily", description="Claim your daily reward!")
    async def claim_daily(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        now = datetime.utcnow()
        reward_xp = 1000  # Amount of XP given as a daily reward

        # Check if the user has already claimed the reward today
        if user_id in self.last_daily_claim:
            last_claim_time = self.last_daily_claim[user_id]
            if now - last_claim_time < timedelta(days=1):
                next_claim_time = last_claim_time + timedelta(days=1)
                remaining_time = next_claim_time - now

                embed = Embed(
                    title="⏳ Claim your daily reward!",
                    description=f"⏳ You have already claimed your daily reward. Come back in {remaining_time.seconds // 3600} hours and {(remaining_time.seconds // 60) % 60} minutes.",
                color=Color.gold()
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                await interaction.response.send_message(embed=embed)
                return

        # Update last claim time and give reward
        self.last_daily_claim[user_id] = now
        user_data = get_user_data(user_id)
        user_data["xp"] += reward_xp
        save_user_data(user_id, user_data)

        embed = Embed(
            title="⏳ Claim your daily reward!",
            description=f"🎉 {interaction.user.mention}, you have claimed your **{reward_xp} XP** daily reward!",
            color=Color.gold()
            )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)