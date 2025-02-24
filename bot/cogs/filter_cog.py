import logging
import pathlib
from collections import defaultdict
from datetime import datetime, timedelta

import discord
from discord import Color, Embed, Member, Message
from discord.ext.commands import Bot, Cog
from profanity_check import predict

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor
from utils.log import logger

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * Filter Cog
# ----------------------------------------------------------------------------------------------------
class Filter(Cog, description="Filters blacklisted message content."):
    MAX_OFFENSES = 5
    GOLD_PENALTY = 500

    def __init__(self, bot: ActBot):
        self.bot = bot
        self.offenses = defaultdict(int)  # { user_id : offense_count }

    @Cog.listener()
    async def on_message(self, message: Message):
        # Ignore DM & bot messages
        member = message.author
        if not isinstance(member, Member) or member.bot:
            return

        # Identify profane words
        profane_words = self.get_profane_words(message.content.split())
        if not profane_words:
            return

        # Censor message content
        censored_content = message.content
        for word in profane_words:
            censored_content = censored_content.replace(word, f"||{word}||")

        # Delete & replace message
        await message.delete()
        embed = Embed(
            title="",
            description=censored_content,
            color=Color.red(),
        )
        embed.add_field(name="", value="")
        embed.set_author(name=member.display_name, icon_url=member.avatar)
        embed.set_footer(text="🚫 Censored Message")
        censored_message = await message.channel.send(embed=embed)

        # Accumulate offenses to detect abuse
        if member.guild_permissions.administrator:
            return
        self.offenses[member.id] += 1
        if self.offenses[member.id] < Filter.MAX_OFFENSES:
            return

        # Penalize by gold
        db = self.bot.get_db(message.guild)
        if not db:
            return
        actor = db.find_one(Actor, Actor.id == member.id)
        if not actor:
            actor = self.bot.create_actor(member)
        debt_gold = 0
        if actor.gold >= self.GOLD_PENALTY:
            actor.gold -= self.GOLD_PENALTY
        else:
            debt_gold = self.GOLD_PENALTY - actor.gold
            actor.gold = 0
        db.save(actor)
        self.offenses[member.id] = 0

        # Penalize by timeout (if insufficient gold)
        if debt_gold:
            time = timedelta(seconds=int(0.5 * debt_gold))  # 0.5 seconds per gold
            await member.timeout(time, reason="Filter")

        # Notice
        embed = Embed(
            title=f"🚨 Penalty",
            description=f"{member.display_name} ({member.mention}) has been penalized for repeated use of offensive language.",
            color=Color.red(),
        )
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="Gold 🔻", value=f"💰 **-{self.GOLD_PENALTY}**")
        if debt_gold:
            embed.add_field(
                name=f"Timeout Activated ❗",
                value=f"⏳ **{time}**\n💰 **{debt_gold}** _Debt Converted_",
            )
        embed.set_thumbnail(url=member.display_avatar.url)
        await censored_message.reply(embed=embed)

    @staticmethod
    def get_profane_words(words: list[str]) -> list[str]:
        """Get list of profane words from given list. If non found, get empty list."""
        predictions = predict(words)
        profane_words = []
        for i, word in enumerate(words):
            if predictions[i] == 1:  # 1 means profane, 0 means clean
                profane_words.append(word)
        return profane_words
