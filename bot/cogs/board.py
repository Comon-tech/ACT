# from discord import Color, Embed, Interaction, Member, app_commands
# from discord.app_commands import command, guild_only
# from discord.ext.commands import Bot, Cog
# from humanize import naturaltime


# class Board(Cog, description="Allows players to view their data."):
#     def __init__(self, bot: Bot):
#         self.bot = bot

#     @app_commands.guild_only()
#     @app_commands.command(description="Get your or another member's information")
#     async def profile(self, interaction: Interaction, member: Member|None = None):
#         member = member or interaction.user
#         embed = Embed(
#             title=f"{member.display_name}",
#             description=" ".join(
#                 [
#                     f"`{role.name}`"
#                     for role in member.roles
#                     if role != member.guild.default_role
#                 ]
#             ),
#             color=Color.blue(),
#         )
#         embed.set_thumbnail(url=member.display_avatar.url)
#         db_user = DbUser.load(member.id)
#         if db_user:
#             embed.add_field(name="", value="", inline=False)
#             embed.add_field(
#                 name="Level",
#                 value=f"🏅 **{db_user.level}**\n{db_user.draw_level()}",
#             )
#             embed.add_field(
#                 name="Experience",
#                 value=f"⏫ **{db_user.xp}** / {db_user.next_level_xp}\n{db_user.draw_xp()}",
#             )
#             embed.add_field(name="", value="", inline=False)
#             embed.add_field(name="Gold", value=f"💰 **{db_user.gold}**")
#             embed.add_field(name="Items", value=f"🎒 **{len(db_user.items)}**")
#             embed.add_field(name="", value="", inline=False)
#         embed.add_field(
#             name="",
#             value=f"-# ⌚ _Joined_ {member.guild.name} **{naturaltime(member.joined_at)}**\n-# ⌚ _Joined_ Discord **{naturaltime(member.created_at)}**",
#         )
#         await interaction.response.send_message(embed=embed)

#     @app_commands.guild_only()
#     @app_commands.command(description="View leaderboard")
#     async def leaderboard(self, interaction: Interaction):
#         await interaction.response.defer()
#         db_users_raw = DbUser.COLLECTION.find()
#         if not db_users_raw:
#             await interaction.followup.send("No members found for the leaderboard.")
#             return
#         db_users_raw = db_users_raw.sort([("level", -1), ("xp", -1), ("gold", -1)])
#         embed = Embed(title="🏆 Leaderboard", color=Color.blue())
#         for i, db_user_raw in enumerate(db_users_raw[:10]):
#             db_user = DbUser.create(db_user_raw)
#             if not db_user:
#                 continue
#             guild = interaction.guild
#             member = guild.get_member(db_user.id)
#             if not member:
#                 try:
#                     member = await guild.fetch_member(db_user.id)
#                 except:
#                     pass
#             if member:
#                 member_name = (
#                     member.display_name if member else f"Unknown User ({db_user.id})"
#                 )
#                 embed.add_field(
#                     name="",
#                     value=10 * "➖",
#                     inline=False,
#                 )
#                 embed.add_field(
#                     name=f"**{i + 1}** ✨ {member_name}",
#                     value=f" ",
#                 )
#                 embed.add_field(
#                     name=f"🏅 {db_user.level} ⏫ {db_user.xp} 💰 {db_user.gold}",
#                     value="",
#                 )
#         await interaction.followup.send(embed=embed)
