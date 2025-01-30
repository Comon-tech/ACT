from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color
from services.db import get_user_data, save_user_data, store_collection
import random

class OpenBox(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="open_box", description="Open a mystery box for surprises!")
    async def open_box(self, interaction: Interaction):

        # rewards from the store
        rewards = list(store_collection.find())
        reward = random.choice(rewards)
        user_data = get_user_data(str(interaction.user.id))

        # check if user has the 📦 Mystery Box in their inventory
        if "📦 Mystery Box" not in user_data.get("inventory", []):
            embed = Embed(
                title="🎁 Mystery Box",
                description="❌ You need a **📦 Mystery Box** to open it!",
                color=Color.gold()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return
        
        if type(reward) != dict and reward.endswith("XP"):
            user_data["xp"] += int(reward.split(" ")[0])
        else:
            user_data["inventory"].append(reward['item_name'])

        # Remove the mystery box from the user's inventory
        user_data["inventory"].remove("📦 Mystery Box")

        save_user_data(str(interaction.user.id), user_data)
        embed = Embed(
            title="🎁 Mystery Box",
            description=f"🎁 You opened a mystery box and received: {reward['item_name']}!",
            color=Color.gold()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)