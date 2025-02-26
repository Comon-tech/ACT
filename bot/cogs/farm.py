import asyncio
import random
import re

from discord import (
    Color,
    Embed,
    Member,
    Message,
    Permissions,
    Role,
    TextChannel,
    User,
    utils,
)
from discord.ext.commands import Bot, Cog

from bot.main import ActBot
from db.actor import Actor


class Farm(Cog, description="Allows players to gain stats and roles."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: Message):
        # Ignore DM & bot messages
        member = message.author
        if not message.guild or not isinstance(member, Member) or member.bot:
            return

        # Get or create actor
        db = self.bot.get_db(message.guild)
        if not db:
            return
        actor = db.find_one(Actor, Actor.id == member.id)
        if not actor:
            actor = self.bot.create_actor(member)

        # Gain xp per message sent
        xp_reward = self.calculate_xp_reward(message)
        actor.xp += xp_reward
        print(f"👤 @{member.name} earned {xp_reward} xp.")

        # Log xp gain to a "log" named channel
        # TODO: This works better with a feature allowing to set log channel per server (maybe a command)
        # log_channel = utils.find(
        #     lambda c: "log" in c.name.lower(), message.guild.text_channels
        # )
        # if log_channel:
        #     await log_channel.send(
        #         f"👤 {member.display_name} earned **⏫ {xp_reward} Experience**."
        #     )

        # Try level-up
        if actor.try_level_up():
            gold_reward = random.randint(1, 500) * actor.level
            actor.gold += gold_reward
            embed = Embed(
                title=f"🏅 Level Up",
                description=f"{member.display_name} {member.mention} has reached a new level and has been rewarded.",
                color=Color.green(),
            )
            embed.add_field(name="", value="", inline=False)
            embed.add_field(name="Level ✨", value=f"🏅 **{actor.level}**")
            embed.add_field(name="Gold 🔼", value=f"💰 **+{gold_reward}**")
            embed.set_thumbnail(url=member.display_avatar.url)
            await message.channel.send(embed=embed)

        # Try role-up
        if actor.try_rank_up():
            # awarded_role = await self.award_role(member, actor.rank_name)
            # if awarded_role:
            gold_reward = random.randint(1, 1000) * actor.level
            actor.gold += gold_reward
            embed = Embed(
                title=f"🏆 Rank Up",
                description=f"{member.display_name} {member.mention} has reached a new rank and has been rewarded.",
                color=Color.green(),
            )
            embed.add_field(name="", value="", inline=False)
            embed.add_field(name="Rank ✨", value=f"🏆 **{actor.rank_name}**")
            embed.add_field(name="Gold 🔼", value=f"💰 **+{gold_reward}**")
            embed.set_thumbnail(url=member.display_avatar.url)
            await message.channel.send(embed=embed)

        # Save changes
        db.save(actor)

    # ----------------------------------------------------------------------------------------------------

    @staticmethod
    def calculate_xp_reward(message: Message):
        word_count = 0
        message_content = message.content

        # Exclude URLs
        message_content = re.sub(r"https?://\S+", "", message_content)  # Remove URLs
        word_count += len(message_content.split())

        # Handle embeds
        if message.embeds:
            word_count += len(message.embeds)  # Each embed counts as 1 word

        # Handle attachments (including GIFs, images, files)
        if message.attachments:
            word_count += len(message.attachments)  # Each attachment counts as 1 word

        # Minimum word count (to avoid 0 XP rewards)
        word_count = max(1, word_count)  # Ensure at least 1 word is counted

        return random.randint(1, word_count)

    @staticmethod
    async def try_award_role(member: Member, role_name: str) -> Role | None:
        role = utils.get(member.guild.roles, name=role_name)
        if role in member.roles:
            return None
        elif not role:
            role = await member.guild.create_role(name=role_name)
        await member.add_roles(role)
        return role
