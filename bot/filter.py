import logging
from collections import defaultdict

from discord import Color, Embed, Message
from discord.ext.commands import Bot, Cog

from utils.log import logger

# from core.user import DbUser

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * Filter Cog
# ----------------------------------------------------------------------------------------------------
# 💡 TODO: Try profanity-filter package: https://pypi.org/project/profanity-filter
class Filter(Cog, description="Filters blacklisted message content."):
    BLACKLIST_PATH = "./bot/filter.txt"
    MAX_OFFENSES = 5
    GOLD_PENALTY = 500

    def __init__(self, bot: Bot):
        self.bot = bot
        self.offenses = defaultdict(int)  # { "user_id": offense_count }
        with open(Filter.BLACKLIST_PATH, "r") as file:
            self.blacklist_words = file.read().split("\n")
            log.info(
                f"{self.__cog_name__} cog: {len(self.blacklist_words)} blacklisted words."
            )

    @Cog.listener()
    async def on_message(self, message: Message):
        user = message.author
        if user.bot:
            return
        content = message.content

        for bl_word in self.blacklist_words:
            if bl_word not in content:
                continue

            # censor message
            await message.delete()
            embed = Embed(
                title="",
                description=content.replace(bl_word, f"||{bl_word}||"),
                color=Color.red(),
            )
            embed.add_field(name="", value="")
            embed.set_author(name=user.display_name, icon_url=user.avatar)
            embed.set_footer(text="🚫 Censored Message")
            await message.channel.send(embed=embed)

            # mark offense & penalize abuse
            self.offenses[user.id] += 1
            if self.offenses[user.id] < Filter.MAX_OFFENSES:
                continue
            # db_user = DbUser.load(user.id)
            # if db_user:
            #     db_user.gold = max(0, db_user.gold - Filter.GOLD_PENALTY)
            #     db_user.save()
            #     self.offenses[user.id] = 0
            #     await message.channel.send(
            #         f"🚨 Attention, {user.mention}! You have been penalized **💰{ Filter.GOLD_PENALTY} Gold** for repeatedly using offensive language."
            #     )
