import discord # type: ignore
from discord.ext import commands # type: ignore
import random
import json

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

@bot.event
async def on_ready():
    load_data()
    print(f"Rewards Bot is ready! Logged in as {bot.user}")

bot.run("YOUR_BOT_TOKEN")
