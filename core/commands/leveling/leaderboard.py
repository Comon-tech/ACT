from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color
from services.db import user_collection

class Leaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Leaderboard command
    @app_commands.command(name="leaderboard", description="Get the TACT leaderboard")
    async def leaderboard(self, interaction: Interaction):
        # Acknowledge the interaction
        await interaction.response.defer()  # Keeps the interaction alive

        # Fetch users sorted by level (descending) and XP (descending) for tiebreaker
        sorted_users = list(user_collection.find().sort([("level", -1), ("xp", -1)]))
        
        if not sorted_users:
            await interaction.followup.send("No users found in the leaderboard.")
            return

        # Create an embed for the leaderboard
        embed = Embed(
            title="🏆 TACT Leaderboard",
            color=Color.gold()
        )

        for i, user_data in enumerate(sorted_users[:10]):  # Top 10 users
            try:
                # Fetch the user's Discord info
                user = await self.bot.fetch_user(int(user_data["user_id"]))
                user_display = user.name
            except Exception:
                # If the user is not found (e.g., left the server), use their ID
                user_display = f"Unknown User ({user_data['user_id']})"
            
            # Add the user to the leaderboard
            embed.add_field(
                #display user avatar next to their name
                name=f"{i+1}. {user_display} ",
                value=f"Level: {user_data['level']} | XP: {user_data['xp']} \n[Avatar]({user.display_avatar.url})",
                inline=False
            )

        await interaction.followup.send(embed=embed)