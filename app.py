import asyncio
import re
import time
import discord  # type: ignore
from discord import app_commands  # type: ignore
from discord.ext import commands  # type: ignore
import dotenv  # type: ignore
import os  # type: ignore
import random
from bad_words import check_for_bad_words, split_msg_into_array, offensive_words
from db import user_collection, store_collection
from datetime import datetime, timedelta
from discord.ui import View, Button
from math import ceil
from collections import Counter, defaultdict

dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Store user offenses count
user_offenses = defaultdict(int)

# Penalty system (e.g., lose 50 coins or XP after 5 offenses)
PENALTY_THRESHOLD = 5
PENALTY_AMOUNT = 50  # Amount of coins or XP to be deducted

# Cooldown tracker
shoot_cooldowns = {}
rob_cooldowns = {}
heist_participants = []
# Track last claim times in a database or dictionary
last_daily_claim = {}
# Track last hourly claim times in a database or dictionary
last_hourly_claim = {}

async def random_xp_drop():
    while True:
        await asyncio.sleep(random.randint(3600, 7200))  # 1-2 hours
        channel = bot.get_channel("998348764282634242") 
        reward = random.randint(50, 150)
        lucky_user = random.choice(channel.members)
        user_data = get_user_data(str(lucky_user.id))
        user_data["xp"] += reward
        save_user_data(str(lucky_user.id), user_data)
        await channel.send(f"🎉 Surprise! {lucky_user.mention} just earned {reward} XP!")

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

    print(f"User {user_id} data saved: {data}\n\n")

def award_xp(user_id, xp):
    user_data = get_user_data(user_id)
    user_data["xp"] += xp

    # Level up if XP exceeds the threshold
    while user_data["xp"] >= get_xp_needed(user_data["level"]):
        # user_data["xp"] -= get_xp_needed(user_data["level"])
        user_data["level"] += 1
    
    print(f"User {user_id} leveled up to {user_data['level']}!, with {user_data['xp']} XPs. \n\n")

    save_user_data(user_id, user_data)
    return user_data

# Function to provide autocomplete options
async def item_autocomplete(interaction: discord.Interaction, current: str):
    # Fetch item names from the database and filter based on the user's input
    all_items = [item["item_name"] for item in store_collection.find()]
    matching_items = [app_commands.Choice(name=item, value=item) for item in all_items if current.lower() in item.lower()]
    return matching_items[:25]  # Return up to 25 matches (Discord's limit)
    
@bot.event
async def on_ready():
    # load_data()
    print(f"TACT Bot is ready! Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

def get_xp_needed(level):
    # Example formula: Quadratic scaling for XP
    return 5 * (level ** 2) + 50 * level + 100

# Function to deduct XP
async def apply_penalty(user):
    user_id = str(user.id)
    user_data = get_user_data(user_id)  # Fetch user data from database

    if not user_data:
        return

    # Deduct the penalty amount
    user_data["xp"] -= PENALTY_AMOUNT # Deduct XP
    save_user_data(user_id, user_data)  # Save the updated user data

    # Notify the user about the penalty
    await user.send(f"🚨 ***You have used offensive words too many times. You have been penalized `{PENALTY_AMOUNT}` XP!***")

def remove_links(message):
    """
    Remove URLs (e.g., GIF links) from a message.
    """
    # Regex to match URLs
    url_pattern = r"(https?://\S+)"
    return re.sub(url_pattern, "", message).strip()

#function to add special badge to usernames if they have a certain role
# def get_special_role_badge(member):
#     if member.top_role == discord.utils.get(member.guild.roles, name="Admin"):
#         return "🛡️"
#     if member.top_role == discord.utils.get(member.guild.roles, name="Moderator"):
#         return "🔧"
#     if member.top_role == discord.utils.get(member.guild.roles, name="Intermediate"):
#         return "🔥"
#     if member.top_role == discord.utils.get(member.guild.roles, name="Novice"):
#         return "🌟"
#     if member.top_role == discord.utils.get(member.guild.roles, name="Techie"):
#         return "👨‍💻"
#     if member.top_role == discord.utils.get(member.guild.roles, name="Geek"):
#         return "🤓"
#     if member.top_role == discord.utils.get(member.guild.roles, name="Hacker"):
#         return "👾"
#     if member.top_role == discord.utils.get(member.guild.roles, name="Guru"):
#         return "🧙"
#     if member.top_role == discord.utils.get(member.guild.roles, name="Godlike"):
#         return "🔱"
#     if member.top_role == discord.utils.get(member.guild.roles, name="Wizard"):
#         return "🧙‍♂️"
#     if member.top_role == discord.utils.get(member.guild.roles, name="Princess"):
#         return "👸"
#     return ""

def get_special_role_badge(member):
    role_badges = {
        "Admin": "🛡️",
        "Moderator": "🔧",
        "Intermediate": "🔥",
        "Novice": "🌟",
        "Techie": "👨‍💻",
        "Geek": "🤓",
        "Hacker": "👾",
        "Guru": "🧙",
        "Godlike": "🔱",
        "Wizard": "🧙‍♂️",
        "Princess": "👸",
    }

    for role in member.roles:
        if role.name in role_badges:
            return role_badges[role.name]
    return ""

# Map roles to their respective emojis
role_emoji_map = {
    "Moderator": "🔧",
    "Admin": "🛡️",
    "Intermediate": "🔥",
    "Novice": "🌟",
    "Techie": "👨‍💻",
    "Geek": "🤓",
    "Hacker": "👾",
    "Guru": "🧙",
    "Godlike": "🔱",
    "Wizard": "🧙‍♂️",
    "Princess": "👸"
}

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    member = message.author
    guild = message.guild
    user_data = get_user_data(str(member.id))

    #rename the user's name to include the special badge
    # check if user already has the badge
    # if get_special_role_badge(member) not in member.display_name:
    #     await member.edit(nick=f"{member.display_name} {get_special_role_badge(member)}")

    badge = get_special_role_badge(member)

    # Ensure the bot has permission and check if the nickname needs an update
    # if member.guild.me.guild_permissions.manage_nicknames:
    # Extract current nickname or fallback to username
    current_nick = member.nick or member.name
    expected_nick = f"{current_nick.split(' ')[0]} {badge}".strip()

    if current_nick != expected_nick:
        try:
            await member.edit(nick=expected_nick)
            print(f"Updated nickname for {member.name} to '{expected_nick}'")
        except discord.Forbidden:
            print(f"Failed to update nickname for {member.name} (insufficient permissions).")
        except discord.HTTPException as e:
            print(f"Error updating nickname for {member.name}: {e}")

    if user_data["level"] in range(1, 3):
        role = discord.utils.get(guild.roles, name="Intermediate")
        #only assign role if the user doesn't have it
        if role not in member.roles:
            await member.add_roles(role)

            #award XP to the user
            xp_earned = random.randint(5, 10)
            award_xp(str(member.id), xp_earned)

            #send this message to the channel
            await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

    elif user_data["level"] in range(4, 9):
        role = discord.utils.get(guild.roles, name="Novice")
        #only assign role if the user doesn't have it
        if role not in member.roles:
            await member.add_roles(role)

            #award XP to the user
            xp_earned = random.randint(5, 10)
            award_xp(str(member.id), xp_earned)

            #send this message to the channel
            await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

    elif user_data["level"] in range(11, 16):
        role = discord.utils.get(guild.roles, name="Techie")
        #only assign role if the user doesn't have it
        if role not in member.roles:
            await member.add_roles(role)

            #award XP to the user
            xp_earned = random.randint(5, 10)
            award_xp(str(member.id), xp_earned)

            #send this message to the channel
            await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

    elif user_data["level"] in range(17, 23):
        role = discord.utils.get(guild.roles, name="Geek")
        print(f"User {member.name} is at level {user_data['level']}")
        #only assign role if the user doesn't have it
        if role not in member.roles:
            await member.add_roles(role)

            #award XP to the user
            xp_earned = random.randint(5, 10)
            award_xp(str(member.id), xp_earned)

            #send this message to the channel
            await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

    elif user_data["level"] in range(24, 30):
        role = discord.utils.get(guild.roles, name="Hacker")
        #only assign role if the user doesn't have it
        if role not in member.roles:
            await member.add_roles(role)

            #award XP to the user
            xp_earned = random.randint(5, 10)
            award_xp(str(member.id), xp_earned)

            #send this message to the channel
            await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs !")

    elif user_data["level"] in range(31, 37):
        role = discord.utils.get(guild.roles, name="Guru")
        
        #only assign role if the user doesn't have it
        if role not in member.roles:
            await member.add_roles(role)
            
            #award XP to the user
            xp_earned = random.randint(5, 10)
            award_xp(str(member.id), xp_earned)

            #send this message to the channel
            await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

    elif user_data["level"] in range(43, 49):
        role = discord.utils.get(guild.roles, name="Godlike")
        #only assign role if the user doesn't have it
        if role not in member.roles:
            await member.add_roles(role)

            #award XP to the user
            xp_earned = random.randint(5, 10)
            award_xp(str(member.id), xp_earned)

            #send this message to the channel
            await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

    elif user_data["level"] in range(55, 61):
        role = discord.utils.get(guild.roles, name="Wizard")
        #only assign role if the user doesn't have it
        if role not in member.roles:
            await member.add_roles(role)
            
            #award XP to the user
            xp_earned = random.randint(5, 10)
            award_xp(str(member.id), xp_earned)

            #send this message to the channel
            await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")
            
    for word in offensive_words:
        if word in [message for message in message.content.split(" ")]:
            await message.delete()
            await message.channel.send(
                f"🛑 {message.author.mention}: ||{message.content}||"
            )
            # Increase the offense count
            user_offenses[message.author.id] += 1
            
            if user_offenses[message.author.id] >= PENALTY_THRESHOLD:
                await apply_penalty(message.author)
                await message.channel.send(f"🚨 {message.author.mention}  ***has been penalized `{PENALTY_AMOUNT}` XPs for using offensive words too many times!!.***")
                # Reset the offense count after penalty
                user_offenses[message.author.id] = 0

    user_id = str(message.author.id)
    user_data = get_user_data(user_id)

    xp_needed = get_xp_needed(user_data["level"])
    # Award random XP between 5 and 10
    xp_earned = random.randint(5, 10)
    print(f"User {message.author.name} earned {xp_earned} XP!\n\n")
    award_xp(user_id, xp_earned)

    await bot.process_commands(message)  # Ensure other commands can still run

# Leaderboard command
@bot.tree.command(name="leaderboard", description="Get the TACT leaderboard")
async def leaderboard(interaction: discord.Interaction):
    # Acknowledge the interaction
    await interaction.response.defer()  # Keeps the interaction alive

    # Fetch users sorted by level (descending) and XP (descending) for tiebreaker
    sorted_users = list(user_collection.find().sort([("level", -1), ("xp", -1)]))
    
    if not sorted_users:
        await interaction.followup.send("No users found in the leaderboard.")
        return

    # Create an embed for the leaderboard
    embed = discord.Embed(
        title="🏆 TACT Leaderboard",
        color=discord.Color.gold()
    )

    for i, user_data in enumerate(sorted_users[:10]):  # Top 10 users
        try:
            # Fetch the user's Discord info
            user = await bot.fetch_user(int(user_data["user_id"]))
            user_display = user.name
        except Exception:
            # If the user is not found (e.g., left the server), use their ID
            user_display = f"Unknown User ({user_data['user_id']})"
        
        # Add the user to the leaderboard
        embed.add_field(
            #display user avatar next to their name
            name=f"{i+1}. {user_display} ",
            value=f"Level: {user_data['level']} | XP: {user_data['xp']} \n[Avatar]({user.display_avatar.url})",
            inline=False
        )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="level", description="Get a user's TACT level")
async def level(interaction: discord.Interaction, user: discord.Member = None):
    # Use the mentioned user if provided, otherwise default to the command invoker
    user = user or interaction.user
    user_id = str(user.id)
    
    # Fetch the user's data from the database
    user_data = get_user_data(user_id)
    level = user_data.get("level", 1)
    xp = user_data.get("xp", 0)

    # Build an embed with the level information
    embed = discord.Embed(
        title=f"{user.display_name}'s Level",
        description=f"**Level:** {level}\n**XP:** {xp}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    # Send the response
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="give_xp", description="Give some XPs to your friends!")
async def give_xp(interaction: discord.Interaction, member: discord.Member, xp: int):

    interaction.response.defer()
    # Validate input
    if xp <= 0:
        await interaction.response.send_message("XP must be a positive number.")
        return

    # Retrieve user data
    user_id = str(member.id)
    user_data = get_user_data(user_id)
    if not user_data:
        await interaction.response.send_message("User not found!")
        return
    
    #check if user is trying to give themselves XP
    # if interaction.user == member:
    #     embed = discord.Embed(
    #         title="❌ XP Not Awarded!!",
    #         description="You can't give yourself XP!",
    #         color=discord.Color.red()
    #     )
    #     embed.set_thumbnail(url=member.display_avatar.url)
    #     await interaction.response.send_message(embed=embed)
    #     return

    # Add XP and update user data
    user_data["xp"] = user_data.get("xp", 0) + xp
    save_user_data(user_id, user_data)

    # Create the response embed
    embed = discord.Embed(
        title="✅ XP Awarded",
        description=(
            f"{interaction.user.mention} has awarded **{xp} XP** to {member.mention}!\n"
            f"**{member.display_name}** now has **{user_data['xp']} XP**."
        ),
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    # Respond with confirmation
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="gift", description="Gift an item to another user.")
@app_commands.describe(item="The item you want to purchase")
@app_commands.autocomplete(item=item_autocomplete)
async def gift(interaction: discord.Interaction, recipient: discord.Member, *, item: str):
    giver_id = str(interaction.user.id)
    recipient_id = str(recipient.id)

    # Prevent self-gifting
    if giver_id == recipient_id:
        embed = discord.Embed(
            title=f"Gift {recipient.display_name}",
            description=f"**❌ You can't gift items to yourself.**",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=recipient.display_avatar.url)
        await interaction.response.send_message(embed=embed)
        return

    # Fetch giver and recipient data
    giver_data = get_user_data(giver_id)
    recipient_data = get_user_data(recipient_id)

    # Validate giver's inventory
    if not giver_data or "inventory" not in giver_data:
        embed = discord.Embed(
            title=f"Gift {recipient.display_name}",
            description=f"**❌ You don't have an inventory to gift from.**",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=recipient.display_avatar.url)
        await interaction.response.send_message(embed=embed)
        return

    # Ensure recipient data exists
    if not recipient_data:
        recipient_data = {"user_id": recipient_id, "balance": 0, "xp": 0, "level": 1, "inventory": []}

    giver_inventory = giver_data.get("inventory", [])

    # Check if the giver owns the item
    if item not in giver_inventory:
        embed = discord.Embed(
            title=f"Gift {recipient.display_name}",
            description=f"**❌ You don't own an item called {item}.**",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=recipient.display_avatar.url)
        await interaction.response.send_message(embed=embed)
        return

    # Update giver's inventory
    giver_inventory.remove(item)
    giver_data["inventory"] = giver_inventory

    # Update recipient's inventory
    recipient_inventory = recipient_data.get("inventory", [])
    recipient_inventory.append(item)
    recipient_data["inventory"] = recipient_inventory

    # Save data to database
    save_user_data(giver_id, giver_data)  # Update giver in the database
    save_user_data(recipient_id, recipient_data)  # Update recipient in the database

    # Confirm the gift
    embed = discord.Embed(
        title="🎁 Gift Successful!",
        description=(
            f"{interaction.user.mention} has gifted **{item}** to {recipient.mention}!\n"
            f"Check your inventory to see the updated items."
        ),
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=recipient.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@gift.error
async def gift_error(ctx, error):
    member: discord.Member
    if isinstance(error, commands.BadArgument, ):
        embed = discord.Embed(
        title=f"Gift error",
        description=f"**❌ Invalid arguments. Usage: `/gift @User item_name`**",
        color=discord.Color.gold()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
        title=f"Gift error",
        description=f"**❌ An error occurred while processing the gift.**",
        color=discord.Color.gold()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

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
        user_data = {"xp": 0}  # Default xp if user is not yet in the database
        save_user_data(user_id, user_data)  # Optionally initialize the user in the database

    # Fetch xp
    balance = user_data.get("xp", 0)

    # Create response
    embed = discord.Embed(
        title=f"{user.display_name}'s Balance",
        description=f"💰 **{balance} XPs**",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    # Send the response
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="inventory", description="Check the items in your inventory or someone else's.")
async def inventory(interaction: discord.Interaction, user: discord.Member = None):
    # Use the command invoker if no user is mentioned
    user = user or interaction.user
    
    user_id = str(user.id)  # Use the mentioned user's ID
    user_data = get_user_data(user_id)  # Fetch the correct user's data

    if not user_data or "inventory" not in user_data or not user_data["inventory"]:
        embed = discord.Embed(
            title="🎒 Inventory",
            description=(
                f"{user.mention}, their inventory is empty." if user != interaction.user else
                f"{user.mention}, your inventory is empty."
            ),
            color=discord.Color.gold()
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

    embed = discord.Embed(
        title=f"{user.display_name}'s Inventory:",
        description=f"**{formatted_inventory}**",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rob_bank", description="Attempt to rob a bank! High risk, high reward.")
async def rob_bank(interaction: discord.Interaction):
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

    # Attempt robbery
    if random.random() < success_chance:
        # Success: Add XPs
        user_data["xp"] += success_amount
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
    embed = discord.Embed(
        title="💰 Rob Bank Results",
        description=result_message,
        color=discord.Color.red() if "caught" in result_message else discord.Color.green()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

# Buy command with autocomplete
@bot.tree.command(name="buy", description="Buy items from the shop")
@app_commands.describe(item="The item you want to purchase")
@app_commands.autocomplete(item=item_autocomplete)
async def buy(interaction: discord.Interaction, item: str):
    user_id = str(interaction.user.id)
    user_data = get_user_data(user_id)

    store_items = {item_data["item_name"]: item_data["item_price"] for item_data in store_collection.find()}

    item_price = store_items.get(item)
    if item_price is None:
        embed = discord.Embed(
            title="🛒 Purchase Unsuccessful !!",
            description=f"❌ {item} is not available in the store.",
            color=discord.Color.red()
            )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)
        return

    if user_data["xp"] < int(item_price):
        embed = discord.Embed(
            title="🛒 Purchase Unsuccessful !!",
            description=f"❌ You need {item_price} XP to buy {item}.",
            color=discord.Color.red()
            )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    else:
        user_data["xp"] -= int(item_price)
        user_data["inventory"].append(item)
        embed = discord.Embed(
            title="🛒 Purchase Successful",
            description=f"✅ {interaction.user.mention} bought {item} for {item_price} XP.",
            color=discord.Color.green()
            )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    save_user_data(user_id, user_data)

def steal_function(victim_id):
    # Fetch victim data
    victim = get_user_data(victim_id)

    stolen_amount = random.randint(50, 200)  # Steal between 50 and 200 XPs
    stolen_amount = min(stolen_amount, victim["xp"])  # Can't steal more than the victim's balance

    return stolen_amount

@bot.tree.command(name="steal", description="Attempt to steal from another user.")
async def steal(interaction: discord.Interaction, target: discord.Member):
    thief_id = str(interaction.user.id) #'673eb3f1491a384eb6545a19'
    victim_id = str(target.id)

    # Ensure thief isn't targeting themselves
    if thief_id == victim_id:
        embed = discord.Embed(
        title="🔫 Steal Results",
        description="🔫 You can't steal from yourself",
        color=discord.Color.red()
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
        embed = discord.Embed(
        title="🔫 Steal Results",
        description=f"⏳ You need to wait {remaining_time // 60} minutes before stealing again!",
        color=discord.Color.red()
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
        stolen_amount = steal_function(victim_id)

        if stolen_amount == 0:
            embed = discord.Embed(
            title="🔫 Steal Results",
            description=f"❌ {target.mention} has no XPs to steal!",
            color=discord.Color.red()
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

        embed = discord.Embed(
        title="🔫 Steal Results",
        description=f"🎉 You successfully stole `{stolen_amount}` XPs from {target.mention}!",
        color=discord.Color.red()
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

@bot.tree.command(name="shoot", description="Shoot another user for a chance to win XPs!")
async def shoot(interaction: discord.Interaction, target: discord.Member):
    attacker_id = str(interaction.user.id)
    target_id = str(target.id)

    # Prevent self-targeting
    if interaction.user == target:
        embed = discord.Embed(
        title="🔫 Shoot Results",
        description="🔫 You can't shoot yourself",
        color=discord.Color.red()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Retrieve attacker and target data
    attacker_data = get_user_data(attacker_id)
    target_data = get_user_data(target_id)

    if not attacker_data or not target_data:
        embed = discord.Embed(
        title="🔫 Shoot Results",
        description="🔍 Both users must be registered to participate!",
        color=discord.Color.red()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Check cooldown
    now = datetime.utcnow()
    last_shoot = shoot_cooldowns.get(attacker_id, None)
    cooldown_time = timedelta(minutes=5)  # Cooldown duration

    if last_shoot and now - last_shoot < cooldown_time:
        remaining_time = cooldown_time - (now - last_shoot)
        embed = discord.Embed(
        title="🔫 Shoot Results",
        description=f"⏳ You need to wait {remaining_time.seconds} seconds before shooting again!",
        color=discord.Color.red()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Set success chance, rewards, and penalties
    success_chance = 0.6  # 60% chance to hit
    reward = random.randint(50, 200)  # XPs gained on success
    penalty = random.randint(30, 100)  # XPs lost on failure

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
    shoot_cooldowns[attacker_id] = now

    # Send result as an embed
    embed = discord.Embed(
        title="🔫 Shoot Results",
        description=result_message,
        color=discord.Color.green() if "successfully" in result_message else discord.Color.red()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

class StoreView(View):
    def __init__(self, items, user, per_page=10):
        super().__init__()
        self.items = items
        self.user = user
        self.per_page = per_page
        self.page = 0
        self.max_pages = ceil(len(items) / per_page)
        self.embed = None
        self.update_embed()

        # Add buttons
        self.previous_button = Button(label="Previous", style=discord.ButtonStyle.primary, disabled=True)
        self.previous_button.callback = self.previous_callback
        self.add_item(self.previous_button)

        self.next_button = Button(label="Next", style=discord.ButtonStyle.primary, disabled=(self.max_pages <= 1))
        self.next_button.callback = self.next_callback
        self.add_item(self.next_button)

    def update_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        items_on_page = self.items[start:end]

        store_list = "\n".join([f"** {item['item_name']}: {item['item_price']} XP ** \n {item['description']}" for item in items_on_page])

        self.embed = discord.Embed(
            title=f"**Welcome to the 🛒 Store! (Page {self.page + 1}/{self.max_pages})**",
            description=store_list,
            color=discord.Color.blue()
        )
        self.embed.set_thumbnail(url=self.user.display_avatar.url)

    async def update_message(self, interaction):
        self.update_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def previous_callback(self, interaction: discord.Interaction):
        self.page -= 1
        self.previous_button.disabled = (self.page == 0)
        self.next_button.disabled = False
        await self.update_message(interaction)

    async def next_callback(self, interaction: discord.Interaction):
        self.page += 1
        self.next_button.disabled = (self.page == self.max_pages - 1)
        self.previous_button.disabled = False
        await self.update_message(interaction)

@bot.tree.command(name="store", description="Checkout the store")
async def store(interaction: discord.Interaction):
    interaction.response.defer()
    items = list(store_collection.find())
    if not items:
        await interaction.response.send_message("The store is currently empty!")
        return

    view = StoreView(items=items, user=interaction.user)
    await interaction.response.send_message(embed=view.embed, view=view)

@bot.tree.command(name="help", description="Get help with the commands")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 TACT Bot Help",
        description=(
            "Welcome to the TACT Bot! Here are some of the available commands:\n"
            "**/balance**: Check your balance\n"
            "**/leaderboard**: View the top users\n"
            "**/level**: Check your level\n"
            "**/steal**: Attempt to steal from another user\n"
            "**/shoot**: Shoot another user for a chance to win XPs\n"
            "**/rob_bank**: Attempt to rob a bank\n"
            "**/store**: View items available for purchase\n"
            "**/buy**: Buy items from the store\n"
            "**/gift**: Gift an item to another user\n"
            "**/inventory**: Check your inventory\n"
            "**/give_xp**: Give XP to another user\n"
            "**/heist**: Team up to pull off an epic heist\n"
            "**/join_heist**: Join the heist\n"
            "**/open_box**: Open a mystery box for surprises\n"
            "**/claim_daily**: Claim your daily reward\n"
            "**/claim_hourly**: Claim your hourly reward\n"
            "**/help**: Get help with the commands"
            "\n\nUse these commands to explore the TACT Bot features!"

        ),
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="heist", description="Team up to pull off an epic heist!")
async def heist(interaction: discord.Interaction):

    #get all users in the database
    # all_user_ids = list(user_collection.find({}, {"user_id": 1}))
    # print("All users: ", all_user_ids)

    heist_planner = interaction.user
    heist_participants = [heist_planner.id]

    embed = discord.Embed(
        title="Epic heist!",
        description=f"💰 A heist is being planned by {interaction.user} ! Type `/join_heist` to participate!",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="join_heist", description="Join the heist!")
async def join_heist(interaction: discord.Interaction):
    if interaction.user.id not in heist_participants:
        heist_participants.append(interaction.user.id)

        embed = discord.Embed(
            title="🎭 Heist Participation",
            description=f"{interaction.user.mention} has joined the heist!",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="🎭 Heist Participation",
            description=f"You're already in the heist!",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# To resolve the heist
async def resolve_heist(interaction):
    if len(heist_participants) < 1:
        await interaction.channel.send("Not enough participants for the heist. Mission failed! 😔")
        return

    success = random.choice([True, False])
    if success:
        rewards = random.randint(100, 500)
        for user_id in heist_participants:
            user_data = get_user_data(str(user_id))
            user_data["xp"] += rewards
            save_user_data(str(user_id), user_data)
        await interaction.channel.send(f"🎉 The heist was successful! Participants earned {rewards} XP each!")
    else:
        await interaction.channel.send("🚨 The heist failed! Better luck next time!")
    heist_participants.clear()

@bot.tree.command(name="open_box", description="Open a mystery box for surprises!")
async def open_box(interaction: discord.Interaction):
    rewards = ["250 XP", "Special Badge", "Exclusive Role"]
    reward = random.choice(rewards)
    user_data = get_user_data(str(interaction.user.id))

    if reward.endswith("XP"):
        user_data["xp"] += int(reward.split(" ")[0])
    else:
        user_data["inventory"].append(reward)

    save_user_data(str(interaction.user.id), user_data)
    await interaction.response.send_message(f"🎁 You opened a mystery box and received: {reward}!")

@bot.tree.command(name="claim_daily", description="Claim your daily reward!")
async def claim_daily(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    now = datetime.utcnow()
    reward_xp = 500  # Amount of XP given as a daily reward

    # Check if the user has already claimed the reward today
    if user_id in last_daily_claim:
        last_claim_time = last_daily_claim[user_id]
        if now - last_claim_time < timedelta(days=1):
            next_claim_time = last_claim_time + timedelta(days=1)
            remaining_time = next_claim_time - now

            embed = discord.Embed(
                title="⏳ Claim your daily reward!",
                description=f"⏳ You have already claimed your daily reward. Come back in {remaining_time.seconds // 3600} hours and {(remaining_time.seconds // 60) % 60} minutes.",
            color=discord.Color.gold()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

    # Update last claim time and give reward
    last_daily_claim[user_id] = now
    user_data = get_user_data(user_id)
    user_data["xp"] += reward_xp
    save_user_data(user_id, user_data)

    embed = discord.Embed(
        title="⏳ Claim your daily reward!",
        description=f"🎉 {interaction.user.mention}, you have claimed your **{reward_xp} XP** daily reward!",
        color=discord.Color.gold()
        )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="claim_hourly", description="Claim your hourly reward!")
async def claim_hourly(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    now = datetime.utcnow()
    reward_xp = 400  # Amount of XP given as an hourly reward

    # Check if the user has already claimed the reward this hour
    if user_id in last_hourly_claim:
        last_claim_time = last_hourly_claim[user_id]
        if now - last_claim_time < timedelta(hours=1):
            next_claim_time = last_claim_time + timedelta(hours=1)
            remaining_time = next_claim_time - now

            embed = discord.Embed(
                title="⏳ Claim your hourly reward!",
                description=f"⏳ You have already claimed your hourly reward. Come back in {remaining_time.seconds // 60} minutes.",
                color=discord.Color.gold()
                )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

            await interaction.response.send_message(embed=embed)
            return

    # Update last claim time and give reward
    last_hourly_claim[user_id] = now
    user_data = get_user_data(user_id)
    user_data["xp"] += reward_xp
    save_user_data(user_id, user_data)

    embed = discord.Embed(
        title="⏳ Claim your hourly reward!",
        description=f"🕒 {interaction.user.mention}, you have claimed your **{reward_xp} XP** hourly reward!",
        color=discord.Color.gold()
        )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

#command to reset user level
@bot.tree.command(name="reset_level", description="Reset the level of a user.")
async def reset_level(interaction: discord.Interaction, member: discord.Member):
    user_id = str(interaction.user.id)
    user_data = get_user_data(user_id)

    user_data["level"] = 0
    save_user_data(user_id, user_data)  # Save the data
    await interaction.response.send_message(f"✅ {member.mention}'s XP has been reset.")
    # else:
    #     await interaction.response.send_message(f"{member.mention} has no XP data to reset.")


bot.run(os.getenv('DISCORD_TOKEN'))