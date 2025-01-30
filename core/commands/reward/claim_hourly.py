from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color
from services.db import get_user_data, save_user_data
from datetime import datetime, timedelta

class ClaimHourly(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_hourly_claim = {} # Track last hourly claim times in a database or dictionary

    @app_commands.command(name="claim_hourly", description="Claim your hourly reward!")
    async def claim_hourly(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        now = datetime.utcnow()
        reward_xp = 600  # Amount of XP given as an hourly reward

        # Check if the user has already claimed the reward this hour
        if user_id in self.last_hourly_claim:
            last_claim_time = self.last_hourly_claim[user_id]
            if now - last_claim_time < timedelta(hours=1):
                next_claim_time = last_claim_time + timedelta(hours=1)
                remaining_time = next_claim_time - now

                embed = Embed(
                    title="⏳ Claim your hourly reward!",
                    description=f"⏳ You have already claimed your hourly reward. Come back in {remaining_time.seconds // 60} minutes.",
                    color=Color.gold()
                    )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)

                await interaction.response.send_message(embed=embed)
                return

        # Update last claim time and give reward
        self.last_hourly_claim[user_id] = now
        user_data = get_user_data(user_id)
        user_data["xp"] += reward_xp
        save_user_data(user_id, user_data)

        embed = Embed(
            title="⏳ Claim your hourly reward!",
            description=f"🕒 {interaction.user.mention}, you have claimed your **{reward_xp} XP** hourly reward!",
            color=Color.gold()
            )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)