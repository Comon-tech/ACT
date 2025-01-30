from discord.ext import commands
from discord import app_commands, Interaction, Embed, Member, Color
from services.db import get_user_data, save_user_data

class Balance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your or another user's balance.")
    async def balance(self, interaction: Interaction, user: Member = None):
        # Use the command invoker if no user is mentioned
        user = user or interaction.user

        # Get user data from the database
        user_id = str(user.id)
        user_data = get_user_data(user_id)  # Replace with your database query function

        # Ensure the user exists in the database
        if not user_data:
            user_data = {"xp": 0}  # Default xp if user is not yet in the database
            save_user_data(user_id, user_data)  # Optionally initialize the user in the database

        # Fetch xp
        balance = user_data.get("xp", 0)

        # Create response
        embed = Embed(
            title=f"{user.display_name}'s Balance",
            description=f"💰 **{balance} XPs**",
            color=Color.gold()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        # Send the response
        await interaction.response.send_message(embed=embed)