from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color
from services.db import get_user_data, save_user_data
import random

class Heist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.heist_participants = []

    @app_commands.command(name="heist", description="Team up to pull off an epic heist!")
    async def heist(self, interaction: Interaction):

        heist_planner = interaction.user
        self.heist_participants = [heist_planner.id]

        embed = Embed(
            title="Epic heist!",
            description=f"💰 A heist is being planned by {interaction.user} ! Type `/join_heist` to participate!",
            color=Color.gold()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="join_heist", description="Join the heist!")
    async def join_heist(self, interaction: Interaction):
        if interaction.user.id not in self.heist_participants:
            self.heist_participants.append(interaction.user.id)

            embed = Embed(
                title="🎭 Heist Participation",
                description=f"{interaction.user.mention} has joined the heist!",
                color=Color.gold()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = Embed(
                title="🎭 Heist Participation",
                description=f"You're already in the heist!",
                color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # To resolve the heist
    async def resolve_heist(self, interaction):
        if len(self.heist_participants) < 1:
            await interaction.channel.send("Not enough participants for the heist. Mission failed! 😔")
            return

        success = random.choice([True, False])
        if success:
            rewards = random.randint(100, 500)
            for user_id in self.heist_participants:
                user_data = get_user_data(str(user_id))
                user_data["xp"] += rewards
                save_user_data(str(user_id), user_data)
            await interaction.channel.send(f"🎉 The heist was successful! Participants earned {rewards} XP each!")
        else:
            await interaction.channel.send("🚨 The heist failed! Better luck next time!")
        self.heist_participants.clear()