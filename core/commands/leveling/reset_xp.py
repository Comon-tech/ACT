from discord.ext import commands
from discord import app_commands, Interaction, Member
from services.db import get_user_data, save_user_data

class ResetXP(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #command to reset user XP
    @app_commands.command(name="reset_xp", description="Reset the XP of a user.")
    async def reset_xp(interaction: Interaction, member: Member):
        user_id = str(member.id)
        user_data = get_user_data(user_id)

        user_data["xp"] = 0
        save_user_data(user_id, user_data)
        await interaction.response.send(f"✅ {member.mention}'s XP has been reset.")