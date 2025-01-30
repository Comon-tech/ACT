from discord.ext import commands
from discord import app_commands, Interaction, Embed, Member, Color
from services.db import get_user_data, save_user_data
import time
import random

class Steal(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="steal", description="Attempt to steal from another user.")
    async def steal(self, interaction: Interaction, target: Member):
        thief_id = str(interaction.user.id) #'673eb3f1491a384eb6545a19'
        victim_id = str(target.id)

        # Ensure thief isn't targeting themselves
        if thief_id == victim_id:
            embed = Embed(
            title="🔫 Steal Results",
            description="🔫 You can't steal from yourself",
            color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Fetch thief and victim data
        thief = get_user_data(thief_id)
        victim = get_user_data(victim_id)

        # Cooldown logic
        cooldown = 3600  # 1 hour cooldown in seconds
        current_time = int(time.time())
        time_since_last_steal = current_time - thief.get("last_steal", 0)
        
        if time_since_last_steal < cooldown:
            remaining_time = cooldown - time_since_last_steal
            embed = Embed(
            title="🔫 Steal Results",
            description=f"⏳ You need to wait {remaining_time // 60} minutes before stealing again!",
            color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(
                f"⏳ You need to wait {remaining_time // 60} minutes before stealing again!",
                ephemeral=True
            )
            return

        # Chance of success
        success_rate = 0.7  # 70% chance to succeed
        success = random.random() < success_rate

        if success:
            stolen_amount = self.steal_function(victim_id)

            if stolen_amount == 0:
                embed = Embed(
                title="🔫 Steal Results",
                description=f"❌ {target.mention} has no XPs to steal!",
                color=Color.red()
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)

                await interaction.response.send_message(embed=embed)
                return

            # Update balances
            thief["xp"] += stolen_amount
            victim["xp"] -= stolen_amount

            # Update timestamps and save
            thief["last_steal"] = current_time
            save_user_data(thief_id, thief)
            save_user_data(victim_id, victim)

            embed = Embed(
            title="🔫 Steal Results",
            description=f"🎉 You successfully stole `{stolen_amount}` XPs from {target.mention}!",
            color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

            await interaction.response.send_message(embed=embed)
        else:
            # Failed attempt penalty
            penalty = random.randint(20, 100)  # Lose between 20 and 100 XPs
            thief["xp"] -= penalty
            thief["xp"] = max(thief["xp"], 0)  # Prevent negative xp

            # Update timestamps and save
            thief["last_steal"] = current_time
            save_user_data(thief_id, thief)

            await interaction.response.send_message(
                f"❌ You got caught and lost `{penalty}` XPs as a penalty!"
            )

        def steal_function(self, victim_id):
            # Fetch victim data
            victim = get_user_data(victim_id)

            stolen_amount = random.randint(50, 2000)  # Steal between 50 and 200 XPs
            stolen_amount = min(stolen_amount, victim["xp"])  # Can't steal more than the victim's balance

            return stolen_amount