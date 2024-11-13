import discord  # type: ignore
from discord.ext import commands  # type: ignore
from discord import Embed  # type: ignore
import dotenv  # type: ignore
import os  # type: ignore
import random
import json

dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# XP and level data storage
user_xp = {}

def save_data():
    with open("xp_data.json", "w") as file:
        json.dump(user_xp, file)

def load_data():
    global user_xp
    try:
        with open("xp_data.json", "r") as file:
            user_xp = json.load(file)
    except FileNotFoundError:
        user_xp = {}

def get_user_data(user_id):
    """Ensures that each user has the necessary data structure, including XP, level, and inventory."""
    if user_id not in user_xp:
        user_xp[user_id] = {"xp": 0, "level": 1, "inventory": []}
    elif "inventory" not in user_xp[user_id]:
        user_xp[user_id]["inventory"] = []
    return user_xp[user_id]

@bot.event
async def on_ready():
    load_data()
    print(f"Rewards Bot is ready! Logged in as {bot.user}")

# Set XP required to level up
def get_xp_needed(level):
    return 5 * (level ** 2) + 50 * level + 100

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore messages from bots

    user_id = str(message.author.id)
    if user_id not in user_xp:
        user_xp[user_id] = {"xp": 0, "level": 1}

    # Award random XP between 5 and 10
    xp_earned = random.randint(5, 10)
    user_xp[user_id]["xp"] += xp_earned

    # Check if user leveled up
    current_level = user_xp[user_id]["level"]
    xp_needed = get_xp_needed(current_level)
    if user_xp[user_id]["xp"] >= xp_needed:
        user_xp[user_id]["level"] += 1
        user_xp[user_id]["xp"] = 0  # Reset XP after level up
        await message.channel.send(f"🎉 {message.author.mention} leveled up to level {user_xp[user_id]['level']}!")

    save_data()  # Save XP data
    await bot.process_commands(message)  # Ensure other commands can still run

# Show user's current XP and level
@bot.command()
async def level(ctx):
    user_id = str(ctx.author.id)
    if user_id in user_xp:
        user_level = user_xp[user_id]["level"]
        xp = user_xp[user_id]["xp"]
        xp_needed = get_xp_needed(user_level)

        await ctx.send(f"{ctx.author.mention}, you are level {level} with {xp}/{xp_needed} XP.")
    else:
        await ctx.send(f"{ctx.author.mention}, you haven't earned any XP yet. Start chatting to level up!")

# Leaderboard command
@bot.command()
async def leaderboard(ctx):
    sorted_users = sorted(user_xp.items(), key=lambda x: x[1]['level'], reverse=True)
    leaderboard_text = "**Leaderboard**\n\n"
    
    for i, (user_id, data) in enumerate(sorted_users[:10]):  # Top 10 users
        user = await bot.fetch_user(user_id)
        leaderboard_text += f"{i+1}. {user.name} - Level {data['level']} ({data['xp']} XP)\n"
    
    await ctx.send(leaderboard_text)

# Give XP command (admin-only)
@bot.command()
# @commands.has_permissions(administrator=True)
async def give_xp(ctx, member: discord.Member, amount: int):
    user_id = str(member.id)
    giver = ctx.author  # Get the user who invoked the command
    
    if user_id not in user_xp:
        user_xp[user_id] = {"xp": 0, "level": 1}
    
    user_xp[user_id]["xp"] += amount
    await ctx.send(f"✅ {giver.mention} has given {amount} XP to {member.mention}. {member.mention} now has {user_xp[user_id]['xp']} XP.")

    save_data()  # Save the data

# Reset XP command (admin-only)
@bot.command()
@commands.has_permissions(administrator=True)
async def reset_xp(ctx, member: discord.Member):
    user_id = str(member.id)
    if user_id in user_xp:
        user_xp[user_id] = {"xp": 0, "level": 1}
        await ctx.send(f"✅ {member.mention}'s XP has been reset.")
    else:
        await ctx.send(f"{member.mention} has no XP data to reset.")

    save_data()  # Save the data

# Server stats command (admin-only)
@bot.command()
@commands.has_permissions(administrator=True)
async def server_stats(ctx):
    total_users = len(user_xp)
    total_xp = sum(user['xp'] for user in user_xp.values())
    avg_level = sum(user['level'] for user in user_xp.values()) / total_users if total_users > 0 else 0

    stats = f"**Server Stats**\n\nTotal Users: {total_users}\nTotal XP: {total_xp}\nAverage Level: {avg_level:.2f}"
    await ctx.send(stats)

# Store items and prices
store_items = {
    "Basic Potion": 50,  # 50 XP
    "Advanced Potion": 150,  # 150 XP
    "Special Badge": 200,  # 200 XP
}

# Helper function to get a user's current balance
def get_balance(user_id):
    return user_xp.get(user_id, {"xp": 0, "level": 1})["xp"]
     
# Crime: Steal XP from another user
@bot.command()
async def steal(ctx, member: discord.Member):
    thief_id = str(ctx.author.id)
    victim_id = str(member.id)
    
    if victim_id == thief_id:
        await ctx.send("You can't steal from yourself!")
        return

    if user_xp[victim_id]["xp"] <= 0:
        await ctx.send(f"{member.mention} has no XP to steal.")
        return

    stolen_xp = random.randint(1, min(20, user_xp[victim_id]["xp"]))
    user_xp[thief_id]["xp"] += stolen_xp
    user_xp[victim_id]["xp"] -= stolen_xp

    await ctx.send(f"💰 {ctx.author.mention} stole {stolen_xp} XP from {member.mention}!")

    save_data()

# Crime: Shoot another user (for fun, no XP effect)
@bot.command()
async def shoot(ctx, member: discord.Member):
    if ctx.author.id == member.id:
        await ctx.send("You can't shoot yourself!")
    else:
        await ctx.send(f"🔫 {ctx.author.mention} shot {member.mention}! 💥")

# Crime: Rob a bank (for fun, no XP effect)
@bot.command()
async def rob_bank(ctx):
    await ctx.send(f"🏦 {ctx.author.mention} is robbing the bank! 💰💰💰")

@bot.command()
async def buy(ctx, item: str):
    user_id = str(ctx.author.id)
    user_data = get_user_data(user_id)

    item_price = store_items.get(item)
    if item_price is None:
        await ctx.send(f"❌ {item} is not available in the store.")
        return

    if user_data["xp"] < item_price:
        await ctx.send(f"❌ You need {item_price} XP to buy {item}.")
    else:
        user_data["xp"] -= item_price
        user_data["inventory"].append(item)
        await ctx.send(f"✅ {ctx.author.mention} bought {item} for {item_price} XP.")

        save_data()

@bot.command()
async def inventory(ctx):
    user_id = str(ctx.author.id)
    user_data = get_user_data(user_id)

    inventory_items = user_data["inventory"]
    if not inventory_items:
        await ctx.send(f"{ctx.author.mention}, your inventory is empty.")
    else:
        items_list = ', '.join(inventory_items)
        await ctx.send(f"{ctx.author.mention}, your inventory: {items_list}.")

@bot.command()
async def store(ctx):
    store_list = "\n".join([f"{item}: {price} XP" for item, price in store_items.items()])
    await ctx.send(f"\n**🛒 Available items for purchase:**\n```{store_list}```")

bot.run(os.getenv('DISCORD_TOKEN'))
