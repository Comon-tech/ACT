from typing import Any

from discord import Color, Embed, Guild, Interaction, Member, User, app_commands
from discord.ext.commands import GroupCog
from humanize import intcomma, naturalsize, naturaltime
from odmantic import query

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Leaderboard Cog
# ----------------------------------------------------------------------------------------------------
class LeaderboardCog(
    GroupCog, group_name="leaderboard", description="Allows players to view their data"
):
    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------

    @app_commands.guild_only()
    @app_commands.command(description="View top members sorted by level")
    async def level(self, interaction: Interaction):
        embed = EmbedX.info(emoji="🏅", title="Level Leaderboard")
        await self.show_leaderboard(
            interaction=interaction,
            embed=embed,
            sort=(
                query.desc(Actor.level),
                query.desc(Actor.xp),
                query.desc(Actor.gold),
            ),
        )

    @app_commands.guild_only()
    @app_commands.command(description="View top members sorted by rank")
    async def rank(self, interaction: Interaction):
        embed = EmbedX.info(emoji="🏆", title="Rank Leaderboard")
        await self.show_leaderboard(
            interaction=interaction,
            embed=embed,
            sort=(
                query.desc(Actor.elo),
                query.desc(Actor.gold),
            ),
        )

    # ----------------------------------------------------------------------------------------------------

    async def show_leaderboard(
        self,
        interaction: Interaction,
        embed: Embed,
        sort: Any,
    ):
        # Check guild
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Get top actors
        await interaction.response.defer()
        actors_members = await self.bot.get_actors_members(guild=guild, sort=sort)
        if not actors_members:
            await interaction.followup.send(
                embed=EmbedX.warning(description="No actors found.")
            )
            return

        # Create board table
        # top_actor: Actor
        names_column_text = ""
        stats_column_text = ""
        for i, (actor, member) in enumerate(actors_members):
            if i == 0:
                top_actor = actor
            name = member.mention
            rank = actor.rank.name if actor.rank else "?"
            level = str(actor.level)
            xp = naturalsize(actor.xp, binary=False, gnu=True).replace("B", "")
            gold = naturalsize(actor.gold, binary=False, gnu=True).replace("B", "")
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else ""
            skull = "`💀`" if actor.health <= 0 else ""
            names_column_text += f"**# {(i+1)}** ― {medal} {name} {skull}\n**`🏆{rank} 🏅{level} ⏫{xp} 💰{gold}`**\n\n"
            # stats_column_text += f"**`🏆{rank} 🏅{level} ⏫{xp} 💰{gold}`**\n"

        # Send embed
        # try:
        #     top_member = guild.get_member(top_actor.id) or await guild.fetch_member(
        #         top_actor.id
        #     )
        #     if top_member:
        #         embed.set_thumbnail(url=top_member.display_avatar)
        # except:
        #     pass
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="", value=names_column_text)
        embed.add_field(name="", value=stats_column_text)
        await interaction.followup.send(embed=embed)
