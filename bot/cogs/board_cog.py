from discord import Color, Embed, Guild, Interaction, Member, User, app_commands
from discord.ext.commands import Cog
from humanize import intcomma, naturalsize, naturaltime
from odmantic import query

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Board Cog
# ----------------------------------------------------------------------------------------------------
class BoardCog(Cog, description="Allows players to view their data."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------
    # * Profile
    # ----------------------------------------------------------------------------------------------------
    @app_commands.guild_only()
    @app_commands.command(
        description="View your or another member's profile information"
    )
    async def profile(
        self, interaction: Interaction, member: Member | User | None = None
    ):
        await interaction.response.defer()
        member = member or interaction.user
        embed = EmbedX.info(icon="👤", title=member.display_name)
        embed.add_field(name="", value=member.mention, inline=False)
        if isinstance(member, Member):
            embed.description = " ".join(
                [
                    f"`{role.name}`"
                    for role in member.roles
                    if role != member.guild.default_role
                ]
            )
        db = self.bot.get_db(interaction.guild)
        actor = db.find_one(Actor, Actor.id == member.id)
        if not actor:
            actor = self.bot.create_actor(member)
        embed.add_field(name="", value="", inline=False)
        embed.add_field(
            name="Rank", value=f"🏆 **{actor.rank_name}**\n`{actor.rank_bar}`"
        )
        embed.add_field(
            name="Level",
            value=f"🏅 **{actor.level}**\n`{actor.level_bar}`",
        )
        embed.add_field(
            name="Experience",
            value=f"⏫ **{intcomma(actor.xp)}** / {intcomma(actor.next_level_xp)}\n`{actor.xp_bar}`",
        )
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="Gold", value=f"💰 **{intcomma(actor.gold)}**")
        embed.add_field(name="Items", value=f"🎒 **{intcomma(len(actor.items))}**")
        embed.add_field(
            name="Equipment",
            value=f"🧰 **{intcomma(len(actor.equipment))}**",
        )
        embed.add_field(name="", value="", inline=False)
        embed.add_field(
            name="Health",
            value=f":heart: **{intcomma(actor.health)}** / {intcomma(actor.base_max_health)}\n`{actor.health_bar}`",
        )
        embed.add_field(
            name="Energy",
            value=f"⚡ **{intcomma(actor.energy)}** / {intcomma(actor.max_energy)}\n`{actor.energy_bar}`",
        )
        embed.add_field(name="", value="", inline=False)
        embed.add_field(
            name="Attack", value=f":crossed_swords: **{intcomma(actor.attack)}**"
        )
        embed.add_field(name="Defense", value=f"🛡 **{intcomma(actor.defense)}**")
        embed.add_field(name="Speed", value=f"🥾 **{intcomma(actor.speed)}**")
        embed.add_field(name="", value="", inline=False)
        if isinstance(member, Member):
            embed.add_field(
                name="Joined",
                value=f"⌚ {member.guild.name} **{naturaltime(member.joined_at or 0)}**\n-# ⌚ Discord **{naturaltime(member.created_at)}**",
            )
        embed.add_field(name="", value="", inline=False)
        embed.set_footer(
            text=f"#️⃣{member.name}\n🆔{member.id}",
            icon_url=member.display_avatar.url,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.followup.send(embed=embed)

    # ----------------------------------------------------------------------------------------------------
    # * Leaderboard
    # ----------------------------------------------------------------------------------------------------
    @app_commands.guild_only()
    @app_commands.command(description="View top members")
    async def leaderboard(self, interaction: Interaction):
        # Check guild (not needed but just for type-checking)
        guild = interaction.guild
        if not guild:
            return

        # Get top actors
        await interaction.response.defer()
        actors = self.get_top_actors(interaction.guild)
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
            name = f"{actor.display_name} @{actor.name}"
            rank = actor.rank_name
            level = str(actor.level)
            xp = naturalsize(actor.xp, binary=False, gnu=True).replace("B", "")
            gold = naturalsize(actor.gold, binary=False, gnu=True).replace("B", "")
            leaderboard_text += f"#{(i+1):<2} {name}\n\t 🏆{rank:<2} 🏅{level:<2} ⏫{xp:<8} 💰{gold}\n\n"
        leaderboard_text += "```"

        # Create embed
        embed = EmbedX.info(icon="🏆", title="Leaderboard")
        try:
            top_member = guild.get_member(top_actor.id) or await guild.fetch_member(
                top_actor.id
            )
            if top_member:
                embed.set_thumbnail(url=top_member.display_avatar)
        except:
            pass
        embed.add_field(name="", value=leaderboard_text, inline=False)
        await interaction.followup.send(embed=embed)

    # ----------------------------------------------------------------------------------------------------

    def get_top_actors(self, guild: Guild | None, limit: int = 10):
        db = self.bot.get_db(guild)
        return db.find(
            Actor,
            Actor.is_member == True,
            sort=(
                query.desc(Actor.rank),
                query.desc(Actor.level),
                query.desc(Actor.xp),
                query.desc(Actor.gold),
            ),
            limit=limit,
        )
