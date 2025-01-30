from discord.ext import commands
from discord import app_commands, Interaction, Member, Embed, Color
from services.db import get_user_data, save_user_data

class GiveXP(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def setup(bot):
        bot.add_cog(GiveXP(bot))

    @app_commands.command(name="give_xp", description="Give some XPs to your friends!")
    async def give_xp(interaction: Interaction, member: Member, xp: int):

        interaction.response.defer()
        # Validate input
        if xp <= 0:
            await interaction.response.send_message("XP must be a positive number.")
            return

        # Retrieve user data
        user_id = str(member.id)
        user_data = get_user_data(user_id)
        if not user_data:
            await interaction.response.send_message("User not found!")
            return
        
        #check if user is trying to give themselves XP 
        if interaction.user == member:
            embed = Embed(
                title="❌ XP Not Awarded!!",
                description="You can't give yourself XP!",
                color=Color.red()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

        # Add XP and update user data
        user_data["xp"] = user_data.get("xp", 0) + xp
        save_user_data(user_id, user_data)

        # Create the response embed
        embed = Embed(
            title="✅ XP Awarded",
            description=(
                f"{interaction.user.mention} has awarded **{xp} XP** to {member.mention}!\n"
                f"**{member.display_name}** now has **{user_data['xp']} XP**."
            ),
            color=Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # Respond with confirmation
        await interaction.response.send_message(embed=embed)