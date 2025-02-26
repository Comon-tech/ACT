import asyncio

from discord import Color, Embed, Interaction, Member, User, app_commands
from discord.ext.commands import Cog
from humanize import intcomma, naturaltime
from odmantic import query

from bot.main import ActBot
from db.actor import Actor
from humanize import intword, metric, ordinal


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
        embed = Embed(
            title=f"👤 {member.display_name}",
            color=Color.blue(),
        )
        if isinstance(member, Member):
            embed.description = " ".join(
                [
                    f"`{role.name}`"
                    for role in member.roles
                    if role != member.guild.default_role
                ]
            )
        db = self.bot.get_db(interaction.guild)
        actor = db.find_one(Actor, Actor.id == member.id) if db else None
        if not actor:
            actor = self.bot.create_actor(member)
        embed.add_field(name="", value="", inline=False)
        embed.add_field(
            name="Rank", value=f"🏆 **{actor.rank_name}**\n{actor.rank_bar}"
        )
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
        if isinstance(member, Member):
            embed.add_field(
                name="Joined",
                value=f"⌚ {member.guild.name} **{naturaltime(member.joined_at or 0)}**\n-# ⌚ Discord **{naturaltime(member.created_at)}**",
            )
        embed.add_field(name="", value="", inline=False)
        embed.set_footer(text=f"#️⃣{member.name} \n🆔{member.id}")
        embed.set_thumbnail(url=member.display_avatar.url)
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
                    query.desc(Actor.rank),
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

        # Create board table
        top_actor: Actor
        leaderboard_text = "```"
        for i, actor in enumerate(actors):
            if i == 0:
                top_actor = actor
            name = f"{actor.display_name} ({actor.name})"
            rank = actor.rank_name
            level = str(actor.level)
            xp = intcomma(actor.xp)
            gold = intcomma(actor.gold)
            leaderboard_text += (
                f"# {(i+1):<2} {name}\n\t 🏆{rank:<2}  🏅{level}  ⏫{xp}  💰{gold}\n\n"
            )
        leaderboard_text += "```"

        # Create embed
        embed = Embed(title="🏆 Leaderboard", color=Color.blue())
        top_member = guild.get_member(top_actor.id) or await guild.fetch_member(
            top_actor.id
        )
        if top_member:
            embed.set_thumbnail(url=top_member.display_avatar)
        embed.add_field(name="", value=leaderboard_text, inline=False)
        await interaction.followup.send(embed=embed)
