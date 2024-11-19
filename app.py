import discord  # type: ignore
from discord import app_commands
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

# Temporary storage for last bumper
last_bumper = None

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
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name="hello", description="This is an hello command")
async def hello(interaction:discord.Interaction):
    await interaction.response.send_message(f"hey {interaction.user.mention} this is a slash command",
                                             ephemeral=True)

@bot.tree.command(name="say")
@app_commands.describe(thing_to_say="Say something")
async def say(interaction:discord.Interaction, thing_to_say:str):
    await interaction.response.send_message(f"{interaction.user.name} said: `{thing_to_say}`")

# Set XP required to level up
def get_xp_needed(level):
    return 5 * (level ** 2) + 50 * level + 100

@bot.event
async def on_message(message):
    # Skip if the message is from your bot or other bots except Arcane and Disboard
    if message.author.bot and message.author.name != "Arcane" and message.author.id != 302050872383242240:
        await bot.process_commands(message)  # Allow other commands to process
        return

    # Detect if the user issued the "/bump" command
    if message.content.lower() == "/bump":
        await message.channel.send(f"{message.author} has bumped the server!")
        last_bumper = message.author.id  # Store the bumper's ID temporarily

    # Check if Disboard confirms the bump
    elif message.author.id == 302050872383242240 and "Bump done!" in message.content:  # Disboard bot's ID
        if last_bumper:
            bumper_id = str(last_bumper)
            bumper_data = get_user_data(bumper_id)

            bump_xp = 50  # Customize XP amount for a bump
            bumper_data["xp"] += bump_xp

            bumper_user = await bot.fetch_user(bumper_id)
            await message.channel.send(f"✅ {bumper_user.mention} has received {bump_xp} XP for bumping the server!")
            
            last_bumper = None  # Reset after awarding XP
            save_data()  # Save XP data

    # Check for Arcane's level-up announcement in Arcane's message
    if message.author.name == "Arcane" and "leveled up to level" in message.content:
        # Parse the user mention from the message
        user_mention = message.mentions[0] if message.mentions else None
        if user_mention:
            user_id = str(user_mention.id)

            # Award XP for leveling up
            xp_award = 50  # Set the amount of XP to award on level up with Arcane
            if user_id not in user_xp:
                user_xp[user_id] = {"xp": 0, "level": 1, "inventory": []}

            user_xp[user_id]["xp"] += xp_award
            await message.channel.send(f"✅ {user_mention.mention} earned {xp_award} XP for leveling up!")

            save_data()  # Save XP data
    
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
        user_xp[user_id]["xp"] -= xp_needed  # Subtract the XP needed to level up, rather than resetting to zero
        await message.channel.send(f"🎉 {message.author.mention} leveled up to level {user_xp[user_id]['level']}!")

    save_data()  # Save XP data
    await bot.process_commands(message)  # Ensure other commands can still run

# Show user's current XP and level
@bot.tree.command(name="level", description="Get your TACT level")
async def level(interaction: discord.Interaction ):
    user_id = str(interaction.user.id)
    if user_id in user_xp:
        user_level = user_xp[user_id]["level"]
        xp = user_xp[user_id]["xp"]
        xp_needed = get_xp_needed(user_level)

        await interaction.response.send_message(f"{interaction.user.mention}, you are in level `{user_level}` with `{xp}`/`{xp_needed}` XP.")
    else:
        await interaction.response.send_message(f"{interaction.user.mention}, you haven't earned any XP yet. Start chatting to level up!")

# Leaderboard command
@bot.tree.command(name="leaderboard", description="Get the TACT leaderboard")
async def leaderboard(interaction: discord.Interaction):
    sorted_users = sorted(user_xp.items(), key=lambda x: x[1]['level'], reverse=True)
    leaderboard_text = "**Leaderboard**\n\n"
    
    for i, (user_id, data) in enumerate(sorted_users[:10]):  # Top 10 users
        user = await bot.fetch_user(user_id)
        leaderboard_text += f"{i+1}. {user.name} - Level {data['level']} ({data['xp']} XP)\n"
    
    await interaction.response.send_message(leaderboard_text)

# Give XP command
@bot.tree.command(name="give_xp", description="Give XP to a user")
@app_commands.describe(member="User to give XP", amount="Amount of XP to give")
async def give_xp(interaction: discord.Interaction, member: discord.Member, amount: int):
    user_id = str(member.id)
    giver = interaction.user  # Get the user who invoked the command
    
    if user_id not in user_xp:
        user_xp[user_id] = {"xp": 0, "level": 1}
    
    user_xp[user_id]["xp"] += amount
    await interaction.response.send_message(f"✅ {giver.mention} has given {amount} XP to {member.mention}. {member.mention} now has {user_xp[user_id]['xp']} XP.")

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

#get user's current balance
@bot.tree.command(name="balance", description="Get your TACT balance")
async def balance(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    balance = get_balance(user_id)
    await interaction.response.send_message(f"{interaction.user.mention}, your current balance is `{balance}` XP.")

# Crime: Steal XP from another user
@bot.tree.command(name="steal", description="Steal xp from user! (risky)")
async def steal(interaction: discord.Interaction, member: discord.Member):
    thief_id = str(interaction.user.id)
    victim_id = str(member.id)
    
    if victim_id == thief_id:
        await interaction.response.send_message("You can't steal from yourself!")
        return

    if user_xp[victim_id]["xp"] <= 0:
        await interaction.response.send_message(f"{member.mention} has no XP to steal.")
        return

    stolen_xp = random.randint(1, min(20, user_xp[victim_id]["xp"]))
    user_xp[thief_id]["xp"] += stolen_xp
    user_xp[victim_id]["xp"] -= stolen_xp

    await interaction.response.send_message(f"💰 {interaction.user.mention} stole {stolen_xp} XP from {member.mention}!")

    save_data()

# Crime: Shoot another user (for fun, no XP effect)
@bot.tree.command(name="shoot", description="Shoot a user!")
async def shoot(interaction: discord.Interaction, member: discord.Member):
    if interaction.user.id == member.id:
        await interaction.response.send_message("You can't shoot yourself!")
    else:
        await interaction.response.send_message(f"🔫 {interaction.user.mention} shot {member.mention}! 💥")

# Crime: Rob a bank (for fun, no XP effect)
@bot.tree.command(name="rob_bank", description="Rob a bank! (riscky)")
async def rob_bank(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏦 {interaction.user.mention} is robbing the bank! 💰💰💰")

@bot.tree.command(name="buy", description="Buy itesm from the shop")
async def buy(interaction: discord.Interaction, item: str):
    user_id = str(interaction.user.id)
    user_data = get_user_data(user_id)

    item_price = store_items.get(item)
    if item_price is None:
        await interaction.response.send_message(f"❌ {item} is not available in the store.")
        return

    if user_data["xp"] < item_price:
        await interaction.response.send_message(f"❌ You need {item_price} XP to buy {item}.")
    else:
        user_data["xp"] -= item_price
        user_data["inventory"].append(item)
        await interaction.response.send_message(f"✅ {interaction.user.mention} bought {item} for {item_price} XP.")

        save_data()

@bot.tree.command(name="inventory", description="Check the items in your inventory")
async def inventory(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = get_user_data(user_id)

    inventory_items = user_data["inventory"]
    if not inventory_items:
        await interaction.response.send_message(f"{interaction.user.mention}, your inventory is empty.")
    else:
        items_list = ', '.join(inventory_items)
        await interaction.response.send_message(f"{interaction.user.mention}, your inventory:\n ```{items_list}```")

@bot.tree.command(name="store", description="Checkout the store")
async def store(interaction: discord.Interaction):
    store_list = "\n".join([f"{item}: {price} XP" for item, price in store_items.items()])
    await interaction.response.send_message(f"\n**🛒 Available items for purchase:**\n```{store_list}```")

bot.run(os.getenv('DISCORD_TOKEN'))
