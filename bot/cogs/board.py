import asyncio

from discord import Color, Embed, Interaction, Member, User, app_commands
from discord.ext.commands import Cog
from humanize import naturaltime
from odmantic import query

from bot.main import ActBot
from db.actor import Actor


class Board(Cog, description="Allows players to view their data."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @app_commands.guild_only()
    @app_commands.command(
        description="View your or another member's profile information"
    )
    async def profile(
        self, interaction: Interaction, member: Member | User | None = None
    ):
        await interaction.response.defer()
        member = member or interaction.user
        embed = Embed(title=f"👤 {member.display_name}", color=Color.blue())
        if isinstance(member, Member):
            embed.description = " ".join(
                [
                    f"`{role.name}`"
                    for role in member.roles
                    if role != member.guild.default_role
                ]
            )
        embed.set_thumbnail(url=member.display_avatar.url)
        db = self.bot.get_db(interaction.guild)
        actor = db.find_one(Actor, Actor.id == member.id) if db else None
        if actor:
            embed.add_field(name="", value="", inline=False)
            embed.add_field(
                name="Level",
                value=f"🏅 **{actor.level}**\n{actor.level_bar}",
            )
            embed.add_field(
                name="Experience",
                value=f"⏫ **{actor.xp}** / {actor.next_level_xp}\n{actor.xp_bar}",
            )
            embed.add_field(name="", value="", inline=False)
            embed.add_field(name="Gold", value=f"💰 **{actor.gold}**")
            embed.add_field(name="Items", value=f"🎒 **{len(actor.items)}**")
            embed.add_field(name="", value="", inline=False)

        if isinstance(member, Member):
            embed.add_field(
                name="Joined",
                value=f"⌚ {member.guild.name} **{naturaltime(member.joined_at or 0)}**\n-# ⌚ Discord **{naturaltime(member.created_at)}**",
            )
        await interaction.followup.send(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(description="View top members")
    async def leaderboard(self, interaction: Interaction):
        # Check guild (not needed but just for type-checking)
        guild = interaction.guild
        if not guild:
            return

        # Get top actors
        await interaction.response.defer()
        db = self.bot.get_db(interaction.guild)
        actors = (
            db.find(
                Actor,
                sort=(
                    query.desc(Actor.level),
                    query.desc(Actor.xp),
                    query.desc(Actor.gold),
                ),
                limit=10,
            )
            if db
            else None
        )
        if not actors:
            await interaction.followup.send(
                embed=Embed(
                    title="❔",
                    description="No members found.",
                    color=Color.yellow(),
                )
            )
            return

        # Create embed while fetching memebrs associated with actors
        embed = Embed(title="🏆 Leaderboard", color=Color.blue())
        for i, actor in enumerate(actors):
            separator = 10 * "‎ "
            embed.add_field(name="", value="", inline=False)
            embed.add_field(
                name=f"# **{i + 1}** {separator} {actor.display_name}",
                value=f"",
            )
            embed.add_field(name="", value="")
            embed.add_field(
                name=f"",
                value=f"-# 🏅 {actor.level} {separator} ⏫ {actor.xp} {separator} 💰 {actor.gold}",
            )
        await interaction.followup.send(embed=embed)
