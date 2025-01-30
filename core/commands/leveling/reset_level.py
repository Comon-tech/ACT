from discord.ext import commands
from discord import app_commands, Interaction, Member, Embed, Color
from services.db import get_user_data, save_user_data

class ResetLevel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #command to reset user level
    @app_commands.command(name="reset_level", description="Reset the level of a user.")
    async def reset_level(interaction: Interaction, member: Member):
        user_id = str(member.id)
        user_data = get_user_data(user_id)

        user_data["level"] = 0
        save_user_data(user_id, user_data)  # Save the data
        await interaction.response.send_message(f"✅ {member.mention}'s XP has been reset.")