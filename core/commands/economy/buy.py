from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color
from services.db import get_user_data, save_user_data
from services.db import store_collection
from .store import Store

class Buy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    # Buy command with autocomplete and quantity
    @app_commands.command(name="buy", description="Buy items from the shop")
    @app_commands.describe(item="The item you want to purchase", quantity="The number of items you want to buy (default: 1)")
    @app_commands.autocomplete(item=Store.item_autocomplete_fn())
    async def buy(self, interaction: Interaction, item: str, quantity: int = 1):
        user_id = str(interaction.user.id)
        user_data = get_user_data(user_id)

        # Fetch store items and prices
        store_items = {item_data["item_name"]: item_data["item_price"] for item_data in store_collection.find()}

        # Check if the item exists in the store
        item_price = store_items.get(item)
        if item_price is None:
            embed = Embed(
                title="🛒 Purchase Unsuccessful !!",
                description=f"❌ {item} is not available in the store.",
                color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

        # Validate quantity
        if quantity <= 0:
            embed = Embed(
                title="🛒 Purchase Unsuccessful !!",
                description="❌ Quantity must be a positive number greater than zero.",
                color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

        # Calculate total cost
        total_cost = int(item_price) * quantity

        # Check if the user has enough XP
        if user_data["xp"] < total_cost:
            embed = Embed(
                title="🛒 Purchase Unsuccessful !!",
                description=f"❌ You need {total_cost} XP to buy {quantity} x {item}.",
                color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

        # Deduct XP and add items to inventory
        user_data["xp"] -= total_cost
        user_data["inventory"].extend([item] * quantity)

        # Send success message
        embed = Embed(
            title="🛒 Purchase Successful",
            description=(
                f"✅ {interaction.user.mention} bought {quantity} x {item} for {total_cost} XP.\n"
                f"💰 Remaining XP: {user_data['xp']}"
            ),
            color=Color.green()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

        # Save updated user data
        save_user_data(user_id, user_data)

    