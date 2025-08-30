import re
from asyncio import sleep
from random import randint

import humanize
from discord import (
    Attachment,
    AuditLogAction,
    Embed,
    Guild,
    HTTPException,
    Interaction,
    Member,
    Message,
    Role,
    StickerItem,
    TextChannel,
    User,
    VoiceChannel,
    app_commands,
    utils,
)
from discord.ext.commands import Cog

from bot.main import ActBot
from bot.ui.embed import EmbedX
from db.actor import Actor
from db.room import Room
from utils.xp import Experience


# ----------------------------------------------------------------------------------------------------
# * Farm Cog
# ----------------------------------------------------------------------------------------------------
class FarmCog(Cog, description="Allow players to gain stats and roles"):
    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------
    # * Set Farm Log
    # ----------------------------------------------------------------------------------------------------
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.command(
        description="Set or get farm log channel", extras={"category": "Farm"}
    )
    async def set_farm_log(
        self,
        interaction: Interaction,
        channel: TextChannel | None = None,
        unset: bool = False,
    ):
        if not interaction.guild:
            return await interaction.response.send_message(
                embed=EmbedX.error(
                    title="Guild Only",
                    description="This command can only be used in a server.",
                ),
                ephemeral=True,
            )

        if unset:
            self.delete_room(id=FarmCog.__name__, guild=interaction.guild)
            return await interaction.response.send_message(
                embed=EmbedX.success(
                    title="Farm Log Channel Unset",
                    description="Farm log channel has been unset.",
                ),
                ephemeral=True,
            )

        if not channel:
            log_room = self.load_room(id=FarmCog.__name__, guild=interaction.guild)
            log_channel = (
                interaction.guild.get_channel(log_room.channel_id) if log_room else None
            )
            return await interaction.response.send_message(
                embed=EmbedX.info(
                    title="Farm Log Channel",
                    description=(
                        f"Current farm log channel is {log_channel.mention}"
                        if log_channel
                        else "No farm log channel set."
                    ),
                ),
                ephemeral=True,
            )

        self.save_room(id=FarmCog.__name__, channel=channel)
        await interaction.response.send_message(
            embed=EmbedX.success(
                title="Farm Log Channel Set",
                description=f"Farm log channel has been set to {channel.mention}.",
            ),
            ephemeral=True,
        )

    # ----------------------------------------------------------------------------------------------------
    # * On Member Join
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_member_join(self, member: Member):
        log_room = self.load_room(id=FarmCog.__name__, guild=member.guild)
        log_channel = (
            member.guild.get_channel(log_room.channel_id) if log_room else None
        )
        if log_channel and isinstance(log_channel, TextChannel):
            await log_channel.send(f"🟢 {member.mention} joined.")

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
        log_room = self.load_room(id=FarmCog.__name__, guild=member.guild)
        log_channel = (
            member.guild.get_channel(log_room.channel_id) if log_room else None
        )
        if log_channel and isinstance(log_channel, TextChannel):
            await sleep(1)  # Wait for audit log to update
            action_taken = False
            # Check for kick
            async for entry in member.guild.audit_logs(
                limit=5, action=AuditLogAction.kick
            ):
                if entry.target and entry.target.id == member.id:
                    await log_channel.send(
                        f"👢 {member.name} was kicked by {entry.user.mention} for reason: {entry.reason or '_No reason provided_'}"
                    )
                    action_taken = True
                    break
            # Check for ban if not kicked
            if not action_taken:
                async for entry in member.guild.audit_logs(
                    limit=5, action=AuditLogAction.ban
                ):
                    if entry.target and entry.target.id == member.id:
                        await log_channel.send(
                            f"🔨 {member.name} was banned by {entry.user.mention} for reason: {entry.reason or '_No reason provided_'}"
                        )
                        action_taken = True
                        break
            if not action_taken:
                await log_channel.send(f"🔴 {member.mention} left.")

        db = self.bot.get_db(member.guild)
        actor = db.find_one(Actor, Actor.id == member.id)
        if not actor:
            return
        actor.is_member = False
        db.save(actor)

    # ----------------------------------------------------------------------------------------------------
    # * On Member Update
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        log_room = self.load_room(id=FarmCog.__name__, guild=after.guild)
        if not log_room:
            return

        log_channel = after.guild.get_channel(log_room.channel_id)
        if not (log_channel and isinstance(log_channel, TextChannel)):
            return

        # Check for timeout added
        if not before.is_timed_out() and after.is_timed_out() and after.timed_out_until:
            entry = None
            await sleep(1)  # Wait for audit log to update
            async for e in after.guild.audit_logs(
                limit=5, action=AuditLogAction.member_update
            ):
                if (
                    e.target
                    and e.target.id == after.id
                    and e.changes.after.timed_out_until is not None
                ):
                    entry = e
                    break

            moderator = entry.user.mention if entry and entry.user else "Unknown"
            reason = (
                entry.reason or "_No reason provided_"
                if entry
                else "_No reason provided_"
            )

            time_left = humanize.naturaldelta(after.timed_out_until - utils.utcnow())
            await log_channel.send(
                f"🔇 {after.mention} timed out by {moderator} for **{time_left}** for reason: {reason}"
            )

        # Check for timeout removed
        elif before.is_timed_out() and not after.is_timed_out():
            await log_channel.send(f"🔊 {after.mention}'s timeout removed.")

    # ----------------------------------------------------------------------------------------------------
    # * On Message
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_message(self, message: Message):
        # Ignore DM
        member = message.author
        if not message.guild or not isinstance(member, Member):
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
        log_room = self.load_room(id=FarmCog.__name__, guild=message.guild)
        log_channel = (
            message.guild.get_channel(log_room.channel_id) if log_room else None
        )
        if not member.bot and log_channel and isinstance(log_channel, TextChannel):
            # embed = EmbedX.info(
            #     emoji="",
            #     title="",
            #     description=f"⏫ {member.mention} earned experience.",
            # )
            # embed.add_field(name="Experience 🔼", value=f"**⏫ +{xp_reward} **")
            # embed.set_author(
            #     name=member.display_name, icon_url=member.display_avatar.url
            # )
            # embed = EmbedX.info(
            #     emoji="",
            #     title="",
            #     description=f"**⏫ +{xp_reward}** XP for {member.mention}.",
            # )
            # await log_channel.send(embed=embed)
            await log_channel.send(f"{member.display_name} earned **{xp_reward}** xp.")

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

    def save_room(self, id: str, channel: TextChannel | VoiceChannel):
        db = self.bot.get_db(channel.guild)
        room = db.find_one(Room, Room.id == id) or self.bot.create_room(id, channel)
        room.channel_id = channel.id
        room.channel_name = channel.name
        room.channel_is_voice = isinstance(channel, VoiceChannel)
        db.save(room)

    def delete_room(self, id: str, guild: Guild):
        db = self.bot.get_db(guild)
        room = db.find_one(Room, Room.id == id)
        if room:
            db.delete(room)

    def load_room(self, id: str, guild: Guild) -> Room | None:
        return self.bot.get_db(guild).find_one(Room, Room.id == id)

    # @staticmethod
    # async def try_award_role(member: Member, role_name: str) -> Role | None:
    #     role = utils.get(member.guild.roles, name=role_name)
    #     if role in member.roles:
    #         return None
    #     elif not role:
    #         role = await member.guild.create_role(name=role_name)
    #     await member.add_roles(role)
    #     return role
