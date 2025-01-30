from discord.ext import commands
from discord import app_commands, Interaction, Embed, Member, Color
from services.db import get_user_data, save_user_data
import random
from datetime import datetime, timedelta

class Shoot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shoot_cooldowns = {}

    @app_commands.command(name="shoot", description="Shoot another user for a chance to win XPs!")
    async def shoot(self, interaction: Interaction, target: Member):
        attacker_id = str(interaction.user.id)
        target_id = str(target.id)

        # Prevent self-targeting
        if interaction.user == target:
            embed = Embed(
                title="🔫 Shoot Results",
                description="🔫 You can't shoot yourself.",
                color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Retrieve attacker and target data
        attacker_data = get_user_data(attacker_id)
        target_data = get_user_data(target_id)

        if not attacker_data or not target_data:
            embed = Embed(
                title="🔫 Shoot Results",
                description="🔍 Both users must be registered to participate!",
                color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if attacker has bullets in inventory (handling inventory as a list)
        inventory = attacker_data.get("inventory", [])
        bullet_count = sum(1 for item in inventory if item == "✏ Bullet")

        if bullet_count < 1:
            embed = Embed(
                title="🔫 Shoot Results",
                description="❌ You don't have any bullets to shoot. Buy some from the store!",
                color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Remove one bullet from inventory
        inventory.remove("✏ Bullet")
        attacker_data["inventory"] = inventory

        # Check if target has the shield
        target_inventory = target_data.get("inventory", [])
        if "🛡 Shield of Protection" in target_inventory:
            # Shield protects the target
            target_inventory.remove("🛡 Shield of Protection")
            target_data["inventory"] = target_inventory
            save_user_data(target_id, target_data)  # Save updated target data

            embed = Embed(
                title="🛡 Shield Activated!",
                description=(
                    f"{target.mention} was protected by the **🛡 Shield of Protection**! "
                    f"The shield blocked {interaction.user.mention}'s attack!"
                ),
                color=Color.blue()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

        # Check cooldown
        now = datetime.utcnow()
        last_shoot = self.shoot_cooldowns.get(attacker_id, None)
        cooldown_time = timedelta(minutes=5)  # Cooldown duration

        if last_shoot and now - last_shoot < cooldown_time:
            remaining_time = cooldown_time - (now - last_shoot)
            embed = Embed(
                title="🔫 Shoot Results",
                description=f"⏳ You need to wait {remaining_time.seconds} seconds before shooting again!",
                color=Color.red()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Set success chance, rewards, and penalties
        success_chance = 0.6  # 60% chance to hit
        reward = random.randint(50, 2000)  # XPs gained on success
        penalty = random.randint(30, 1000)  # XPs lost on failure

        # Attempt to shoot
        if random.random() < success_chance:
            # Success: Attacker steals XPs from the target
            if target_data["xp"] >= reward:
                target_data["xp"] -= reward
            else:
                reward = target_data["xp"]
                target_data["xp"] = 0

            attacker_data["xp"] += reward
            result_message = (
                f"🎯 {interaction.user.mention} successfully shot {target.mention} and stole **{reward} XPs**!"
            )
        else:
            # Failure: Attacker loses XPs
            if attacker_data["xp"] >= penalty:
                attacker_data["xp"] -= penalty
            else:
                penalty = attacker_data["xp"]
                attacker_data["xp"] = 0

            result_message = (
                f"❌ {interaction.user.mention} missed their shot and lost **{penalty} XPs**!"
            )

        # Save updated data
        save_user_data(attacker_id, attacker_data)
        save_user_data(target_id, target_data)

        # Update cooldown
        self.shoot_cooldowns[attacker_id] = now

        # Send result as an embed
        embed = Embed(
            title="🔫 Shoot Results",
            description=result_message,
            color=Color.green() if "successfully" in result_message else Color.red()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)