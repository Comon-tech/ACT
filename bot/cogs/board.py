from discord import Color, Embed, Interaction, Member, User, app_commands
from discord.app_commands import command, guild_only
from discord.ext.commands import Cog
from humanize import naturaltime

from bot.main import ActBot
from db.actor import Actor


class Board(Cog, description="Allows players to view their data."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @app_commands.guild_only()
    @app_commands.command(description="Get your or another member's information")
    async def profile(
        self, interaction: Interaction, member: Member | User | None = None
    ):
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
        await interaction.response.send_message(embed=embed)

    # @app_commands.guild_only()
    # @app_commands.command(description="View leaderboard")
    # async def leaderboard(self, interaction: Interaction):
    #     await interaction.response.defer()
    #     db = self.bot.db_engine(interaction.guild)
    #     actors = db.find(Actor) if db  else None
    #     if not actors:
    #         await interaction.followup.send("No members found for the leaderboard.")
    #         return
    #     actors = actors.sort([("level", -1), ("xp", -1), ("gold", -1)])
    #     embed = Embed(title="🏆 Leaderboard", color=Color.blue())
    #     for i, db_user_raw in enumerate(actors[:10]):
    #         db_user = DbUser.create(db_user_raw)
    #         if not db_user:
    #             continue
    #         guild = interaction.guild
    #         member = guild.get_member(db_user.id)
    #         if not member:
    #             try:
    #                 member = await guild.fetch_member(db_user.id)
    #             except:
    #                 pass
    #         if member:
    #             member_name = (
    #                 member.display_name if member else f"Unknown User ({db_user.id})"
    #             )
    #             embed.add_field(
    #                 name="",
    #                 value=10 * "➖",
    #                 inline=False,
    #             )
    #             embed.add_field(
    #                 name=f"**{i + 1}** ✨ {member_name}",
    #                 value=f" ",
    #             )
    #             embed.add_field(
    #                 name=f"🏅 {db_user.level} ⏫ {db_user.xp} 💰 {db_user.gold}",
    #                 value="",
    #             )
    #     await interaction.followup.send(embed=embed)