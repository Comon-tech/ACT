import discord  # type: ignore
from discord import app_commands  # type: ignore
from discord.ext import commands  # type: ignore
from discord.ui import View, Button
from services.bad_words import check_for_bad_words, split_msg_into_array, offensive_words
from services.db import user_collection, store_collection, chat_collection
import asyncio

import inspect

import dotenv  # type: ignore
import os  # type: ignore
import importlib
from pathlib import Path

import re
import time
import random
from datetime import datetime, timedelta
from math import ceil
from collections import Counter, defaultdict

dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Cooldown tracker
rob_cooldowns = {}

def remove_links(message):
    """
    Remove URLs (e.g., GIF links) from a message.
    """
    # Regex to match URLs
    url_pattern = r"(https?://\S+)"
    return re.sub(url_pattern, "", message).strip()

# ------------------------------------------------

if __name__ == "__main__":
    # clear screen (works on windows only)
    os.system('cls')
    
    async def load_cogs():
        base_path = os.path.join(os.path.dirname(__file__), "commands")
        events_path = os.path.join(os.path.dirname(__file__), "events")
        for path in [base_path, events_path]:
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        relative_path = os.path.relpath(os.path.join(root, file), os.path.dirname(__file__))
                        module_path = relative_path.replace(os.sep, ".")[:-3]
                        try:
                            module = importlib.import_module(module_path)
                            for name, obj in inspect.getmembers(module, inspect.isclass):
                                if issubclass(obj, commands.Cog) and obj.__module__ == module.__name__:
                                    await bot.add_cog(obj(bot))
                                    print(f"✅ Loaded {name} cog from {module_path}")
                                    break
                        except Exception as e:
                            print(f"⛔ Failed to load cog {module_path}: {e}\n")
    
    asyncio.run(load_cogs())

    # run bot
    bot.run(os.getenv('DISCORD_TOKEN'))
    
