from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color
from services.db import get_user_data, save_user_data
from datetime import datetime, timedelta
import random

class RobBank(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rob_bank", description="Attempt to rob a bank! High risk, high reward.")
    async def rob_bank(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        user_data = get_user_data(user_id)

        # Ensure the user exists in the database
        if not user_data:
            user_data = {"xp": 0, "last_rob": None}
            save_user_data(user_id, user_data)

        # Check cooldown
        now = datetime.utcnow()
        last_rob = user_data.get("last_rob")
        cooldown_time = timedelta(hours=1)  # Set cooldown to 1 hour

        if last_rob and now - last_rob < cooldown_time:
            remaining_time = cooldown_time - (now - last_rob)
            await interaction.response.send_message(
                f"⏳ You need to wait {remaining_time.seconds // 60} minutes before trying again!",
                ephemeral=True
            )
            return

        # Set success rate and rewards/penalties
        success_chance = 0.5  # 50% chance of success
        success_amount = random.randint(100, 500)  # XPs gained on success
        failure_penalty = random.randint(50, 300)  # XPs lost on failure

        # Check for "🚗 Escape Car" in inventory
        has_escape_car = "🚗 Escape Car" in user_data["inventory"]
        if has_escape_car:
            success_chance = 0.75  # Tripled success chance
            success_amount = random.randint(500, 1500)  # Tripled reward
            # Remove the Escape Car from the inventory
            user_data["inventory"].remove("🚗 Escape Car")

        # Attempt robbery
        if random.random() < success_chance:
            # Success: Add XPs
            user_data["xp"] += success_amount
            if has_escape_car:
                result_message = (f"🚗 The **Escape Car** tripled your heist to **{success_amount} XPs**! The car is now used up.")
            else:
                result_message = f"🎉 Success! You managed to rob the bank and got **{success_amount} XPs**!"
        else:
            # Failure: Deduct XPs
            if user_data["xp"] >= failure_penalty:
                user_data["xp"] -= failure_penalty
            else:
                failure_penalty = user_data["xp"] 
                user_data["xp"] = 0 
            result_message = (
                f"🚨 You got caught trying to rob the bank and lost **{failure_penalty} XPs**. Better luck next time!"
            )

        # Update last rob time and save data
        user_data["last_rob"] = now
        save_user_data(user_id, user_data)

        # Send response
        embed = Embed(
            title="💰 Rob Bank Results",
            description=result_message,
            color=Color.red() if "caught" in result_message else Color.green()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)