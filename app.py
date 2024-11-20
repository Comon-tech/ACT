import datetime
import time
import discord  # type: ignore
from discord import app_commands
from discord.ext import commands  # type: ignore
from discord import Embed  # type: ignore
import dotenv  # type: ignore
import os  # type: ignore
import random
import json
from db import user_collection, store_collection
from datetime import datetime, timedelta

dotenv.load_dotenv()


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

shoot_cooldowns = {}

def get_user_data(user_id):
    user_data = user_collection.find_one({"user_id": user_id})
    if not user_data:
        user_data = {"user_id": user_id, "xp": 0, "level": 1, "inventory": [], "balance": 0}
        user_collection.insert_one(user_data)
    return user_data

def save_user_data(user_id, data):
    user_collection.update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True
    )

def award_xp(user_id, xp):
    user_data = get_user_data(user_id)
    user_data["xp"] += xp
    xp_needed = get_xp_needed(user_data["level"])
    while user_data["xp"] >= xp_needed:
        user_data["level"] += 1
        user_data["xp"] -= xp_needed
        xp_needed = get_xp_needed(user_data["level"])
    save_user_data(user_id, user_data)
    return user_data


@bot.event
async def on_ready():
    # load_data()
    print(f"Rewards Bot is ready! Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# Set XP required to level up
def get_xp_needed(level):
    return 5 * (level ** 2) + 50 * level + 100

@bot.event
async def on_message(message):
    user_id = str(message.author.id)
    user_data = get_user_data(user_id)

    xp_needed = get_xp_needed(user_data["level"])
    # Award random XP between 5 and 10
    xp_earned = random.randint(5, 10)
    award_xp(user_id, xp_earned)

    await bot.process_commands(message)  # Ensure other commands can still run

# Leaderboard command
@bot.tree.command(name="leaderboard", description="Get the TACT leaderboard")
async def leaderboard(interaction: discord.Interaction):
    sorted_users = sorted(user_collection.find(), key=lambda x: x['level'], reverse=True)
    leaderboard_text = "**Leaderboard**\n\n"
    
    for i, user_data in enumerate(sorted_users[:10]):  # Top 10 users
        user = await bot.fetch_user(user_data['user_id'])
        leaderboard_text += f"{i+1}. {user.name} - Level {user_data['level']} ({user_data['xp']} XP)\n"
    
    await interaction.response.send_message(leaderboard_text)

@bot.tree.command(name="level", description="Get your TACT level")
async def level(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = get_user_data(user_id)

    user_level = user_data["level"]
    xp_needed = get_xp_needed(user_level)

    await interaction.response.send_message(f"{interaction.user.mention}, you are in level `{user_level}` with `{user_data['xp']}`/`{xp_needed}` XP.")


# Give XP command
@bot.tree.command(name="give_xp", description="Give XP to a user")
@app_commands.describe(member="User to give XP", amount="Amount of XP to give")
async def give_xp(interaction: discord.Interaction, member: discord.Member, amount: int):
    user_id = str(member.id)
    giver = interaction.user  # Get the user who invoked the command

    user_data = user_data(user_id)
    
    if user_id not in user_data:
        user_data[user_id] = {"xp": 0, "level": 1}
    
    user_data[user_id]["xp"] += amount
    await interaction.response.send_message(f"✅ {giver.mention} has given {amount} XP to {member.mention}. {member.mention} now has {user_data[user_id]['xp']} XP.")

    save_user_data(user_id, user_data)  # Save the data

# Reset XP command (admin-only)
@bot.command()
@commands.has_permissions(administrator=True)
async def reset_xp(ctx, member: discord.Member):
    user_id = str(member.id)
    user_data = get_user_data(user_id)

    if user_id in user_data:
        user_data[user_id] = {"xp": 0, "level": 1}
        await ctx.send(f"✅ {member.mention}'s XP has been reset.")
    else:
        await ctx.send(f"{member.mention} has no XP data to reset.")

    save_user_data(user_id, user_data)  # Save the data

@bot.tree.command(name="balance", description="Check your or another user's balance.")
async def balance(interaction: discord.Interaction, user: discord.Member = None):
    # Use the command invoker if no user is mentioned
    user = user or interaction.user

    # Get user data from the database
    user_id = str(user.id)
    user_data = get_user_data(user_id)  # Replace with your database query function

    # Ensure the user exists in the database
    if not user_data:
        user_data = {"balance": 0}  # Default balance if user is not yet in the database
        save_user_data(user_id, user_data)  # Optionally initialize the user in the database

    # Fetch balance
    balance = user_data.get("balance", 0)

    # Create response
    embed = discord.Embed(
        title=f"{user.display_name}'s Balance",
        description=f"💰 **{balance} coins**",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    # Send the response
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="inventory", description="Check the items in your inventory")
async def inventory(interaction: discord.Interaction, user: discord.Member = None):
    
    # Use the command invoker if no user is mentioned
    user = user or interaction.user
    
    user_id = str(interaction.user.id)
    user_data = get_user_data(user_id)

    inventory_items = user_data["inventory"]
    if not inventory_items:
        await interaction.response.send_message(f"{interaction.user.mention}, your inventory is empty.")
    else:
        items_list = ', '.join(inventory_items)
        embed = discord.Embed(
        title=f"{user.display_name}'s Inventory:",
        description=f"**{items_list} **",
        color=discord.Color.gold()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.response.send_message(embed=embed)


# Cooldown tracker
rob_cooldowns = {}

@bot.tree.command(name="rob_bank", description="Attempt to rob a bank! High risk, high reward.")
async def rob_bank(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = get_user_data(user_id)

    # Ensure the user exists in the database
    if not user_data:
        user_data = {"balance": 0, "last_rob": None}
        save_user_data(user_id, user_data)

    # Check cooldown
    now = datetime.utcnow()
    last_rob = user_data.get("last_rob")
    cooldown_time = datetime.timedelta(hours=1)  # Set cooldown to 1 hour

    if last_rob and now - last_rob < cooldown_time:
        remaining_time = cooldown_time - (now - last_rob)
        await interaction.response.send_message(
            f"⏳ You need to wait {remaining_time.seconds // 60} minutes before trying again!",
            ephemeral=True
        )
        return

    # Set success rate and rewards/penalties
    success_chance = 0.5  # 50% chance of success
    success_amount = random.randint(100, 500)  # Coins gained on success
    failure_penalty = random.randint(50, 300)  # Coins lost on failure

    # Attempt robbery
    if random.random() < success_chance:
        # Success: Add coins
        user_data["balance"] += success_amount
        result_message = f"🎉 Success! You managed to rob the bank and got **{success_amount} coins**!"
    else:
        # Failure: Deduct coins
        if user_data["balance"] >= failure_penalty:
            user_data["balance"] -= failure_penalty
        else:
            failure_penalty = user_data["balance"]
            user_data["balance"] = 0
        result_message = (
            f"🚨 You got caught trying to rob the bank and lost **{failure_penalty} coins**. Better luck next time!"
        )

    # Update last rob time and save data
    user_data["last_rob"] = now
    save_user_data(user_id, user_data)

    # Send response
    embed = discord.Embed(
        title="💰 Rob Bank Results",
        description=result_message,
        color=discord.Color.red() if "caught" in result_message else discord.Color.green()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name="buy", description="Buy itesm from the shop")
async def buy(interaction: discord.Interaction, item: str):
    user_id = str(interaction.user.id)
    user_data = get_user_data(user_id)

    store_items = {item["item_name"]: item["item_price"] for item in store_collection.find()}

    item_price = store_items.get(item)
    if item_price is None:
        await interaction.response.send_message(f"❌ {item} is not available in the store.")
        return

    if user_data["xp"] < int(item_price):
        await interaction.response.send_message(f"❌ You need {item_price} XP to buy {item}.")
    else:
        user_data["xp"] -= int(item_price)
        user_data["inventory"].append(item)
        await interaction.response.send_message(f"✅ {interaction.user.mention} bought {item} for {item_price} XP.")

    save_user_data(user_id, user_data)

@bot.tree.command(name="steal", description="Attempt to steal from another user.")
async def steal(interaction: discord.Interaction, target: discord.Member):
    thief_id = str(interaction.user.id)
    victim_id = str(target.id)

    # Ensure thief isn't targeting themselves
    if thief_id == victim_id:
        await interaction.response.send_message("You can't steal from yourself!", ephemeral=True)
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
        await interaction.response.send_message(
            f"⏳ You need to wait {remaining_time // 60} minutes before stealing again!",
            ephemeral=True
        )
        return

    # Chance of success
    success_rate = 0.7  # 70% chance to succeed
    success = random.random() < success_rate

    if success:
        # Calculate stolen amount
        stolen_amount = random.randint(50, 200)  # Steal between 50 and 200 coins
        stolen_amount = min(stolen_amount, victim["balance"])  # Can't steal more than the victim's balance

        # Update balances
        thief["balance"] += stolen_amount
        victim["balance"] -= stolen_amount

        # Update timestamps and save
        thief["last_steal"] = current_time
        save_user_data(thief_id, thief)
        save_user_data(victim_id, victim)

        await interaction.response.send_message(
            f"🎉 You successfully stole `{stolen_amount}` coins from {target.mention}!"
        )
    else:
        # Failed attempt penalty
        penalty = random.randint(20, 100)  # Lose between 20 and 100 coins
        thief["balance"] -= penalty
        thief["balance"] = max(thief["balance"], 0)  # Prevent negative balance

        # Update timestamps and save
        thief["last_steal"] = current_time
        save_user_data(thief_id, thief)

        await interaction.response.send_message(
            f"❌ You got caught and lost `{penalty}` coins as a penalty!"
        )

@bot.tree.command(name="shoot", description="Shoot another user for a chance to win coins!")
async def shoot(interaction: discord.Interaction, target: discord.Member):
    attacker_id = str(interaction.user.id)
    target_id = str(target.id)

    # Prevent self-targeting
    if interaction.user == target:
        await interaction.response.send_message(
            "🔫 You can't shoot yourself!", ephemeral=True
        )
        return

    # Retrieve attacker and target data
    attacker_data = get_user_data(attacker_id)
    target_data = get_user_data(target_id)

    if not attacker_data or not target_data:
        await interaction.response.send_message(
            "🔍 Both users must be registered to participate!", ephemeral=True
        )
        return

    # Check cooldown
    now = datetime.utcnow()
    last_shoot = shoot_cooldowns.get(attacker_id, None)
    cooldown_time = timedelta(minutes=5)  # Cooldown duration

    if last_shoot and now - last_shoot < cooldown_time:
        remaining_time = cooldown_time - (now - last_shoot)
        await interaction.response.send_message(
            f"⏳ You need to wait {remaining_time.seconds} seconds before shooting again!",
            ephemeral=True
        )
        return

    # Set success chance, rewards, and penalties
    success_chance = 0.6  # 60% chance to hit
    reward = random.randint(50, 200)  # Coins gained on success
    penalty = random.randint(30, 100)  # Coins lost on failure

    # Attempt to shoot
    if random.random() < success_chance:
        # Success: Attacker steals coins from the target
        if target_data["balance"] >= reward:
            target_data["balance"] -= reward
        else:
            reward = target_data["balance"]
            target_data["balance"] = 0

        attacker_data["balance"] += reward
        result_message = (
            f"🎯 {interaction.user.mention} successfully shot {target.mention} and stole **{reward} coins**!"
        )
    else:
        # Failure: Attacker loses coins
        if attacker_data["balance"] >= penalty:
            attacker_data["balance"] -= penalty
        else:
            penalty = attacker_data["balance"]
            attacker_data["balance"] = 0

        result_message = (
            f"❌ {interaction.user.mention} missed their shot and lost **{penalty} coins**!"
        )

    # Save updated data
    save_user_data(attacker_id, attacker_data)
    save_user_data(target_id, target_data)

    # Update cooldown
    shoot_cooldowns[attacker_id] = now

    # Send result as an embed
    embed = discord.Embed(
        title="🔫 Shoot Results",
        description=result_message,
        color=discord.Color.green() if "successfully" in result_message else discord.Color.red()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="store", description="Checkout the store")
async def store(interaction: discord.Interaction):
    store_list = "\n".join([f"{item['item_name']}: {item['item_price']} XP" for item in store_collection.find()])
    await interaction.response.send_message(f"\n**🛒 Available items for purchase:**\n```{store_list}```")


bot.run(os.getenv('DISCORD_TOKEN'))
