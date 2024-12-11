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