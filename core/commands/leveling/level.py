from discord.ext import commands
from discord import app_commands, Interaction, Member, Embed, Color
from services.db import get_user_data

class Level(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="level", description="Get a user's TACT level")
    async def level(self, interaction: Interaction, user: Member = None):
        # Use the mentioned user if provided, otherwise default to the command invoker
        user = user or interaction.user
        user_id = str(user.id)
        
        # Fetch the user's data from the database
        user_data = get_user_data(user_id)
        level = user_data.get("level", 1)
        xp = user_data.get("xp", 0)

        # Build an embed with the level information
        embed = Embed(
            title=f"{user.display_name}'s Level",
            description=f"**Level:** {level}\n**XP:** {xp} / {self.get_xp_needed(level + 1)}",
            color=Color.blue()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        # Send the response
        await interaction.response.send_message(embed=embed)

    @staticmethod
    def get_xp_needed(level):
        # XP needed for next level should be more than the previous level and have a gap of 1000
        # return 5 * (level ** 2) + 50 * level + 100
        return 1000 + (level - 1) ** 2 * 1000