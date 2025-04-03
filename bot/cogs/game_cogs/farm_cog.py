import re
from random import randint

from discord import Member, Message, Role, utils
from discord.ext.commands import Cog

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor
from utils.xp import Experience


# ----------------------------------------------------------------------------------------------------
# * Farm Cog
# ----------------------------------------------------------------------------------------------------
class FarmCog(Cog, description="Allow players to gain stats and roles"):
    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------
    # * On Member Join
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_member_join(self, member: Member):
        db = self.bot.get_db(member.guild)
        actor = db.find_one(Actor, Actor.id == member.id)
        if not actor:
            actor = self.bot.create_actor(member)
        actor.is_member = True
        db.save(actor)

    # ----------------------------------------------------------------------------------------------------
    # * On Member Remove
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_member_remove(self, member: Member):
        db = self.bot.get_db(member.guild)
        actor = db.find_one(Actor, Actor.id == member.id)
        if not actor:
            return
        actor.is_member = False
        db.save(actor)

    # ----------------------------------------------------------------------------------------------------
    # * On Message
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_message(self, message: Message):
        # Ignore DM & bot messages
        member = message.author
        if not message.guild or not isinstance(member, Member) or member.bot:
            return

        # Get or create actor
        db = self.bot.get_db(message.guild)
        actor = db.find_one(Actor, Actor.id == member.id) or self.bot.create_actor(
            member
        )

        # Gain xp per message sent
        xp_reward = Experience.calculate_reward(
            content=message.content,
            attachment_count=len(message.attachments),
            embed_count=len(message.embeds),
            sticker_count=len(message.stickers),
        )

        actor.xp += xp_reward
        print(f"👤 @{member.name} earned {xp_reward} xp.")

        # Log xp gain to a "log" named channel
        # TODO: This works better with a feature allowing to set log channel per server (maybe a command)
        log_channel = utils.find(
            lambda c: "📜・log" in c.name.lower(), message.guild.text_channels
        )
        if log_channel:
            embed = EmbedX.info(
                emoji="", title="", description=f"{member.mention} earned experience."
            )
            embed.add_field(name="Experience 🔼", value=f"**⏫ +{xp_reward} **")
            embed.set_author(
                name=member.display_name, icon_url=member.display_avatar.url
            )
            await log_channel.send(embed=embed)

        # Try level-up
        if actor.try_level_up():
            gold_reward = actor.current_level_gold
            actor.gold += gold_reward
            embed = EmbedX.success(
                emoji="🏅",
                title="Level Up",
                description=f"{member.mention} has reached a new level and has been rewarded.",
            )
            embed.add_field(name="", value="", inline=False)
            embed.add_field(name="Level ✨", value=f"🏅 **{actor.level}**")
            embed.add_field(name="Gold 🔼", value=f"💰 **+{gold_reward}**")
            embed.set_thumbnail(url=member.display_avatar.url)
            await message.channel.send(
                content=f"Congratulations, {member.mention}! 🎉", embed=embed
            )

        # Try role-up
        # if actor.try_rank_up():
        #     # awarded_role = await self.award_role(member, actor.rank_name)
        #     # if awarded_role:
        #     gold_reward = randint(1, 1000) * actor.level
        #     actor.gold += gold_reward
        #     embed = EmbedX.success(
        #         emoji="🏆",
        #         title="Rank Up",
        #         description=f"{member.mention} has reached a new rank and has been rewarded.",
        #     )
        #     embed.add_field(name="", value="", inline=False)
        #     embed.add_field(name="Rank ✨", value=f"🏆 **{actor.rank}**")
        #     embed.add_field(name="Gold 🔼", value=f"💰 **+{gold_reward}**")
        #     embed.set_thumbnail(url=member.display_avatar.url)
        #     await message.channel.send(
        #         content=f"Congratulations, {member.mention}! 🎉", embed=embed
        #     )

        # Save changes
        db.save(actor)

    # ----------------------------------------------------------------------------------------------------

    # @staticmethod
    # async def try_award_role(member: Member, role_name: str) -> Role | None:
    #     role = utils.get(member.guild.roles, name=role_name)
    #     if role in member.roles:
    #         return None
    #     elif not role:
    #         role = await member.guild.create_role(name=role_name)
    #     await member.add_roles(role)
    #     return role
