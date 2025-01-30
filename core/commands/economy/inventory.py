from discord.ext import commands
from discord import app_commands, Interaction, Member, Embed, Color
from services.db import get_user_data
from collections import Counter

class Inventory(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="Check the items in your inventory or someone else's.")
    async def inventory(interaction: Interaction, user: Member = None):
        # Use the command invoker if no user is mentioned
        user = user or interaction.user
        
        user_id = str(user.id)  # Use the mentioned user's ID
        user_data = get_user_data(user_id)  # Fetch the correct user's data

        if not user_data or "inventory" not in user_data or not user_data["inventory"]:
            embed = Embed(
                title="🎒 Inventory",
                description=(
                    f"{user.mention}, their inventory is empty." if user != interaction.user else
                    f"{user.mention}, your inventory is empty."
                ),
                color=Color.gold()
            )
            embed.set_thumbnail(url=user.display_avatar.url)

            await interaction.response.send_message(embed=embed)
            return

        inventory_items = user_data["inventory"]
        item_counts = Counter(inventory_items)  # Count occurrences of each item

        # Format the inventory to show "Item XCount"
        formatted_inventory = "\n".join(
            f"{item} x{count}" for item, count in item_counts.items()
        )

        embed = Embed(
            title=f"{user.display_name}'s Inventory:",
            description=f"**{formatted_inventory}**",
            color=Color.gold()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
    